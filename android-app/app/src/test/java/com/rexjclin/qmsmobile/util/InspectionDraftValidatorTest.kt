package com.rexjclin.qmsmobile.util

import com.rexjclin.qmsmobile.model.InspectionItemDisplayModel
import com.rexjclin.qmsmobile.model.InspectionResultDraft
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.math.BigDecimal

class InspectionDraftValidatorTest {
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
}
