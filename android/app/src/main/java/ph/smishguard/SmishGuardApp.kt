package ph.smishguard

import android.app.Application
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.sync.Mutex
import ph.smishguard.model.Detection
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
    private var loadedDetector: Detector? = null
    private val loadLock = Any()
    private val inference = Mutex()
    internal open val slowNoticeMillis: Long = 7000
    internal open val workDeadlineMillis: Long = 60000
    protected open fun createDetector(): Detector {
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
        return if (BuildConfig.BUILD_TYPE in listOf("mbert", "mbertQuantized")) Class.forName("ph.smishguard.model.MbertDetector")
            .getConstructor(android.content.Context::class.java, String::class.java).newInstance(this, json) as Detector
        else if (BuildConfig.BUILD_TYPE == "lrCalibrated4") SuppliedDetector.parse(json, folded = true)
        else if (BuildConfig.BUILD_TYPE == "lrCandidate") SuppliedDetector.parse(json, candidate = true)
        else if (BuildConfig.BUILD_TYPE in listOf("lr", "nb", "svm"))
            ComparisonDetector(json, BuildConfig.BUILD_TYPE)
        else ModelLoader.parse(json)
    }
    open suspend fun detector(): Detector = withContext(Dispatchers.IO) {
        val context = currentCoroutineContext()
        synchronized(loadLock) {
            context.ensureActive()
            loadedDetector ?: try {
                createDetector().also { if (it !is MissingDetector) loadedDetector = it }
            } catch (e: CancellationException) { throw e }
            catch (_: FileNotFoundException) { MissingDetector() }
            catch (_: Exception) { MissingDetector(invalid = true) }
        }
    }
    // The permit remains held until synchronous native work actually returns.
    // Cancellation prevents publication; it cannot forcibly interrupt session.run.
    suspend fun assess(text: String): Detection {
        if (!inference.tryLock()) return Detection.Busy
        return try {
            withContext(Dispatchers.Default) {
                val model = detector()
                currentCoroutineContext().ensureActive()
                model.detect(text).also { currentCoroutineContext().ensureActive() }
            }
        } finally { inference.unlock() }
    }
    override fun onCreate() { super.onCreate(); WarningNotifications.createChannel(this); ph.smishguard.sms.CheckPrompt.createChannel(this) }
}
