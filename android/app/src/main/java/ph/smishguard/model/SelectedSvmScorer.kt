package ph.smishguard.model

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import org.json.JSONObject
import kotlin.math.exp
import kotlin.math.sqrt

/** Frozen training contract shared by app inference and Python parity checks. */
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
