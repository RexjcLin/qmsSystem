package com.rexjclin.qmsmobile

import android.app.Application
import com.rexjclin.qmsmobile.data.AppContainer

class QmsApplication : Application() {
    val container: AppContainer by lazy { AppContainer(applicationContext) }
}
