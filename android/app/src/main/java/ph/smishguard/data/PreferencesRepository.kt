package ph.smishguard.data

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.emptyPreferences
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.map
import java.io.IOException
import java.time.LocalDate

/** Increase when the privacy notice text changes materially; everyone sees and agrees to it again. */
const val PRIVACY_NOTICE_VERSION = 2

/** Drops the removed "Your city" setting from older installs. */
private val dropCity = object : androidx.datastore.core.DataMigration<androidx.datastore.preferences.core.Preferences> {
    private val key = stringPreferencesKey("manual_city")
    override suspend fun shouldMigrate(currentData: androidx.datastore.preferences.core.Preferences) = key in currentData
    override suspend fun migrate(currentData: androidx.datastore.preferences.core.Preferences) =
        currentData.toMutablePreferences().apply { remove(key) }.toPreferences()
    override suspend fun cleanUp() {}
}
private val Context.preferences by preferencesDataStore("preferences", produceMigrations = { listOf(dropCity) })
enum class ThemeMode(val storedValue: String) {
    SYSTEM("system"), LIGHT("light"), DARK("dark");

    companion object {
        fun fromStored(value: String?): ThemeMode = entries.firstOrNull { it.storedValue == value } ?: SYSTEM
    }
}

data class Preferences(val onboarded: Boolean = false, val scanning: Boolean = false, val reduceTransparency: Boolean = false,
                       val privacyVersion: Int = 0, val privacyAcceptedOn: String? = null,
                       val themeMode: ThemeMode = ThemeMode.SYSTEM) {
    val privacyAccepted get() = privacyVersion >= PRIVACY_NOTICE_VERSION
}
class PreferencesRepository(context: Context) {
    private val store = context.applicationContext.preferences
    private val consent = booleanPreferencesKey("onboarded")
    private val scanning = booleanPreferencesKey("incoming_sms_consent")
    private val solid = booleanPreferencesKey("reduce_transparency")
    private val theme = stringPreferencesKey("theme_mode")
    // Only the notice version and the date (no time, no identity) are kept as proof of consent.
    private val privacyVersion = intPreferencesKey("privacy_notice_version")
    private val privacyDate = stringPreferencesKey("privacy_notice_accepted_on")
    val flow = store.data.catch { if (it is IOException) emit(emptyPreferences()) else throw it }.map {
        Preferences(it[consent] ?: false, it[scanning] ?: false, it[solid] ?: false, it[privacyVersion] ?: 0, it[privacyDate],
            ThemeMode.fromStored(it[theme]))
    }
    suspend fun onboard() { store.edit { it[consent] = true } }
    suspend fun scanning(enabled: Boolean) { store.edit { it[scanning] = enabled } }
    suspend fun reduceTransparency(enabled: Boolean) { store.edit { it[solid] = enabled } }
    suspend fun themeMode(mode: ThemeMode) { store.edit { it[theme] = mode.storedValue } }
    suspend fun acceptPrivacy() { store.edit { it[privacyVersion] = PRIVACY_NOTICE_VERSION; it[privacyDate] = LocalDate.now().toString() } }
    suspend fun clear() { store.edit { it.clear() } }
}
