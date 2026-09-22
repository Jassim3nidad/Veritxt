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
    fun tokens(text: String): List<String> {
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
        val result = mutableListOf<String>(); val token = StringBuilder()
        lowered.toString().codePoints().forEach { cp ->
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

/** Experimental full-dataset LR export: software compatibility is not research approval. */
class SuppliedDetector private constructor(
    private val vocabulary: Map<String, Int>, private val idf: DoubleArray,
    private val weights: DoubleArray, private val bias: Double, val tokenizer: PythonUnicode
) : Detector {
    override val status = "Experimental model · unverified performance"
    override suspend fun detect(text: String): Detection {
        if (text.isBlank() || text.length > MAX_MESSAGE_LENGTH) return Detection.Failure
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
        var margin = bias
        if (norm > 0) for ((i, value) in counts) margin += weights[i] * value / norm
        val score = if (margin >= 0) 1.0 / (1.0 + exp(-margin)) else exp(margin) / (1.0 + exp(margin))
        if (!score.isFinite()) return Detection.Failure
        return Detection.Success(score > .5, score, experimental = true)
    }
    companion object {
        fun parse(json: String): SuppliedDetector {
            val o = JSONObject(json)
            require(o.getInt("schema_version") == 2 && o.getString("preprocessing_version") == "python-unicode-word-v2")
            require(o.getString("feature_type") == "word-unigram-bigram-tfidf-l2")
            require(o.getJSONArray("classes").toString() == "[\"ham\",\"smishing\"]" && o.getString("positive_class") == "smishing")
            require(o.getJSONArray("ngram_range").toString() == "[1,2]" && o.getBoolean("lowercase"))
            require(o.getString("token_pattern") == "\\b\\w+\\b")
            require(o.getString("term_frequency") == "raw" && o.getString("normalization") == "l2" && o.getString("score_transform") == "sigmoid")
            require(o.getDouble("threshold") == .5 && o.getString("threshold_comparison") == "strict_greater")
            require(!o.getBoolean("synthetic") && !o.getBoolean("automatic_warnings_approved"))
            require(o.getString("evaluation_status") == "unverified" && o.getString("calibration_status") == "uncalibrated")
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
            return SuppliedDetector(vocabulary, idf, array("weights"), o.getDouble("bias").also { require(it.isFinite()) }, tokenizer)
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
