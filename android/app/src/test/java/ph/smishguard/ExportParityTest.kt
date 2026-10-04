package ph.smishguard

import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.Detection
import ph.smishguard.model.LinearDetector
import ph.smishguard.model.Preprocessing
import java.io.File

class ExportParityTest {
    @Test fun realExportMatchesFrozenPythonPipeline() = runBlocking {
        val directory = System.getProperty("smishguard.parity.dir")
        assumeTrue("No real trained export is installed", !directory.isNullOrBlank())
        val modelJson = File(directory!!,"model.json").readText()
        val casesJson = File(directory,"cases.json").readText()
        if (org.json.JSONObject(modelJson).optString("evaluation_status") == "preliminary_retrospective") {
            val result = ComparisonParity.verify(modelJson, casesJson, org.json.JSONObject(modelJson).getString("algorithm"))
            File(directory,"jvm-aggregate.json").writeText(result.toString(2))
            return@runBlocking
        }
        val model = LinearDetector.parse(modelJson)
        val cases = JSONArray(File(directory,"cases.json").readText())
        assertTrue(cases.length() > 0)
        for (i in 0 until cases.length()) {
            val case = cases.getJSONObject(i)
            val text = case.getString("text")
            assertEquals(case.getString("normalized"), Preprocessing.normalize(text))
            val result = model.detect(text) as Detection.Success
            assertEquals(case.getDouble("score"), result.score, 1e-10)
            assertEquals(case.getBoolean("suspicious"), result.suspicious)
            assertFalse(result.synthetic)
        }
    }
}
