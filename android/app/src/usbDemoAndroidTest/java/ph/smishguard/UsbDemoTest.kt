package ph.smishguard

import android.Manifest
import android.app.Notification
import android.app.NotificationManager
import android.content.pm.PackageManager
import android.os.Build
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import ph.smishguard.model.*
import ph.smishguard.sms.*

/** The host sends the delivered PowerShell samples through the real shell receiver, with radios off. */
class UsbDemoTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun prepareNormalProcessColdStart() = runBlocking {
        val app = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext as SoftwareTestApp
        app.testDetector = null
        app.getSystemService(NotificationManager::class.java).cancelAll()
        PendingChecks.clear()
        app.preferences.acceptPrivacy(); app.preferences.onboard(); app.preferences.scanning(false)
    }

    @Test fun realUsbTransportReportsInstalledModelAndOpensEveryMessage() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val app = compose.activity.application as SoftwareTestApp
        val manager = app.getSystemService(NotificationManager::class.java)
        assertTrue(BuildConfig.DEBUG && BuildConfig.USB_DEMO_ENABLED)
        assertEquals(PackageManager.PERMISSION_DENIED, app.checkSelfPermission(Manifest.permission.DUMP))
        assertEquals(PackageManager.PERMISSION_DENIED, app.checkSelfPermission(Manifest.permission.RECEIVE_SMS))
        if (Build.VERSION.SDK_INT >= 33) instrumentation.uiAutomation.grantRuntimePermission(app.packageName, Manifest.permission.POST_NOTIFICATIONS)
        app.testDetector = null
        manager.cancelAll(); PendingChecks.clear()
        runBlocking { app.preferences.acceptPrivacy(); app.preferences.onboard(); app.preferences.scanning(false) }
        val encoded = InstrumentationRegistry.getArguments().getString("usbCasesBase64") ?: error("Host samples required")
        val samples = JSONArray(String(java.util.Base64.getDecoder().decode(encoded), Charsets.UTF_8))
        val model = app.assets.open("model.json").bufferedReader().use { it.readText() }
        val adapter = app.assets.open("raw-sms-adapter.json").bufferedReader().use { it.readText() }
        fun fixture(name: String) = instrumentation.context.assets.open(name).bufferedReader().use { it.readText() }
        val parity = runBlocking { SelectedSvmParity.verify(model, fixture("selected-svm-cases.json")) }
        val rawParity = runBlocking { RawSmsParity.verify(model, adapter, fixture("raw-sms-cases.json")) }
        assertTrue(runBlocking { app.detector() } is SelectedSvmDetector)
        val ready = File(app.filesDir, "usb-demo-ready")
        try {
            ready.writeText("ready")
            compose.waitUntil(60000) { SmsReportGroup.children(app).size == samples.length() }
            val children = SmsReportGroup.children(app)
            val records = JSONArray()
            for (i in 0 until samples.length()) {
                val sample = samples.getJSONObject(i)
                val text = sample.getString("text")
                val detection = runBlocking { app.assess(text) }
                val assessment = AppRiskPolicy.assess(text, detection)
                val report = InitialSmsReport(assessment, (detection as? Detection.Success)?.category)
                val posted = children.single { it.notification.extras.getCharSequence(Notification.EXTRA_TEXT).toString() == SmsNotificationPreview.text(text) }
                val notification = posted.notification
                assertTrue(notification.extras.getBoolean(CheckPrompt.EXTRA_DEMO))
                assertEquals("Demo · " + app.getString(ph.smishguard.ui.RiskPresentation.label(assessment.level)), notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString())
                assertEquals(SmsNotificationPreview.text(text) + "\n" + report.expanded(app), notification.extras.getCharSequence(Notification.EXTRA_BIG_TEXT).toString())
                assertEquals(if (assessment.level == RiskLevel.HIGH) WarningNotifications.CHANNEL else CheckPrompt.CHANNEL, notification.channelId)
                assertEquals(Notification.VISIBILITY_SECRET, notification.visibility)
                assertNotNull(notification.getLargeIcon())
                assertNull(notification.publicVersion)
                if (assessment.level == RiskLevel.UNABLE_TO_ASSESS) {
                    assertNull(assessment.score)
                    assertFalse(notification.extras.getCharSequence(Notification.EXTRA_BIG_TEXT).toString().contains("/100"))
                }
                notification.contentIntent.send()
                compose.waitUntil(15000) {
                    val state = ViewModelProvider(compose.activity)[CheckViewModel::class.java].state.value
                    state.checkedMessage == text && state.assessment == assessment && state.result == detection
                }
                records.put(JSONObject().put("sample", sample.getString("id"))
                    .put("title", notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString())
                    .put("expanded", notification.extras.getCharSequence(Notification.EXTRA_BIG_TEXT).toString())
                    .put("risk", assessment.level.name).put("risk_score", assessment.score ?: JSONObject.NULL)
                    .put("model_score", (detection as? Detection.Success)?.score ?: JSONObject.NULL)
                    .put("category", (detection as? Detection.Success)?.category?.name ?: JSONObject.NULL)
                    .put("detection", detection.javaClass.simpleName).put("exact_result_opened", true))
            }
            assertEquals(setOf(RiskLevel.LOW.name, RiskLevel.MEDIUM.name, RiskLevel.HIGH.name, RiskLevel.UNABLE_TO_ASSESS.name),
                (0 until records.length()).map { records.getJSONObject(it).getString("risk") }.toSet())
            File(app.filesDir, "usb-demo-results.json").writeText(JSONObject().put("cases", records)
                .put("parity", parity).put("raw_parity", rawParity).put("risk_policy", AppRiskPolicy.VERSION)
                .put("sms_permission", false).put("incoming_sms_consent", false).toString(2))
        } finally { ready.delete() }
    }

    @Test fun demoRespectsPrivacyAndReportsModelFailuresWithoutScores() = runBlocking {
        val app = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext as SoftwareTestApp
        val manager = app.getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= 33) InstrumentationRegistry.getInstrumentation().uiAutomation.grantRuntimePermission(app.packageName, Manifest.permission.POST_NOTIFICATIONS)
        manager.cancelAll(); PendingChecks.clear()
        try {
            app.preferences.clear()
            assertNull(IncomingSmsNotifications.show(app, "Fictional meeting notice", demo = true))
            app.preferences.acceptPrivacy()
            for (failure in listOf(Detection.Unavailable, Detection.InvalidModel, Detection.Failure)) {
                app.testDetector = object : Detector {
                    override val status = "Separate test-only failure fixture"
                    override val automaticWarningsAllowed = true
                    override suspend fun detect(text: String) = failure
                }
                val id = IncomingSmsNotifications.show(app, "Fictional meeting notice", demo = true)
                assertNotNull(id)
                compose.waitUntil(5000) { manager.activeNotifications.any { it.id == id } }
                val notification = manager.activeNotifications.single { it.id == id }.notification
                assertTrue(notification.extras.getCharSequence(Notification.EXTRA_TITLE).toString().contains("Unable to assess"))
                assertFalse(notification.extras.getCharSequence(Notification.EXTRA_BIG_TEXT).toString().contains("/100"))
                manager.cancelAll(); PendingChecks.clear()
            }
        } finally { app.testDetector = null; manager.cancelAll(); PendingChecks.clear() }
    }
}
