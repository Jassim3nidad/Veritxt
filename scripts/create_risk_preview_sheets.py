"""Arrange genuine emulator captures into labeled review sheets; never redraw app content."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def make_sheet(source, output, name, items, columns, note):
    tile_width, tile_height = 300, 667
    margin, gap, label_height, row_gap = 20, 20, 34, 26
    rows = (len(items) + columns - 1) // columns
    width = margin * 2 + columns * tile_width + (columns - 1) * gap
    height = margin * 2 + rows * (label_height + tile_height) + (rows - 1) * row_gap + 30
    canvas = Image.new("RGB", (width, height), "#E8E8E6")
    draw = ImageDraw.Draw(canvas)
    bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 20)
    small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
    for index, (label, filename) in enumerate(items):
        x = margin + (index % columns) * (tile_width + gap)
        y = margin + (index // columns) * (tile_height + label_height + row_gap)
        draw.text((x, y - 3), label, fill="#202525", font=bold)
        with Image.open(source / filename) as image:
            # Only scale and position captures. Dialog crops keep their native proportions.
            size = (tile_width, round(image.height * tile_width / image.width))
            if size[1] > tile_height:
                size = (round(image.width * tile_height / image.height), tile_height)
            thumb = image.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
            canvas.paste(thumb, (x + (tile_width - size[0]) // 2, y + label_height), thumb)
    draw.text((margin, height - 25), note, fill="#535957", font=small)
    canvas.save(output / name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    output = args.directory
    source = output / "screens"
    sheets = [
        ("01-main-screens.png", [("Onboarding", "01-onboarding.png"), ("Home", "02-home.png"),
          ("Check", "03-check.png"), ("Settings", "04-settings.png")], 4,
         "Veritxt · Current Android emulator screens · Selected SVM build"),
        ("02-risk-results.png", [("Low Risk", "06-low-risk.png"), ("Medium Risk", "07-medium-risk.png"),
          ("High Risk", "08-high-risk.png"), ("Unable to Assess", "13-unable-to-assess.png")], 4,
         "Actual installed model · Fictional SMS examples · Scores are evidence indices, not probabilities"),
        ("03-recommendations.png", [("Low Risk: action", "06-low-risk-actions.png"),
          ("Medium Risk: verify", "07-medium-risk-actions.png"), ("High Risk: avoid interaction", "08-high-risk-actions.png")], 3,
         "Genuine scrolled result screens · Blocking remains a user decision"),
        ("04-dialogs-and-blocking.png", [("Permission Consent", "05-permission-consent.png"),
          ("Explanation", "11-explanation.png"), ("Reporting Disabled", "12-reporting-disabled.png"),
          ("Block Confirmation", "09-block-confirmation.png"), ("Manual Instructions", "10-block-instructions.png")], 3,
         "Genuine app dialogs · Veritxt does not directly block numbers or submit reports"),
        ("05-unavailable-checks.png", [("Model Unavailable", "14-model-unavailable.png"),
          ("Invalid Model", "15-invalid-model.png"), ("Check Failed", "16-check-failed.png")], 3,
         "Test-only failure-state fixtures · Each uses Unable to Assess without a numerical score"),
    ]
    for name, items, columns, note in sheets:
        make_sheet(source, output, name, items, columns, note)
        print(name)


if __name__ == "__main__":
    main()
