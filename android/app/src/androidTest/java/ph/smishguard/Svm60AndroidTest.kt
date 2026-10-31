package ph.smishguard

import android.provider.Settings
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.*

class Svm60AndroidTest {
    @Test fun actual60AssetAndBothFrozenModelsMatchPython() = runBlocking {
        assumeTrue(BuildConfig.BUILD_TYPE == "multiclassSvm60")
        val instrumentation = InstrumentationRegistry.getInstrumentation(); val context = instrumentation.targetContext
        assertEquals(1, Settings.Global.getInt(context.contentResolver, Settings.Global.AIRPLANE_MODE_ON))
        fun asset(name: String) = instrumentation.context.assets.open(name).bufferedReader().use { it.readText() }
        val json = context.assets.open("model.json").bufferedReader().use { it.readText() }
        val fixture = asset("multiclass-svm60-cases.json")
        val result = MulticlassSvmParity.verify(json, fixture, 60)
        val practical = Svm60PracticalParity.verify(json, asset("comparison-svm80-model.json"), asset("practical-comparison.json"))
        File(context.filesDir, "practical-android-parity.json").writeText(practical.toString(2))
        val app = context.applicationContext as SoftwareTestApp; app.testDetector = null
        assertTrue(app.detector() is MulticlassSvmDetector)
        assertEquals(60, (app.detector() as MulticlassSvmDetector).trainingPercent)
        val model = MulticlassSvmDetector.parse(json, 60); val cases = JSONObject(fixture).getJSONArray("cases")
        var checked = 0
        for (i in 0 until cases.length()) {
            val text = cases.getJSONObject(i).getString("text")
            if (text.isNotBlank() && text.length <= MAX_MESSAGE_LENGTH && RiskPolicy.inputKind(text) == InputKind.MESSAGE) {
                assertEquals("actual app path at $i", model.detect(text), app.assess(text)); checked++
            }
        }
        result.put("app_path_cases", checked).put("training_percent", 60).put("api", android.os.Build.VERSION.SDK_INT)
            .put("thesis_test_messages_used", 0).put("physical_device", false).put("offline", true)
        File(context.filesDir, "svm60-android-parity.json").writeText(result.toString(2))
    }
}
