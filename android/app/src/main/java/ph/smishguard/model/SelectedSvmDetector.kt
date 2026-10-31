package ph.smishguard.model

/** Raw SMS adapter plus the frozen validation-selected Linear SVM. */
class SelectedSvmDetector(modelJson: String, adapterJson: String, private val showCategory: Boolean = false) : Detector {
    private val scorer = SelectedSvmScorer.parse(modelJson)
    private val adapter = RawSmsView.parse(adapterJson)
    override val status = "Experimental · Linear SVM · svm-C-10.0"
    // Preserve the team's experimental incoming-SMS feature. This software policy
    // does not change the model's research approval/calibration metadata.
    override val automaticWarningsAllowed = true

    override suspend fun detect(text: String): Detection {
        // Check original length before masking can shorten it.
        if (text.length > MAX_MESSAGE_LENGTH) return Detection.Failure
        val result = scorer.detect(adapter.view(text))
        return if (showCategory && result is Detection.Success)
            result.copy(category = if (result.suspicious) SmsCategory.SMISHING else SmsCategory.HAM)
        else result
    }
}
