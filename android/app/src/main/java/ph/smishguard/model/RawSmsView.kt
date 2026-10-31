package ph.smishguard.model

import java.util.regex.Pattern
import org.json.JSONObject

/** Frozen training contract shared by app inference and Python parity checks. */
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
