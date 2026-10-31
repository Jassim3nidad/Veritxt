package ph.smishguard

import android.graphics.Bitmap
import android.graphics.Color
import android.media.MediaMetadataRetriever
import android.view.WindowManager
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import ph.smishguard.data.ThemeMode

/** OS compositor captures, without clearing flags or drawing views into a bitmap. */
class ScreenCaptureTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val app get() = compose.activity.application as SoftwareTestApp
    private val directory get() = File(app.filesDir, "capture-review").apply { mkdirs() }

    private fun visible(bitmap: Bitmap) {
        var bright = 0; var dark = 0
        for (x in 0 until bitmap.width step 12) for (y in bitmap.height / 10 until bitmap.height * 9 / 10 step 12) {
            val pixel = bitmap.getPixel(x, y)
            val average = (Color.red(pixel) + Color.green(pixel) + Color.blue(pixel)) / 3
            if (average > 180) bright++
            if (average < 120) dark++
        }
        assertTrue("Capture contains the light app background", bright > 1000)
        assertTrue("Capture contains visible text and controls", dark > 30)
    }

    private fun capture(name: String) {
        compose.waitForIdle()
        compose.activityRule.scenario.onActivity {
            assertEquals("Window must allow screen capture", 0, it.window.attributes.flags and WindowManager.LayoutParams.FLAG_SECURE)
        }
        // Compose semantics can be ready before SurfaceFlinger presents that frame.
        // Poll the real compositor until visible app content has been presented.
        compose.waitUntil(10000) {
            val bitmap = InstrumentationRegistry.getInstrumentation().uiAutomation.takeScreenshot()
            assertNotNull("Android compositor screenshot", bitmap)
            try {
                File(directory, "$name.png").outputStream().use { bitmap!!.compress(Bitmap.CompressFormat.PNG, 100, it) }
                try { visible(bitmap!!); true } catch (_: AssertionError) { false }
            } finally { bitmap?.recycle() }
        }
    }

    @Test fun actualAppAllowsScreenshotsAndRecording() {
        app.testDetector = null
        if (BuildConfig.BUILD_TYPE == "selectedSvm")
            assertTrue(runBlocking { app.detector() } is ph.smishguard.model.SelectedSvmDetector)
        if (BuildConfig.BUILD_TYPE == "nbGeneralization")
            assertTrue(runBlocking { app.detector() } is ph.smishguard.model.NbGeneralizationDetector)
        runBlocking {
            app.preferences.clear(); app.preferences.themeMode(ThemeMode.LIGHT); app.preferences.reduceTransparency(true)
        }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Your privacy").fetchSemanticsNodes().isNotEmpty() }
        capture("privacy")
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard() }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Check a message").fetchSemanticsNodes().isNotEmpty() }
        capture("home")
        compose.activityRule.scenario.onActivity {
            ViewModelProvider(it)[CheckViewModel::class.java].share(
                "SGTEST fictional showcase: Your account is suspended. Send your OTP and PIN to https://example.invalid/account immediately.")
        }
        compose.waitUntil(10000) { compose.onAllNodesWithText("Check message", substring=false).fetchSemanticsNodes().isNotEmpty() }
        capture("message")
        compose.onNodeWithText("Check message", substring=false).performScrollTo().performClick()
        compose.waitUntil(15000) { compose.onAllNodesWithText("Risk Score:", substring=true).fetchSemanticsNodes().isNotEmpty() }
        capture("result")
        compose.onNodeWithText("What does this mean?").performScrollTo().performClick()
        compose.waitUntil(10000) { compose.onAllNodes(isDialog()).fetchSemanticsNodes().isNotEmpty() }
        capture("explanation-dialog")
        compose.onNodeWithText("Close", substring=false).performClick()
        if (InstrumentationRegistry.getArguments().getString("record") == "true") {
            val signal = File(directory, "recording-ready")
            val done = File(directory, "recording-done"); done.delete(); signal.writeText("ready")
            try {
                val end = System.currentTimeMillis() + 45000
                while (!done.exists() && System.currentTimeMillis() < end) Thread.sleep(200)
                assertTrue("Host recorded the app display", done.exists())
            } finally { signal.delete() }
        }
        File(directory, "capture-verification.json").writeText(JSONObject().put("variant",BuildConfig.BUILD_TYPE)
            .put("secure_window_flag",false).put("screenshot_source","Android UiAutomation compositor")
            .put("screenshots",5).put("fictional_message",true).put("actual_bundled_detector",true).toString(2))
    }

    @Test fun recordedDisplayContainsVisibleAppFrames() {
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getArguments().getString("recordingVerification") == "true")
        val video = File(directory,"showcase.mp4")
        assertTrue("Host screen recording exists",video.isFile)
        val retriever = MediaMetadataRetriever()
        try {
            java.io.FileInputStream(video).use { retriever.setDataSource(it.fd) }
            val metadata = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)
            assertNotNull("Recorded video has duration metadata", metadata)
            val duration = metadata!!.toLong()
            assertTrue("Actual video duration",duration >= 4000)
            for (seconds in listOf(1,3)) {
                val bitmap = retriever.getFrameAtTime(seconds*1000000L,MediaMetadataRetriever.OPTION_CLOSEST)
                assertNotNull("Decoded recording frame",bitmap)
                try {
                    visible(bitmap!!)
                    File(directory,"recording-frame-$seconds.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG,100,it) }
                } finally { bitmap?.recycle() }
            }
            File(directory,"recording-verification.json").writeText(JSONObject().put("duration_ms",duration)
                .put("frames_checked",2).put("source","adb screenrecord using Android display capture")
                .put("visible_app_frames",true).toString(2))
        } finally { retriever.release() }
    }
}
