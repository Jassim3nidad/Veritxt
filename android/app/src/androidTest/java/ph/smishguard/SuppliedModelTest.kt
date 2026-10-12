package ph.smishguard

import android.Manifest
import android.content.pm.PackageManager
import android.provider.Settings
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.*
import ph.smishguard.privacy.*
import java.time.ZonedDateTime

class SuppliedModelTest {
    private fun source(): String = InstrumentationRegistry.getInstrumentation().targetContext.assets.open("model.json").bufferedReader().use { it.readText() }
    @Test fun offlinePythonParityAndDevelopmentPolicy() = runBlocking {
        assumeTrue(BuildConfig.BUILD_TYPE == "development")
        assumeTrue(InstrumentationRegistry.getArguments().getString("offline") == "true")
        val instrumentation = InstrumentationRegistry.getInstrumentation(); val context = instrumentation.targetContext
        assertEquals(1, Settings.Global.getInt(context.contentResolver, Settings.Global.AIRPLANE_MODE_ON))
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(Manifest.permission.INTERNET))
        val detector = ModelLoader.parse(source()) as SuppliedDetector
        assertFalse(detector.automaticWarningsAllowed)
        val cases = JSONArray(instrumentation.context.assets.open("supplied-parity.json").bufferedReader().use { it.readText() })
        for (i in 0 until cases.length()) {
            val case = cases.getJSONObject(i); val text = case.getString("text")
            val expectedTokens = case.getJSONArray("tokens")
            assertEquals(List(expectedTokens.length()) { expectedTokens.getString(it) }, detector.tokenizer.tokens(text))
            val output = detector.detect(text)
            if (!case.getBoolean("valid_input")) { assertEquals(Detection.Failure, output); continue }
            val result = output as Detection.Success
            assertEquals(case.getDouble("score"), result.score, 1e-10)
            assertEquals(case.getBoolean("suspicious"), result.suspicious)
            assertTrue(result.experimental); assertFalse(result.synthetic); assertFalse(result.probability)
            assertNull(ReportPayload.create(null, result, ZonedDateTime.now(), Brand.UNSPECIFIED))
        }
        assertEquals(Detection.Failure, detector.detect("a".repeat(10001)))
    }
    @Test fun unsupportedAndMalformedModelsFailClosed() {
        assumeTrue(BuildConfig.BUILD_TYPE == "development")
        val original = source()
        val changes: List<(JSONObject) -> Unit> = listOf(
            { it.put("schema_version", 999) }, { it.put("threshold_comparison", "greater_or_equal") },
            { it.put("automatic_warnings_approved", true) }, { it.put("evaluation_status", "approved") },
            { it.put("classes", JSONArray("[\"smishing\",\"ham\"]")) },
            { it.put("weights", JSONArray("[0.1]")) }, { it.put("bias", "not-a-number") },
            { it.getJSONObject("unicode").put("unicode_version", "unknown") }
        )
        for (change in changes) {
            val objectValue = JSONObject(original); change(objectValue)
            assertThrows(Exception::class.java) { ModelLoader.parse(objectValue.toString()) }
        }
        assertThrows(Exception::class.java) { ModelLoader.parse("{") }
    }
}
