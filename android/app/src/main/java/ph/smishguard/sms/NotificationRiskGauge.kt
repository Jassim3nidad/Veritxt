package ph.smishguard.sms

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Typeface
import kotlin.math.cos
import kotlin.math.sin

/** Original vector-drawn dial. The needle maps the existing evidence index, never a probability. */
object NotificationRiskGauge {
    fun render(score: Int?): Bitmap {
        require(score == null || score in 0..100)
        val bitmap = Bitmap.createBitmap(256, 256, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG)
        val cx = 128f
        val cy = 119f
        // An opaque face keeps the dark pointer legible on light and dark notification surfaces.
        paint.color = Color.rgb(250, 250, 250)
        canvas.drawCircle(cx, cy, 118f, paint)
        paint.style = Paint.Style.STROKE
        paint.strokeWidth = 30f
        val ring = RectF(29f, 20f, 227f, 218f)
        if (score == null) {
            paint.color = Color.rgb(161, 167, 171)
            canvas.drawArc(ring, 135f, 270f, false, paint)
        } else {
            // Color transitions at 30 and 70 exactly match the Low/Medium/High thresholds.
            val bands = listOf(
                Triple(0, 15, 0xFF19B96A.toInt()), Triple(15, 30, 0xFF8CCB16.toInt()),
                Triple(30, 50, 0xFFF4CB20.toInt()), Triple(50, 70, 0xFFFF9424.toInt()),
                Triple(70, 85, 0xFFFA5738.toInt()), Triple(85, 100, 0xFFE52F45.toInt())
            )
            for ((start, end, color) in bands) {
                paint.color = color
                canvas.drawArc(ring, 135f + start * 2.7f, (end - start) * 2.7f, false, paint)
            }
        }
        paint.style = Paint.Style.FILL
        paint.color = Color.rgb(43, 49, 50)
        if (score != null) {
            val angle = Math.toRadians(135.0 + score * 2.7)
            val dx = cos(angle).toFloat()
            val dy = sin(angle).toFloat()
            val needle = Path().apply {
                moveTo(cx + dx * 89f, cy + dy * 89f)
                lineTo(cx - dy * 9f - dx * 9f, cy + dx * 9f - dy * 9f)
                lineTo(cx + dy * 9f - dx * 9f, cy - dx * 9f - dy * 9f)
                close()
            }
            canvas.drawPath(needle, paint)
            canvas.drawCircle(cx, cy, 17f, paint)
        } else {
            // No pointer or zero-like score for an unavailable assessment.
            paint.textAlign = Paint.Align.CENTER
            paint.typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            paint.textSize = 60f
            canvas.drawText("?", cx, cy + 20f, paint)
        }
        paint.textAlign = Paint.Align.CENTER
        paint.typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
        paint.textSize = 32f
        canvas.drawText(score?.let { "$it/100" } ?: "—", cx, 234f, paint)
        return bitmap
    }
}
