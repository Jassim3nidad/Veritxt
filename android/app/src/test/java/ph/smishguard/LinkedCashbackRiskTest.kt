package ph.smishguard

import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.*

class LinkedCashbackRiskTest {
    private val flagged = Detection.Success(true, .8037948780036812, category = SmsCategory.SMISHING)
    private val ham = Detection.Success(false, .12, category = SmsCategory.HAM)
    private val text = "[EWB]You have PHP 5,216 available for cashback. Claim it before it expires today. https://eastwinfu.com/ph"
    private fun assess(value: String, result: Detection = flagged) =
        RiskPolicy.assess(value, result, linkedCashbackReview = true)

    @Test fun modelAndLinkedCashbackDeadlineCombineToHighRisk() {
        val risk = assess(text)
        assertEquals(70, risk.score)
        assertEquals(RiskLevel.HIGH, risk.level)
        assertTrue(risk.indicators.containsAll(listOf(RiskIndicator.MODEL_SIGNAL, RiskIndicator.CASHBACK_DEADLINE, RiskIndicator.LINK_PRESENT)))
        assertEquals(SmsCategory.SMISHING, flagged.category)
        assertEquals(40, RiskPolicy.assess(text, flagged).score)
    }

    @Test fun ruleDoesNotDependOnBankAmountOrTheReportedDomain() {
        for (value in listOf(text.replace("[EWB]", "[BPI]").replace("5,216", "950").replace("eastwinfu.com/ph", "example.invalid/redeem"),
            "A rebate is available. Collect it before midnight. https://example.invalid/rebate",
            "Cash back is available. Redeem it within 24 hours. https://example.invalid/claim"))
            assertEquals(value, RiskLevel.HIGH, assess(value).level)
    }

    @Test fun allSupportingPartsAreRequiredAndAModelFlagAloneStaysMedium() {
        for (value in listOf(text.substringBefore(" https://"),
            "Cashback is available. Claim it in the app. https://example.invalid/claim",
            "Your cashback expires today. https://example.invalid/offer",
            "Claim it before it expires today. https://example.invalid/offer",
            "Please review your account at https://example.invalid/account")) {
            val risk = assess(value)
            assertEquals(value, RiskLevel.MEDIUM, risk.level)
            assertFalse(value, risk.indicators.contains(RiskIndicator.CASHBACK_DEADLINE))
        }
    }

    @Test fun adviceAndCreditedCashbackDoNotTriggerTheRule() {
        for (value in listOf(
            "Never claim cashback before it expires today through message links. https://example.invalid/advice",
            "Do not redeem cashback before midnight from an unsolicited SMS. https://example.invalid/advice",
            "Your cashback was credited today. No action is required. https://example.invalid/notice",
            "Cashback is available in the official app. https://example.invalid/notice")) {
            assertFalse(value, assess(value, ham).indicators.contains(RiskIndicator.CASHBACK_DEADLINE))
            assertEquals(value, RiskLevel.LOW, assess(value, ham).level)
        }
    }

    @Test fun linkContentsAndMalformedLinksCannotSupplyTheProseEvidence() {
        for (value in listOf("Read https://example.invalid/claim-cashback-before-it-expires-today",
            "Cashback was credited. Read https://example.invalid/claim-before-it-expires-today",
            "Cashback is available. Claim it before it expires today. https://?invalid"))
            assertFalse(value, assess(value).indicators.contains(RiskIndicator.CASHBACK_DEADLINE))
    }

    @Test fun unflaggedMessagesAreNotPromotedToHighAndRepeatedCuesCountOnce() {
        assertEquals(30, assess(text, ham).score)
        assertEquals(RiskLevel.MEDIUM, assess(text, ham).level)
        assertEquals(70, assess((text + " ").repeat(5)).score)
        assertEquals(1, assess((text + " ").repeat(5)).indicators.count { it == RiskIndicator.CASHBACK_DEADLINE })
    }

    @Test fun applicationProfileOptsInOnlyForTheRequestedVariant() {
        if (BuildConfig.BUILD_TYPE in listOf("oldSvm", "usbDemo")) {
            assertEquals("linked-cashback-claim-deadline-v1", AppRiskPolicy.VERSION)
            assertEquals(70, AppRiskPolicy.assess(text, flagged).score)
        } else if (BuildConfig.BUILD_TYPE != "cashbackReview") {
            assertEquals(RiskPolicy.VERSION, AppRiskPolicy.VERSION)
            assertEquals(40, AppRiskPolicy.assess(text, flagged).score)
        }
    }
}
