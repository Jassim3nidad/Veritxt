package ph.smishguard.model

import ph.smishguard.BuildConfig

/** Explicit application profile; old build variants retain their original risk behavior. */
object AppRiskPolicy {
    val linkedCashbackReviewEnabled: Boolean get() = BuildConfig.BUILD_TYPE in listOf("oldSvm", "usbDemo")
    val scoringV2Enabled: Boolean get() = BuildConfig.BUILD_TYPE in listOf("selectedSvm", "oldSvm", "usbDemo")
    val VERSION: String get() = when {
        scoringV2Enabled -> RiskPolicy.VERSION_V2
        BuildConfig.BUILD_TYPE == "cashbackReview" -> "cashback-claim-deadline-v1"
        else -> RiskPolicy.VERSION
    }
    fun assess(text: String, detection: Detection?): RiskAssessment =
        RiskPolicy.assess(text, detection, cashbackReview = BuildConfig.BUILD_TYPE == "cashbackReview",
            linkedCashbackReview = linkedCashbackReviewEnabled, rules = if (scoringV2Enabled) RiskRules.V2 else RiskRules.V1)
}
