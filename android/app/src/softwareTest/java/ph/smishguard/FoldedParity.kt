package ph.smishguard

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import ph.smishguard.model.*
import java.security.MessageDigest

/** Private fixtures supplied by the test runner only; assertions never include message text. */
object FoldedParity {
    fun sha(text: String): String = MessageDigest.getInstance("SHA-256").digest(text.toByteArray(Charsets.UTF_8))
        .joinToString("") { "%02x".format(it) }

    suspend fun verify(modelJson: String, casesJson: String): JSONObject {
        val model = SuppliedDetector.parse(modelJson, folded = true)
        val cases = JSONArray(casesJson)
        var maxError = 0.0; var abstained = 0; var scored = 0
        for (i in 0 until cases.length()) {
            val case = cases.getJSONObject(i); val text = case.getString("text")
            val tokens = JSONArray(model.tokenizer.tokens(text))
            assertTrue("token parity at index $i", tokens.toString() == case.getJSONArray("tokens").toString())
            if (text.isNotBlank() && text.length <= MAX_MESSAGE_LENGTH) {
                val raw = model.rawDetection(text) as Detection.Success
                val error = kotlin.math.abs(case.getDouble("score") - raw.score)
                maxError = maxOf(maxError, error)
                assertTrue("score parity at index $i", error <= 1e-10)
                assertTrue("threshold parity at index $i", case.getBoolean("suspicious") == raw.suspicious)
            }
            when (val result = model.detect(text)) {
                Detection.UnableToAssess -> abstained++
                is Detection.Success -> { scored++; assertTrue(result.experimental); assertFalse(result.probability) }
                else -> assertTrue("Unexpected policy at index $i", text.length > MAX_MESSAGE_LENGTH)
            }
        }
        assertFalse(model.automaticWarningsAllowed)
        return JSONObject().put("cases", cases.length()).put("max_absolute_error", maxError)
            .put("scored", scored).put("abstained", abstained)
            .put("model_sha256", sha(modelJson)).put("cases_sha256", sha(casesJson))
    }
}
