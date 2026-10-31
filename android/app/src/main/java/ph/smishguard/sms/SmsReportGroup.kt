package ph.smishguard.sms

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Handler
import android.os.Looper
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import ph.smishguard.R

/** One native group header; every received SMS retains its own child and independent actions. */
object SmsReportGroup {
    const val KEY = "veritxt.sms.reports"
    const val CHANNEL = "sms_report_summary"
    const val TAG = "sms_report_summary"
    const val ID = 1
    const val ACTION_CLEAR = "ph.smishguard.action.CLEAR_SMS_REPORTS"
    private val handler = Handler(Looper.getMainLooper())

    fun createChannel(context: Context) {
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL, CheckPrompt.localized(context).getString(R.string.notif_group_channel),
                NotificationManager.IMPORTANCE_LOW).apply {
                lockscreenVisibility = Notification.VISIBILITY_PUBLIC
                setShowBadge(false)
            })
    }

    fun children(context: Context) = context.getSystemService(NotificationManager::class.java)
        .activeNotifications.filter { it.notification.group == KEY && it.notification.flags and Notification.FLAG_GROUP_SUMMARY == 0 }

    fun schedule(context: Context) {
        // NotificationManager publishes asynchronously. Re-read actual active children, including swipes.
        val app = context.applicationContext
        handler.postDelayed({ refresh(app) }, 150)
        handler.postDelayed({ refresh(app) }, 500)
    }

    @Synchronized fun refresh(context: Context) {
        val reports = children(context)
        val manager = NotificationManagerCompat.from(context)
        if (reports.isEmpty()) { manager.cancel(TAG, ID); return }
        val hasHeader = context.getSystemService(NotificationManager::class.java).activeNotifications.any { it.tag == TAG }
        // Cancelling an existing group summary can cancel its last child too. Keep a one-report
        // header until the last report is opened/dismissed, but don't add a header to the first SMS.
        if (reports.size == 1 && !hasHeader) return
        val c = CheckPrompt.localized(context)
        val dismiss = PendingIntent.getBroadcast(context, 0,
            Intent(context, PendingCheckReceiver::class.java).setAction(ACTION_CLEAR),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val count = if (reports.size == 1) c.getString(R.string.notif_group_single)
            else c.getString(R.string.notif_group_title, reports.size)
        val countLabel = if (reports.all { it.notification.extras.getBoolean(CheckPrompt.EXTRA_DEMO) }) "Demo · $count" else count
        val notification = NotificationCompat.Builder(context, CHANNEL)
            .setSmallIcon(R.drawable.ic_stat_veritxt)
            .setContentTitle(countLabel)
            // Android's collapsed group header can hide the normal title; keep the count there too.
            .setSubText(countLabel)
            .setContentText(c.getString(R.string.notif_group_body))
            .setNumber(reports.size)
            .setGroup(KEY).setGroupSummary(true)
            .setGroupAlertBehavior(NotificationCompat.GROUP_ALERT_CHILDREN)
            .setOnlyAlertOnce(true).setDeleteIntent(dismiss)
            // This header contains counts and instructions only, never senders, text or risk details.
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .build()
        try { manager.notify(TAG, ID, notification) } catch (_: SecurityException) { /* permission revoked */ }
    }

    fun clear(context: Context) {
        val manager = NotificationManagerCompat.from(context)
        children(context).forEach {
            it.tag?.let(PendingChecks::discard)
            manager.cancel(it.tag, it.id)
        }
        manager.cancel(TAG, ID)
    }
}
