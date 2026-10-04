package ph.smishguard

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import ph.smishguard.model.*

/** Full fitted-pipeline expectations stay in private test assets, never the app APK. */
object ComparisonParity {
    suspend fun verify(modelJson: String, casesJson: String, algorithm: String): JSONObject {
        val metadata = JSONObject(modelJson)
        assertEquals(algorithm, metadata.getString("algorithm"))
        val raw = LinearDetector.parse(modelJson)
        val detector = ComparisonDetector(modelJson, algorithm)
        val cases = JSONArray(casesJson)
        var maxScore = 0.0; var maxMargin = 0.0; var scored = 0; var abstained = 0
        for (i in 0 until cases.length()) {
            val case = cases.getJSONObject(i); val text = case.getString("text")
            assertTrue("normalization at $i", case.getString("normalized") == Preprocessing.normalize(text))
            val marginError = kotlin.math.abs(case.getDouble("margin") - raw.decisionMargin(text))
            maxMargin = maxOf(maxMargin, marginError)
            assertTrue("margin at $i", marginError <= 1e-10)
            if (text.isNotBlank()) {
                val result = raw.detect(text) as Detection.Success
                val error = kotlin.math.abs(case.getDouble("score") - result.score)
                maxScore = maxOf(maxScore, error)
                assertTrue("score at $i", error <= 1e-10)
                assertTrue("threshold at $i", case.getBoolean("suspicious") == result.suspicious)
            }
            val actual = detector.detect(text)
            assertTrue("abstention at $i", case.getBoolean("assessable") == (actual is Detection.Success))
            when (actual) {
                is Detection.Success -> { scored++; assertTrue(actual.experimental); assertFalse(actual.probability) }
                Detection.UnableToAssess -> abstained++
                else -> fail("Unexpected result at $i")
            }
        }
        assertFalse(detector.automaticWarningsAllowed)
        return JSONObject().put("algorithm", algorithm).put("model_version", metadata.getString("model_version"))
            .put("cases", cases.length()).put("scored", scored).put("abstained", abstained)
            .put("max_score_error", maxScore).put("max_margin_error", maxMargin)
            .put("model_sha256", FoldedParity.sha(modelJson)).put("cases_sha256", FoldedParity.sha(casesJson))
    }
}
