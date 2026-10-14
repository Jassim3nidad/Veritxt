package ph.smishguard.sms

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Telephony
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeout
import ph.smishguard.MainActivity
import ph.smishguard.R
import ph.smishguard.SmishGuardApp
import ph.smishguard.model.Detection
import ph.smishguard.model.MAX_MESSAGE_LENGTH

data class PermissionState(val telephony: Boolean, val sms: Boolean, val notifications: Boolean) {
    fun active(consent: Boolean) = consent && telephony && sms
    companion object {
        fun read(context: Context) = PermissionState(
            context.packageManager.hasSystemFeature(PackageManager.FEATURE_TELEPHONY),
            ContextCompat.checkSelfPermission(context, Manifest.permission.RECEIVE_SMS) == PackageManager.PERMISSION_GRANTED,
            NotificationManagerCompat.from(context).areNotificationsEnabled() &&
                context.getSystemService(NotificationManager::class.java).getNotificationChannel(WarningNotifications.CHANNEL)?.importance != NotificationManager.IMPORTANCE_NONE
        )
    }
}

object SmsParts {
    /** Android assembles one broadcast's PDUs in segment order. No sender is read. */
    fun combine(parts: List<String?>): String? {
        if (parts.isEmpty() || parts.size > 100 || parts.any { it == null }) return null
        if (parts.sumOf { it!!.length } > MAX_MESSAGE_LENGTH) return null
        return parts.joinToString("").takeIf { it.isNotBlank() }
    }
}

class IncomingSmsReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return
        if (!PermissionState.read(context).active(true)) return
        val pending = goAsync()
        val app = context.applicationContext as SmishGuardApp
        CoroutineScope(SupervisorJob() + Dispatchers.Default).launch {
            try {
                withTimeout(7000) {
                    val prefs = app.preferences.flow.first()
                    if (!prefs.scanning || !prefs.privacyAccepted) return@withTimeout
                    val parts = Telephony.Sms.Intents.getMessagesFromIntent(intent)
                    val text = SmsParts.combine(parts.map { it.messageBody }) ?: return@withTimeout
                    val detector = app.detector()
                    if (!detector.automaticWarningsAllowed) {
                        // No model can warn automatically (e.g. none installed), so ask the user instead of judging.
                        // The prompt carries no verdict; the check runs only after the user taps "Check now".
                        CheckPrompt.show(context, text)
                        return@withTimeout
                    }
                    val result = app.assess(text)
                    // Warn only when the model flags the text. Experimental results may warn (labelled as such in the
                    // app); synthetic test fixtures never do. Consent and permission are re-read after the check.
                    if (result is Detection.Success && result.suspicious && !result.synthetic &&
                        app.preferences.flow.first().scanning && PermissionState.read(context).active(true)) {
                        WarningNotifications.warn(context, text)
                    }
                }
            } catch (_: Exception) {
                // No input/exception logging: vendor exceptions can contain private SMS data.
            } finally { pending.finish() }
        }
    }
}

object WarningNotifications {
    const val CHANNEL = "suspected_financial_impersonation"
    fun createChannel(context: Context) {
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL, CheckPrompt.localized(context).getString(R.string.channel_warning_name), NotificationManager.IMPORTANCE_HIGH).apply {
                description = CheckPrompt.localized(context).getString(R.string.channel_warning_desc)
                lockscreenVisibility = android.app.Notification.VISIBILITY_SECRET
            })
    }
    /** Posts "Possible phishing (scam) text" (no message content); "See why" opens Veritxt and shows the result. */
    fun warn(context: Context, text: String): Int? = CheckPrompt.show(context, text, CheckPrompt.Kind.WARNING)
}
