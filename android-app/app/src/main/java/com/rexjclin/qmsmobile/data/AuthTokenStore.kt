package com.rexjclin.qmsmobile.data

import android.content.Context
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.emptyPreferences
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import java.io.IOException

private val Context.authDataStore by preferencesDataStore(name = "qms_auth")

data class StoredSession(
    val authToken: String? = null,
    val username: String? = null,
)

class AuthTokenStore(private val context: Context) {
    private object Keys {
        val AuthToken = stringPreferencesKey("auth_token")
        val Username = stringPreferencesKey("username")
    }

    val sessionFlow: Flow<StoredSession> = context.authDataStore.data
        .catch { exception ->
            if (exception is IOException) emit(emptyPreferences()) else throw exception
        }
        .map { prefs: Preferences ->
            StoredSession(
                authToken = prefs[Keys.AuthToken],
                username = prefs[Keys.Username],
            )
        }

    suspend fun saveSession(authToken: String, username: String) {
        context.authDataStore.edit { prefs ->
            prefs[Keys.AuthToken] = authToken
            prefs[Keys.Username] = username
        }
    }

    suspend fun clearSession() {
        context.authDataStore.edit { prefs ->
            prefs.remove(Keys.AuthToken)
            prefs.remove(Keys.Username)
        }
    }

    suspend fun currentToken(): String? = sessionFlow.first().authToken
}
