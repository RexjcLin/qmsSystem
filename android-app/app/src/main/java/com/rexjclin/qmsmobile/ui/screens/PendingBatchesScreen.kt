package com.rexjclin.qmsmobile.ui.screens

import androidx.compose.material3.ExperimentalMaterial3Api

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ExitToApp
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Card
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.rexjclin.qmsmobile.model.InspectionBatchItem
import com.rexjclin.qmsmobile.ui.viewmodel.PendingBatchesViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PendingBatchesScreen(
    viewModel: PendingBatchesViewModel,
    onLogout: () -> Unit,
    onBatchSelected: (InspectionBatchItem) -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("待檢驗批次") },
                actions = {
                    IconButton(onClick = viewModel::refresh) {
                        Icon(Icons.Default.Refresh, contentDescription = "刷新")
                    }
                    IconButton(onClick = onLogout) {
                        Icon(Icons.Default.ExitToApp, contentDescription = "登出")
                    }
                },
            )
        },
    ) { paddingValues ->
        when {
            state.isLoading -> LoadingScreen(modifier = Modifier.padding(paddingValues))
            state.errorMessage != null -> ErrorScreen(
                message = state.errorMessage ?: "讀取失敗",
                modifier = Modifier.padding(paddingValues),
            )
            state.batches.isEmpty() -> EmptyScreen(
                message = "目前沒有待檢驗批次。",
                modifier = Modifier.padding(paddingValues),
            )
            else -> LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                items(state.batches, key = { it.id }) { batch ->
                    Card(modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onBatchSelected(batch) }) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(batch.code, style = MaterialTheme.typography.titleMedium)
                            Text(batch.productName, style = MaterialTheme.typography.bodyLarge)
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(top = 8.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Text("數量：${batch.quantity}")
                                Text("狀態：${batch.status}")
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
internal fun LoadingScreen(modifier: Modifier = Modifier) {
    Row(
        modifier = modifier.fillMaxSize(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Center,
    ) {
        CircularProgressIndicator()
    }
}

@Composable
internal fun ErrorScreen(message: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(message, color = MaterialTheme.colorScheme.error)
    }
}

@Composable
internal fun EmptyScreen(message: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(message)
    }
}
