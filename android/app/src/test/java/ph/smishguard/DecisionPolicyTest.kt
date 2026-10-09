package ph.smishguard

import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.*
import kotlin.math.exp

class DecisionPolicyTest {
    @Test fun exactBoundariesAndHiddenRoundingForCurrentAndHistoricalRules() {
        for ((threshold, inclusive) in listOf(.82 to true, .63 to true, .59 to true,
            .8899999999999999 to true, .4 to true, .5 to false)) {
            val policy = DecisionPolicy(threshold, inclusive)
            assertFalse(policy.suspicious(Math.nextDown(threshold)))
            assertEquals(inclusive, policy.suspicious(threshold))
            assertTrue(policy.suspicious(Math.nextUp(threshold)))
            assertEquals(ResultCopy.score(Math.nextDown(threshold)), ResultCopy.score(Math.nextUp(threshold)))
            assertTrue(policy.explanation().contains(threshold.toString()))
            assertTrue(policy.explanation().contains(if (inclusive) "greater than or equal to" else "strictly greater than"))
        }
    }
    @Test fun linearDetectorUsesUnroundedRuleAndCalibratesOnce() = runBlocking {
        val fixture = javaClass.getResource("/synthetic-model.json")!!.readText()
        for (threshold in listOf(.82, .63, .59, .8899999999999999)) {
            for (score in listOf(Math.nextDown(threshold), threshold, Math.nextUp(threshold))) {
                // OOV input isolates the bias to test the actual detector comparison.
                val json = JSONObject(fixture).put("threshold", threshold).put("bias", score)
                json.remove("calibration")
                val r = LinearDetector.parse(json.toString(), true).detect("fictionaloovword") as Detection.Success
                assertEquals(score >= threshold, r.suspicious)
                assertEquals(score, r.score, 0.0)
                assertEquals(DecisionPolicy(threshold, true), r.policy)
                assertNull(r.tokenWindow)
            }
        }
        val json = JSONObject(fixture).put("bias", .7).put("threshold", .82)
            .put("calibration", JSONObject().put("method", "sigmoid").put("a", 2.0).put("b", -.3))
        val r = LinearDetector.parse(json.toString(), true).detect("fictionaloovword") as Detection.Success
        assertEquals(1.0 / (1.0 + exp(-(2.0 * .7 - .3))), r.score, 0.0)
    }
}
