package ph.smishguard

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.first
import org.junit.Assert.*
import org.junit.Test
import ph.smishguard.model.*
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

class RecoveryTest {
    @Test fun slowInitializationIsSharedAndCancelledSessionCannotPublish() = runBlocking {
        val entered = CountDownLatch(1); val release = CountDownLatch(1)
        val calls = AtomicInteger()
        val fixture = object : Detector {
            override val status = "Recovered loading fixture"
            override suspend fun detect(text: String) = Detection.Success(false, .1)
        }
        val app = object : SmishGuardApp() {
            override fun createDetector(): Detector {
                calls.incrementAndGet(); entered.countDown()
                check(release.await(10, TimeUnit.SECONDS)); return fixture
            }
        }
        val store = ViewModelStore()
        try {
            val vm = withContext(Dispatchers.Main) { CheckViewModel(app).also { store.put("load", it) } }
            assertTrue(entered.await(5, TimeUnit.SECONDS))
            withContext(Dispatchers.Main) { vm.edit("hello"); vm.scan(); vm.endSession(Screen.SETTINGS) }
            assertEquals(Screen.SETTINGS, vm.state.value.screen)
            release.countDown()
            assertSame(fixture, app.detector())
            assertSame(fixture, app.detector())
            assertEquals(1, calls.get())
            delay(100)
            assertNull(vm.state.value.result)
            assertEquals("", vm.state.value.checkedMessage)
        } finally { release.countDown(); withContext(Dispatchers.Main) { store.clear() } }
    }
    @Test fun deadlineStopsWaitingWhileNativePermitSurvivesAndRetryRecovers() = runBlocking {
        val entered = CountDownLatch(1); val release = CountDownLatch(1)
        val calls = AtomicInteger()
        val app = object : SmishGuardApp() {
            override val slowNoticeMillis = 50L
            override val workDeadlineMillis = 250L
            override suspend fun detector() = object : Detector {
                override val status = "Slow fixture"
                override suspend fun detect(text: String): Detection {
                    if (calls.incrementAndGet() == 1) { entered.countDown(); check(release.await(10, TimeUnit.SECONDS)) }
                    return Detection.Success(false, .1)
                }
            }
        }
        val store = ViewModelStore()
        try {
            val vm = withContext(Dispatchers.Main) { CheckViewModel(app).also { store.put("deadline", it); it.edit("hello"); it.scan() } }
            assertTrue(entered.await(5, TimeUnit.SECONDS))
            withTimeout(5000) { vm.state.first { it.error?.contains("taking longer") == true } }
            withTimeout(5000) { vm.state.first { it.result == Detection.Failure } }
            assertFalse(vm.state.value.busy)
            assertEquals(Detection.Busy, app.assess("hello"))
            assertEquals(1, calls.get())
            release.countDown()
            withTimeout(5000) { while (app.assess("hello") == Detection.Busy) delay(10) }
            withContext(Dispatchers.Main) { vm.edit("new hello"); vm.scan() }
            withTimeout(5000) { vm.state.first { it.result is Detection.Success } }
            assertEquals("new hello", vm.state.value.checkedMessage)
        } finally { release.countDown(); withContext(Dispatchers.Main) { store.clear() } }
    }
    @Test fun initializationFailureCanRetryWithoutRestart() = runBlocking {
        val calls = AtomicInteger()
        val app = object : SmishGuardApp() {
            override fun createDetector(): Detector {
                if (calls.incrementAndGet() == 1) error("Controlled initialization failure")
                return object : Detector {
                    override val status = "Recovered fixture"
                    override suspend fun detect(text: String) = Detection.Unavailable
                }
            }
        }
        assertTrue(app.detector() is MissingDetector)
        assertEquals("Recovered fixture", app.detector().status)
        assertEquals("Recovered fixture", app.detector().status)
        assertEquals(2, calls.get())
    }

    @Test fun cancelledSynchronousCallCannotOverlapOrPublishIntoNewSession() = runBlocking {
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val calls = AtomicInteger()
        val detector = object : Detector {
            override val status = "Controlled fixture"
            override suspend fun detect(text: String): Detection {
                calls.incrementAndGet(); entered.countDown()
                check(release.await(10, TimeUnit.SECONDS))
                return Detection.Success(false, 0.1)
            }
        }
        val app = object : SmishGuardApp() { override suspend fun detector() = detector }
        val store = ViewModelStore()
        try {
            val vm = withContext(Dispatchers.Main) { CheckViewModel(app).also { store.put("test", it); it.edit("hello"); it.scan() } }
            assertTrue(entered.await(5, TimeUnit.SECONDS))
            withContext(Dispatchers.Main) { vm.endSession(); vm.edit("new fictional session"); vm.scan() }
            delay(300)
            assertEquals("Never overlap native work after cancellation", 1, calls.get())
            withContext(Dispatchers.Main) { vm.endSession(Screen.SETTINGS) }
            release.countDown(); delay(300)
            assertEquals(Screen.SETTINGS, vm.state.value.screen)
            assertNull(vm.state.value.result)
            assertEquals("", vm.state.value.checkedMessage)
        } finally { release.countDown(); withContext(Dispatchers.Main) { store.clear() } }
    }
}
