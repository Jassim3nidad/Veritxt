package ph.smishguard

import androidx.compose.ui.semantics.SemanticsProperties
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
        val app = compose.activity.application as SmishGuardApp
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        compose.waitForIdle()
        if (InstrumentationRegistry.getArguments().getString("largeFont") == "true")
            assertTrue(compose.activity.resources.configuration.fontScale >= 1.9f)
        compose.onNodeWithText("Settings").performClick()
        compose.onNodeWithText("Privacy & settings").assert(SemanticsMatcher.expectValue(SemanticsProperties.Heading, Unit))
        compose.onNodeWithContentDescription("Scan incoming SMS").performScrollTo().assertIsToggleable().assertHeightIsAtLeast(48.dp)
        compose.onNodeWithText("Clear local preferences and session").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Check", substring = false).performClick()
        compose.onNodeWithText("SMS message").performScrollTo().assertIsDisplayed().assertHeightIsAtLeast(48.dp)
        compose.onNodeWithText("Check message", substring = false).performScrollTo().assertIsDisplayed()
    }
}
