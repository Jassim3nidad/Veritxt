package ph.smishguard

import java.io.File
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.MulticlassSvmDetector

class MulticlassSvmParityTest {
    @Test fun exactFrozenModelMatchesIndependentPythonFixtures() = runBlocking {
        val directory = System.getProperty("smishguard.multiclass.parity.dir")
        assumeTrue("Private multiclass model and independent fixtures required", directory != null)
        val root = File(directory!!); val json = File(root, "model.json").readText()
        val result = MulticlassSvmParity.verify(json, File(root, "multiclass-svm-cases.json").readText())
        File(root, "multiclass-jvm-parity.json").writeText(result.toString(2))
    }

    @Test fun incompatibleArtifactsAreRejected() {
        val directory = System.getProperty("smishguard.multiclass.parity.dir")
        assumeTrue(directory != null)
        val json = File(directory!!, "model.json").readText()
        for (change in listOf<(JSONObject) -> Unit>(
            { it.put("schema_version", 9) }, { it.put("C", 1) },
            { it.put("classes", JSONArray("[1,0,2]")) }, { it.put("input_view", "masked") },
            { it.put("decision", "threshold") }, { it.put("stop_words", JSONArray()) },
            { it.put("coefficients", JSONArray()) }, { it.put("intercepts", JSONArray("[1,2]")) },
            { it.put("calibration", "sigmoid") }
        )) {
            val bad = JSONObject(json); change(bad)
            assertThrows(Exception::class.java) { MulticlassSvmDetector.parse(bad.toString()) }
        }
    }
}
