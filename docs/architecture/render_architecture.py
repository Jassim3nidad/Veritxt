"""Render the source-traced Veritxt architecture as SVG and a high-resolution PNG."""
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
W, H, SCALE = 1800, 1420, 2
image = Image.new("RGB", (W * SCALE, H * SCALE), "#f8fafc")
draw = ImageDraw.Draw(image)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<title>Veritxt system architecture</title>',
       '<desc>Offline Android SMS inference, separate research and packaging, and a disconnected Flask reporting prototype. Based on code inspected 19 October 2026.</desc>',
       '<rect width="1800" height="1420" fill="#f8fafc"/>']
FONT = Path("C:/Windows/Fonts")


def text(x, y, value, size=19, color="#334155", bold=False):
    font = ImageFont.truetype(str(FONT / ("segoeuib.ttf" if bold else "segoeui.ttf")), size * SCALE)
    draw.text((x * SCALE, y * SCALE), value, font=font, fill=color)
    svg.append(f'<text x="{x}" y="{y}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}" dominant-baseline="text-before-edge">{escape(value)}</text>')


def rect(x, y, w, h, fill, stroke, radius=16):
    draw.rounded_rectangle((x*SCALE, y*SCALE, (x+w)*SCALE, (y+h)*SCALE), radius*SCALE, fill=fill, outline=stroke, width=2*SCALE)
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')


def box(x, y, w, h, title, lines, theme="green"):
    fill, stroke, ink = {
        "green": ("#ffffff", "#8ab8aa", "#185c4d"),
        "blue": ("#ffffff", "#a0b6e0", "#304f87"),
        "gray": ("#ffffff", "#c4c7d0", "#505563"),
    }[theme]
    rect(x, y, w, h, fill, stroke)
    text(x+18, y+14, title, 21, ink, True)
    for i, line in enumerate(lines):
        text(x+18, y+48+i*25, line, 18)


def arrow(points, color="#437c6e", dashed=False):
    # Orthogonal polylines; SVG and PNG share the same coordinates.
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if dashed:
            length = abs(x2-x1) + abs(y2-y1)
            for start in range(0, int(length), 14):
                end = min(start+8, length)
                t1, t2 = start/length, end/length
                draw.line(((x1+(x2-x1)*t1)*SCALE, (y1+(y2-y1)*t1)*SCALE,
                           (x1+(x2-x1)*t2)*SCALE, (y1+(y2-y1)*t2)*SCALE), fill=color, width=3*SCALE)
        else:
            draw.line((x1*SCALE,y1*SCALE,x2*SCALE,y2*SCALE), fill=color, width=3*SCALE)
    x, y = points[-1]
    px, py = points[-2]
    dx, dy = (0 if x == px else (1 if x > px else -1)), (0 if y == py else (1 if y > py else -1))
    triangle = [(x,y), (x-dx*10+dy*5,y-dy*10-dx*5), (x-dx*10-dy*5,y-dy*10+dx*5)]
    draw.polygon([(a*SCALE,b*SCALE) for a,b in triangle], fill=color)
    coords = " ".join(f"{a},{b}" for a,b in points)
    dash = ' stroke-dasharray="8 6"' if dashed else ''
    svg.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="3"{dash}/>')
    svg.append(f'<polygon points="{" ".join(f"{a},{b}" for a,b in triangle)}" fill="{color}"/>')


text(40, 32, "Veritxt", 42, "#123f35", True)
text(215, 42, "System architecture", 32, "#1e293b", True)
text(40, 98, "Code-based view  |  19 October 2026  |  selectedSvm inference path", 21)
text(40, 132, "Solid arrows: local processing    Dashed arrow: build-time delivery    Backend: separate prototype", 18, "#64748b")

rect(40, 180, 350, 970, "#edf2fc", "#bcccea", 22)
text(65, 204, "DEVELOPMENT COMPUTER", 21, "#304f87", True)
text(65, 238, "Research + APK packaging", 18)
rect(430, 180, 1330, 970, "#edf7f3", "#afcec2", 22)
text(465, 204, "ANDROID DEVICE / VERITXT", 23, "#185c4d", True)
text(465, 242, "Kotlin + Jetpack Compose  |  Offline inference  |  English / Filipino", 20)
text(1310, 242, "No prediction-server connection", 18, "#185c4d")

# Research pipeline.
box(65, 290, 300, 110, "Private SMS data", ["Source / label review", "Preparation + grouped splits"], "blue")
box(65, 455, 300, 135, "Python experiments", ["LR / Multinomial NB / SVM", "mBERT fine-tuning", "Evaluation + threshold policy"], "blue")
box(65, 650, 300, 135, "Frozen export", ["Model + preprocessing contract", "Reference / JVM / Android", "feature and score parity"], "blue")
box(65, 870, 300, 135, "Gradle build variant", ["Asset validation + APK", "selectedSvm: model.json", "+ raw-sms-adapter.json"], "blue")
arrow([(215,400),(215,455)], "#526db2")
arrow([(215,590),(215,650)], "#526db2")
arrow([(215,785),(215,870)], "#526db2")
text(65, 1040, "Models train on the computer.", 18, "#304f87")
text(65, 1070, "New candidates stay separate", 18, "#304f87")
text(65, 1098, "until explicitly integrated.", 18, "#304f87")

# Device inputs and their coordinators.
box(465, 300, 350, 110, "Manual / shared text", ["Type / paste SMS", "Android ACTION_SEND → MainActivity"])
box(905, 300, 350, 110, "Local preferences", ["DataStore: privacy + scanning consent", "Onboarding + reduced transparency"])
box(1345, 300, 380, 110, "New incoming SMS", ["Android SMS_RECEIVED broadcast", "Multipart body + sender metadata"])
box(465, 475, 350, 110, "CheckViewModel", ["StateFlow + transient session", "Scan job / cancellation / timeout"])
box(905, 475, 350, 110, "SmishGuardApp", ["Cached build-specific detector", "Input-kind gate + inference mutex"])
box(1345, 475, 380, 110, "IncomingSmsReceiver", ["Privacy + scanning + SMS permission", "Auto-warning gate / neutral prompt"])
arrow([(640,410),(640,475)])
arrow([(1535,410),(1535,475)])
arrow([(815,530),(905,530)])
arrow([(1345,530),(1255,530)])
arrow([(1180,410),(1180,442),(1535,442),(1535,475)])
text(955, 422, "consent gates incoming checks", 16, "#43675e")

# Shared inference and shared policy are distinct stages.
box(590, 635, 1000, 120, "Packaged selectedSvm detector", [
    "RawSmsView masking → Unicode tokens / stopwords → word unigram + bigram TF-IDF / L2",
    "Linear SVM → fitted sigmoid → saved threshold; assessability and model-error states"])
arrow([(1080,585),(1080,635)])
arrow([(365,935),(550,935),(550,695),(590,695)], "#526db2", True)
text(397, 910, "APK assets", 16, "#304f87")
box(590, 815, 1000, 115, "Shared RiskPolicy", [
    "Original-text indicators + usable suspicious model signal → evidence index (not probability)",
    "Low 0–29  |  Medium 30–69  |  High 70–100  |  Unable to assess: no score"])
arrow([(1090,755),(1090,815)])

box(465, 1000, 350, 105, "Result screen", ["Risk + indicators + limitations", "Temporary checked-message preview"])
box(905, 1000, 350, 105, "Private SMS notifications", ["High Risk warning / neutral prompt", "Generic text; permission + channel gate"])
box(1345, 1000, 380, 105, "Android blocklist handoff", ["Explicit user confirmation + entry", "Settings UI / fallback instructions"])
arrow([(765,930),(765,965),(640,965),(640,1000)])
arrow([(1080,930),(1080,1000)])
text(1100, 948, "incoming branch", 16, "#43675e")
arrow([(1725,530),(1742,530),(1742,970),(1280,970),(1280,1040),(1255,1040)])
text(1345, 941, "auto warnings off → neutral prompt", 16, "#43675e")
arrow([(640,1105),(640,1128),(1535,1128),(1535,1105)])
text(850, 1105, "eligible result → user requests blocking", 16, "#43675e")

# Isolated prototype: deliberately no Android-to-backend arrow.
rect(40, 1190, 1720, 180, "#f0f1f5", "#c4c7d0", 20)
text(65, 1207, "SEPARATE LOCAL PROTOTYPE / DISCONNECTED FROM ANDROID", 21, "#505563", True)
box(65, 1252, 460, 95, "Android reporting disabled", ["DisabledReportingRepository; no INTERNET"], "gray")
box(680, 1252, 300, 95, "Flask report API", ["POST /api/reports + validation"], "gray")
box(1065, 1252, 230, 95, "SQLite", ["Report metadata"], "gray")
box(1380, 1252, 345, 95, "Aggregate dashboard", ["Flask GET / → HTML"], "gray")
arrow([(980,1300),(1065,1300)], "#85858e")
arrow([(1295,1300),(1380,1300)], "#85858e")
text(40, 1385, "Messages: transient app memory  |  Pending notification checks: single-use IDs, 10-minute expiry  |  No persistent scan history", 18, "#64748b")

svg.append("</svg>")
(OUT / "veritxt-system-architecture.svg").write_text("\n".join(svg), encoding="utf-8")
image.save(OUT / "veritxt-system-architecture.png", optimize=True)
print(f"Rendered SVG and {W*SCALE} x {H*SCALE} PNG in {OUT}")
