package com.rexjclin.qmsmobile.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.Button
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardOptions
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.rexjclin.qmsmobile.model.InspectionItemDisplayModel
import com.rexjclin.qmsmobile.model.InspectionResultDraft
import com.rexjclin.qmsmobile.ui.viewmodel.InspectionSubmitViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SubmitInspectionScreen(
    batchId: Int,
    viewModel: InspectionSubmitViewModel,
    onBack: () -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("檢驗結果填寫 / 批次 #$batchId") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                    }
                },
            )
        },
    ) { paddingValues ->
        when {
            state.isLoading -> LoadingScreen(modifier = Modifier.padding(paddingValues))
            state.errorMessage != null && state.items.isEmpty() -> ErrorScreen(
                message = state.errorMessage ?: "讀取失敗",
                modifier = Modifier.padding(paddingValues),
            )
            else -> LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                item {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("逐項輸入量測值與結果", style = MaterialTheme.typography.titleMedium)
                        state.errorMessage?.let {
                            Text(it, color = MaterialTheme.colorScheme.error)
                        }
                        state.successMessage?.let {
                            Text(it, color = MaterialTheme.colorScheme.primary)
                        }
                    }
                }
                items(state.items, key = { it.itemId }) { item ->
                    val draft = state.drafts[item.itemId] ?: InspectionResultDraft(itemId = item.itemId)
                    InspectionInputCard(
                        item = item,
                        draft = draft,
                        onMeasuredValueChange = { viewModel.updateMeasuredValue(item.itemId, it) },
                        onResultChange = { viewModel.updateResult(item.itemId, it) },
                        onRemarkChange = { viewModel.updateRemark(item.itemId, it) },
                    )
                }
                item {
                    OutlinedTextField(
                        value = state.batchRemark,
                        onValueChange = viewModel::updateBatchRemark,
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("整批備註") },
                        minLines = 3,
                    )
                }
                item {
                    Button(
                        onClick = viewModel::submit,
                        enabled = !state.isSubmitting,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(if (state.isSubmitting) "送出中..." else "送出檢驗結果")
                    }
                }
            }
        }
    }
}

@Composable
private fun InspectionInputCard(
    item: InspectionItemDisplayModel,
    draft: InspectionResultDraft,
    onMeasuredValueChange: (String) -> Unit,
    onResultChange: (String) -> Unit,
    onRemarkChange: (String) -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(item.itemName, style = MaterialTheme.typography.titleMedium)
            Text("方法：${item.method.ifBlank { "未設定" }}")
            Text("規格：${item.specLabel}")
            Text(if (item.isRequired) "必填項目" else "選填項目", color = MaterialTheme.colorScheme.primary)
            OutlinedTextField(
                value = draft.measuredValue,
                onValueChange = onMeasuredValueChange,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("量測值") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
            )
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("PASS", "FAIL", "NA").forEach { option ->
                    FilterChip(
                        selected = draft.result == option,
                        onClick = { onResultChange(option) },
                        label = { Text(option) },
                    )
                }
            }
            OutlinedTextField(
                value = draft.remark,
                onValueChange = onRemarkChange,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("備註") },
                minLines = 2,
            )
        }
    }
}
