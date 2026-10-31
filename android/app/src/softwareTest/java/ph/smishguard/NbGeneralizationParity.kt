package ph.smishguard

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import ph.smishguard.model.*
import kotlin.math.abs

/** Shared actual-model checks for the host JVM and Android runtime. Never in app assets. */
object NbGeneralizationParity {
    suspend fun verify(json: String, fixture: String): JSONObject {
        val start = System.nanoTime()
        val model = NbGeneralizationDetector.parse(json)
        val loadMs = (System.nanoTime() - start) / 1e6
        val cases = JSONObject(fixture).getJSONArray("cases")
        assertTrue(cases.length() >= 684)
        var maximumScoreError = 0.0; var maximumFeatureError = 0.0
        var heldOut = 0; var assessed = 0; var abstained = 0
        val latencies = mutableListOf<Double>()
        for (j in 0 until cases.length()) {
            val c = cases.getJSONObject(j); val text = c.getString("text")
            assertEquals("terms at $j", c.getJSONArray("terms").toString(), JSONArray(model.terms(text)).toString())
            val expected = c.getJSONObject("features"); val actual = model.features(text)
            assertEquals("feature keys at $j", expected.keys().asSequence().map { it.toInt() }.toSet(), actual.keys)
            for ((key, value) in actual) {
                val error = abs(value - expected.getDouble(key.toString()))
                maximumFeatureError = maxOf(maximumFeatureError, error)
                assertTrue("feature value at $j/$key", error <= 1e-10)
            }
            val tick = System.nanoTime(); val score = model.score(text)
            latencies.add((System.nanoTime() - tick) / 1e6)
            maximumScoreError = maxOf(maximumScoreError, abs(score - c.getDouble("score")))
            assertEquals("score at $j", c.getDouble("score"), score, 1e-10)
            assertEquals("decision at $j", c.getBoolean("suspicious"), score >= model.threshold)
            if (c.getString("name").startsWith("held_out_")) {
                heldOut++
                when (val result = model.detect(text)) {
                    is Detection.Success -> {
                        assessed++; assertEquals(c.getBoolean("suspicious"), result.suspicious)
                        assertEquals(score, result.score, 1e-10); assertFalse(result.probability); assertTrue(result.experimental)
                    }
                    Detection.UnableToAssess -> abstained++
                    else -> fail("Unexpected held-out status at $j")
                }
            }
        }
        assertEquals(684, heldOut)
        for (text in listOf("", "???", "qzxvqzxvunknown", "1234567890", "https://example.invalid/account", "₱123456.90"))
            assertEquals("abstention", Detection.UnableToAssess, model.detect(text))
        for (text in listOf("\u0000", "hello\uD800", "hello\uDC00", "x".repeat(10001)))
            assertEquals("invalid input", Detection.Failure, model.detect(text))
        assertTrue(model.automaticWarningsAllowed)
        assertEquals(.5, model.threshold, 0.0)
        assertTrue(DecisionPolicy(.5, inclusive = true).suspicious(.5))
        for (change in listOf<(JSONObject) -> Unit>(
            { it.put("schema_version", 8) }, { it.put("threshold", .4) }, { it.put("tf", "sublinear") },
            { it.put("input_view", "masked") }, { it.put("probability_approved", true) },
            { it.put("classes", JSONArray("[\"smishing\",\"ham\"]")) },
            { it.put("weights", JSONArray("[0]")) }, { it.put("bias", "NaN") },
            { it.put("token_pattern", "\\w+") }, { it.put("stop_words", JSONArray()) }
        )) {
            val bad = JSONObject(json); change(bad)
            assertThrows(Exception::class.java) { NbGeneralizationDetector.parse(bad.toString()) }
        }
        latencies.sort()
        return JSONObject().put("cases", cases.length()).put("held_out_cases", heldOut)
            .put("held_out_assessed", assessed).put("held_out_abstained", abstained)
            .put("maximum_score_error", maximumScoreError).put("maximum_feature_error", maximumFeatureError)
            .put("load_ms", loadMs).put("score_p50_ms", latencies[latencies.size / 2])
            .put("score_p95_ms", latencies[(latencies.size * .95).toInt()]).put("score_max_ms", latencies.last())
    }
}
