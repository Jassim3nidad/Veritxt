package ph.smishguard.demo

import java.util.Base64
import org.junit.Assert.*
import org.junit.Test

class UsbDemoInputTest {
    private fun encode(text: String) = Base64.getEncoder().encodeToString(text.toByteArray(Charsets.UTF_8))
    @Test fun unicodeNewlinesAndShellCharactersSurviveTransport() {
        val text = "Kumusta po 😀\nMeeting sa café; \"quotes\" & literal ${'$'}(text)"
        assertEquals(text, UsbDemoReceiver.decode(encode(text)))
        assertEquals("a".repeat(10000), UsbDemoReceiver.decode(encode("a".repeat(10000))))
    }
    @Test fun malformedEmptyAndOversizedPayloadsAreRejected() {
        for (value in listOf(null, "!bad-base64", encode(" \n"), encode("a".repeat(10001)), "a".repeat(60001), "/w=="))
            assertNull(UsbDemoReceiver.decode(value))
    }
}
