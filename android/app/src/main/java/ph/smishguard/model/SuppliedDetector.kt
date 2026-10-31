package ph.smishguard.model

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import org.json.JSONObject
import kotlin.math.exp
import kotlin.math.sqrt

/** Frozen Python Unicode tables avoid Android/JVM regex and Unicode-version differences. */
class PythonUnicode private constructor(
    private val words: List<IntRange>, private val cased: List<IntRange>,
    private val ignorable: List<IntRange>, private val lower: Map<Int, String>
) {
    private fun contains(ranges: List<IntRange>, cp: Int): Boolean {
        var lo = 0; var hi = ranges.lastIndex
        while (lo <= hi) {
            val mid = (lo + hi) / 2; val range = ranges[mid]
            when { cp < range.first -> hi = mid - 1; cp > range.last -> lo = mid + 1; else -> return true }
        }
        return false
    }
    fun lowercase(text: String): String {
        val codepoints = text.codePoints().toArray()
        val lowered = StringBuilder()
        for (i in codepoints.indices) {
            val cp = codepoints[i]
            if (cp == 0x03A3) {
                var before = i - 1; var after = i + 1
                while (before >= 0 && contains(ignorable, codepoints[before])) before--
                while (after < codepoints.size && contains(ignorable, codepoints[after])) after++
                val final = before >= 0 && contains(cased, codepoints[before]) &&
                    (after == codepoints.size || !contains(cased, codepoints[after]))
                lowered.appendCodePoint(if (final) 0x03C2 else 0x03C3)
            } else lowered.append(lower[cp] ?: String(Character.toChars(cp)))
        }
        return lowered.toString()
    }
    fun tokens(text: String): List<String> {
        val result = mutableListOf<String>(); val token = StringBuilder()
        lowercase(text).codePoints().forEach { cp ->
            if (contains(words, cp)) token.appendCodePoint(cp)
            else if (token.isNotEmpty()) { result.add(token.toString()); token.clear() }
        }
        if (token.isNotEmpty()) result.add(token.toString())
        return result
    }
    companion object {
        fun parse(o: JSONObject): PythonUnicode {
            require(o.getString("unicode_version") == "15.0.0")
            fun ranges(key: String): List<IntRange> {
                val input = o.getJSONArray(key); require(input.length() in 1..5000)
                var previous = -1
                return List(input.length()) { i ->
                    val pair = input.getJSONArray(i); require(pair.length() == 2)
                    val first = pair.getInt(0); val last = pair.getInt(1)
                    require(first > previous && last >= first && last <= 0x10FFFF)
                    previous = last; first..last
                }
            }
            val map = o.getJSONObject("lowercase_map"); require(map.length() in 1..5000)
            val lower = map.keys().asSequence().associate { key ->
                val cp = key.toInt(); require(cp in 0..0x10FFFF)
                cp to map.getString(key).also { require(it.isNotEmpty() && it.length <= 4) }
            }
            return PythonUnicode(ranges("word_ranges"), ranges("cased_ranges"), ranges("case_ignorable_ranges"), lower)
        }
    }
}

/** Experimental supplied LR exports: software compatibility is not research approval. */
class SuppliedDetector private constructor(
    private val vocabulary: Map<String, Int>, private val idf: DoubleArray,
    private val weights: DoubleArray, private val bias: Double, val tokenizer: PythonUnicode,
    private val calibrationA: Double = 1.0, private val calibrationB: Double = 0.0,
    private val candidate: Boolean = false, private val folded: Boolean = false
) : Detector {
    override val status = "Experimental model · unverified performance"
    // Team decision (2026-10-12): warn automatically on incoming SMS with this model. Its results stay labelled
    // experimental and uncalibrated in the app; research evaluation is still pending (docs/model-contract.md).
    override val automaticWarningsAllowed = !candidate && !folded
    override suspend fun detect(text: String): Detection {
        if (text.length > MAX_MESSAGE_LENGTH) return Detection.Failure
        val words = tokenizer.tokens(Assessability.textOutsideLinks(text))
        if (!Assessability.canAssess(words) { vocabulary.containsKey(it) }) return Detection.UnableToAssess
        return rawDetection(text)
    }
    // Preserve the original mathematical path for independent export parity checks.
    // Production callers must use detect(), which applies abstention first.
    internal suspend fun rawDetection(text: String): Detection {
        if (text.isBlank() || text.length > MAX_MESSAGE_LENGTH) return Detection.Failure
        val features = featureValues(text)
        var margin = bias
        for ((i, value) in features) margin += weights[i] * value
        margin = calibrationA * margin + calibrationB
        val score = if (margin >= 0) 1.0 / (1.0 + exp(-margin)) else exp(margin) / (1.0 + exp(margin))
        if (!score.isFinite()) return Detection.Failure
        val policy = DecisionPolicy(if (candidate) .4 else .5, inclusive = candidate)
        return Detection.Success(policy.suspicious(score), score, experimental = true, policy = policy)
    }
    internal suspend fun featureValues(text: String): Map<Int, Double> {
        val tokens = tokenizer.tokens(text)
        val counts = HashMap<Int, Double>()
        fun add(term: String) { vocabulary[term]?.let { counts[it] = (counts[it] ?: 0.0) + 1.0 } }
        for (i in tokens.indices) {
            currentCoroutineContext().ensureActive()
            add(tokens[i]); if (i > 0) add(tokens[i - 1] + " " + tokens[i])
        }
        var norm = 0.0
        counts.replaceAll { i, count -> (count * idf[i]).also { norm += it * it } }
        norm = sqrt(norm)
        if (norm > 0) counts.replaceAll { _, value -> value / norm }
        return counts
    }
    companion object {
        internal fun isSuspicious(score: Double, candidate: Boolean): Boolean =
            if (candidate) score >= .4 else score > .5

        fun parse(json: String, candidate: Boolean = false, folded: Boolean = false): SuppliedDetector {
            require(!(candidate && folded))
            val o = JSONObject(json)
            require(o.getInt("schema_version") == (if (folded) 4 else if (candidate) 3 else 2) && o.getString("preprocessing_version") == "python-unicode-word-v2")
            require(o.getString("feature_type") == "word-unigram-bigram-tfidf-l2")
            require(o.getJSONArray("classes").toString() == "[\"ham\",\"smishing\"]" && o.getString("positive_class") == "smishing")
            require(o.getJSONArray("ngram_range").toString() == "[1,2]" && o.getBoolean("lowercase"))
            require(o.getString("token_pattern") == "\\b\\w+\\b")
            require(o.getString("term_frequency") == "raw" && o.getString("normalization") == "l2" && o.getString("score_transform") == "sigmoid")
            require(o.getDouble("threshold") == (if (candidate) .4 else .5))
            require(o.getString("threshold_comparison") == (if (candidate) "greater_or_equal" else "strict_greater"))
            require(!o.getBoolean("synthetic") && !o.getBoolean("automatic_warnings_approved"))
            require(o.getString("evaluation_status") == "unverified")
            require(o.getString("calibration_status") == (if (candidate || folded) "fitted_unvalidated" else "uncalibrated"))
            if (folded) {
                require(o.getString("algorithm") == "lr" && o.getString("model_version") == "lr-calibrated-4")
                require(o.getString("calibration_encoding") == "folded_into_parameters")
                // Applying source a/b here would calibrate twice. Schema v4 forbids it.
                require(!o.has("calibration") && !o.has("calibration_a") && !o.has("calibration_b"))
            }
            val calibration = if (candidate) {
                require(o.getString("algorithm") == "lr" && o.getString("model_version").isNotBlank())
                o.getJSONObject("calibration").let { Pair(it.getDouble("a"), it.getDouble("b")) }.also {
                    require(it.first.isFinite() && it.first > 0 && it.second.isFinite())
                }
            } else Pair(1.0, 0.0)
            require(o.getString("intended_use") == "manual_development" && o.getString("technical_compatibility") == "reference_verified")
            val provenance = o.getJSONObject("provenance")
            require(provenance.getString("kind") == "user_supplied_export")
            require(Regex("[0-9a-f]{64}").matches(provenance.getString("source_sha256")))
            val tokenizer = PythonUnicode.parse(o.getJSONObject("unicode"))
            val words = o.getJSONArray("vocabulary"); require(words.length() in 1..50000)
            val vocabulary = (0 until words.length()).associate { words.getString(it) to it }
            require(vocabulary.size == words.length())
            require(vocabulary.keys.all { term -> tokenizer.tokens(term).let { it.size in 1..2 && it.joinToString(" ") == term } })
            fun array(key: String): DoubleArray {
                val a = o.getJSONArray(key); require(a.length() == words.length())
                return DoubleArray(a.length()) { a.getDouble(it).also { value -> require(value.isFinite()) } }
            }
            val idf = array("idf"); require(idf.all { it > 0.0 })
            return SuppliedDetector(vocabulary, idf, array("weights"), o.getDouble("bias").also { require(it.isFinite()) },
                tokenizer, calibration.first, calibration.second, candidate, folded)
        }
    }
}

object ModelLoader {
    fun parse(json: String): Detector = when (JSONObject(json).getInt("schema_version")) {
        1 -> LinearDetector.parse(json)
        2 -> SuppliedDetector.parse(json)
        else -> throw IllegalArgumentException("Unsupported model schema")
    }
}
