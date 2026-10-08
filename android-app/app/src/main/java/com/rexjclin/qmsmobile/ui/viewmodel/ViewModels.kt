package com.rexjclin.qmsmobile.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.rexjclin.qmsmobile.data.QmsRepository
import com.rexjclin.qmsmobile.model.AuthSessionState
import com.rexjclin.qmsmobile.model.InspectionBatchItem
import com.rexjclin.qmsmobile.model.InspectionItemDisplayModel
import com.rexjclin.qmsmobile.model.InspectionResultDraft
import com.rexjclin.qmsmobile.model.LoginState
import com.rexjclin.qmsmobile.model.SubmitInspectionResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class PendingBatchesUiState(
    val isLoading: Boolean = true,
    val batches: List<InspectionBatchItem> = emptyList(),
    val errorMessage: String? = null,
)

data class InspectionItemsUiState(
    val isLoading: Boolean = true,
    val items: List<InspectionItemDisplayModel> = emptyList(),
    val errorMessage: String? = null,
)

data class SubmitInspectionUiState(
    val isLoading: Boolean = true,
    val isSubmitting: Boolean = false,
    val items: List<InspectionItemDisplayModel> = emptyList(),
    val drafts: Map<Int, InspectionResultDraft> = emptyMap(),
    val batchRemark: String = "",
    val errorMessage: String? = null,
    val successMessage: String? = null,
    val lastSubmission: SubmitInspectionResponse? = null,
)

class SessionViewModel(private val repository: QmsRepository) : ViewModel() {
    val sessionState: StateFlow<AuthSessionState> = repository.sessionFlow
        .map { session -> if (session.authToken.isNullOrBlank()) AuthSessionState.LoggedOut else AuthSessionState.LoggedIn }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), AuthSessionState.Loading)

    fun logout() {
        viewModelScope.launch { repository.logout() }
    }
}

class LoginViewModel(private val repository: QmsRepository) : ViewModel() {
    private val _state = MutableStateFlow(LoginState())
    val state: StateFlow<LoginState> = _state.asStateFlow()

    fun updateUsername(value: String) = _state.update { it.copy(username = value, errorMessage = null) }

    fun updatePassword(value: String) = _state.update { it.copy(password = value, errorMessage = null) }

    fun login() {
        val snapshot = _state.value
        if (snapshot.username.isBlank() || snapshot.password.isBlank()) {
            _state.update { it.copy(errorMessage = "請輸入帳號與密碼。") }
            return
        }
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, errorMessage = null) }
            runCatching { repository.login(snapshot.username.trim(), snapshot.password) }
                .onSuccess { _state.update { it.copy(isLoading = false) } }
                .onFailure { error ->
                    _state.update {
                        it.copy(isLoading = false, errorMessage = error.message ?: "登入失敗。")
                    }
                }
        }
    }
}

class PendingBatchesViewModel(private val repository: QmsRepository) : ViewModel() {
    private val _state = MutableStateFlow(PendingBatchesUiState())
    val state: StateFlow<PendingBatchesUiState> = _state.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, errorMessage = null) }
            runCatching { repository.getPendingBatches() }
                .onSuccess { batches ->
                    _state.value = PendingBatchesUiState(isLoading = false, batches = batches)
                }
                .onFailure { error ->
                    _state.value = PendingBatchesUiState(
                        isLoading = false,
                        errorMessage = error.message ?: "載入待檢驗批次失敗。",
                    )
                }
        }
    }
}

class InspectionItemsViewModel(
    private val repository: QmsRepository,
    private val productId: Int,
) : ViewModel() {
    private val _state = MutableStateFlow(InspectionItemsUiState())
    val state: StateFlow<InspectionItemsUiState> = _state.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, errorMessage = null) }
            runCatching { repository.getInspectionItems(productId) }
                .onSuccess { items ->
                    _state.value = InspectionItemsUiState(isLoading = false, items = items)
                }
                .onFailure { error ->
                    _state.value = InspectionItemsUiState(
                        isLoading = false,
                        errorMessage = error.message ?: "載入檢驗項目失敗。",
                    )
                }
        }
    }
}

class InspectionSubmitViewModel(
    private val repository: QmsRepository,
    private val batchId: Int,
    private val productId: Int,
) : ViewModel() {
    private val _state = MutableStateFlow(SubmitInspectionUiState())
    val state: StateFlow<SubmitInspectionUiState> = _state.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, errorMessage = null, successMessage = null) }
            runCatching { repository.getInspectionItems(productId) }
                .onSuccess { items ->
                    val drafts = items.associate { item ->
                        item.itemId to (_state.value.drafts[item.itemId] ?: InspectionResultDraft(itemId = item.itemId))
                    }
                    _state.value = _state.value.copy(
                        isLoading = false,
                        items = items,
                        drafts = drafts,
                        errorMessage = null,
                    )
                }
                .onFailure { error ->
                    _state.value = _state.value.copy(
                        isLoading = false,
                        errorMessage = error.message ?: "載入檢驗項目失敗。",
                    )
                }
        }
    }

    fun updateMeasuredValue(itemId: Int, value: String) {
        _state.update { state ->
            state.copy(
                drafts = state.drafts + (itemId to state.drafts.getValue(itemId).copy(measuredValue = value)),
                errorMessage = null,
            )
        }
    }

    fun updateResult(itemId: Int, result: String) {
        _state.update { state ->
            state.copy(
                drafts = state.drafts + (itemId to state.drafts.getValue(itemId).copy(result = result)),
                errorMessage = null,
            )
        }
    }

    fun updateRemark(itemId: Int, remark: String) {
        _state.update { state ->
            state.copy(
                drafts = state.drafts + (itemId to state.drafts.getValue(itemId).copy(remark = remark)),
            )
        }
    }

    fun updateBatchRemark(remark: String) {
        _state.update { it.copy(batchRemark = remark) }
    }

    fun submit() {
        val snapshot = _state.value
        viewModelScope.launch {
            _state.update { it.copy(isSubmitting = true, errorMessage = null, successMessage = null) }
            runCatching {
                repository.submitInspection(batchId, snapshot.batchRemark, snapshot.items, snapshot.drafts)
            }.onSuccess { response ->
                _state.update {
                    it.copy(
                        isSubmitting = false,
                        successMessage = "送出成功：${response.overall_result}",
                        lastSubmission = response,
                    )
                }
            }.onFailure { error ->
                _state.update {
                    it.copy(
                        isSubmitting = false,
                        errorMessage = error.message ?: "送出失敗。",
                    )
                }
            }
        }
    }
}
