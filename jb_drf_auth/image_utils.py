from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image

from jb_drf_auth.conf import get_setting


def _int_setting(name: str, default: int) -> int:
    value = get_setting(name)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def optimize_profile_picture(uploaded_file):
    if not get_setting("PROFILE_PICTURE_OPTIMIZE"):
        return uploaded_file

    max_bytes = _int_setting("PROFILE_PICTURE_MAX_BYTES", 1024 * 1024)
    max_width = _int_setting("PROFILE_PICTURE_MAX_WIDTH", 1080)
    max_height = _int_setting("PROFILE_PICTURE_MAX_HEIGHT", 1080)
    start_quality = _int_setting("PROFILE_PICTURE_JPEG_QUALITY", 85)
    min_quality = _int_setting("PROFILE_PICTURE_MIN_JPEG_QUALITY", 65)

    if getattr(uploaded_file, "size", None) is not None and uploaded_file.size <= max_bytes:
        return uploaded_file

    try:
        uploaded_file.seek(0)
    except Exception:
        return uploaded_file

    try:
        image = Image.open(uploaded_file)
    except Exception:
        return uploaded_file

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    elif image.mode == "L":
        image = image.convert("RGB")

    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    best = None
    for quality in range(start_quality, min_quality - 1, -5):
        buffer = BytesIO()
        image.save(buffer, format="JPEG", optimize=True, quality=quality)
        candidate = buffer.getvalue()
        best = candidate
        if len(candidate) <= max_bytes:
            break

    if not best:
        return uploaded_file

    stem = Path(getattr(uploaded_file, "name", "profile-picture")).stem or "profile-picture"
    optimized = ContentFile(best)
    optimized.name = f"{stem}.jpg"
    return optimized
