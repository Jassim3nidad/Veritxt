package ph.smishguard.sms

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.os.Build
import android.os.SystemClock
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import ph.smishguard.MainActivity
import ph.smishguard.R
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

/**
 * Message text waiting for the user to tap "Check now". Process memory only: never written to disk,
 * logs, intents, or saved state. Entries expire after [TTL_MS] or as soon as they are taken.
 */
object PendingChecks {
    const val TTL_MS = 10 * 60 * 1000L
    private class Entry(val text: String, val expiresAt: Long)
    private val entries = ConcurrentHashMap<String, Entry>()

    fun put(text: String): String {
        prune()
        return UUID.randomUUID().toString().also { entries[it] = Entry(text, SystemClock.elapsedRealtime() + TTL_MS) }
    }
    /** Returns the text once, or null if it expired, was dismissed, or the process restarted. */
    fun take(id: String): String? = entries.remove(id)?.takeIf { it.expiresAt > SystemClock.elapsedRealtime() }?.text
    fun discard(id: String) { entries.remove(id) }
    fun clear() = entries.clear()
    private fun prune() { val now = SystemClock.elapsedRealtime(); entries.entries.removeIf { it.value.expiresAt <= now } }
}

/**
 * Notifications about a new SMS. None of them ever show the message, the sender, or a link.
 * [Kind.PROMPT]: neutral "New text received — check it?" (no model can warn automatically).
 * [Kind.WARNING]: "Possible scam text" after the model flagged it. [Kind.TEST]: sample from Settings.
 */
object CheckPrompt {
    enum class Kind { PROMPT, WARNING, TEST }
    const val CHANNEL = "new_text_check"
    const val ACTION_CHECK = "ph.smishguard.action.CHECK_PENDING"
    const val ACTION_DISMISS = "ph.smishguard.action.DISMISS_PENDING"
    const val EXTRA_ID = "pending_id"
    const val EXTRA_NOTIFICATION = "notification_id"

    fun createChannel(context: Context) {
        val c = localized(context)
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL, c.getString(R.string.channel_check_name), NotificationManager.IMPORTANCE_HIGH).apply {
                description = c.getString(R.string.channel_check_desc)
                lockscreenVisibility = android.app.Notification.VISIBILITY_PRIVATE
            })
    }

    fun canNotify(context: Context): Boolean =
        PermissionState.read(context).notifications && (Build.VERSION.SDK_INT < 33 ||
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED)

    /** Holds [text] in memory and posts the notification. Returns its id, or null if notifications are off. */
    fun show(context: Context, text: String, kind: Kind = Kind.PROMPT): Int? {
        if (!canNotify(context)) return null
        val warning = kind == Kind.WARNING
        val channel = if (warning) WarningNotifications.CHANNEL else CHANNEL
        val c = localized(context)
        val id = PendingChecks.put(text)
        val notificationId = id.hashCode()
        val check = PendingIntent.getActivity(context, notificationId,
            Intent(context, MainActivity::class.java).setAction(ACTION_CHECK).putExtra(EXTRA_ID, id)
                .putExtra(EXTRA_NOTIFICATION, notificationId).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val dismiss = PendingIntent.getBroadcast(context, notificationId,
            Intent(context, PendingCheckReceiver::class.java).setAction(ACTION_DISMISS).putExtra(EXTRA_ID, id)
                .putExtra(EXTRA_NOTIFICATION, notificationId),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val builder = NotificationCompat.Builder(context, channel)
            .setSmallIcon(R.drawable.ic_stat_veritxt)
            .setColor(if (warning) 0xFFB3261E.toInt() else 0xFF1F6457.toInt())
            .setContentTitle(c.getString(when (kind) { Kind.WARNING -> R.string.warning_title; Kind.TEST -> R.string.notif_test_title; Kind.PROMPT -> R.string.notif_check_title }))
            .setContentText(c.getString(if (warning) R.string.warning_body else R.string.notif_check_body))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(check).setDeleteIntent(dismiss).setAutoCancel(true)
            .addAction(0, c.getString(if (warning) R.string.notif_action_see_why else R.string.notif_action_check), check)
            .addAction(0, c.getString(R.string.notif_action_dismiss), dismiss)
        // Warnings stay off the lock screen entirely (as before); prompts show a generic line there.
        if (warning) builder.setVisibility(NotificationCompat.VISIBILITY_SECRET)
        else builder.setVisibility(NotificationCompat.VISIBILITY_PRIVATE).setPublicVersion(NotificationCompat.Builder(context, channel)
            .setSmallIcon(R.drawable.ic_stat_veritxt).setContentTitle(c.getString(R.string.notif_check_public)).build())
        val notification = builder.build()
        return try { NotificationManagerCompat.from(context).notify(notificationId, notification); notificationId }
        catch (_: SecurityException) { PendingChecks.discard(id); null }
    }

    fun cancel(context: Context, notificationId: Int) = NotificationManagerCompat.from(context).cancel(notificationId)

    /** Notifications are posted outside an Activity, so apply the in-app language by hand. */
    fun localized(context: Context): Context {
        val locales = AppCompatDelegate.getApplicationLocales()
        if (locales.isEmpty) return context
        val config = Configuration(context.resources.configuration).apply { setLocales(android.os.LocaleList.forLanguageTags(locales.toLanguageTags())) }
        return context.createConfigurationContext(config)
    }
}

class PendingCheckReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != CheckPrompt.ACTION_DISMISS) return
        intent.getStringExtra(CheckPrompt.EXTRA_ID)?.let(PendingChecks::discard)
        CheckPrompt.cancel(context, intent.getIntExtra(CheckPrompt.EXTRA_NOTIFICATION, 0))
    }
}
