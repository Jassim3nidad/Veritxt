package ph.smishguard

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

class MbertTokenizerTest {
    @Test fun actualCasedTokenizerMatchesFrozenPythonIds() {
        val directory=System.getProperty("smishguard.mbert.parity.dir")
        assumeTrue("Private mBERT parity not configured",directory!=null)
        val root=File(directory!!)
        val metadata=JSONObject(File(root,"app-assets/model.json").readText())
        val vocabulary=File(root,"app-assets/vocab.txt").readLines()
        val type=Class.forName("ph.smishguard.model.BertWordPiece")
        val tokenizer=type.getConstructor(List::class.java,Int::class.javaPrimitiveType).newInstance(vocabulary,metadata.getInt("max_length"))
        val cases=JSONArray(File(root,"android-test-assets/mbert-private-cases.json").readText())
        for(i in 0 until cases.length()) {
            val case=cases.getJSONObject(i)
            val encoded=type.getMethod("encode",String::class.java).invoke(tokenizer,case.getString("text"))
            for((field,getter) in listOf("input_ids" to "getIds","attention_mask" to "getMask","token_type_ids" to "getTypes")) {
                val actual=encoded.javaClass.getMethod(getter).invoke(encoded) as LongArray
                val expected=case.getJSONArray(field)
                assertTrue("tokenizer $field at index $i",actual.size==expected.length() && actual.indices.all{actual[it]==expected.getLong(it)})
            }
        }
        File(root,"jvm-tokenizer-aggregate.json").writeText(JSONObject().put("cases",cases.length()).put("exact_token_ids_masks_types",true).toString(2))
    }
}
