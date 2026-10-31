package ph.smishguard

import android.app.Activity
import android.app.Instrumentation
import android.content.Intent
import android.graphics.Bitmap
import android.telecom.TelecomManager
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.Assert.*
import ph.smishguard.model.*
import java.io.File

class RiskResultsTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @After fun reset() { (compose.activity.application as SoftwareTestApp).testDetector = null }

    private fun scan(text: String, detection: Detection = Detection.Success(false, .1), senderNumber: String? = null) {
        val app = compose.activity.application as SoftwareTestApp
        app.testDetector = object : Detector {
            override val status = "Software test"
            override suspend fun detect(text: String) = detection
        }
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        if (senderNumber != null) compose.activityRule.scenario.onActivity { ViewModelProvider(it)[CheckViewModel::class.java].checkPending(text, senderNumber) }
        else {
            compose.activityRule.scenario.onActivity { ViewModelProvider(it)[CheckViewModel::class.java].share(text) }
            compose.waitUntil(10000) { compose.onAllNodesWithText("Test a message").fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithText("Check message", substring = false).performScrollTo()
                .performSemanticsAction(SemanticsActions.OnClick) { it() }
        }
        compose.waitUntil(10000) { compose.onAllNodesWithText("What does this mean?").fetchSemanticsNodes().isNotEmpty() }
    }

    @Test fun everyResultHasTheSameSectionsAndNoBlockingForLowRisk() {
        scan("Your OTP is 123456. Never share your OTP.")
        for (label in listOf("Risk Level", "Low Risk", "Risk Score: 0/100", "Analysis", "Detected Indicators", "Recommended Action"))
            compose.onNodeWithText(label).assertExists()
        compose.onNodeWithText("Block Number").assertDoesNotExist()
        compose.onNodeWithText(compose.activity.getString(R.string.risk_low_action)).assertExists()
    }

    @Test fun mediumRiskEmphasizesVerification() {
        scan("Please review your account", Detection.Success(true, .97))
        compose.onNodeWithText("Medium Risk").assertExists()
        compose.onNodeWithText("Risk Score: 40/100").assertExists()
        compose.onNodeWithText(compose.activity.getString(R.string.risk_medium_action)).assertExists()
        compose.onNodeWithText("Block Number").assertExists()
    }

    @Test fun blockInstructionsRequireConfirmationAndCancelDoesNothing() {
        scan("Please send your OTP immediately")
        compose.onNodeWithText("High Risk").assertExists()
        compose.onNodeWithText("How to block a number").assertDoesNotExist()
        compose.onNodeWithText("Block Number").performScrollTo().performClick()
        compose.onNodeWithText("Review manual blocking?").assertExists()
        compose.onNodeWithText("How to block a number").assertDoesNotExist()
        compose.onNodeWithText("Cancel").performClick()
        compose.onNodeWithText("Review manual blocking?").assertDoesNotExist()
        compose.onNodeWithText("Block Number").performScrollTo().performClick()
        compose.onNodeWithText("Show instructions").performClick()
        compose.onNodeWithText("How to block a number").assertExists()
        compose.onNodeWithText(compose.activity.getString(R.string.block_instructions_body)).assertExists()
        compose.onNodeWithText("Close").performClick()
        scan("Hello there")
        compose.onNodeWithText("Block Number").assertDoesNotExist()
        compose.onNodeWithText("How to block a number").assertDoesNotExist()
    }

    @Test fun unfamiliarPhoneNumbersHaveNoNumericalScore() {
        scan("+1 202 555 0100", Detection.Success(true, .999))
        compose.onNodeWithText("Unable to assess").assertExists()
        compose.onAllNodes(hasText("Risk Score:", substring = true)).assertCountEquals(0)
        compose.onNodeWithText(compose.activity.getString(R.string.risk_limit_phone)).assertExists()
        compose.onNodeWithText("Block Number").assertExists()
    }

    @Test fun confirmedBlockingUsesAndroidHandoffWithoutSendingScanData() {
        scan("Please send your OTP immediately")
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val expected = compose.activity.getSystemService(TelecomManager::class.java).createManageBlockedNumbersIntent()
        var launches = 0
        val monitor = object : Instrumentation.ActivityMonitor() {
            override fun onStartActivity(intent: Intent): Instrumentation.ActivityResult? {
                if (!intent.filterEquals(expected)) return null
                launches++
                assertNull(intent.data)
                assertTrue(intent.extras == null || intent.extras!!.isEmpty)
                return Instrumentation.ActivityResult(Activity.RESULT_CANCELED, null)
            }
        }
        instrumentation.addMonitor(monitor)
        try {
            compose.onNodeWithText("Block Number").performScrollTo().performClick()
            compose.runOnIdle { assertEquals(0, launches) }
            compose.onNodeWithText("Cancel").performClick()
            compose.runOnIdle { assertEquals(0, launches) }
            compose.onNodeWithText("Block Number").performScrollTo().performClick()
            compose.onNodeWithText("Open blocked numbers").performClick()
            compose.runOnIdle { assertEquals(1, launches) }
            compose.onNodeWithText("Review manual blocking?").assertDoesNotExist()
            compose.onNodeWithText("How to block a number").assertDoesNotExist()
        } finally { instrumentation.removeMonitor(monitor) }
    }

    @Test fun realAndroidBlocklistOpensAndReturningClearsTheScan() {
        val sender = "+16505550100"
        scan("Please send your OTP immediately", senderNumber = sender)
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val activity = compose.activity
        val intent = activity.getSystemService(TelecomManager::class.java).createManageBlockedNumbersIntent()
        val targetPackage = intent.component?.packageName ?: intent.`package`
        assertNotNull("Android should identify its own blocked-number activity", targetPackage)
        compose.onNodeWithText("Sender: $sender").assertExists()
        compose.onNodeWithText("Block sender").performScrollTo().performClick()
        val previewDirectory = File(activity.filesDir, "blocking-preview").apply { mkdirs() }
        val confirmation = compose.onNode(isDialog()).captureToImage().asAndroidBitmap()
        File(previewDirectory, "confirmation.png").outputStream().use { confirmation.compress(Bitmap.CompressFormat.PNG, 100, it) }
        confirmation.recycle()
        compose.onNodeWithText("Open blocked numbers").performClick()
        try {
            compose.waitUntil(10000) {
                val root = instrumentation.uiAutomation.rootInActiveWindow
                root?.packageName?.toString() == targetPackage && root.findAccessibilityNodeInfosByText("Add a number").isNotEmpty()
            }
            instrumentation.uiAutomation.waitForIdle(500, 5000)
            // Native Android UI evidence only: never add a number or alter the blocklist.
            instrumentation.uiAutomation.takeScreenshot()?.let { bitmap ->
                File(previewDirectory, "android-blocked-numbers.png").outputStream().use {
                    bitmap.compress(Bitmap.CompressFormat.PNG, 100, it)
                }
                bitmap.recycle()
            }
        } finally {
            activity.startActivity(Intent(activity, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT))
        }
        compose.waitUntil(10000) { instrumentation.uiAutomation.rootInActiveWindow?.packageName?.toString() == activity.packageName }
        compose.runOnIdle {
            val state = ViewModelProvider(activity)[CheckViewModel::class.java].state.value
            assertEquals(Screen.HOME, state.screen)
            assertNull(state.result)
            assertNull(state.senderNumber)
            assertTrue(state.checkedMessage.isEmpty())
        }
        compose.onNodeWithText("Block this sender?").assertDoesNotExist()
    }

    @Test fun plainUrlsAndEmailAddressesHaveNoReputationVerdict() {
        for (text in listOf("https://example.com", "someone@example.com")) {
            scan(text, Detection.Success(true, .999))
            compose.onNodeWithText("Unable to assess").assertExists()
            compose.onAllNodes(hasText("Risk Score:", substring = true)).assertCountEquals(0)
            compose.onNodeWithText("What does this mean?").performScrollTo().performClick()
            compose.onAllNodes(hasText("Research model output:", substring = true)).assertCountEquals(0)
            compose.onNodeWithText("Close").performClick()
        }
    }

    @Test fun reviewingReportingDoesNotChangeTheRiskResult() {
        scan("Send your password")
        compose.onNodeWithText("High Risk").assertExists()
        compose.onNodeWithText("Risk Score: 70/100").assertExists()
        compose.onNodeWithText("Review reporting options").performScrollTo().performClick()
        compose.onNodeWithText("Back to result").performScrollTo().performClick()
        compose.onNodeWithText("High Risk").assertExists()
        compose.onNodeWithText("Risk Score: 70/100").assertExists()
        compose.onNodeWithText("Send your password").assertDoesNotExist()
    }
}
