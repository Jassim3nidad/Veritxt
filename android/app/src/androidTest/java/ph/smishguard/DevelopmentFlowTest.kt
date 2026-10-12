package ph.smishguard

import android.content.Intent
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import kotlinx.coroutines.runBlocking
import org.junit.Rule
import org.junit.Test
import org.junit.Assume.assumeTrue

class DevelopmentFlowTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun suppliedModelShareShowsExperimentalResultAndCannotReport() {
        assumeTrue(BuildConfig.BUILD_TYPE == "development")
        val app = compose.activity.application as SoftwareTestApp
        app.testDetector = null
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        compose.waitForIdle()
        val text = "SGTEST supplied model manual privacy marker. Kumusta po, tingnan ang opisyal na app."
        compose.activityRule.scenario.onActivity {
            it.startActivity(Intent(it, MainActivity::class.java).apply {
                action = Intent.ACTION_SEND; type = "text/plain"; putExtra(Intent.EXTRA_TEXT, text)
                addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
            })
        }
        compose.waitUntil(10000) { compose.onAllNodesWithText(text).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Check message", substring = false).performScrollTo().performClick()
        compose.waitUntil(10000) { compose.onAllNodesWithText("Experimental result").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText(text).assertDoesNotExist()
        compose.onNodeWithText("Uncalibrated model score:", substring = true).assertExists()
        compose.onAllNodesWithText("Estimated suspicious-class probability", substring = true).assertCountEquals(0)
        compose.onNodeWithText("Automatic warnings and reporting are disabled.").assertExists()
        compose.onNodeWithText("Review reporting options").performScrollTo().performClick()
        compose.onNodeWithText("Submit report · unavailable").performScrollTo().assertIsNotEnabled()
    }
}
