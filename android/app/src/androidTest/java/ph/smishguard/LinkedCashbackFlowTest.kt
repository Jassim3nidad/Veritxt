package ph.smishguard

import android.graphics.Bitmap
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import java.io.File
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.*

class LinkedCashbackFlowTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun frozenModelAndSupportingEvidenceShowHighRiskTogether() {
        assertEquals("oldSvm", BuildConfig.BUILD_TYPE)
        val app = compose.activity.application as SoftwareTestApp
        app.testDetector = null
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        val text = "[EWB]You have PHP 5,216 available for cashback. Claim it before it expires today. https://eastwinfu.com/ph"
        fun check(value: String) {
            compose.activityRule.scenario.onActivity {
                ViewModelProvider(it)[CheckViewModel::class.java].apply { share(value); scan() }
            }
            compose.waitUntil(10000) { compose.onAllNodesWithText("Check result").fetchSemanticsNodes().isNotEmpty() &&
                compose.onAllNodesWithText(value).fetchSemanticsNodes().isNotEmpty() }
        }
        check(text)
        compose.onNodeWithText("Smishing", substring = false).assertExists()
        compose.onNodeWithText("High Risk", substring = false).assertExists()
        compose.onNodeWithText("Risk Score: 70/100").assertExists()
        val record = JSONObject().put("risk_profile", AppRiskPolicy.VERSION)
        compose.activityRule.scenario.onActivity {
            val state = ViewModelProvider(it)[CheckViewModel::class.java].state.value
            val prediction = state.result as Detection.Success
            assertEquals(SmsCategory.SMISHING, prediction.category)
            assertEquals(.8037948780036812, prediction.score, 1e-10)
            assertEquals(70, state.assessment!!.score)
            assertTrue(state.assessment!!.indicators.contains(RiskIndicator.CASHBACK_DEADLINE))
            record.put("model_score", prediction.score).put("risk_score", state.assessment!!.score)
                .put("category", prediction.category!!.name).put("risk_level", state.assessment!!.level.name)
        }
        compose.onNodeWithText("SMS category").performScrollTo(); compose.waitForIdle()
        val bitmap = compose.onRoot().captureToImage().asAndroidBitmap()
        File(app.filesDir, "linked-cashback-high.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        bitmap.recycle()
        check(text.substringBefore(" https://"))
        compose.activityRule.scenario.onActivity {
            val risk = ViewModelProvider(it)[CheckViewModel::class.java].state.value.assessment!!
            assertNotEquals(RiskLevel.HIGH, risk.level)
            assertFalse(risk.indicators.contains(RiskIndicator.CASHBACK_DEADLINE))
        }
        check("Kita tayo bukas sa opisina. Ingat sa biyahe.")
        compose.onNodeWithText("Ham", substring = false).assertExists()
        compose.onNodeWithText("Low Risk", substring = false).assertExists()
        File(app.filesDir, "linked-cashback-flow.json").writeText(record.put("no_link_control_not_high", true)
            .put("ordinary_sms_control", "Ham / Low Risk").toString(2))
    }
}
