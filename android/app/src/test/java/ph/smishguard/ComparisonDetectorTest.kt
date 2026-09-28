package ph.smishguard

import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.*

class ComparisonDetectorTest {
    private fun resource(name: String) = javaClass.classLoader!!.getResource(name)!!.readText()

    @Test fun allThreeAlgorithmsMatchPythonGoldenScores() = runBlocking {
        for (name in listOf("lr", "nb", "svm")) {
            val model = LinearDetector.parse(resource("software/$name-model.json"), allowSynthetic = true)
            val cases = JSONArray(resource("software/$name-cases.json"))
            for (i in 0 until cases.length()) {
                val case = cases.getJSONObject(i)
                val result = model.detect(case.getString("text")) as Detection.Success
                assertEquals(case.getDouble("score"), result.score, 1e-10)
                assertEquals(case.getBoolean("suspicious"), result.suspicious)
                assertFalse(result.probability)
            }
        }
    }

    @Test fun manualPolicyAbstainsAndNeverApprovesWarningsOrProbability() = runBlocking {
        for (name in listOf("lr", "nb", "svm")) {
            // In-memory policy fixture only. Never written or bundled as a research model.
            val fixture = JSONObject(resource("software/$name-model.json"))
                .put("synthetic", false).put("algorithm", name)
            val detector = ComparisonDetector(fixture.toString(), name)
            assertFalse(detector.automaticWarningsAllowed)
            for (text in listOf("", "12345", "!!!", "qwerty", "zzzz", "🧪", "unseenword", "https://example.org")) {
                assertEquals(text, Detection.UnableToAssess, detector.detect(text))
            }
            val result = detector.detect("verify account") as Detection.Success
            assertTrue(result.experimental)
            assertFalse(result.probability)
            assertEquals(Detection.Failure, detector.detect("a".repeat(10001)))
            fixture.put("algorithm", "other")
            assertThrows(IllegalArgumentException::class.java) { ComparisonDetector(fixture.toString(), name) }
            fixture.put("algorithm", name).put("synthetic", true)
            assertThrows(IllegalArgumentException::class.java) { ComparisonDetector(fixture.toString(), name) }
            fixture.put("synthetic", false).remove("calibration")
            assertThrows(Exception::class.java) { ComparisonDetector(fixture.toString(), name) }
        }
    }
}
