package ph.smishguard

import android.graphics.Bitmap
import androidx.compose.ui.graphics.asAndroidBitmap
import android.view.WindowManager
import androidx.compose.ui.test.*
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Rule
import org.junit.Test
import androidx.lifecycle.ViewModelProvider
import ph.smishguard.model.*
import java.io.File

/** Test-only screenshots of static UI; no real message input is ever entered here. */
class VisualReviewTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun captureStaticScreens() {
        val app = compose.activity.application as SmishGuardApp
        runBlocking { app.preferences.clear() }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Continue without permissions").fetchSemanticsNodes().isNotEmpty() }
        compose.activityRule.scenario.onActivity { it.window.clearFlags(WindowManager.LayoutParams.FLAG_SECURE) }
        try {
            compose.waitUntil(15000) { compose.onAllNodesWithText("Loading model status", substring = true).fetchSemanticsNodes().isEmpty() }
            capture("onboarding")
            compose.onNodeWithText("Continue without permissions").performScrollTo().performSemanticsAction(SemanticsActions.OnClick) { it() }
            compose.waitUntil(10000) { compose.onAllNodesWithText("Check a message").fetchSemanticsNodes().isNotEmpty() }
            capture("home")
            compose.onNodeWithText("Check a message").performScrollTo().performSemanticsAction(SemanticsActions.OnClick) { it() }
            compose.waitUntil(10000) { compose.onAllNodesWithText("Test a message").fetchSemanticsNodes().isNotEmpty() }
            capture("check")
            compose.onNodeWithText("Settings").performClick()
            compose.waitUntil(10000) { compose.onAllNodesWithText("Privacy & settings").fetchSemanticsNodes().isNotEmpty() }
            capture("settings")
            compose.onNodeWithContentDescription("Scan incoming SMS").performScrollTo().performClick()
            compose.onNodeWithText("Allow incoming SMS checks?").assertExists()
            capture("permission-consent")
            compose.onNodeWithText("Keep off").performClick()
            val testApp = app as SoftwareTestApp
            for ((name, result) in listOf(
                "likely-phishing" to Detection.Success(true, .9229, experimental = true),
                "no-phishing-detected" to Detection.Success(false, .1234, experimental = true),
                "unable-to-assess" to Detection.UnableToAssess,
                "model-unavailable" to Detection.Unavailable,
                "invalid-model" to Detection.InvalidModel,
                "loading-error" to Detection.Failure
            )) {
                // Injected UI fixtures, never research evidence or packaged model changes.
                testApp.testDetector = object : Detector {
                    override val status = "UI test fixture"
                    override suspend fun detect(text: String) = result
                }
                compose.activityRule.scenario.onActivity {
                    ViewModelProvider(it)[CheckViewModel::class.java].share("Invented message for interface testing")
                }
                compose.waitUntil(10000) { compose.onAllNodesWithText("Invented message for interface testing").fetchSemanticsNodes().isNotEmpty() }
                compose.onNodeWithText("Check message", substring = false).performScrollTo().performClick()
                compose.waitUntil(10000) { compose.onAllNodesWithText("What does this mean?").fetchSemanticsNodes().isNotEmpty() }
                if (result !is Detection.Success) compose.onAllNodes(hasText("%", substring = true)).assertCountEquals(0)
                compose.onNodeWithText("Check result").performScrollTo()
                capture(name)
            }
            compose.onNodeWithText("What does this mean?").performScrollTo().performClick()
            capture("explanation")
            compose.onNodeWithText("Review reporting options").performScrollTo().performClick()
            compose.onNodeWithText("Submit report", substring = true).performScrollTo().assertIsNotEnabled()
            compose.onNodeWithText("Your choice to report").performScrollTo()
            capture("reporting-disabled")
            testApp.testDetector = null
        } finally {
            (app as SoftwareTestApp).testDetector = null
            compose.activityRule.scenario.onActivity { it.window.addFlags(WindowManager.LayoutParams.FLAG_SECURE) }
        }
    }
    private fun capture(name: String) {
        compose.waitForIdle()
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.waitForIdleSync()
        // Draw the settled test-owned view, avoiding a stale compositor frame
        // immediately after a screen transition. No user message is captured.
        lateinit var bitmap: Bitmap
        if (name == "permission-consent" || name == "explanation") {
            // Dialogs own a separate window and are absent from the activity decor.
            bitmap = compose.onNode(isDialog()).captureToImage().asAndroidBitmap()
        } else instrumentation.runOnMainSync {
            val view = compose.activity.window.decorView
            bitmap = Bitmap.createBitmap(view.width, view.height, Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
        }
        val directory = File(compose.activity.filesDir,"visual-review").apply { mkdirs() }
        File(directory,"$name.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG,100,it) }
        bitmap.recycle()
    }
}
