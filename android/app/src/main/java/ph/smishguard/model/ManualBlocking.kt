package ph.smishguard.model

/** This app is not the default dialer and cannot write Android's blocked-number provider.
 * Confirmation opens Android's blocklist, with instructions if the handoff is unavailable.
 * The user enters and confirms the actual sender in Android's UI.
 * No number from a message body is assumed to be its sender.
 */
enum class BlockingStep { IDLE, AWAITING_CONFIRMATION, INSTRUCTIONS }
object ManualBlocking {
    fun offered(assessment: RiskAssessment): Boolean = assessment.kind == InputKind.PHONE_NUMBER ||
        (assessment.kind == InputKind.MESSAGE && assessment.level in setOf(RiskLevel.MEDIUM, RiskLevel.HIGH))
    fun request() = BlockingStep.AWAITING_CONFIRMATION
    fun confirm(step: BlockingStep): BlockingStep =
        if (step == BlockingStep.AWAITING_CONFIRMATION) BlockingStep.INSTRUCTIONS else step
    fun dismiss() = BlockingStep.IDLE
}
