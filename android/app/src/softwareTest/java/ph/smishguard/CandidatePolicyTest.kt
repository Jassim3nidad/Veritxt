package ph.smishguard

import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.*

class CandidatePolicyTest {
    // Handcrafted in-memory software fixture; never a fitted model or shipped asset.
    private fun fixture(): JSONObject = JSONObject("""{
        "schema_version":3,"model_version":"software-only","algorithm":"lr",
        "preprocessing_version":"python-unicode-word-v2","feature_type":"word-unigram-bigram-tfidf-l2",
        "vocabulary":["hello","account"],"idf":[1,2],"weights":[-0.4,0.7],"bias":-0.2,
        "classes":["ham","smishing"],"positive_class":"smishing","ngram_range":[1,2],
        "lowercase":true,"token_pattern":"\\b\\w+\\b","term_frequency":"raw","normalization":"l2",
        "score_transform":"sigmoid","calibration":{"a":2,"b":-0.1},"threshold":0.4,
        "threshold_comparison":"greater_or_equal","synthetic":false,"automatic_warnings_approved":false,
        "evaluation_status":"unverified","calibration_status":"fitted_unvalidated",
        "intended_use":"manual_development","technical_compatibility":"reference_verified",
        "provenance":{"kind":"user_supplied_export","source_sha256":"${"0".repeat(64)}"},
        "unicode":{"unicode_version":"15.0.0","word_ranges":[[48,57],[65,90],[95,95],[97,122]],
        "cased_ranges":[[65,90],[97,122]],"case_ignorable_ranges":[[768,879]],"lowercase_map":{"65":"a"}}
    }""")

    @Test fun candidateBoundaryDoesNotChangeHistoricalThreshold() {
        assertFalse(SuppliedDetector.isSuspicious(Math.nextDown(.4), true))
        assertTrue(SuppliedDetector.isSuspicious(.4, true))
        assertTrue(SuppliedDetector.isSuspicious(Math.nextUp(.4), true))
        assertFalse(SuppliedDetector.isSuspicious(.5, false))
        assertTrue(SuppliedDetector.isSuspicious(Math.nextUp(.5), false))
    }

    @Test fun calibrationAbstentionAndPolicy() = runBlocking {
        val model = SuppliedDetector.parse(fixture().toString(), candidate = true)
        val result = model.detect("hello account") as Detection.Success
        val margin = -.2 + (-.4 + 2 * .7) / kotlin.math.sqrt(5.0)
        assertEquals(1 / (1 + kotlin.math.exp(-(2 * margin - .1))), result.score, 1e-12)
        assertFalse(result.probability)
        assertTrue(result.experimental)
        assertFalse(model.automaticWarningsAllowed)
        for (text in listOf("", "   ", "xqzvplmkj", "!!!", "https://example.invalid"))
            assertEquals(Detection.UnableToAssess, model.detect(text))
        assertEquals(Detection.Failure, model.detect("a".repeat(10001)))
    }

    @Test fun candidateIsExplicitAndMalformedPolicyRejected() {
        assertThrows(Exception::class.java) { ModelLoader.parse(fixture().toString()) }
        for ((key, value) in listOf("algorithm" to "svm", "threshold" to .5,
            "automatic_warnings_approved" to true, "calibration_status" to "validated")) {
            assertThrows(Exception::class.java) { SuppliedDetector.parse(fixture().put(key, value).toString(), candidate = true) }
        }
        assertThrows(Exception::class.java) {
            SuppliedDetector.parse(fixture().put("calibration", JSONObject().put("a", -1).put("b", 0)).toString(), candidate = true)
        }
    }

}
