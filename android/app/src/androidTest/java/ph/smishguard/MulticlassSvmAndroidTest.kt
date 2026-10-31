package ph.smishguard

import android.Manifest
import android.content.pm.PackageManager
import android.provider.Settings
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.*

class MulticlassSvmAndroidTest {
    @Test fun actualBundledModelMatchesPythonAndAppPath() = runBlocking {
        assumeTrue(BuildConfig.BUILD_TYPE == "multiclassSvm")
        val instrumentation = InstrumentationRegistry.getInstrumentation(); val context = instrumentation.targetContext
        assertEquals(1, Settings.Global.getInt(context.contentResolver, Settings.Global.AIRPLANE_MODE_ON))
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(Manifest.permission.INTERNET))
        val json = context.assets.open("model.json").bufferedReader().use { it.readText() }
        val fixture = instrumentation.context.assets.open("multiclass-svm-cases.json").bufferedReader().use { it.readText() }
        val result = MulticlassSvmParity.verify(json, fixture)
        val app = context.applicationContext as SoftwareTestApp; app.testDetector = null
        assertTrue(app.detector() is MulticlassSvmDetector)
        val model = MulticlassSvmDetector.parse(json); val cases = JSONObject(fixture).getJSONArray("cases")
        var checked = 0
        for (i in 0 until cases.length()) {
            val c = cases.getJSONObject(i); val text = c.getString("text")
            if (text.isNotBlank() && text.length <= MAX_MESSAGE_LENGTH && RiskPolicy.inputKind(text) == InputKind.MESSAGE) {
                assertEquals("app classifier at $i", model.detect(text), app.assess(text)); checked++
            }
        }
        for (text in listOf("https://example.invalid/", "+1 202 555 0100", "fictional@example.invalid"))
            assertEquals(Detection.UnableToAssess, app.assess(text))
        result.put("app_path_cases", checked).put("api", android.os.Build.VERSION.SDK_INT).put("offline", true).put("physical_device", false)
        File(context.filesDir, "multiclass-android-parity.json").writeText(result.toString(2))
    }
}
