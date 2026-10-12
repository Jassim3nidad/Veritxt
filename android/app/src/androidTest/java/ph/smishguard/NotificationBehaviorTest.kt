package ph.smishguard

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.sms.PermissionState
import ph.smishguard.sms.WarningNotifications

class NotificationBehaviorTest {
    private fun awaitNotificationState(predicate: () -> Boolean) {
        val deadline = android.os.SystemClock.uptimeMillis() + 5000
        while (!predicate() && android.os.SystemClock.uptimeMillis() < deadline) Thread.sleep(50)
        assertTrue("Notification service did not reach the expected state", predicate())
    }
    @Test fun privateNotificationConstructionAndBlockedChannel() {
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getArguments().getString("granted") == "true")
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val manager = context.getSystemService(NotificationManager::class.java)
        assertTrue("Run with notification permission granted on emulator", PermissionState.read(context).notifications)
        val id = WarningNotifications.warn(context, "SGTEST synthetic notification plumbing test only")
        assertNotNull(id)
        awaitNotificationState { manager.activeNotifications.any { it.id == id } }
        val notification = manager.activeNotifications.first { it.id == id }.notification
        assertEquals(Notification.VISIBILITY_SECRET, notification.visibility)
        assertEquals("Possible scam text", notification.extras.getCharSequence(Notification.EXTRA_TITLE)?.toString())
        assertFalse(notification.extras.getCharSequence(Notification.EXTRA_TEXT).toString().contains("SGTEST"))
        assertNotNull(notification.contentIntent)
        manager.cancelAll()
        awaitNotificationState { manager.activeNotifications.isEmpty() }
        manager.createNotificationChannel(NotificationChannel(WarningNotifications.CHANNEL, "Scam warnings", NotificationManager.IMPORTANCE_NONE))
        assertFalse(PermissionState.read(context).notifications)
        assertNull(WarningNotifications.warn(context, "SGTEST blocked channel"))
        assertTrue(manager.activeNotifications.isEmpty())
    }

    @Test fun runtimeDenialSuppressesWarning() {
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getArguments().getString("denied") == "true")
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val manager = context.getSystemService(NotificationManager::class.java)
        assertFalse(PermissionState.read(context).notifications)
        assertNull(WarningNotifications.warn(context, "SGTEST denied"))
        assertTrue(manager.activeNotifications.isEmpty())
    }
}
