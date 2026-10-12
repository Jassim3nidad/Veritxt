package ph.smishguard.data

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.emptyPreferences
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.map
import java.io.IOException

/** Drops the removed "Your city" setting from older installs. */
private val dropCity = object : androidx.datastore.core.DataMigration<androidx.datastore.preferences.core.Preferences> {
    private val key = stringPreferencesKey("manual_city")
    override suspend fun shouldMigrate(currentData: androidx.datastore.preferences.core.Preferences) = key in currentData
    override suspend fun migrate(currentData: androidx.datastore.preferences.core.Preferences) =
        currentData.toMutablePreferences().apply { remove(key) }.toPreferences()
    override suspend fun cleanUp() {}
}
private val Context.preferences by preferencesDataStore("preferences", produceMigrations = { listOf(dropCity) })
data class Preferences(val onboarded: Boolean = false, val scanning: Boolean = false, val reduceTransparency: Boolean = false)
class PreferencesRepository(context: Context) {
    private val store = context.applicationContext.preferences
    private val consent = booleanPreferencesKey("onboarded")
    private val scanning = booleanPreferencesKey("incoming_sms_consent")
    private val solid = booleanPreferencesKey("reduce_transparency")
    val flow = store.data.catch { if (it is IOException) emit(emptyPreferences()) else throw it }.map {
        Preferences(it[consent] ?: false, it[scanning] ?: false, it[solid] ?: false)
    }
    suspend fun onboard() { store.edit { it[consent] = true } }
    suspend fun scanning(enabled: Boolean) { store.edit { it[scanning] = enabled } }
    suspend fun reduceTransparency(enabled: Boolean) { store.edit { it[solid] = enabled } }
    suspend fun clear() { store.edit { it.clear() } }
}
