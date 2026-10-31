package ph.smishguard.model

import java.util.Locale

object ResultCopy {
    fun heading(assessment: RiskAssessment): String = when (assessment.level) {
        RiskLevel.LOW -> "Low Risk"
        RiskLevel.MEDIUM -> "Medium Risk"
        RiskLevel.HIGH -> "High Risk"
        RiskLevel.UNABLE_TO_ASSESS -> "Unable to assess"
    }
    fun riskScore(value: Int): String = "Risk Score: $value/100"
    /** Raw model output for the explanation dialog only. Never a percentage or risk index. */
    fun score(value: Double): String =
        String.format(Locale.ROOT, "Research model output: %.4f", value)
    const val LONG_MESSAGE = "The SMS model assessed only the beginning; visible-text indicators cover the full submitted message."
    const val DISCLAIMER = "Provisional evidence index; not a probability of fraud."
}
