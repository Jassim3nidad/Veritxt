package ph.smishguard

import android.content.ClipboardManager
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.Detection
import ph.smishguard.model.Detector
import ph.smishguard.sms.PendingChecks
import ph.smishguard.blocking.SenderNumberClipboard

class SenderBlockingTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val sender = "+16505550100"
    private val body = "Send your password to +16505550199 immediately"
    private val app get() = compose.activity.application as SoftwareTestApp
    private val vm get() = ViewModelProvider(compose.activity)[CheckViewModel::class.java]

    @After fun reset() { app.testDetector = null; PendingChecks.clear() }

    private fun received() {
        app.testDetector = object : Detector {
            override val status = "Sender UI software fixture"
            override suspend fun detect(text: String) = Detection.Success(false, .1)
        }
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        compose.activityRule.scenario.onActivity { vm.checkPending(body, sender) }
        compose.waitUntil(10000) { compose.onAllNodesWithText("High Risk").fetchSemanticsNodes().isNotEmpty() }
    }

    @Test fun actualSenderIsShownAndCopiedOnlyByChoiceInsteadOfBodyNumber() {
        received()
        compose.onNodeWithText("Sender: $sender").assertExists()
        compose.onNodeWithText("Block sender").performScrollTo().performClick()
        compose.onNodeWithText("Block this sender?").assertExists()
        compose.onAllNodesWithText("Sender: $sender").assertCountEquals(2)
        val clipboard = compose.activity.getSystemService(ClipboardManager::class.java)
        val previous = clipboard.primaryClip
        try {
            compose.onNodeWithText("Copy sender number").performScrollTo().performClick()
            compose.onNodeWithText("Sender number copied").assertExists()
            compose.runOnIdle {
                assertEquals(sender, clipboard.primaryClip!!.getItemAt(0).text.toString())
            }
        } finally {
            compose.runOnIdle {
                if (previous != null) clipboard.setPrimaryClip(previous)
                else if (android.os.Build.VERSION.SDK_INT >= 28) clipboard.clearPrimaryClip()
                else clipboard.setPrimaryClip(android.content.ClipData.newPlainText("", ""))
            }
        }
        compose.onNodeWithText("Cancel").performClick()
        compose.onNodeWithText("Block this sender?").assertDoesNotExist()
    }

    @Test fun senderIsClearedWhenLeavingResultOrEditingAndNeverInferredFromPaste() {
        received()
        compose.onNodeWithText("Review reporting options").performScrollTo().performClick()
        compose.runOnIdle { assertNull(vm.state.value.senderNumber) }
        compose.onNodeWithText("Back to result").performScrollTo().performClick()
        compose.onNodeWithText("Sender: $sender").assertDoesNotExist()
        compose.activityRule.scenario.onActivity { vm.checkPending(body, sender) }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Sender: $sender").fetchSemanticsNodes().isNotEmpty() }
        compose.activityRule.scenario.onActivity { vm.edit("New text") }
        compose.runOnIdle { assertNull(vm.state.value.senderNumber) }
        compose.activityRule.scenario.onActivity { vm.share(body); vm.scan() }
        compose.waitUntil(10000) { compose.onAllNodesWithText("High Risk").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Block sender").assertDoesNotExist()
        compose.onNodeWithText("Block Number").performScrollTo().performClick()
        compose.onNodeWithText(compose.activity.getString(R.string.sms_sender_missing)).assertExists()
        compose.onNodeWithText("Copy sender number").assertDoesNotExist()
        compose.activityRule.scenario.onActivity { vm.endSession() }
        compose.runOnIdle { assertNull(vm.state.value.senderNumber) }
    }

    @Test fun pendingSenderIsTakenOnceOrDiscardedWithTheText() {
        val id = PendingChecks.put(body, sender)
        val sms = PendingChecks.take(id)!!
        assertEquals(body, sms.text)
        assertEquals(sender, sms.senderNumber)
        assertNull(PendingChecks.take(id))
        val dismissed = PendingChecks.put(body, sender)
        PendingChecks.discard(dismissed)
        assertNull(PendingChecks.take(dismissed))
        val invalid = PendingChecks.take(PendingChecks.put(body, "BANK"))!!
        assertNull(invalid.senderNumber)
        val cleared = PendingChecks.put(body, sender)
        PendingChecks.clear()
        assertNull(PendingChecks.take(cleared))
    }

    @Test fun outgoingSenderClipRequestsSensitivePreview() {
        // Verify before publishing: emulator host-clipboard mirroring replaces clip metadata.
        val clip = SenderNumberClipboard.createClip("Sender number", sender)
        assertEquals(sender, clip.getItemAt(0).text.toString())
        assertTrue(clip.description.extras!!.getBoolean("android.content.extra.IS_SENSITIVE"))
    }
}
