package com.rexjclin.qmsmobile.data

import com.google.gson.annotations.SerializedName
import com.rexjclin.qmsmobile.model.SubmitInspectionRequest
import com.rexjclin.qmsmobile.model.SubmitInspectionResponse
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import java.math.BigDecimal

data class PendingBatchDto(
    @SerializedName("id") val id: Int,
    @SerializedName("code") val code: String,
    @SerializedName("product") val productId: Int,
    @SerializedName("product_name") val productName: String,
    @SerializedName("quantity") val quantity: Int,
    @SerializedName("status") val status: String,
)

data class InspectionItemDto(
    @SerializedName("item_id") val itemId: Int,
    @SerializedName("item_name") val itemName: String,
    @SerializedName("method") val method: String,
    @SerializedName("unit") val unit: String,
    @SerializedName("standard_min") val standardMin: BigDecimal?,
    @SerializedName("standard_max") val standardMax: BigDecimal?,
    @SerializedName("is_required") val isRequired: Boolean,
)

interface QmsApi {
    @GET("inspection/pending/")
    suspend fun getPendingBatches(@Header("Authorization") authHeader: String): List<PendingBatchDto>

    @GET("products/{productId}/inspection-items/")
    suspend fun getInspectionItems(
        @Header("Authorization") authHeader: String,
        @Path("productId") productId: Int,
    ): List<InspectionItemDto>

    @POST("inspection/submit/")
    suspend fun submitInspection(
        @Header("Authorization") authHeader: String,
        @Body request: SubmitInspectionRequest,
    ): SubmitInspectionResponse
}
