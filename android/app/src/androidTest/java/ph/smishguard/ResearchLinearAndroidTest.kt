package ph.smishguard

import android.Manifest
import android.content.pm.PackageManager
import android.os.Debug
import android.provider.Settings
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.Detection
import ph.smishguard.model.ResearchLinearScorer
import ph.smishguard.model.ResearchLinearRawDetector

class ResearchLinearAndroidTest {
    @Test fun actualResearchExportMatchesPythonOffline() = runBlocking {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        assumeTrue(InstrumentationRegistry.getArguments().getString("researchParity") == "true")
        val context = instrumentation.targetContext
        assertEquals(1,Settings.Global.getInt(context.contentResolver,Settings.Global.AIRPLANE_MODE_ON))
        assertEquals(PackageManager.PERMISSION_DENIED,context.checkSelfPermission(Manifest.permission.INTERNET))
        fun asset(name: String) = instrumentation.context.assets.open(name).bufferedReader().use { it.readText() }
        val before = Debug.getPss(); val start = System.nanoTime()
        val model = ResearchLinearScorer.parse(asset("candidate-model.json"))
        val loadMs = (System.nanoTime()-start)/1e6
        val cases = JSONObject(asset("candidate-cases.json")).getJSONArray("cases")
        var maximumScore = 0.0; var maximumFeature = 0.0
        val latencies = mutableListOf<Double>()
        for (j in 0 until cases.length()) {
            val c = cases.getJSONObject(j); val text = c.getString("text")
            val expected = c.getJSONObject("features"); val actual = model.features(text)
            for (key in expected.keys().asSequence().map { it.toInt() }.toSet() + actual.keys) {
                val error = kotlin.math.abs(expected.optDouble(key.toString(),0.0)-(actual[key] ?: 0.0))
                maximumFeature = maxOf(maximumFeature,error);assertTrue("Feature parity $j/$key",error<=1e-10)
            }
            val tick = System.nanoTime(); val score = model.score(text)
            latencies.add((System.nanoTime()-tick)/1e6)
            val error = kotlin.math.abs(score-c.getDouble("score"))
            maximumScore = maxOf(maximumScore,error);assertTrue("Score parity $j",error<=1e-10)
            assertEquals(c.getBoolean("suspicious"),score>=model.threshold)
        }
        assertEquals(Detection.UnableToAssess,model.detect(""))
        assertEquals(Detection.UnableToAssess,model.detect("qzxv qzxv ???"))
        assertEquals(Detection.Failure,model.detect("\u0000"))
        assertEquals(Detection.Failure,model.detect("\uD800"))
        assertFalse(model.automaticWarningsAllowed)
        val raw = ResearchLinearRawDetector(asset("candidate-model.json"),asset("raw-sms-adapter.json"))
        val probes = JSONObject(asset("research-raw-cases.json")).getJSONArray("cases")
        for (i in 0 until probes.length()) {
            val probe = probes.getJSONObject(i);val text = probe.getString("raw")
            assertEquals(probe.getString("view"),raw.view(text))
            assertEquals(probe.getDouble("score"),raw.score(text),1e-10)
        }
        val records = JSONObject(asset("research-evaluation-cases.json")).getJSONArray("cases")
        var assessed = 0; var abstained = 0; var failed = 0; var maxRealError = 0.0
        val realLatencies = mutableListOf<Double>()
        for (i in 0 until records.length()) {
            val record = records.getJSONObject(i);val text = record.getString("text")
            assertEquals("Idempotent masked input at index $i",text,raw.view(text))
            val error = kotlin.math.abs(model.score(text)-record.getDouble("score"))
            maxRealError = maxOf(maxRealError,error);assertTrue("Frozen real score $i",error<=1e-10)
            val tick = System.nanoTime(); val detection = model.detect(text)
            realLatencies.add((System.nanoTime()-tick)/1e6)
            when (detection) {
                is Detection.Success -> { assessed++;assertEquals(record.getDouble("score")>=model.threshold,detection.suspicious) }
                Detection.UnableToAssess -> abstained++
                else -> failed++
            }
        }
        assertEquals(records.length(),assessed+abstained+failed);assertEquals(0,failed)
        realLatencies.sort()
        latencies.sort()
        File(context.filesDir,"research-android-parity.json").writeText(JSONObject()
            .put("api",android.os.Build.VERSION.SDK_INT).put("offline",true).put("physical_device",false)
            .put("cases",cases.length()).put("max_score_error",maximumScore).put("max_feature_error",maximumFeature)
            .put("raw_sms_adapter_cases",probes.length())
            .put("real_masked_cases",records.length()).put("assessed",assessed).put("abstained",abstained).put("failed",failed)
            .put("max_real_score_error",maxRealError)
            .put("real_detection_p50_ms",realLatencies[realLatencies.size/2])
            .put("real_detection_p95_ms",realLatencies[(realLatencies.size*.95).toInt().coerceAtMost(realLatencies.lastIndex)])
            .put("load_ms",loadMs).put("synthetic_score_p50_ms",latencies[latencies.size/2])
            .put("synthetic_score_max_ms",latencies.last()).put("pss_kib_before",before).put("pss_kib_after",Debug.getPss())
            .put("memory_note","Whole instrumentation process samples, not isolated model memory")
            .put("production_pointer_changed",false).toString(2))
    }
}
