package ph.smishguard.sms

import android.content.Context
import ph.smishguard.R
import ph.smishguard.model.RiskAssessment
import ph.smishguard.model.RiskLevel
import ph.smishguard.model.SmsCategory
import ph.smishguard.ui.RiskPresentation

/** Only fixed labels and a risk index enter notification extras, never input or sender data. */
data class InitialSmsReport(val assessment: RiskAssessment, val category: SmsCategory? = null) {
    fun title(context: Context): String = context.getString(R.string.notif_report_title,
        context.getString(RiskPresentation.label(assessment.level)))

    fun summary(context: Context): String {
        val score = assessment.score ?: return context.getString(R.string.notif_report_unavailable)
        val categoryLabel = category?.let {
            context.getString(when (it) {
                SmsCategory.HAM -> R.string.sms_category_ham
                SmsCategory.SMISHING -> R.string.sms_category_smishing
                SmsCategory.GAMBLING -> R.string.sms_category_gambling
            })
        }
        return listOfNotNull(context.getString(R.string.risk_score, score), categoryLabel).joinToString(" · ")
    }

    fun expanded(context: Context): String = buildList {
        add(summary(context))
        add(context.getString(RiskPresentation.analysis(assessment.level)))
        if (assessment.level != RiskLevel.UNABLE_TO_ASSESS) {
            add(context.getString(R.string.risk_score_note))
        }
    }.joinToString("\n")
}
