package ph.smishguard

import kotlinx.coroutines.runBlocking
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

class FoldedCandidateTest {
    @Test fun privateFoldedCandidateMatchesPython() = runBlocking {
        val directory = System.getProperty("smishguard.folded.parity.dir")
        assumeTrue("Private folded parity not configured", directory != null)
        val root = File(directory!!)
        val result = FoldedParity.verify(File(root, "model.json").readText(), File(root, "cases.json").readText())
        File(root, "jvm-folded-aggregate.json").writeText(result.toString(2))
    }
}
