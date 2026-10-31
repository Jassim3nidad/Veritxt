package ph.smishguard

import android.Manifest
import android.app.NotificationManager
import android.content.ActivityNotFoundException
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.annotation.StringRes
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
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
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.HelpOutline
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
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.layout.onSizeChanged
import dev.chrisbanes.haze.HazeState
import dev.chrisbanes.haze.hazeSource
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.net.toUri
import androidx.core.os.LocaleListCompat
import androidx.core.view.WindowCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import kotlinx.coroutines.launch
import ph.smishguard.data.Preferences
import ph.smishguard.data.ThemeMode
import ph.smishguard.blocking.SystemNumberBlocking
import ph.smishguard.blocking.SenderNumberClipboard
import ph.smishguard.model.Detection
import ph.smishguard.model.AppRiskPolicy as RiskPolicy
import ph.smishguard.model.RiskLevel
import ph.smishguard.model.ManualBlocking
import ph.smishguard.model.BlockingStep
import ph.smishguard.privacy.Brand
import ph.smishguard.privacy.ReportPayload
import ph.smishguard.sms.CheckPrompt
import ph.smishguard.sms.PendingChecks
import ph.smishguard.sms.PermissionState
import ph.smishguard.ui.*
import java.text.NumberFormat
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale

// AppCompatActivity (not ComponentActivity) so the in-app language also applies on Android 8-12.
class MainActivity : AppCompatActivity() {
    private val vm: CheckViewModel by viewModels()
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        consumeIntent(intent)
        setContent {
            // No Compose saveable state, including text field state, enters activity bundles.
            CompositionLocalProvider(LocalSaveableStateRegistry provides null) {
                SmishGuardUi(application as SmishGuardApp, vm)
            }
        }
    }
    override fun onNewIntent(intent: Intent) { super.onNewIntent(intent); consumeIntent(intent) }
    private fun consumeIntent(incoming: Intent) {
        if (incoming.action == Intent.ACTION_SEND && incoming.type == "text/plain") {
            val text = incoming.getCharSequenceExtra(Intent.EXTRA_TEXT)?.toString()
            incoming.removeExtra(Intent.EXTRA_TEXT)
            incoming.clipData = null
            incoming.replaceExtras(null as Bundle?)
            // Keep routing identity stable; discard the payload rather than replace the
            // launch intent. Android lifecycle observers match action/type/categories.
            incoming.setDataAndType(null, "text/plain")
            if (text != null) vm.share(text)
        } else if (incoming.action == CheckPrompt.ACTION_CHECK) {
            // "Check now" carries only an id; the text itself never leaves process memory.
            val id = incoming.getStringExtra(CheckPrompt.EXTRA_ID)
            CheckPrompt.cancel(this, incoming.getIntExtra(CheckPrompt.EXTRA_NOTIFICATION, 0), id)
            incoming.replaceExtras(null as Bundle?)
            incoming.action = null // so a recreate (rotation, language change) doesn't run it again
            val pending = id?.let(PendingChecks::take)
            vm.checkPending(pending?.text, pending?.senderNumber)
        }
    }
    override fun onStop() { vm.endSession(); super.onStop() }
    override fun onSaveInstanceState(outState: Bundle) { super.onSaveInstanceState(outState); outState.clear() }
}

enum class AppLanguage(val tag: String) { SYSTEM(""), ENGLISH("en"), FILIPINO("fil");
    companion object {
        fun current(): AppLanguage = AppCompatDelegate.getApplicationLocales().toLanguageTags().let {
            when { it.startsWith("fil") || it.startsWith("tl") -> FILIPINO; it.startsWith("en") -> ENGLISH; else -> SYSTEM }
        }
        fun set(language: AppLanguage) = AppCompatDelegate.setApplicationLocales(
            if (language == SYSTEM) LocaleListCompat.getEmptyLocaleList() else LocaleListCompat.forLanguageTags(language.tag))
    }
}

@Composable private fun SmishGuardTheme(solid: Boolean, mode: ThemeMode, content: @Composable () -> Unit) {
    val dark = when (mode) {
        ThemeMode.SYSTEM -> isSystemInDarkTheme()
        ThemeMode.LIGHT -> false
        ThemeMode.DARK -> true
    }
    val activity = androidx.activity.compose.LocalActivity.current
    SideEffect {
        activity?.let {
            WindowCompat.getInsetsController(it.window, it.window.decorView).apply {
                isAppearanceLightStatusBars = !dark
                isAppearanceLightNavigationBars = !dark
            }
        }
    }
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
    BackHandler(state.screen != Screen.HOME) {
        if (state.screen == Screen.PRIVACY || state.screen == Screen.HELP) vm.navigate(Screen.SETTINGS) else vm.endSession()
    }
    val scope = rememberCoroutineScope()
    val activity = androidx.activity.compose.LocalActivity.current
    // Android 11 and older keep the keyboard open after the text field leaves the screen; close it on every
    // screen change and when a check starts.
    val keyboard = LocalSoftwareKeyboardController.current
    val focus = LocalFocusManager.current
    LaunchedEffect(state.screen, state.busy) { if (state.screen != Screen.CHECK || state.busy) { focus.clearFocus(); keyboard?.hide() } }
    SmishGuardTheme(solid = preferences?.reduceTransparency == true, mode = preferences?.themeMode ?: ThemeMode.SYSTEM) {
        val haze = remember { HazeState() }
        val showNav = preferences?.privacyAccepted == true && preferences?.onboarded == true
        var navHeight by remember { mutableIntStateOf(0) }
        Box(Modifier.fillMaxSize()) {
          // Everything under the nav bar is the blur source; the bar itself sits outside it, on top.
          Box(Modifier.fillMaxSize().hazeSource(haze)) {
            GlassBackground()
            Scaffold(containerColor = Color.Transparent, contentColor = MaterialTheme.colorScheme.onSurface, bottomBar = {
                // Reserves the floating bar's height so the last item can scroll above it.
                if (showNav) Spacer(Modifier.height(with(LocalDensity.current) { navHeight.toDp() }))
            }) { padding ->
                val prefs = preferences
                when {
                    prefs == null -> Box(Modifier.fillMaxSize(), Alignment.Center) { CircularProgressIndicator() }
                    // The privacy notice comes first; nothing else is usable until the user agrees.
                    !prefs.privacyAccepted -> Box(Modifier.padding(top = padding.calculateTopPadding())) {
                        Page(bottom = padding.calculateBottomPadding()) {
                            PrivacyNotice(accepting = true, acceptedOn = null, onAgree = { scope.launch { app.preferences.acceptPrivacy() } },
                                onNotNow = { activity?.finish() }, onBack = {})
                        }
                    }
                    !prefs.onboarded -> Onboarding(app, state.modelStatus, Modifier.padding(padding))
                    // Content scrolls under the floating glass nav bar; only the top inset is reserved.
                    else -> AnimatedContent(state.screen, Modifier.padding(top = padding.calculateTopPadding()), label = "screen",
                        transitionSpec = { (fadeIn(tween(220)) + slideInVertically(spring(stiffness = 500f)) { it / 14 }) togetherWith fadeOut(tween(120)) }) { screen ->
                        Page(bottom = padding.calculateBottomPadding()) {
                            when (screen) {
                                Screen.HOME -> HomeScreen(state, prefs, permissions, app, vm)
                                Screen.CHECK -> CheckScreen(state, app, vm)
                                Screen.RESULT -> ResultScreen(state, vm)
                                Screen.REPORT -> ReportScreen(state, vm)
                                Screen.SETTINGS -> SettingsContent(app, prefs, permissions, vm, { permissions = PermissionState.read(app) }, { vm.endSession() })
                                Screen.PRIVACY -> PrivacyNotice(accepting = false, acceptedOn = prefs.privacyAcceptedOn, onAgree = {}, onNotNow = {},
                                    onBack = { vm.navigate(Screen.SETTINGS) })
                                Screen.HELP -> HelpScreen(app, prefs, permissions, vm)
                            }
                        }
                    }
                }
            }
          }
          // 3-button navigation (common on Android 11) is tall; keep scrolled text from showing behind its buttons.
          val systemNav = WindowInsets.navigationBars.asPaddingValues().calculateBottomPadding()
          if (systemNav > 32.dp) Box(Modifier.align(Alignment.BottomCenter).fillMaxWidth().height(systemNav).background(LocalGlass.current.barFill))
          if (showNav) {
              val tab = when (state.screen) { Screen.SETTINGS, Screen.PRIVACY, Screen.HELP -> Screen.SETTINGS; Screen.HOME -> Screen.HOME; else -> Screen.CHECK }
              GlassNavBar(listOf(NavItem(Screen.HOME, stringResource(R.string.nav_home), Icons.Outlined.Home),
                  NavItem(Screen.CHECK, stringResource(R.string.nav_check), Icons.Outlined.Sms),
                  NavItem(Screen.SETTINGS, stringResource(R.string.nav_settings), Icons.Outlined.Settings)), tab, vm::navigate,
                  Modifier.align(Alignment.BottomCenter).onSizeChanged { navHeight = it.height }, haze)
          }
        }
    }
}

@Composable private fun Page(bottom: androidx.compose.ui.unit.Dp, content: @Composable ColumnScope.() -> Unit) {
    Column(Modifier.fillMaxSize().imePadding().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Image(painterResource(R.drawable.ic_veritxt_mark), null, Modifier.size(24.dp).clearAndSetSemantics { })
            Text(stringResource(R.string.app_name) + when (BuildConfig.BUILD_TYPE) {
                "debug", "development", "release", "selectedSvm" -> ""
                "nbGeneralization" -> " · Retrained NB"
                "multiclassSvm" -> " · SVM 80%"
                "multiclassSvm60" -> " · SVM 60%"
                "cashbackReview" -> " · Review"
                "oldSvm" -> " · Ham/Smishing"
                else -> " · " + BuildConfig.BUILD_TYPE
            }, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
        }
        content()
        Spacer(Modifier.height(bottom + 8.dp))
    }
}

@Composable private fun Heading(text: String) { Text(text, modifier = Modifier.semantics { heading() }, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold) }

@Composable private fun BackLink(text: String, onClick: () -> Unit) {
    Row(Modifier.clip(RoundedCornerShape(50)).clickable(onClick = onClick).heightIn(min = 48.dp).padding(horizontal = 2.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        Icon(Icons.AutoMirrored.Outlined.ArrowBack, null, Modifier.size(20.dp)); Text(text)
    }
}

/** Model status arrives in English from the detector; show it in the app language. */
@Composable private fun statusLabel(status: String): String = when {
    status.startsWith("Loading") -> stringResource(R.string.status_loading)
    status.startsWith("Model not installed") -> stringResource(R.string.status_missing)
    status.startsWith("Unsupported") -> stringResource(R.string.status_invalid)
    status.startsWith("Experimental · Linear SVM · svm-C-10.0") -> stringResource(R.string.status_linear_svm)
    status.startsWith("Experimental · Naive Bayes") -> stringResource(R.string.status_retrained_nb)
    status.startsWith("Experimental") -> stringResource(R.string.status_experimental)
    status.startsWith("Model ready") -> stringResource(R.string.status_ready)
    status.startsWith("Synthetic") -> stringResource(R.string.status_synthetic)
    else -> status
}

@Composable private fun ThemePicker(selected: ThemeMode, onSelect: (ThemeMode) -> Unit) {
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        listOf(ThemeMode.SYSTEM to R.string.theme_system, ThemeMode.LIGHT to R.string.theme_light,
            ThemeMode.DARK to R.string.theme_dark).forEach { (mode, label) ->
            FilterChip(selected == mode, { onSelect(mode) }, { Text(stringResource(label)) },
                shape = RoundedCornerShape(50), modifier = Modifier.heightIn(min = 48.dp).testTag("theme_${mode.storedValue}"))
        }
    }
}

@Composable private fun LanguagePicker() {
    var current by remember { mutableStateOf(AppLanguage.current()) }
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        listOf(AppLanguage.SYSTEM to R.string.language_system, AppLanguage.ENGLISH to R.string.language_en,
            AppLanguage.FILIPINO to R.string.language_fil).forEach { (language, label) ->
            FilterChip(current == language, { current = language; AppLanguage.set(language) }, { Text(stringResource(label)) },
                shape = RoundedCornerShape(50), modifier = Modifier.heightIn(min = 48.dp))
        }
    }
}

@Composable private fun ColumnScope.PrivacyNotice(accepting: Boolean, acceptedOn: String?, onAgree: () -> Unit, onNotNow: () -> Unit, onBack: () -> Unit) {
    var agreed by remember { mutableStateOf(false) }
    var nudge by remember { mutableStateOf(false) }
    val scheme = MaterialTheme.colorScheme
    if (!accepting) BackLink(stringResource(R.string.back), onBack)
    Heading(stringResource(R.string.privacy_title))
    Text(stringResource(R.string.privacy_intro), style = MaterialTheme.typography.bodyLarge)
    if (accepting) LanguagePicker()
    GlassSurface(Modifier.fillMaxWidth()) {
        listOf(Triple(Icons.Outlined.Sms, R.string.privacy_checks_title, R.string.privacy_checks_body),
            Triple(Icons.Outlined.PhoneAndroid, R.string.privacy_where_title, R.string.privacy_where_body),
            Triple(Icons.Outlined.Save, R.string.privacy_saved_title, R.string.privacy_saved_body),
            Triple(Icons.Outlined.ToggleOn, R.string.privacy_optional_title, R.string.privacy_optional_body),
            Triple(Icons.Outlined.Gavel, R.string.privacy_rights_title, R.string.privacy_rights_body)).forEach { (icon, title, body) ->
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Icon(icon, null, Modifier.size(22.dp).clearAndSetSemantics { }, tint = scheme.primary)
                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(stringResource(title), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
                    Text(stringResource(body))
                }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Icon(Icons.Outlined.MailOutline, null, Modifier.size(22.dp).clearAndSetSemantics { }, tint = scheme.primary)
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(stringResource(R.string.privacy_contact_title), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
                Text(stringResource(R.string.privacy_contact_body, stringResource(R.string.privacy_contact_value)))
            }
        }
    }
    if (accepting) {
        Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp))
            .toggleable(agreed, role = Role.Checkbox) { agreed = it; nudge = false }.heightIn(min = 56.dp).padding(horizontal = 4.dp),
            verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Checkbox(agreed, null)
            Text(stringResource(R.string.privacy_checkbox), style = MaterialTheme.typography.bodyLarge)
        }
        if (nudge) Text(stringResource(R.string.privacy_tick_first), color = scheme.error)
        GlassButton(stringResource(R.string.privacy_agree), { if (agreed) onAgree() else nudge = true })
        GlassButton(stringResource(R.string.privacy_not_now), onNotNow, primary = false)
    } else if (acceptedOn != null) {
        val locale = LocalConfiguration.current.locales[0] ?: Locale.getDefault()
        val date = runCatching { LocalDate.parse(acceptedOn).format(DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale)) }.getOrDefault(acceptedOn)
        Text(stringResource(R.string.privacy_accepted_on, date), style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant)
    }
}

@Composable private fun Onboarding(app: SmishGuardApp, modelStatus: String, modifier: Modifier) {
    val scope = rememberCoroutineScope()
    val pages = listOf(
        Triple<ImageVector?, Int, Int>(null, R.string.home_title, R.string.onb1_body),
        Triple(Icons.Outlined.Lock, R.string.onb2_title, R.string.onb2_body),
        Triple(Icons.Outlined.NotificationsNone, R.string.onb3_title, R.string.onb3_body))
    val pager = rememberPagerState { pages.size }
    Column(modifier.fillMaxSize().padding(20.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
        HorizontalPager(pager, Modifier.weight(1f)) { i ->
            val (icon, title, body) = pages[i]
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally) {
                GlassSurface(Modifier.fillMaxWidth(), padding = 28.dp) {
                    if (icon == null) {
                        Image(painterResource(R.drawable.ic_veritxt_mark), null, Modifier.size(64.dp))
                        Text(stringResource(R.string.app_tagline), style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                    }
                    else Box(Modifier.size(64.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary.copy(alpha = .14f)), Alignment.Center) {
                        Icon(icon, null, Modifier.size(32.dp), tint = MaterialTheme.colorScheme.primary)
                    }
                    Text(stringResource(title), Modifier.semantics { heading() }, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
                    Text(stringResource(body), style = MaterialTheme.typography.bodyLarge)
                    if (i == 2) Text(stringResource(if (modelStatus.startsWith("Experimental")) R.string.onb_model_experimental else R.string.onb_model_missing),
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
        // Scrollable so the actions stay reachable at large font sizes.
        Column(Modifier.verticalScroll(rememberScrollState()), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
            val pageLabel = stringResource(R.string.onb_pages, pager.currentPage + 1, pages.size)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.clearAndSetSemantics { contentDescription = pageLabel }) {
                repeat(pages.size) { Box(Modifier.size(if (it == pager.currentPage) 22.dp else 8.dp, 8.dp).clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primary.copy(alpha = if (it == pager.currentPage) 1f else .3f))) }
            }
            Text(stringResource(R.string.onb_permissions_note), style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.Center, color = MaterialTheme.colorScheme.onSurfaceVariant)
            GlassButton(stringResource(R.string.onb_continue), { scope.launch { app.preferences.onboard() } })
        }
    }
}

private fun clipboardText(context: Context): String? = context.getSystemService(ClipboardManager::class.java)?.primaryClip
    ?.takeIf { it.itemCount > 0 }?.getItemAt(0)?.coerceToText(context)?.toString()?.takeIf { it.isNotBlank() }

@Composable private fun ColumnScope.HomeScreen(state: CheckState, preferences: Preferences, permissions: PermissionState, app: SmishGuardApp, vm: CheckViewModel) {
    val scheme = MaterialTheme.colorScheme
    val dark = LocalGlass.current.dark
    Heading(stringResource(R.string.home_title))
    GlassSurface(Modifier.fillMaxWidth().clip(RoundedCornerShape(28.dp)).clickable { vm.navigate(Screen.CHECK) }, tint = scheme.primary, padding = 24.dp) {
        Box(Modifier.size(56.dp).clip(CircleShape).background(scheme.primary), Alignment.Center) {
            Icon(Icons.Outlined.ContentPasteSearch, null, Modifier.size(28.dp), tint = scheme.onPrimary)
        }
        Text(stringResource(R.string.home_check_title), style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
        Text(stringResource(R.string.home_check_body), style = MaterialTheme.typography.bodyMedium)
    }
    GlassButton(stringResource(R.string.home_paste), {
        val clip = clipboardText(app)
        vm.navigate(Screen.CHECK); if (clip != null) vm.edit(clip)
    }, primary = false, icon = Icons.Outlined.ContentPaste)
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        val ready = state.modelStatus.startsWith("Model ready") || state.modelStatus.startsWith("Experimental")
        StatusPill(statusLabel(state.modelStatus), Icons.Outlined.Memory,
            if (ready) (if (dark) Verdict.safeDark else Verdict.safe) else (if (dark) Verdict.cautionDark else Verdict.caution))
        val scanning = permissions.active(preferences.scanning)
        StatusPill(stringResource(if (scanning) R.string.status_incoming_on else R.string.status_incoming_off),
            if (scanning) Icons.Outlined.MarkChatRead else Icons.Outlined.SpeakerNotesOff, scheme.onSurfaceVariant)
    }
    val note = when {
        !state.autoWarnings -> R.string.home_note_missing
        state.modelStatus.startsWith("Experimental") -> R.string.home_note_experimental
        else -> null
    }
    note?.let { Text(stringResource(it), style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant) }
    GlassSurface(Modifier.fillMaxWidth()) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Icon(Icons.Outlined.Lightbulb, null, tint = scheme.primary)
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(stringResource(R.string.tip_title), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
                Text(stringResource(R.string.tip_body))
            }
        }
    }
}

@Composable private fun ColumnScope.CheckScreen(state: CheckState, app: SmishGuardApp, vm: CheckViewModel) {
    val scheme = MaterialTheme.colorScheme
    val glass = LocalGlass.current
    Heading(stringResource(R.string.check_title))
    GlassSurface(Modifier.fillMaxWidth(), padding = 8.dp) {
        OutlinedTextField(value = state.text, onValueChange = vm::edit, modifier = Modifier.fillMaxWidth(),
            label = { Text(stringResource(R.string.check_field_label)) }, placeholder = { Text(stringResource(R.string.check_placeholder)) },
            minLines = 7, maxLines = 12, enabled = !state.busy, shape = RoundedCornerShape(22.dp),
            colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color.Transparent, focusedContainerColor = glass.fill, unfocusedContainerColor = Color.Transparent),
            keyboardOptions = KeyboardOptions(autoCorrectEnabled = false, keyboardType = KeyboardType.Password),
            supportingText = { Text(stringResource(R.string.check_counter, NumberFormat.getIntegerInstance().format(state.text.length))) })
    }
    state.error?.let { Text(stringResource(it), color = scheme.error) }
    GlassButton(stringResource(if (state.busy) R.string.check_busy else R.string.check_button), vm::scan, enabled = !state.busy,
        leading = if (state.busy) ({ CircularProgressIndicator(Modifier.size(20.dp), color = scheme.onPrimary, strokeWidth = 2.dp); Spacer(Modifier.width(12.dp)) }) else null)
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        GlassButton(stringResource(R.string.check_paste), { clipboardText(app)?.let(vm::edit) }, Modifier.weight(1f), primary = false, icon = Icons.Outlined.ContentPaste)
        GlassButton(stringResource(R.string.check_clear), { vm.edit("") }, Modifier.weight(1f), primary = false)
    }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
        Icon(Icons.Outlined.LinkOff, null, Modifier.size(18.dp).clearAndSetSemantics { }, tint = scheme.onSurfaceVariant)
        Text(stringResource(R.string.check_links_note, statusLabel(state.modelStatus)), style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant)
    }
}

@Composable private fun ColumnScope.ResultScreen(state: CheckState, vm: CheckViewModel) {
    val dark = LocalGlass.current.dark
    val scheme = MaterialTheme.colorScheme
    val result = state.result
    var explain by remember(result) { mutableStateOf(false) }
    val assessment = state.assessment ?: RiskPolicy.assess(state.checkedMessage, result)
    val red = if (dark) Verdict.dangerDark else Verdict.danger
    val amber = if (dark) Verdict.cautionDark else Verdict.caution
    val green = if (dark) Verdict.safeDark else Verdict.safe
    val (icon, color) = when (assessment.level) {
        RiskLevel.LOW -> Icons.Outlined.GppGood to green
        RiskLevel.MEDIUM -> Icons.Outlined.GppMaybe to amber
        RiskLevel.HIGH -> Icons.Outlined.GppBad to red
        RiskLevel.UNABLE_TO_ASSESS -> Icons.AutoMirrored.Outlined.HelpOutline to if (dark) Color(0xFFC3C7CB) else Color(0xFF5B5F63)
    }
    var shown by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { shown = true }
    Heading(stringResource(R.string.result_title))
    AnimatedVisibility(shown, enter = scaleIn(spring(dampingRatio = .7f, stiffness = 380f), initialScale = .85f) + fadeIn()) {
        GlassSurface(Modifier.fillMaxWidth().semantics { liveRegion = LiveRegionMode.Polite }.border(1.5.dp, color.copy(alpha = .55f), RoundedCornerShape(28.dp)), tint = color, padding = 22.dp) {
            if (result is Detection.Success && result.experimental) StatusPill(stringResource(R.string.tag_experimental), Icons.Outlined.Science, amber)
            if (result is Detection.Success) result.category?.let { category ->
                Text(stringResource(R.string.sms_category_heading), style = MaterialTheme.typography.labelLarge)
                Text(stringResource(when (category) {
                    ph.smishguard.model.SmsCategory.HAM -> R.string.sms_category_ham
                    ph.smishguard.model.SmsCategory.SMISHING -> R.string.sms_category_smishing
                    ph.smishguard.model.SmsCategory.GAMBLING -> R.string.sms_category_gambling
                }), style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
                Text(stringResource(if (BuildConfig.BUILD_TYPE == "oldSvm") R.string.sms_category_binary_note else R.string.sms_category_note), style = MaterialTheme.typography.bodySmall)
            }
            Text(stringResource(R.string.risk_level), style = MaterialTheme.typography.labelLarge)
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Icon(icon, null, Modifier.size(36.dp).clearAndSetSemantics { }, tint = color)
                Text(stringResource(RiskPresentation.label(assessment.level)), modifier = Modifier.semantics { heading() }, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold, color = color)
            }
            assessment.score?.let { score ->
                Text(stringResource(R.string.risk_score, score), style = MaterialTheme.typography.titleLarge)
                ScoreBar(score / 100.0, color)
                Text(stringResource(R.string.risk_score_note), style = MaterialTheme.typography.bodySmall)
            }
            Text(stringResource(R.string.risk_analysis), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
            Text(stringResource(RiskPresentation.analysis(assessment.level)))
            assessment.limit?.let { Text(stringResource(RiskPresentation.limit(it))) }
            if (result is Detection.Success && result.tokenWindow?.truncated == true) Text(stringResource(R.string.result_truncated))
        }
    }
    state.senderNumber?.let { number -> GlassSurface(Modifier.fillMaxWidth()) {
        Text(stringResource(R.string.sms_sender, number), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
        Text(stringResource(R.string.sms_sender_note), style = MaterialTheme.typography.bodySmall)
    } }
    if (state.checkedMessage.isNotEmpty()) GlassSurface(Modifier.fillMaxWidth()) {
        Text(stringResource(R.string.checked_message), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
        Text(state.checkedMessage)
    }
    GlassSurface(Modifier.fillMaxWidth()) {
        Text(stringResource(R.string.signs_title), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        if (assessment.indicators.isEmpty()) Text(stringResource(if (assessment.score == null) R.string.risk_indicators_unavailable else R.string.risk_indicators_none))
        assessment.indicators.forEach { indicator ->
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.Info, null, Modifier.size(20.dp).clearAndSetSemantics { }, tint = scheme.onSurfaceVariant)
                Text(stringResource(RiskPresentation.indicator(indicator)))
            }
        }
        Text(stringResource(R.string.risk_evidence_note), style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant)
    }
    GlassSurface(Modifier.fillMaxWidth()) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Icon(Icons.Outlined.TipsAndUpdates, null, tint = scheme.primary)
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(stringResource(R.string.todo_title), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
                Text(stringResource(RiskPresentation.action(assessment.level)))
            }
        }
    }
    val context = LocalContext.current
    if (ManualBlocking.offered(assessment)) ManualBlockingControl(assessment, state.senderNumber) { SystemNumberBlocking.openSettings(context) }
    ResultExplanation(state, explain, { explain = it }) { vm.navigate(Screen.REPORT) }
    Text(stringResource(R.string.result_cleared), style = MaterialTheme.typography.labelMedium, color = scheme.onSurfaceVariant)
    GlassButton(stringResource(R.string.result_again), { vm.navigate(Screen.CHECK) })
    if (!explain) GlassButton(stringResource(R.string.result_report), { vm.navigate(Screen.REPORT) }, primary = false, icon = Icons.Outlined.Flag)
}

@Composable internal fun ManualBlockingControl(assessment: ph.smishguard.model.RiskAssessment, senderNumber: String? = null, openBlockedNumbers: () -> Boolean) {
    val context = LocalContext.current
    val senderLabel = stringResource(R.string.sender_number_label)
    var step by remember(assessment, senderNumber) { mutableStateOf(BlockingStep.IDLE) }
    var launchFailed by remember(assessment, senderNumber) { mutableStateOf(false) }
    var copied by remember(assessment, senderNumber) { mutableStateOf(false) }
    GlassButton(stringResource(if (senderNumber == null) R.string.block_number else R.string.block_sender), { launchFailed = false; copied = false; step = ManualBlocking.request() }, primary = false, icon = Icons.Outlined.Block)
    if (step != BlockingStep.IDLE) AlertDialog(onDismissRequest = { step = ManualBlocking.dismiss() },
        title = { Text(stringResource(if (step == BlockingStep.AWAITING_CONFIRMATION) {
            if (senderNumber == null) R.string.block_confirm_title else R.string.block_sender_title
        } else R.string.block_instructions_title)) },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                if (launchFailed) Text(stringResource(R.string.block_unavailable))
                senderNumber?.let { number ->
                    Text(stringResource(R.string.sms_sender, number), fontWeight = FontWeight.SemiBold)
                    Text(stringResource(R.string.sms_sender_note), style = MaterialTheme.typography.bodySmall)
                    TextButton(onClick = {
                        val clip = SenderNumberClipboard.createClip(senderLabel, number)
                        context.getSystemService(ClipboardManager::class.java).setPrimaryClip(clip)
                        copied = true
                    }) { Text(stringResource(if (copied) R.string.sender_number_copied else R.string.copy_sender_number)) }
                }
                if (senderNumber == null && assessment.kind == ph.smishguard.model.InputKind.MESSAGE) Text(stringResource(R.string.sms_sender_missing))
                Text(stringResource(if (step == BlockingStep.AWAITING_CONFIRMATION) {
                    if (senderNumber == null) R.string.block_confirm_body else R.string.block_sender_body
                } else R.string.block_instructions_body))
                if (step == BlockingStep.AWAITING_CONFIRMATION) TextButton(onClick = { step = ManualBlocking.confirm(step) }) {
                    Text(stringResource(R.string.block_show_instructions))
                }
            }
        },
        confirmButton = { TextButton(onClick = {
            if (step == BlockingStep.AWAITING_CONFIRMATION) {
                // Dismiss before leaving; returning from Android must not reopen this dialog.
                step = ManualBlocking.dismiss()
                if (!openBlockedNumbers()) { launchFailed = true; step = BlockingStep.INSTRUCTIONS }
            } else step = ManualBlocking.dismiss()
        }) {
            Text(stringResource(if (step == BlockingStep.AWAITING_CONFIRMATION) R.string.block_confirm else R.string.result_close))
        } },
        dismissButton = { if (step == BlockingStep.AWAITING_CONFIRMATION) TextButton(onClick = { step = ManualBlocking.dismiss() }) { Text(stringResource(R.string.block_cancel)) } })
}

@Composable private fun ResultExplanation(state: CheckState, explain: Boolean, setExplain: (Boolean) -> Unit, report: () -> Unit) {
    TextButton(onClick = { setExplain(true) }, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.result_explain)) }
    if (explain) AlertDialog(onDismissRequest = { setExplain(false) },
        title = { Text(stringResource(R.string.result_about)) },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(stringResource(R.string.result_explanation))
                if (RiskPolicy.linkedCashbackReviewEnabled) Text(stringResource(R.string.linked_cashback_explanation))
                (state.result as? Detection.Success)?.takeIf { state.assessment?.score != null }?.let { result ->
                    // Preserve raw research output separately; it is never presented as a risk percentage.
                    if (result.classScores != null && result.classScores.size == 3) {
                        Text(stringResource(R.string.multiclass_decision_note))
                        Text(stringResource(R.string.multiclass_margins, result.classScores[0], result.classScores[1], result.classScores[2]))
                    } else Text(ph.smishguard.model.ResultCopy.score(result.score))
                    result.policy?.let { Text(it.explanation()) }
                    result.tokenWindow?.takeIf { it.truncated }?.let { Text(it.explanation()) }
                }
                Text(stringResource(R.string.result_abstention))
                Text(stringResource(if (state.autoWarnings) R.string.score_disabled else R.string.automatic_disabled))
                Text(stringResource(R.string.result_cleared))
                TextButton(onClick = { setExplain(false); report() }) { Text(stringResource(R.string.result_report)) }
            }
        }, confirmButton = { TextButton(onClick = { setExplain(false) }) { Text(stringResource(R.string.result_close)) } })
}

@Composable private fun brandLabel(brand: Brand): String = when (brand) {
    Brand.UNSPECIFIED -> stringResource(R.string.brand_unspecified)
    Brand.OTHER -> stringResource(R.string.brand_other)
    else -> brand.label
}

@Composable private fun ColumnScope.ReportScreen(state: CheckState, vm: CheckViewModel) {
    val amber = if (LocalGlass.current.dark) Verdict.cautionDark else Verdict.caution
    BackLink(stringResource(R.string.report_back)) { vm.navigate(Screen.RESULT) }
    Heading(stringResource(R.string.report_title))
    Text(stringResource(R.string.report_intro))
    var brand by remember { mutableStateOf(Brand.UNSPECIFIED) }
    Text(stringResource(R.string.report_brand_label), style = MaterialTheme.typography.labelLarge)
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Brand.entries.forEach { b -> FilterChip(b == brand, { brand = b }, { Text(brandLabel(b)) }, shape = RoundedCornerShape(50)) }
    }
    val result = state.result as? Detection.Success
    val payload = if (result != null && state.checkedAt != null) ReportPayload.create(state.domain, result, state.checkedAt, brand) else null
    GlassSurface(Modifier.fillMaxWidth()) {
        if (payload != null) {
            Text(stringResource(R.string.report_preview), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
            Text(payload.json(), fontFamily = FontFamily.Monospace, style = MaterialTheme.typography.bodySmall)
        } else {
            Text(stringResource(R.string.report_none_title), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
            Text(stringResource(R.string.report_none_body))
        }
    }
    GlassSurface(Modifier.fillMaxWidth(), tint = amber) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Icon(Icons.Outlined.Info, null, tint = amber)
            Text(stringResource(R.string.report_unavailable))
        }
    }
    GlassButton(stringResource(R.string.report_submit), {}, enabled = false)
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

private fun Context.openSettings(vararg intents: Intent) {
    for (intent in intents) try { startActivity(intent); return } catch (_: ActivityNotFoundException) { }
}
private fun appInfo(context: Context) = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, "package:${context.packageName}".toUri())
private fun notificationSettings(context: Context) = Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, context.packageName)

/** Sends the sample prompt; returns the message to show. */
@StringRes private fun sendTestNotification(context: Context): Int =
    if (CheckPrompt.show(context, context.getString(R.string.notif_test_sample), CheckPrompt.Kind.TEST) != null) R.string.test_sent else R.string.test_needs_notifications

@Composable private fun rememberNotificationRequest(refresh: () -> Unit): () -> Unit {
    val context = LocalContext.current
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { refresh() }
    return {
        if (Build.VERSION.SDK_INT >= 33 && androidx.core.content.ContextCompat.checkSelfPermission(context,
                Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED)
            launcher.launch(Manifest.permission.POST_NOTIFICATIONS)
        else context.openSettings(notificationSettings(context), appInfo(context))
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable private fun ColumnScope.SettingsContent(app: SmishGuardApp, preferences: Preferences, permissions: PermissionState, vm: CheckViewModel,
                                                   refresh: () -> Unit, clear: () -> Unit) {
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    var consentDialog by remember { mutableStateOf(false) }
    var clearDialog by remember { mutableStateOf(false) }
    var notice by remember { mutableStateOf<Int?>(null) }
    val scheme = MaterialTheme.colorScheme
    val edge = LocalGlass.current.edge
    val smsRequest = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        scope.launch { app.preferences.scanning(granted) }
        notice = if (granted) R.string.sms_granted_note else R.string.sms_denied_note
        refresh()
    }
    val requestNotifications = rememberNotificationRequest(refresh)
    Heading(stringResource(R.string.settings_title))
    SectionLabel(stringResource(R.string.section_protection))
    GlassSurface(Modifier.fillMaxWidth(), padding = 12.dp) {
        val active = preferences.scanning && permissions.active(true)
        val incomingCd = stringResource(R.string.incoming_cd)
        SettingsRow(Icons.Outlined.Sms, stringResource(R.string.incoming_title),
            stringResource(if (!permissions.telephony) R.string.incoming_unavailable else if (!active) R.string.incoming_off else R.string.incoming_all)) {
            Switch(checked = active, onCheckedChange = {
                if (it) consentDialog = true else scope.launch { app.preferences.scanning(false) }
            }, enabled = permissions.telephony, modifier = Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp).semantics { contentDescription = incomingCd })
        }
        HorizontalDivider(color = edge)
        SettingsRow(Icons.Outlined.NotificationsNone, stringResource(R.string.notif_title),
            stringResource(if (permissions.notifications) R.string.notif_on else R.string.notif_off),
            onClick = if (permissions.notifications) null else requestNotifications) {
            if (!permissions.notifications) Text(stringResource(R.string.notif_turn_on), color = scheme.primary, fontWeight = FontWeight.SemiBold)
        }
        Text(stringResource(R.string.status_lines,
            stringResource(if (permissions.telephony) R.string.value_available else R.string.value_unavailable),
            stringResource(if (permissions.sms) R.string.value_granted else R.string.value_not_granted),
            stringResource(if (permissions.notifications) R.string.value_enabled else R.string.value_disabled)),
            style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant, modifier = Modifier.padding(start = 40.dp))
        notice?.let { Text(stringResource(it), style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(start = 40.dp)) }
        HorizontalDivider(color = edge)
        SettingsRow(Icons.Outlined.NotificationAdd, stringResource(R.string.test_notification), onClick = { notice = sendTestNotification(context) })
        HorizontalDivider(color = edge)
        SettingsRow(Icons.AutoMirrored.Outlined.HelpOutline, stringResource(R.string.why_title), onClick = { vm.navigate(Screen.HELP) }) {
            Icon(Icons.Outlined.ChevronRight, null, tint = scheme.onSurfaceVariant)
        }
    }
    SectionLabel(stringResource(R.string.section_preferences))
    GlassSurface(Modifier.fillMaxWidth(), padding = 12.dp) {
        SettingsRow(Icons.Outlined.Palette, stringResource(R.string.theme_title))
        Box(Modifier.padding(start = 40.dp)) {
            ThemePicker(preferences.themeMode) { mode -> scope.launch { app.preferences.themeMode(mode) } }
        }
        HorizontalDivider(color = edge)
        SettingsRow(Icons.Outlined.Translate, stringResource(R.string.language_title))
        Box(Modifier.padding(start = 40.dp)) { LanguagePicker() }
        HorizontalDivider(color = edge)
        val reduceCd = stringResource(R.string.reduce_title)
        SettingsRow(Icons.Outlined.Contrast, stringResource(R.string.reduce_title), stringResource(R.string.reduce_body)) {
            Switch(preferences.reduceTransparency, { on -> scope.launch { app.preferences.reduceTransparency(on) } },
                modifier = Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp).semantics { contentDescription = reduceCd })
        }
        HorizontalDivider(color = edge)
        SettingsRow(Icons.AutoMirrored.Outlined.OpenInNew, stringResource(R.string.android_settings), onClick = { context.openSettings(appInfo(context)) })
    }
    SectionLabel(stringResource(R.string.section_privacy))
    GlassSurface(Modifier.fillMaxWidth(), padding = 12.dp) {
        SettingsRow(Icons.Outlined.Policy, stringResource(R.string.privacy_notice_row), onClick = { vm.navigate(Screen.PRIVACY) }) {
            Icon(Icons.Outlined.ChevronRight, null, tint = scheme.onSurfaceVariant)
        }
        HorizontalDivider(color = edge)
        Column(Modifier.padding(horizontal = 4.dp, vertical = 8.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(stringResource(R.string.local_title), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
            Text(stringResource(R.string.local_body))
            Text(stringResource(R.string.local_limits), style = MaterialTheme.typography.bodySmall, color = scheme.onSurfaceVariant)
        }
    }
    GlassButton(stringResource(R.string.clear_button), { clearDialog = true }, primary = false, icon = Icons.Outlined.DeleteOutline)
    if (consentDialog) AlertDialog(onDismissRequest = { consentDialog = false }, icon = { Icon(Icons.Outlined.Sms, null) },
        title = { Text(stringResource(R.string.consent_title)) }, text = { Text(stringResource(R.string.consent_body)) },
        confirmButton = { TextButton(onClick = {
            consentDialog = false
            if (permissions.sms) scope.launch { app.preferences.scanning(true) } else smsRequest.launch(Manifest.permission.RECEIVE_SMS)
        }) { Text(stringResource(R.string.consent_agree)) } },
        dismissButton = { TextButton(onClick = { consentDialog = false }) { Text(stringResource(R.string.consent_keep_off)) } })
    if (clearDialog) AlertDialog(onDismissRequest = { clearDialog = false }, title = { Text(stringResource(R.string.clear_title)) },
        text = { Text(stringResource(R.string.clear_body)) },
        confirmButton = { TextButton(onClick = { clearDialog = false; ph.smishguard.sms.SmsReportGroup.clear(context); PendingChecks.clear(); scope.launch { app.preferences.clear(); clear() } }) { Text(stringResource(R.string.clear_confirm)) } },
        dismissButton = { TextButton(onClick = { clearDialog = false }) { Text(stringResource(R.string.cancel)) } })
}

private enum class HelpStatus { OK, FIX, INFO }

@Composable private fun HelpItem(status: HelpStatus, title: String, body: String, action: Pair<String, () -> Unit>? = null) {
    val dark = LocalGlass.current.dark
    val (color, label, icon) = when (status) {
        HelpStatus.OK -> Triple(if (dark) Verdict.safeDark else Verdict.safe, stringResource(R.string.help_ok), Icons.Outlined.CheckCircle)
        HelpStatus.FIX -> Triple(if (dark) Verdict.cautionDark else Verdict.caution, stringResource(R.string.help_fix), Icons.Outlined.ReportProblem)
        HelpStatus.INFO -> Triple(MaterialTheme.colorScheme.onSurfaceVariant, stringResource(R.string.help_info), Icons.Outlined.Info)
    }
    GlassSurface(Modifier.fillMaxWidth(), padding = 16.dp) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(title, Modifier.weight(1f), style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
            StatusPill(label, icon, color)
        }
        Text(body)
        action?.let { (text, onClick) -> GlassButton(text, onClick, primary = false) }
    }
}

private enum class PhoneBrand(val display: String, @param:StringRes val steps: Int) {
    XIAOMI("Xiaomi / Redmi / POCO", R.string.autostart_xiaomi), OPPO("OPPO / realme / OnePlus", R.string.autostart_oppo),
    VIVO("vivo / iQOO", R.string.autostart_vivo), HUAWEI("Huawei / Honor", R.string.autostart_huawei),
    SAMSUNG("Samsung", R.string.autostart_samsung), OTHER("", R.string.autostart_other);
    companion object {
        fun detect(): PhoneBrand = Build.MANUFACTURER.lowercase(Locale.ROOT).let { m ->
            when {
                listOf("xiaomi", "redmi", "poco").any { it in m } -> XIAOMI
                listOf("oppo", "realme", "oneplus").any { it in m } -> OPPO
                listOf("vivo", "iqoo").any { it in m } -> VIVO
                listOf("huawei", "honor").any { it in m } -> HUAWEI
                "samsung" in m -> SAMSUNG
                else -> OTHER
            }
        }
    }
}

@Composable private fun ColumnScope.HelpScreen(app: SmishGuardApp, preferences: Preferences, permissions: PermissionState, vm: CheckViewModel) {
    val context = LocalContext.current
    var notice by remember { mutableStateOf<Int?>(null) }
    var refreshTick by remember { mutableIntStateOf(0) }
    val requestNotifications = rememberNotificationRequest { refreshTick++ }
    val checkChannelOn = remember(permissions, refreshTick) {
        app.getSystemService(NotificationManager::class.java).getNotificationChannel(CheckPrompt.CHANNEL)?.importance != NotificationManager.IMPORTANCE_NONE
    }
    val batteryOk = remember(permissions, refreshTick) {
        app.getSystemService(PowerManager::class.java)?.isIgnoringBatteryOptimizations(app.packageName) == true
    }
    BackLink(stringResource(R.string.back)) { vm.navigate(Screen.SETTINGS) }
    Heading(stringResource(R.string.why_title))
    Text(stringResource(R.string.help_intro))
    HelpItem(if (permissions.sms) HelpStatus.OK else HelpStatus.FIX, stringResource(R.string.help_sms_title),
        stringResource(if (permissions.sms) R.string.help_sms_ok else R.string.help_sms_bad),
        if (permissions.sms) null else stringResource(R.string.help_open_app) to { context.openSettings(appInfo(context)) })
    val scanning = preferences.scanning && permissions.active(true)
    HelpItem(if (scanning) HelpStatus.OK else HelpStatus.FIX, stringResource(R.string.help_scan_title),
        stringResource(if (scanning) R.string.help_scan_ok else R.string.help_scan_bad),
        if (scanning) null else stringResource(R.string.nav_settings) to { vm.navigate(Screen.SETTINGS) })
    val notificationsOk = permissions.notifications && checkChannelOn
    HelpItem(if (notificationsOk) HelpStatus.OK else HelpStatus.FIX, stringResource(R.string.help_notif_title),
        stringResource(if (notificationsOk) R.string.help_notif_ok else R.string.help_notif_bad),
        if (notificationsOk) null else stringResource(R.string.help_open_notifications) to requestNotifications)
    HelpItem(if (batteryOk) HelpStatus.OK else HelpStatus.FIX, stringResource(R.string.help_battery_title),
        stringResource(if (batteryOk) R.string.help_battery_ok else R.string.help_battery_bad),
        stringResource(R.string.help_open_battery) to { context.openSettings(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS), appInfo(context)) })
    val brand = PhoneBrand.detect()
    HelpItem(HelpStatus.INFO, stringResource(R.string.help_autostart_title, if (brand == PhoneBrand.OTHER) Build.MANUFACTURER else brand.display),
        stringResource(brand.steps), stringResource(R.string.help_open_app) to { context.openSettings(appInfo(context)) })
    var others by remember { mutableStateOf(false) }
    TextButton({ others = !others }, Modifier.heightIn(min = 48.dp)) {
        Text(stringResource(R.string.help_other_brands)); Icon(if (others) Icons.Outlined.ExpandLess else Icons.Outlined.ExpandMore, null)
    }
    AnimatedVisibility(others) {
        GlassSurface(Modifier.fillMaxWidth(), padding = 16.dp) {
            PhoneBrand.entries.filter { it != brand && it != PhoneBrand.OTHER }.forEach {
                Text(it.display, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
                Text(stringResource(it.steps), style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
    HelpItem(HelpStatus.INFO, stringResource(R.string.help_forcestop_title), stringResource(R.string.help_forcestop_body))
    if (Build.VERSION.SDK_INT >= 33) HelpItem(HelpStatus.INFO, stringResource(R.string.help_restricted_title), stringResource(R.string.help_restricted_body),
        stringResource(R.string.help_open_app) to { context.openSettings(appInfo(context)) })
    HelpItem(HelpStatus.INFO, stringResource(R.string.help_rcs_title), stringResource(R.string.help_rcs_body))
    Text(stringResource(R.string.help_test_body))
    GlassButton(stringResource(R.string.test_notification), { notice = sendTestNotification(context) }, icon = Icons.Outlined.NotificationAdd)
    notice?.let { Text(stringResource(it), style = MaterialTheme.typography.bodySmall) }
}
