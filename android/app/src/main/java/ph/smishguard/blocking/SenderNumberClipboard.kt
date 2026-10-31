package ph.smishguard.blocking

import android.content.ClipData
import android.content.ClipDescription
import android.os.Build
import android.os.PersistableBundle

object SenderNumberClipboard {
    /** Caller must only publish this clip after the user chooses to copy the sender. */
    fun createClip(label: String, number: String): ClipData = ClipData.newPlainText(label, number).apply {
        val sensitiveKey = if (Build.VERSION.SDK_INT >= 33) ClipDescription.EXTRA_IS_SENSITIVE else "android.content.extra.IS_SENSITIVE"
        description.extras = PersistableBundle().apply { putBoolean(sensitiveKey, true) }
    }
}
