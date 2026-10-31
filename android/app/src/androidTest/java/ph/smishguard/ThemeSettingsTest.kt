package ph.smishguard

import android.graphics.Bitmap
import android.graphics.Canvas
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.core.view.WindowCompat
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import ph.smishguard.data.ThemeMode

/** Real Settings interactions, rendered colours and persistence; no synthetic model. */
class ThemeSettingsTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val app get() = compose.activity.application as SoftwareTestApp

    private fun settings() {
        compose.waitUntil(10000) { compose.onAllNodes(isSelectable() and hasText("Settings")).fetchSemanticsNodes().size == 1 }
        compose.onNode(isSelectable() and hasText("Settings")).performClick()
        compose.waitUntil(10000) { compose.onAllNodesWithTag("theme_dark").fetchSemanticsNodes().isNotEmpty() }
    }

    private fun verify(mode: ThemeMode, dark: Boolean, screenshot: String) {
        compose.onNodeWithTag("theme_${mode.storedValue}").performScrollTo().assertIsSelected()
        compose.waitUntil(10000) { runBlocking { app.preferences.flow.first().themeMode == mode } }
        compose.waitForIdle()
        compose.activityRule.scenario.onActivity { activity ->
            val controller = WindowCompat.getInsetsController(activity.window, activity.window.decorView)
            assertEquals("Status-bar icon contrast", !dark, controller.isAppearanceLightStatusBars)
            assertEquals("Navigation-bar icon contrast", !dark, controller.isAppearanceLightNavigationBars)
            val view = activity.window.decorView
            val bitmap = Bitmap.createBitmap(view.width, view.height, Bitmap.Config.ARGB_8888)
            view.draw(Canvas(bitmap))
            // The page's left margin is the solid GlassBackground, outside all panels/text.
            assertEquals("Rendered theme background", if (dark) 0xFF0E1613.toInt() else 0xFFF2F6F3.toInt(),
                bitmap.getPixel(4, bitmap.height / 2))
            val output = File(app.filesDir, "theme-review").apply { mkdirs() }
            File(output, "$screenshot.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
            bitmap.recycle()
        }
    }

    @Test fun themeChoicePersistsAndRendersCorrectly() {
        val args = InstrumentationRegistry.getArguments()
        val restore = args.getString("themePhase") == "verifyStoredDark"
        app.testDetector = null
        if (BuildConfig.BUILD_TYPE == "nbGeneralization")
            assertTrue(runBlocking { app.detector() } is ph.smishguard.model.NbGeneralizationDetector)
        if (BuildConfig.BUILD_TYPE == "selectedSvm")
            assertTrue(runBlocking { app.detector() } is ph.smishguard.model.SelectedSvmDetector)
        if (restore) {
            assertEquals(ThemeMode.DARK, runBlocking { app.preferences.flow.first().themeMode })
            settings()
            verify(ThemeMode.DARK, true, "dark-after-process-restart")
        } else {
            runBlocking {
                app.preferences.clear(); app.preferences.acceptPrivacy(); app.preferences.onboard()
                app.preferences.reduceTransparency(true)
            }
            settings()
            val deviceDark = args.getString("deviceDark") == "true"
            verify(ThemeMode.SYSTEM, deviceDark, "follow-system")
            compose.onNodeWithTag("theme_light").performScrollTo().performClick()
            verify(ThemeMode.LIGHT, false, "light")
            compose.onNodeWithTag("theme_dark").performScrollTo().performClick()
            verify(ThemeMode.DARK, true, "dark")
            compose.activityRule.scenario.recreate()
            settings()
            verify(ThemeMode.DARK, true, "dark-after-recreation")
            compose.onNodeWithTag("theme_system").performScrollTo().performClick()
            verify(ThemeMode.SYSTEM, deviceDark, "follow-system-restored")
            // The host force-stops the process before a second instrumentation invocation.
            compose.onNodeWithTag("theme_dark").performScrollTo().performClick()
            verify(ThemeMode.DARK, true, "dark-before-process-restart")
        }
        File(app.filesDir, "theme-${if (restore) "restart" else "switch"}-verified.json").writeText(
            JSONObject().put("variant", BuildConfig.BUILD_TYPE).put("phase", if (restore) "process-restart" else "switch-and-recreate")
                .put("device_dark", args.getString("deviceDark") == "true").put("passed", true).toString(2))
    }
}
