package ph.smishguard

import android.Manifest
import android.app.Notification
import android.app.NotificationManager
import android.os.Build
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import ph.smishguard.sms.CheckPrompt

/**
 * End-to-end with a real modem SMS. Run with `-e modemPrompt true`, then from the host within 60 s:
 *   adb emu sms send 5550100 "SGTEST BDO: Your account is on hold. Verify at sgtest-verify.example.com"
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
        val realModel = InstrumentationRegistry.getArguments().getString("realModel") == "true"
        app.testDetector = if (realModel) null else object : ph.smishguard.model.Detector {
            override val status = "Experimental model · test stub"
            override val automaticWarningsAllowed = true
            override suspend fun detect(text: String) = ph.smishguard.model.Detection.Success(text.contains("BDO"), .9, experimental = true)
        }
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard(); app.preferences.scanning(true) }
        val signal = java.io.File(app.filesDir, "automatic-warning-ready")
        if (realModel) {
            assertTrue(runBlocking { app.detector() }.automaticWarningsAllowed)
            signal.writeText("ready")
        }
        try {
            var posted: Notification? = null
            val deadline = System.currentTimeMillis() + 60_000
            while (posted == null && System.currentTimeMillis() < deadline) {
                posted = manager.activeNotifications.firstOrNull { it.notification.channelId == ph.smishguard.sms.WarningNotifications.CHANNEL }?.notification
                if (posted == null) Thread.sleep(500)
            }
            assertNotNull("No automatic warning within 60 s of the SMS", posted)
            assertTrue(posted!!.extras.getCharSequence(Notification.EXTRA_TITLE).toString().endsWith("· High Risk"))
            val expectedSender = InstrumentationRegistry.getArguments().getString("expectedSender")
            if (expectedSender != null) assertTrue(posted.extras.toString().contains(expectedSender))
            assertEquals(Notification.VISIBILITY_SECRET, posted.visibility)
            InstrumentationRegistry.getArguments().getString("pauseMs")?.toLongOrNull()?.let(Thread::sleep)
            posted.contentIntent.send()
            compose.waitUntil(10000) { compose.onAllNodesWithText("High Risk").fetchSemanticsNodes().isNotEmpty() }
            if (expectedSender != null) {
                compose.onNodeWithText("Sender: $expectedSender").assertExists()
                compose.onNodeWithText("Block sender").performScrollTo().assertIsDisplayed()
                compose.onNodeWithText("Block sender").performClick()
                compose.onNodeWithText("Block this sender?").assertExists()
                compose.onAllNodesWithText("Sender: $expectedSender").assertCountEquals(2)
                if (InstrumentationRegistry.getArguments().getString("shot") == "true") {
                    val bitmap = compose.onNode(isDialog()).captureToImage().asAndroidBitmap()
                    val directory = java.io.File(app.filesDir, "visual-review").apply { mkdirs() }
                    java.io.File(directory, "sender-block-confirmation.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
                    bitmap.recycle()
                }
                compose.onNodeWithText("Cancel").performClick()
            }
            assertTrue(manager.activeNotifications.none { it.notification.channelId == CheckPrompt.CHANNEL })
            if (InstrumentationRegistry.getArguments().getString("shot") == "true") captureResult(app)
        } finally {
            signal.delete()
            app.testDetector = null
            runBlocking { app.preferences.scanning(false) }
        }
    }

    /** Test-only native rendering, excluding other apps' notifications. */
    private fun captureResult(app: SoftwareTestApp) {
        compose.waitForIdle()
        lateinit var bitmap: android.graphics.Bitmap
        compose.activityRule.scenario.onActivity {
            val view = it.window.decorView
            bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
        }
        val dir = java.io.File(app.filesDir, "visual-review").apply { mkdirs() }
        java.io.File(dir, "warning-result.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
        bitmap.recycle()
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
            assertTrue(shown.contains("· Unable to assess"))
            assertTrue(posted!!.extras.getCharSequence(Notification.EXTRA_BIG_TEXT).toString().contains("Automatic scan unavailable"))
            assertEquals(Notification.VISIBILITY_SECRET, posted!!.visibility)
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
