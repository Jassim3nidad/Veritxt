package ph.smishguard

import android.Manifest
import android.content.Intent
import androidx.core.net.toUri
import androidx.compose.ui.semantics.heading
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.LocalSaveableStateRegistry
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import ph.smishguard.model.ResultCopy
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import kotlinx.coroutines.launch
import ph.smishguard.data.Preferences
import ph.smishguard.model.Detection
import ph.smishguard.privacy.Brand
import ph.smishguard.privacy.City
import ph.smishguard.privacy.ReportPayload
import ph.smishguard.sms.PermissionState

class MainActivity : ComponentActivity() {
    private val vm: CheckViewModel by viewModels()
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        enableEdgeToEdge()
        consumeShare(intent)
        setContent {
            SmishGuardTheme {
                // No Compose saveable state, including text field state, enters activity bundles.
                CompositionLocalProvider(LocalSaveableStateRegistry provides null) {
                    SmishGuardUi(application as SmishGuardApp, vm)
                }
            }
        }
    }
    override fun onNewIntent(intent: Intent) { super.onNewIntent(intent); consumeShare(intent) }
    private fun consumeShare(incoming: Intent) {
        if (incoming.action == Intent.ACTION_SEND && incoming.type == "text/plain") {
            val text = incoming.getCharSequenceExtra(Intent.EXTRA_TEXT)?.toString()
            incoming.removeExtra(Intent.EXTRA_TEXT)
            incoming.clipData = null
            incoming.replaceExtras(null as Bundle?)
            // Keep routing identity stable; discard the payload rather than replace the
            // launch intent. Android lifecycle observers match action/type/categories.
            incoming.setDataAndType(null, "text/plain")
            if (text != null) vm.share(text)
        }
    }
    override fun onStop() { vm.endSession(); super.onStop() }
    override fun onSaveInstanceState(outState: Bundle) { super.onSaveInstanceState(outState); outState.clear() }
}

@Composable
private fun SmishGuardUi(app: SmishGuardApp, vm: CheckViewModel) {
    val state by vm.state.collectAsStateWithLifecycle()
    val preferences by app.preferences.flow.collectAsStateWithLifecycle(initialValue = null)
    val scope = rememberCoroutineScope()
    val scroll = rememberScrollState()
    LaunchedEffect(state.screen, state.result, preferences?.onboarded) { scroll.scrollTo(0) }
    var permissions by remember { mutableStateOf(PermissionState.read(app)) }
    val owner = LocalLifecycleOwner.current
    DisposableEffect(owner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) permissions = PermissionState.read(app)
        }
        owner.lifecycle.addObserver(observer)
        onDispose { owner.lifecycle.removeObserver(observer) }
    }
    BackHandler(state.screen != Screen.HOME) { vm.endSession() }
    Scaffold(bottomBar = {
        if (preferences?.onboarded == true) NavigationBar(containerColor = MaterialTheme.colorScheme.surface, modifier = Modifier.navigationDivider()) {
            listOf(Screen.HOME to "Home", Screen.CHECK to "Check", Screen.SETTINGS to "Settings").forEach { (screen, label) ->
                NavigationBarItem(selected = state.screen == screen || (screen == Screen.CHECK && state.screen == Screen.RESULT), onClick = { vm.navigate(screen) },
                    icon = { NavGlyph(screen) }, label = { Text(label) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = MaterialTheme.colorScheme.onSurface,
                        selectedTextColor = MaterialTheme.colorScheme.onSurface,
                        unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                        unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant,
                        indicatorColor = MaterialTheme.colorScheme.surfaceContainer))
            }
        }
    }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).imePadding().verticalScroll(scroll).padding(horizontal = 24.dp, vertical = 24.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp)) {
            Text("SmishGuard", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold)
            when {
                preferences == null -> CircularProgressIndicator()
                preferences?.onboarded != true -> {
                    Heading("A moment to check.\nA little more clarity.")
                    Text("Check SMS messages for potential financial-institution impersonation in Filipino, English, and Taglish.")
                    InfoSection("Your message stays here", "Processing happens on this phone. Message text is not stored or sent. Leaving the app clears your checking session.")
                    InfoSection("A warning tool", "SmishGuard never blocks, deletes, sends, or changes SMS. It does not replace your messaging app. Checks can miss scams or flag legitimate messages.")
                    Text(if (state.modelStatus.startsWith("Loading")) "Loading model status. Please wait before checking." else if (state.modelStatus.startsWith("Experimental")) "Experimental model for manual development testing. Research performance is unverified; automatic warnings and reporting are disabled." else "This build has no usable model. It cannot currently assess whether a message is suspicious.")
                    Text("Incoming SMS scanning is optional and off by default. No permission is needed to paste or share text. RCS and other messaging services are not monitored.")
                    PrimaryAction(onClick = { scope.launch { app.preferences.onboard() } }, Modifier.fillMaxWidth()) { Text("Continue without permissions") }
                }
                else -> when (state.screen) {
                    Screen.HOME -> {
                        Heading("Before you tap,\ncheck the message.")
                        Text("A private space to pause and review a financial SMS.", style = MaterialTheme.typography.bodyLarge)
                        PrimaryAction(onClick = { vm.navigate(Screen.CHECK) }, Modifier.fillMaxWidth().heightIn(min = 52.dp)) { Text("Check a message") }
                        InfoSection("Automatic warnings disabled", "Reporting is also disabled. Use manual checks to review a message.")
                        InfoSection(if (state.modelStatus == "Model not installed") "Model unavailable" else state.modelStatus, if (state.modelStatus.startsWith("Experimental")) "Manual offline testing only. Scores are uncalibrated and performance is unverified." else if (state.modelStatus.startsWith("Model ready")) "Checks run entirely on this phone." else "No assessment is available until a compatible trained model is included.")
                        Text("No SMS permission is needed to paste or share.", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text("Never share an OTP, PIN, or password. Verify requests using your bank’s official app or a number you already trust.")
                        Text("Research prototype · On-device processing", style = MaterialTheme.typography.labelMedium)
                    }
                    Screen.CHECK, Screen.RESULT -> {
                        val result = state.result
                        if (result == null) {
                            Heading("Test a message")
                            Text("Paste or share an SMS to review it privately.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                            OutlinedTextField(value = state.text, onValueChange = vm::edit, modifier = Modifier.fillMaxWidth(),
                                shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedBorderColor = MaterialTheme.colorScheme.primary,
                                    unfocusedBorderColor = MaterialTheme.colorScheme.outline,
                                    unfocusedContainerColor = MaterialTheme.colorScheme.surfaceContainer,
                                    focusedContainerColor = MaterialTheme.colorScheme.surfaceContainer),
                                label = { Text("SMS message") }, placeholder = { Text("Paste your message here") },
                                minLines = 6, maxLines = 10, enabled = !state.busy,
                                keyboardOptions = KeyboardOptions(autoCorrectEnabled = false, keyboardType = KeyboardType.Password),
                                supportingText = { Text("${state.text.length} / 10,000 characters") })
                            state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                            val keyboard = LocalSoftwareKeyboardController.current
                            PrimaryAction(onClick = { keyboard?.hide(); vm.scan() }, enabled = !state.busy, modifier = Modifier.fillMaxWidth()) {
                                if (state.busy) { CircularProgressIndicator(Modifier.size(20.dp), color = MaterialTheme.colorScheme.onPrimary); Spacer(Modifier.width(12.dp)) }
                                Text(if (state.busy) "Checking on your phone..." else "Check message")
                            }
                            Text("Text is cleared after checking. Automatic warnings and reporting are off.",
                                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            if (state.text.isNotEmpty()) TextButton(onClick = { vm.edit("") }) { Text("Clear message") }
                        } else {
                            Text("Check result", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            CompactResult(result) { vm.navigate(Screen.REPORT) }
                            PrimaryAction(onClick = { vm.edit("") }, modifier = Modifier.fillMaxWidth()) { Text("Check another message") }
                        }
                    }
                    Screen.REPORT -> {
                        Heading("Your choice to report")
                        Text("Only the metadata below would be sent. Reporting never includes your message or phone number.")
                        var brand by remember { mutableStateOf(Brand.UNSPECIFIED) }
                        Choice("Impersonated brand (optional)", Brand.entries, brand, { it.label }) { brand = it }
                        val result = state.result as? Detection.Success
                        val payload = if (result != null && state.checkedAt != null) ReportPayload.create(state.domain, result, state.checkedAt!!, preferences!!.city, brand) else null
                        if (payload != null) InfoSection("Exact metadata preview", payload.json())
                        else InfoSection("No report can be prepared", "An approved model result and a manually selected city would be required. Experimental, synthetic and unavailable results cannot be reported.")
                        InfoSection("Reporting unavailable", "No reporting endpoint is configured in this build. Nothing will be sent or queued. Offline checks do not depend on this service.")
                        PrimaryAction(onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth()) { Text("Submit report · unavailable") }
                        Text("Future city dashboards will summarize voluntary reports; their counts cannot measure total citywide scam prevalence.")
                    }
                    Screen.SETTINGS -> SettingsContent(app, preferences!!, permissions, { permissions = PermissionState.read(app) }, { vm.endSession() })
                }
            }
        }
    }
}


@Composable private fun CompactResult(result: Detection, report: () -> Unit) {
    var explain by remember(result) { mutableStateOf(false) }
    Column(Modifier.fillMaxWidth().semantics { liveRegion = LiveRegionMode.Polite }, verticalArrangement = Arrangement.spacedBy(16.dp)) {
        when (result) {
            is Detection.Success -> if (result.synthetic) {
                Heading("Synthetic interface fixture")
                Text("Software test only; no assessment.")
            } else {
                Heading(ResultCopy.heading(result))
                Text(ResultCopy.score(result.score), style = MaterialTheme.typography.titleLarge)
                Text(ResultCopy.DISCLAIMER, style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Detection.UnableToAssess -> {
                Heading("Unable to assess")
                Text("Enter an SMS message with meaningful text.")
            }
            Detection.Unavailable, Detection.InvalidModel -> {
                Heading("Model unavailable")
                Text(if (result == Detection.InvalidModel) "The bundled model is invalid or unsupported. No prediction was made."
                    else "No usable model is bundled. No prediction was made.")
            }
            Detection.Failure -> {
                Heading("Could not complete the check")
                Text("No prediction was made. Try checking the message again.")
            }
        }
    }
    TextButton(onClick = { explain = true }, modifier = Modifier.heightIn(min = 48.dp)) { Text("What does this mean?") }
    if (explain) AlertDialog(onDismissRequest = { explain = false },
        title = { Text("About this result") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("The score is experimental, not a verified probability or chance of fraud. Research performance is unverified. Likely phishing means the model score is strictly above the unchanged 50% threshold. No phishing detected does not establish that a message is safe.")
                Text("Unable to assess means there is no usable model word outside links or numbers, or the input is blank or obvious keyboard mashing. It can also occur for meaningful words this model does not know. Short messages are allowed; no minimum word count is required.")
                Text("Verify suspicious requests through an official app, a website entered independently, or a phone number you already know. Never share an OTP, PIN, or password. Do not rely on contact details in the message.")
                Text("Automatic warnings and reporting are disabled.")
                Text("Message text is cleared after checking and when you leave the app. No scan history is saved.")
                TextButton(onClick = { explain = false; report() }) { Text("Review reporting options") }
            }
        },
        confirmButton = { TextButton(onClick = { explain = false }) { Text("Close") } })
}

@Composable private fun SettingsContent(app: SmishGuardApp, preferences: Preferences, permissions: PermissionState, refresh: () -> Unit, clear: () -> Unit) {
    val scope = rememberCoroutineScope()
    var consentDialog by remember { mutableStateOf(false) }
    var clearDialog by remember { mutableStateOf(false) }
    var notice by remember { mutableStateOf<String?>(null) }
    val smsRequest = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        scope.launch { app.preferences.scanning(granted) }
        notice = if (granted) "SMS permission granted. Automatic model-driven warnings remain disabled in this development build." else "SMS permission was not granted. Use paste or share, or review Android app settings."
        refresh()
    }
    val notificationRequest = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { refresh() }
    Heading("Privacy & settings")
    InfoSection("Automatic protection & reporting - off", "This build supports manual testing only. Permission choices below do not enable automatic model warnings or reporting.")
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text("Scan incoming SMS", Modifier.weight(1f).padding(top = 12.dp))
        Switch(checked = preferences.scanning && permissions.active(true), onCheckedChange = {
            if (it) consentDialog = true else scope.launch { app.preferences.scanning(false) }
        }, enabled = permissions.telephony, modifier = Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp)
            .semantics { contentDescription = "Scan incoming SMS" })
    }
    Text("Telephony: ${if (permissions.telephony) "available" else "unavailable"}\nSMS permission: ${if (permissions.sms) "granted" else "not granted"}\nNotifications: ${if (permissions.notifications) "enabled" else "disabled"}")
    notice?.let { Text(it) }
    if (!permissions.notifications) SecondaryAction(onClick = {
        if (Build.VERSION.SDK_INT >= 33 && androidx.core.content.ContextCompat.checkSelfPermission(app,
                Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED)
            notificationRequest.launch(Manifest.permission.POST_NOTIFICATIONS)
        else app.startActivity(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, app.packageName).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }) { Text("Enable warning notifications") }
    TextButton(onClick = { app.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, "package:${app.packageName}".toUri()).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }) { Text("Open Android permission settings") }
    Choice("Your city · selected manually", City.entries, preferences.city, { it.label }) { city -> scope.launch { app.preferences.city(city) } }
    InfoSection("Local processing", "Only onboarding, incoming-SMS consent, and your selected city are saved. No scan history or raw message records are kept. Reports are not queued. The app has no internet permission.")
    InfoSection("Know the limits", "Android treats SMS access as a restricted permission. Your installer and device may prevent it, even for a directly installed APK. Force-stopping the app prevents automatic scanning until you open it again. Battery policies and certain protected SMS may also limit delivery. Notifications must be enabled for warnings.")
    SecondaryAction(onClick = { clearDialog = true }, Modifier.fillMaxWidth()) { Text("Clear local preferences and session") }
    if (consentDialog) AlertDialog(onDismissRequest = { consentDialog = false }, title = { Text("Allow incoming SMS checks?") },
        text = { Text("SmishGuard will receive new SMS text to check locally, then discard it. It will not read your inbox or change messages. Automatic checks and warnings are disabled until a model is approved for that use. Use manual paste/share for experimental testing. Android may refuse this restricted permission. Notifications are a separate choice.") },
        confirmButton = { TextButton(onClick = {
            consentDialog = false
            if (permissions.sms) scope.launch { app.preferences.scanning(true) } else smsRequest.launch(Manifest.permission.RECEIVE_SMS)
        }) { Text("Agree and continue") } }, dismissButton = { TextButton(onClick = { consentDialog = false }) { Text("Keep off") } })
    if (clearDialog) AlertDialog(onDismissRequest = { clearDialog = false }, title = { Text("Clear local records?") },
        text = { Text("This clears your city, consent preferences, and current checking session. Incoming scanning turns off. Android permissions remain under system settings.") },
        confirmButton = { TextButton(onClick = { clearDialog = false; scope.launch { app.preferences.clear(); clear() } }) { Text("Clear") } },
        dismissButton = { TextButton(onClick = { clearDialog = false }) { Text("Cancel") } })
}

@Composable private fun Heading(text: String) { Text(text, modifier = Modifier.semantics { heading() }, style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.SemiBold) }
@Composable private fun InfoSection(title: String, body: String) {
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        Spacer(Modifier.height(4.dp))
        Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        Text(body, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
@Composable private fun <T> Choice(label: String, choices: List<T>, selected: T, display: (T) -> String, change: (T) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Column {
        Text(label, style = MaterialTheme.typography.labelLarge)
        Box {
            SecondaryAction(onClick = { expanded = true }, Modifier.fillMaxWidth()) { Text(display(selected)) }
            DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                choices.forEach { choice -> DropdownMenuItem(text = { Text(display(choice)) }, onClick = { expanded = false; change(choice) }) }
            }
        }
    }
}
