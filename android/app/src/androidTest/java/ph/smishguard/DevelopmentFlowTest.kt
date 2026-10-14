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
        assumeTrue(BuildConfig.BUILD_TYPE in listOf("development", "lr", "nb", "svm", "mbert", "lrCalibrated4"))
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
        compose.waitUntil(120000) { compose.onAllNodesWithText("Warning signs:", substring = true).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText(text).assertExists()
        compose.onAllNodes(hasText("%", substring = true)).assertCountEquals(0)
        compose.onAllNodesWithText("Estimated suspicious-class probability", substring = true).assertCountEquals(0)
        compose.onNodeWithText(compose.activity.getString(R.string.score_disclaimer)).assertExists()
        compose.onNodeWithText("What does this mean?").performScrollTo().performClick()
        compose.onNodeWithText("Model score:", substring = true).assertExists()
        compose.onNodeWithText("Reporting is disabled in this build.").assertExists()
        compose.onNodeWithText("Review reporting options").performScrollTo().performClick()
        compose.onNodeWithText("Submit report · unavailable").performScrollTo().assertIsNotEnabled()
    }
}
