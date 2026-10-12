package ph.smishguard

import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.dp
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

class AccessibilityTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun labeledControlsAndHeadingsRemainReachable() {
        try {
            val app = compose.activity.application as SmishGuardApp
            runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
            compose.waitUntil(10000) {
                compose.onAllNodesWithText("Settings", substring = false).fetchSemanticsNodes().size == 1 &&
                    compose.activity.hasWindowFocus()
            }
            if (InstrumentationRegistry.getArguments().getString("largeFont") == "true")
                assertTrue(compose.activity.resources.configuration.fontScale >= 1.9f)
            // Select the actionable tab, not a coordinate on a moving/scaled label.
            val settings = compose.onNode(isSelectable() and hasText("Settings"))
            settings.assertIsDisplayed().assertHeightIsAtLeast(48.dp).assertWidthIsAtLeast(48.dp)
                .performSemanticsAction(SemanticsActions.OnClick) { assertTrue(it()) }
            settings.assertIsSelected()
            compose.waitUntil(10000) {
                compose.onAllNodesWithText("Privacy & settings").fetchSemanticsNodes().size == 1
            }
            compose.onNodeWithText("Privacy & settings").assert(SemanticsMatcher.expectValue(SemanticsProperties.Heading, Unit))
            compose.onNodeWithContentDescription("Scan incoming SMS").performScrollTo().assertIsToggleable().assertHeightIsAtLeast(48.dp)
            compose.onNodeWithText("Clear local preferences and session").performScrollTo().assertIsDisplayed()
            compose.onNode(isSelectable() and hasText("Check")).assertIsDisplayed()
                .performSemanticsAction(SemanticsActions.OnClick) { assertTrue(it()) }
            compose.waitUntil(10000) { compose.onAllNodesWithText("SMS message").fetchSemanticsNodes().size == 1 }
            compose.onNodeWithText("SMS message").performScrollTo().assertIsDisplayed().assertHeightIsAtLeast(48.dp)
            compose.onNodeWithText("Check message", substring = false).performScrollTo().assertIsDisplayed()
            compose.onNodeWithText("Check message", substring = false)
                .performSemanticsAction(SemanticsActions.OnClick) { assertTrue(it()) }
            compose.waitUntil(10000) { compose.onAllNodesWithText("Unable to assess").fetchSemanticsNodes().size == 1 }
            compose.onNodeWithText("Unable to assess").assert(SemanticsMatcher.expectValue(SemanticsProperties.Heading, Unit))
            compose.onAllNodes(hasText("%", substring = true)).assertCountEquals(0)
            compose.onNodeWithText("Check another message").performScrollTo().assertIsDisplayed().assertHeightIsAtLeast(48.dp)
            recordReliabilitySnapshot(compose.activity, "accessible-result", null, "Empty-input result; no message content")
            compose.onNodeWithText("Check another message").performClick()
            compose.onNodeWithText("SMS message").performScrollTo().assertIsDisplayed()
            // Retain physical hit-target coverage after the screen/scroll has settled.
            compose.onNode(isSelectable() and hasText("Home")).assertIsDisplayed().performClick().assertIsSelected()
            settings.assertIsDisplayed().performClick().assertIsSelected()
            compose.onNodeWithText("Privacy & settings").performScrollTo().assertIsDisplayed()
            recordReliabilitySnapshot(compose.activity, "accessibility", null, compose.onRoot(useUnmergedTree = true).printToString())
        } catch (error: Throwable) {
            recordReliabilitySnapshot(compose.activity, "accessibility", error, compose.onRoot(useUnmergedTree = true).printToString())
            throw error
        }
    }
}
