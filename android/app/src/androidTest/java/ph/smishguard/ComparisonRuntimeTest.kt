package ph.smishguard

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.provider.Settings
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.*
import ph.smishguard.privacy.*
import java.time.ZonedDateTime

class ComparisonRuntimeTest {
    @Test fun bundledModelOfflinePolicyAndWarmLatency() = runBlocking {
        assumeTrue(BuildConfig.BUILD_TYPE in listOf("lr", "nb", "svm"))
        assumeTrue(InstrumentationRegistry.getArguments().getString("offline") == "true")
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        assertEquals(1, Settings.Global.getInt(context.contentResolver, Settings.Global.AIRPLANE_MODE_ON))
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(Manifest.permission.INTERNET))
        val app = context.applicationContext as SoftwareTestApp
        app.testDetector = null
        val loadStarted = System.nanoTime()
        val detector = app.detector()
        val loadMillis = (System.nanoTime() - loadStarted) / 1e6
        assertTrue(detector is ComparisonDetector)
        assertFalse(detector.automaticWarningsAllowed)
        assertEquals(Detection.Unavailable, MissingDetector().detect("hello"))
        assertEquals(Detection.InvalidModel, MissingDetector(true).detect("hello"))
        for (probe in listOf("", "qwerty", "!!!", "123456", "https://account.example/verify"))
            assertEquals(Detection.UnableToAssess, detector.detect(probe))
        val probes = listOf("Hello po", "Bayad na po", "Your payment is received.",
            "Your account is suspended. Verify your password at https://account.example now.")
        repeat(20) { detector.detect(probes[it % probes.size]) }
        var scored = 0; var abstained = 0
        val samples = LongArray(200) { index ->
            val started = System.nanoTime()
            val result = detector.detect(probes[index % probes.size])
            val elapsed = System.nanoTime() - started
            if (result is Detection.Success) {
                scored++; assertTrue(result.experimental); assertFalse(result.probability)
                assertNull(ReportPayload.create(null, result, ZonedDateTime.now(), Brand.UNSPECIFIED))
            } else { abstained++; assertEquals(Detection.UnableToAssess, result) }
            elapsed
        }.sorted()
        val bytes = context.assets.open("model.json").use { it.readBytes().size }
        instrumentation.sendStatus(0, Bundle().apply {
            putString("stream", "BENCHMARK algorithm=${BuildConfig.BUILD_TYPE} probes=4 warmups=20 scans=200 scored=$scored abstained=$abstained model_bytes=$bytes p50_ms=${samples[99] / 1e6} p95_ms=${samples[189] / 1e6} model_load_ms=$loadMillis\n")
        })
    }
}
