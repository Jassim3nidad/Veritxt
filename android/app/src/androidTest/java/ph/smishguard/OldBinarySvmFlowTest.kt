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
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.*

class OldBinarySvmFlowTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun actualOldModelDisplaysOnlyItsTwoCategories() {
        assertEquals("oldSvm", BuildConfig.BUILD_TYPE)
        val app = compose.activity.application as SoftwareTestApp
        app.testDetector = null
        assertTrue(runBlocking { app.detector() } is SelectedSvmDetector)
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        val cases = listOf(
            SmsCategory.HAM to "Kita tayo bukas sa opisina. Ingat sa biyahe.",
            SmsCategory.SMISHING to "Your account is suspended. Verify your password at https://example.invalid/verify"
        )
        for ((category, text) in cases) {
            compose.activityRule.scenario.onActivity { ViewModelProvider(it)[CheckViewModel::class.java].share(text) }
            compose.waitUntil(10000) { compose.onAllNodesWithText("Check message", substring=false).fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithText("Check message", substring=false).performScrollTo()
                .performSemanticsAction(SemanticsActions.OnClick) { it() }
            val label = if (category == SmsCategory.HAM) "Ham" else "Smishing"
            compose.waitUntil(10000) { compose.onAllNodesWithText(label, substring=false).fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithText("SMS category").assertExists()
            compose.onNodeWithText(label, substring=false).assertExists()
            compose.onNodeWithText("Gambling", substring=false).assertDoesNotExist()
            compose.onNodeWithText(compose.activity.getString(R.string.sms_category_binary_note)).assertExists()
            compose.activityRule.scenario.onActivity {
                val state = ViewModelProvider(it)[CheckViewModel::class.java].state.value
                val actual = state.result as Detection.Success
                assertEquals(category, actual.category)
                assertNull(actual.classScores)
                assertEquals(RiskPolicy.assess(text, actual), AppRiskPolicy.assess(text, actual))
            }
            compose.onNodeWithText("SMS category").performScrollTo(); compose.waitForIdle()
            val directory = File(app.filesDir, "old-binary").apply { mkdirs() }
            val bitmap = compose.onRoot().captureToImage().asAndroidBitmap()
            File(directory,"$label.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG,100,it) }
            bitmap.recycle()
        }
    }
}
