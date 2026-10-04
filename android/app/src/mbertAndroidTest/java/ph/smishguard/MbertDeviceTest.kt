package ph.smishguard

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.provider.Settings
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.*
import ph.smishguard.privacy.*
import java.time.ZonedDateTime

class MbertDeviceTest {
    @Test fun realOfflineModelParityPolicyAndLatency() = runBlocking {
        assumeTrue(InstrumentationRegistry.getArguments().getString("offline")=="true")
        val i=InstrumentationRegistry.getInstrumentation();val context=i.targetContext
        assertEquals(1,Settings.Global.getInt(context.contentResolver,Settings.Global.AIRPLANE_MODE_ON))
        assertEquals(PackageManager.PERMISSION_DENIED,context.checkSelfPermission(Manifest.permission.INTERNET))
        val app=context.applicationContext as SoftwareTestApp;app.testDetector=null
        val coldStarted=System.nanoTime()
        val detector=app.detector()
        val coldMillis=(System.nanoTime()-coldStarted)/1e6
        assertTrue("Actual mBERT model must load",detector is MbertDetector)
        val model=detector as MbertDetector
        assertThrows(Exception::class.java) { MbertDetector(context,JSONObject(model.metadata.toString()).put("schema_version",0).toString()) }
        assertThrows(java.io.FileNotFoundException::class.java) { MbertDetector(i.context,model.metadata.toString()) }
        val cases=JSONArray(i.context.assets.open("mbert-private-cases.json").bufferedReader().use{it.readText()})
        var maxLogit=0.0;var maxMargin=0.0;var maxScore=0.0;var near=0;var flips=0
        for(n in 0 until cases.length()) {
            val case=cases.getJSONObject(n);val text=case.getString("text")
            val encoded=model.tokenizer.encode(BertWordPiece.redact(text))
            for((field,actual) in listOf("input_ids" to encoded.ids,"attention_mask" to encoded.mask,"token_type_ids" to encoded.types)) {
                val expected=case.getJSONArray(field)
                assertTrue("$field at private index $n",actual.size==expected.length() && actual.indices.all{actual[it]==expected.getLong(it)})
            }
            val logits=model.rawLogits(encoded);val expected=case.getJSONArray("logits")
            val error=logits.indices.maxOf{kotlin.math.abs(logits[it].toDouble()-expected.getDouble(it))}
            val marginError=kotlin.math.abs((logits[1].toDouble()-logits[0].toDouble())-(expected.getDouble(1)-expected.getDouble(0)))
            val score=model.score(logits);val reference=case.getDouble("score");val threshold=model.metadata.getDouble("threshold")
            maxLogit=maxOf(maxLogit,error);maxScore=maxOf(maxScore,kotlin.math.abs(score-reference))
            maxMargin=maxOf(maxMargin,marginError)
            assertTrue("margin at private index $n",marginError<=1e-4)
            assertTrue("logits at private index $n",error<=1e-4)
            assertTrue("score at private index $n",kotlin.math.abs(score-reference)<=1e-5)
            if(kotlin.math.abs(reference-threshold)<=1e-5)near++
            if((score>=threshold)!=case.getBoolean("suspicious")) {
                flips++;assertTrue("threshold at private index $n",kotlin.math.abs(reference-threshold)<=1e-5)
            }
        }
        assertFalse(model.automaticWarningsAllowed)
        for(text in listOf("","qwerty","xqzvplmkj","123456","!!!","https://example.invalid"))
            assertEquals(Detection.UnableToAssess,model.detect(text))
        assertEquals(Detection.Failure,model.detect("a".repeat(10001)))
        assertEquals(Detection.Unavailable,MissingDetector().detect("hello"))
        assertEquals(Detection.InvalidModel,MissingDetector(true).detect("hello"))
        val probes=listOf("Hello po","Bayad na po","Your payment is received.","Your account is suspended. Verify your password at https://account.example now.")
        repeat(20){model.detect(probes[it%4])}
        var scored=0;var abstained=0
        val timings=LongArray(200){n ->
            val start=System.nanoTime();val result=model.detect(probes[n%4]);val elapsed=System.nanoTime()-start
            if(result is Detection.Success){scored++;assertTrue(result.experimental);assertFalse(result.probability)
                assertNull(ReportPayload.create(null,result,ZonedDateTime.now(),City.MANILA,Brand.UNSPECIFIED))}
            else{abstained++;assertEquals(Detection.UnableToAssess,result)}
            elapsed
        }.sorted()
        val record=JSONObject().put("cases",cases.length()).put("max_logit_error",maxLogit).put("max_score_error",maxScore).put("max_margin_error",maxMargin)
            .put("near_threshold_cases",near).put("class_changes",flips).put("model_sha256",model.metadata.getString("model_sha256"))
            .put("model_load_ms",model.modelLoadMillis).put("cold_detector_ms",coldMillis).put("scored",scored).put("abstained",abstained)
            .put("warmups",20).put("scans",200).put("probes",4).put("p50_ms",timings[99]/1e6).put("p95_ms",timings[189]/1e6)
        i.sendStatus(0,Bundle().apply{putString("stream","MBERT_AGGREGATE="+record.toString()+"\n")})
    }
}
