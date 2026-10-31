package ph.smishguard

import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.*

class RiskPolicyTest {
    private val neutral = Detection.Success(false, .12)
    private val flagged = Detection.Success(true, .93, experimental = true)

    @Test fun everyIntegerHasExactlyOneClassification() {
        for (score in 0..100) {
            val expected = when (score) { in 0..29 -> RiskLevel.LOW; in 30..69 -> RiskLevel.MEDIUM; else -> RiskLevel.HIGH }
            assertEquals(expected, RiskPolicy.classify(score))
        }
        for (invalid in listOf(-1, 101, Int.MIN_VALUE, Int.MAX_VALUE))
            assertThrows(IllegalArgumentException::class.java) { RiskPolicy.classify(invalid) }
    }

    @Test fun failuresSyntheticAndInsufficientEvidenceHaveNoScore() {
        for (result in listOf(Detection.Unavailable, Detection.InvalidModel, Detection.Busy, Detection.Failure,
            Detection.UnableToAssess, null, neutral.copy(synthetic = true), neutral.copy(score = Double.NaN))) {
            val assessment = RiskPolicy.assess("hello", result)
            assertEquals(RiskLevel.UNABLE_TO_ASSESS, assessment.level)
            assertNull(assessment.score)
            assertEquals(EvidenceStatus.INSUFFICIENT, assessment.evidence)
        }
        for (text in listOf("", "  ", "123456", "qwerty", "https://example.com", "name@example.com", "+1 202 555 0100")) {
            val assessment = RiskPolicy.assess(text, flagged)
            assertNull(text, assessment.score)
            assertEquals(text, RiskLevel.UNABLE_TO_ASSESS, assessment.level)
        }
    }

    @Test fun modelSignalAloneIsMediumAndRawScoreDoesNotBecomeAProbability() {
        for (rawScore in listOf(-9.0, 0.0, .5, .99999, 22.0)) {
            val result = RiskPolicy.assess("Please review your account", flagged.copy(score = rawScore))
            assertEquals(40, result.score)
            assertEquals(RiskLevel.MEDIUM, result.level)
            assertEquals(EvidenceStatus.SUSPECTED, result.evidence)
        }
        assertEquals(0, RiskPolicy.assess("Please review your account", neutral).score)
    }

    @Test fun contextAndEvidenceStrengthMatter() {
        assertEquals(70, RiskPolicy.assess("Please send us your OTP", neutral).score)
        assertEquals(30, RiskPolicy.assess("Enter your password in the official app", neutral).score)
        assertEquals(0, RiskPolicy.assess("Never send your OTP to anyone", neutral).score)
        assertEquals(0, RiskPolicy.assess("Do not share your password", neutral).score)
        assertEquals(0, RiskPolicy.assess("Huwag ibigay ang OTP", neutral).score)
        assertEquals(0, RiskPolicy.assess("Your OTP is 123456", neutral).score)
        assertEquals(0, RiskPolicy.assess("GCash transaction completed", neutral).score)
        assertEquals(0, RiskPolicy.assess("Read https://example.com/send-your-password", neutral).score)
        assertEquals(30, RiskPolicy.assess("Please pay the delivery fee", neutral).score)
        assertEquals(70, RiskPolicy.assess("Please pay the delivery fee", flagged).score)
        assertEquals(100, RiskPolicy.assess("Urgent winner: send your OTP and pay the fee https://bit.ly/demo", flagged).score)
    }

    @Test fun repeatedIndicatorsCannotInflateRisk() {
        val repeated = RiskPolicy.assess("urgent ".repeat(100), neutral)
        assertEquals(10, repeated.score)
        assertEquals(listOf(RiskIndicator.URGENCY), repeated.indicators)
        assertEquals(70, RiskPolicy.assess("Send your OTP. Share your password. Send your PIN.", neutral).score)
    }

    @Test fun urlAndEmailChecksDoNotUseTheSmsModelOrAssertReputation() {
        for (url in listOf("https://example.com@evil.example/", "https://127.0.0.1/login", "https://xn--test-9za.example")) {
            val result = RiskPolicy.assess(url, flagged)
            assertEquals(url, RiskLevel.MEDIUM, result.level)
            assertEquals(30, result.score)
            assertEquals(AssessmentLimit.URL_REPUTATION, result.limit)
            assertFalse(result.indicators.contains(RiskIndicator.MODEL_SIGNAL))
        }
        val email = RiskPolicy.assess("From: support@example.com\nSubject: Account\nPlease send your OTP immediately", flagged)
        assertEquals(RiskLevel.HIGH, email.level)
        assertEquals(AssessmentLimit.EMAIL_SCOPE, email.limit)
        assertFalse(email.indicators.contains(RiskIndicator.MODEL_SIGNAL))
        assertNull(RiskPolicy.assess("Subject: Lunch\nSee you tomorrow", flagged).score)
        assertNull(RiskPolicy.assess("https://bit.ly/demo", flagged).score)
    }

    @Test fun blockingAlwaysRequiresAUserRequestAndConfirmation() {
        val low = RiskPolicy.assess("Hello there", neutral)
        val high = RiskPolicy.assess("Send your password", flagged)
        assertFalse(ManualBlocking.offered(low))
        assertTrue(ManualBlocking.offered(high))
        assertTrue(ManualBlocking.offered(RiskPolicy.assess("+12025550100", neutral)))
        assertEquals(BlockingStep.IDLE, ManualBlocking.confirm(BlockingStep.IDLE))
        assertEquals(BlockingStep.AWAITING_CONFIRMATION, ManualBlocking.request())
        assertEquals(BlockingStep.INSTRUCTIONS, ManualBlocking.confirm(ManualBlocking.request()))
        assertEquals(BlockingStep.IDLE, ManualBlocking.dismiss())
        // Reassessing a number can neither confirm nor persist a blocking action.
        repeat(5) { assertNull(RiskPolicy.assess("+12025550100", flagged).score) }
        assertEquals(BlockingStep.IDLE, ManualBlocking.dismiss())
    }
}
