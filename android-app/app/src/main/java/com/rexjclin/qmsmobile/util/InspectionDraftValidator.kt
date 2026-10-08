package com.rexjclin.qmsmobile.util

import com.rexjclin.qmsmobile.model.InspectionItemDisplayModel
import com.rexjclin.qmsmobile.model.InspectionResultDraft
import java.math.BigDecimal

object InspectionDraftValidator {
    fun validate(
        items: List<InspectionItemDisplayModel>,
        drafts: Map<Int, InspectionResultDraft>,
    ): String? {
        items.forEach { item ->
            val draft = drafts[item.itemId] ?: return "缺少 ${item.itemName} 的檢驗資料。"
            if (item.isRequired && draft.result.isNullOrBlank()) {
                return "請先選擇 ${item.itemName} 的檢驗結果。"
            }
            if (draft.measuredValue.isNotBlank()) {
                draft.measuredValue.toBigDecimalOrNull() ?: return "${item.itemName} 的量測值格式不正確。"
            }
            if ((item.standardMin != null || item.standardMax != null) && draft.result == "PASS" && draft.measuredValue.isBlank()) {
                return "${item.itemName} 需要輸入量測值才能標記為 PASS。"
            }
        }
        return null
    }

    fun toBigDecimalOrNull(value: String): BigDecimal? = value.toBigDecimalOrNull()
}
