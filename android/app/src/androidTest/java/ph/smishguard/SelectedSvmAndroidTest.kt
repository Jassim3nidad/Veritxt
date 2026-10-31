package ph.smishguard

import android.Manifest
import android.content.pm.PackageManager
import android.os.Debug
import android.provider.Settings
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test

class SelectedSvmAndroidTest {
    @Test fun bundledSelectedSvmIsTheActualAppDetector() = runBlocking {
        assumeTrue(BuildConfig.BUILD_TYPE == "selectedSvm")
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        val app = context.applicationContext as SoftwareTestApp
        app.testDetector = null
        val actual = app.detector()
        assertTrue(actual is ph.smishguard.model.SelectedSvmDetector)
        assertTrue(actual.automaticWarningsAllowed)
        fun asset(name: String) = context.assets.open(name).bufferedReader().use { it.readText() }
        val model = asset("model.json")
        val adapter = asset("raw-sms-adapter.json")
        val expected = ph.smishguard.model.SelectedSvmDetector(model, adapter)
        val cases = org.json.JSONArray(instrumentation.context.assets.open("raw-sms-cases.json").bufferedReader().use { it.readText() })
        for (i in 0 until cases.length()) {
            val raw = cases.getJSONObject(i).getString("raw")
            assertEquals("Bundled app path at probe $i", expected.detect(raw), app.assess(raw))
        }
        assertEquals(.37, org.json.JSONObject(model).getDouble("threshold"), 1e-15)
    }

    @Test fun rawSmsPreparationMatchesTrainingOffline() = runBlocking {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val arguments = InstrumentationRegistry.getArguments()
        assumeTrue("Raw SMS probes requested", arguments.getString("rawSms") == "true")
        assertEquals("true", arguments.getString("offline"))
        val context = instrumentation.targetContext
        assertEquals(1, Settings.Global.getInt(context.contentResolver, Settings.Global.AIRPLANE_MODE_ON))
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(Manifest.permission.INTERNET))
        fun asset(name: String) = instrumentation.context.assets.open(name).bufferedReader().use { it.readText() }
        val result = RawSmsParity.verify(asset("selected-svm-model.json"), asset("raw-sms-adapter.json"), asset("raw-sms-cases.json"))
            .put("api", android.os.Build.VERSION.SDK_INT).put("offline",true).put("physical_device",false)
        File(context.filesDir,"raw-sms-android-aggregate.json").writeText(result.toString(2))
    }

    @Test fun actualSelectedModelMatchesPythonOffline() = runBlocking {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        assumeTrue("Offline verification flag required", InstrumentationRegistry.getArguments().getString("offline") == "true")
        val context = instrumentation.targetContext
        assertEquals(1, Settings.Global.getInt(context.contentResolver, Settings.Global.AIRPLANE_MODE_ON))
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(Manifest.permission.INTERNET))
        fun asset(name: String) = instrumentation.context.assets.open(name).bufferedReader().use { it.readText() }
        val before = Debug.getPss()
        val result = SelectedSvmParity.verify(asset("selected-svm-model.json"), asset("selected-svm-cases.json"))
            .put("pss_kib_before", before).put("pss_kib_after", Debug.getPss())
            .put("memory_note", "Whole instrumentation process PSS samples; not isolated model memory")
            .put("api", android.os.Build.VERSION.SDK_INT).put("offline", true).put("physical_device", false)
        File(context.filesDir, "selected-svm-android-aggregate.json").writeText(result.toString(2))
    }
}
