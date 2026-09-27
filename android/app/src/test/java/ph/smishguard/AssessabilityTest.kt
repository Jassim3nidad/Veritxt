package ph.smishguard

import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.*
import java.util.Locale

class AssessabilityTest {
    private val known = setOf("hi", "ok", "po", "bayad", "na", "your", "otp", "verify", "account")
    private fun assess(text: String) = Assessability.canAssess(
        Assessability.textOutsideLinks(text).lowercase().split(Regex("\\W+")), known::contains)

    @Test fun emptyUnknownAndKeyboardInputsAbstain() {
        for (text in listOf("", "  \n", "xqzvplmkj", "zorbquux flarnquux", "asdfghjkl", "qwerty", "zzzzzz"))
            assertFalse(assess(text))
        assertFalse(Assessability.canAssess(listOf("asdf", "aaaa", "1234", "a")) { true })
    }
    @Test fun noMinimumWordCountOrCoverageRatio() {
        for (text in listOf("Hi", "OK", "Bayad na po", "your OTP 123456", "verify account",
            "hi " + "zorbquux ".repeat(50))) assertTrue(assess(text))
    }
    @Test fun linksAndNumericTokensCannotBeTheOnlyEvidence() {
        for (text in listOf("123456", "https://account.example/verify", "www.account.example", "account.example/verify 123"))
            assertFalse(assess(text))
        assertTrue(assess("verify https://account.example 123456"))
    }
    @Test fun scoreFormattingIsStableAndUsesActualValue() {
        val prior = Locale.getDefault()
        try {
            Locale.setDefault(Locale.GERMANY)
            assertEquals("Model score: 92.3%", ResultCopy.score(.9229))
            assertEquals("Model score: 33.6%", ResultCopy.score(.336317))
            assertEquals("Model score: 0.0%", ResultCopy.score(0.0))
            assertEquals("Model score: 100.0%", ResultCopy.score(1.0))
            assertEquals("No phishing detected", ResultCopy.heading(Detection.Success(false, .5)))
            assertEquals("Likely phishing", ResultCopy.heading(Detection.Success(true, .50001)))
        } finally { Locale.setDefault(prior) }
    }
}
