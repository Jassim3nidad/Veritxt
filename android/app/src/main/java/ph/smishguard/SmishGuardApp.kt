package ph.smishguard

import android.app.Application
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import ph.smishguard.data.PreferencesRepository
import ph.smishguard.model.Detector
import ph.smishguard.model.ModelLoader
import ph.smishguard.model.MissingDetector
import ph.smishguard.model.ComparisonDetector
import ph.smishguard.model.SuppliedDetector
import ph.smishguard.privacy.DisabledReportingRepository
import ph.smishguard.sms.WarningNotifications
import java.io.FileNotFoundException

open class SmishGuardApp : Application() {
    val preferences by lazy { PreferencesRepository(this) }
    val reporting = DisabledReportingRepository()
    // Only immutable model parameters are cached, never input messages or predictions.
    private val detector: Detector by lazy {
        try {
            val json = assets.open("model.json").use {
                val buffer = java.io.ByteArrayOutputStream()
                val chunk = ByteArray(8192)
                while (true) {
                    val count = it.read(chunk)
                    if (count < 0) break
                    require(buffer.size() + count <= 8_000_000)
                    buffer.write(chunk, 0, count)
                }
                buffer.toString("UTF-8")
            }
            if (BuildConfig.BUILD_TYPE in listOf("mbert", "mbertQuantized")) Class.forName("ph.smishguard.model.MbertDetector")
                .getConstructor(android.content.Context::class.java, String::class.java).newInstance(this, json) as Detector
            else if (BuildConfig.BUILD_TYPE == "lrCalibrated4") SuppliedDetector.parse(json, folded = true)
            else if (BuildConfig.BUILD_TYPE == "lrCandidate") SuppliedDetector.parse(json, candidate = true)
            else if (BuildConfig.BUILD_TYPE in listOf("lr", "nb", "svm"))
                ComparisonDetector(json, BuildConfig.BUILD_TYPE)
            else ModelLoader.parse(json)
        } catch (_: FileNotFoundException) { MissingDetector() }
        catch (_: Exception) { MissingDetector(invalid = true) }
    }
    open suspend fun detector(): Detector = withContext(Dispatchers.IO) { detector }
    override fun onCreate() { super.onCreate(); WarningNotifications.createChannel(this) }
}
