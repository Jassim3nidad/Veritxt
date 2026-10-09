package ph.smishguard

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

class MbertTokenizerTest {
    @Test fun fictionalWindowBoundaryAndTailCuePreserveExactPrefix() {
        val type = try { Class.forName("ph.smishguard.model.BertWordPiece") }
            catch (_: ClassNotFoundException) { assumeTrue("mBERT variant only", false); return }
        val vocab = MutableList(110) { "unused$it" }
        for ((id, token) in mapOf(0 to "[PAD]", 100 to "[UNK]", 101 to "[CLS]", 102 to "[SEP]", 103 to "[MASK]",
            104 to "hello", 105 to "claim", 106 to "password", 107 to "##s")) vocab[id] = token
        val tokenizer = type.getConstructor(List::class.java, Int::class.javaPrimitiveType).newInstance(vocab, 160)
        fun encode(text: String) = type.getMethod("encode", String::class.java).invoke(tokenizer, text)!!
        fun window(encoded: Any) = encoded.javaClass.getMethod("getWindow").invoke(encoded) as ph.smishguard.model.TokenWindow
        fun ids(encoded: Any) = encoded.javaClass.getMethod("getIds").invoke(encoded) as LongArray
        val short = encode("hello")
        assertFalse(window(short).truncated)
        val full = encode("hello ".repeat(158))
        assertFalse(window(full).truncated)
        val tail = encode("hello ".repeat(158) + "claim passwords")
        assertTrue(window(tail).truncated)
        assertEquals(161, window(tail).totalContentTokens)
        assertEquals(158, window(tail).retainedContentTokens)
        assertArrayEquals(ids(full), ids(tail))
        assertEquals(101L, ids(tail).first()); assertEquals(102L, ids(tail).last())
        assertTrue(window(encode("hello ".repeat(157) + "passwords")).truncated)
        assertFalse(window(encode("hello ".repeat(156) + "passwords")).truncated)
    }
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
