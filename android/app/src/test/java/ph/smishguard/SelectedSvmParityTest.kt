package ph.smishguard

import java.io.File
import kotlinx.coroutines.runBlocking
import org.junit.Assume.assumeTrue
import org.junit.Test

class SelectedSvmParityTest {
    @Test fun actualSelectedFrozenSvmMatchesPython() = runBlocking {
        val directory = System.getProperty("smishguard.parity.dir")
        assumeTrue("Actual selected SVM export not configured", directory != null && File(directory, "selected-model.json").isFile)
        val root = File(directory!!)
        val aggregate = SelectedSvmParity.verify(File(root, "selected-model.json").readText(), File(root, "selected-cases.json").readText())
        File(root, "selected-jvm-aggregate.json").writeText(aggregate.toString(2))
    }
}
