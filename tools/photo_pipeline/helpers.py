"""Shared utility helpers for photo pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def clamp(value: float, low: float, high: float) -> float:
    """Clamp value into [low, high]."""
    return max(low, min(high, value))


def list_images(input_dir: Path) -> list[Path]:
    """Recursively list supported image files."""
    files: list[Path] = []
    for path in input_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    files.sort()
    return files


def ensure_rgba(image: Image.Image) -> Image.Image:
    """Convert image to RGBA for compositing safety."""
    if image.mode != "RGBA":
        return image.convert("RGBA")
    return image


def ensure_rgb(image: Image.Image) -> Image.Image:
    """Convert image to RGB for color operations."""
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def choose_output_ext(formats: Iterable[str]) -> str:
    """Pick first format extension from list."""
    for fmt in formats:
        normalized = fmt.lower().strip()
        if normalized in {"png", "webp", "jpg", "jpeg"}:
            if normalized == "jpeg":
                return ".jpg"
            return f".{normalized}"
    return ".png"
