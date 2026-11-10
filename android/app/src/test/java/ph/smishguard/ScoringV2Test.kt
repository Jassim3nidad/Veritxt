package ph.smishguard

import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.*

/** Synthetic text and stub detections only. */
class ScoringV2Test {
    private val neutral = Detection.Success(false, .05)
    private fun flagged(score: Double) = Detection.Success(true, score)
    private fun v2(text: String, result: Detection = neutral, linked: Boolean = false) =
        RiskPolicy.assess(text, result, linkedCashbackReview = linked, rules = RiskRules.V2)
    private val pointsText = "Your 7,352 reward points expire today. Redeem now at https://example.invalid/rewards"

    @Test fun codeRequestsReachHighRisk() {
        val security = v2("ibigay mo sakin ang iyong security code hahaha")
        assertEquals(70, security.score)
        assertEquals(RiskLevel.HIGH, security.level)
        val otp = v2("please give me your otp account", flagged(.70))
        assertEquals(100, otp.score)
        assertEquals(RiskLevel.HIGH, otp.level)
        for (text in listOf("Tell me your PIN now", "Pahingi ng OTP mo", "Sabihin mo ang password mo", "I-send mo ang OTP"))
            assertEquals(text, 70, v2(text).score)
        assertEquals(30, v2("Enter your security code in the app").score)
    }

    @Test fun safeWordingIsNotACredentialRequest() {
        for (text in listOf("Never give your OTP to anyone.", "Huwag ibigay ang OTP mo kahit kanino.",
            "Please give me your feedback on the report.", "Give this code to the rider.",
            "Your security code is 482910. Do not share it.")) {
            val result = v2(text)
            assertFalse(text, RiskIndicator.CREDENTIAL_REQUEST in result.indicators)
            assertFalse(text, RiskIndicator.CREDENTIAL_ENTRY in result.indicators)
            assertEquals(text, 0, result.score)
        }
    }

    @Test fun modelConfidenceAddsPointsOnlyAtOrAboveTheFixedCutoffWhenFlagged() {
        val text = "Please review your account"
        assertEquals(40, v2(text, flagged(.89)).score)
        assertEquals(RiskLevel.MEDIUM, v2(text, flagged(.89)).level)
        val confident = v2(text, flagged(.90))
        assertEquals(70, confident.score)
        assertEquals(RiskLevel.HIGH, confident.level)
        assertTrue(RiskIndicator.MODEL_HIGH_CONFIDENCE in confident.indicators)
        val notFlagged = v2(text, Detection.Success(false, .95))
        assertEquals(0, notFlagged.score)
        assertFalse(RiskIndicator.MODEL_HIGH_CONFIDENCE in notFlagged.indicators)
    }

    @Test fun pointsRuleNeedsOfferExpiryActionAndLink() {
        val full = v2(pointsText, flagged(.75))
        assertEquals(70, full.score)
        assertEquals(RiskLevel.HIGH, full.level)
        assertTrue(RiskIndicator.POINTS_OFFER_DEADLINE in full.indicators)
        assertEquals(30, v2(pointsText).score)
        val noLink = v2("Your 7,352 reward points expire today. Redeem now in the official app", flagged(.75))
        assertEquals(40, noLink.score)
        assertFalse(RiskIndicator.POINTS_OFFER_DEADLINE in noLink.indicators)
        assertEquals(0, v2("Your points expire today.").score)
        assertFalse(RiskIndicator.POINTS_OFFER_DEADLINE in v2("Your points expire today.", flagged(.75)).indicators)
        assertFalse(RiskIndicator.POINTS_OFFER_DEADLINE in v2("Your points expire today at https://example.invalid/info").indicators)
    }

    @Test fun negatedRedeemActionsDoNotCount() {
        val warning = "Warning: fake texts say your reward points expire today. Do not click or redeem at https://example.invalid/x"
        assertFalse(RiskIndicator.POINTS_OFFER_DEADLINE in v2(warning).indicators)
    }

    @Test fun cashbackAndPointsRulesCountOnce() {
        val text = "[EWB]You have PHP 5,216 available for cashback. Claim it before it expires today. https://example.invalid/ph"
        val result = v2(text, flagged(.75), linked = true)
        assertEquals(70, result.score)
        assertTrue(RiskIndicator.CASHBACK_DEADLINE in result.indicators)
        assertFalse(RiskIndicator.POINTS_OFFER_DEADLINE in result.indicators)
    }

    @Test fun rulesAreOffUnlessRequested() {
        assertEquals(40, RiskPolicy.assess("please give me your otp account", flagged(.70)).score)
        assertEquals(0, RiskPolicy.assess("ibigay mo sakin ang iyong security code hahaha", neutral).score)
        assertEquals(40, RiskPolicy.assess("Please review your account", flagged(.99)).score)
        assertEquals(40, RiskPolicy.assess(pointsText, flagged(.75)).score)
        if (!AppRiskPolicy.scoringV2Enabled && BuildConfig.BUILD_TYPE != "cashbackReview") {
            assertEquals(RiskPolicy.VERSION, AppRiskPolicy.VERSION)
            assertEquals(40, AppRiskPolicy.assess(pointsText, flagged(.75)).score)
        }
    }

    @Test fun breakdownListsPointItemsModelFirstAndKnowsTheCap() {
        val result = v2("please give me your otp account immediately", flagged(.95))
        assertEquals(listOf(RiskIndicator.MODEL_SIGNAL, RiskIndicator.MODEL_HIGH_CONFIDENCE,
            RiskIndicator.CREDENTIAL_REQUEST, RiskIndicator.URGENCY), result.pointItems)
        assertEquals(150, result.uncappedPoints)
        assertEquals(100, result.score)
        val zero = v2("BDO notice at https://example.invalid/x")
        assertTrue(zero.pointItems.isEmpty())
    }

    @Test fun breakdownScoreIsAPlainTwoDecimalValue() {
        assertEquals("0.89", ResultCopy.breakdownScore(.8999))
        assertEquals("0.90", ResultCopy.breakdownScore(.90))
        assertEquals("0.37", ResultCopy.breakdownScore(.37))
        assertEquals("0.57", ResultCopy.breakdownScore(.57))
        assertFalse(ResultCopy.breakdownScore(.88).contains("%"))
    }
}
