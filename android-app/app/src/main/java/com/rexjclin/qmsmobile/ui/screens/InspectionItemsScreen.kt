package com.rexjclin.qmsmobile.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Card
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ElevatedButton
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.rexjclin.qmsmobile.model.InspectionItemDisplayModel
import com.rexjclin.qmsmobile.ui.viewmodel.InspectionItemsViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InspectionItemsScreen(
    batchId: Int,
    viewModel: InspectionItemsViewModel,
    onBack: () -> Unit,
    onStartInspection: () -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("檢驗項目 / 批次 #$batchId") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                    }
                },
                actions = {
                    IconButton(onClick = viewModel::refresh) {
                        Icon(Icons.Default.Refresh, contentDescription = "刷新")
                    }
                },
            )
        },
        floatingActionButton = {
            if (!state.isLoading && state.items.isNotEmpty()) {
                FloatingActionButton(onClick = onStartInspection) {
                    Icon(Icons.Default.PlayArrow, contentDescription = "開始填寫")
                }
            }
        },
    ) { paddingValues ->
        when {
            state.isLoading -> LoadingScreen(modifier = Modifier.padding(paddingValues))
            state.errorMessage != null -> ErrorScreen(
                message = state.errorMessage ?: "讀取失敗",
                modifier = Modifier.padding(paddingValues),
            )
            state.items.isEmpty() -> EmptyScreen(
                message = "此產品尚未設定檢驗項目。",
                modifier = Modifier.padding(paddingValues),
            )
            else -> LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                items(state.items, key = { it.itemId }) { item ->
                    InspectionItemCard(item = item)
                }
                item {
                    ElevatedButton(
                        onClick = onStartInspection,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 8.dp),
                    ) {
                        Text("進入檢驗結果填寫")
                    }
                }
            }
        }
    }
}

@Composable
private fun InspectionItemCard(item: InspectionItemDisplayModel) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(item.itemName, style = MaterialTheme.typography.titleMedium)
            Text("方法：${item.method.ifBlank { "未設定" }}")
            Text("規格：${item.specLabel}")
            Text(if (item.isRequired) "必填項目" else "選填項目", color = MaterialTheme.colorScheme.primary)
        }
    }
}
