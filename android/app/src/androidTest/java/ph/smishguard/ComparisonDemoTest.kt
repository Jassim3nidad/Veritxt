package ph.smishguard

import android.content.ClipData
import android.content.ClipboardManager
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.json.JSONObject
import ph.smishguard.model.*

/** Fictional text, real bundled models and results. No injected detector or expected labels. */
class ComparisonDemoTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun actualPasteRepeatedScansAndFictionalScreenshots() {
        assumeTrue(BuildConfig.BUILD_TYPE in listOf("lr", "nb", "svm", "mbert"))
        val app = compose.activity.application as SoftwareTestApp
        app.testDetector = null
        val detector = runBlocking { app.preferences.onboard(); app.detector() }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Check a message").fetchSemanticsNodes().isNotEmpty() }
        val versionPrefix=JSONObject(compose.activity.assets.open("model.json").bufferedReader().use { it.readText() })
            .getString("model_version")
        compose.waitUntil(120000) { compose.onAllNodesWithText(versionPrefix, substring=true).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText(versionPrefix, substring=true).performScrollTo()
        recordReliabilitySnapshot(compose.activity,"comparison-home",null,"Fictional demo; actual algorithm and model version")
        val probes = listOf("Your account is suspended. Verify your password at https://account.example now.",
            "Bayad na po. Salamat sa tulong, kita tayo bukas.")
        for ((index,text) in probes.withIndex()) {
            if (index==0) compose.onNodeWithText("Check a message").performScrollTo().performClick()
            else compose.onNodeWithText("Check another message").performScrollTo().performClick()
            compose.onNodeWithText("SMS message").performClick()
            compose.activityRule.scenario.onActivity {
                it.getSystemService(ClipboardManager::class.java).setPrimaryClip(ClipData.newPlainText("Fictional demo",text))
            }
            compose.onNodeWithText("SMS message").performSemanticsAction(SemanticsActions.PasteText) { assertTrue(it()) }
            compose.waitUntil(10000) { compose.onAllNodesWithText(text).fetchSemanticsNodes().isNotEmpty() }
            compose.activityRule.scenario.onActivity {
                it.getSystemService(ClipboardManager::class.java).setPrimaryClip(ClipData.newPlainText("",""))
            }
            compose.onNodeWithText("Check message",substring=false).performScrollTo().performClick()
            compose.waitUntil(10000) { compose.onAllNodesWithText("What does this mean?").fetchSemanticsNodes().isNotEmpty() }
            val expected=runBlocking { detector.detect(text) }
            if (expected is Detection.Success) compose.onNodeWithText(ResultCopy.score(expected.score)).assertExists()
            else compose.onNodeWithText("Unable to assess").assertExists()
            compose.onNodeWithText("Check result").performScrollTo()
            recordReliabilitySnapshot(compose.activity,"comparison-result-$index",null,"Fictional demo; real bundled inference")
        }
    }
}
