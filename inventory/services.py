import logging
from typing import Iterable, Mapping

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def analyze_item_images(files: Iterable) -> Mapping[str, str]:
    """
    Call an OpenAI-style vision API to suggest a title and description
    for a lost-and-found item based on one or more uploaded images.

    This implementation is intentionally generic so it can be wired up to
    any external service that accepts multipart image uploads and returns
    a JSON payload shaped like:

        {"title": "...", "description": "..."}

    In tests we mock `requests.post` so no real network calls are made.
    """
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    endpoint = getattr(
        settings,
        "OPENAI_VISION_ENDPOINT",
        "https://api.openai.com/v1/lost-and-found/analyze",
    )

    # If there is no API key or no files, just skip auto-fill quietly.
    if not api_key:
        return {}

    files = list(files or [])
    if not files:
        return {}

    multipart_files = []
    for f in files:
        if not f:
            continue
        content_type = getattr(f, "content_type", "application/octet-stream")
        # Ensure the file pointer is at the start for reading.
        try:
            f.seek(0)
        except (AttributeError, OSError):
            # If the object doesn't support seek we just rely on current position.
            pass
        multipart_files.append(("images", (getattr(f, "name", "image"), f, content_type)))

    if not multipart_files:
        return {}

    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "prompt": (
            "You are helping catalog lost-and-found items for a reception desk. "
            "Based on the uploaded images, suggest a concise but specific title "
            "and a detailed description with key identifiers such as brand, color, "
            "size, model, and visible markings. Respond as JSON with keys "
            "'title' and 'description'."
        )
    }

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            data=data,
            files=multipart_files,
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json() or {}
    except Exception:  # pragma: no cover - defensive, behaviour tested via mocks
        logger.exception("Vision API call failed")
        return {}

    title = payload.get("title") or ""
    description = payload.get("description") or ""
    return {
        "title": title.strip(),
        "description": description.strip(),
    }



