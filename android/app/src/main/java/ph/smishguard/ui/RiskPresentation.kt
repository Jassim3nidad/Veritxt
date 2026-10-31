package ph.smishguard.ui

import ph.smishguard.R
import ph.smishguard.model.*

object RiskPresentation {
    fun label(level: RiskLevel) = when (level) {
        RiskLevel.LOW -> R.string.risk_low
        RiskLevel.MEDIUM -> R.string.risk_medium
        RiskLevel.HIGH -> R.string.risk_high
        RiskLevel.UNABLE_TO_ASSESS -> R.string.verdict_abstain_title
    }
    fun analysis(level: RiskLevel) = when (level) {
        RiskLevel.LOW -> R.string.risk_low_analysis
        RiskLevel.MEDIUM -> R.string.risk_medium_analysis
        RiskLevel.HIGH -> R.string.risk_high_analysis
        RiskLevel.UNABLE_TO_ASSESS -> R.string.risk_unable_analysis
    }
    fun action(level: RiskLevel) = when (level) {
        RiskLevel.LOW -> R.string.risk_low_action
        RiskLevel.MEDIUM -> R.string.risk_medium_action
        RiskLevel.HIGH -> R.string.risk_high_action
        RiskLevel.UNABLE_TO_ASSESS -> R.string.risk_unable_action
    }
    fun indicator(indicator: RiskIndicator) = when (indicator) {
        RiskIndicator.CREDENTIAL_REQUEST -> R.string.indicator_credentials
        RiskIndicator.CREDENTIAL_ENTRY -> R.string.indicator_credential_entry
        RiskIndicator.IDENTITY_CLAIM -> R.string.indicator_identity
        RiskIndicator.DECEPTIVE_URL -> R.string.indicator_url_structure
        RiskIndicator.PAYMENT_REQUEST -> R.string.indicator_payment
        RiskIndicator.MODEL_SIGNAL -> R.string.indicator_model
        RiskIndicator.URGENCY -> R.string.indicator_urgency
        RiskIndicator.REWARD -> R.string.indicator_reward
        RiskIndicator.SHORTENED_URL -> R.string.indicator_short_url
        RiskIndicator.LINK_PRESENT -> R.string.indicator_link
        RiskIndicator.CASHBACK_DEADLINE -> R.string.indicator_cashback_deadline
    }
    fun limit(limit: AssessmentLimit) = when (limit) {
        AssessmentLimit.INSUFFICIENT_CONTENT -> R.string.risk_limit_content
        AssessmentLimit.PHONE_IDENTITY -> R.string.risk_limit_phone
        AssessmentLimit.URL_REPUTATION -> R.string.risk_limit_url
        AssessmentLimit.EMAIL_SCOPE -> R.string.risk_limit_email
        AssessmentLimit.MODEL_MISSING -> R.string.verdict_missing_body
        AssessmentLimit.MODEL_INVALID -> R.string.verdict_invalid_body
        AssessmentLimit.CHECK_FAILED -> R.string.verdict_failed_body
        AssessmentLimit.CHECK_BUSY -> R.string.verdict_busy_body
        AssessmentLimit.SYNTHETIC -> R.string.verdict_synthetic_body
    }
}
