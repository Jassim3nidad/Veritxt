package ph.smishguard

import android.graphics.Bitmap
import android.graphics.Canvas
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.*
import ph.smishguard.ui.RiskPresentation
import java.io.File

/** Genuine emulator renders, using fictional SMS and the installed model for the primary risk examples. */
class RiskScreenshotTourTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val app get() = compose.activity.application as SoftwareTestApp
    private val manifest = JSONObject()
    private fun waitFor(text: String) = compose.waitUntil(15000) {
        compose.onAllNodesWithText(text, substring = false).fetchSemanticsNodes().isNotEmpty()
    }
    private fun click(text: String) {
        val node = compose.onNodeWithText(text, substring = false)
        try { node.performScrollTo() }
        catch (error: AssertionError) {
            if (!error.message.orEmpty().contains("no parent layout with a Scroll")) throw error
        }
        node.performSemanticsAction(SemanticsActions.OnClick) { it() }
    }

    @Test fun captureUpdatedApplication() {
        app.testDetector = null
        runBlocking { app.preferences.clear(); app.preferences.acceptPrivacy() }
        waitFor("Continue without permissions")
        capture("01-onboarding")
        click("Continue without permissions")
        waitFor("Check a message")
        compose.waitUntil(15000) { compose.onAllNodesWithText("Loading model status…").fetchSemanticsNodes().isEmpty() }
        capture("02-home")
        click("Check a message")
        waitFor("Test a message")
        capture("03-check")
        click("Settings")
        waitFor("Privacy & settings")
        capture("04-settings")
        compose.onNodeWithContentDescription("Scan incoming SMS").performScrollTo().performClick()
        waitFor("Allow incoming SMS checks?")
        capture("05-permission-consent", dialog = true)
        click("Keep off")

        val candidates = linkedMapOf(
            RiskLevel.LOW to listOf("Bayad na po. Salamat sa tulong.", "Hello, are we meeting for lunch?", "Your appointment is tomorrow. Please arrive early.", "The meeting is urgent, please join us.", "BPI sent your monthly statement."),
            RiskLevel.MEDIUM to listOf("Please review your account", "Please enter your password in the official app.", "Please pay the delivery fee at the counter.", "Our prize ceremony is today.", "Your OTP is 123456. Never share your OTP."),
            RiskLevel.HIGH to listOf("Please send your OTP immediately", "Share your password with our support agent.")
        )
        for ((level, probes) in candidates) {
            val chosen = probes.firstOrNull { text -> runBlocking { RiskPolicy.assess(text, app.assess(text)).level == level } }
            assertNotNull("The installed model needs a fictional example for $level", chosen)
            scan(chosen!!)
            val state = ViewModelProvider(compose.activity)[CheckViewModel::class.java].state.value
            assertEquals(level, state.assessment!!.level)
            manifest.put(level.name, JSONObject().put("text", chosen).put("score", state.assessment.score)
                .put("detector", state.modelStatus).put("source", "actual installed model, fictional input"))
            top()
            val name = when (level) { RiskLevel.LOW -> "06-low-risk"; RiskLevel.MEDIUM -> "07-medium-risk"; else -> "08-high-risk" }
            capture(name)
            compose.onNodeWithText(app.getString(RiskPresentation.action(level))).performScrollTo()
            if (level != RiskLevel.LOW) compose.onNodeWithText("Block Number").performScrollTo()
            compose.onAllNodes(hasScrollAction()).onFirst()
                .performSemanticsAction(SemanticsActions.ScrollBy) { it(0f, 10000f) }
            capture("$name-actions")
        }
        click("Block Number")
        waitFor("Review manual blocking?")
        capture("09-block-confirmation", dialog = true)
        click("Show instructions")
        waitFor("How to block a number")
        capture("10-block-instructions", dialog = true)
        click("Close")
        click("What does this mean?")
        waitFor("About this result")
        capture("11-explanation", dialog = true)
        click("Close")
        click("Review reporting options")
        waitFor("Your choice to report")
        compose.onNodeWithText("Your choice to report").performScrollTo()
        capture("12-reporting-disabled")

        scan("+1 202 555 0100")
        waitFor("Unable to assess")
        top()
        capture("13-unable-to-assess")
        // Failure-state fixtures exercise presentation only, never claim actual model failures.
        try {
            for ((name, result) in listOf("14-model-unavailable" to Detection.Unavailable,
                "15-invalid-model" to Detection.InvalidModel, "16-check-failed" to Detection.Failure)) {
                app.testDetector = object : Detector {
                    override val status = "UI failure-state fixture"
                    override suspend fun detect(text: String) = result
                }
                scan("Fictional message for an unavailable-check example")
                waitFor("Unable to assess")
                top()
                capture(name)
            }
        } finally { app.testDetector = null }
        File(compose.activity.filesDir, "risk-screenshots/manifest.json").writeText(manifest.toString(2))
    }

    private fun scan(text: String) {
        compose.activityRule.scenario.onActivity { ViewModelProvider(it)[CheckViewModel::class.java].share(text) }
        waitFor("Test a message")
        click("Check message")
        waitFor("What does this mean?")
    }

    private fun top() = compose.onAllNodes(hasScrollAction()).onFirst()
        .performSemanticsAction(SemanticsActions.ScrollBy) { it(0f, -10000f) }

    private fun capture(name: String, dialog: Boolean = false) {
        compose.waitForIdle()
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.waitForIdleSync()
        val bitmap: Bitmap
        if (dialog) bitmap = compose.onNode(isDialog()).captureToImage().asAndroidBitmap()
        else {
            lateinit var rendered: Bitmap
            instrumentation.runOnMainSync {
                val view = compose.activity.window.decorView
                rendered = Bitmap.createBitmap(view.width, view.height, Bitmap.Config.ARGB_8888)
                view.draw(Canvas(rendered))
            }
            bitmap = rendered
        }
        val directory = File(compose.activity.filesDir, "risk-screenshots").apply { mkdirs() }
        File(directory, "$name.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        bitmap.recycle()
    }
}
