package ph.smishguard

import android.Manifest
import android.app.Notification
import android.app.NotificationManager
import android.os.Build
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import ph.smishguard.model.*
import ph.smishguard.sms.*

/** Exercise the receiver's actual notification routing, including model failures and consent changes. */
class AllSmsNotificationsTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val app get() = instrumentation.targetContext.applicationContext as SoftwareTestApp
    private val manager get() = app.getSystemService(NotificationManager::class.java)

    @Before fun ready() = runBlocking {
        instrumentation.uiAutomation.grantRuntimePermission(app.packageName, Manifest.permission.RECEIVE_SMS)
        if (Build.VERSION.SDK_INT >= 33)
            instrumentation.uiAutomation.grantRuntimePermission(app.packageName, Manifest.permission.POST_NOTIFICATIONS)
        app.preferences.acceptPrivacy(); app.preferences.onboard(); app.preferences.scanning(true)
        manager.cancelAll(); PendingChecks.clear()
    }

    @After fun reset() = runBlocking {
        app.testDetector = null
        app.preferences.scanning(false)
        manager.cancelAll(); PendingChecks.clear()
    }

    private fun model(result: Detection) = object : Detector {
        override val status = "Notification routing fixture"
        override val automaticWarningsAllowed = true
        override suspend fun detect(text: String) = result
    }

    private suspend fun expectPrompt(text: String, level: RiskLevel = RiskLevel.UNABLE_TO_ASSESS, score: Int? = null) {
        val sender = "+16505550100"
        val id = IncomingSmsNotifications.show(app, text, sender)
        assertNotNull("Every SMS should notify while enabled", id)
        val deadline = android.os.SystemClock.uptimeMillis() + 5000
        while (manager.activeNotifications.none { it.id == id } && android.os.SystemClock.uptimeMillis() < deadline) delay(50)
        val posted = manager.activeNotifications.single { it.id == id }.notification
        assertEquals(if (level == RiskLevel.HIGH) WarningNotifications.CHANNEL else CheckPrompt.CHANNEL, posted.channelId)
        val expectedTitle = "$sender · " + app.getString(ph.smishguard.ui.RiskPresentation.label(level))
        assertEquals(expectedTitle, posted.extras.getCharSequence(Notification.EXTRA_TITLE).toString())
        assertEquals(SmsNotificationPreview.text(text), posted.extras.getCharSequence(Notification.EXTRA_TEXT).toString())
        val body = posted.extras.getCharSequence(Notification.EXTRA_BIG_TEXT).toString()
        if (score != null) assertTrue(body.contains("Risk Score: $score/100"))
        else { assertTrue(body.contains("Automatic scan unavailable")); assertFalse(body.contains("/100")) }
        assertEquals("View report", posted.actions.first().title.toString())
        assertNotNull("Every initial report includes its risk dial", posted.getLargeIcon())
        assertEquals(Notification.VISIBILITY_SECRET, posted.visibility)
        assertFalse(posted.publicVersion?.extras.toString().contains("/100"))
        assertNull("The dial stays out of the public lockscreen version", posted.publicVersion?.getLargeIcon())
        assertTrue(posted.extras.toString().contains(sender))
        assertEquals(SmsReportGroup.KEY, posted.group)
        assertEquals(1, manager.activeNotifications.size)
        val pendingId = posted.contentIntent.intentSender // An opaque intent sender never exposes SMS text.
        assertNotNull(pendingId)
        manager.cancelAll(); PendingChecks.clear()
        while (manager.activeNotifications.isNotEmpty() && android.os.SystemClock.uptimeMillis() < deadline) delay(50)
    }

    @Test fun lowMediumHighAndUnassessableSmsAllNotify() = runBlocking {
        val cases = listOf(
            Triple("Kita tayo bukas sa opisina.", Detection.Success(false, .1), RiskLevel.LOW),
            Triple("Please review the meeting agenda.", Detection.Success(true, .9), RiskLevel.MEDIUM),
            Triple("Send your OTP immediately.", Detection.Success(true, .9), RiskLevel.HIGH),
            Triple("123456", Detection.UnableToAssess, RiskLevel.UNABLE_TO_ASSESS)
        )
        for ((text, result, level) in cases) {
            app.testDetector = model(result)
            val risk = AppRiskPolicy.assess(text, app.assess(text))
            assertEquals(level, risk.level)
            expectPrompt(text, level, risk.score)
        }
    }

    @Test fun missingInvalidFailedAndBusyModelsStillPrompt() = runBlocking {
        for (result in listOf(Detection.Unavailable, Detection.InvalidModel, Detection.Failure, Detection.Busy)) {
            app.testDetector = model(result)
            expectPrompt("SGTEST ordinary incoming message")
        }
        app.testDetector = MissingDetector()
        expectPrompt("SGTEST message without an automatic model")
    }

    @Test fun thrownInferenceErrorStillPrompts() = runBlocking {
        app.testDetector = object : Detector {
            override val status = "Throwing fixture"
            override val automaticWarningsAllowed = true
            override suspend fun detect(text: String): Detection = error("Synthetic inference failure")
        }
        expectPrompt("SGTEST incoming message after model failure")
    }

    @Test fun slowInferenceStillPrompts() = runBlocking {
        app.testDetector = object : Detector {
            override val status = "Slow fixture"
            override val automaticWarningsAllowed = true
            override suspend fun detect(text: String): Detection { delay(10000); return Detection.Failure }
        }
        expectPrompt("SGTEST incoming message after model timeout")
    }

    @Test fun scanningOffAndMissingPrivacyConsentSuppressNotifications() = runBlocking {
        app.testDetector = model(Detection.Success(false, .1))
        app.preferences.scanning(false)
        assertNull(IncomingSmsNotifications.show(app, "SGTEST disabled"))
        app.preferences.clear(); app.preferences.scanning(true)
        assertNull(IncomingSmsNotifications.show(app, "SGTEST privacy not accepted"))
        assertTrue(manager.activeNotifications.isEmpty())
    }

    @Test fun consentRevokedDuringInferenceSuppressesNotification() = runBlocking {
        app.testDetector = object : Detector {
            override val status = "Consent change fixture"
            override val automaticWarningsAllowed = true
            override suspend fun detect(text: String): Detection {
                app.preferences.scanning(false)
                return Detection.Success(false, .1)
            }
        }
        assertNull(IncomingSmsNotifications.show(app, "SGTEST revoked while checking"))
        assertTrue(manager.activeNotifications.isEmpty())
    }

    @Test fun nearbySmsWaitForInferenceAndKeepSeparateReports() = runBlocking {
        app.testDetector = object : Detector {
            override val status = "Concurrent incoming fixture"
            override val automaticWarningsAllowed = true
            override suspend fun detect(text: String): Detection {
                delay(150)
                return Detection.Success(text.contains("OTP"), .9, category = if (text.contains("OTP")) SmsCategory.SMISHING else SmsCategory.HAM)
            }
        }
        val messages = listOf("Kita tayo bukas sa opisina.", "Send your OTP immediately.", "123456")
        val ids = coroutineScope { messages.map { async { IncomingSmsNotifications.show(app, it) } }.awaitAll() }
        assertEquals(3, ids.filterNotNull().distinct().size)
        val deadline = android.os.SystemClock.uptimeMillis() + 5000
        while (manager.activeNotifications.count { it.id in ids } < 3 && android.os.SystemClock.uptimeMillis() < deadline) delay(50)
        // Android may add an automatic group summary; only the three posted report IDs are SMS reports.
        val reports = manager.activeNotifications.filter { it.id in ids }
        assertEquals(setOf("Unknown sender · Low Risk", "Unknown sender · High Risk", "Unknown sender · Unable to assess"),
            reports.map { it.notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString() }.toSet())
        val bodies = reports.map { it.notification.extras.getCharSequence(Notification.EXTRA_BIG_TEXT).toString() }
        assertTrue(bodies.any { it.contains("0/100") && it.contains("Ham") })
        assertTrue(bodies.any { it.contains("100/100") && it.contains("Smishing") })
        assertTrue(bodies.any { it.contains("Automatic scan unavailable") && !it.contains("/100") })
    }

    @Test fun manualOnlyModelDoesNotInventAnAutomaticScore() = runBlocking {
        app.testDetector = object : Detector {
            override val status = "Manual-only fixture"
            override suspend fun detect(text: String): Detection = error("Must not run automatically")
        }
        expectPrompt("SGTEST manual-only model")
    }

    @Test fun reportLabelsAreLocalizedWithoutExposingInput() {
        val config = android.content.res.Configuration(app.resources.configuration)
        config.setLocales(android.os.LocaleList.forLanguageTags("fil"))
        val context = app.createConfigurationContext(config)
        val report = InitialSmsReport(AppRiskPolicy.assess("Ordinary fictional SMS", Detection.Success(false, .1)), SmsCategory.HAM)
        assertEquals("SMS: Mababang Panganib", report.title(context))
        assertEquals("Iskor ng Panganib: 0/100 · Ham", report.summary(context))
        assertFalse(report.expanded(context).contains("Ordinary fictional SMS"))
    }

    @Test fun gaugeNeedleAndUnavailableStateMatchTheIndex() {
        val low = NotificationRiskGauge.render(0)
        val high = NotificationRiskGauge.render(100)
        val unknown = NotificationRiskGauge.render(null)
        fun isPointer(bitmap: android.graphics.Bitmap, x: Int, y: Int): Boolean {
            val pixel = bitmap.getPixel(x, y)
            return android.graphics.Color.red(pixel) < 80 && android.graphics.Color.green(pixel) < 80
        }
        try {
            // Endpoints point into opposite bottom segments, rather than displaying a fixed illustration.
            assertTrue(isPointer(low, 78, 169))
            assertFalse(isPointer(high, 78, 169))
            assertTrue(isPointer(high, 178, 169))
            assertFalse(isPointer(low, 178, 169))
            assertFalse(isPointer(unknown, 78, 169))
            assertFalse(isPointer(unknown, 178, 169))
            assertFalse("An unscored dial must not look like Low Risk", unknown.sameAs(low))
        } finally { low.recycle(); high.recycle(); unknown.recycle() }
    }

    @Test fun previewsAreBoundedPlainTextAndDoNotSplitEmoji() {
        assertEquals("Hello meeting now", SmsNotificationPreview.text("Hello\n\tmeeting\u202Enow"))
        val preview = SmsNotificationPreview.text("😀".repeat(100))
        assertEquals(91, preview.codePointCount(0, preview.length))
        assertTrue(preview.endsWith("…"))
        assertFalse(Character.isHighSurrogate(preview[preview.length - 2]))
    }

    @Test fun oneGroupIdentifiesMessagesAndKeepsItsHeaderGeneric() = runBlocking {
        app.testDetector = model(Detection.Success(false, .1))
        val first = IncomingSmsNotifications.show(app, "SGPREVIEW Team meeting at noon", "5550901")!!
        IncomingSmsNotifications.show(app, "SGPREVIEW Bring the printed draft", "5550902")!!
        suspend fun await(label: String, predicate: () -> Boolean) {
            val deadline = android.os.SystemClock.uptimeMillis() + 5000
            while (!predicate() && android.os.SystemClock.uptimeMillis() < deadline) delay(50)
            assertTrue("Grouped report state did not update: $label", predicate())
        }
        await("two-report header") { manager.activeNotifications.any { it.tag == SmsReportGroup.TAG } }
        val summary = manager.activeNotifications.single { it.tag == SmsReportGroup.TAG }.notification
        assertEquals("2 SMS reports", summary.extras.getCharSequence(Notification.EXTRA_TITLE).toString())
        assertTrue(summary.flags and Notification.FLAG_GROUP_SUMMARY != 0)
        assertEquals(SmsReportGroup.KEY, summary.group)
        assertFalse(summary.extras.toString().contains("555090"))
        assertFalse(summary.extras.toString().contains("SGPREVIEW"))
        val children = SmsReportGroup.children(app)
        assertEquals(2, children.size)
        assertTrue(children.all { it.notification.visibility == Notification.VISIBILITY_SECRET })
        assertTrue(children.all { it.notification.publicVersion == null })
        children.single { it.id == first }.notification.actions[1].actionIntent.send()
        await("last child preserved with one-report header") {
            SmsReportGroup.children(app).size == 1 && manager.activeNotifications.any {
                it.tag == SmsReportGroup.TAG && it.notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString() == "1 SMS report"
            }
        }
        assertEquals("5550902 · Low Risk", SmsReportGroup.children(app).single().notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString())
        // Swiping the group header explicitly dismisses its reports; it never opens an arbitrary SMS.
        IncomingSmsNotifications.show(app, "SGPREVIEW Another separate message", "5550903")
        await("new child updates header count") {
            manager.activeNotifications.any { it.tag == SmsReportGroup.TAG && it.notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString() == "2 SMS reports" }
        }
        manager.activeNotifications.single { it.tag == SmsReportGroup.TAG }.notification.deleteIntent.send()
        await("group swipe clears its children") { manager.activeNotifications.isEmpty() }
    }
}
