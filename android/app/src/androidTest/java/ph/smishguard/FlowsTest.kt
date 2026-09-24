package ph.smishguard

import android.content.Intent
import android.content.ClipData
import android.content.ClipboardManager
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowCompat
import kotlinx.coroutines.runBlocking
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class FlowsTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private fun scrollToVisible(text: String): SemanticsNodeInteraction {
        val node = compose.onNodeWithText(text, substring = false)
        // Native IME insets can relocate a focused field after Compose is idle.
        // Re-evaluate the viewport condition; do not rely on one earlier scroll.
        compose.waitUntil(10000) {
            node.performScrollTo()
            node.isDisplayed()
        }
        return node.assertIsDisplayed()
    }
    @org.junit.After fun clearDetector() { (compose.activity.application as SoftwareTestApp).testDetector = null }
    @Before fun resetPreferences() {
        val app = compose.activity.application as SoftwareTestApp
        app.testDetector = ph.smishguard.model.MissingDetector()
        runBlocking { app.preferences.clear() }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Continue without permissions").fetchSemanticsNodes().isNotEmpty() }
        runBlocking { app.preferences.onboard() }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Before you tap,\ncheck the message.").fetchSemanticsNodes().isNotEmpty() }
        compose.waitForIdle()
    }
    @Test fun emptyInputAndMissingModel() {
        compose.onNodeWithText("Check a message").performScrollTo().performClick()
        compose.onNodeWithText("Check message", substring = false).performScrollTo().performClick()
        compose.onNodeWithText("Enter a message to check.").assertExists()
        compose.onNodeWithText("SMS message").performTextInput("Kumusta po, pakiverify ang account. ".repeat(40))
        compose.waitForIdle()
        // Invoke the accessible action after long-input/IME scrolling settles.
        compose.onNodeWithText("Check message", substring = false).performScrollTo()
            .performSemanticsAction(SemanticsActions.OnClick) { it() }
        try {
            compose.waitUntil(10000) { compose.onAllNodesWithText("Model not installed", substring = false).fetchSemanticsNodes().isNotEmpty() }
        } catch (error: Exception) {
            var summary = ""
            compose.activityRule.scenario.onActivity {
                val state = androidx.lifecycle.ViewModelProvider(it)[CheckViewModel::class.java].state.value
                summary = "screen=${state.screen}, busy=${state.busy}, length=${state.text.length}, result=${state.result?.javaClass?.simpleName}, detector=${(it.application as SoftwareTestApp).testDetector?.javaClass?.simpleName}"
            }
            throw AssertionError("Missing-model UI not reached: $summary", error)
        }
        compose.onNodeWithText("No prediction was made. This prototype needs an evaluated model before it can assess messages.").assertExists()
        compose.onNodeWithText("Review reporting options").performScrollTo().performClick()
        compose.onNodeWithText("Submit report · unavailable").performScrollTo().assertIsNotEnabled()
    }
    @Test fun sharedTextAndClear() {
        val intent = Intent(compose.activity, MainActivity::class.java).apply {
            action = Intent.ACTION_SEND; type = "text/plain"
            putExtra(Intent.EXTRA_TEXT,"Synthetic Taglish share: pakiverify ang bayad")
            addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        }
        compose.activity.runOnUiThread { compose.activity.startActivity(intent) }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Synthetic Taglish share: pakiverify ang bayad").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Clear message").performScrollTo().performClick()
        compose.onNodeWithText("Synthetic Taglish share: pakiverify ang bayad").assertDoesNotExist()
    }
    @Test fun deniedPermissionsStillAllowManualCheck() {
        compose.onNodeWithText("Settings").performClick()
        compose.onNodeWithText("SMS permission: not granted", substring = true).assertExists()
        compose.onNodeWithText("Check", substring = false).performClick()
        compose.onNodeWithText("SMS message").assertExists()
    }
    @Test fun clipboardPasteWorksWithoutSmsPermission() {
        compose.onNodeWithText("Check a message").performScrollTo().performClick()
        compose.onNodeWithText("SMS message").performClick()
        compose.activityRule.scenario.onActivity {
            val clipboard = it.getSystemService(ClipboardManager::class.java)
            org.junit.Assert.assertTrue("Activity must own input focus before clipboard access", it.hasWindowFocus())
            clipboard.setPrimaryClip(
                ClipData.newPlainText("Synthetic test", "Synthetic clipboard: kumusta po"))
            org.junit.Assert.assertTrue("Platform clipboard must contain the test-owned fixture", clipboard.hasPrimaryClip())
        }
        compose.onNodeWithText("SMS message").performSemanticsAction(SemanticsActions.PasteText) {
            org.junit.Assert.assertTrue("Paste semantic action must be accepted", it())
        }
        // Compose reads the platform clipboard asynchronously.
        compose.waitUntil(10000) { compose.onAllNodesWithText("Synthetic clipboard: kumusta po").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Synthetic clipboard: kumusta po").assertExists()
        // The test owns this synthetic clipboard; application code never clears user clipboard.
        compose.activityRule.scenario.onActivity {
            it.getSystemService(ClipboardManager::class.java).setPrimaryClip(ClipData.newPlainText("", ""))
        }
    }
    @Test fun navigationDiscardsInput() {
        compose.onNodeWithText("Check", substring = false).performClick()
        compose.onNodeWithText("SMS message").performTextInput("SGTEST navigation private marker")
        compose.onNodeWithText("Settings").performClick()
        compose.onNodeWithText("Check", substring = false).performClick()
        compose.onNodeWithText("SGTEST navigation private marker").assertDoesNotExist()
        compose.onNodeWithText("Home", substring = false).performClick()
        compose.onNodeWithText("Check a message").assertExists()
    }
    @Test fun invalidFailureAndSyntheticResultsStayHonest() {
        val app = compose.activity.application as SoftwareTestApp
        val invocations = java.util.concurrent.atomic.AtomicInteger()
        val cases = listOf(
            ph.smishguard.model.Detection.InvalidModel to "Unsupported or invalid model",
            ph.smishguard.model.Detection.Failure to "Could not complete the check",
            ph.smishguard.model.Detection.Success(true, .99, probability = true, synthetic = true) to "Synthetic interface fixture"
        )
        try {
            for ((index, entry) in cases.withIndex()) {
                val (result, heading) = entry
                app.testDetector = object : ph.smishguard.model.Detector {
                    override val status = "Software fixture"
                    override suspend fun detect(text: String): ph.smishguard.model.Detection {
                        invocations.incrementAndGet()
                        return result
                    }
                }
                compose.onNode(isSelectable() and hasText("Check")).assertIsDisplayed()
                    .performSemanticsAction(SemanticsActions.OnClick) { org.junit.Assert.assertTrue(it()) }
                compose.onNodeWithText("SMS message").performTextInput("SGTEST result privacy marker")
                // Finish the native keyboard interaction before scrolling to a
                // control outside the focused text field's viewport.
                compose.activityRule.scenario.onActivity {
                    WindowCompat.getInsetsController(it.window, it.window.decorView)
                        .hide(WindowInsetsCompat.Type.ime())
                }
                compose.waitUntil(10000) {
                    ViewCompat.getRootWindowInsets(compose.activity.window.decorView)
                        ?.isVisible(WindowInsetsCompat.Type.ime()) == false
                }
                // IME appearance and scroll relocation can move a physical tap's
                // coordinates. Activate the same button callback deterministically.
                scrollToVisible("Check message").assertIsEnabled()
                    .performSemanticsAction(SemanticsActions.OnClick) { org.junit.Assert.assertTrue(it()) }
                compose.waitUntil(10000) { compose.onAllNodesWithText(heading).fetchSemanticsNodes().isNotEmpty() }
                org.junit.Assert.assertEquals("Exactly one inference per scan", index + 1, invocations.get())
                compose.onNodeWithText("SGTEST result privacy marker").assertDoesNotExist()
                compose.onAllNodesWithText("Estimated suspicious-class probability", substring = true).assertCountEquals(0)
                scrollToVisible("Review reporting options")
                    .performSemanticsAction(SemanticsActions.OnClick) { org.junit.Assert.assertTrue(it()) }
                compose.onNodeWithText("Submit report · unavailable").performScrollTo().assertIsNotEnabled()
            }
        } catch (error: Throwable) {
            recordReliabilitySnapshot(compose.activity, "result-flow", error,
                "detectorInvocations=${invocations.get()}\n" + compose.onRoot(useUnmergedTree = true).printToString())
            throw error
        } finally { app.testDetector = null }
    }
}
