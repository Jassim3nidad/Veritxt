package ph.smishguard

import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import ph.smishguard.model.*

class AssessabilityModelTest {
    private fun model(): SuppliedDetector {
        assumeTrue(BuildConfig.BUILD_TYPE == "development")
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        return ModelLoader.parse(context.assets.open("model.json").bufferedReader().use { it.readText() }) as SuppliedDetector
    }
    @Test fun interceptOnlyInputsDoNotExposePercentages() = runBlocking {
        val model = model()
        for (text in listOf("xqzvplmkj", "asdfghjkl", "zorbquux flarnquux")) {
            assertTrue(model.featureValues(text).isEmpty())
            assertEquals(.336317, (model.rawDetection(text) as Detection.Success).score, .000001)
            assertEquals(Detection.UnableToAssess, model.detect(text))
        }
        // Meaningful but out-of-vocabulary words also have no model evidence.
        for (text in listOf("", " \n", "qwerty", "zzzzzz", "123456", "https://account.example/verify 123456", "OK", "Salamat"))
            assertEquals(Detection.UnableToAssess, model.detect(text))
    }
    @Test fun meaningfulShortMultilingualOtpAndPhishingKeepOriginalScores() = runBlocking {
        val model = model()
        // Invented software probes, not labeled evaluation records.
        val probes = listOf("Hi", "Bayad na po", "Your payment is received.",
            "Nabayaran na po ang account, thank you.", "Your OTP is 123456. Do not share this code.",
            "Your account is suspended. Verify your password at https://account.example now.",
            "Verify https://account.example 123456 789012")
        for (text in probes) {
            val result = model.detect(text)
            assertTrue("A meaningful software probe must remain assessable", result is Detection.Success)
            assertEquals(model.rawDetection(text), result)
            assertFalse(model.automaticWarningsAllowed)
        }
    }
}
