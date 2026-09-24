package ph.smishguard

import android.graphics.Bitmap
import android.graphics.Canvas
import androidx.lifecycle.ViewModelProvider
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File

/** Opt-in test-only evidence. Called only by tests using invented inputs. */
fun recordReliabilitySnapshot(activity: MainActivity, label: String, error: Throwable?, semantics: String) {
    val instrumentation = InstrumentationRegistry.getInstrumentation()
    if (InstrumentationRegistry.getArguments().getString("diagnostics") != "true") return
    val directory = File(activity.filesDir, "reliability").apply { mkdirs() }
    var summary = ""
    lateinit var bitmap: Bitmap
    instrumentation.runOnMainSync {
        val state = ViewModelProvider(activity)[CheckViewModel::class.java].state.value
        summary = "screen=${state.screen}, busy=${state.busy}, length=${state.text.length}, " +
            "result=${state.result?.javaClass?.simpleName}, focus=${activity.hasWindowFocus()}, " +
            "fontScale=${activity.resources.configuration.fontScale}"
        // Render only the test-owned view. FLAG_SECURE remains enabled; native
        // screenshots of this emulator can be black and are not layout evidence.
        val view = activity.window.decorView
        bitmap = Bitmap.createBitmap(view.width, view.height, Bitmap.Config.ARGB_8888)
        view.draw(Canvas(bitmap))
    }
    try {
        File(directory, "$label.txt").writeText(summary + "\n" + (error?.stackTraceToString() ?: "Verified test state") + "\n" + semantics)
        File(directory, "$label.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
    } finally {
        bitmap.recycle()
    }
}
