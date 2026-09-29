package ph.smishguard

import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.*
import java.io.File
import java.security.MessageDigest

class CandidateDetectorTest {
    @Test fun privateCandidateMatchesIndependentPythonWithoutLoggingMessages() = runBlocking {
        val directory = System.getProperty("smishguard.candidate.parity.dir")
        assumeTrue("Private candidate parity not configured", directory != null)
        val root = File(directory!!)
        val model = SuppliedDetector.parse(File(root, "model.json").readText(), candidate = true)
        val cases = JSONArray(File(root, "cases.json").readText())
        var maxError = 0.0
        var abstained = 0
        var scored = 0
        for (i in 0 until cases.length()) {
            val case = cases.getJSONObject(i)
            val text = case.getString("text")
            assertEquals("tokens at index $i", case.getJSONArray("tokens").toString(), JSONArray(model.tokenizer.tokens(text)).toString())
            // Raw empty input is intentionally not a legitimate-message prediction.
            if (text.isNotBlank() && text.length <= MAX_MESSAGE_LENGTH) {
                val raw = model.rawDetection(text) as Detection.Success
                val error = kotlin.math.abs(case.getDouble("score") - raw.score)
                maxError = maxOf(maxError, error)
                assertTrue("score parity at index $i", error <= 1e-10)
                assertEquals("threshold at index $i", case.getBoolean("suspicious"), raw.suspicious)
            }
            when (val result = model.detect(text)) {
                Detection.UnableToAssess -> abstained++
                is Detection.Success -> { scored++; assertFalse(result.probability); assertTrue(result.experimental) }
                else -> assertTrue("Unexpected outcome at index $i", text.length > MAX_MESSAGE_LENGTH)
            }
        }
        File(root, "jvm-adapter-aggregate.json").writeText(JSONObject().put("cases", cases.length())
            .put("max_absolute_error", maxError).put("abstained", abstained).put("scored", scored)
            .put("model_sha256", sha(File(root, "model.json")))
            .put("cases_sha256", sha(File(root, "cases.json"))).toString(2))
    }
    private fun sha(file: File) = MessageDigest.getInstance("SHA-256").digest(file.readBytes())
        .joinToString("") { "%02x".format(it) }
}
