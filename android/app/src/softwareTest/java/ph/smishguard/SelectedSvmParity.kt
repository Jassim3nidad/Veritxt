package ph.smishguard

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import ph.smishguard.model.*
import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.sqrt

object SelectedSvmParity {
    suspend fun verify(modelJson: String, casesJson: String): JSONObject {
        val loadStart = System.nanoTime()
        val detector = SelectedSvmScorer.parse(modelJson)
        val loadMillis = (System.nanoTime() - loadStart) / 1e6
        val cases = JSONArray(casesJson)
        require(cases.length() > 0)
        var maximumError = 0.0; var maximumFeatureError = 0.0; var abstentions = 0; var elapsed = 0.0
        for (i in 0 until cases.length()) {
            val case = cases.getJSONObject(i); val text = case.getString("text")
            assertEquals("terms at case $i", case.getJSONArray("terms").toString(), JSONArray(detector.terms(text)).toString())
            val expected = case.getJSONObject("features")
            val actual = detector.features(text)
            assertEquals("feature indices at case $i", expected.keys().asSequence().map { it.toInt() }.toSet(), actual.keys)
            for ((index, value) in actual) {
                val error = abs(value - expected.getDouble(index.toString()))
                maximumFeatureError = maxOf(maximumFeatureError, error)
                assertTrue("feature value at case $i", error <= 1e-10)
            }
            val start = System.nanoTime(); val score = detector.score(text); elapsed += (System.nanoTime() - start) / 1e6
            maximumError = maxOf(maximumError, abs(score - case.getDouble("score")))
            assertEquals("score at case $i", case.getDouble("score"), score, 1e-10)
            assertEquals(case.getBoolean("suspicious"), score >= detector.threshold)
            if (case.getBoolean("must_abstain")) {
                assertEquals("abstention at case $i", Detection.UnableToAssess, detector.detect(text)); abstentions++
            } else if (text.length > MAX_MESSAGE_LENGTH) {
                assertEquals(Detection.Failure, detector.detect(text))
            } else {
                val result = detector.detect(text)
                if (result is Detection.Success) { assertFalse(result.probability); assertTrue(result.experimental) }
            }
        }
        // Production loader must continue to reject this test-only candidate contract.
        assertThrows(Exception::class.java) { ModelLoader.parse(modelJson) }
        for (change in listOf<(JSONObject) -> Unit>(
            { it.put("automatic_warnings_approved", true) }, { it.put("probability_approved", true) },
            { it.put("threshold", -1) }, { it.put("input_view", "raw_sms") },
            { it.put("classes", JSONArray("[\"smishing\",\"ham\"]")) },
            { it.put("idf", JSONArray("[0]")) }, { it.put("bias", "NaN") },
            { it.getJSONObject("calibration").put("a", -1) }
        )) {
            val bad = JSONObject(modelJson); change(bad)
            assertThrows(Exception::class.java) { SelectedSvmScorer.parse(bad.toString()) }
        }
        return JSONObject().put("cases", cases.length()).put("maximum_score_error", maximumError)
            .put("maximum_feature_error", maximumFeatureError).put("required_abstentions", abstentions)
            .put("model_bytes", modelJson.toByteArray().size).put("load_ms", loadMillis)
            .put("mean_score_ms", elapsed / cases.length()).put("production_loader_rejects", true)
    }
}
