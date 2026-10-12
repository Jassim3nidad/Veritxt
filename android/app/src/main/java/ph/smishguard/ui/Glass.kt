package ph.smishguard.ui

import android.os.Build
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import dev.chrisbanes.haze.HazeState
import dev.chrisbanes.haze.HazeStyle
import dev.chrisbanes.haze.HazeTint
import dev.chrisbanes.haze.hazeEffect

/** Glass tokens. `solid` = reduce transparency (user setting) for maximum legibility. */
data class GlassStyle(val dark: Boolean, val solid: Boolean) {
    val fill get() = when {
        solid -> if (dark) Color(0xFF1E2A25) else Color(0xFFFFFFFF)
        // API 26-30 has no blur, so panels are more opaque to keep text readable over the background.
        Build.VERSION.SDK_INT < 31 -> if (dark) Color(0xD91B2621) else Color(0xD9FFFFFF)
        else -> if (dark) Color(0x991B2621) else Color(0xA6FFFFFF)
    }
    /** Nav bar tint over Haze blur (API 31+). Strong enough for AA-contrast labels over any content. */
    val barTint get() = if (dark) Color(0xB8182320) else Color(0xBFFAFCFB)
    /** Nav bar without blur (API 26-30, or Reduce transparency): opaque so scrolled content can't show through. */
    val barFill get() = if (dark) Color(0xFF182320) else Color(0xFFFAFCFB)
    val blurAvailable get() = !solid && Build.VERSION.SDK_INT >= 31
    val edge get() = if (solid) (if (dark) Color(0xFF34453D) else Color(0xFFD5DED8))
        else if (dark) Color(0x40FFFFFF) else Color(0xCCFFFFFF)
    val edgeLow get() = if (solid) edge else if (dark) Color(0x14FFFFFF) else Color(0x33FFFFFF)
}
val LocalGlass = staticCompositionLocalOf { GlassStyle(dark = false, solid = false) }

object Verdict {
    val danger = Color(0xFFB3261E); val dangerDark = Color(0xFFFFB4AB)
    val caution = Color(0xFF8A5A00); val cautionDark = Color(0xFFFFCF7A)
    val safe = Color(0xFF2E6B3A); val safeDark = Color(0xFF9BD7A6)
}

/** Soft, slowly drifting colour field behind every screen. Blurred on API 31+, soft gradients below. */
@Composable fun GlassBackground(modifier: Modifier = Modifier) {
    val style = LocalGlass.current
    val base = if (style.dark) Color(0xFF0E1613) else Color(0xFFF2F6F3)
    val shift by rememberInfiniteTransition(label = "bg").animateFloat(0f, 1f,
        infiniteRepeatable(tween(14000, easing = LinearEasing), RepeatMode.Reverse), label = "drift")
    val blobs = if (style.dark) listOf(Color(0xFF1F5B4D), Color(0xFF274B63), Color(0xFF3B5A2E))
        else listOf(Color(0xFF9FD8C4), Color(0xFFB9D7EE), Color(0xFFD7EBC0))
    Box(modifier.fillMaxSize().background(base)) {
        if (!style.solid) Canvas(Modifier.fillMaxSize().then(if (Build.VERSION.SDK_INT >= 31) Modifier.blur(48.dp) else Modifier)) {
            val w = size.width; val h = size.height
            listOf(Offset(w * (.15f + .2f * shift), h * .12f), Offset(w * (.9f - .15f * shift), h * .45f),
                Offset(w * (.3f + .1f * shift), h * .88f)).forEachIndexed { i, c ->
                val r = w * (.55f + .1f * i)
                drawCircle(Brush.radialGradient(listOf(blobs[i].copy(alpha = .75f), Color.Transparent), c, r), r, c)
            }
        }
    }
}

@Composable fun GlassSurface(modifier: Modifier = Modifier, shape: Shape = RoundedCornerShape(28.dp), tint: Color? = null,
                             padding: Dp = 20.dp, fill: Color? = null, effect: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    val style = LocalGlass.current
    Column(modifier.clip(shape).then(effect).background(tint?.let { it.copy(alpha = if (style.solid) .18f else .14f).compositeOver(style.fill) } ?: fill ?: style.fill)
        .border(BorderStroke(1.dp, Brush.verticalGradient(listOf(style.edge, style.edgeLow))), shape).padding(padding),
        verticalArrangement = Arrangement.spacedBy(10.dp), content = content)
}

private fun Color.compositeOver(bg: Color): Color {
    val a = alpha + bg.alpha * (1 - alpha)
    fun ch(f: Color.() -> Float) = (f(this) * alpha + f(bg) * bg.alpha * (1 - alpha)) / a
    return Color(ch { red }, ch { green }, ch { blue }, a)
}

@Composable fun GlassButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier, primary: Boolean = true,
                            enabled: Boolean = true, icon: ImageVector? = null, leading: (@Composable () -> Unit)? = null) {
    val scheme = MaterialTheme.colorScheme
    val style = LocalGlass.current
    val shape = RoundedCornerShape(50)
    val colors = if (primary) ButtonDefaults.buttonColors(containerColor = scheme.primary.copy(alpha = if (style.solid) 1f else .92f))
        else ButtonDefaults.outlinedButtonColors(containerColor = style.fill, contentColor = scheme.onSurface)
    Button(onClick, modifier.fillMaxWidth().heightIn(min = 56.dp), enabled = enabled, shape = shape, colors = colors,
        border = if (primary) BorderStroke(1.dp, Color.White.copy(alpha = .25f)) else BorderStroke(1.dp, style.edge),
        contentPadding = PaddingValues(horizontal = 24.dp, vertical = 14.dp)) {
        leading?.invoke()
        if (icon != null) { Icon(icon, null, Modifier.size(20.dp)); Spacer(Modifier.width(10.dp)) }
        Text(text, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
    }
}

data class NavItem<T>(val key: T, val label: String, val icon: ImageVector)

/** Floating pill navigation; the active tab gets a brighter glass "lens". */
/**
 * Floating pill navigation; the active tab gets a brighter glass "lens". With [haze] on API 31+ the content
 * scrolling underneath is really blurred (Haze); otherwise the bar is opaque.
 */
@Composable fun <T> GlassNavBar(items: List<NavItem<T>>, selected: T, onSelect: (T) -> Unit, modifier: Modifier = Modifier, haze: HazeState? = null) {
    val style = LocalGlass.current
    val scheme = MaterialTheme.colorScheme
    val blur = haze != null && style.blurAvailable
    GlassSurface(modifier.padding(horizontal = 24.dp, vertical = 12.dp).navigationBarsPadding().fillMaxWidth(),
        shape = RoundedCornerShape(50), padding = 6.dp, fill = if (blur) Color.Transparent else style.barFill,
        effect = if (blur) Modifier.hazeEffect(haze!!, HazeStyle(backgroundColor = if (style.dark) Color(0xFF0E1613) else Color(0xFFF2F6F3),
            tint = HazeTint(style.barTint), blurRadius = 24.dp, noiseFactor = 0f)) else Modifier) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            items.forEach { item ->
                val active = item.key == selected
                val lens by animateColorAsState(if (active) scheme.primary.copy(alpha = if (style.dark) .28f else .16f) else Color.Transparent, label = "lens")
                Column(Modifier.weight(1f).clip(RoundedCornerShape(50)).background(lens)
                    .clickable(role = Role.Tab) { onSelect(item.key) }.semantics { this.selected = active }
                    .heightIn(min = 56.dp).padding(vertical = 8.dp), horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center) {
                    Icon(item.icon, null, Modifier.size(22.dp).clearAndSetSemantics { },
                        tint = if (active) scheme.primary else scheme.onSurfaceVariant)
                    Text(item.label, style = MaterialTheme.typography.labelMedium,
                        color = if (active) scheme.primary else scheme.onSurfaceVariant,
                        fontWeight = if (active) FontWeight.SemiBold else FontWeight.Normal)
                }
            }
        }
    }
}

@Composable fun StatusPill(text: String, icon: ImageVector, color: Color) {
    val style = LocalGlass.current
    Row(Modifier.clip(RoundedCornerShape(50)).background(color.copy(alpha = if (style.dark) .22f else .13f))
        .border(1.dp, color.copy(alpha = .35f), RoundedCornerShape(50)).padding(horizontal = 12.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        Icon(icon, null, Modifier.size(16.dp).clearAndSetSemantics { }, tint = color)
        Text(text, style = MaterialTheme.typography.labelLarge, color = color)
    }
}

@Composable fun ScoreBar(score: Double, color: Color) {
    val target = score.coerceIn(0.0, 1.0).toFloat()
    val anim = remember { Animatable(0f) }
    LaunchedEffect(target) { anim.animateTo(target, spring(dampingRatio = .8f, stiffness = Spring.StiffnessLow)) }
    Box(Modifier.fillMaxWidth().height(10.dp).clip(RoundedCornerShape(50)).background(color.copy(alpha = .18f))) {
        Box(Modifier.fillMaxWidth(anim.value).fillMaxHeight().clip(RoundedCornerShape(50)).background(color))
    }
}
