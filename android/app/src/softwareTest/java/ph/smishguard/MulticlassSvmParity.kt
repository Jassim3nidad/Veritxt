package ph.smishguard

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import ph.smishguard.model.*
import kotlin.math.abs

/** Shared host/Android checks against independent synthetic Python fixtures. */
object MulticlassSvmParity {
    suspend fun verify(json: String, fixture: String, trainingPercent: Int = 80): JSONObject {
        val started = System.nanoTime(); val model = MulticlassSvmDetector.parse(json, trainingPercent)
        val loadMs = (System.nanoTime() - started) / 1e6
        val f = JSONObject(fixture); val cases = f.getJSONArray("cases")
        assertTrue(f.getBoolean("independent_of_thesis_test")); assertEquals(0, f.getInt("thesis_messages_used"))
        assertEquals(if (trainingPercent == 60) MulticlassSvmDetector.SOURCE60_SHA256 else MulticlassSvmDetector.SOURCE_SHA256, f.getString("source_pipeline_sha256"))
        assertTrue(cases.length() >= if (trainingPercent == 60) 900 else 1000)
        val hash = java.security.MessageDigest.getInstance("SHA-256").digest(json.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }
        assertEquals(f.getString("model_sha256"), hash)
        var maximumScoreError = 0.0; var maximumFeatureError = 0.0; var matched = 0
        var successes = 0; var abstentions = 0; var rejected = 0
        val predicted = mutableSetOf<Int>(); val latencies = mutableListOf<Double>()
        for (i in 0 until cases.length()) {
            val c = cases.getJSONObject(i); val text = c.getString("text")
            assertEquals("terms ${c.getString("name")}", c.getJSONArray("terms").toString(), JSONArray(model.terms(text)).toString())
            val expected = c.getJSONObject("features"); val actual = model.features(text)
            assertEquals("features at $i", expected.keys().asSequence().map { it.toInt() }.toSet(), actual.keys)
            for ((k, value) in actual) {
                val error = abs(expected.getDouble(k.toString()) - value)
                maximumFeatureError = maxOf(maximumFeatureError, error)
                assertTrue("feature error at $i/$k", error <= 1e-10)
            }
            val tick = System.nanoTime(); val scores = model.scores(text)
            latencies.add((System.nanoTime() - tick) / 1e6)
            for (label in 0..2) {
                val error = abs(scores[label] - c.getJSONArray("scores").getDouble(label))
                maximumScoreError = maxOf(maximumScoreError, error)
                assertTrue("margin error at $i/$label", error <= 1e-10)
            }
            val label = MulticlassSvmDetector.winner(scores)
            assertEquals("class at $i", c.getInt("prediction"), label); matched++; predicted.add(label)
            when (val result = model.detect(text)) {
                is Detection.Success -> {
                    assertEquals("success boundary at $i", "success", c.getString("wrapper")); successes++
                    assertEquals(SmsCategory.entries[label], result.category)
                    assertEquals(label == 1, result.suspicious); assertFalse(result.probability)
                    assertNull(result.policy); assertEquals(scores, result.classScores)
                }
                Detection.UnableToAssess -> { assertEquals("unable", c.getString("wrapper")); abstentions++ }
                Detection.Failure -> { assertEquals("failure", c.getString("wrapper")); rejected++ }
                else -> fail("Unexpected wrapper at $i")
            }
        }
        assertEquals(setOf(0, 1, 2), predicted)
        assertEquals(0, MulticlassSvmDetector.winner(listOf(0.0, 0.0, 0.0)))
        assertEquals(1, MulticlassSvmDetector.winner(listOf(-3.0, -1.0, -1.0)))
        assertTrue(model.automaticWarningsAllowed)
        for (text in listOf("hello\uD800", "hello\uDC00")) assertEquals(Detection.Failure, model.detect(text))
        latencies.sort()
        return JSONObject().put("cases", cases.length()).put("matching_predictions", matched).put("mismatches", cases.length()-matched)
            .put("maximum_score_error", maximumScoreError).put("maximum_feature_error", maximumFeatureError)
            .put("wrapper_successes", successes).put("wrapper_abstentions", abstentions).put("wrapper_rejections", rejected)
            .put("thesis_test_messages_used", 0).put("tolerance", 1e-10).put("load_ms", loadMs)
            .put("score_p50_ms", latencies[latencies.size/2]).put("score_p95_ms", latencies[(latencies.size*.95).toInt()])
    }
}
