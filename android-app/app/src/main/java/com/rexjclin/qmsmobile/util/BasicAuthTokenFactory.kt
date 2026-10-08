package com.rexjclin.qmsmobile.util

import java.util.Base64

object BasicAuthTokenFactory {
    fun create(username: String, password: String): String {
        val raw = "$username:$password"
        val encoded = Base64.getEncoder().encodeToString(raw.toByteArray(Charsets.UTF_8))
        return "Basic $encoded"
    }
}
