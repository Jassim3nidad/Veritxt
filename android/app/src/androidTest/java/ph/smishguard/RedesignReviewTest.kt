package ph.smishguard

import android.graphics.Bitmap
import android.view.WindowManager
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.Detection
import ph.smishguard.model.Detector
import java.io.File

/** Test-only screenshots of the redesigned screens. Messages are synthetic; the detector is a fixed test stub. */
class RedesignReviewTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private class Fixed(private val result: Detection) : Detector {
        override val status = "Experimental model · test stub"
        override suspend fun detect(text: String) = result
    }
    @Test fun captureRedesign() {
        val app = compose.activity.application as SoftwareTestApp
        val mode = (InstrumentationRegistry.getArguments().getString("mode") ?: "light")
        runBlocking { app.preferences.clear() }
        compose.waitForIdle()
        compose.activityRule.scenario.onActivity { it.window.clearFlags(WindowManager.LayoutParams.FLAG_SECURE) }
        try {
            capture("$mode-1-onboarding")
            compose.onNodeWithText("Continue without permissions").performClick()
            compose.waitUntil(10000) { compose.onAllNodesWithText("Before you tap,\ncheck the message.").fetchSemanticsNodes().isNotEmpty() }
            capture("$mode-2-home")
            check(app, Detection.Success(true, .87, experimental = true),
                "SGTEST BDO reminds you that your 7,352 points will expire today. Visit sgtest-rewards.example.com to redeem.")
            capture("$mode-3-result-scam")
            compose.onNodeWithText("Review reporting options").performScrollTo().performClick()
            capture("$mode-4-report")
            check(app, Detection.Success(false, .31, experimental = true),
                "SGTEST Congrats! You won a reward. Claim today at sgtest-prize.example.com")
            capture("$mode-5-result-caution")
            compose.onNodeWithText("Settings").performClick()
            capture("$mode-6-settings")
        } finally {
            app.testDetector = null
            compose.activityRule.scenario.onActivity { it.window.addFlags(WindowManager.LayoutParams.FLAG_SECURE) }
        }
    }
    private fun check(app: SoftwareTestApp, result: Detection, text: String) {
        app.testDetector = Fixed(result)
        compose.onNodeWithText("Check").performClick()
        compose.onNodeWithText("SMS message").performTextInput(text)
        compose.waitForIdle()
        capture(text.substringAfter("SGTEST ").take(6).let { "check-$it" }, skip = true)
        compose.onNodeWithText("Check message", substring = false).performScrollTo().performSemanticsAction(SemanticsActions.OnClick) { it() }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Check result").fetchSemanticsNodes().isNotEmpty() }
        Thread.sleep(900)
    }
    private var checkCaptured = false
    private fun capture(name: String, skip: Boolean = false) {
        if (skip) { if (checkCaptured) return; checkCaptured = true }
        val mode = InstrumentationRegistry.getArguments().getString("mode") ?: "light"
        val file = if (skip) "$mode-2b-check" else name
        compose.waitForIdle()
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.waitForIdleSync()
        Thread.sleep(400)
        val bitmap = instrumentation.uiAutomation.takeScreenshot()
        val directory = File(compose.activity.filesDir, "visual-review").apply { mkdirs() }
        File(directory, "$file.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        bitmap.recycle()
    }
}
