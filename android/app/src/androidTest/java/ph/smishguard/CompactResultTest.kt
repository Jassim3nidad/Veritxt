package ph.smishguard

import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModelProvider
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.*

class CompactResultTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @After fun reset() { (compose.activity.application as SoftwareTestApp).testDetector = null }

    private fun scan(result: Detection, text: String = "Synthetic software fixture") {
        val app = compose.activity.application as SoftwareTestApp
        app.testDetector = object : Detector {
            override val status = "Software fixture"
            override suspend fun detect(text: String) = result
        }
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        compose.activityRule.scenario.onActivity {
            ViewModelProvider(it)[CheckViewModel::class.java].share(text)
        }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Test a message").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Check message", substring = false).performScrollTo()
            .performSemanticsAction(SemanticsActions.OnClick) { it() }
        compose.waitUntil(10000) { compose.onAllNodesWithText("What does this mean?").fetchSemanticsNodes().isNotEmpty() }
    }

    @Test fun compactCopyBothDecisionsAndAccessibleExplanation() {
        for (suspicious in listOf(true, false)) {
            val result = Detection.Success(suspicious, if (suspicious) .9229 else .1234, experimental = true)
            scan(result)
            // The original supplied model's warnings were enabled by the team.
            // Assert the actual build policy while keeping reporting disabled.
            val autoWarnings = ViewModelProvider(compose.activity)[CheckViewModel::class.java].state.value.autoWarnings
            val policyNote = compose.activity.getString(if (autoWarnings) R.string.score_disabled else R.string.automatic_disabled)
            compose.onNodeWithText("Check result").assertExists()
            compose.onNodeWithText("Checked message").assertExists()
            compose.onNodeWithText("Synthetic software fixture").assertExists()
            compose.onNodeWithText("SMS message").assertDoesNotExist()
            compose.onNode(isSelectable() and hasText("Check")).assertIsSelected()
            compose.onNodeWithText("Check another message", substring = false).assertHeightIsAtLeast(48.dp)
            compose.onNodeWithText(ResultCopy.heading(result)).assert(SemanticsMatcher.expectValue(SemanticsProperties.Heading, Unit))
            // Plain level on the card, no percentage; exact score only inside "What does this mean?".
            compose.onNodeWithText(if (suspicious) "Warning signs: High" else "Warning signs: Few").assertExists()
            compose.onAllNodes(hasText("%", substring = true)).assertCountEquals(0)
            compose.onNodeWithText(compose.activity.getString(R.string.score_disclaimer)).assertExists()
            compose.onNode(SemanticsMatcher.expectValue(SemanticsProperties.LiveRegion, LiveRegionMode.Polite)).assertExists()
            compose.onNodeWithText(policyNote).assertDoesNotExist()
            compose.onNodeWithText("What does this mean?").performScrollTo().assertHeightIsAtLeast(48.dp).performClick()
            compose.onNodeWithText("About this result").assertExists()
            compose.onNodeWithText(if (suspicious) "Model score: 0.92" else "Model score: 0.12", substring = true).assertExists()
            compose.onNodeWithText("Texts scoring above 0.50 are shown as Likely phishing.").assertExists()
            compose.onNodeWithText(policyNote).performScrollTo().assertExists()
            compose.onNodeWithText("Close").performClick()
        }
    }

    @Test fun warningLevelMatchesVerdictAndWarningSigns() {
        scan(Detection.Success(true, .9, experimental = true))
        compose.onNodeWithText("Warning signs: High").assertExists()
        scan(Detection.Success(false, .3, experimental = true), "BDO: verify your account today at bdo-check.example.com")
        compose.onNodeWithText("Not flagged, but be careful").assertExists()
        compose.onNodeWithText("Warning signs: Some").assertExists()
        scan(Detection.Success(false, .1, experimental = true), "See you at lunch later")
        compose.onNodeWithText("Warning signs: Few").assertExists()
        compose.onAllNodes(hasText("%", substring = true)).assertCountEquals(0)
    }

    @Test fun abstentionNeverShowsPercentageAndEditClearsOldResult() {
        scan(Detection.UnableToAssess, "qwertyuiop")
        compose.onNodeWithText("Unable to assess").assertExists()
        compose.onNodeWithText("Enter an SMS message with meaningful text.").assertExists()
        compose.onAllNodes(hasText("%", substring = true)).assertCountEquals(0)
        compose.onNodeWithText("Check another message").performScrollTo().performClick()
        compose.onNodeWithText("qwertyuiop").assertDoesNotExist()
        compose.onNodeWithText("SMS message").performTextInput("Hi")
        compose.onNodeWithText("Unable to assess").assertDoesNotExist()
        compose.onNodeWithText("What does this mean?").assertDoesNotExist()
    }

    @Test fun longNoticeAndExactDetailsAreAccessibleAndScrollable() {
        val policy = DecisionPolicy(.8899999999999999, true)
        val window = TokenWindow(180, 158, 160)
        scan(Detection.Success(false, .42, experimental = true, policy = policy, tokenWindow = window),
            "hello ".repeat(158) + "Fictional parcel: claim a prize and send a password.")
        compose.onNodeWithText(ResultCopy.LONG_MESSAGE).performScrollTo().assertIsDisplayed()
        recordReliabilitySnapshot(compose.activity, "long-message-notice", null,
            compose.onRoot(useUnmergedTree = true).printToString())
        compose.onNode(SemanticsMatcher.expectValue(SemanticsProperties.LiveRegion, LiveRegionMode.Polite)).assertExists()
        compose.onNodeWithText("What does this mean?").performScrollTo().performClick()
        compose.onNodeWithText("Texts scoring 0.89 or more are shown as Likely phishing.").performScrollTo().assertExists()
        compose.onNodeWithText(window.explanation()).performScrollTo().assertExists()
        compose.onNodeWithText("Close").performClick()
        compose.onNodeWithText("Check another message").performScrollTo().performClick()
        compose.onNodeWithText(ResultCopy.LONG_MESSAGE).assertDoesNotExist()
        scan(Detection.Success(false, .42, policy = DecisionPolicy(.82, true)))
        compose.onNodeWithText(ResultCopy.LONG_MESSAGE).assertDoesNotExist()
    }

    @Test fun failuresAndBusyNeverInventPercentage() {
        for (result in listOf(Detection.Failure, Detection.Busy, Detection.Unavailable)) {
            scan(result)
            compose.onAllNodes(hasText("%", substring = true)).assertCountEquals(0)
        }
    }

    @Test fun blankAndInvalidHaveDistinctNoScoreResults() {
        scan(Detection.Success(false, .1), "   ")
        compose.onNodeWithText("Unable to assess").assertExists()
        compose.onAllNodes(hasText("%", substring = true)).assertCountEquals(0)
        scan(Detection.InvalidModel)
        compose.onNodeWithText("Model unavailable").assertExists()
        compose.onNodeWithText("The bundled model is invalid or unsupported. No prediction was made.").assertExists()
        compose.onAllNodes(hasText("%", substring = true)).assertCountEquals(0)
    }

    @Test fun shippedModelSyntheticScanScreenshot() {
        org.junit.Assume.assumeTrue(BuildConfig.BUILD_TYPE in listOf("development", "lr", "nb", "svm"))
        val app = compose.activity.application as SoftwareTestApp
        app.testDetector = null
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        compose.activityRule.scenario.onActivity {
            ViewModelProvider(it)[CheckViewModel::class.java].share(
                "Your account is suspended. Verify your password at https://account.example now.")
        }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Test a message").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Check message", substring = false).performScrollTo().performClick()
        compose.waitUntil(10000) { compose.onAllNodesWithText("Warning signs:", substring = true).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Check result").performScrollTo()
        recordReliabilitySnapshot(compose.activity, "compact-result", null, "Synthetic test; input cleared; shipped model")
    }
}
