package ph.smishguard.model

/** Abstention, not a ham classifier. No word-count or coverage-ratio threshold. */
object Assessability {
    private val links = Regex("(?i)(?:https?://|www\\.)\\S+|\\b[\\w-]+(?:\\.[\\w-]+)+[/\\w?=&%#.-]*")
    private val keyboardRows = listOf("qwertyuiop", "asdfghjkl", "zxcvbnm")

    fun textOutsideLinks(text: String): String = links.replace(text, " ")

    fun usableWord(word: String): Boolean {
        if (word in setOf("zznumberzz", "zzemailzz", "zzurlzz", "zznamezz", "zzaccountzz")) return false
        if (word.count { it.isLetter() } < 2 || !word.all { it.isLetter() }) return false
        if (word.length >= 4 && word.toSet().size == 1) return false
        if (word.length >= 4 && keyboardRows.any { word in it || word in it.reversed() }) return false
        return true
    }

    fun canAssess(tokensOutsideLinks: List<String>, knownWord: (String) -> Boolean): Boolean =
        tokensOutsideLinks.any { usableWord(it) && knownWord(it) }
}
