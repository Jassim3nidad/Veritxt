package ph.smishguard

import android.Manifest
import android.app.Notification
import android.app.NotificationManager
import android.os.Build
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import ph.smishguard.sms.CheckPrompt

/**
 * End-to-end with a real modem SMS. Run with `-e modemPrompt true`, then from the host within 60 s:
 *   adb emu sms send 09171234567 "SGTEST BDO: Your account is on hold. Verify at sgtest-verify.example.com"
 */
class IncomingPromptModemTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    /**
     * Automatic warning from a real modem SMS. Uses a stub that behaves like the supplied experimental model
     * (the real model file is not in this repository). Run with `-e modemWarning true`, then send the SMS above.
     */
    @Test fun realSmsFlaggedByModelShowsAutomaticWarning() {
        assumeTrue(InstrumentationRegistry.getArguments().getString("modemWarning") == "true")
        val app = compose.activity.application as SoftwareTestApp
        val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
        automation.grantRuntimePermission(app.packageName, Manifest.permission.RECEIVE_SMS)
        if (Build.VERSION.SDK_INT >= 33) automation.grantRuntimePermission(app.packageName, Manifest.permission.POST_NOTIFICATIONS)
        val manager = app.getSystemService(NotificationManager::class.java)
        manager.cancelAll()
        app.testDetector = object : ph.smishguard.model.Detector {
            override val status = "Experimental model · test stub"
            override val automaticWarningsAllowed = true
            override suspend fun detect(text: String) = ph.smishguard.model.Detection.Success(text.contains("BDO"), .9, experimental = true)
        }
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard(); app.preferences.scanning(true) }
        try {
            var posted: Notification? = null
            val deadline = System.currentTimeMillis() + 60_000
            while (posted == null && System.currentTimeMillis() < deadline) {
                posted = manager.activeNotifications.firstOrNull { it.notification.channelId == ph.smishguard.sms.WarningNotifications.CHANNEL }?.notification
                if (posted == null) Thread.sleep(500)
            }
            assertNotNull("No automatic warning within 60 s of the SMS", posted)
            assertEquals("Possible scam text", posted!!.extras.getCharSequence(Notification.EXTRA_TITLE)?.toString())
            InstrumentationRegistry.getArguments().getString("pauseMs")?.toLongOrNull()?.let(Thread::sleep)
            posted.contentIntent.send()
            compose.waitUntil(10000) { compose.onAllNodesWithText("Likely scam").fetchSemanticsNodes().isNotEmpty() }
            assertTrue(manager.activeNotifications.none { it.notification.channelId == CheckPrompt.CHANNEL })
        } finally {
            app.testDetector = null
            runBlocking { app.preferences.scanning(false) }
        }
    }

    @Test fun realSmsShowsNeutralPromptAndCheckNowWorks() {
        assumeTrue(InstrumentationRegistry.getArguments().getString("modemPrompt") == "true")
        val app = compose.activity.application as SoftwareTestApp
        val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
        automation.grantRuntimePermission(app.packageName, Manifest.permission.RECEIVE_SMS)
        if (Build.VERSION.SDK_INT >= 33) automation.grantRuntimePermission(app.packageName, Manifest.permission.POST_NOTIFICATIONS)
        val manager = app.getSystemService(NotificationManager::class.java)
        manager.cancelAll()
        app.testDetector = null // the real detector of this build (no approved model) decides the path
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard(); app.preferences.scanning(true) }
        try {
            var posted: Notification? = null
            val deadline = System.currentTimeMillis() + 60_000
            while (posted == null && System.currentTimeMillis() < deadline) {
                posted = manager.activeNotifications.firstOrNull { it.notification.channelId == CheckPrompt.CHANNEL }?.notification
                if (posted == null) Thread.sleep(500)
            }
            assertNotNull("No check prompt within 60 s of the SMS", posted)
            val shown = listOf(Notification.EXTRA_TITLE, Notification.EXTRA_TEXT).joinToString(" ") { posted!!.extras.getCharSequence(it)?.toString().orEmpty() }
            assertEquals("New text received Check it with Veritxt before you tap any link.", shown)
            // Optional pause so a host script can screenshot the notification (-e pauseMs 8000).
            InstrumentationRegistry.getArguments().getString("pauseMs")?.toLongOrNull()?.let(Thread::sleep)
            posted!!.contentIntent.send()
            compose.waitUntil(10000) { compose.onAllNodesWithText("Check result").fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithText("Mentions BDO").performScrollTo().assertExists()
            compose.onAllNodesWithText("SGTEST", substring = true).assertCountEquals(0)
        } finally {
            runBlocking { app.preferences.scanning(false) }
        }
    }
}
