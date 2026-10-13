package ph.smishguard

import java.io.File
import kotlin.math.abs
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.*

/** Real unchanged supplied parameters, safe inputs, and a fitted portable comparator. */
class BantayTextParityTest {
    @Test fun activeModelMatchesPythonAndAbstainsOnUnassessableInput() = runBlocking {
        val directory = System.getProperty("smishguard.parity.dir")
        assumeTrue("Private active-model probes not configured", directory != null && File(directory, "active-model.json").isFile)
        val root = File(directory!!)
        val detector = SuppliedDetector.parse(File(root, "active-model.json").readText())
        val cases = JSONArray(File(root, "active-cases.json").readText())
        var maximumError = 0.0
        var abstained = 0
        for (i in 0 until cases.length()) {
            val case = cases.getJSONObject(i)
            val text = case.getString("text")
            assertEquals("tokens at probe $i", case.getJSONArray("tokens").toString(), JSONArray(detector.tokenizer.tokens(text)).toString())
            if (text.isNotBlank() && text.length <= MAX_MESSAGE_LENGTH) {
                val raw = detector.rawDetection(text) as Detection.Success
                maximumError = maxOf(maximumError, abs(raw.score - case.getDouble("score")))
                assertEquals("score at probe $i", case.getDouble("score"), raw.score, 1e-10)
                assertEquals(case.getBoolean("suspicious"), raw.suspicious)
                assertTrue(raw.score.isFinite() && raw.score in 0.0..1.0)
                assertFalse(raw.probability)
            }
            val result = detector.detect(text)
            if (case.getBoolean("must_abstain")) {
                assertEquals("abstention at probe $i", Detection.UnableToAssess, result)
                abstained++
            } else if (text.length > MAX_MESSAGE_LENGTH) {
                assertEquals(Detection.Failure, result)
            } else if (result is Detection.Success) {
                assertFalse(result.probability)
                assertTrue(result.score.isFinite())
            }
        }
        File(root, "active-jvm-aggregate.json").writeText(JSONObject().put("cases", cases.length())
            .put("maximum_absolute_error", maximumError).put("required_abstentions", abstained)
            .put("physical_device", false).toString(2))
    }

    @Test fun comparatorNeverClaimsProbabilityAndRejectsEmptyOrOversizedInput() = runBlocking {
        val directory = System.getProperty("smishguard.parity.dir")
        assumeTrue("Private export not configured", directory != null)
        val root = File(directory!!)
        val json = JSONObject(File(root, "model.json").readText())
        assumeTrue("Comparator schema required", json.optInt("schema_version") == 1)
        val detector = LinearDetector.parse(json.toString())
        assertFalse(detector.automaticWarningsAllowed)
        for (text in listOf("", "   ", "x".repeat(MAX_MESSAGE_LENGTH + 1))) {
            assertEquals(Detection.Failure, detector.detect(text))
        }
        for (text in listOf("qzxvunknownword zzzqqq", "\uD800", "OTP po", "🙂 ñ café")) {
            val result = detector.detect(text) as Detection.Success
            assertTrue(result.score.isFinite() && result.score in 0.0..1.0)
            assertFalse(result.probability)
        }
    }
}
