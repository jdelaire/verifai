"""Image metadata extraction using Pillow and exifread."""

from __future__ import annotations

import io

import exifread
from PIL import Image

from app.schemas import MetadataResult


def extract_metadata(image_bytes: bytes) -> MetadataResult:
    """Extract structural and EXIF metadata from raw image bytes.

    Parameters
    ----------
    image_bytes:
        The raw bytes of the image file.

    Returns
    -------
    MetadataResult
        Populated metadata including dimensions, format, and any EXIF fields
        we care about (camera make/model, software tag).
    """

    # --- Structural info via Pillow -------------------------------------------
    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size
    img_format = (img.format or "UNKNOWN").upper()

    # --- EXIF info via exifread -----------------------------------------------
    tags = exifread.process_file(io.BytesIO(image_bytes), details=False)

    has_exif = len(tags) > 0

    # Camera make / model
    camera_make_model: str | None = None
    make_tag = tags.get("Image Make")
    model_tag = tags.get("Image Model")
    if make_tag or model_tag:
        parts = [str(make_tag).strip() if make_tag else None,
                 str(model_tag).strip() if model_tag else None]
        camera_make_model = " ".join(p for p in parts if p)

    # Software tag (e.g. "Adobe Photoshop", "DALL-E", etc.)
    software_tag: str | None = None
    sw = tags.get("Image Software")
    if sw:
        software_tag = str(sw).strip()

    return MetadataResult(
        has_exif=has_exif,
        camera_make_model=camera_make_model or None,
        software_tag=software_tag or None,
        width=width,
        height=height,
        format=img_format,
    )
