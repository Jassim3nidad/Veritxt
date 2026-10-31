package ph.smishguard.sms

import android.content.Context
import ph.smishguard.R
import ph.smishguard.ui.RiskPresentation

/** Bounded plain text only: no spans, links, line-break injection or bidi control characters. */
object SmsNotificationPreview {
    const val MAX_CODE_POINTS = 90

    fun text(message: String): String {
        val clean = message.replace(Regex("[\\p{Cc}\\p{Cf}\\s]+"), " ").trim()
        if (clean.codePointCount(0, clean.length) <= MAX_CODE_POINTS) return clean
        return clean.substring(0, clean.offsetByCodePoints(0, MAX_CODE_POINTS)) + "…"
    }

    fun title(context: Context, report: InitialSmsReport, sender: String?): String = context.getString(
        R.string.notif_sender_risk, SenderNumbers.normalize(sender) ?: context.getString(R.string.notif_unknown_sender),
        context.getString(RiskPresentation.label(report.assessment.level)))
}
