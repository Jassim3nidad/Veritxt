package ph.smishguard

import android.Manifest
import android.app.Notification
import android.app.NotificationManager
import android.os.Build
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.AppRiskPolicy
import ph.smishguard.sms.CheckPrompt
import ph.smishguard.sms.PendingChecks
import ph.smishguard.sms.WarningNotifications

/** Host sends three actual modem SMS together, then every notification opens its own result. */
class InitialSmsBurstTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun threeIncomingSmsHaveIndependentInitialReports() {
        assumeTrue(InstrumentationRegistry.getArguments().getString("initialReportBurst") == "true")
        val app = compose.activity.application as SoftwareTestApp
        val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
        automation.grantRuntimePermission(app.packageName, Manifest.permission.RECEIVE_SMS)
        if (Build.VERSION.SDK_INT >= 33) automation.grantRuntimePermission(app.packageName, Manifest.permission.POST_NOTIFICATIONS)
        app.testDetector = null
        val manager = app.getSystemService(NotificationManager::class.java)
        manager.cancelAll(); PendingChecks.clear()
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard(); app.preferences.scanning(true) }
        val cases = listOf(
            Triple("5550301", "SGTEST Kita tayo bukas sa opisina. Ingat sa biyahe.", "Low Risk SMS"),
            Triple("5550302", "SGTEST Your accumulated 7,894.50 Philippine Pesos in cash expires today, or you can choose an https://example.invalid", "Medium Risk SMS"),
            Triple("5550303", "SGTEST Your account is suspended. Send your OTP and PIN to https://example.invalid/account immediately.", "High Risk SMS")
        )
        val ready = File(app.filesDir, "initial-report-burst-ready")
        try {
            ready.writeText("ready")
            fun notifications() = manager.activeNotifications.filter {
                it.notification.channelId in listOf(CheckPrompt.CHANNEL, WarningNotifications.CHANNEL) &&
                    it.notification.flags and Notification.FLAG_GROUP_SUMMARY == 0
            }
            val deadline = android.os.SystemClock.uptimeMillis() + 45000
            while (notifications().size < cases.size && android.os.SystemClock.uptimeMillis() < deadline) Thread.sleep(50)
            val posted = notifications()
            assertEquals(3, posted.size)
            assertEquals(3, posted.map { it.id }.distinct().size)
            assertEquals(cases.map { (sender, _, title) -> "$sender · " + title.removeSuffix(" SMS") }.toSet(),
                posted.map { it.notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString() }.toSet())
            val records = JSONArray()
            for ((sender, text, title) in cases) {
                val notification = posted.single { it.notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString().startsWith(sender) }.notification
                val body = notification.extras.getCharSequence(Notification.EXTRA_BIG_TEXT).toString()
                assertEquals(ph.smishguard.sms.SmsNotificationPreview.text(text), notification.extras.getCharSequence(Notification.EXTRA_TEXT).toString())
                assertEquals(Notification.VISIBILITY_SECRET, notification.visibility)
                assertEquals("View report", notification.actions.first().title.toString())
                notification.contentIntent.send()
                compose.waitUntil(10000) {
                    ViewModelProvider(compose.activity)[CheckViewModel::class.java].state.value.let {
                        it.checkedMessage == text && it.senderNumber == sender && it.assessment != null
                    }
                }
                compose.activityRule.scenario.onActivity {
                    val state = ViewModelProvider(it)[CheckViewModel::class.java].state.value
                    val risk = AppRiskPolicy.assess(text, state.result)
                    assertTrue(body.contains("Risk Score: ${risk.score}/100"))
                    records.put(JSONObject().put("sender", sender).put("title", title)
                        .put("initial_report", body).put("risk_score", risk.score).put("exact_message_opened", true))
                }
            }
            File(app.filesDir, "initial-report-burst-result.json").writeText(JSONObject()
                .put("notification_count", posted.size).put("cases", records).toString(2))
        } finally {
            ready.delete()
            runBlocking { app.preferences.scanning(false) }
        }
    }

    @Test fun fiveIdenticalSmsFromOneSenderHaveFiveIndependentNotifications() {
        assumeTrue(InstrumentationRegistry.getArguments().getString("oneToOneBurst") == "true")
        val app = compose.activity.application as SoftwareTestApp
        val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
        automation.grantRuntimePermission(app.packageName, Manifest.permission.RECEIVE_SMS)
        if (Build.VERSION.SDK_INT >= 33) automation.grantRuntimePermission(app.packageName, Manifest.permission.POST_NOTIFICATIONS)
        app.testDetector = null
        val manager = app.getSystemService(NotificationManager::class.java)
        manager.cancelAll(); PendingChecks.clear()
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard(); app.preferences.scanning(true) }
        val ready = File(app.filesDir, "one-to-one-ready")
        val sender = "5550601"
        val text = "SGTEST Kita tayo bukas sa opisina. Ingat sa biyahe."
        try {
            ready.writeText("ready")
            fun reports() = manager.activeNotifications.filter {
                it.notification.flags and Notification.FLAG_GROUP_SUMMARY == 0 &&
                    it.notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString() == "5550601 · Low Risk"
            }
            val deadline = android.os.SystemClock.uptimeMillis() + 45000
            while (reports().size < 5 && android.os.SystemClock.uptimeMillis() < deadline) Thread.sleep(50)
            val posted = reports()
            assertEquals("Five modem SMS must produce exactly five Veritxt notifications", 5, posted.size)
            assertEquals(5, posted.map { it.tag }.distinct().size)
            assertEquals(5, posted.map { it.key }.distinct().size)
            assertTrue(posted.all { it.tag != null && it.notification.flags and Notification.FLAG_GROUP_SUMMARY == 0 })
            assertTrue(posted.all { it.notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString() == "5550601 · Low Risk" })
            compose.waitUntil(10000) {
                manager.activeNotifications.any {
                    it.tag == ph.smishguard.sms.SmsReportGroup.TAG &&
                        it.notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString() == "5 SMS reports"
                }
            }
            val platformSummaries = manager.activeNotifications.count { it.notification.flags and Notification.FLAG_GROUP_SUMMARY != 0 }
            val remaining = posted.map { it.tag }.toMutableSet()
            val dismissed = posted.first()
            dismissed.notification.actions[1].actionIntent.send()
            remaining.remove(dismissed.tag)
            compose.waitUntil(10000) { reports().map { it.tag }.toSet() == remaining }
            assertNull(PendingChecks.take(requireNotNull(dismissed.tag)))
            for (item in posted.drop(1)) {
                item.notification.contentIntent.send()
                remaining.remove(item.tag)
                compose.waitUntil(10000) {
                    val state = ViewModelProvider(compose.activity)[CheckViewModel::class.java].state.value
                    reports().map { it.tag }.toSet() == remaining &&
                        state.checkedMessage == text && state.senderNumber == sender && state.assessment != null
                }
            }
            File(app.filesDir, "one-to-one-result.json").writeText(JSONObject()
                .put("incoming_sms", 5).put("veritxt_notifications", posted.size)
                .put("distinct_tags", posted.map { it.tag }.distinct().size)
                .put("distinct_notification_keys", posted.map { it.key }.distinct().size)
                .put("platform_summary_count", platformSummaries).put("same_sender_and_body", true)
                .put("dismiss_only_removes_its_message", true).put("open_only_removes_its_message", true)
                .put("remaining_sms_reports", reports().size).toString(2))
        } finally {
            ready.delete()
            runBlocking { app.preferences.scanning(false) }
        }
    }
}
