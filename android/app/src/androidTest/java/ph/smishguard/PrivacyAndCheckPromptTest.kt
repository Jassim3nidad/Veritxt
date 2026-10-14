package ph.smishguard

import android.Manifest
import android.app.Notification
import android.app.NotificationManager
import android.os.Build
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.MissingDetector
import ph.smishguard.sms.CheckPrompt
import ph.smishguard.sms.PendingChecks

/** Privacy gate and the neutral "check this text?" notification. Messages are synthetic. */
class PrivacyAndCheckPromptTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val app get() = compose.activity.application as SoftwareTestApp
    private val manager get() = app.getSystemService(NotificationManager::class.java)
    private val marker = "SGTEST BDO account on hold, verify at sgtest-verify.example.com"

    @After fun reset() { app.testDetector = null; manager.cancelAll(); PendingChecks.clear() }

    @Test fun privacyNoticeMustBeAcceptedFirst() {
        runBlocking { app.preferences.clear() }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Your privacy").fetchSemanticsNodes().isNotEmpty() }
        compose.onAllNodesWithText("Home").assertCountEquals(0)
        compose.onNodeWithText("Agree and continue").performScrollTo().performClick()
        compose.onNodeWithText("Tick the box first to show you've read the notice.").assertExists()
        compose.onAllNodesWithText("Continue without permissions").assertCountEquals(0)
        compose.onNodeWithText("I have read and understood this notice").performScrollTo().performClick()
        compose.onNodeWithText("Agree and continue").performScrollTo().performClick()
        compose.waitUntil(10000) { compose.onAllNodesWithText("Continue without permissions").fetchSemanticsNodes().isNotEmpty() }
        assertTrue(runBlocking { app.preferences.flow.first().privacyAccepted })
    }

    @Test fun checkNowOpensAndChecksTheTextWithoutShowingItInTheNotification() {
        ready()
        val id = CheckPrompt.show(app, marker)
        assertNotNull("Notifications must be allowed for this test", id)
        val posted = posted(id!!)
        assertEquals(CheckPrompt.CHANNEL, posted.channelId)
        val shown = listOf(Notification.EXTRA_TITLE, Notification.EXTRA_TEXT, Notification.EXTRA_BIG_TEXT)
            .joinToString(" ") { posted.extras.getCharSequence(it)?.toString().orEmpty() }
        assertFalse("Notification must not contain the message", shown.contains("SGTEST") || shown.contains("example.com"))
        assertEquals(Notification.VISIBILITY_PRIVATE, posted.visibility)
        posted.contentIntent.send()
        compose.waitUntil(10000) { compose.onAllNodesWithText("Check result").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText(marker).assertExists()
        compose.onNodeWithText("Model unavailable", substring = false).assertExists()
        compose.onNodeWithText("Link goes to sgtest-verify.example.com, not an official site").performScrollTo().assertExists()
        assertTrue("Notification should be cancelled after Check now", manager.activeNotifications.none { it.id == id })
    }

    @Test fun automaticWarningIsPrivateAndSeeWhyShowsTheResult() {
        ready()
        app.testDetector = object : ph.smishguard.model.Detector {
            override val status = "Experimental model · test stub"
            override val automaticWarningsAllowed = true
            override suspend fun detect(text: String) = ph.smishguard.model.Detection.Success(true, .9, experimental = true)
        }
        val id = ph.smishguard.sms.WarningNotifications.warn(app, marker)!!
        val warning = posted(id)
        assertEquals(ph.smishguard.sms.WarningNotifications.CHANNEL, warning.channelId)
        assertEquals("Possible phishing (scam) text", warning.extras.getCharSequence(Notification.EXTRA_TITLE)?.toString())
        val shown = listOf(Notification.EXTRA_TITLE, Notification.EXTRA_TEXT).joinToString(" ") { warning.extras.getCharSequence(it)?.toString().orEmpty() }
        assertFalse("Warning must not contain the message", shown.contains("SGTEST") || shown.contains("example.com"))
        assertEquals(Notification.VISIBILITY_SECRET, warning.visibility)
        warning.contentIntent.send()
        compose.waitUntil(10000) { compose.onAllNodesWithText("Likely phishing (scam)").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Experimental result").assertExists()
        compose.onNodeWithText(marker).assertExists()
    }

    @Test fun expiredTextExplainsWhatToDo() {
        ready()
        val id = CheckPrompt.show(app, marker)!!
        val posted = posted(id)
        PendingChecks.clear() // same as the app process restarting before the tap
        posted.contentIntent.send()
        compose.waitUntil(10000) {
            compose.onAllNodesWithText("This message is no longer available", substring = true).fetchSemanticsNodes().isNotEmpty()
        }
    }

    /** Posting is asynchronous (notably on Android 11), so wait for the notification to appear. */
    private fun posted(id: Int): Notification {
        val deadline = System.currentTimeMillis() + 5000
        while (true) {
            manager.activeNotifications.firstOrNull { it.id == id }?.let { return it.notification }
            if (System.currentTimeMillis() > deadline) fail("Notification $id was not posted"); Thread.sleep(100)
        }
    }

    private fun ready() {
        if (Build.VERSION.SDK_INT >= 33) InstrumentationRegistry.getInstrumentation().uiAutomation
            .grantRuntimePermission(app.packageName, Manifest.permission.POST_NOTIFICATIONS)
        app.testDetector = MissingDetector()
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Before you tap,\ncheck the message.").fetchSemanticsNodes().isNotEmpty() }
        manager.cancelAll()
    }
}
