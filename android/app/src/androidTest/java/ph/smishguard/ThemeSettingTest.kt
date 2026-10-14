package ph.smishguard

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import ph.smishguard.data.AppTheme

/** Light / Dark / System can be chosen in Settings, apply instantly, and keep the user on Settings. */
class ThemeSettingTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val app get() = compose.activity.application as SmishGuardApp

    @After fun reset() = runBlocking { app.preferences.theme(AppTheme.SYSTEM) }

    @Test fun themeChoiceIsSavedAndStaysOnSettings() {
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard(); app.preferences.theme(AppTheme.SYSTEM) }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Settings").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Settings").performClick()
        for ((label, expected) in listOf("Dark" to AppTheme.DARK, "Light" to AppTheme.LIGHT, "System default" to AppTheme.SYSTEM)) {
            // "System default" also labels a language chip; the Theme row comes after Language, so take the last match.
            val chip = { compose.onAllNodesWithText(label).let { it[it.fetchSemanticsNodes().size - 1] } }
            // Press the chip itself; a coordinate tap after scrolling can land on the floating nav bar.
            chip().performScrollTo().performSemanticsAction(androidx.compose.ui.semantics.SemanticsActions.OnClick) { it() }
            compose.waitUntil(5000) { runBlocking { app.preferences.flow.first().theme } == expected }
            compose.onNodeWithText("Privacy & settings").assertExists()
            chip().assertIsSelected()
        }
    }
}
