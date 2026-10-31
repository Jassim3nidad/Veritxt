package ph.smishguard

import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.sms.SenderNumbers

class SenderNumbersTest {
    @Test fun acceptsOnlyNumericOriginsAndNormalizesFormatting() {
        assertEquals("+16505550100", SenderNumbers.normalize("+1 (650) 555-0100"))
        assertEquals("215800", SenderNumbers.normalize("215800"))
        for (value in listOf(null, "", "BDO", "sender@example.com", "+12", "1234567890123456", "12+345", "123\n456", "１２３４５６", "123\u202e456"))
            assertNull(SenderNumbers.normalize(value))
    }

    @Test fun multipartOriginsMustAllAgree() {
        assertEquals("+16505550100", SenderNumbers.fromParts(listOf("+16505550100", "+1 (650) 555-0100")))
        assertNull(SenderNumbers.fromParts(emptyList()))
        assertNull(SenderNumbers.fromParts(listOf(null)))
        assertNull(SenderNumbers.fromParts(listOf("+16505550100", null)))
        assertNull(SenderNumbers.fromParts(listOf("+16505550100", "+16505550199")))
        assertNull(SenderNumbers.fromParts(listOf("GCash", "GCash")))
    }
}
