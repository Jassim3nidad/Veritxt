package ph.smishguard

import android.content.Intent
import android.content.ClipData
import android.content.ClipboardManager
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class FlowsTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @org.junit.After fun clearDetector() { (compose.activity.application as SoftwareTestApp).testDetector = null }
    @Before fun resetPreferences() {
        val app = compose.activity.application as SoftwareTestApp
        app.testDetector = ph.smishguard.model.MissingDetector()
        runBlocking { app.preferences.clear(); app.preferences.acceptPrivacy() }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Continue without permissions").fetchSemanticsNodes().isNotEmpty() }
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
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
        val cases = listOf(
            ph.smishguard.model.Detection.InvalidModel to "Unsupported or invalid model",
            ph.smishguard.model.Detection.Failure to "Could not complete the check",
            ph.smishguard.model.Detection.Success(true, .99, probability = true, synthetic = true) to "Synthetic interface fixture"
        )
        try {
            for ((result, heading) in cases) {
                app.testDetector = object : ph.smishguard.model.Detector {
                    override val status = "Software fixture"
                    override suspend fun detect(text: String) = result
                }
                compose.onNodeWithText("Check", substring = false).performClick()
                compose.onNodeWithText("SMS message").performTextInput("SGTEST result privacy marker")
                compose.onNodeWithText("Check message", substring = false).performScrollTo().performClick()
                compose.waitUntil(10000) { compose.onAllNodesWithText(heading).fetchSemanticsNodes().isNotEmpty() }
                compose.onNodeWithText("SGTEST result privacy marker").assertDoesNotExist()
                compose.onAllNodesWithText("Estimated suspicious-class probability", substring = true).assertCountEquals(0)
                compose.onNodeWithText("Review reporting options").performScrollTo().performClick()
                compose.onNodeWithText("Submit report · unavailable").performScrollTo().assertIsNotEnabled()
            }
        } finally { app.testDetector = null }
    }
}
