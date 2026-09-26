package ph.smishguard

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.interaction.collectIsPressedAsState
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

internal val NeoMint = Color(0xFFBAF4DB)
internal val NeoYellow = Color(0xFFFFE69A)
internal val NeoCoral = Color(0xFFFFB7A6)
private val Ink = Color(0xFF17151D)
private val Violet = Color(0xFF6840C6)
private val Lime = Color(0xFFD9FA70)

@Composable internal fun NeoTheme(content: @Composable () -> Unit) {
    val dark = isSystemInDarkTheme()
    val colors = if (dark) darkColorScheme(
        primary = Color(0xFFCAB5FF), onPrimary = Ink,
        background = Color(0xFF19171F), surface = Color(0xFF26232E),
        onSurface = Color(0xFFFFF9ED), onBackground = Color(0xFFFFF9ED),
        secondaryContainer = Color(0xFF564475), onSecondaryContainer = Color.White
    ) else lightColorScheme(
        primary = Violet, onPrimary = Color.White,
        background = Color(0xFFFFF9ED), surface = Color(0xFFFFFEF9),
        onSurface = Ink, onBackground = Ink,
        secondaryContainer = Color(0xFFDDCFFF), onSecondaryContainer = Ink
    )
    MaterialTheme(colorScheme = colors, shapes = Shapes(
        extraSmall = RoundedCornerShape(6.dp), small = RoundedCornerShape(8.dp),
        medium = RoundedCornerShape(12.dp), large = RoundedCornerShape(16.dp),
        extraLarge = RoundedCornerShape(20.dp)), content = content)
}

internal fun Modifier.neoOutline() = drawBehind {
    drawLine(Ink, Offset.Zero, Offset(size.width, 0f), 3.dp.toPx())
}

@Composable internal fun NeoCard(modifier: Modifier = Modifier, tone: Color = NeoMint, content: @Composable ColumnScope.() -> Unit) {
    Card(modifier.padding(end = 4.dp, bottom = 4.dp).drawBehind {
        drawRoundRect(Ink, topLeft = Offset(4.dp.toPx(), 4.dp.toPx()), size = size, cornerRadius = CornerRadius(12.dp.toPx()))
    }, shape = RoundedCornerShape(12.dp), border = BorderStroke(2.dp, Ink),
        colors = CardDefaults.cardColors(containerColor = tone, contentColor = Ink), content = content)
}

@Composable internal fun NeoButton(onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true, content: @Composable RowScope.() -> Unit) {
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val focused by interaction.collectIsFocusedAsState()
    val focusColor = MaterialTheme.colorScheme.primary
    Button(onClick, modifier.padding(end = 4.dp, bottom = 4.dp).heightIn(min = 52.dp)
        .offset(x = if (pressed) 3.dp else 0.dp, y = if (pressed) 3.dp else 0.dp)
        .drawBehind {
            if (!pressed) drawRoundRect(Ink, topLeft = Offset(4.dp.toPx(), 4.dp.toPx()), size = size, cornerRadius = CornerRadius(10.dp.toPx()))
            if (focused) drawRoundRect(focusColor, topLeft = Offset(-4.dp.toPx(), -4.dp.toPx()), size = size.copy(width = size.width + 8.dp.toPx(), height = size.height + 8.dp.toPx()), cornerRadius = CornerRadius(14.dp.toPx()), style = Stroke(3.dp.toPx()))
        }, enabled = enabled, shape = RoundedCornerShape(10.dp), border = BorderStroke(2.dp, Ink),
        colors = ButtonDefaults.buttonColors(containerColor = Lime, contentColor = Ink), interactionSource = interaction) {
        ProvideTextStyle(MaterialTheme.typography.labelLarge.copy(fontWeight = FontWeight.Bold), content = { content() })
    }
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

@Composable internal fun NeoSecondaryButton(onClick: () -> Unit, modifier: Modifier = Modifier, content: @Composable RowScope.() -> Unit) {
    OutlinedButton(onClick, modifier.heightIn(min = 48.dp), shape = RoundedCornerShape(10.dp),
        border = BorderStroke(2.dp, MaterialTheme.colorScheme.onSurface), content = content)
}
