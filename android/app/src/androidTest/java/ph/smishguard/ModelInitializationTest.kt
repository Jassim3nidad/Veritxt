package ph.smishguard

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.junit.Assert.assertEquals
import org.junit.Test
import ph.smishguard.model.Detection
import ph.smishguard.model.Detector

/** Controls model-load completion without real assets, delays or UI timing. */
class ModelInitializationTest {
    private fun delayedStatusPreserves(action: (CheckViewModel) -> Unit) = runBlocking {
        val started = CompletableDeferred<Unit>()
        val loaded = CompletableDeferred<Detector>()
        val app = object : SmishGuardApp() {
            override suspend fun detector(): Detector {
                started.complete(Unit)
                return loaded.await()
            }
        }
        val store = ViewModelStore()
        try {
            val vm = withContext(Dispatchers.Main) {
                CheckViewModel(app).also { store.put("controlled-load", it) }
            }
            withTimeout(5000) { started.await() }
            val expected = withContext(Dispatchers.Main) {
                action(vm)
                vm.state.value.copy(modelStatus = "Controlled fixture ready")
            }
            loaded.complete(object : Detector {
                override val status = "Controlled fixture ready"
                override suspend fun detect(text: String) = Detection.Unavailable
            })
            val actual = withTimeout(5000) { vm.state.first { it.modelStatus == expected.modelStatus } }
            assertEquals("Loading status must preserve the latest session state", expected, actual)
        } finally {
            withContext(Dispatchers.Main) { store.clear() }
        }
    }

    @Test fun lateModelStatusPreservesSettingsNavigation() = delayedStatusPreserves {
        it.navigate(Screen.SETTINGS)
    }

    @Test fun lateModelStatusPreservesManualInput() = delayedStatusPreserves {
        it.navigate(Screen.CHECK)
        it.edit("Synthetic initialization fixture")
    }

    @Test fun lateModelStatusPreservesClearedSession() = delayedStatusPreserves {
        it.navigate(Screen.CHECK)
        it.edit("Synthetic initialization fixture")
        it.endSession(Screen.CHECK)
    }
}
