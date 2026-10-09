package ph.smishguard.model

import android.content.Context
import ai.onnxruntime.*
import org.json.JSONObject
import java.io.File
import java.nio.LongBuffer
import java.security.MessageDigest
import kotlin.math.exp
import ph.smishguard.BuildConfig

/** CPU-only ONNX; no network, input persistence or automatic/reporting path. */
class MbertDetector(context: Context, metadataJson: String): Detector, AutoCloseable {
    val metadata=JSONObject(metadataJson)
    val tokenizer: BertWordPiece
    private val words: Set<String>
    private val environment=OrtEnvironment.getEnvironment()
    private val session: OrtSession
    val modelLoadMillis: Double
    override val status="Experimental · mBERT · " + metadata.getString("model_version")
    init {
        val started=System.nanoTime()
        require(metadata.getInt("schema_version")==5 && metadata.getString("algorithm")=="mbert")
        require(metadata.getString("base_model")=="google-bert/bert-base-multilingual-cased")
        require(metadata.getString("revision")=="3f076fdb1ab68d5b2880cb87a0886f315b8146f8")
        require(metadata.getJSONArray("classes").toString()=="[\"ham\",\"smishing\"]")
        val quantizedExperiment = BuildConfig.BUILD_TYPE == "mbertQuantized"
        require(metadata.getString("positive_class")=="smishing" &&
            metadata.getString("precision")==if (quantizedExperiment) "int8_dynamic" else "float32")
        if (quantizedExperiment) require(metadata.getString("evaluation_status")=="experimental_quantization" &&
            metadata.getString("reference_model_sha256").matches(Regex("[0-9a-f]{64}")))
        require(metadata.getString("score_transform")=="sigmoid_of_logit_difference")
        require(metadata.getInt("max_length") in 2..512)
        val tokenConfig=metadata.getJSONObject("tokenizer")
        require(tokenConfig.getString("type")=="BertWordPiece" && !tokenConfig.getBoolean("lowercase") &&
            !tokenConfig.getBoolean("strip_accents") && tokenConfig.getBoolean("clean_text") &&
            tokenConfig.getBoolean("handle_chinese_chars") && tokenConfig.getInt("max_chars_per_word")==100)
        require(listOf("model_sha256","vocab_sha256").all { metadata.getString(it).matches(Regex("[0-9a-f]{64}")) })
        require(!metadata.getBoolean("synthetic") && !metadata.getBoolean("automatic_warnings_approved") && metadata.getBoolean("quantized")==quantizedExperiment)
        require(metadata.getString("threshold_comparison")=="greater_or_equal" && metadata.getDouble("threshold") in 0.0..1.0)
        val calibration=metadata.getJSONObject("calibration")
        require(calibration.getString("method")=="sigmoid" && !calibration.getBoolean("evaluated"))
        require(calibration.getDouble("a").isFinite() && calibration.getDouble("b").isFinite())
        val vocabulary=context.assets.open("vocab.txt").use { it.readBytes() }
        require(sha(vocabulary)==metadata.getString("vocab_sha256"))
        tokenizer=BertWordPiece(vocabulary.toString(Charsets.UTF_8).lineSequence().filter{it.isNotEmpty()}.toList(),metadata.getInt("max_length"))
        words=metadata.getJSONArray("assessability_vocabulary").let { a -> (0 until a.length()).map{a.getString(it)}.toSet() }
        val model=ModelCache.verified(context.noBackupFilesDir,metadata.getString("model_sha256")) {
            context.assets.open("model.onnx")
        }
        OrtSession.SessionOptions().use { options ->
            options.setIntraOpNumThreads(2);options.setInterOpNumThreads(1)
            options.setCPUArenaAllocator(false);options.setMemoryPatternOptimization(false)
            session=environment.createSession(model.absolutePath,options)
        }
        try {
            require(session.inputNames==setOf("input_ids","attention_mask","token_type_ids") && session.outputNames==setOf("logits"))
        } catch (e: Exception) { session.close(); throw e }
        modelLoadMillis=(System.nanoTime()-started)/1e6
    }
    private var closed = false
    @Synchronized override fun close() { if (!closed) { session.close(); closed = true } }
    @Synchronized fun rawLogits(encoded: BertWordPiece.Encoded): FloatArray {
        check(!closed)
        val shape=longArrayOf(1,tokenizer.maxLength.toLong())
        OnnxTensor.createTensor(environment,LongBuffer.wrap(encoded.ids),shape).use { ids ->
            OnnxTensor.createTensor(environment,LongBuffer.wrap(encoded.mask),shape).use { mask ->
                OnnxTensor.createTensor(environment,LongBuffer.wrap(encoded.types),shape).use { types ->
                    session.run(mapOf("input_ids" to ids,"attention_mask" to mask,"token_type_ids" to types)).use { result ->
                        @Suppress("UNCHECKED_CAST")
                        return (result[0].value as Array<FloatArray>)[0].copyOf()
                    }
                }
            }
        }
    }
    fun score(logits: FloatArray): Double {
        require(logits.size==2 && logits.all{it.isFinite()})
        val cal=metadata.getJSONObject("calibration")
        return 1.0/(1.0+exp(-(cal.getDouble("a")*(logits[1].toDouble()-logits[0].toDouble())+cal.getDouble("b"))))
    }
    override suspend fun detect(text: String): Detection {
        if(text.length>MAX_MESSAGE_LENGTH)return Detection.Failure
        if(!Assessability.canAssess(Preprocessing.tokens(Assessability.textOutsideLinks(text)),words::contains))return Detection.UnableToAssess
        return try {
            val encoded=tokenizer.encode(BertWordPiece.redact(text))
            val score=score(rawLogits(encoded))
            val policy=DecisionPolicy(metadata.getDouble("threshold"),inclusive=true)
            Detection.Success(policy.suspicious(score),score,experimental=true,policy=policy,tokenWindow=encoded.window)
        } catch (_: Exception) { Detection.Failure }
    }
    companion object {
        private fun sha(bytes: ByteArray)=MessageDigest.getInstance("SHA-256").digest(bytes).joinToString(""){"%02x".format(it)}
        private fun sha(file: File): String {
            val digest=MessageDigest.getInstance("SHA-256")
            file.inputStream().use { input -> val block=ByteArray(1024*1024);while(true){val n=input.read(block);if(n<0)break;digest.update(block,0,n)} }
            return digest.digest().joinToString(""){"%02x".format(it)}
        }
    }
}
