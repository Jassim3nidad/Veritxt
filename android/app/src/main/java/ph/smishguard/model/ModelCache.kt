package ph.smishguard.model

import java.io.File
import java.io.InputStream
import java.security.MessageDigest

/** Immutable model bytes only; never message data. */
object ModelCache {
    fun sha(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val block = ByteArray(1024 * 1024)
            while (true) { val n = input.read(block); if (n < 0) break; digest.update(block, 0, n) }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }
    @Synchronized fun verified(directory: File, hash: String, source: () -> InputStream): File {
        require(hash.matches(Regex("[0-9a-f]{64}")))
        val model = File(directory, "mbert-$hash.onnx")
        val pending = File(directory, "mbert-copy.pending")
        // A prior process may have died before publish. Never load its partial bytes.
        if (pending.exists()) check(pending.delete())
        if (model.isFile && sha(model) == hash) return model
        try {
            source().use { input -> java.io.FileOutputStream(pending).use {
                input.copyTo(it); it.fd.sync()
            } }
            require(sha(pending) == hash)
            java.nio.file.Files.move(pending.toPath(), model.toPath(),
                java.nio.file.StandardCopyOption.ATOMIC_MOVE, java.nio.file.StandardCopyOption.REPLACE_EXISTING)
        } finally {
            if (pending.exists()) check(pending.delete())
        }
        require(sha(model) == hash)
        return model
    }
}
