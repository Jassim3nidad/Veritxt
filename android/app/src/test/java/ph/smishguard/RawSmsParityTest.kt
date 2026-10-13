package ph.smishguard
import java.io.File
import kotlinx.coroutines.runBlocking
import org.junit.Assume.assumeTrue
import org.junit.Test

class RawSmsParityTest {
    @Test fun rawSmsReplaysTrainingPreparation() = runBlocking {
        val directory = System.getProperty("smishguard.parity.dir")
        assumeTrue("Raw SMS probes not configured", directory != null && File(directory,"raw-cases.json").isFile)
        val root = File(directory!!)
        val result = RawSmsParity.verify(File(root,"selected-model.json").readText(),File(root,"raw-adapter.json").readText(),File(root,"raw-cases.json").readText())
        File(root,"raw-jvm-aggregate.json").writeText(result.toString(2))
    }
}
