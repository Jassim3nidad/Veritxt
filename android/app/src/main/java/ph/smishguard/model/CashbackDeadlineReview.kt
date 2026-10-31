package ph.smishguard.model

/** Review cue, not a fraud verdict: cashback + a positive claim action + a nearby deadline. */
object CashbackDeadlineReview {
    private val offer = Regex("\\bcash\\s?back\\b|\\brebate\\b", RegexOption.IGNORE_CASE)
    private val claimDeadline = Regex(
        "\\b(?:claim|redeem|collect)\\b[^.!?;]{0,160}\\b(?:expires?\\s+(?:today|tonight|soon|on\\b)|" +
            "before\\s+midnight|within\\s+\\d+\\s*(?:minutes?|hours?|days?))\\b", RegexOption.IGNORE_CASE)
    private val negation = Regex("\\b(?:never|not|no|avoid|huwag|wag|hindi|don.t)\\b", RegexOption.IGNORE_CASE)

    fun matches(prose: String): Boolean {
        val normalized = prose.replace(Regex("\\s+"), " ")
        return claimDeadline.findAll(normalized).any { match ->
            val action = match.range.first
            val start = maxOf(0, action - 180)
            val end = minOf(normalized.length, match.range.last + 1 + 100)
            val sentence = normalized.lastIndexOfAny(charArrayOf('.', '!', '?', ';'), (action - 1).coerceAtLeast(0)) + 1
            val before = normalized.substring(maxOf(sentence.coerceAtMost(action), action - 40), action)
            offer.containsMatchIn(normalized.substring(start, end)) && !negation.containsMatchIn(before)
        }
    }
}
