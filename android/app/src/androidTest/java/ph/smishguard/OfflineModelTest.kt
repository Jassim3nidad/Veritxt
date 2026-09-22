package ph.smishguard

import android.Manifest
import android.content.pm.PackageManager
import android.provider.Settings
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.Detection
import ph.smishguard.model.LinearDetector

class OfflineModelTest {
    @Test fun exportedSklearnModelsRunOfflineAndStaySynthetic() = runBlocking {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getArguments().getString("offline") == "true")
        val context = instrumentation.targetContext
        assertEquals(1, Settings.Global.getInt(context.contentResolver, Settings.Global.AIRPLANE_MODE_ON))
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(Manifest.permission.INTERNET))
        for (name in listOf("lr", "nb", "svm")) {
            val json = instrumentation.context.assets.open("software/$name-model.json").bufferedReader().use { it.readText() }
            assertThrows(IllegalArgumentException::class.java) { LinearDetector.parse(json) }
            val model = LinearDetector.parse(json, allowSynthetic = true)
            val cases = JSONArray(instrumentation.context.assets.open("software/$name-cases.json").bufferedReader().use { it.readText() })
            for (i in 0 until cases.length()) {
                val case = cases.getJSONObject(i)
                val result = model.detect(case.getString("text")) as Detection.Success
                assertEquals(case.getDouble("score"), result.score, 1e-10)
                assertEquals(case.getBoolean("suspicious"), result.suspicious)
                assertTrue(result.synthetic)
                assertFalse(result.probability)
            }
        }
    }
}
