package ph.smishguard

import org.json.JSONObject
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test
import org.junit.Assume.assumeTrue
import kotlinx.coroutines.runBlocking
import java.io.File
import ph.smishguard.model.*

class RiskEvaluationTest {
    @Test fun evaluateAvailableFrozenModelsOnTheLabeledScenarios() = runBlocking {
        val module = listOf(File("."), File("android/app")).firstOrNull { File(it, "src/main/AndroidManifest.xml").isFile }
        assumeTrue("Private model assets are optional in public checkouts", module != null)
        val models = mutableListOf<Pair<String, Detector>>()
        val supplied = File(module, "src/development/assets/model.json")
        if (supplied.isFile) models += "development" to ModelLoader.parse(supplied.readText())
        val svm = File(module, "src/selectedSvm/assets/model.json")
        val adapter = File(module, "src/selectedSvm/assets/raw-sms-adapter.json")
        if (svm.isFile && adapter.isFile) models += "selectedSvm" to SelectedSvmDetector(svm.readText(), adapter.readText())
        assumeTrue("No private frozen models configured", models.isNotEmpty())
        val fixture = JSONObject(javaClass.getResource("/risk-evaluation-cases.json")!!.readText())
        val cases = fixture.getJSONArray("cases")
        val summaries = JSONArray()
        for ((name, model) in models) {
            var tp = 0; var tn = 0; var fp = 0; var fn = 0; var abstentions = 0; var insufficient = 0
            var highLegitimate = 0; var highMalicious = 0
            val levels = mutableMapOf<String, Int>()
            for (i in 0 until cases.length()) {
                val case = cases.getJSONObject(i)
                val text = case.getString("text")
                val assessment = RiskPolicy.assess(text, model.detect(text))
                levels[assessment.level.name] = (levels[assessment.level.name] ?: 0) + 1
                val positive = assessment.level in setOf(RiskLevel.MEDIUM, RiskLevel.HIGH)
                if (case.getString("label") == "insufficient") { insufficient++; assertNull(assessment.score); continue }
                if (assessment.score == null) abstentions++
                when (case.getString("label")) {
                    "legitimate" -> if (positive) fp++ else tn++
                    "malicious" -> if (positive) tp++ else fn++
                }
                if (assessment.level == RiskLevel.HIGH) {
                    if (case.getString("label") == "legitimate") highLegitimate++ else highMalicious++
                }
            }
            summaries.put(JSONObject().put("model", name).put("true_positive", tp).put("true_negative", tn)
                .put("false_positive", fp).put("false_negative", fn).put("assessable_scenario_abstentions", abstentions)
                .put("insufficient_cases", insufficient).put("risk_level_counts", JSONObject(levels))
                .put("high_risk_legitimate", highLegitimate).put("high_risk_malicious", highMalicious))
        }
        println("RISK_ACTUAL_MODEL_JSON=" + JSONObject().put("policy_version", RiskPolicy.VERSION)
            .put("scope", "Actual frozen local models on 38 authored fictional scenarios; not independent or representative validation. Medium or High Risk is positive; abstained malicious scenarios count as missed.")
            .put("models", summaries))
    }

    @Test fun evaluateLabeledRegressionScenariosAndReportErrors() {
        val fixture = JSONObject(javaClass.getResource("/risk-evaluation-cases.json")!!.readText())
        val cases = fixture.getJSONArray("cases")
        var tp = 0; var fp = 0; var tn = 0; var fn = 0; var abstentions = 0
        val outcomes = JSONArray()
        for (i in 0 until cases.length()) {
            val case = cases.getJSONObject(i)
            val flag = case.getBoolean("flag")
            val result = RiskPolicy.assess(case.getString("text"), Detection.Success(flag, if (flag) .93 else .12))
            assertEquals(case.getString("id"), RiskLevel.valueOf(case.getString("expected")), result.level)
            val positive = result.level in setOf(RiskLevel.MEDIUM, RiskLevel.HIGH)
            when (case.getString("label")) {
                "legitimate" -> if (positive) fp++ else tn++
                "malicious" -> if (positive) tp++ else fn++
                else -> { abstentions++; assertNull(result.score) }
            }
            outcomes.put(JSONObject().put("id", case.getString("id")).put("label", case.getString("label"))
                .put("risk_level", result.level.name).put("risk_score", result.score ?: JSONObject.NULL))
        }
        println("RISK_EVALUATION_JSON=" + JSONObject().put("policy_version", RiskPolicy.VERSION)
            .put("provenance", fixture.getString("provenance"))
            .put("positive_definition", "Medium or High Risk; injected model decisions")
            .put("true_positive", tp).put("false_positive", fp).put("true_negative", tn).put("false_negative", fn)
            .put("insufficient_cases", abstentions).put("outcomes", outcomes))
        assertEquals(38, cases.length())
        assertEquals(2, fp) // Legitimate credential entry and payment requests need verification too.
        assertEquals(2, fn) // Context-free conversational lures expose a known limitation.
    }
}
