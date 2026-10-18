"""Focused publication guards; no application or provider dependencies."""

from io import BytesIO
import unittest

from reportlab.pdfgen.canvas import Canvas

from layout import Page, register_fonts
from localization import translate


class LocalizationTests(unittest.TestCase):
    def test_missing_chinese_copy_fails_instead_of_falling_back_to_english(self):
        with self.assertRaisesRegex(ValueError, "Chinese copy missing"):
            translate("A new sentence without reviewed Chinese copy.", "zh")

    def test_unsupported_language_fails(self):
        with self.assertRaisesRegex(ValueError, "Unsupported publication language"):
            translate("Private Client Graph", "fr")

    def test_continuous_page_numbers_do_not_need_translation(self):
        self.assertEqual(translate("21", "zh"), "21")
        self.assertEqual(translate("40", "zh"), "40")


class TypographyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_fonts()

    def test_original_english_quote_keeps_its_height_in_chinese_edition(self):
        quote = (
            "“The purpose of the meeting was to establish an accurate understanding "
            "of the current family and beneficiary position before any further "
            "review or substantive advice is undertaken.”"
        )
        ends = []
        for language in ("en", "zh"):
            canvas = Canvas(BytesIO())
            canvas.folio_language = language
            page = Page(canvas, 2, "The original problem")
            ends.append(page.paragraph(quote, 69, 380, 580, 25, 30, font="Serif"))
        self.assertEqual(translate(quote, "zh"), quote)
        self.assertEqual(ends[0], ends[1])
        self.assertLess(ends[1], 514)  # The documentary caption begins here.

    def test_missing_font_glyph_fails_before_rendering_an_empty_character(self):
        page = Page(Canvas(BytesIO()), 1, "The original problem")
        with self.assertRaisesRegex(ValueError, "missing Sans glyphs"):
            page.text("Unsupported unicorn: \U0001f984", 48, 100)


if __name__ == "__main__":
    unittest.main()
