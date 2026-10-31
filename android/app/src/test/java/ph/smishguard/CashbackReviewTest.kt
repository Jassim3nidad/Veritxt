package ph.smishguard

import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.*

class CashbackReviewTest {
    private val ham = Detection.Success(false, .35, category = SmsCategory.HAM)
    private val message = "[EWB]You have PHP 5,216 available for cashback. Claim it before it expires today"

    @Test fun requestedExampleIsMediumWithoutChangingTheModelOrOldPolicy() {
        assertEquals(0, RiskPolicy.assess(message, ham).score)
        val revised = RiskPolicy.assess(message, ham, cashbackReview = true)
        assertEquals(30, revised.score); assertEquals(RiskLevel.MEDIUM, revised.level)
        assertEquals(EvidenceStatus.SUSPECTED, revised.evidence)
        assertTrue(revised.indicators.contains(RiskIndicator.CASHBACK_DEADLINE))
        assertEquals(SmsCategory.HAM, ham.category)
    }

    @Test fun offerActionAndDeadlineAreRequiredRatherThanAnEastwestName() {
        for (text in listOf(message, message.replace("[EWB]", "[BPI]").replace("5,216", "950"),
            "Cash back is available. Redeem it before midnight.",
            "A rebate is available. Collect it within 24 hours.",
            "Cashback offer: CLAIM it before it EXPIRES TONIGHT.")) {
            val result = RiskPolicy.assess(text, ham, cashbackReview = true)
            assertEquals(text, RiskLevel.MEDIUM, result.level)
            assertTrue(text, result.indicators.contains(RiskIndicator.CASHBACK_DEADLINE))
        }
        for (text in listOf("EastWest: Your monthly statement is available in the app.",
            "[EWB] Your cashback was credited today. No action is required.",
            "My cashback arrived today. See you tomorrow.",
            "Cashback is available in your account.",
            "Please claim your cashback in the app.",
            "Your cashback expires today.",
            "Never claim cashback before it expires today from an unknown message.",
            "Do not redeem cashback before midnight through a message link.",
            "No need to redeem cashback before it expires today.",
            "Review the meeting notes before midnight.")) {
            val result = RiskPolicy.assess(text, ham, cashbackReview = true)
            assertEquals(text, RiskLevel.LOW, result.level)
            assertFalse(text, result.indicators.contains(RiskIndicator.CASHBACK_DEADLINE))
        }
    }

    @Test fun strongerIndicatorsRemainHighAndRepeatedClaimsCannotInflateScores() {
        val strong = message + ". Send your OTP immediately."
        assertEquals(RiskLevel.HIGH, RiskPolicy.assess(strong, ham, cashbackReview = true).level)
        assertEquals(30, RiskPolicy.assess((message + ". ").repeat(5), ham, cashbackReview = true).score)
        assertFalse(RiskPolicy.assess("Read https://example.invalid/claim-cashback-expires-today", ham, cashbackReview = true)
            .indicators.contains(RiskIndicator.CASHBACK_DEADLINE))
        assertFalse(RiskPolicy.assess("Cashback was credited. Read https://example.invalid/claim-it-expires-today", ham, cashbackReview = true)
            .indicators.contains(RiskIndicator.CASHBACK_DEADLINE))
    }
}
