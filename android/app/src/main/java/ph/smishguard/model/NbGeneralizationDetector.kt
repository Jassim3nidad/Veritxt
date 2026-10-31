package ph.smishguard.model

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.exp
import kotlin.math.sqrt

/** Exact raw-SMS TF-IDF + MultinomialNB log odds from the frozen 80/20 fold.
 * URLs, amounts and numbers remain intact, as in training. No masking adapter.
 */
class NbGeneralizationDetector private constructor(
    private val unicode: PythonUnicode,
    private val whitespace: List<IntRange>, private val wordRanges: List<IntRange>,
    private val digitRanges: List<IntRange>,
    private val stopWords: Set<String>, private val vocabulary: Map<String, Int>,
    private val idf: DoubleArray, private val weights: DoubleArray, private val bias: Double
) : Detector {
    override val status = "Experimental · Naive Bayes · 80/20 retrained"
    // Retain the existing experimental incoming-SMS feature and its consent controls.
    // This app policy does not approve probability calibration or research labels.
    override val automaticWarningsAllowed = true
    val threshold = .5

    private fun contains(ranges: List<IntRange>, cp: Int): Boolean {
        var lo = 0; var hi = ranges.lastIndex
        while (lo <= hi) {
            val mid = (lo + hi) / 2; val range = ranges[mid]
            when { cp < range.first -> hi = mid - 1; cp > range.last -> lo = mid + 1; else -> return true }
        }
        return false
    }

    private fun normalize(text: String): String {
        val result = StringBuilder()
        var pendingSpace = false
        text.codePoints().forEach { cp ->
            if (contains(whitespace, cp)) pendingSpace = result.isNotEmpty()
            else {
                if (pendingSpace) result.append(' ')
                result.appendCodePoint(cp); pendingSpace = false
            }
        }
        return unicode.lowercase(result.toString())
    }

    fun terms(text: String): List<String> {
        val points = normalize(text).codePoints().toArray()
        val tokens = mutableListOf<String>()
        fun word(i: Int) = i in points.indices && contains(wordRanges, points[i])
        fun digit(i: Int) = i in points.indices && contains(digitRanges, points[i])
        fun prefix(start: Int, value: String): Boolean = start + value.length <= points.size &&
            value.indices.all { points[start + it] == value[it].code }
        // Possible regex backtracking endpoints, longest first. In "12.34abc",
        // Python's numeric branch backs up to "12" before the dot.
        fun numberEnds(start: Int): List<Int> {
            val ends = mutableListOf<Int>(); var end = start
            if (!digit(end)) return ends
            while (digit(end)) { end++; ends.add(end) }
            while (end + 1 < points.size && points[end] in listOf('.'.code, ','.code) && digit(end + 1)) {
                end++
                while (digit(end)) { end++; ends.add(end) }
            }
            return ends
        }
        var position = 0
        while (position < points.size) {
            var end = -1
            val urlPrefix = listOf("https://", "http://", "www.").firstOrNull { prefix(position, it) }
            if (urlPrefix != null) {
                var tail = position + urlPrefix.length
                val body = tail
                while (tail < points.size && points[tail] !in listOf(' '.code, '<'.code, '>'.code)) tail++
                if (tail > body) end = tail
            }
            if (end < 0 && points[position] in listOf('₱'.code, '$'.code, '€'.code, '£'.code)) {
                var start = position + 1
                if (start < points.size && points[start] == ' '.code) start++
                end = numberEnds(start).lastOrNull() ?: -1
            }
            if (end < 0 && !word(position - 1) && digit(position))
                end = numberEnds(position).lastOrNull { !word(it) } ?: -1
            if (end < 0 && !word(position - 1) && word(position)) {
                end = position + 1
                while (word(end)) end++
            }
            if (end > position) {
                val token = String(points, position, end - position)
                if (token !in stopWords) tokens.add(token)
                position = end
            } else position++
        }
        // sklearn filters stopwords before forming adjacent bigrams.
        return tokens + tokens.zipWithNext { a, b -> "$a $b" }
    }

    suspend fun features(text: String): Map<Int, Double> {
        val counts = linkedMapOf<Int, Double>()
        for (term in terms(text)) {
            currentCoroutineContext().ensureActive()
            vocabulary[term]?.let { counts[it] = (counts[it] ?: 0.0) + 1.0 }
        }
        var norm = 0.0
        counts.replaceAll { i, count -> (count * idf[i]).also { norm += it * it } }
        norm = sqrt(norm)
        if (norm > 0.0) counts.replaceAll { _, value -> value / norm }
        return counts
    }

    /** Mathematical score, including the prior for zero features; detect applies abstention. */
    suspend fun score(text: String): Double {
        var margin = bias
        for ((i, value) in features(text)) margin += weights[i] * value
        return (if (margin >= 0) 1.0 / (1.0 + exp(-margin)) else exp(margin) / (1.0 + exp(margin)))
            .also { require(it.isFinite() && it in 0.0..1.0) }
    }

    override suspend fun detect(text: String): Detection {
        if (text.length > MAX_MESSAGE_LENGTH || '\u0000' in text ||
            text.codePoints().anyMatch { it in 0xD800..0xDFFF }) return Detection.Failure
        val words = unicode.tokens(Assessability.textOutsideLinks(text))
        if (!Assessability.canAssess(words) { vocabulary.containsKey(it) }) return Detection.UnableToAssess
        val score = score(text)
        val policy = DecisionPolicy(threshold, inclusive = true)
        return Detection.Success(policy.suspicious(score), score, probability = false, experimental = true, policy = policy)
    }

    companion object {
        private const val CONTRACT = "raw-unicode-url-amount-nb-android-v1"
        private const val TOKEN_PATTERN = """(?u)https?://[^\s<>]+|www\.[^\s<>]+|[₱$€£]\s?\d+(?:[,.]\d+)*|\b\d+(?:[,.]\d+)*\b|\b\w+\b"""
        private val STOP_WORDS = setOf("from", "the", "their", "theirs", "these", "those", "which", "whom", "whose", "with", "yours", "yourself", "yourselves")

        private fun ranges(input: JSONArray): List<IntRange> {
            require(input.length() in 1..5000)
            var previous = -1
            return List(input.length()) { i ->
                val pair = input.getJSONArray(i); require(pair.length() == 2)
                val first = pair.getInt(0); val last = pair.getInt(1)
                require(first > previous && last >= first && last <= 0x10FFFF)
                previous = last; first..last
            }
        }

        fun parse(json: String): NbGeneralizationDetector {
            val o = JSONObject(json)
            require(o.getInt("schema_version") == 9 && o.getString("research_contract") == CONTRACT)
            require(o.getString("model_version") == "nb-generalization-20261019-fold0-alpha0.1")
            require(o.getString("algorithm") == "nb" && o.getString("input_view") == "raw_sms")
            require(o.getJSONArray("classes").toString() == "[\"ham\",\"smishing\"]" && o.getString("positive_class") == "smishing")
            require(o.getJSONArray("ngram_range").toString() == "[1,2]")
            require(o.getString("token_pattern") == TOKEN_PATTERN && o.getString("unicode_version") == "15.0.0")
            require(o.getString("normalize") == "collapse Unicode whitespace, Python Unicode lowercase")
            require(o.getString("tf") == "raw" && o.getString("norm") == "l2" && o.getString("score") == "sigmoid log odds")
            require(o.getDouble("threshold") == .5 && o.getString("threshold_comparison") == "greater_or_equal")
            require(o.getBoolean("android_compatible") && !o.getBoolean("probability_approved") && !o.getBoolean("automatic_warnings_approved"))
            require(o.getString("evaluation_status") == "retrospective_unverified_labels" && o.getString("calibration_status") == "uncalibrated")
            val provenance = o.getJSONObject("provenance")
            require(provenance.getString("fold") == "group-fold-0" && provenance.getInt("training_records") == 2734 && provenance.getInt("held_out_records") == 684)
            for (key in listOf("pipeline_sha256", "freeze_sha256", "dataset_sha256"))
                require(provenance.getString(key).matches(Regex("[0-9a-f]{64}")))
            val stop = o.getJSONArray("stop_words")
            require(stop.length() == STOP_WORDS.size && (0 until stop.length()).map { stop.getString(it) }.toSet() == STOP_WORDS)
            val u = o.getJSONObject("unicode")
            val unicode = PythonUnicode.parse(u)
            val word = ranges(u.getJSONArray("word_ranges"))
            val digit = ranges(o.getJSONArray("digit_ranges"))
            val whitespace = ranges(o.getJSONArray("whitespace_ranges"))
            val words = o.getJSONArray("vocabulary"); require(words.length() in 1..100000)
            val vocabulary = (0 until words.length()).associate { words.getString(it) to it }
            require(vocabulary.size == words.length() && vocabulary.keys.all { it.isNotEmpty() })
            fun array(key: String): DoubleArray {
                val values = o.getJSONArray(key); require(values.length() == words.length())
                return DoubleArray(values.length()) { values.getDouble(it).also { number -> require(number.isFinite()) } }
            }
            val idf = array("idf"); require(idf.all { it > 0.0 })
            val weights = array("weights"); val bias = o.getDouble("bias").also { require(it.isFinite()) }
            return NbGeneralizationDetector(unicode, whitespace, word, digit, STOP_WORDS, vocabulary, idf, weights, bias)
        }
    }
}
