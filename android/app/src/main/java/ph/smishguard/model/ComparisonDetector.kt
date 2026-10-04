package ph.smishguard.model

import org.json.JSONObject

/** Manual-only policy around the exact research inference implementation. */
class ComparisonDetector(json: String, algorithm: String) : Detector {
    private val metadata = JSONObject(json)
    private val delegate = ModelLoader.parse(json)
    private val words = metadata.getJSONArray("vocabulary").let { array ->
        (0 until array.length()).map { array.getString(it) }.toSet()
    }
    init {
        require(algorithm in listOf("lr", "nb", "svm"))
        require(!metadata.getBoolean("synthetic"))
        if (metadata.getInt("schema_version") == 1) {
            require(metadata.getString("algorithm") == algorithm)
            require(!metadata.getBoolean("calibration_evaluated"))
            require(metadata.getJSONObject("calibration").getString("method") == "sigmoid")
        } else require(algorithm == "lr" && metadata.getInt("schema_version") == 2)
    }
    override val status = "Experimental · " + when (algorithm) {
        "lr" -> "Logistic Regression"
        "nb" -> "Multinomial Naive Bayes"
        else -> "Linear SVM"
    } + " · " + metadata.optString("model_version", "version unavailable")
    override suspend fun detect(text: String): Detection {
        if (text.length > MAX_MESSAGE_LENGTH) return Detection.Failure
        if (metadata.getInt("schema_version") == 1 && !Assessability.canAssess(
                Preprocessing.tokens(Assessability.textOutsideLinks(text)), words::contains)) {
            return Detection.UnableToAssess
        }
        return when (val result = delegate.detect(text)) {
            is Detection.Success -> result.copy(probability = false, experimental = true)
            else -> result
        }
    }
}
