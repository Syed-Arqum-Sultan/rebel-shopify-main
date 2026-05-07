"""Helpers for deriving subject and background masks."""

from __future__ import annotations

from PIL import Image, ImageChops, ImageFilter, ImageOps

from .helpers import ensure_rgba, ensure_rgb


def build_subject_mask(image: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Return soft subject mask and inverse background mask (L mode)."""
    rgba = ensure_rgba(image)
    alpha = rgba.split()[-1]

    # If alpha has transparency variance, use it directly.
    alpha_min, alpha_max = alpha.getextrema()
    if alpha_min < 245:
        subject = alpha.filter(ImageFilter.GaussianBlur(radius=1.2))
        background = ImageChops.invert(subject)
        return subject, background

    # Fallback for opaque input: detect subject by contrast from border baseline.
    gray = ImageOps.grayscale(ensure_rgb(rgba))
    width, height = gray.size
    border = max(2, int(min(width, height) * 0.05))
    border_band = Image.new("L", (width * 2 + border * 2, border))
    border_band.paste(gray.crop((0, 0, width, border)), (0, 0))
    border_band.paste(gray.crop((0, height - border, width, height)), (width, 0))
    border_band.paste(gray.crop((0, 0, border, border)), (width * 2, 0))
    border_band.paste(gray.crop((width - border, 0, width, border)), (width * 2 + border, 0))
    border_mean = sum(i * count for i, count in enumerate(border_band.histogram())) / max(
        1, border_band.size[0] * border_band.size[1]
    )
    threshold = int(max(12, min(96, border_mean + 14)))

    hard = gray.point(lambda px: 255 if px > threshold else 0)
    opened = hard.filter(ImageFilter.MinFilter(size=3)).filter(ImageFilter.MaxFilter(size=5))
    subject = opened.filter(ImageFilter.GaussianBlur(radius=2.4))
    background = ImageChops.invert(subject)
    return subject, background

