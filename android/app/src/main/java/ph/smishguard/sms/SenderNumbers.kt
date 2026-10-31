package ph.smishguard.sms

/** Numeric SMS origin only; never extracts a supposed sender from message text. */
object SenderNumbers {
    fun normalize(value: String?): String? {
        if (value.isNullOrEmpty() || value.length > 64 || value.any { it !in "0123456789+ ().-" }) return null
        val number = value.filter { it in "0123456789+" }
        return number.takeIf { Regex("\\+?[0-9]{3,15}").matches(it) }
    }

    /** Only associate multipart text with a number when every PDU agrees. */
    fun fromParts(addresses: List<String?>): String? {
        if (addresses.isEmpty()) return null
        val number = normalize(addresses.first()) ?: return null
        return number.takeIf { addresses.all { normalize(it) == number } }
    }
}

/** Short-lived in-process handoff. No generated toString containing message/sender data. */
class PendingSms(val text: String, val senderNumber: String?)
