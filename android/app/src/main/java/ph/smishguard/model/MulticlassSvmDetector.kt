package ph.smishguard.model

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.sqrt

/** Exact frozen 60%/80% TF-IDF and three one-versus-rest margins; no masking or calibration. */
class MulticlassSvmDetector private constructor(
    val trainingPercent: Int,
    private val unicode: PythonUnicode,
    private val whitespace: List<IntRange>, private val wordRanges: List<IntRange>,
    private val digitRanges: List<IntRange>, private val stopWords: Set<String>,
    private val vocabulary: Map<String, Int>, private val idf: DoubleArray,
    private val coefficients: List<DoubleArray>, private val intercepts: DoubleArray
) : Detector {
    override val status = "Linear SVM · $trainingPercent% · Ham / Smishing / Gambling"
    // Preserve the existing experimental incoming-SMS consent and risk-policy gates.
    override val automaticWarningsAllowed = true

    private fun contains(ranges: List<IntRange>, cp: Int): Boolean {
        var lo = 0; var hi = ranges.lastIndex
        while (lo <= hi) {
            val mid = (lo + hi) / 2; val range = ranges[mid]
            when { cp < range.first -> hi = mid - 1; cp > range.last -> lo = mid + 1; else -> return true }
        }
        return false
    }

    private fun normalize(text: String): String {
        val result = StringBuilder(); var pendingSpace = false
        text.codePoints().forEach { cp ->
            if (contains(whitespace, cp)) pendingSpace = result.isNotEmpty()
            else {
                if (pendingSpace) result.append(' ')
                result.appendCodePoint(cp); pendingSpace = false
            }
        }
        return unicode.lowercase(result.toString())
    }

    /** Python regex alternation, word/digit boundaries and lowercase use frozen Unicode 15 tables. */
    fun terms(text: String): List<String> {
        val points = normalize(text).codePoints().toArray()
        val tokens = mutableListOf<String>()
        fun word(i: Int) = i in points.indices && contains(wordRanges, points[i])
        fun digit(i: Int) = i in points.indices && contains(digitRanges, points[i])
        fun prefix(start: Int, value: String): Boolean = start + value.length <= points.size &&
            value.indices.all { points[start + it] == value[it].code }
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
                var tail = position + urlPrefix.length; val body = tail
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
        // Unknown words remain in adjacency; stopwords are removed before bigrams.
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

    /** Mathematical pipeline path, including intercept-only predictions for blank/OOV text. */
    suspend fun scores(text: String): List<Double> {
        val result = intercepts.copyOf()
        for ((i, value) in features(text)) for (c in result.indices) result[c] += coefficients[c][i] * value
        require(result.all { it.isFinite() })
        return result.toList()
    }

    override suspend fun detect(text: String): Detection {
        if (text.length > MAX_MESSAGE_LENGTH || '\u0000' in text ||
            text.codePoints().anyMatch { it in 0xD800..0xDFFF }) return Detection.Failure
        // Existing app input boundaries are explicit; the mathematical parity path above still scores empty text.
        if (normalize(text).isEmpty()) return Detection.UnableToAssess
        val margins = scores(text); val label = winner(margins)
        return Detection.Success(suspicious = label == 1, score = margins[label], probability = false,
            experimental = true, category = SmsCategory.entries[label], classScores = margins)
    }

    companion object {
        const val VERSION = "veritxt-multiclass-20261020-svm-80-C10"
        const val SOURCE_SHA256 = "957fe1ef05885a81d909c495d23a06487908c07b891f204109fdd13b474f8104"
        const val ASSET_SHA256 = "ba6fc0bf7f32cd4405402534fdda408eed418072279928958ae4ba88c83894d6"
        const val SOURCE60_SHA256 = "73c996492889c846a396aba1b6f250eb3e488605104cb18c5318bb75c9dc605a"
        const val ASSET60_SHA256 = "3703fdb51583f090979ada04fc79201e58cbeb61b0a464cb6389b0baf5b07dd1"
        private const val TOKEN_PATTERN = """(?u)https?://[^\s<>]+|www\.[^\s<>]+|[₱$€£]\s?\d+(?:[,.]\d+)*|\b\d+(?:[,.]\d+)*\b|\b\w+\b"""
        private val STOP_WORDS = setOf("from", "the", "their", "theirs", "these", "those", "which", "whom", "whose", "with", "yours", "yourself", "yourselves")

        /** numpy.argmax chooses the first class at an exact tie; negative margins are valid. */
        internal fun winner(scores: List<Double>): Int {
            require(scores.size == 3 && scores.all { it.isFinite() })
            var best = 0
            for (i in 1..2) if (scores[i] > scores[best]) best = i
            return best
        }

        private fun ranges(input: JSONArray): List<IntRange> {
            require(input.length() in 1..5000); var previous = -1
            return List(input.length()) { i ->
                val pair = input.getJSONArray(i); require(pair.length() == 2)
                val first = pair.getInt(0); val last = pair.getInt(1)
                require(first > previous && last >= first && last <= 0x10FFFF)
                previous = last; first..last
            }
        }

        fun parse(json: String, trainingPercent: Int = 80): MulticlassSvmDetector {
            require(trainingPercent == 60 || trainingPercent == 80)
            val sourceHash = if (trainingPercent == 60) SOURCE60_SHA256 else SOURCE_SHA256
            val featureCount = if (trainingPercent == 60) 30227 else 37885
            val trainingRecords = if (trainingPercent == 60) 2281 else 3042
            val o = JSONObject(json)
            require(o.getInt("schema_version") == 10 && o.getString("research_contract") == "veritxt-raw-unicode-multiclass-svm-v1")
            require(o.getString("model_version") == "veritxt-multiclass-20261020-svm-$trainingPercent-C10" && o.getString("algorithm") == "linear_svm" && o.getDouble("C") == 10.0)
            require(o.getString("input_view") == "raw_sms" && o.getString("decision") == "argmax_first_class_on_tie")
            require(o.getJSONArray("classes").toString() == "[0,1,2]")
            require(o.getJSONArray("class_names").toString() == "[\"Ham\",\"Smishing\",\"Gambling\"]")
            require(o.getString("score") == "raw_one_vs_rest_margins" && o.getString("calibration") == "none" && !o.getBoolean("probability"))
            require(o.getJSONArray("ngram_range").toString() == "[1,2]" && o.getString("token_pattern") == TOKEN_PATTERN)
            require(o.getString("normalization") == "whitespace-collapse-then-python-lowercase")
            require(o.getString("tf") == "raw" && o.getString("norm") == "l2" && o.getBoolean("smooth_idf"))
            val provenance = o.getJSONObject("provenance")
            require(provenance.getString("pipeline_sha256") == sourceHash && provenance.getString("experiment") == "multiclass-20261020/run-v1")
            require(provenance.getString("source_artifact") == "svm-$trainingPercent.pkl" && !provenance.getBoolean("refitted"))
            require(provenance.getInt("training_records") == trainingRecords && provenance.getInt("test_records") == 761)
            if (trainingPercent == 60) require(provenance.getInt("validation_records") == 761)
            val stop = o.getJSONArray("stop_words")
            require(stop.length() == STOP_WORDS.size && (0 until stop.length()).map { stop.getString(it) }.toSet() == STOP_WORDS)
            val u = o.getJSONObject("unicode"); val unicode = PythonUnicode.parse(u)
            val words = o.getJSONArray("vocabulary"); require(words.length() == featureCount)
            val vocabulary = (0 until words.length()).associate { words.getString(it) to it }
            require(vocabulary.size == words.length() && vocabulary.keys.all { it.isNotEmpty() })
            fun array(a: JSONArray, n: Int): DoubleArray {
                require(a.length() == n)
                return DoubleArray(n) { a.getDouble(it).also { v -> require(v.isFinite()) } }
            }
            val idf = array(o.getJSONArray("idf"), words.length()); require(idf.all { it > 0.0 })
            val weights = o.getJSONArray("coefficients"); require(weights.length() == 3)
            return MulticlassSvmDetector(trainingPercent, unicode, ranges(o.getJSONArray("whitespace_ranges")),
                ranges(u.getJSONArray("word_ranges")), ranges(o.getJSONArray("digit_ranges")), STOP_WORDS,
                vocabulary, idf, List(3) { array(weights.getJSONArray(it), words.length()) }, array(o.getJSONArray("intercepts"), 3))
        }
    }
}
