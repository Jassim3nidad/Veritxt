package ph.smishguard

import androidx.annotation.StringRes
import ph.smishguard.ui.HintSummary
import ph.smishguard.ui.Hints
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay
import ph.smishguard.model.Detection
import ph.smishguard.model.MAX_MESSAGE_LENGTH
import ph.smishguard.model.RiskAssessment
import ph.smishguard.model.AppRiskPolicy as RiskPolicy
import ph.smishguard.privacy.SafeDomain
import ph.smishguard.sms.SenderNumbers
import java.time.ZonedDateTime

enum class Screen { HOME, CHECK, RESULT, REPORT, SETTINGS, PRIVACY, HELP }
data class CheckState(val screen: Screen = Screen.HOME, val text: String = "", val busy: Boolean = false,
    val checkedMessage: String = "", @param:StringRes val error: Int? = null, val result: Detection? = null, val domain: String? = null,
    val checkedAt: ZonedDateTime? = null, val hints: HintSummary? = null, val autoWarnings: Boolean = false, val modelStatus: String = "Loading model status…",
    val assessment: RiskAssessment? = null, val senderNumber: String? = null)

class CheckViewModel(application: android.app.Application) : AndroidViewModel(application) {
    private val app = application as SmishGuardApp
    private val mutable = MutableStateFlow(CheckState())
    val state = mutable.asStateFlow()
    private var job: Job? = null
    private var watchdog: Job? = null
    private var generation = 0L
    private fun cancelWork() { generation++; watchdog?.cancel(); watchdog = null; job?.cancel(); job = null }
    init {
        viewModelScope.launch {
            // Loading can suspend while the user navigates, edits or clears a
            // session. Read the current state only after loading has completed.
            val detector = app.detector()
            mutable.value = mutable.value.copy(modelStatus = detector.status, autoWarnings = detector.automaticWarningsAllowed)
        }
    }
    fun edit(text: String) {
        cancelWork()
        mutable.value = mutable.value.copy(text = text.take(MAX_MESSAGE_LENGTH), busy = false,
            checkedMessage = "", result = null, domain = null, checkedAt = null, hints = null, assessment = null, senderNumber = null,
            error = if (text.length > MAX_MESSAGE_LENGTH) R.string.error_too_long else null)
    }
    fun share(text: String) { endSession(Screen.CHECK); edit(text) }
    fun checkPending(text: String?, senderNumber: String? = null) {
        if (text == null) { endSession(Screen.CHECK); mutable.value = mutable.value.copy(error = R.string.error_expired) }
        else { share(text); mutable.value = mutable.value.copy(senderNumber = SenderNumbers.normalize(senderNumber)); scan() }
    }
    fun navigate(screen: Screen) {
        if (screen in setOf(Screen.HOME, Screen.CHECK, Screen.SETTINGS, Screen.PRIVACY, Screen.HELP)) endSession(screen)
        else mutable.value = mutable.value.copy(screen = screen, checkedMessage = "", senderNumber = null)
    }
    fun endSession(screen: Screen = Screen.HOME) {
        cancelWork()
        mutable.value = CheckState(screen = screen, modelStatus = mutable.value.modelStatus, autoWarnings = mutable.value.autoWarnings)
    }
    fun scan() {
        if (mutable.value.text.isBlank()) {
            mutable.value = mutable.value.copy(screen = Screen.RESULT, text = "", checkedMessage = "", result = Detection.UnableToAssess,
                assessment = RiskPolicy.assess("", Detection.UnableToAssess), error = null)
            return
        }
        if (mutable.value.busy) return
        val submittedText = mutable.value.text
        cancelWork()
        val session = generation
        mutable.value = mutable.value.copy(busy = true, error = null)
        watchdog = viewModelScope.launch {
            delay(app.slowNoticeMillis)
            if (session == generation) mutable.value = mutable.value.copy(
                error = R.string.error_slow)
            delay((app.workDeadlineMillis - app.slowNoticeMillis).coerceAtLeast(0))
            if (session == generation) {
                generation++
                job?.cancel()
                mutable.value = mutable.value.copy(screen = Screen.RESULT, text = "", checkedMessage = "", busy = false,
                    result = Detection.Failure, assessment = RiskPolicy.assess(submittedText, Detection.Failure), error = null)
            }
        }
        job = viewModelScope.launch {
            try {
                val result = app.assess(submittedText)
                val status = if (result is Detection.Success) app.detector().status else mutable.value.modelStatus
                if (session == generation) mutable.value = mutable.value.copy(screen = Screen.RESULT,
                    text = "", checkedMessage = submittedText, busy = false, error = null,
                    result = result, assessment = RiskPolicy.assess(submittedText, result), modelStatus = status,
                    hints = Hints.read(submittedText), domain = SafeDomain.fromMessage(submittedText), checkedAt = ZonedDateTime.now())
            } catch (e: CancellationException) { throw e }
            catch (_: Exception) {
                if (session == generation) mutable.value = mutable.value.copy(screen = Screen.RESULT,
                    text = "", checkedMessage = submittedText, busy = false, error = null, result = Detection.Failure,
                    assessment = RiskPolicy.assess(submittedText, Detection.Failure))
            } finally {
                if (session == generation) watchdog?.cancel()
            }
        }
    }
}
