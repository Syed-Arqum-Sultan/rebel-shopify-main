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


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """Parse #RGB or #RRGGBB into sRGB triple."""
    stripped = value.strip().lstrip("#")
    if len(stripped) == 3:
        stripped = "".join(ch * 2 for ch in stripped)
    if len(stripped) != 6:
        return (20, 18, 16)
    return (
        int(stripped[0:2], 16),
        int(stripped[2:4], 16),
        int(stripped[4:6], 16),
    )


def flatten_rgba_on_color(image: Image.Image, pad_color: str) -> Image.Image:
    """Composite RGBA onto a flat RGB backdrop (matches solid PDP backgrounds)."""
    rgba = ensure_rgba(image)
    bg = Image.new("RGB", rgba.size, hex_to_rgb(pad_color))
    bg.paste(rgba, mask=rgba.split()[3])
    return bg


def choose_output_ext(formats: Iterable[str]) -> str:
    """Pick first format extension from list."""
    for fmt in formats:
        normalized = fmt.lower().strip()
        if normalized in {"png", "webp", "jpg", "jpeg"}:
            if normalized == "jpeg":
                return ".jpg"
            return f".{normalized}"
    return ".png"
