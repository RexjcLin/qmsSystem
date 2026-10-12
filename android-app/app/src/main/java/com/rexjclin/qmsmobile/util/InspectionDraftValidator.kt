package com.rexjclin.qmsmobile.util

import com.rexjclin.qmsmobile.model.InspectionItemDisplayModel
import com.rexjclin.qmsmobile.model.InspectionResultDraft
import java.math.BigDecimal

object InspectionDraftValidator {
    fun validate(
        items: List<InspectionItemDisplayModel>,
        drafts: Map<Int, InspectionResultDraft>,
    ): String? {
        if (items.isEmpty()) return "此產品尚未設定檢驗項目。"
        items.forEach { item ->
            val draft = drafts[item.itemId]
            if (draft == null) {
                if (item.isRequired) return "缺少 ${item.itemName} 的檢驗資料。"
                return@forEach
            }
            if (draft.result.isNullOrBlank()) {
                if (item.isRequired || draft.measuredValue.isNotBlank() || draft.remark.isNotBlank()) {
                    return "請先選擇 ${item.itemName} 的檢驗結果。"
                }
                return@forEach
            }
            if (draft.result !in setOf("PASS", "FAIL", "NA")) return "${item.itemName} 的檢驗結果不正確。"
            if (item.isRequired && draft.result == "NA") return "${item.itemName} 是必填項目，不可標記為 NA。"
            val value = toBigDecimalOrNull(draft.measuredValue)
            if (draft.measuredValue.isNotBlank() && value == null) return "${item.itemName} 的量測值格式不正確。"
            if (value != null && (value.scale() > 2 || value.abs() >= BigDecimal("100000000"))) {
                return "${item.itemName} 的量測值最多 8 位整數、2 位小數。"
            }
            if (draft.result != "NA" && (item.standardMin != null || item.standardMax != null)) {
                if (value == null) return "${item.itemName} 必須輸入量測值。"
                val outOfRange = (item.standardMin != null && value < item.standardMin) ||
                    (item.standardMax != null && value > item.standardMax)
                if (outOfRange && draft.result == "PASS") return "${item.itemName} 的量測值超出規格，不可標記為 PASS。"
            }
        }
        if (items.none { drafts[it.itemId]?.result in setOf("PASS", "FAIL") }) {
            return "至少需要一項有效的檢驗結果。"
        }
        return null
    }

    fun toBigDecimalOrNull(value: String): BigDecimal? = value.toBigDecimalOrNull()
}
