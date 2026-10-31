package ph.smishguard

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import ph.smishguard.model.*
import kotlin.math.abs

/** User example + documented synthetic scenarios; expected labels are model outputs, not human truth. */
object Svm60PracticalParity {
    suspend fun verify(model60Json: String, model80Json: String, fixture: String): JSONObject {
        val models = listOf(MulticlassSvmDetector.parse(model60Json, 60), MulticlassSvmDetector.parse(model80Json, 80))
        val cases = JSONObject(fixture).getJSONArray("cases"); val results = JSONArray()
        assertEquals(20, cases.length()); var maximumError = 0.0
        for (i in 0 until cases.length()) {
            val row = cases.getJSONObject(i); val text = row.getString("text")
            assertTrue("Do not invent independently verified labels", row.isNull("human_verified_expected_label"))
            val result = JSONObject().put("name", row.getString("name"))
            for ((j, percent) in listOf(60, 80).withIndex()) {
                val expected = row.getJSONObject("svm$percent"); val actual = models[j].scores(text)
                val label = MulticlassSvmDetector.winner(actual)
                assertEquals("practical label $percent/$i", expected.getInt("prediction"), label)
                for (c in 0..2) {
                    val error = abs(actual[c] - expected.getJSONArray("scores").getDouble(c))
                    maximumError = maxOf(maximumError, error); assertTrue(error <= 1e-10)
                }
                result.put("svm${percent}_prediction", label).put("svm${percent}_scores", JSONArray(actual))
            }
            if (row.getString("name") == "user_cashback") {
                for (model in models) {
                    val detection = model.detect(text) as Detection.Success
                    assertEquals(SmsCategory.HAM, detection.category)
                    val risk = RiskPolicy.assess(text, detection)
                    assertEquals(0, risk.score); assertEquals(RiskLevel.LOW, risk.level)
                    assertTrue(risk.indicators.none { it.weight > 0 })
                }
                result.put("risk_score", 0).put("risk_level", "LOW").put("authenticity_verified", false)
            }
            results.put(result)
        }
        // The independent risk system can flag a credential request even when the model says Ham.
        val request = "Your account is suspended. Send your OTP and PIN immediately."
        assertEquals(RiskLevel.HIGH, RiskPolicy.assess(request, models[0].detect(request)).level)
        return JSONObject().put("practical_cases", cases.length()).put("predictions_checked", cases.length()*2)
            .put("matching_predictions", cases.length()*2).put("mismatches", 0)
            .put("maximum_score_error", maximumError).put("human_verified_labels_available", 0)
            .put("risk_rules_changed", false).put("results", results)
    }
}
