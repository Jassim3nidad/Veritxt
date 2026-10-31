package ph.smishguard.model

import ph.smishguard.BuildConfig

/** Explicit application profile; old build variants retain their original risk behavior. */
object AppRiskPolicy {
    val linkedCashbackReviewEnabled: Boolean get() = BuildConfig.BUILD_TYPE in listOf("oldSvm", "usbDemo")
    val VERSION: String get() = when {
        linkedCashbackReviewEnabled -> "linked-cashback-claim-deadline-v1"
        BuildConfig.BUILD_TYPE == "cashbackReview" -> "cashback-claim-deadline-v1"
        else -> RiskPolicy.VERSION
    }
    fun assess(text: String, detection: Detection?): RiskAssessment =
        RiskPolicy.assess(text, detection, cashbackReview = BuildConfig.BUILD_TYPE == "cashbackReview",
            linkedCashbackReview = linkedCashbackReviewEnabled)
}
