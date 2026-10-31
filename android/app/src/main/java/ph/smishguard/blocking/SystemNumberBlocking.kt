package ph.smishguard.blocking

import android.content.Context
import android.provider.BlockedNumberContract
import android.telecom.TelecomManager

/** Opens Android's user-managed blocklist; never reads or changes its entries. */
object SystemNumberBlocking {
    fun openSettings(context: Context): Boolean = try {
        if (!BlockedNumberContract.canCurrentUserBlockNumbers(context)) false
        else {
            val telecom = context.getSystemService(TelecomManager::class.java)
            val intent = telecom?.createManageBlockedNumbersIntent()
            if (intent == null) false
            else {
                // No message, extracted number, or sender identity is passed to another app.
                context.startActivity(intent)
                true // This confirms the handoff only, never that a number was blocked.
            }
        }
    } catch (_: RuntimeException) {
        // Missing activities, restricted users, and unavailable OEM services use instructions.
        false
    }
}
