package ph.smishguard

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import ph.smishguard.ui.HintKind
import ph.smishguard.ui.Hints

class HintsTest {
    private fun kinds(text: String) = Hints.read(text).hints.map { it.kind }.toSet()

    @Test fun impersonationWithLookalikeLink() {
        val summary = Hints.read("BDO reminds you that your 7,352 points will expire today. Visit bdokwl.com/ph to redeem.")
        assertEquals("BDO", summary.brand)
        assertEquals(setOf(HintKind.BRAND, HintKind.LINK, HintKind.URGENCY, HintKind.BAIT), summary.hints.map { it.kind }.toSet())
        assertEquals("bdokwl.com", summary.hints.first { it.kind == HintKind.LINK }.detail)
    }
    @Test fun officialDomainIsNotFlagged() {
        assertTrue(HintKind.LINK !in kinds("Your GCash login was successful. Learn more at https://www.gcash.com/help"))
    }
    @Test fun credentialRequest() {
        assertTrue(HintKind.CREDENTIALS in kinds("Ibigay ang OTP mo para ma-verify ang account"))
    }
    @Test fun plainMessageHasNoHints() {
        assertEquals(emptySet<HintKind>(), kinds("Kumusta po, see you later sa bahay."))
    }
    @Test fun decimalsAreNotLinks() {
        assertTrue(HintKind.LINK !in kinds("Your bill is 1,234.50 pesos."))
    }
}
