package ph.smishguard.model

/** Pinned cased BERT tokenizer contract: no lowercase or accent stripping. */
class BertWordPiece(vocabulary: List<String>, val maxLength: Int) {
    private val words = vocabulary.withIndex().associate { it.value to it.index }
    private val special = Regex("\\[(?:PAD|UNK|CLS|SEP|MASK)\\]")
    init {
        require(words.size == vocabulary.size && maxLength in 2..512)
        require(words["[PAD]"] == 0 && words["[UNK]"] == 100 && words["[CLS]"] == 101 && words["[SEP]"] == 102 && words["[MASK]"] == 103)
    }
    private fun chinese(c: Int) = c in 0x4E00..0x9FFF || c in 0x3400..0x4DBF || c in 0x20000..0x2A6DF ||
        c in 0x2A700..0x2B73F || c in 0x2B740..0x2B81F || c in 0x2B820..0x2CEAF || c in 0xF900..0xFAFF || c in 0x2F800..0x2FA1F
    private fun whitespace(c: Int) = c in listOf(32,9,10,13) || Character.getType(c) == Character.SPACE_SEPARATOR.toInt()
    private fun punctuation(c: Int) = c in 33..47 || c in 58..64 || c in 91..96 || c in 123..126 ||
        Character.getType(c) in setOf(Character.CONNECTOR_PUNCTUATION.toInt(),Character.DASH_PUNCTUATION.toInt(),
            Character.START_PUNCTUATION.toInt(),Character.END_PUNCTUATION.toInt(),Character.INITIAL_QUOTE_PUNCTUATION.toInt(),
            Character.FINAL_QUOTE_PUNCTUATION.toInt(),Character.OTHER_PUNCTUATION.toInt())
    private fun basic(text: String): List<String> {
        val tokens=mutableListOf<String>();val current=StringBuilder()
        fun flush() { if (current.isNotEmpty()) { tokens.add(current.toString());current.setLength(0) } }
        for (c in text.codePoints().toArray()) {
            val type=Character.getType(c)
            when {
                c==0 || c==0xFFFD -> {}
                c !in listOf(9,10,13) && type in setOf(Character.CONTROL.toInt(),Character.FORMAT.toInt()) -> {}
                whitespace(c) -> flush()
                chinese(c) || punctuation(c) -> { flush();tokens.add(String(Character.toChars(c))) }
                else -> current.appendCodePoint(c)
            }
        }
        flush();return tokens
    }
    private fun pieces(token: String): List<Int> {
        val chars=token.codePoints().toArray()
        if (chars.size>100) return listOf(100)
        val result=mutableListOf<Int>();var start=0
        while (start<chars.size) {
            var end=chars.size;var found: Int?=null
            while (end>start) {
                val part=(if(start>0) "##" else "")+String(chars,start,end-start)
                found=words[part];if(found!=null)break;end--
            }
            if(found==null)return listOf(100)
            result.add(found);start=end
        }
        return result
    }
    data class Encoded(val ids: LongArray,val mask: LongArray,val types: LongArray)
    fun encode(text: String): Encoded {
        val ids=mutableListOf<Int>();var start=0
        for (match in special.findAll(text)) {
            basic(text.substring(start,match.range.first)).forEach { ids.addAll(pieces(it)) }
            ids.add(words.getValue(match.value));start=match.range.last+1
        }
        basic(text.substring(start)).forEach { ids.addAll(pieces(it)) }
        val selected=listOf(101)+ids.take(maxLength-2)+listOf(102)
        return Encoded(LongArray(maxLength){if(it<selected.size)selected[it].toLong() else 0L},
            LongArray(maxLength){if(it<selected.size)1L else 0L},LongArray(maxLength))
    }
    companion object {
        fun redact(text: String): String {
            var value=Regex("(?:https?://|www\\.)[^\\s<>]+",RegexOption.IGNORE_CASE).replace(text," zzurlzz ")
            value=Regex("[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}").replace(value," zzemailzz ")
            return Regex("[0-9]+").replace(value," zznumberzz ")
        }
    }
}
