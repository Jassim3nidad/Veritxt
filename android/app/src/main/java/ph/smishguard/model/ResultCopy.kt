package ph.smishguard.model

import java.util.Locale

object ResultCopy {
    fun heading(result: Detection.Success): String =
        if (result.suspicious) "Likely phishing" else "No phishing detected"
    fun score(value: Double): String =
        String.format(Locale.ROOT, "%.1f%% phishing model score", value * 100)
    const val DISCLAIMER = "Experimental score; not a verified probability."
}
