package com.rexjclin.qmsmobile.model

import java.math.BigDecimal

data class LoginState(
    val username: String = "",
    val password: String = "",
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
)

data class InspectionBatchItem(
    val id: Int,
    val code: String,
    val productId: Int,
    val productName: String,
    val quantity: Int,
    val status: String,
)

data class InspectionItemDisplayModel(
    val itemId: Int,
    val itemName: String,
    val method: String,
    val unit: String,
    val standardMin: BigDecimal?,
    val standardMax: BigDecimal?,
    val isRequired: Boolean,
) {
    val specLabel: String
        get() = when {
            standardMin != null && standardMax != null -> "$standardMin ~ $standardMax${if (unit.isNotBlank()) " $unit" else ""}"
            standardMin != null -> ">= $standardMin${if (unit.isNotBlank()) " $unit" else ""}"
            standardMax != null -> "<= $standardMax${if (unit.isNotBlank()) " $unit" else ""}"
            unit.isNotBlank() -> unit
            else -> "未設定"
        }
}

data class InspectionResultDraft(
    val itemId: Int,
    val measuredValue: String = "",
    val result: String? = null,
    val remark: String = "",
)

data class SubmitInspectionRequest(
    val batch_id: Int,
    val remark: String,
    val results: List<SubmitInspectionResultInput>,
)

data class SubmitInspectionResultInput(
    val item_id: Int,
    val measured_value: BigDecimal?,
    val result: String,
    val remark: String,
)

data class SubmitInspectionResponse(
    val inspection_id: Int,
    val overall_result: String,
)

enum class AuthSessionState {
    Loading,
    LoggedOut,
    LoggedIn,
}
