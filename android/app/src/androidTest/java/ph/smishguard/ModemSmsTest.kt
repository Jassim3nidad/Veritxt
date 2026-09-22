package ph.smishguard

import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.provider.Telephony
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.Detection
import ph.smishguard.model.Detector
import java.io.File
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/** Run with scripts/emulator_verify.py: the host injects genuine emulator modem events. */
class ModemSmsTest {
    @Test fun modemDeliveryMultipartConsentAndSyntheticSuppression() = runBlocking {
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getArguments().getString("modem") == "true")
        val app = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext as SoftwareTestApp
        val events = LinkedBlockingQueue<String>() // Synthetic test input, process memory only.
        val signals = File(app.filesDir, "sms-test-signals").apply { mkdirs() }
        val manager = app.getSystemService(NotificationManager::class.java)
        val segmentCount = AtomicInteger()
        val observer = object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                segmentCount.set(Telephony.Sms.Intents.getMessagesFromIntent(intent).size)
            }
        }
        androidx.core.content.ContextCompat.registerReceiver(app, observer,
            IntentFilter(Telephony.Sms.Intents.SMS_RECEIVED_ACTION), androidx.core.content.ContextCompat.RECEIVER_EXPORTED)
        manager.cancelAll()
        app.testDetector = object : Detector {
            override val status = "Synthetic software test"
            override val automaticWarningsAllowed = true
            override suspend fun detect(text: String): Detection {
                events.offer(text)
                return Detection.Success(true, .99, synthetic = true)
            }
        }
        try {
            app.preferences.onboard()
            app.preferences.scanning(true)
            File(signals, "single").writeText("ready")
            assertTrue("Modem single SMS not received intact", events.poll(30, TimeUnit.SECONDS) == "SGTEST single kumusta")
            File(signals, "multipart").writeText("ready")
            val multipart = events.poll(30, TimeUnit.SECONDS)
            assertTrue("Modem multipart SMS not assembled intact (received length=${multipart?.length})", multipart == "SGTEST multipart " + "kumusta po ñ ".repeat(20))
            assertTrue("Android must deliver multiple PDUs", segmentCount.get() > 1)
            assertNull("Unexpected duplicate multipart delivery", events.poll(2, TimeUnit.SECONDS))
            app.preferences.scanning(false)
            File(signals, "disabled").writeText("ready")
            assertNull("Consent-off SMS reached detector", events.poll(5, TimeUnit.SECONDS))
            assertEquals("Synthetic output must never create a warning", 0, manager.activeNotifications.size)
        } finally {
            app.preferences.scanning(false)
            app.testDetector = null
            app.unregisterReceiver(observer)
            signals.listFiles()?.forEach { it.delete() }
            signals.delete()
            events.clear()
        }
    }
}
