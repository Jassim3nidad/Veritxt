package ph.smishguard

import java.util.regex.Pattern
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import ph.smishguard.model.*
import kotlin.math.abs

object RawSmsParity {
    suspend fun verify(modelJson: String, adapterJson: String, casesJson: String): JSONObject {
        val adapter = RawSmsView.parse(adapterJson)
        val detector = SelectedSvmScorer.parse(modelJson)
        val deployed = SelectedSvmDetector(modelJson, adapterJson)
        val cases = JSONArray(casesJson); var maxError = 0.0; var abstained = 0
        for (i in 0 until cases.length()) {
            val case = cases.getJSONObject(i); val raw = case.getString("raw"); val view = adapter.view(raw)
            assertEquals("raw view at probe $i", case.getString("view"), view)
            assertEquals("terms at probe $i", case.getJSONArray("terms").toString(), JSONArray(detector.terms(view)).toString())
            val expected = case.getJSONObject("features"); val actual = detector.features(view)
            assertEquals(expected.keys().asSequence().map { it.toInt() }.toSet(), actual.keys)
            actual.forEach { (index,value) -> assertEquals("feature at probe $i", expected.getDouble(index.toString()), value, 1e-10) }
            val score = detector.score(view); maxError = maxOf(maxError, abs(score-case.getDouble("score")))
            assertEquals("score at probe $i", case.getDouble("score"), score, 1e-10)
            assertEquals(case.getBoolean("suspicious"), score >= detector.threshold)
            val result = if (raw.length > MAX_MESSAGE_LENGTH) Detection.Failure else detector.detect(view)
            assertEquals("App raw-SMS inference at probe $i", result, deployed.detect(raw))
            if (case.getBoolean("overlong")) assertEquals(Detection.Failure, result)
            else if (case.getBoolean("must_abstain")) { assertEquals("abstention at probe $i", Detection.UnableToAssess, result); abstained++ }
            else if (result is Detection.Success) { assertFalse(result.probability); assertTrue(result.experimental) }
        }
        return JSONObject().put("raw_cases",cases.length()).put("maximum_score_error",maxError)
            .put("required_abstentions",abstained).put("raw_view_matches",true)
    }
}
