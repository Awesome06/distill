"""High-resolution asset carving for embedded diagrams and pictures."""

from __future__ import annotations

import contextlib
import hashlib
from pathlib import Path
from typing import Any

from distill.models.slide import ExtractedAsset


def carve_shape_asset(
    shape: Any,
    deck_stem: str,
    slide_num: int,
    asset_idx: int,
    output_dir: Path,
) -> ExtractedAsset | None:
    """Extract embedded image from a slide shape and persist to disk with SHA-256 hash.

    Args:
        shape: python-pptx shape object.
        deck_stem: Clean base name of the presentation (e.g. 'lecture_01').
        slide_num: 1-indexed slide number.
        asset_idx: 1-indexed asset position on this slide.
        output_dir: Directory where assets are persisted (e.g. 01_raw_markdown/assets/).

    Returns:
        ExtractedAsset metadata object, or None if shape does not contain image bytes.
    """
    image = None

    # Standard picture shape
    if hasattr(shape, "image") and shape.image:
        image = shape.image
    elif hasattr(shape, "shape_type") and str(shape.shape_type).endswith("PICTURE"):
        with contextlib.suppress(Exception):
            image = shape.image

    if image is None:
        return None

    try:
        blob = image.blob
        ext = image.ext.lower()
        if not ext:
            ext = "png"
    except Exception:
        return None

    sha256 = hashlib.sha256(blob).hexdigest()
    asset_id = f"{deck_stem}_s{slide_num:02d}_img{asset_idx:02d}"
    filename = f"{asset_id}.{ext}"
    target_path = output_dir / filename

    output_dir.mkdir(parents=True, exist_ok=True)
    if not target_path.exists():
        target_path.write_bytes(blob)

    # Relative path from project root
    if "01_raw_markdown" in output_dir.parts:
        idx = output_dir.parts.index("01_raw_markdown")
        rel_parts = output_dir.parts[idx:] + (filename,)
        rel_path = "/".join(rel_parts)
    else:
        rel_path = f"01_raw_markdown/assets/{filename}"

    return ExtractedAsset(
        asset_id=asset_id,
        file_path=rel_path,
        shape_type=f"image/{ext}",
        sha256=sha256,
    )
