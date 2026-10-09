package ph.smishguard

import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.MbertDetector
import ph.smishguard.model.ModelCache
import org.json.JSONObject
import java.io.File

/** Run in its own instrumentation process: closes the process-owned test session. */
class MbertResourceTest {
    @Test fun sessionCloseIsIdempotentAndPreventsUseAfterClose() = runBlocking {
        val app = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext as SoftwareTestApp
        app.testDetector = null
        val metadata = JSONObject(app.assets.open("model.json").bufferedReader().use { it.readText() })
        val hash = metadata.getString("model_sha256")
        val cache = File(app.noBackupFilesDir, "mbert-$hash.onnx")
        cache.writeText("Controlled incomplete model fixture")
        val pending = File(app.noBackupFilesDir, "mbert-copy.pending")
        pending.writeText("Controlled interrupted copy fixture")
        val model = app.detector() as MbertDetector
        assertEquals(hash, ModelCache.sha(cache))
        assertFalse(pending.exists())
        val encoded = model.tokenizer.encode("hello")
        assertEquals(2, model.rawLogits(encoded).size)
        model.close(); model.close()
        assertThrows(IllegalStateException::class.java) { model.rawLogits(encoded) }
    }
}
