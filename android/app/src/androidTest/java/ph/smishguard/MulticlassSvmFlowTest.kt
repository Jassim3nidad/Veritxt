package ph.smishguard

import android.graphics.Bitmap
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import java.io.File
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.*

class MulticlassSvmFlowTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun manualChecksDisplayAllThreeActualModelCategories() {
        assumeTrue(BuildConfig.BUILD_TYPE == "multiclassSvm")
        val app = compose.activity.application as SoftwareTestApp; app.testDetector = null
        assertTrue(runBlocking { app.detector() } is MulticlassSvmDetector)
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        val cases = listOf(
            SmsCategory.HAM to "Kita tayo bukas sa opisina. Ingat sa biyahe.",
            SmsCategory.SMISHING to "Your account is suspended. Verify your password at https://example.invalid/verify",
            SmsCategory.GAMBLING to "Play slots casino now! Register and claim your free bonus at https://example.invalid/casino"
        )
        for ((category, text) in cases) {
            compose.activityRule.scenario.onActivity { ViewModelProvider(it)[CheckViewModel::class.java].share(text) }
            compose.waitUntil(10000) { compose.onAllNodesWithText("Check message", substring = false).fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithText("Check message", substring = false).performScrollTo()
                .performSemanticsAction(SemanticsActions.OnClick) { it() }
            val label = when (category) { SmsCategory.HAM -> "Ham"; SmsCategory.SMISHING -> "Smishing"; SmsCategory.GAMBLING -> "Gambling" }
            compose.waitUntil(10000) { compose.onAllNodesWithText(label, substring = false).fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithText("SMS category").assertExists(); compose.onNodeWithText(label, substring = false).assertExists()
            compose.onNodeWithText("Risk Level").assertExists()
            compose.activityRule.scenario.onActivity {
                val state = ViewModelProvider(it)[CheckViewModel::class.java].state.value
                assertEquals(category, (state.result as Detection.Success).category)
                assertEquals(3, (state.result as Detection.Success).classScores!!.size)
            }
            compose.onNodeWithText("SMS category").performScrollTo()
            compose.waitForIdle()
            val directory = File(app.filesDir, "multiclass-review").apply { mkdirs() }
            val bitmap = compose.onRoot().captureToImage().asAndroidBitmap()
            File(directory, "$label.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }; bitmap.recycle()
            compose.onNodeWithText("What does this mean?").performScrollTo().performClick()
            compose.onNodeWithText(compose.activity.getString(R.string.multiclass_decision_note)).assertExists()
            compose.onNodeWithText("Close").performClick()
        }
    }
}
