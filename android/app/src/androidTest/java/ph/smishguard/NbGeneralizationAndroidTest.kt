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
import ph.smishguard.model.NbGeneralizationDetector
import ph.smishguard.model.RiskPolicy
import ph.smishguard.model.InputKind

class NbGeneralizationAndroidTest {
    @Test fun actualBundledNbMatchesPythonOffline() = runBlocking {
        assumeTrue(BuildConfig.BUILD_TYPE == "nbGeneralization")
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        assertEquals(1, Settings.Global.getInt(context.contentResolver, Settings.Global.AIRPLANE_MODE_ON))
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(Manifest.permission.INTERNET))
        val json = context.assets.open("model.json").bufferedReader().use { it.readText() }
        val fixture = instrumentation.context.assets.open("nb-generalization-cases.json").bufferedReader().use { it.readText() }
        val result = NbGeneralizationParity.verify(json, fixture)
        val app = context.applicationContext as SoftwareTestApp
        app.testDetector = null
        assertTrue(app.detector() is NbGeneralizationDetector)
        assertTrue(app.detector().automaticWarningsAllowed)
        val model = NbGeneralizationDetector.parse(json)
        val cases = JSONObject(fixture).getJSONArray("cases")
        var checked = 0
        for (i in 0 until cases.length()) {
            val c = cases.getJSONObject(i)
            if (!c.getString("name").startsWith("held_out_")) continue
            val text = c.getString("text")
            if (RiskPolicy.inputKind(text) == InputKind.MESSAGE) {
                assertEquals("App model path at $i", model.detect(text), app.assess(text)); checked++
            }
        }
        result.put("app_path_cases", checked).put("api", android.os.Build.VERSION.SDK_INT)
            .put("offline", true).put("physical_device", false)
        File(context.filesDir, "nb-android-parity.json").writeText(result.toString(2))
    }
}
