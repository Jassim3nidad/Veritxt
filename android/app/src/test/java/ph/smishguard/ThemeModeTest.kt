package ph.smishguard

import org.junit.Assert.assertEquals
import org.junit.Test
import ph.smishguard.data.ThemeMode

class ThemeModeTest {
    @Test fun readsThemeValuesSavedByEitherBranch() {
        for (mode in ThemeMode.entries) {
            assertEquals(mode, ThemeMode.fromStored(mode.storedValue))
            assertEquals(mode, ThemeMode.fromStored(mode.name))
        }
        assertEquals(ThemeMode.SYSTEM, ThemeMode.fromStored(null))
        assertEquals(ThemeMode.SYSTEM, ThemeMode.fromStored("unknown"))
    }
}
