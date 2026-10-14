package ph.smishguard.model

import java.util.Locale

object ResultCopy {
    fun heading(result: Detection.Success): String =
        if (result.suspicious) "Likely phishing (scam)" else "No phishing (scam) detected"
    fun score(value: Double): String =
        String.format(Locale.ROOT, "Model score: %.1f%%", value * 100)
    const val LONG_MESSAGE = "Long message: only the beginning was assessed."
    const val DISCLAIMER = "Experimental score; not a verified probability."
}
