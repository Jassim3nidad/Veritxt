package ph.smishguard

import java.io.File
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.MulticlassSvmDetector

class Svm60ParityTest {
    private fun directory(): File? = System.getProperty("smishguard.svm60.parity.dir")?.let(::File)

    @Test fun exactFrozen60ModelMatchesPython() = runBlocking {
        val root = directory(); assumeTrue(root != null)
        val result = MulticlassSvmParity.verify(File(root!!, "model.json").readText(), File(root, "multiclass-svm60-cases.json").readText(), 60)
        File(root, "svm60-jvm-parity.json").writeText(result.toString(2))
    }

    @Test fun bothFrozenModelsAndUnchangedRiskRulesMatchPracticalExamples() = runBlocking {
        val root = directory(); assumeTrue(root != null)
        val result = Svm60PracticalParity.verify(File(root!!, "model.json").readText(),
            File(root, "comparison-svm80-model.json").readText(), File(root, "practical-comparison.json").readText())
        File(root, "practical-jvm-parity.json").writeText(result.toString(2))
    }

    @Test fun wrongTrainingVersionIsRejectedRatherThanLoaded() {
        val root = directory(); assumeTrue(root != null)
        val sixty = File(root!!, "model.json").readText(); val eighty = File(root, "comparison-svm80-model.json").readText()
        assertThrows(Exception::class.java) { MulticlassSvmDetector.parse(eighty, 60) }
        assertThrows(Exception::class.java) { MulticlassSvmDetector.parse(sixty, 80) }
        assertEquals(60, MulticlassSvmDetector.parse(sixty, 60).trainingPercent)
        assertEquals(80, MulticlassSvmDetector.parse(eighty, 80).trainingPercent)
    }
}
