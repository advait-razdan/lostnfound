from io import BytesIO
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from inventory.services import analyze_item_images


class VisionServiceTests(TestCase):
    @override_settings(OPENAI_API_KEY="test-key")
    @patch("inventory.services.requests.post")
    def test_analyze_item_images_happy_path(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "title": "Black Umbrella",
            "description": "A compact black umbrella with silver handle.",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        file_obj = SimpleUploadedFile(
            "umbrella.jpg",
            BytesIO(b"fake-image-bytes").getvalue(),
            content_type="image/jpeg",
        )

        result = analyze_item_images([file_obj])

        self.assertEqual(result["title"], "Black Umbrella")
        self.assertIn("compact black umbrella", result["description"].lower())
        mock_post.assert_called_once()

    @override_settings(OPENAI_API_KEY="")
    def test_analyze_item_images_no_api_key_returns_empty(self):
        result = analyze_item_images([])
        self.assertEqual(result, {})



