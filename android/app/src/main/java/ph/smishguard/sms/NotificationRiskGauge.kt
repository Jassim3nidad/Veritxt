package ph.smishguard.sms

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Typeface
import ph.smishguard.model.RiskLevel
import ph.smishguard.model.RiskPolicy

/** Shield and level pips for the existing risk band. Glyph and pips keep it readable without color. */
object NotificationRiskGauge {
    private enum class Glyph { CROSS, ALERT, PLAIN, UNKNOWN }
    private class Style(val tile: Int, val glyph: Glyph, val pips: Int)

    fun render(score: Int?): Bitmap {
        require(score == null || score in 0..100)
        val style = when (score?.let(RiskPolicy::classify)) {
            RiskLevel.HIGH -> Style(0xFFB3261E.toInt(), Glyph.CROSS, 3)
            RiskLevel.MEDIUM -> Style(0xFF8A5700.toInt(), Glyph.ALERT, 2)
            RiskLevel.LOW -> Style(0xFF5B6B66.toInt(), Glyph.PLAIN, 1)
            RiskLevel.UNABLE_TO_ASSESS, null -> Style(0xFF5F6368.toInt(), Glyph.UNKNOWN, 0)
        }
        val bitmap = Bitmap.createBitmap(256, 256, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG)
        // Opaque tile, so the badge reads the same on light and dark notification surfaces.
        paint.color = style.tile
        canvas.drawRoundRect(RectF(0f, 0f, 256f, 256f), 58f, 58f, paint)
        paint.color = Color.WHITE
        canvas.drawPath(Path().apply {
            moveTo(128f, 30f)
            cubicTo(146f, 44f, 168f, 52f, 192f, 54f)
            lineTo(192f, 108f)
            cubicTo(192f, 146f, 166f, 172f, 128f, 188f)
            cubicTo(90f, 172f, 64f, 146f, 64f, 108f)
            lineTo(64f, 54f)
            cubicTo(88f, 52f, 110f, 44f, 128f, 30f)
            close()
        }, paint)
        drawGlyph(canvas, paint, style)
        for (i in 0 until 3) {
            paint.color = if (i < style.pips) Color.WHITE else Color.argb(90, 255, 255, 255)
            canvas.drawCircle(94f + i * 34f, 216f, 11f, paint)
        }
        return bitmap
    }

    private fun drawGlyph(canvas: Canvas, paint: Paint, style: Style) {
        paint.color = style.tile
        paint.strokeCap = Paint.Cap.ROUND
        paint.strokeWidth = 18f
        paint.style = Paint.Style.STROKE
        when (style.glyph) {
            Glyph.CROSS -> {
                canvas.drawLine(104f, 80f, 152f, 128f, paint)
                canvas.drawLine(152f, 80f, 104f, 128f, paint)
            }
            Glyph.ALERT -> {
                canvas.drawLine(128f, 74f, 128f, 114f, paint)
                paint.style = Paint.Style.FILL
                canvas.drawCircle(128f, 144f, 11f, paint)
            }
            Glyph.UNKNOWN -> {
                paint.style = Paint.Style.FILL
                paint.textAlign = Paint.Align.CENTER
                paint.typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
                paint.textSize = 88f
                canvas.drawText("?", 128f, 138f, paint)
            }
            Glyph.PLAIN -> Unit
        }
        paint.style = Paint.Style.FILL
    }
}
