package ph.smishguard

import java.io.File
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assume.assumeTrue
import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.Detection
import ph.smishguard.model.ResearchLinearScorer
import ph.smishguard.model.ResearchLinearRawDetector
import ph.smishguard.model.ModelLoader

class ResearchLinearParityTest {
    @Test fun actualCandidateMatchesPythonFeaturesAndScores() = runBlocking {
        val dir = System.getProperty("smishguard.parity.dir")
        assumeTrue("Actual research export required", dir != null && File(dir,"candidate-model.json").isFile)
        val root = File(dir!!); val json = File(root,"candidate-model.json").readText()
        val start = System.nanoTime(); val model = ResearchLinearScorer.parse(json)
        val loadMs = (System.nanoTime() - start) / 1e6
        val cases = JSONObject(File(root,"candidate-cases.json").readText()).getJSONArray("cases")
        var maxScore = 0.0; var maxFeature = 0.0; var latency = 0.0
        for (j in 0 until cases.length()) {
            val c = cases.getJSONObject(j); val text = c.getString("text")
            val expected = c.getJSONObject("features"); val actual = model.features(text)
            val keys = expected.keys().asSequence().map { it.toInt() }.toSet() + actual.keys
            for (key in keys) {
                val error = kotlin.math.abs(expected.optDouble(key.toString(),0.0) - (actual[key] ?: 0.0))
                maxFeature = maxOf(maxFeature,error); assertTrue("Feature case $j/$key", error <= 1e-10)
            }
            val before = System.nanoTime(); val score = model.score(text)
            latency += (System.nanoTime()-before)/1e6
            val error = kotlin.math.abs(score - c.getDouble("score")); maxScore = maxOf(maxScore,error)
            assertTrue("Score case $j",error <= 1e-10)
            assertEquals(c.getBoolean("suspicious"),score >= model.threshold)
        }
        assertEquals(Detection.UnableToAssess,model.detect(""))
        assertEquals(Detection.UnableToAssess,model.detect("??? qzxv qzxv"))
        assertEquals(Detection.Failure,model.detect("\u0000"))
        assertEquals(Detection.Failure,model.detect("\uD800"))
        assertEquals(Detection.Failure,model.detect("x".repeat(10001)))
        assertFalse(model.automaticWarningsAllowed)
        assertThrows(Exception::class.java) { ModelLoader.parse(json) }
        var rawCases = 0
        var realCases = 0; var assessed = 0; var abstained = 0; var failed = 0
        if (File(root,"research-evaluation-cases.json").isFile) {
            val records = JSONObject(File(root,"research-evaluation-cases.json").readText()).getJSONArray("cases")
            realCases = records.length()
            for (i in 0 until records.length()) {
                val record = records.getJSONObject(i);val text = record.getString("text")
                assertEquals("Frozen real score at index $i",record.getDouble("score"),model.score(text),1e-10)
                when (val detection = model.detect(text)) {
                    is Detection.Success -> { assessed++;assertEquals(record.getDouble("score")>=model.threshold,detection.suspicious) }
                    Detection.UnableToAssess -> abstained++
                    else -> failed++
                }
            }
            assertEquals(realCases,assessed+abstained+failed)
            assertEquals(0,failed)
        }
        if (File(root,"research-raw-cases.json").isFile) {
            val raw = ResearchLinearRawDetector(json,File(root,"raw-sms-adapter.json").readText())
            val probes = JSONObject(File(root,"research-raw-cases.json").readText()).getJSONArray("cases")
            rawCases = probes.length()
            for (i in 0 until probes.length()) {
                val probe = probes.getJSONObject(i);val text = probe.getString("raw")
                assertEquals(probe.getString("view"),raw.view(text))
                assertEquals(probe.getDouble("score"),raw.score(text),1e-10)
            }
            assertEquals(Detection.UnableToAssess,raw.detect(""))
            assertEquals(Detection.Failure,raw.detect("x".repeat(10001)))
        }
        for (mutate in listOf<(JSONObject)->Unit>(
            { it.put("probability_approved",true) },{ it.put("automatic_warnings_approved",true) },
            { it.put("classes",JSONArray("[\"smishing\",\"ham\"]")) },
            { it.put("weights",JSONArray("[0]")) },{ it.put("threshold","NaN") },
            { it.getJSONArray("blocks").getJSONObject(0).put("norm","l1") }
        )) {
            val bad = JSONObject(json); mutate(bad)
            assertThrows(Exception::class.java) { ResearchLinearScorer.parse(bad.toString()) }
        }
        File(root,"research-jvm-parity.json").writeText(JSONObject()
            .put("cases",cases.length()).put("max_score_error",maxScore).put("max_feature_error",maxFeature)
            .put("load_ms",loadMs).put("mean_synthetic_score_ms",latency/cases.length())
            .put("raw_sms_adapter_cases",rawCases)
            .put("real_masked_cases",realCases).put("assessed",assessed).put("abstained",abstained).put("failed",failed)
            .put("candidate_json_bytes",json.toByteArray().size).put("production_pointer_changed",false).toString(2))
    }
}
