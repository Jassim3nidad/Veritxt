package ph.smishguard

import java.io.File
import kotlinx.coroutines.runBlocking
import org.junit.Assume.assumeTrue
import org.junit.Test

class NbGeneralizationParityTest {
    @Test fun frozenNbMatchesPython() = runBlocking {
        val directory = System.getProperty("smishguard.nb.parity.dir")
        assumeTrue("Private NB export required", directory != null)
        val root = File(directory!!)
        val result = NbGeneralizationParity.verify(File(root, "model.json").readText(),
            File(root, "nb-generalization-cases.json").readText())
        File(root, "nb-jvm-parity.json").writeText(result.toString(2))
    }
}
