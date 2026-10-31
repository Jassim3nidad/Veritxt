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
import kotlinx.coroutines.withTimeoutOrNull
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.delay
import ph.smishguard.MainActivity
import ph.smishguard.BuildConfig
import ph.smishguard.R
import ph.smishguard.SmishGuardApp
import ph.smishguard.model.MAX_MESSAGE_LENGTH
import ph.smishguard.model.AppRiskPolicy as RiskPolicy
import ph.smishguard.model.RiskLevel
import ph.smishguard.model.Detection

data class PermissionState(val telephony: Boolean, val sms: Boolean, val notifications: Boolean) {
    fun active(consent: Boolean) = consent && telephony && sms
    companion object {
        fun read(context: Context, channel: String? = null) = PermissionState(
            context.packageManager.hasSystemFeature(PackageManager.FEATURE_TELEPHONY),
            ContextCompat.checkSelfPermission(context, Manifest.permission.RECEIVE_SMS) == PackageManager.PERMISSION_GRANTED,
            NotificationManagerCompat.from(context).areNotificationsEnabled() &&
                (channel?.let { listOf(it) } ?: listOf(CheckPrompt.CHANNEL, WarningNotifications.CHANNEL)).any {
                    context.getSystemService(NotificationManager::class.java).getNotificationChannel(it)?.importance != NotificationManager.IMPORTANCE_NONE
                }
        )
    }
}

object SmsParts {
    /** Android assembles one broadcast's PDUs in segment order. */
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
                    val senderNumber = SenderNumbers.fromParts(parts.map { it.originatingAddress })
                    IncomingSmsNotifications.show(app, text, senderNumber)
                }
            } catch (_: Exception) {
                // No input/exception logging: vendor exceptions can contain private SMS data.
            } finally { pending.finish() }
        }
    }
}

/** Every received SMS gets one initial report; only High Risk uses the warning channel. */
object IncomingSmsNotifications {
    suspend fun show(app: SmishGuardApp, text: String, senderNumber: String? = null, demo: Boolean = false): Int? {
        if (demo && !BuildConfig.USB_DEMO_ENABLED) return null
        if (text.isBlank() || text.length > MAX_MESSAGE_LENGTH) return null
        suspend fun enabled(): Boolean {
            val prefs = app.preferences.flow.first()
            val permissions = PermissionState.read(app)
            return prefs.privacyAccepted && permissions.notifications && (demo || permissions.active(prefs.scanning))
        }
        if (!enabled()) return null
        // Leave time within the receiver's deadline to report an unavailable scan if inference fails.
        val report = try {
            withTimeoutOrNull(5000) {
                if (!app.detector().automaticWarningsAllowed) return@withTimeoutOrNull null
                var detection = app.assess(text)
                // Nearby SMS may share the inference permit. Retry within this receiver's deadline.
                while (detection == Detection.Busy) {
                    delay(50)
                    detection = app.assess(text)
                }
                InitialSmsReport(RiskPolicy.assess(text, detection), (detection as? Detection.Success)?.category)
            }
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (_: Exception) {
            null // Model errors still produce an explicit, unscored report.
        } ?: InitialSmsReport(RiskPolicy.assess(text, Detection.Failure))
        // Consent and permissions may have changed while the model was running.
        if (!enabled()) return null
        return CheckPrompt.show(app, text,
            kind = if (report.assessment.level == RiskLevel.HIGH) CheckPrompt.Kind.WARNING else CheckPrompt.Kind.PROMPT,
            senderNumber = senderNumber, report = report, demo = demo)
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
    /** Posts a generic High Risk SMS notification; "See why" opens the result. Never blocks a number. */
    fun warn(context: Context, text: String, senderNumber: String? = null): Int? = CheckPrompt.show(context, text, CheckPrompt.Kind.WARNING, senderNumber)
}
