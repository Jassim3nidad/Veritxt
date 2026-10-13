package ph.smishguard

import java.util.regex.Pattern
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import ph.smishguard.model.*
import kotlin.math.abs

/** Pure test-only adapter: exactly replay source cleaning/masking without URL access. */
class RawSmsView private constructor(private val whitespace: Set<Int>) {
    private val placeholder = Pattern.compile("<(?:REAL NAME|NAME|REDACTED|BLANK|n)>|\\[name redacted\\]|\\(full name\\)|\\[my name\\]", Pattern.CASE_INSENSITIVE or Pattern.UNICODE_CASE)
    // Android ICU folds non-ASCII letters even with CASE_INSENSITIVE alone.
    // Explicit ASCII pairs/whitespace reproduce Python re.I | re.ASCII exactly.
    private val url = Pattern.compile("(?:[hH][tT][tT][pP][sS]?://|[wW][wW][wW]\\.)[^\\x09-\\x0D\\x20<>]+")
    private val email = Pattern.compile("[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
    private val digits = Pattern.compile("[0-9]+")
    private fun clean(text: String): String {
        val replaced = placeholder.matcher(text).replaceAll(" ")
        val collapsed = StringBuilder(); var inWhitespace = false
        replaced.codePoints().forEach { cp ->
            if (cp in whitespace) {
                if (!inWhitespace) collapsed.append(' ')
                inWhitespace = true
            } else { collapsed.appendCodePoint(cp); inWhitespace = false }
        }
        return collapsed.toString().trim(' ', ',')
    }
    fun view(raw: String): String {
        var text = clean(raw)
        text = url.matcher(text).replaceAll(" zzurlzz ")
        text = email.matcher(text).replaceAll(" zzemailzz ")
        text = digits.matcher(text).replaceAll(" zznumberzz ")
        return clean(text)
    }
    companion object {
        fun parse(json: String): RawSmsView {
            val o = JSONObject(json)
            require(o.getString("version") == "case-preserving-mask-v1" && o.getString("unicode_version") == "15.0.0")
            require(o.getJSONArray("order").toString() == "[\"clean\",\"url\",\"email\",\"ascii_digits\",\"clean\"]")
            require(o.getString("url_case") == "ascii_insensitive" && !o.getBoolean("lowercase"))
            val array = o.getJSONArray("whitespace_codepoints")
            val whitespace = (0 until array.length()).map { array.getInt(it) }.toSet()
            require(whitespace == setOf(9,10,11,12,13,28,29,30,31,32,133,160,5760,8192,8193,8194,8195,8196,8197,8198,8199,8200,8201,8202,8232,8233,8239,8287,12288))
            val adapter = RawSmsView(whitespace)
            require(o.getString("placeholder_pattern") == adapter.placeholder.pattern())
            require(o.getString("url_pattern") == "(?:https?://|www\\.)[^\\s<>]+")
            require(o.getString("email_pattern") == adapter.email.pattern())
            require(o.getString("digit_pattern") == adapter.digits.pattern())
            return adapter
        }
    }
}

object RawSmsParity {
    suspend fun verify(modelJson: String, adapterJson: String, casesJson: String): JSONObject {
        val adapter = RawSmsView.parse(adapterJson)
        val detector = SelectedSvmScorer.parse(modelJson)
        val cases = JSONArray(casesJson); var maxError = 0.0; var abstained = 0
        for (i in 0 until cases.length()) {
            val case = cases.getJSONObject(i); val raw = case.getString("raw"); val view = adapter.view(raw)
            assertEquals("raw view at probe $i", case.getString("view"), view)
            assertEquals("terms at probe $i", case.getJSONArray("terms").toString(), JSONArray(detector.terms(view)).toString())
            val expected = case.getJSONObject("features"); val actual = detector.features(view)
            assertEquals(expected.keys().asSequence().map { it.toInt() }.toSet(), actual.keys)
            actual.forEach { (index,value) -> assertEquals("feature at probe $i", expected.getDouble(index.toString()), value, 1e-10) }
            val score = detector.score(view); maxError = maxOf(maxError, abs(score-case.getDouble("score")))
            assertEquals("score at probe $i", case.getDouble("score"), score, 1e-10)
            assertEquals(case.getBoolean("suspicious"), score >= detector.threshold)
            val result = if (raw.length > MAX_MESSAGE_LENGTH) Detection.Failure else detector.detect(view)
            if (case.getBoolean("overlong")) assertEquals(Detection.Failure, result)
            else if (case.getBoolean("must_abstain")) { assertEquals("abstention at probe $i", Detection.UnableToAssess, result); abstained++ }
            else if (result is Detection.Success) { assertFalse(result.probability); assertTrue(result.experimental) }
        }
        return JSONObject().put("raw_cases",cases.length()).put("maximum_score_error",maxError)
            .put("required_abstentions",abstained).put("raw_view_matches",true)
    }
}
