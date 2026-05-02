"""Normalization stage (exposure, white balance, contrast)."""

from __future__ import annotations

from PIL import Image, ImageEnhance

from .helpers import ensure_rgb
from .models import AdjustmentPlan


def apply_normalization(image: Image.Image, plan: AdjustmentPlan) -> Image.Image:
    """Apply global color/exposure normalization from adaptive plan."""
    rgb = ensure_rgb(image)

    # White balance by channel scaling.
    r, g, b = rgb.split()
    shift = plan.white_balance_shift
    # Positive shift warms (boost R, reduce B), negative cools.
    r = r.point(lambda px: _scale_channel(px, 1.0 + shift * 0.22))
    b = b.point(lambda px: _scale_channel(px, 1.0 - shift * 0.22))
    balanced = Image.merge("RGB", (r, g, b))

    brightness_factor = 1.0 + plan.exposure
    contrast_factor = 1.0 + plan.contrast

    balanced = ImageEnhance.Brightness(balanced).enhance(max(0.1, brightness_factor))
    balanced = ImageEnhance.Contrast(balanced).enhance(max(0.1, contrast_factor))
    balanced = ImageEnhance.Color(balanced).enhance(max(0.05, 1.0 + plan.saturation))

    return balanced


def _scale_channel(value: int, scale: float) -> int:
    scaled = int(round(value * scale))
    return max(0, min(255, scaled))
