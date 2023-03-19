"""
Content Blocks test_abstract_models.py
"""
import pytest
from django.core.exceptions import ValidationError

from content_blocks.fields import validate_svg


class TestValidateSVG:
    def test_validate_svg_passes(self, svg_file):
        svg_file = svg_file.open()
        assert validate_svg(svg_file) == svg_file

    def test_validate_svg_fails(self, text_file):
        text_file = text_file.open()
        with pytest.raises(ValidationError):
            validate_svg(text_file)
