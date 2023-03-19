"""
Content blocks test_widgets.py
"""
import uuid

from content_blocks.widgets import FileWidget


class TestFileWidget:
    def test_clear_checkbox_id(self):
        file_widget = FileWidget()
        # This will raise ValueError and fail the test if the id is not a valid uuid
        uuid.UUID(file_widget.clear_checkbox_id("filefield"))
