"""Small vector-first page vocabulary for the judge's reading document."""

from pathlib import Path
from html import unescape
import re

from fontTools.ttLib import TTFont as FontToolsFont
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader

from localization import translate


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WIDTH, HEIGHT = 720, 900
FOREST = "#173F31"
INK = "#20372B"
MUTED = "#52665B"
CHALK = "#F4F7F2"
WHITE = "#FFFFFF"
YELLOW = "#FFF0A6"
BURGUNDY = "#773B46"
RULE = "#C7D3C8"


def register_fonts():
    """Convert the project's licensed web fonts for subset embedding in PDF."""
    destination = HERE / ".build" / "fonts"
    destination.mkdir(parents=True, exist_ok=True)
    for name, filename in (
        ("Sans", "public-sans-latin-400-normal.woff2"),
        ("SansBold", "public-sans-latin-600-normal.woff2"),
        ("Serif", "newsreader-display-latin-400-normal.woff2"),
        ("SerifItalic", "newsreader-display-latin-400-italic.woff2"),
    ):
        target = destination / f"{name}.ttf"
        font = FontToolsFont(ROOT / "web/src/styles/fonts" / filename, recalcTimestamp=False)
        font.flavor = None
        font.save(target)
        pdfmetrics.registerFont(TTFont(name, target))
    pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="SansBold")
    pdfmetrics.registerFontFamily("Serif", normal="Serif", italic="SerifItalic")
    for name, filename in (
        ("SansSC", "noto-sans-sc-chinese-simplified-400-normal.woff2"),
        ("SansBoldSC", "noto-sans-sc-chinese-simplified-600-normal.woff2"),
        ("SerifSC", "noto-serif-sc-chinese-simplified-400-normal.woff2"),
    ):
        target = destination / f"{name}.ttf"
        font = FontToolsFont(ROOT / "presentation/product-demo/public/fonts" / filename,
                            recalcTimestamp=False)
        font.flavor = None
        font.save(target)
        pdfmetrics.registerFont(TTFont(name, target))
    pdfmetrics.registerFontFamily("SansSC", normal="SansSC", bold="SansBoldSC")
    pdfmetrics.registerFontFamily("SerifSC", normal="SerifSC", italic="SerifSC")


class Page:
    """Top-origin coordinates and explicit typography; no application semantics."""

    def __init__(self, canvas, number, section, dark=False):
        self.canvas = canvas
        self.number = number
        self.dark = dark
        self.language = getattr(canvas, "folio_language", "en")
        self.rect(0, 0, WIDTH, HEIGHT, FOREST if dark else WHITE)
        self.text("Private Client Graph", 48, 29, 10.5,
                  WHITE if dark else MUTED, "SansBold")
        self.text(section, 672, 29, 10.5,
                  WHITE if dark else MUTED, align="right")

    def rect(self, x, y, width, height, fill, stroke=None, line_width=0.7):
        c = self.canvas
        c.setFillColor(HexColor(fill))
        if stroke:
            c.setStrokeColor(HexColor(stroke))
            c.setLineWidth(line_width)
        c.rect(x, HEIGHT-y-height, width, height, fill=1, stroke=int(bool(stroke)))

    def line(self, x1, y1, x2, y2, color=RULE, width=0.7, dash=None):
        c = self.canvas
        c.saveState()
        c.setStrokeColor(HexColor(color))
        c.setLineWidth(width)
        if dash:
            c.setDash(dash)
        c.line(x1, HEIGHT-y1, x2, HEIGHT-y2)
        c.restoreState()

    def text(self, text, x, y, size=16, color=INK, font="Sans", align="left"):
        text = translate(text, self.language)
        font = self._font(font, text)
        self._check_glyphs(text, font)
        c = self.canvas
        c.setFillColor(HexColor(color))
        # The project's Latin Public Sans subset omits the mathematical prime.
        # Retain the published A-prime notation with a licensed project-font fallback.
        runs = [(part, "Serif" if part == "′" else font)
                for part in re.split("(′)", text) if part]
        widths = [pdfmetrics.stringWidth(part, face, size) for part, face in runs]
        x -= sum(widths) * {"left": 0, "center": 0.5, "right": 1}[align]
        for (part, face), width in zip(runs, widths):
            c.setFont(face, size)
            c.drawString(x, HEIGHT-y-size*0.8, part)
            x += width

    def paragraph(self, text, x, y, width, size=16, leading=23,
                  color=INK, font="Sans", max_height=None):
        text = translate(text, self.language)
        font = self._font(font, text)
        self._check_glyphs(text, font)
        style = ParagraphStyle("body", fontName=font, fontSize=size,
                               leading=leading, textColor=HexColor(color),
                               wordWrap="CJK" if self._has_chinese(text) else None)
        text = text.replace("′", '<font name="Serif">′</font>')
        paragraph = Paragraph(text, style)
        _, height = paragraph.wrap(width, HEIGHT)
        if max_height is not None and height > max_height:
            raise ValueError(f"Page {self.number}: text exceeds its {max_height}pt box: {text}")
        if y + height > 840:
            raise ValueError(f"Page {self.number}: text crosses the footer: {text}")
        paragraph.drawOn(self.canvas, x, HEIGHT-y-height)
        return y + height

    def heading(self, text, y=82, size=42, width=624, color=INK):
        return self.paragraph(text, 48, y, width, size, size*1.06, color, "Serif",
                              max_height=size*2.12+0.1)

    def circle(self, x, y, radius, fill, stroke=None):
        self.canvas.setFillColor(HexColor(fill))
        if stroke:
            self.canvas.setStrokeColor(HexColor(stroke))
        self.canvas.circle(x, HEIGHT-y, radius, fill=1, stroke=int(bool(stroke)))

    def image_detail(self, path, crop, x, y, width):
        """Clip original screenshot pixels in PDF without changing the asset."""
        image = ImageReader(str(path))
        image_width, image_height = image.getSize()
        left, top, right, bottom = crop
        scale = width / (right-left)
        height = (bottom-top)*scale
        c = self.canvas
        c.saveState()
        clip = c.beginPath()
        clip.rect(x, HEIGHT-y-height, width, height)
        c.clipPath(clip, stroke=0, fill=0)
        c.drawImage(image, x-left*scale, HEIGHT-y-(image_height-top)*scale,
                    image_width*scale, image_height*scale)
        c.restoreState()
        return height

    def link(self, label, url, x, y, size=11.5, color=MUTED):
        self.text(label, x, y, size, color)
        label = translate(label, self.language)
        width = sum(pdfmetrics.stringWidth(part, "Serif" if part == "′" else self._font("Sans", label), size)
                    for part in re.split("(′)", label))
        self.canvas.linkURL(url, (x, HEIGHT-y-size-3, x+width, HEIGHT-y+2), relative=0)

    def _font(self, font, text):
        if self.language == "en" or not self._has_chinese(text):
            return font
        return {"Sans": "SansSC", "SansBold": "SansBoldSC",
                "Serif": "SerifSC", "SerifItalic": "SerifSC"}[font]

    @staticmethod
    def _has_chinese(text):
        return bool(re.search(r"[\u3400-\u9fff]", text))

    def _check_glyphs(self, text, font):
        plain = unescape(re.sub(r"<[^>]+>", "", text))
        available = pdfmetrics.getFont(font).face.charWidths
        missing = {character for character in plain
                   if not character.isspace() and character != "′" and ord(character) not in available}
        if missing:
            raise ValueError(f"Page {self.number}: missing {font} glyphs {sorted(missing)}")

    def footer(self, source=None, url=None):
        color = WHITE if self.dark else MUTED
        if source:
            if url:
                self.link(source, url, 48, 852, 9.5, color)
            else:
                self.text(source, 48, 852, 9.5, color)
        self.text(f"{self.number:02d}", 672, 851, 11.5, color, align="right")
        self.canvas.showPage()
