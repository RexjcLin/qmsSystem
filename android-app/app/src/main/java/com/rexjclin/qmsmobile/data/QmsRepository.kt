package com.rexjclin.qmsmobile.data

import com.rexjclin.qmsmobile.model.InspectionBatchItem
import com.rexjclin.qmsmobile.model.InspectionItemDisplayModel
import com.rexjclin.qmsmobile.model.InspectionResultDraft
import com.rexjclin.qmsmobile.model.SubmitInspectionRequest
import com.rexjclin.qmsmobile.model.SubmitInspectionResponse
import com.rexjclin.qmsmobile.model.SubmitInspectionResultInput
import com.rexjclin.qmsmobile.util.BasicAuthTokenFactory
import com.rexjclin.qmsmobile.util.InspectionDraftValidator
import kotlinx.coroutines.flow.Flow
import retrofit2.HttpException
import java.io.IOException

class QmsRepository(
    private val api: QmsApi,
    private val authTokenStore: AuthTokenStore,
) {
    val sessionFlow: Flow<StoredSession> = authTokenStore.sessionFlow

    suspend fun login(username: String, password: String) {
        val authToken = BasicAuthTokenFactory.create(username, password)
        try {
            api.getPendingBatches(authToken)
            authTokenStore.saveSession(authToken, username)
        } catch (exception: Exception) {
            throw IllegalStateException(mapError(exception, "登入失敗，請確認帳號密碼或伺服器設定。"))
        }
    }

    suspend fun logout() {
        authTokenStore.clearSession()
    }

    suspend fun getPendingBatches(): List<InspectionBatchItem> {
        val auth = requireAuthToken()
        return try {
            api.getPendingBatches(auth).map { dto ->
                InspectionBatchItem(
                    id = dto.id,
                    code = dto.code,
                    productId = dto.productId,
                    productName = dto.productName,
                    quantity = dto.quantity,
                    status = dto.status,
                )
            }
        } catch (exception: Exception) {
            throw IllegalStateException(mapError(exception, "無法取得待檢驗批次。"))
        }
    }

    suspend fun getInspectionItems(productId: Int): List<InspectionItemDisplayModel> {
        val auth = requireAuthToken()
        return try {
            api.getInspectionItems(auth, productId).map { dto ->
                InspectionItemDisplayModel(
                    itemId = dto.itemId,
                    itemName = dto.itemName,
                    method = dto.method,
                    unit = dto.unit,
                    standardMin = dto.standardMin,
                    standardMax = dto.standardMax,
                    isRequired = dto.isRequired,
                )
            }
        } catch (exception: Exception) {
            throw IllegalStateException(mapError(exception, "無法取得產品檢驗項目。"))
        }
    }

    suspend fun submitInspection(
        batchId: Int,
        batchRemark: String,
        items: List<InspectionItemDisplayModel>,
        drafts: Map<Int, InspectionResultDraft>,
    ): SubmitInspectionResponse {
        val validation = InspectionDraftValidator.validate(items, drafts)
        if (validation != null) throw IllegalStateException(validation)

        val auth = requireAuthToken()
        val request = SubmitInspectionRequest(
            batch_id = batchId,
            remark = batchRemark,
            results = items.mapNotNull { item ->
                val draft = drafts[item.itemId] ?: return@mapNotNull null
                SubmitInspectionResultInput(
                    item_id = item.itemId,
                    measured_value = InspectionDraftValidator.toBigDecimalOrNull(draft.measuredValue),
                    result = draft.result ?: return@mapNotNull null,
                    remark = draft.remark,
                )
            },
        )
        return try {
            api.submitInspection(auth, request)
        } catch (exception: Exception) {
            throw IllegalStateException(mapError(exception, "送出檢驗結果失敗。"))
        }
    }

    private suspend fun requireAuthToken(): String = authTokenStore.currentToken()
        ?: throw IllegalStateException("請先登入後再操作。")

    private fun mapError(exception: Exception, fallback: String): String = when (exception) {
        is HttpException -> when (exception.code()) {
            401, 403 -> "驗證失敗，請重新登入。"
            else -> fallback
        }
        is IOException -> "無法連線到伺服器，請確認裝置與後端是否在同一網路。"
        is IllegalStateException -> exception.message ?: fallback
        else -> fallback
    }
}
