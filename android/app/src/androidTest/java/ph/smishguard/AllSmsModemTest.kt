package ph.smishguard

import android.Manifest
import android.app.Notification
import android.app.NotificationManager
import android.os.Build
import android.util.Base64
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.*
import ph.smishguard.sms.*

/** Host injects one synthetic modem SMS after the readiness signal, using the real bundled model. */
class AllSmsModemTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun everyRiskLevelNotifiesAndOpensItsOwnMessage() {
        val args = InstrumentationRegistry.getArguments()
        assumeTrue(args.containsKey("allSmsRisk"))
        val expected = RiskLevel.valueOf(args.getString("allSmsRisk")!!)
        val text = String(Base64.decode(args.getString("messageBase64"), Base64.DEFAULT), Charsets.UTF_8)
        val app = compose.activity.application as SoftwareTestApp
        val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
        automation.grantRuntimePermission(app.packageName, Manifest.permission.RECEIVE_SMS)
        if (Build.VERSION.SDK_INT >= 33) automation.grantRuntimePermission(app.packageName, Manifest.permission.POST_NOTIFICATIONS)
        app.testDetector = null
        val manager = app.getSystemService(NotificationManager::class.java)
        manager.cancelAll(); PendingChecks.clear()
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard(); app.preferences.scanning(true) }
        val ready = File(app.filesDir, "all-sms-modem-ready")
        try {
            ready.writeText("ready")
            val deadline = android.os.SystemClock.uptimeMillis() + 45000
            var posted: Notification? = null
            while (posted == null && android.os.SystemClock.uptimeMillis() < deadline) {
                posted = manager.activeNotifications.firstOrNull {
                    it.notification.channelId in listOf(CheckPrompt.CHANNEL, WarningNotifications.CHANNEL)
                }?.notification
                if (posted == null) Thread.sleep(100)
            }
            assertNotNull("No notification for $expected SMS", posted)
            assertEquals("Exactly one notification per SMS", 1, manager.activeNotifications.size)
            val warning = expected == RiskLevel.HIGH
            assertEquals(if (warning) WarningNotifications.CHANNEL else CheckPrompt.CHANNEL, posted!!.channelId)
            assertEquals("5550100 · " + app.getString(ph.smishguard.ui.RiskPresentation.label(expected)),
                posted.extras.getCharSequence(Notification.EXTRA_TITLE).toString())
            assertEquals("View report", posted.actions.first().title.toString())
            assertNotNull("The real incoming-SMS notification needs a gauge", posted.getLargeIcon())
            assertEquals(SmsNotificationPreview.text(text), posted.extras.getCharSequence(Notification.EXTRA_TEXT).toString())
            assertEquals(Notification.VISIBILITY_SECRET, posted.visibility)
            assertNull(posted.publicVersion)
            val record = JSONObject().put("expected_risk", expected.name).put("notification_count", 1)
                .put("channel", posted.channelId).put("title", posted.extras.getCharSequence(Notification.EXTRA_TITLE))
                .put("initial_report", posted.extras.getCharSequence(Notification.EXTRA_BIG_TEXT))
                .put("preview", posted.extras.getCharSequence(Notification.EXTRA_TEXT))
                .put("expanded_report", posted.extras.getCharSequence(Notification.EXTRA_BIG_TEXT))
                .put("risk_gauge_present", posted.getLargeIcon() != null)
            posted.contentIntent.send()
            compose.waitUntil(10000) { compose.onAllNodesWithText("Check result").fetchSemanticsNodes().isNotEmpty() }
            compose.activityRule.scenario.onActivity {
                val state = ViewModelProvider(it)[CheckViewModel::class.java].state.value
                assertEquals(text, state.checkedMessage)
                val risk = AppRiskPolicy.assess(text, state.result)
                assertEquals(expected, risk.level)
                val body = posted.extras.getCharSequence(Notification.EXTRA_BIG_TEXT).toString()
                if (risk.score != null) assertTrue(body.contains("Risk Score: ${risk.score}/100"))
                else assertFalse(body.contains("/100"))
                (state.result as? Detection.Success)?.category?.let {
                    assertTrue(body.contains(when (it) { SmsCategory.HAM -> "Ham"; SmsCategory.SMISHING -> "Smishing"; SmsCategory.GAMBLING -> "Gambling" }))
                }
                record.put("result_risk", risk.level.name).put("risk_score", risk.score ?: JSONObject.NULL)
                    .put("message_matches", true).put("api", Build.VERSION.SDK_INT)
            }
            File(app.filesDir, "all-sms-modem-result.json").writeText(record.toString(2))
        } finally {
            ready.delete()
            runBlocking { app.preferences.scanning(false) }
        }
    }
}
