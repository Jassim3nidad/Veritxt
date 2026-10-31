package ph.smishguard.demo

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import java.util.Base64
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeout
import ph.smishguard.BuildConfig
import ph.smishguard.SmishGuardApp
import ph.smishguard.model.MAX_MESSAGE_LENGTH
import ph.smishguard.sms.IncomingSmsNotifications

/** Compiled only into usbDemo. Explicit shell broadcasts contain fictional inputs, never real SMS. */
class UsbDemoReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (!BuildConfig.DEBUG || !BuildConfig.USB_DEMO_ENABLED || intent.action != ACTION) return
        val text = decode(intent.getStringExtra(EXTRA_MESSAGE))
        // Discard the transport payload as soon as it has been read. Do not log it.
        intent.removeExtra(EXTRA_MESSAGE)
        if (text == null) { setResult(2, "Invalid demo message", null); return }
        val pending = goAsync()
        val app = context.applicationContext as SmishGuardApp
        CoroutineScope(SupervisorJob() + Dispatchers.Default).launch {
            try {
                val id = withTimeout(7000) { IncomingSmsNotifications.show(app, text, "5550100", demo = true) }
                pending.setResultCode(if (id == null) 3 else -1)
                pending.setResultData(if (id == null) "Open Veritxt and accept privacy; enable Android notifications and both report channels" else "Demo report posted")
            } catch (_: Exception) {
                pending.setResultCode(4)
                pending.setResultData("Demo processing unavailable; retry")
            } finally { pending.finish() }
        }
    }

    companion object {
        const val ACTION = "ph.smishguard.action.USB_DEMO_MESSAGE"
        const val EXTRA_MESSAGE = "message_base64"
        internal fun decode(encoded: String?): String? = try {
            // UTF-8 uses at most four bytes per code point; bound before allocating a decoded buffer.
            if (encoded == null || encoded.length > MAX_MESSAGE_LENGTH * 6) null else {
                val bytes = Base64.getDecoder().decode(encoded)
                Charsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString()
                    .takeIf { it.isNotBlank() && it.length <= MAX_MESSAGE_LENGTH }
            }
        } catch (_: Exception) { null }
    }
}
