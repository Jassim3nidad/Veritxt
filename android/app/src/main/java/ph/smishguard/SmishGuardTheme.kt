package ph.smishguard

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/** Neutral surfaces keep message content and the result in focus. */
@Composable internal fun SmishGuardTheme(content: @Composable () -> Unit) {
    val colors = if (isSystemInDarkTheme()) darkColorScheme(
        primary = Color(0xFFF2F1EE), onPrimary = Color(0xFF1B1B1B),
        background = Color(0xFF161616), surface = Color(0xFF161616),
        surfaceContainer = Color(0xFF242424), surfaceVariant = Color(0xFF292929),
        surfaceContainerLowest = Color(0xFF101010), surfaceContainerLow = Color(0xFF202020),
        surfaceContainerHigh = Color(0xFF292929), surfaceContainerHighest = Color(0xFF333333),
        secondary = Color(0xFFC5C4C0), onSecondary = Color(0xFF202020),
        onSurface = Color(0xFFF2F1EE), onBackground = Color(0xFFF2F1EE),
        onSurfaceVariant = Color(0xFFC5C4C0), outline = Color(0xFF93938F), outlineVariant = Color(0xFF3D3D3B),
        secondaryContainer = Color(0xFF303030), onSecondaryContainer = Color(0xFFF2F1EE)
    ) else lightColorScheme(
        primary = Color(0xFF202020), onPrimary = Color.White,
        background = Color(0xFFFCFBF8), surface = Color(0xFFFCFBF8),
        surfaceContainer = Color(0xFFF1F0ED), surfaceVariant = Color(0xFFF1F0ED),
        surfaceContainerLowest = Color.White, surfaceContainerLow = Color(0xFFF7F6F3),
        surfaceContainerHigh = Color(0xFFF1F0ED), surfaceContainerHighest = Color(0xFFE5E4E0),
        secondary = Color(0xFF5B5B57), onSecondary = Color.White,
        onSurface = Color(0xFF202020), onBackground = Color(0xFF202020),
        onSurfaceVariant = Color(0xFF5B5B57), outline = Color(0xFF858580), outlineVariant = Color(0xFFDEDDD8),
        secondaryContainer = Color(0xFFEBEAE6), onSecondaryContainer = Color(0xFF202020)
    )
    MaterialTheme(colorScheme = colors, shapes = Shapes(
        extraSmall = RoundedCornerShape(4.dp), small = RoundedCornerShape(8.dp),
        medium = RoundedCornerShape(12.dp), large = RoundedCornerShape(16.dp),
        extraLarge = RoundedCornerShape(20.dp)), content = content)
}

@Composable internal fun Modifier.navigationDivider(): Modifier {
    val line = MaterialTheme.colorScheme.outlineVariant
    return drawBehind { drawLine(line, Offset.Zero, Offset(size.width, 0f), 1.dp.toPx()) }
}

@Composable internal fun PrimaryAction(onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true, content: @Composable RowScope.() -> Unit) {
    val interaction = remember { MutableInteractionSource() }
    val focused by interaction.collectIsFocusedAsState()
    val focusColor = MaterialTheme.colorScheme.onSurface
    Button(onClick, modifier.heightIn(min = 52.dp).drawBehind {
        if (focused) drawRoundRect(focusColor, topLeft = Offset(-4.dp.toPx(), -4.dp.toPx()),
            size = size.copy(width = size.width + 8.dp.toPx(), height = size.height + 8.dp.toPx()),
            cornerRadius = CornerRadius(12.dp.toPx()), style = Stroke(2.dp.toPx()))
    }, enabled = enabled, shape = RoundedCornerShape(8.dp), interactionSource = interaction) {
        ProvideTextStyle(MaterialTheme.typography.labelLarge.copy(fontWeight = FontWeight.SemiBold), content = { content() })
    }
}

@Composable internal fun SecondaryAction(onClick: () -> Unit, modifier: Modifier = Modifier, content: @Composable RowScope.() -> Unit) {
    OutlinedButton(onClick, modifier.heightIn(min = 48.dp), shape = RoundedCornerShape(8.dp),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline), content = content)
}

/** Vector-like marks avoid device-dependent emoji rendering; tab labels supply semantics. */
@Composable internal fun NavGlyph(screen: Screen) {
    val c = LocalContentColor.current
    androidx.compose.foundation.Canvas(Modifier.size(24.dp).clearAndSetSemantics { }) {
        val stroke = Stroke(2.dp.toPx())
        when (screen) {
            Screen.HOME -> {
                val p = androidx.compose.ui.graphics.Path().apply {
                    moveTo(size.width / 2, 2f); lineTo(size.width - 2, size.height * .42f)
                    lineTo(size.width - 2, size.height - 2); lineTo(2f, size.height - 2)
                    lineTo(2f, size.height * .42f); close()
                }
                drawPath(p, c, style = stroke)
            }
            Screen.CHECK -> {
                drawRoundRect(c, cornerRadius = CornerRadius(3.dp.toPx()), style = stroke)
                drawLine(c, Offset(2f, 3f), Offset(size.width / 2, size.height * .55f), stroke.width)
                drawLine(c, Offset(size.width - 2, 3f), Offset(size.width / 2, size.height * .55f), stroke.width)
            }
            else -> {
                for (row in 1..3) {
                    val y = size.height * row / 4
                    drawLine(c, Offset(0f, y), Offset(size.width, y), stroke.width)
                    drawCircle(c, radius = 3.dp.toPx(), center = Offset(size.width * (if (row == 2) .7f else .3f), y))
                }
            }
        }
    }
}
