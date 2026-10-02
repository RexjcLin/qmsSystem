package com.rexjclin.qmsmobile.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import androidx.navigation.NavGraph.Companion.findStartDestination
import com.rexjclin.qmsmobile.QmsApplication
import com.rexjclin.qmsmobile.model.AuthSessionState
import com.rexjclin.qmsmobile.ui.navigation.QmsRoute
import com.rexjclin.qmsmobile.ui.screens.InspectionItemsScreen
import com.rexjclin.qmsmobile.ui.screens.LoginScreen
import com.rexjclin.qmsmobile.ui.screens.PendingBatchesScreen
import com.rexjclin.qmsmobile.ui.screens.SubmitInspectionScreen
import com.rexjclin.qmsmobile.ui.viewmodel.InspectionItemsViewModel
import com.rexjclin.qmsmobile.ui.viewmodel.InspectionSubmitViewModel
import com.rexjclin.qmsmobile.ui.viewmodel.LoginViewModel
import com.rexjclin.qmsmobile.ui.viewmodel.PendingBatchesViewModel
import com.rexjclin.qmsmobile.ui.viewmodel.SessionViewModel

@Composable
fun QmsMobileApp() {
    val app = LocalContext.current.applicationContext as QmsApplication
    val navController = rememberNavController()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val sessionViewModel: SessionViewModel = viewModel(
        factory = remember(app) {
            viewModelFactory {
                initializer { SessionViewModel(app.container.repository) }
            }
        }
    )
    val sessionState by sessionViewModel.sessionState.collectAsState()

    LaunchedEffect(sessionState, backStackEntry?.destination?.route) {
        when (sessionState) {
            AuthSessionState.Loading -> if (backStackEntry?.destination?.route != QmsRoute.Splash.route) {
                navController.navigate(QmsRoute.Splash.route)
            }
            AuthSessionState.LoggedOut -> if (backStackEntry?.destination?.route != QmsRoute.Login.route) {
                navController.navigate(QmsRoute.Login.route) {
                    popUpTo(navController.graph.findStartDestination().id) { inclusive = true }
                    launchSingleTop = true
                }
            }
            AuthSessionState.LoggedIn -> if (backStackEntry?.destination?.route in setOf(QmsRoute.Splash.route, QmsRoute.Login.route)) {
                navController.navigate(QmsRoute.PendingBatches.route) {
                    popUpTo(navController.graph.findStartDestination().id) { inclusive = true }
                    launchSingleTop = true
                }
            }
        }
    }

    Scaffold { paddingValues ->
        NavHost(
            navController = navController,
            startDestination = QmsRoute.Splash.route,
            modifier = Modifier.padding(paddingValues),
        ) {
            composable(QmsRoute.Splash.route) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }
            composable(QmsRoute.Login.route) {
                val viewModel: LoginViewModel = viewModel(
                    factory = remember(app) {
                        viewModelFactory { initializer { LoginViewModel(app.container.repository) } }
                    }
                )
                LoginScreen(viewModel)
            }
            composable(QmsRoute.PendingBatches.route) {
                val viewModel: PendingBatchesViewModel = viewModel(
                    factory = remember(app) {
                        viewModelFactory { initializer { PendingBatchesViewModel(app.container.repository) } }
                    }
                )
                PendingBatchesScreen(
                    viewModel = viewModel,
                    onLogout = sessionViewModel::logout,
                    onBatchSelected = { batch ->
                        navController.navigate(QmsRoute.InspectionItems.create(batch.id, batch.productId))
                    },
                )
            }
            composable(
                route = QmsRoute.InspectionItems.route,
                arguments = listOf(
                    navArgument("batchId") { type = NavType.IntType },
                    navArgument("productId") { type = NavType.IntType },
                ),
            ) { entry ->
                val batchId = entry.arguments?.getInt("batchId") ?: 0
                val productId = entry.arguments?.getInt("productId") ?: 0
                val viewModel: InspectionItemsViewModel = viewModel(
                    key = "inspection-items-$batchId-$productId",
                    factory = remember(app, batchId, productId) {
                        viewModelFactory {
                            initializer { InspectionItemsViewModel(app.container.repository, productId) }
                        }
                    }
                )
                InspectionItemsScreen(
                    batchId = batchId,
                    viewModel = viewModel,
                    onBack = { navController.popBackStack() },
                    onStartInspection = {
                        navController.navigate(QmsRoute.SubmitInspection.create(batchId, productId))
                    },
                )
            }
            composable(
                route = QmsRoute.SubmitInspection.route,
                arguments = listOf(
                    navArgument("batchId") { type = NavType.IntType },
                    navArgument("productId") { type = NavType.IntType },
                ),
            ) { entry ->
                val batchId = entry.arguments?.getInt("batchId") ?: 0
                val productId = entry.arguments?.getInt("productId") ?: 0
                val viewModel: InspectionSubmitViewModel = viewModel(
                    key = "submit-inspection-$batchId-$productId",
                    factory = remember(app, batchId, productId) {
                        viewModelFactory {
                            initializer { InspectionSubmitViewModel(app.container.repository, batchId, productId) }
                        }
                    }
                )
                SubmitInspectionScreen(
                    batchId = batchId,
                    viewModel = viewModel,
                    onBack = { navController.popBackStack() },
                )
            }
        }
    }
}
