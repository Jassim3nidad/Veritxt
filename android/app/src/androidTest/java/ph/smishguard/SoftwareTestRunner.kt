package ph.smishguard

import android.app.Application
import android.content.Context
import androidx.test.runner.AndroidJUnitRunner
import ph.smishguard.model.Detector

/** Injection exists in the separate test APK only, never in the delivered app. */
class SoftwareTestRunner : AndroidJUnitRunner() {
    override fun newApplication(cl: ClassLoader, name: String, context: Context): Application =
        super.newApplication(cl, SoftwareTestApp::class.java.name, context)
}

class SoftwareTestApp : SmishGuardApp() {
    @Volatile var testDetector: Detector? = null
    override suspend fun detector(): Detector = testDetector ?: super.detector()
}
