package ph.smishguard

import android.graphics.Bitmap
import android.view.WindowManager
import androidx.appcompat.app.AppCompatDelegate
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.core.os.LocaleListCompat
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.Detection
import ph.smishguard.model.Detector
import java.io.File

/**
 * Test-only screenshot tour of every screen. Messages are synthetic and the detector is a fixed stub,
 * so verdicts here say nothing about the real model. Run with `-e mode <prefix>` to name the files.
 */
class RedesignReviewTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val mode = InstrumentationRegistry.getArguments().getString("mode") ?: "light"
    private class Fixed(private val result: Detection) : Detector {
        override val status = "Experimental model · test stub"
        override suspend fun detect(text: String) = result
    }

    @Test fun captureRedesign() {
        val app = compose.activity.application as SoftwareTestApp
        runBlocking { app.preferences.clear() }
        compose.waitForIdle()
        unsecure()
        try {
            waitFor("Your privacy")
            capture("01-privacy")
            compose.onNodeWithText("I have read and understood this notice").performScrollTo().performClick()
            compose.onNodeWithText("Agree and continue").performScrollTo().performClick()
            waitFor("Continue without permissions")
            capture("02-onboarding")
            compose.onNodeWithText("Continue without permissions").performScrollTo().performClick()
            waitFor("Before you tap,\ncheck the message.")
            capture("03-home")
            check(app, Detection.Success(true, .87, experimental = true),
                "SGTEST BDO reminds you that your 7,352 points will expire today. Visit sgtest-rewards.example.com to redeem.", "04-check")
            capture("05-result-scam")
            compose.onNodeWithText("Review reporting options").performScrollTo().performClick()
            capture("06-report")
            check(app, Detection.Success(false, .31, experimental = true), "SGTEST Congrats! You won a reward. Claim today at sgtest-prize.example.com", null)
            capture("07-result-caution")
            compose.onNodeWithText("Settings").performClick()
            capture("08-settings")
            compose.onNodeWithText("Why didn't I get a notification?").performScrollTo().performClick()
            capture("09-help")
            // Filipino
            setLanguage("fil") // recreating the activity ends the session, so this lands on Home
            waitFor("Bago mag-tap,\nsuriin muna ang mensahe.")
            capture("10-fil-home")
            compose.onNodeWithText("Suriin").performClick()
            check(app, Detection.Success(true, .87, experimental = true),
                "SGTEST BDO: Ang account mo ay naka-hold. I-verify ngayon sa sgtest-verify.example.com", null, button = "Suriin ang mensahe", resultTitle = "Resulta ng pagsusuri")
            capture("11-fil-result")
        } finally {
            setLanguage(null)
            app.testDetector = null
            compose.activityRule.scenario.onActivity { it.window.addFlags(WindowManager.LayoutParams.FLAG_SECURE) }
        }
    }

    private fun unsecure() = compose.activityRule.scenario.onActivity { it.window.clearFlags(WindowManager.LayoutParams.FLAG_SECURE) }
    private fun waitFor(text: String) = compose.waitUntil(15000) { compose.onAllNodesWithText(text).fetchSemanticsNodes().isNotEmpty() }
    private fun setLanguage(tag: String?) {
        InstrumentationRegistry.getInstrumentation().runOnMainSync {
            AppCompatDelegate.setApplicationLocales(if (tag == null) LocaleListCompat.getEmptyLocaleList() else LocaleListCompat.forLanguageTags(tag))
        }
        Thread.sleep(1500) // the activity is recreated in the new language
        compose.waitForIdle()
        unsecure()
    }
    private fun check(app: SoftwareTestApp, detection: Detection, text: String, shot: String?,
                      button: String = "Check message", resultTitle: String = "Check result") {
        app.testDetector = Fixed(detection)
        if (compose.onAllNodesWithText(button).fetchSemanticsNodes().isEmpty()) compose.onNodeWithText("Check").performClick()
        compose.onNode(hasSetTextAction()).performTextInput(text)
        compose.waitForIdle()
        shot?.let(::capture)
        compose.onNodeWithText(button, substring = false).performScrollTo().performSemanticsAction(SemanticsActions.OnClick) { it() }
        compose.waitUntil(10000) { compose.onAllNodesWithText(resultTitle).fetchSemanticsNodes().isNotEmpty() }
        Thread.sleep(900)
    }
    private fun capture(name: String) {
        compose.waitForIdle()
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.waitForIdleSync()
        Thread.sleep(400)
        val bitmap = instrumentation.uiAutomation.takeScreenshot()
        val directory = File(compose.activity.filesDir, "visual-review").apply { mkdirs() }
        File(directory, "$mode-$name.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        bitmap.recycle()
    }
}
