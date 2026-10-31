package ph.smishguard

import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.*
import java.io.File
import java.security.MessageDigest

class OldBinarySvmAndroidTest {
    @Test fun unchangedOldModelAndRawSmsPreparationMatchPython() = runBlocking {
        assertEquals("oldSvm", BuildConfig.BUILD_TYPE)
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val app = instrumentation.targetContext.applicationContext as SoftwareTestApp
        app.testDetector = null
        fun asset(name: String) = app.assets.open(name).bufferedReader().use { it.readText() }
        fun fixture(name: String) = instrumentation.context.assets.open(name).bufferedReader().use { it.readText() }
        val model = asset("model.json")
        val adapter = asset("raw-sms-adapter.json")
        val hash = MessageDigest.getInstance("SHA-256").digest(model.toByteArray()).joinToString("") { "%02x".format(it) }
        assertEquals("15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c", hash)
        assertEquals("[\"ham\",\"smishing\"]", JSONObject(model).getJSONArray("classes").toString())
        assertEquals(18473, JSONObject(model).getJSONArray("vocabulary").length())
        assertEquals("linked-cashback-claim-deadline-v1", AppRiskPolicy.VERSION)
        val parity = SelectedSvmParity.verify(model, fixture("selected-svm-cases.json"))
        val rawParity = RawSmsParity.verify(model, adapter, fixture("raw-sms-cases.json"))
        val detector = app.detector()
        assertTrue(detector is SelectedSvmDetector)
        val baseline = SelectedSvmDetector(model, adapter)
        val cases = JSONArray(fixture("raw-sms-cases.json"))
        var appCases = 0
        for (i in 0 until cases.length()) {
            val text = cases.getJSONObject(i).getString("raw")
            val expected = baseline.detect(text)
            val labeled = if (expected is Detection.Success) expected.copy(
                category = if (expected.suspicious) SmsCategory.SMISHING else SmsCategory.HAM) else expected
            assertEquals("Production detector $i", labeled, detector.detect(text))
            if (RiskPolicy.inputKind(text) == InputKind.MESSAGE) {
                val actual = app.assess(text)
                assertEquals("Application path $i", labeled, actual)
                assertEquals("Original risk policy $i", RiskPolicy.assess(text, actual), AppRiskPolicy.assess(text, actual))
                assertFalse(AppRiskPolicy.assess(text, actual).indicators.contains(RiskIndicator.CASHBACK_DEADLINE))
                appCases++
            }
        }
        val result = JSONObject().put("parity", parity).put("raw_parity", rawParity)
            .put("app_path_cases", appCases).put("model_sha256", hash)
            .put("risk_profile", AppRiskPolicy.VERSION).put("cashback_rule_enabled", true)
            .put("cashback_requires_link", true)
            .put("api", android.os.Build.VERSION.SDK_INT).put("physical_device", false)
        File(app.filesDir,"old-binary-android-parity.json").writeText(result.toString(2))
    }
}
