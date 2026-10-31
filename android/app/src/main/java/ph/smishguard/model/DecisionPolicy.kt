package ph.smishguard.model

/** The exact serialized rule; display rounding is never used for a decision. */
data class DecisionPolicy(val threshold: Double, val inclusive: Boolean) {
    init { require(threshold.isFinite()) }
    fun suspicious(score: Double): Boolean = if (inclusive) score >= threshold else score > threshold
    fun explanation(): String = "The SMS model contributes a supporting risk indicator when its unrounded output is " +
        (if (inclusive) "greater than or equal to" else "strictly greater than") +
        " $threshold (on the model's own score scale). This model threshold is separate from the 0–100 risk index. The risk level is always determined by the displayed integer risk score."
}

data class TokenWindow(val totalContentTokens: Int, val retainedContentTokens: Int, val maxTokens: Int) {
    val truncated: Boolean get() = totalContentTokens > retainedContentTokens
    fun explanation(): String = "mBERT supports $maxTokens tokens: ${maxTokens - 2} content tokens plus [CLS] and [SEP]. " +
        "After the frozen preprocessing and WordPiece tokenizer, this message has $totalContentTokens content tokens; " +
        "only the first $retainedContentTokens were retained. Text beyond that retained prefix did not affect the model score or classification."
}
