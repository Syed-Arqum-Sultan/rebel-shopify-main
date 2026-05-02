"""Optional background removal stage."""

from __future__ import annotations

import contextlib
import io

from PIL import Image

from .helpers import ensure_rgba


def apply_background_removal(image: Image.Image, enabled: bool) -> tuple[Image.Image, list[str]]:
    """Run rembg when available; otherwise return input unchanged."""
    warnings: list[str] = []
    if not enabled:
        return ensure_rgba(image), warnings

    rgba = ensure_rgba(image)
    try:
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            from rembg import remove as rembg_remove  # type: ignore
    except BaseException:
        warnings.append("rembg_not_ready_background_removal_skipped")
        return rgba, warnings

    try:
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            buffer = io.BytesIO()
            rgba.save(buffer, format="PNG")
            removed = rembg_remove(buffer.getvalue())
    except BaseException:
        warnings.append("rembg_runtime_error_background_removal_skipped")
        return rgba, warnings

    if isinstance(removed, (bytes, bytearray)):
        try:
            return ensure_rgba(Image.open(io.BytesIO(removed))), warnings
        except BaseException:
            warnings.append("rembg_decode_error_background_removal_skipped")
            return rgba, warnings
    if isinstance(removed, Image.Image):
        return ensure_rgba(removed), warnings
    warnings.append("rembg_returned_unexpected_type_background_removal_skipped")
    return rgba, warnings
