package com.rexjclin.qmsmobile.util

import org.junit.Assert.assertEquals
import org.junit.Test

class BasicAuthTokenFactoryTest {
    @Test
    fun create_returns_basic_authorization_header() {
        val header = BasicAuthTokenFactory.create("inspector", "secret")

        assertEquals("Basic aW5zcGVjdG9yOnNlY3JldA==", header)
    }
}
