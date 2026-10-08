package com.rexjclin.qmsmobile.ui.navigation

sealed class QmsRoute(val route: String) {
    data object Splash : QmsRoute("splash")
    data object Login : QmsRoute("login")
    data object PendingBatches : QmsRoute("pending_batches")
    data object InspectionItems : QmsRoute("inspection_items/{batchId}/{productId}") {
        fun create(batchId: Int, productId: Int): String = "inspection_items/$batchId/$productId"
    }

    data object SubmitInspection : QmsRoute("submit_inspection/{batchId}/{productId}") {
        fun create(batchId: Int, productId: Int): String = "submit_inspection/$batchId/$productId"
    }
}
