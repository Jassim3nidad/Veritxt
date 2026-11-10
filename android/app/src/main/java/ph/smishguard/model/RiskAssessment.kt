package ph.smishguard.model

import java.net.URI
import java.util.Locale

enum class RiskLevel { LOW, MEDIUM, HIGH, UNABLE_TO_ASSESS }
enum class EvidenceStatus { SUSPECTED, NO_SIGNIFICANT_INDICATORS, INSUFFICIENT }
enum class InputKind { MESSAGE, URL, EMAIL_ADDRESS, PHONE_NUMBER, EMAIL_MESSAGE }
enum class AssessmentLimit { INSUFFICIENT_CONTENT, PHONE_IDENTITY, URL_REPUTATION, EMAIL_SCOPE, MODEL_MISSING, MODEL_INVALID, CHECK_FAILED, CHECK_BUSY, SYNTHETIC }

/** Ordinal evidence weights, not fitted coefficients or estimated probabilities. See docs/risk-policy.md. */
enum class RiskIndicator(val weight: Int) {
    CREDENTIAL_REQUEST(70), CREDENTIAL_ENTRY(30), DECEPTIVE_URL(30), PAYMENT_REQUEST(30), IDENTITY_CLAIM(0),
    MODEL_SIGNAL(40), URGENCY(10), REWARD(10), SHORTENED_URL(10), LINK_PRESENT(0), CASHBACK_DEADLINE(30),
    POINTS_OFFER_DEADLINE(30), MODEL_HIGH_CONFIDENCE(30)
}

/** Optional evidence-index-v2 rules. Separate switches let each change be compared on its own. */
data class RiskRules(val codeRequests: Boolean = false, val pointsOffer: Boolean = false, val modelConfidence: Boolean = false) {
    companion object {
        val V1 = RiskRules()
        val V2 = RiskRules(codeRequests = true, pointsOffer = true, modelConfidence = true)
    }
}

data class RiskAssessment(
    val level: RiskLevel,
    val score: Int?,
    val indicators: List<RiskIndicator>,
    val kind: InputKind,
    val limit: AssessmentLimit? = null
) {
    init {
        require((score == null) == (level == RiskLevel.UNABLE_TO_ASSESS))
        require(score == null || RiskPolicy.classify(score) == level)
    }
    val evidence: EvidenceStatus get() = when (level) {
        RiskLevel.UNABLE_TO_ASSESS -> EvidenceStatus.INSUFFICIENT
        RiskLevel.LOW -> EvidenceStatus.NO_SIGNIFICANT_INDICATORS
        else -> EvidenceStatus.SUSPECTED
    }
    /** Items that added points to this result, model signals first. */
    val pointItems: List<RiskIndicator> get() = indicators.filter { it.weight > 0 }.sortedBy {
        when (it) { RiskIndicator.MODEL_SIGNAL -> 0; RiskIndicator.MODEL_HIGH_CONFIDENCE -> 1; else -> 2 }
    }
    val uncappedPoints: Int get() = pointItems.sumOf { it.weight }
}

/** Shared by manual checks and incoming-SMS warnings; never invokes a blocking operation. */
object RiskPolicy {
    const val VERSION = "evidence-index-v1"
    const val VERSION_V2 = "evidence-index-v2"
    /** Fixed before any held-out testing. Applies to the 0-1 score of the Linear SVM builds. */
    const val HIGH_CONFIDENCE = 0.90
    fun classify(score: Int): RiskLevel {
        require(score in 0..100)
        return when { score < 30 -> RiskLevel.LOW; score < 70 -> RiskLevel.MEDIUM; else -> RiskLevel.HIGH }
    }

    private val phone = Regex("\\+?[0-9][0-9 ()-]{5,}[0-9]")
    private val email = Regex("[^\\s@]+@[^\\s@]+\\.[^\\s@]+")
    private val urls = Regex("(?:https?://|www\\.)[^\\s<>]+|(?<![@\\w])(?:[a-z0-9-]+\\.)+[a-z]{2,63}(?:/[^\\s<>]*)?", RegexOption.IGNORE_CASE)
    private val credentials = "(?:otp|m?pin|password|passcode|cvv|card number|one[ -]?time(?: password| code)?|verification code)"
    private val request = Regex("\\b(?:send|share|reply(?: with)?|disclose|ibigay|ipadala)\\b.{0,55}\\b$credentials\\b", RegexOption.IGNORE_CASE)
    private val entry = Regex("\\b(?:enter|provide|submit|confirm|verify|ilagay)\\b.{0,55}\\b$credentials\\b", RegexOption.IGNORE_CASE)
    // Plain "code" stays out: promo and delivery codes are ordinary.
    private val credentialsV2 = "(?:otp|m?pin|password|passcode|cvv|card number|one[ -]?time(?: password| code)?|verification code|security code)"
    private val requestV2 = Regex("\\b(?:send|share|reply(?: with)?|disclose|ibigay|ipadala|give|tell|bigay|bigyan|pahingi|sabihin|i-send|isend)\\b.{0,55}\\b$credentialsV2\\b", RegexOption.IGNORE_CASE)
    private val entryV2 = Regex("\\b(?:enter|provide|submit|confirm|verify|ilagay)\\b.{0,55}\\b$credentialsV2\\b", RegexOption.IGNORE_CASE)
    private val pointsOffer = Regex("\\b(?:points?|rewards?|cash\\s?back|cash|gifts?|rebate|puntos)\\b", RegexOption.IGNORE_CASE)
    private val expiryDeadline = Regex("\\b(?:expir\\w*|deadline|valid until)\\b", RegexOption.IGNORE_CASE)
    private val redeemAction = Regex("\\b(?:redeem|iredeem|claim|iclaim|convert|select|choose|visit|click)\\b", RegexOption.IGNORE_CASE)
    private val negation = Regex("\\b(?:never|not|no|avoid|without|huwag|wag|hindi|don.t|do not)\\b", RegexOption.IGNORE_CASE)
    private val payment = Regex("\\b(?:pay|transfer|deposit|wire|send|bayad|magbayad|ipadala)\\b.{0,45}\\b(?:money|funds|fee|payment|pesos|php|pera|bayad|bitcoin|crypto)\\b", RegexOption.IGNORE_CASE)
    private val urgency = Regex("\\b(?:urgent|immediately|suspended|suspend|locked|deactivated|final notice|act now|within \\d+|ngayon|agad|huling babala)\\b", RegexOption.IGNORE_CASE)
    private val reward = Regex("\\b(?:won|winner|prize|claim your|nanalo|premyo)\\b", RegexOption.IGNORE_CASE)
    private val shorteners = setOf("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly")

    fun inputKind(text: String): InputKind {
        val value = text.trim()
        return when {
            phone.matches(value) -> InputKind.PHONE_NUMBER
            urls.matches(value) -> InputKind.URL
            email.matches(value) -> InputKind.EMAIL_ADDRESS
            Regex("(?im)^(?:from|subject|to):").containsMatchIn(value) -> InputKind.EMAIL_MESSAGE
            else -> InputKind.MESSAGE
        }
    }

    /** Negated advice does not become a request. Deliberately conservative, sentence-local matching. */
    private fun positiveRequest(text: String, pattern: Regex): Boolean =
        text.split(Regex("[.!?;\\n]+(?![0-9])")).any { sentence ->
            pattern.findAll(sentence).any { match ->
                !negation.containsMatchIn(sentence.substring(maxOf(0, match.range.first - 32), match.range.last + 1))
            }
        }

    fun assess(text: String, detection: Detection?, cashbackReview: Boolean = false,
               linkedCashbackReview: Boolean = false, rules: RiskRules = RiskRules.V1): RiskAssessment {
        val kind = inputKind(text)
        fun unable(reason: AssessmentLimit, indicators: List<RiskIndicator> = emptyList()) =
            RiskAssessment(RiskLevel.UNABLE_TO_ASSESS, null, indicators, kind, reason)
        if (text.isBlank() || text.length > MAX_MESSAGE_LENGTH) return unable(AssessmentLimit.INSUFFICIENT_CONTENT)
        if (kind == InputKind.PHONE_NUMBER) return unable(AssessmentLimit.PHONE_IDENTITY)
        if (kind == InputKind.EMAIL_ADDRESS) return unable(AssessmentLimit.EMAIL_SCOPE)
        when (detection) {
            Detection.Failure -> return unable(AssessmentLimit.CHECK_FAILED)
            Detection.Busy -> return unable(AssessmentLimit.CHECK_BUSY)
            Detection.InvalidModel -> return unable(AssessmentLimit.MODEL_INVALID)
            Detection.Unavailable, null -> return unable(AssessmentLimit.MODEL_MISSING)
            is Detection.Success -> {
                if (detection.synthetic) return unable(AssessmentLimit.SYNTHETIC)
                if (!detection.score.isFinite()) return unable(AssessmentLimit.CHECK_FAILED)
            }
            else -> Unit
        }
        val found = linkedSetOf<RiskIndicator>()
        val links = urls.findAll(text).map { it.value.trimEnd('.', ',', ';', ')', ']', '}') }.toList()
        if (links.isNotEmpty()) found += RiskIndicator.LINK_PRESENT
        val parsed = links.mapNotNull { link -> runCatching {
            URI(if (link.startsWith("http", ignoreCase = true)) link else "https://$link")
        }.getOrNull() }
        if (parsed.any { uri -> uri.rawUserInfo != null || uri.host?.let { host ->
                host.split('.').any { it.startsWith("xn--", ignoreCase = true) } ||
                    Regex("[0-9]+(?:\\.[0-9]+){3}").matches(host) || host.contains(':')
            } == true }) found += RiskIndicator.DECEPTIVE_URL
        if (parsed.any { it.host?.lowercase(Locale.ROOT) in shorteners }) found += RiskIndicator.SHORTENED_URL

        // URL paths, email addresses and query strings are not human requests.
        val prose = email.replace(urls.replace(text, " "), " ")
        if (positiveRequest(prose, if (rules.codeRequests) requestV2 else request)) found += RiskIndicator.CREDENTIAL_REQUEST
        else if (positiveRequest(prose, if (rules.codeRequests) entryV2 else entry)) found += RiskIndicator.CREDENTIAL_ENTRY
        if (positiveRequest(prose, payment)) found += RiskIndicator.PAYMENT_REQUEST
        if (ph.smishguard.ui.Hints.read(prose).brand != null) found += RiskIndicator.IDENTITY_CLAIM
        if (urgency.containsMatchIn(prose)) found += RiskIndicator.URGENCY
        if (reward.containsMatchIn(prose)) found += RiskIndicator.REWARD
        val reviewCashback = cashbackReview || (linkedCashbackReview && parsed.any { it.host != null })
        if (reviewCashback && kind == InputKind.MESSAGE && CashbackDeadlineReview.matches(prose))
            found += RiskIndicator.CASHBACK_DEADLINE
        // The cashback cue and this one describe the same evidence, so only one can count.
        if (rules.pointsOffer && kind == InputKind.MESSAGE && parsed.any { it.host != null } &&
            RiskIndicator.CASHBACK_DEADLINE !in found && pointsOffer.containsMatchIn(prose) &&
            expiryDeadline.containsMatchIn(prose) && positiveRequest(prose, redeemAction)) found += RiskIndicator.POINTS_OFFER_DEADLINE
        // SMS models have no validated standalone-URL, phone or email classification capability.
        val usableModel = detection is Detection.Success && kind == InputKind.MESSAGE &&
            Preprocessing.tokens(Assessability.textOutsideLinks(text)).any(Assessability::usableWord)
        if (usableModel && detection.suspicious) {
            found += RiskIndicator.MODEL_SIGNAL
            if (rules.modelConfidence && detection.score >= HIGH_CONFIDENCE) found += RiskIndicator.MODEL_HIGH_CONFIDENCE
        }
        val score = found.sumOf { it.weight }.coerceAtMost(100)
        val limit = when (kind) {
            InputKind.URL -> AssessmentLimit.URL_REPUTATION
            InputKind.EMAIL_MESSAGE -> AssessmentLimit.EMAIL_SCOPE
            else -> null
        }
        // A neutral model result can support Low Risk for assessable SMS prose. Other inputs need
        // positive evidence; absence of a reputation lookup must not masquerade as a safe verdict.
        if (!usableModel && score < 30) return unable(limit ?: AssessmentLimit.INSUFFICIENT_CONTENT, found.toList())
        return RiskAssessment(classify(score), score, found.toList(), kind, limit)
    }
}
