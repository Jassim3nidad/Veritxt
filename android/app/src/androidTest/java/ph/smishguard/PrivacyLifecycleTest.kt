package ph.smishguard

import android.os.Bundle
import android.view.WindowManager
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.Lifecycle
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

class PrivacyLifecycleTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun backgroundAndRecreateDiscardText() {
        val app = compose.activity.application as SmishGuardApp
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        compose.waitForIdle()
        compose.onNodeWithText("Check a message").performScrollTo().performClick()
        compose.onNodeWithText("SMS message").performTextInput("SYNTHETIC_PRIVATE_SESSION_MARKER")
        compose.activityRule.scenario.moveToState(Lifecycle.State.CREATED)
        compose.activityRule.scenario.moveToState(Lifecycle.State.RESUMED)
        compose.onNodeWithText("SYNTHETIC_PRIVATE_SESSION_MARKER").assertDoesNotExist()
        compose.activityRule.scenario.recreate()
        compose.onNodeWithText("SYNTHETIC_PRIVATE_SESSION_MARKER").assertDoesNotExist()
        compose.activityRule.scenario.onActivity {
            assertTrue(it.window.attributes.flags and WindowManager.LayoutParams.FLAG_SECURE != 0)
        }
    }

    @Test fun checkedMessageIsTransientAndClearsAtEveryExit() {
        val app = compose.activity.application as SoftwareTestApp
        app.testDetector = ph.smishguard.model.MissingDetector()
        val message = "Invented SMS for result privacy testing.\nSecond line stays intact."
        try {
            runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
            for (exit in listOf("another", "settings", "report", "background", "recreate")) {
                compose.activityRule.scenario.onActivity {
                    val vm = androidx.lifecycle.ViewModelProvider(it)[CheckViewModel::class.java]
                    vm.share(message)
                    vm.scan()
                }
                compose.waitUntil(10000) { compose.onAllNodesWithText(message).fetchSemanticsNodes().isNotEmpty() &&
                    compose.onAllNodesWithText("Checked message").fetchSemanticsNodes().isNotEmpty() }
                compose.onNodeWithText(message).assertExists()
                compose.activityRule.scenario.onActivity {
                    assertEquals("", androidx.lifecycle.ViewModelProvider(it)[CheckViewModel::class.java].state.value.text)
                    assertTrue(it.window.attributes.flags and WindowManager.LayoutParams.FLAG_SECURE != 0)
                }
                when (exit) {
                    "another" -> compose.onNodeWithText("Check another message").performScrollTo().performClick()
                    "settings" -> compose.onNodeWithText("Settings").performClick()
                    "report" -> compose.activityRule.scenario.onActivity {
                        androidx.lifecycle.ViewModelProvider(it)[CheckViewModel::class.java].navigate(Screen.REPORT)
                    }
                    "background" -> {
                        compose.activityRule.scenario.moveToState(Lifecycle.State.CREATED)
                        compose.activityRule.scenario.moveToState(Lifecycle.State.RESUMED)
                    }
                    else -> compose.activityRule.scenario.recreate()
                }
                compose.waitForIdle()
                compose.onNodeWithText(message).assertDoesNotExist()
                compose.activityRule.scenario.onActivity {
                    assertEquals("", androidx.lifecycle.ViewModelProvider(it)[CheckViewModel::class.java].state.value.checkedMessage)
                }
            }
        } finally { app.testDetector = null }
    }
}
