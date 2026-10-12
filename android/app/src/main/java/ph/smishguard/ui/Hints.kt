package ph.smishguard.ui

import java.util.Locale

/** Rule-based warning signs shown beside the model result. They are hints, not the model's explanation. */
enum class HintKind { BRAND, LINK, URGENCY, CREDENTIALS, BAIT }
/** [detail] is the brand or link host the hint refers to; the UI turns kind + detail into translated text. */
data class Hint(val kind: HintKind, val detail: String? = null)
data class HintSummary(val hints: List<Hint>, val brand: String?)

object Hints {
    private val brands = linkedMapOf(
        "BDO" to "\\bbdo\\b|banco de oro", "BPI" to "\\bbpi\\b", "GCash" to "g-?cash", "Maya" to "\\bmaya\\b|paymaya",
        "Metrobank" to "metrobank", "UnionBank" to "union\\s?bank", "EastWest" to "eastwest|\\[ewb\\]",
        "Landbank" to "land\\s?bank", "PNB" to "\\bpnb\\b", "Security Bank" to "security bank", "RCBC" to "\\brcbc\\b",
        "SSS" to "\\bsss\\b", "PhilHealth" to "philhealth", "Pag-IBIG" to "pag-?ibig", "LBC" to "\\blbc\\b",
        "J&T Express" to "j&t|\\bjnt\\b", "Shopee" to "shopee", "Lazada" to "lazada")
    private val official = listOf("bdo.com.ph", "bpi.com.ph", "gcash.com", "maya.ph", "paymaya.com", "metrobank.com.ph",
        "unionbankph.com", "eastwestbanker.com", "landbank.com", "pnb.com.ph", "securitybank.com", "rcbc.com",
        "sss.gov.ph", "philhealth.gov.ph", "pagibigfund.gov.ph", "gov.ph", "lbcexpress.com", "jtexpress.ph",
        "shopee.ph", "lazada.com.ph")
    private val link = Regex("(?:https?://)?(?:www\\.)?((?:[a-z0-9-]+\\.)+[a-z]{2,10})(?:/\\S*)?", RegexOption.IGNORE_CASE)
    private val urgency = Regex("expir|today|tomorrow|within \\d+|24 hours|suspend|locked|deactivat|final notice|right away|" +
        "ngayon|agad|huling", RegexOption.IGNORE_CASE)
    private val credentials = Regex("\\botp\\b|\\bm?pin\\b|password|\\bcvv\\b|card number|one.?time", RegexOption.IGNORE_CASE)
    private val bait = Regex("\\bwon\\b|winner|prize|reward|points|cash ?back|claim|refund|nanalo|premyo|napili", RegexOption.IGNORE_CASE)

    fun read(text: String): HintSummary {
        val lower = text.lowercase(Locale.ROOT)
        val brand = brands.entries.firstOrNull { Regex(it.value).containsMatchIn(lower) }?.key
        val hosts = link.findAll(text).map { it.groupValues[1].lowercase(Locale.ROOT).removePrefix("www.") }
            .filter { host -> host.substringAfterLast('.').all { it.isLetter() } }.toList()
        val unofficial = hosts.firstOrNull { host -> official.none { host == it || host.endsWith(".$it") } }
        val hints = buildList {
            if (brand != null) add(Hint(HintKind.BRAND, brand))
            if (unofficial != null) add(Hint(HintKind.LINK, unofficial))
            if (credentials.containsMatchIn(text)) add(Hint(HintKind.CREDENTIALS))
            if (urgency.containsMatchIn(text)) add(Hint(HintKind.URGENCY))
            if (bait.containsMatchIn(text)) add(Hint(HintKind.BAIT))
        }
        return HintSummary(hints, brand)
    }
}
