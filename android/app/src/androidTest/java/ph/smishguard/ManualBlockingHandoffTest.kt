package ph.smishguard

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.ContextWrapper
import android.content.Intent
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import ph.smishguard.blocking.SystemNumberBlocking
import ph.smishguard.model.Detection
import ph.smishguard.model.RiskPolicy

class ManualBlockingHandoffTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    private fun control(open: () -> Boolean) {
        val assessment = RiskPolicy.assess("Please send your OTP immediately", Detection.Success(false, .1))
        compose.activityRule.scenario.onActivity { activity ->
            activity.setContent { MaterialTheme { ManualBlockingControl(assessment, openBlockedNumbers = open) } }
        }
    }

    @Test fun cancellationAndInstructionsNeverLaunchAndConfirmationLaunchesOnce() {
        var launches = 0
        control { launches++; true }
        compose.onNodeWithText("Block Number").performClick()
        compose.runOnIdle { assertEquals(0, launches) }
        compose.onNodeWithText("Cancel").performClick()
        compose.runOnIdle { assertEquals(0, launches) }
        compose.onNodeWithText("Block Number").performClick()
        compose.onNodeWithText("Show instructions").performClick()
        compose.onNodeWithText("How to block a number").assertExists()
        compose.runOnIdle { assertEquals(0, launches) }
        compose.onNodeWithText("Close").performClick()
        compose.onNodeWithText("Block Number").performClick()
        compose.onNodeWithText("Open blocked numbers").performClick()
        compose.onNodeWithText("Review manual blocking?").assertDoesNotExist()
        compose.onNodeWithText("How to block a number").assertDoesNotExist()
        compose.runOnIdle { assertEquals(1, launches) }
    }

    @Test fun unavailableHandoffShowsInstructionsAndCanBeDismissed() {
        control { false }
        compose.onNodeWithText("Block Number").performClick()
        compose.onNodeWithText("Open blocked numbers").performClick()
        compose.onNodeWithText("How to block a number").assertExists()
        compose.onNodeWithText(compose.activity.getString(R.string.block_unavailable)).assertExists()
        compose.onNodeWithText("Close").performClick()
        compose.onNodeWithText("How to block a number").assertDoesNotExist()
        compose.onNodeWithText("Block Number").performClick()
        compose.onNodeWithText(compose.activity.getString(R.string.block_unavailable)).assertDoesNotExist()
    }

    @Test fun platformIntentCarriesNoScannedTextOrPhoneNumber() {
        var launched: Intent? = null
        val context = object : ContextWrapper(compose.activity) {
            override fun startActivity(intent: Intent) { launched = intent }
        }
        assertTrue("Test device must support Android's blocked-number screen", SystemNumberBlocking.openSettings(context))
        assertNotNull(launched)
        val intent = requireNotNull(launched)
        assertNull(intent.data)
        assertTrue(intent.extras == null || intent.extras!!.isEmpty)
    }

    @Test fun missingServiceAndRejectedActivitiesFallBackWithoutCrashing() {
        var launches = 0
        val missing = object : ContextWrapper(compose.activity) {
            override fun getSystemService(name: String): Any? = if (name == Context.TELECOM_SERVICE) null else super.getSystemService(name)
            override fun startActivity(intent: Intent) { launches++ }
        }
        assertFalse(SystemNumberBlocking.openSettings(missing))
        assertEquals(0, launches)
        for (failure in listOf(ActivityNotFoundException(), SecurityException("Restricted profile"))) {
            val rejected = object : ContextWrapper(compose.activity) {
                override fun startActivity(intent: Intent) { launches++; throw failure }
            }
            assertFalse(SystemNumberBlocking.openSettings(rejected))
        }
        assertEquals(2, launches)
    }
}
