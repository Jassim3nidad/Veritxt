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

class FoldedCandidateAndroidTest {
    @Test fun privateModelOfflineParityAndPolicy() = runBlocking {
        assumeTrue(BuildConfig.BUILD_TYPE == "lrCalibrated4")
        assumeTrue(InstrumentationRegistry.getArguments().getString("offline") == "true")
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        assertEquals(1, Settings.Global.getInt(context.contentResolver, Settings.Global.AIRPLANE_MODE_ON))
        for (permission in listOf(Manifest.permission.INTERNET, Manifest.permission.READ_CONTACTS))
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(permission))
        val modelJson = context.assets.open("model.json").bufferedReader().use { it.readText() }
        val casesJson = instrumentation.context.assets.open("folded-private-cases.json").bufferedReader().use { it.readText() }
        val result = FoldedParity.verify(modelJson, casesJson)
        val app = context.applicationContext as SoftwareTestApp
        app.testDetector = null
        val detector = app.detector()
        assertTrue(detector is SuppliedDetector)
        assertFalse(detector.automaticWarningsAllowed)
        for (probe in listOf("", "   ", "xqzvplmkj", "!!!", "https://example.invalid"))
            assertEquals(Detection.UnableToAssess, detector.detect(probe))
        assertEquals(Detection.Failure, detector.detect("a".repeat(10001)))
        val probes = listOf("Bayad na po", "Hello po, kita tayo bukas.", "Your account needs verification at https://example.invalid")
        repeat(20) { detector.detect(probes[it % probes.size]) }
        val timings = LongArray(200) { i ->
            val started = System.nanoTime()
            val detection = detector.detect(probes[i % probes.size])
            val elapsed = System.nanoTime() - started
            if (detection is Detection.Success)
                assertNull(ReportPayload.create(null, detection, ZonedDateTime.now(), Brand.UNSPECIFIED))
            elapsed
        }.sorted()
        result.put("warm_scan_p50_ms", timings[99]/1e6).put("warm_scan_p95_ms", timings[189]/1e6)
            .put("api", android.os.Build.VERSION.SDK_INT).put("timing_scope", "emulator; 3 invented probes, 20 warmups, 200 scans; load/UI excluded")
        instrumentation.sendStatus(0, Bundle().apply { putString("stream", "FOLDED_AGGREGATE=" + result.toString() + "\n") })
    }
}
