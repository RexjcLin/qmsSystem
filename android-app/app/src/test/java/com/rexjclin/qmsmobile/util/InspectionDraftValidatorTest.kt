package com.rexjclin.qmsmobile.util

import com.google.gson.Gson
import com.google.gson.JsonParser
import com.rexjclin.qmsmobile.data.InspectionItemDto
import com.rexjclin.qmsmobile.data.QmsApi
import com.rexjclin.qmsmobile.model.InspectionItemDisplayModel
import com.rexjclin.qmsmobile.model.InspectionResultDraft
import com.rexjclin.qmsmobile.model.SubmitInspectionResultInput
import com.rexjclin.qmsmobile.model.SubmitInspectionRequest
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Test
import java.math.BigDecimal

class InspectionDraftValidatorTest {
    @Test
    fun retrofit_loads_starts_and_submits_inspection_with_matching_contract() = runBlocking {
        MockWebServer().use { server ->
            server.start()
            server.enqueue(MockResponse().setBody("""[{"product_item_id":42,"item_id":7,"item_name":"Length","method":"Caliper","unit":"mm","is_required":true}]"""))
            server.enqueue(MockResponse().setBody("""{"id":5,"code":"B5","product":3,"product_name":"Part","quantity":10,"status":"INSPECTING"}"""))
            server.enqueue(MockResponse().setResponseCode(201).setBody("""{"inspection_id":9,"overall_result":"FAIL","defect_ids":[11]}"""))
            val api = Retrofit.Builder().baseUrl(server.url("/api/"))
                .addConverterFactory(GsonConverterFactory.create()).build().create(QmsApi::class.java)
            val item = api.getInspectionItems("Basic test", 3).single()
            api.startInspection("Basic test", 5)
            val response = api.submitInspection("Basic test", SubmitInspectionRequest(
                5, "Sample", listOf(SubmitInspectionResultInput(item.productItemId, BigDecimal("5.30"), "FAIL", "")),
            ))
            assertEquals(listOf(11), response.defect_ids)
            assertEquals("/api/products/3/inspection-items/", server.takeRequest().path)
            assertEquals("/api/inspection/batches/5/start/", server.takeRequest().path)
            val request = server.takeRequest()
            assertEquals("POST", request.method)
            assertEquals("/api/inspection/submit/", request.path)
            assertEquals("Basic test", request.getHeader("Authorization"))
            val result = JsonParser.parseString(request.body.readUtf8()).asJsonObject
                .getAsJsonArray("results")[0].asJsonObject
            assertEquals(42, result.get("product_item_id").asInt)
            assertFalse(result.has("item_id"))
        }
    }

    @Test
    fun submission_uses_product_item_id_instead_of_generic_item_id() {
        val gson = Gson()
        val item = gson.fromJson(
            """{"product_item_id":42,"item_id":7,"item_name":"Length","method":"Caliper","unit":"mm","is_required":true}""",
            InspectionItemDto::class.java,
        )
        assertEquals(42, item.productItemId)
        val input = SubmitInspectionResultInput(item.productItemId, BigDecimal("5.00"), "PASS", "")
        val payload = JsonParser.parseString(gson.toJson(input)).asJsonObject
        assertEquals(42, payload.get("product_item_id").asInt)
        assertFalse(payload.has("item_id"))
    }

    @Test
    fun validate_rejects_missing_result_for_required_item() {
        val message = InspectionDraftValidator.validate(
            items = listOf(
                InspectionItemDisplayModel(
                    itemId = 1,
                    itemName = "電壓",
                    method = "Multimeter",
                    unit = "V",
                    standardMin = BigDecimal("4.90"),
                    standardMax = BigDecimal("5.10"),
                    isRequired = true,
                )
            ),
            drafts = mapOf(1 to InspectionResultDraft(itemId = 1))
        )

        assertEquals("請先選擇 電壓 的檢驗結果。", message)
    }

    @Test
    fun validate_accepts_complete_draft() {
        val message = InspectionDraftValidator.validate(
            items = listOf(
                InspectionItemDisplayModel(
                    itemId = 1,
                    itemName = "電壓",
                    method = "Multimeter",
                    unit = "V",
                    standardMin = BigDecimal("4.90"),
                    standardMax = BigDecimal("5.10"),
                    isRequired = true,
                )
            ),
            drafts = mapOf(
                1 to InspectionResultDraft(itemId = 1, measuredValue = "5.00", result = "PASS")
            )
        )

        assertNull(message)
    }

    private fun dimension(required: Boolean = true) = InspectionItemDisplayModel(
        itemId = 42, itemName = "Length", method = "Caliper", unit = "mm",
        standardMin = BigDecimal("4.90"), standardMax = BigDecimal("5.10"), isRequired = required,
    )

    @Test
    fun validate_rejects_out_of_range_pass_missing_value_and_required_na() {
        listOf(
            InspectionResultDraft(42, "5.11", "PASS"),
            InspectionResultDraft(42, "4.89", "PASS"),
            InspectionResultDraft(42, "", "FAIL"),
            InspectionResultDraft(42, "", "NA"),
            InspectionResultDraft(42, "5.001", "PASS"),
        ).forEach { draft ->
            org.junit.Assert.assertNotNull(InspectionDraftValidator.validate(listOf(dimension()), mapOf(42 to draft)))
        }
    }

    @Test
    fun validate_accepts_boundary_and_out_of_range_fail() {
        listOf(
            InspectionResultDraft(42, "4.90", "PASS"),
            InspectionResultDraft(42, "5.10", "PASS"),
            InspectionResultDraft(42, "5.11", "FAIL"),
        ).forEach { draft ->
            assertNull(InspectionDraftValidator.validate(listOf(dimension()), mapOf(42 to draft)))
        }
    }

    @Test
    fun validate_allows_omitted_optional_items_but_rejects_empty_inspection() {
        val optional = dimension(false).copy(itemId = 43)
        assertNull(InspectionDraftValidator.validate(
            listOf(dimension(), optional), mapOf(42 to InspectionResultDraft(42, "5.00", "PASS")),
        ))
        org.junit.Assert.assertNotNull(InspectionDraftValidator.validate(emptyList(), emptyMap()))
        org.junit.Assert.assertNotNull(InspectionDraftValidator.validate(listOf(optional), mapOf(43 to InspectionResultDraft(43, "", "NA"))))
    }
}
