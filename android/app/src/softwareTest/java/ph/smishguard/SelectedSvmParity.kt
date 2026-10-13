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

/** Test-only selected-model contract. This source never enters the application APK. */
class SelectedSvmScorer private constructor(
    val tokenizer: PythonUnicode, private val stopWords: Set<String>,
    private val vocabulary: Map<String, Int>, private val idf: DoubleArray,
    private val weights: DoubleArray, private val bias: Double,
    private val a: Double, private val b: Double, val threshold: Double
) {
    fun terms(text: String): List<String> {
        val tokens = tokenizer.tokens(text).filter { it.codePointCount(0, it.length) >= 2 && it !in stopWords }
        // Filter stopwords before n-grams; preserve unknown words when forming adjacency.
        return tokens + tokens.zipWithNext { left, right -> "$left $right" }
    }
    suspend fun features(text: String): Map<Int, Double> {
        val counts = mutableMapOf<Int, Double>()
        for (term in terms(text)) {
            currentCoroutineContext().ensureActive()
            vocabulary[term]?.let { counts[it] = (counts[it] ?: 0.0) + 1.0 }
        }
        var norm = 0.0
        counts.replaceAll { index, count -> (count * idf[index]).also { norm += it * it } }
        norm = sqrt(norm)
        if (norm > 0.0) counts.replaceAll { _, value -> value / norm }
        return counts
    }
    suspend fun score(text: String): Double {
        var margin = bias
        for ((index, value) in features(text)) margin += weights[index] * value
        val calibrated = a * margin + b
        return (if (calibrated >= 0.0) 1.0 / (1.0 + exp(-calibrated)) else exp(calibrated) / (1.0 + exp(calibrated)))
            .also { require(it.isFinite() && it in 0.0..1.0) }
    }
    suspend fun detect(text: String): Detection {
        if (text.length > MAX_MESSAGE_LENGTH) return Detection.Failure
        val outsideLinks = tokenizer.tokens(Assessability.textOutsideLinks(text))
        if (!Assessability.canAssess(outsideLinks) { vocabulary.containsKey(it) }) return Detection.UnableToAssess
        val score = score(text)
        val policy = DecisionPolicy(threshold, inclusive = true)
        return Detection.Success(policy.suspicious(score), score, probability = false, experimental = true, policy = policy)
    }
    companion object {
        fun parse(json: String): SelectedSvmScorer {
            val o = JSONObject(json)
            require(o.getInt("schema_version") == 6 && o.getString("research_contract") == "unicode-stopword-svm-v1")
            require(o.getString("algorithm") == "svm" && o.getString("input_view") == "already_masked_case_preserving_text")
            require(o.getString("preprocessing_version") == "python-unicode-15-word-min2-english-v1")
            require(o.getInt("minimum_token_codepoints") == 2)
            require(o.getJSONArray("ngram_range").toString() == "[1,2]")
            require(o.getString("normalization") == "l2" && o.getString("term_frequency") == "raw")
            require(o.getJSONArray("classes").toString() == "[\"ham\",\"smishing\"]" && o.getString("positive_class") == "smishing")
            require(o.getString("threshold_comparison") == "greater_or_equal")
            require(o.getString("evaluation_status") == "retrospective_unverified_labels" && o.getString("calibration_status") == "fitted_unvalidated")
            require(!o.getBoolean("automatic_warnings_approved") && !o.getBoolean("probability_approved"))
            val tokenizer = PythonUnicode.parse(o.getJSONObject("unicode"))
            val stop = o.getJSONArray("stop_words")
            require(stop.length() == 318)
            val stopWords = (0 until stop.length()).map { stop.getString(it) }.toSet()
            require(stopWords.size == stop.length())
            val words = o.getJSONArray("vocabulary")
            require(words.length() in 1..50000)
            val vocabulary = (0 until words.length()).associate { words.getString(it) to it }
            require(vocabulary.size == words.length())
            require(vocabulary.keys.all { term -> tokenizer.tokens(term).let { ts ->
                ts.size in 1..2 && ts.all { it.codePointCount(0, it.length) >= 2 && it !in stopWords } && ts.joinToString(" ") == term
            } })
            fun array(name: String): DoubleArray {
                val array = o.getJSONArray(name); require(array.length() == words.length())
                return DoubleArray(array.length()) { array.getDouble(it).also { number -> require(number.isFinite()) } }
            }
            val idf = array("idf").also { require(it.all { number -> number > 0.0 }) }
            val bias = o.getDouble("bias").also { require(it.isFinite()) }
            val threshold = o.getDouble("threshold").also { require(it.isFinite() && it in 0.0..1.0) }
            val calibration = o.getJSONObject("calibration")
            val a = calibration.getDouble("a").also { require(it.isFinite() && it > 0.0) }
            val b = calibration.getDouble("b").also { require(it.isFinite()) }
            return SelectedSvmScorer(tokenizer, stopWords, vocabulary, idf, array("weights"), bias, a, b, threshold)
        }
    }
}

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
