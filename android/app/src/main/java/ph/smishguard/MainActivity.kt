package ph.smishguard

import android.Manifest
import android.content.ClipboardManager
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
import androidx.compose.animation.*
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.OpenInNew
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.LocalSaveableStateRegistry
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
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
import ph.smishguard.ui.*

class MainActivity : ComponentActivity() {
    private val vm: CheckViewModel by viewModels()
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        enableEdgeToEdge()
        consumeShare(intent)
        setContent {
            // No Compose saveable state, including text field state, enters activity bundles.
            CompositionLocalProvider(LocalSaveableStateRegistry provides null) {
                SmishGuardUi(application as SmishGuardApp, vm)
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

@Composable private fun SmishGuardTheme(solid: Boolean, content: @Composable () -> Unit) {
    val dark = isSystemInDarkTheme()
    val colors = if (dark) darkColorScheme(primary = Color(0xFF9BD4BE), onPrimary = Color(0xFF00382D), secondary = Color(0xFFBACBBF),
            background = Color(0xFF0E1613), surface = Color(0xFF0E1613), onSurface = Color(0xFFE3EAE5),
            onSurfaceVariant = Color(0xFFBFCAC3), surfaceContainer = Color(0xFF202B26), secondaryContainer = Color(0xFF344B40))
        else lightColorScheme(primary = Color(0xFF236B5E), secondary = Color(0xFF4E6358), background = Color(0xFFF2F6F3),
            surface = Color(0xFFF2F6F3), onSurface = Color(0xFF16201C), onSurfaceVariant = Color(0xFF3F4945),
            surfaceContainer = Color(0xFFEBF0E9), secondaryContainer = Color(0xFFD9EBDD))
    CompositionLocalProvider(LocalGlass provides GlassStyle(dark, solid)) {
        MaterialTheme(colorScheme = colors) {
            // Glass panels are not Material Surfaces, so set the default text colour explicitly for both themes.
            CompositionLocalProvider(LocalContentColor provides colors.onSurface, content = content)
        }
    }
}

@Composable
private fun SmishGuardUi(app: SmishGuardApp, vm: CheckViewModel) {
    val state by vm.state.collectAsStateWithLifecycle()
    val preferences by app.preferences.flow.collectAsStateWithLifecycle(initialValue = null)
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
    SmishGuardTheme(solid = preferences?.reduceTransparency == true) {
        Box(Modifier.fillMaxSize()) {
            GlassBackground()
            Scaffold(containerColor = Color.Transparent, contentColor = MaterialTheme.colorScheme.onSurface, bottomBar = {
                if (preferences?.onboarded == true) {
                    val tab = when (state.screen) { Screen.SETTINGS -> Screen.SETTINGS; Screen.HOME -> Screen.HOME; else -> Screen.CHECK }
                    GlassNavBar(listOf(NavItem(Screen.HOME, "Home", Icons.Outlined.Home), NavItem(Screen.CHECK, "Check", Icons.Outlined.Sms),
                        NavItem(Screen.SETTINGS, "Settings", Icons.Outlined.Settings)), tab, vm::navigate)
                }
            }) { padding ->
                val prefs = preferences
                when {
                    prefs == null -> Box(Modifier.fillMaxSize(), Alignment.Center) { CircularProgressIndicator() }
                    !prefs.onboarded -> Onboarding(app, state.modelStatus, Modifier.padding(padding))
                    // Content scrolls under the floating glass nav bar; only the top inset is reserved.
                    else -> AnimatedContent(state.screen, Modifier.padding(top = padding.calculateTopPadding()), label = "screen",
                        transitionSpec = { (fadeIn(tween(220)) + slideInVertically(spring(stiffness = 500f)) { it / 14 }) togetherWith fadeOut(tween(120)) }) { screen ->
                        Page(bottom = padding.calculateBottomPadding()) {
                            when (screen) {
                                Screen.HOME -> HomeScreen(state, prefs, permissions, app, vm)
                                Screen.CHECK -> CheckScreen(state, app, vm)
                                Screen.RESULT -> ResultScreen(state, vm)
                                Screen.REPORT -> ReportScreen(state, prefs, vm)
                                Screen.SETTINGS -> SettingsContent(app, prefs, permissions, { permissions = PermissionState.read(app) }, { vm.endSession() })
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable private fun Page(bottom: androidx.compose.ui.unit.Dp, content: @Composable ColumnScope.() -> Unit) {
    Column(Modifier.fillMaxSize().imePadding().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Image(painterResource(R.drawable.ic_veritxt_mark), null, Modifier.size(24.dp).clearAndSetSemantics { })
            Text(stringResource(R.string.app_name), style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
        }
        content()
        Spacer(Modifier.height(bottom + 8.dp))
    }
}

@Composable private fun Onboarding(app: SmishGuardApp, modelStatus: String, modifier: Modifier) {
    val scope = rememberCoroutineScope()
    val pages = listOf(
        Triple(Icons.Outlined.Shield, "Before you tap,\ncheck the message.", "Check SMS messages for possible scams in Filipino, English, and Taglish."),
        Triple(Icons.Outlined.Lock, "Your message stays here", "Checks happen on this phone. Message text is never stored or sent, and it's cleared when you leave the app."),
        Triple(Icons.Outlined.NotificationsNone, "A warning tool", "Veritxt never blocks, deletes, or changes your SMS. It can miss scams or flag real messages, so always double-check."))
    val pager = rememberPagerState { pages.size }
    Column(modifier.fillMaxSize().padding(20.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
        HorizontalPager(pager, Modifier.weight(1f)) { i ->
            val (icon, title, body) = pages[i]
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally) {
                GlassSurface(Modifier.fillMaxWidth(), padding = 28.dp) {
                    Box(Modifier.size(64.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary.copy(alpha = .14f)), Alignment.Center) {
                        Icon(icon, null, Modifier.size(32.dp), tint = MaterialTheme.colorScheme.primary)
                    }
                    Text(title, Modifier.semantics { heading() }, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
                    Text(body, style = MaterialTheme.typography.bodyLarge)
                    if (i == 2) Text(if (modelStatus.startsWith("Experimental")) "Experimental model: research performance is unverified. Automatic warnings and reporting are disabled."
                        else "This build has no usable model yet, so it can't assess messages.", style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
        // Scrollable so the actions stay reachable at large font sizes.
        Column(Modifier.verticalScroll(rememberScrollState()), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.clearAndSetSemantics { contentDescription = "Page ${pager.currentPage + 1} of ${pages.size}" }) {
            repeat(pages.size) { Box(Modifier.size(if (it == pager.currentPage) 22.dp else 8.dp, 8.dp).clip(CircleShape)
                .background(MaterialTheme.colorScheme.primary.copy(alpha = if (it == pager.currentPage) 1f else .3f))) }
        }
        Text("Paste or share works without any permissions. Incoming SMS scanning is optional and off.", style = MaterialTheme.typography.bodySmall,
            textAlign = TextAlign.Center, color = MaterialTheme.colorScheme.onSurfaceVariant)
        GlassButton("Continue without permissions", { scope.launch { app.preferences.onboard() } })
        }
    }
}

@Composable private fun Heading(text: String) { Text(text, modifier = Modifier.semantics { heading() }, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold) }

@Composable private fun ColumnScope.HomeScreen(state: CheckState, preferences: Preferences, permissions: PermissionState, app: SmishGuardApp, vm: CheckViewModel) {
    val scheme = MaterialTheme.colorScheme
    val dark = LocalGlass.current.dark
    Heading("Before you tap,\ncheck the message.")
    GlassSurface(Modifier.fillMaxWidth().clip(RoundedCornerShape(28.dp)).clickable { vm.navigate(Screen.CHECK) }, tint = scheme.primary, padding = 24.dp) {
        Box(Modifier.size(56.dp).clip(CircleShape).background(scheme.primary), Alignment.Center) {
            Icon(Icons.Outlined.ContentPasteSearch, null, Modifier.size(28.dp), tint = scheme.onPrimary)
        }
        Text("Check a message", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
        Text("Paste or share an SMS. Links are never opened.", style = MaterialTheme.typography.bodyMedium)
    }
    GlassButton("Paste from clipboard", {
        val clip = app.getSystemService(ClipboardManager::class.java)?.primaryClip?.takeIf { it.itemCount > 0 }?.getItemAt(0)?.coerceToText(app)?.toString()
        vm.navigate(Screen.CHECK); if (!clip.isNullOrBlank()) vm.edit(clip)
    }, primary = false, icon = Icons.Outlined.ContentPaste)
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        val ready = !state.modelStatus.startsWith("Model not") && !state.modelStatus.startsWith("Loading") && !state.modelStatus.contains("nvalid")
        StatusPill(state.modelStatus.substringBefore(" ·").substringBefore("."), Icons.Outlined.Memory,
            if (ready) (if (dark) Verdict.safeDark else Verdict.safe) else (if (dark) Verdict.cautionDark else Verdict.caution))
        val scanning = permissions.active(preferences.scanning)
        StatusPill(if (scanning) "Incoming SMS · enabled" else "Incoming SMS · off", if (scanning) Icons.Outlined.MarkChatRead else Icons.Outlined.SpeakerNotesOff, scheme.onSurfaceVariant)
    }
    if (!state.modelStatus.startsWith("Model ready")) Text("Automatic warnings and reporting are disabled in this development build.",
        style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant)
    GlassSurface(Modifier.fillMaxWidth()) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Icon(Icons.Outlined.Lightbulb, null, tint = scheme.primary)
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Scam tip", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
                Text("Never share an OTP, PIN, or password. Verify requests using your bank’s official app or a number you already trust.")
            }
        }
    }
}

@Composable private fun ColumnScope.CheckScreen(state: CheckState, app: SmishGuardApp, vm: CheckViewModel) {
    val scheme = MaterialTheme.colorScheme
    val glass = LocalGlass.current
    Heading("Check a message")
    GlassSurface(Modifier.fillMaxWidth(), padding = 8.dp) {
        OutlinedTextField(value = state.text, onValueChange = vm::edit, modifier = Modifier.fillMaxWidth(),
            label = { Text("SMS message") }, placeholder = { Text("Paste the message you want to check…") },
            minLines = 7, maxLines = 12, enabled = !state.busy, shape = RoundedCornerShape(22.dp),
            colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color.Transparent, focusedContainerColor = glass.fill, unfocusedContainerColor = Color.Transparent),
            keyboardOptions = KeyboardOptions(autoCorrectEnabled = false, keyboardType = KeyboardType.Password),
            supportingText = { Text("${state.text.length} / 10,000 characters · cleared after checking") })
    }
    state.error?.let { Text(it, color = scheme.error) }
    GlassButton(if (state.busy) "Checking on your phone…" else "Check message", vm::scan, enabled = !state.busy,
        leading = if (state.busy) ({ CircularProgressIndicator(Modifier.size(20.dp), color = scheme.onPrimary, strokeWidth = 2.dp); Spacer(Modifier.width(12.dp)) }) else null)
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        GlassButton("Paste", {
            val clip = app.getSystemService(ClipboardManager::class.java)?.primaryClip?.takeIf { it.itemCount > 0 }?.getItemAt(0)?.coerceToText(app)?.toString()
            if (!clip.isNullOrBlank()) vm.edit(clip)
        }, Modifier.weight(1f), primary = false, icon = Icons.Outlined.ContentPaste)
        GlassButton("Clear message", { vm.edit("") }, Modifier.weight(1f), primary = false)
    }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
        Icon(Icons.Outlined.LinkOff, null, Modifier.size(18.dp).clearAndSetSemantics { }, tint = scheme.onSurfaceVariant)
        Text("${state.modelStatus}. Links are never opened or fetched.", style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant)
    }
}

private data class VerdictLook(val title: String, val body: String, val icon: ImageVector, val color: Color)

@Composable private fun ColumnScope.ResultScreen(state: CheckState, vm: CheckViewModel) {
    val dark = LocalGlass.current.dark
    val scheme = MaterialTheme.colorScheme
    val result = state.result
    val hints = state.hints?.hints.orEmpty()
    val red = if (dark) Verdict.dangerDark else Verdict.danger
    val amber = if (dark) Verdict.cautionDark else Verdict.caution
    val green = if (dark) Verdict.safeDark else Verdict.safe
    val look = when (result) {
        is Detection.Success -> when {
            result.synthetic -> VerdictLook("Synthetic interface fixture", "This is not a real assessment.", Icons.Outlined.Science, scheme.onSurfaceVariant)
            result.suspicious -> VerdictLook("Likely scam", "This message may be a scam. Pause before acting on any request for money or account access.", Icons.Outlined.GppBad, red)
            hints.size >= 2 -> VerdictLook("Not flagged, but be careful", "The model didn't flag it, but it has warning signs. A low score doesn't prove a message is real.", Icons.Outlined.GppMaybe, amber)
            else -> VerdictLook("Not flagged by this model", "The model did not flag this message. This does not establish that it is legitimate.", Icons.Outlined.GppGood, green)
        }
        Detection.Unavailable -> VerdictLook("Model not installed", "No prediction was made. This prototype needs an evaluated model before it can assess messages.", Icons.Outlined.CloudOff, scheme.onSurfaceVariant)
        Detection.InvalidModel -> VerdictLook("Unsupported or invalid model", "This model can't be used, so no prediction was made. Contact the research team for a compatible build.", Icons.Outlined.ErrorOutline, scheme.onSurfaceVariant)
        else -> VerdictLook("Could not complete the check", "No prediction was made. Try checking the message again.", Icons.Outlined.ErrorOutline, scheme.onSurfaceVariant)
    }
    var shown by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { shown = true }
    Heading("Check result")
    AnimatedVisibility(shown, enter = scaleIn(spring(dampingRatio = .7f, stiffness = 380f), initialScale = .85f) + fadeIn()) {
        GlassSurface(Modifier.fillMaxWidth().border(1.5.dp, look.color.copy(alpha = .55f), RoundedCornerShape(28.dp)), tint = look.color, padding = 22.dp) {
            if (result is Detection.Success && result.experimental) StatusPill("Experimental result", Icons.Outlined.Science, amber)
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Icon(look.icon, null, Modifier.size(36.dp), tint = look.color)
                Text(look.title, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold, color = look.color)
            }
            Text(look.body)
            if (result is Detection.Success && !result.synthetic && (result.experimental || result.probability)) {
                ScoreBar(result.score, look.color)
                if (result.experimental) {
                    Text("Uncalibrated model score: ${"%.4f".format(java.util.Locale.ROOT, result.score)}. This is not a likelihood of fraud.", style = MaterialTheme.typography.bodySmall)
                    Text(if (result.suspicious) "Above provisional threshold (0.5)." else "At or below provisional threshold (0.5).", style = MaterialTheme.typography.bodySmall)
                    Text("Automatic warnings and reporting are disabled.", style = MaterialTheme.typography.bodySmall)
                } else Text("Estimated suspicious-class probability: ${"%.1f".format(result.score * 100)}%. This is a model estimate, not certainty.", style = MaterialTheme.typography.bodySmall)
            } else if (result is Detection.Success && !result.synthetic) Text("No confidence percentage is available.", style = MaterialTheme.typography.bodySmall)
        }
    }
    if (hints.isNotEmpty()) GlassSurface(Modifier.fillMaxWidth()) {
        Text("Warning signs found", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        hints.forEach { hint ->
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(when (hint.kind) { HintKind.BRAND -> Icons.Outlined.AccountBalance; HintKind.LINK -> Icons.Outlined.Link
                    HintKind.URGENCY -> Icons.Outlined.Schedule; HintKind.CREDENTIALS -> Icons.Outlined.Password; HintKind.BAIT -> Icons.Outlined.Redeem },
                    null, Modifier.size(20.dp).clearAndSetSemantics { }, tint = amber)
                Text(hint.text)
            }
        }
        Text("These are simple pattern checks, not the model's reasoning.", style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant)
    }
    GlassSurface(Modifier.fillMaxWidth()) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Icon(Icons.Outlined.TipsAndUpdates, null, tint = scheme.primary)
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("What to do", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
                Text(Hints.nextStep(state.hints?.brand))
            }
        }
    }
    Text("Message text has been cleared.", style = MaterialTheme.typography.labelMedium, color = scheme.onSurfaceVariant)
    GlassButton("Check another message", { vm.navigate(Screen.CHECK) })
    GlassButton("Review reporting options", { vm.navigate(Screen.REPORT) }, primary = false, icon = Icons.Outlined.Flag)
}

@Composable private fun ColumnScope.ReportScreen(state: CheckState, preferences: Preferences, vm: CheckViewModel) {
    val scheme = MaterialTheme.colorScheme
    val amber = if (LocalGlass.current.dark) Verdict.cautionDark else Verdict.caution
    Row(Modifier.clip(RoundedCornerShape(50)).clickable { vm.navigate(Screen.RESULT) }.padding(vertical = 4.dp, horizontal = 2.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        Icon(Icons.AutoMirrored.Outlined.ArrowBack, null, Modifier.size(20.dp)); Text("Back to result")
    }
    Heading("Your choice to report")
    Text("Only the details below would be shared. Never your message or phone number.")
    var brand by remember { mutableStateOf(Brand.UNSPECIFIED) }
    Text("Impersonated brand (optional)", style = MaterialTheme.typography.labelLarge)
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Brand.entries.forEach { b -> FilterChip(b == brand, { brand = b }, { Text(b.label) }, shape = RoundedCornerShape(50)) }
    }
    val result = state.result as? Detection.Success
    val payload = if (result != null && state.checkedAt != null) ReportPayload.create(state.domain, result, state.checkedAt, preferences.city, brand) else null
    GlassSurface(Modifier.fillMaxWidth()) {
        if (payload != null) {
            Text("Exact metadata preview", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
            Text(payload.json(), fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace, style = MaterialTheme.typography.bodySmall)
        } else {
            Text("No report can be prepared", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
            Text("An approved model result and a manually selected city would be required. Experimental, synthetic and unavailable results cannot be reported.")
        }
    }
    GlassSurface(Modifier.fillMaxWidth(), tint = amber) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Icon(Icons.Outlined.Info, null, tint = amber)
            Text("Reporting isn't available in this build. Nothing will be sent or queued.")
        }
    }
    GlassButton("Submit report · unavailable", {}, enabled = false)
    Text("Future city dashboards will summarize voluntary reports; their counts cannot measure total citywide scam prevalence.",
        style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant)
}

@Composable private fun SettingsRow(icon: ImageVector, title: String, subtitle: String? = null, onClick: (() -> Unit)? = null, trailing: @Composable () -> Unit = {}) {
    Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier)
        .heightIn(min = 56.dp).padding(horizontal = 4.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(14.dp)) {
        Icon(icon, null, Modifier.size(22.dp).clearAndSetSemantics { }, tint = MaterialTheme.colorScheme.primary)
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.bodyLarge)
            subtitle?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        }
        trailing()
    }
}

@Composable private fun SectionLabel(text: String) { Text(text, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(start = 8.dp)) }

@OptIn(ExperimentalMaterial3Api::class)
@Composable private fun ColumnScope.SettingsContent(app: SmishGuardApp, preferences: Preferences, permissions: PermissionState, refresh: () -> Unit, clear: () -> Unit) {
    val scope = rememberCoroutineScope()
    var consentDialog by remember { mutableStateOf(false) }
    var clearDialog by remember { mutableStateOf(false) }
    var cityMenu by remember { mutableStateOf(false) }
    var notice by remember { mutableStateOf<String?>(null) }
    val scheme = MaterialTheme.colorScheme
    val smsRequest = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        scope.launch { app.preferences.scanning(granted) }
        notice = if (granted) "SMS permission granted. Automatic model-driven warnings remain disabled in this development build." else "SMS permission was not granted. You can still paste or share messages, or allow it later in Android settings."
        refresh()
    }
    val notificationRequest = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { refresh() }
    Heading("Privacy & settings")
    SectionLabel("Protection")
    GlassSurface(Modifier.fillMaxWidth(), padding = 12.dp) {
        SettingsRow(Icons.Outlined.Sms, "Scan incoming SMS", if (permissions.telephony) "Checks new texts on this phone, then discards them" else "This device can't receive SMS") {
            Switch(checked = preferences.scanning && permissions.active(true), onCheckedChange = {
                if (it) consentDialog = true else scope.launch { app.preferences.scanning(false) }
            }, enabled = permissions.telephony, modifier = Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp).semantics { contentDescription = "Scan incoming SMS" })
        }
        HorizontalDivider(color = LocalGlass.current.edge)
        SettingsRow(Icons.Outlined.NotificationsNone, "Warning notifications", if (permissions.notifications) "On" else "Off · warnings can't appear",
            onClick = if (permissions.notifications) null else ({
                if (Build.VERSION.SDK_INT >= 33 && androidx.core.content.ContextCompat.checkSelfPermission(app,
                        Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED)
                    notificationRequest.launch(Manifest.permission.POST_NOTIFICATIONS)
                else app.startActivity(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, app.packageName).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            })) { if (!permissions.notifications) Text("Turn on", color = scheme.primary, fontWeight = FontWeight.SemiBold) }
        Text("Telephony: ${if (permissions.telephony) "available" else "unavailable"}\nSMS permission: ${if (permissions.sms) "granted" else "not granted"}\nNotifications: ${if (permissions.notifications) "enabled" else "disabled"}",
            style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant, modifier = Modifier.padding(start = 40.dp))
        notice?.let { Text(it, style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(start = 40.dp)) }
    }
    SectionLabel("Preferences")
    GlassSurface(Modifier.fillMaxWidth(), padding = 12.dp) {
        Box {
            SettingsRow(Icons.Outlined.Place, "Your city · selected manually", preferences.city.label, onClick = { cityMenu = true }) {
                Icon(Icons.Outlined.ExpandMore, null, tint = scheme.onSurfaceVariant)
            }
            DropdownMenu(cityMenu, { cityMenu = false }) {
                City.entries.forEach { c -> DropdownMenuItem({ Text(c.label) }, { cityMenu = false; scope.launch { app.preferences.city(c) } }) }
            }
        }
        HorizontalDivider(color = LocalGlass.current.edge)
        SettingsRow(Icons.Outlined.Contrast, "Reduce transparency", "Solid backgrounds for easier reading") {
            Switch(preferences.reduceTransparency, { on -> scope.launch { app.preferences.reduceTransparency(on) } },
                modifier = Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp).semantics { contentDescription = "Reduce transparency" })
        }
        HorizontalDivider(color = LocalGlass.current.edge)
        SettingsRow(Icons.AutoMirrored.Outlined.OpenInNew, "Android permission settings", onClick = {
            app.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, "package:${app.packageName}".toUri()).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        })
    }
    SectionLabel("Privacy")
    GlassSurface(Modifier.fillMaxWidth()) {
        Text("Local processing", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
        Text("Only onboarding, incoming-SMS consent, display settings, and your selected city are saved. No scan history or raw messages are kept. The app has no internet permission.")
        Text("Android treats SMS access as a restricted permission and may refuse it. Force-stopping the app pauses automatic scanning until you open it again.",
            style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant)
    }
    GlassButton("Clear local preferences and session", { clearDialog = true }, primary = false, icon = Icons.Outlined.DeleteOutline)
    if (consentDialog) AlertDialog(onDismissRequest = { consentDialog = false }, icon = { Icon(Icons.Outlined.Sms, null) }, title = { Text("Allow incoming SMS checks?") },
        text = { Text("Veritxt will receive new SMS text to check locally, then discard it. It will not read your inbox or change messages. Automatic checks and warnings are disabled until a model is approved for that use. Use manual paste/share for experimental testing. Android may refuse this restricted permission. Notifications are a separate choice.") },
        confirmButton = { TextButton(onClick = {
            consentDialog = false
            if (permissions.sms) scope.launch { app.preferences.scanning(true) } else smsRequest.launch(Manifest.permission.RECEIVE_SMS)
        }) { Text("Agree and continue") } }, dismissButton = { TextButton(onClick = { consentDialog = false }) { Text("Keep off") } })
    if (clearDialog) AlertDialog(onDismissRequest = { clearDialog = false }, title = { Text("Clear local records?") },
        text = { Text("This clears your city, consent and display preferences, and current checking session. Incoming scanning turns off. Android permissions remain under system settings.") },
        confirmButton = { TextButton(onClick = { clearDialog = false; scope.launch { app.preferences.clear(); clear() } }) { Text("Clear") } },
        dismissButton = { TextButton(onClick = { clearDialog = false }) { Text("Cancel") } })
}
