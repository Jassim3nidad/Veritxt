package ph.smishguard

import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.ModelCache
import java.io.File
import java.io.InputStream
import java.nio.file.Files
import java.security.MessageDigest

class ModelCacheTest {
    private val bytes = "fictional immutable model fixture".toByteArray()
    private val hash = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
    @Test fun corruptExistingCacheIsRepairedFromOriginalBytes() {
        val dir = Files.createTempDirectory("sg-cache-test").toFile()
        try {
            File(dir, "mbert-$hash.onnx").writeText("incomplete")
            File(dir, "mbert-copy.pending").writeText("previous process stopped mid-copy")
            val model = ModelCache.verified(dir, hash) { bytes.inputStream() }
            assertArrayEquals(bytes, model.readBytes())
            assertFalse(File(dir, "mbert-copy.pending").exists())
            ModelCache.verified(dir, hash) { error("Verified cache should be reused") }
        } finally { dir.deleteRecursively() }
    }
    @Test fun interruptedCopyLeavesNoPublishableOrPendingFileAndRetrySucceeds() {
        val dir = Files.createTempDirectory("sg-copy-test").toFile()
        try {
            assertThrows(java.io.IOException::class.java) {
                ModelCache.verified(dir, hash) { object : InputStream() {
                    var count = 0
                    override fun read(): Int { if (count++ < 4) return 1; throw java.io.IOException("Controlled interruption") }
                } }
            }
            assertTrue("Partial copy must be removed", dir.listFiles()!!.isEmpty())
            assertArrayEquals(bytes, ModelCache.verified(dir, hash) { bytes.inputStream() }.readBytes())
        } finally { dir.deleteRecursively() }
    }
    @Test fun wrongSourceHashIsNeverPublished() {
        val dir = Files.createTempDirectory("sg-hash-test").toFile()
        try {
            assertThrows(IllegalArgumentException::class.java) { ModelCache.verified(dir, hash) { byteArrayOf(0).inputStream() } }
            assertFalse(File(dir, "mbert-$hash.onnx").exists())
        } finally { dir.deleteRecursively() }
    }
}
