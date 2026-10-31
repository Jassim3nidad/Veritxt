package ph.smishguard.model

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import org.json.JSONObject
import kotlin.math.exp
import kotlin.math.sqrt

/** Separate research candidate runtime. No ModelLoader registration or app pointer. */
class ResearchLinearScorer private constructor(
    private val unicode: PythonUnicode, private val whitespace: Set<Int>,
    private val blocks: List<Block>, private val weights: DoubleArray, private val bias: Double,
    private val calibration: Pair<Double, Double>?, val threshold: Double
) : Detector {
    private data class Block(val analyzer: String, val min: Int, val max: Int,
                             val vocabulary: Map<String, Int>, val idf: DoubleArray, val offset: Int)
    override val status = "Experimental research candidate · inherited labels"
    override val automaticWarningsAllowed = false
    fun normalize(text: String): String {
        val output = StringBuilder(); var inSpace = false
        text.codePoints().forEach { cp ->
            if (cp in whitespace) { if (!inSpace) output.append(' '); inSpace = true }
            else { output.appendCodePoint(cp); inSpace = false }
        }
        return output.toString().trim(' ')
    }
    suspend fun features(text: String): Map<Int, Double> {
        val normalized = normalize(text)
        val result = mutableMapOf<Int, Double>()
        for (block in blocks) {
            val counts = mutableMapOf<Int, Double>()
            fun add(term: String) { block.vocabulary[term]?.let { counts[it] = (counts[it] ?: 0.0) + 1.0 } }
            if (block.analyzer == "word") {
                val tokens = unicode.tokens(normalized).filter { it.codePointCount(0, it.length) >= 2 }
                for (n in block.min..block.max) for (i in 0..tokens.size - n) {
                    currentCoroutineContext().ensureActive()
                    add(tokens.subList(i, i + n).joinToString(" "))
                }
            } else {
                // sklearn char_wb pads each whitespace-delimited token. Slices are
                // Unicode codepoints, not UTF-16 indices; short words counted once.
                for (word in unicode.lowercase(normalized).split(' ').filter { it.isNotEmpty() }) {
                    val cp = (" $word ").codePoints().toArray()
                    for (n in block.min..block.max) {
                        var offset = 0
                        add(String(cp, 0, minOf(n, cp.size)))
                        while (offset + n < cp.size) {
                            currentCoroutineContext().ensureActive(); offset++
                            add(String(cp, offset, n))
                        }
                        if (offset == 0) break
                    }
                }
            }
            var norm = 0.0
            counts.replaceAll { index, count -> (count * block.idf[index]).also { norm += it * it } }
            norm = sqrt(norm)
            if (norm > 0.0) counts.forEach { (i, v) -> result[block.offset + i] = v / norm }
        }
        return result
    }
    suspend fun score(text: String): Double {
        var margin = bias
        for ((index, value) in features(text)) margin += weights[index] * value
        val value = calibration?.let { (a,b) ->
            val z = a * margin + b
            if (z >= 0) 1.0 / (1.0 + exp(-z)) else exp(z) / (1.0 + exp(z))
        } ?: margin
        require(value.isFinite()); return value
    }
    override suspend fun detect(text: String): Detection {
        if (text.length > MAX_MESSAGE_LENGTH || '\u0000' in text ||
            text.any { it.isSurrogate() } && !validSurrogates(text)) return Detection.Failure
        val tokens = unicode.tokens(Assessability.textOutsideLinks(text))
        val word = blocks.first().vocabulary
        if (!Assessability.canAssess(tokens) { it in word }) return Detection.UnableToAssess
        val score = score(text)
        // SVM margins or fitted sigmoid estimates are not approved real-traffic probabilities.
        return Detection.Success(score >= threshold, score, probability = false, experimental = true)
    }
    private fun validSurrogates(text: String): Boolean {
        var i = 0
        while (i < text.length) {
            val c = text[i++]
            if (Character.isHighSurrogate(c)) {
                if (i == text.length || !Character.isLowSurrogate(text[i++])) return false
            } else if (Character.isLowSurrogate(c)) return false
        }
        return true
    }
    companion object {
        fun parse(json: String): ResearchLinearScorer {
            val o = JSONObject(json)
            require(o.getInt("schema_version") == 7 && o.getString("research_contract") == "word-char-linear-v1")
            require(o.getString("algorithm") in setOf("lr","svm","nb"))
            require(o.getString("input_view") == "whitespace_normalized_existing_masked_text")
            require(o.getString("evaluation_status") == "retrospective_inherited_labels")
            require(o.getJSONArray("classes").toString() == "[\"ham\",\"smishing\"]" && o.getString("positive_class") == "smishing")
            require(!o.getBoolean("probability_approved") && !o.getBoolean("automatic_warnings_approved"))
            require(o.getString("threshold_comparison") == "greater_or_equal")
            val unicode = PythonUnicode.parse(o.getJSONObject("unicode"))
            val spaces = o.getJSONArray("whitespace_codepoints")
            val whitespace = (0 until spaces.length()).map { spaces.getInt(it) }.toSet()
            require(whitespace == setOf(9,10,11,12,13,28,29,30,31,32,133,160,5760,8192,8193,8194,8195,8196,8197,8198,8199,8200,8201,8202,8232,8233,8239,8287,12288))
            val array = o.getJSONArray("blocks"); require(array.length() in 1..2)
            var offset = 0
            val blocks = List(array.length()) { j ->
                val b = array.getJSONObject(j); val analyzer = b.getString("analyzer")
                require(analyzer == if (j == 0) "word" else "char_wb")
                require(b.getString("norm") == "l2" && b.getString("tf") == "raw")
                val ng = b.getJSONArray("ngram_range"); val min = ng.getInt(0); val max = ng.getInt(1)
                require(ng.length() == 2 && min <= max && (if (j == 0) min == 1 && max in 1..2 else min == 3 && max in 5..6))
                val words = b.getJSONArray("vocabulary"); require(words.length() in 1..200000)
                val vocabulary = (0 until words.length()).associate { words.getString(it) to it }
                require(vocabulary.size == words.length() && vocabulary.keys.all { it.isNotEmpty() })
                val idfs = b.getJSONArray("idf"); require(idfs.length() == words.length())
                val idf = DoubleArray(idfs.length()) { idfs.getDouble(it).also { x -> require(x.isFinite() && x > 0.0) } }
                Block(analyzer,min,max,vocabulary,idf,offset).also { offset += words.length() }
            }
            val values = o.getJSONArray("weights"); require(values.length() == offset)
            val weights = DoubleArray(offset) { values.getDouble(it).also { v -> require(v.isFinite()) } }
            val bias = o.getDouble("bias").also { require(it.isFinite()) }
            val threshold = o.getDouble("threshold").also { require(it.isFinite()) }
            val calibration = if (o.isNull("calibration")) null else o.getJSONObject("calibration").let {
                val a = it.getDouble("a"); val b = it.getDouble("b")
                require(a.isFinite() && a > 0 && b.isFinite() && threshold in 0.0..1.0); a to b
            }
            return ResearchLinearScorer(unicode,whitespace,blocks,weights,bias,calibration,threshold)
        }
    }
}

/** Raw SMS entry point using the existing frozen masking contract. */
class ResearchLinearRawDetector(modelJson: String, adapterJson: String) : Detector {
    private val model = ResearchLinearScorer.parse(modelJson)
    private val adapter = RawSmsView.parse(adapterJson)
    override val status = model.status
    override val automaticWarningsAllowed = false
    fun view(text: String): String = adapter.view(text)
    suspend fun score(text: String): Double = model.score(view(text))
    override suspend fun detect(text: String): Detection {
        if (text.length > MAX_MESSAGE_LENGTH) return Detection.Failure
        return model.detect(view(text))
    }
}
