package ph.smishguard

import android.os.Bundle
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Test
import org.junit.Assume.assumeTrue

class ComparisonExportTest {
    @Test fun actualBundledPipelineMatchesPrivatePythonExpectations() = runBlocking {
        assumeTrue(BuildConfig.BUILD_TYPE in listOf("lr", "nb", "svm"))
        assumeTrue(InstrumentationRegistry.getArguments().getString("offline") == "true")
        val i = InstrumentationRegistry.getInstrumentation()
        val model = i.targetContext.assets.open("model.json").bufferedReader().use { it.readText() }
        val cases = i.context.assets.open("comparison-private-cases.json").bufferedReader().use { it.readText() }
        val result = ComparisonParity.verify(model, cases, BuildConfig.BUILD_TYPE)
        i.sendStatus(0, Bundle().apply { putString("stream", "COMPARISON_PARITY=" + result.toString() + "\n") })
    }
}
