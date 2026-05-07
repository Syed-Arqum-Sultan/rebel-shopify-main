"""Grading stage for tonal shaping and detail."""

from __future__ import annotations

from PIL import Image, ImageEnhance, ImageFilter

from .helpers import ensure_rgb
from .models import AdjustmentPlan


def apply_grade(
    image: Image.Image,
    plan: AdjustmentPlan,
    subject_mask: Image.Image | None = None,
    background_mask: Image.Image | None = None,
) -> Image.Image:
    """Apply tone shaping (shadow/highlight) and micro-contrast."""
    rgb = ensure_rgb(image)

    # Shadow lift and highlight compression with point mapping.
    shadow_strength = max(0.0, plan.shadow_lift)
    highlight_strength = max(0.0, plan.highlight_compress)
    toned = rgb.point(
        lambda px: _tone_curve(
            px,
            shadow_strength=shadow_strength,
            highlight_strength=highlight_strength,
            black_floor=plan.black_floor,
        )
    )

    if subject_mask is not None:
        # Preserve deep background by restricting tonal operations to subject.
        toned = Image.composite(toned, rgb, subject_mask)

    # Clarity: mild unsharp with low radius for local contrast.
    if plan.clarity > 0:
        clarity_img = toned.filter(
            ImageFilter.UnsharpMask(
                radius=1.2,
                percent=int(60 + 180 * plan.clarity),
                threshold=2,
            )
        )
        toned = Image.blend(toned, clarity_img, min(0.85, plan.clarity))
        if subject_mask is not None:
            toned = Image.composite(toned, rgb, subject_mask)

    # Final sharpen.
    if plan.sharpen > 0:
        toned = toned.filter(
            ImageFilter.UnsharpMask(
                radius=0.8,
                percent=int(70 + 160 * plan.sharpen),
                threshold=1,
            )
        )
        if subject_mask is not None:
            toned = Image.composite(toned, rgb, subject_mask)

    # Slight saturation polish after tone operations.
    toned = ImageEnhance.Color(toned).enhance(max(0.05, 1.0 + plan.saturation * 0.2))
    if subject_mask is not None:
        toned = Image.composite(toned, rgb, subject_mask)

    if background_mask is not None and plan.background_damping < 1.0:
        # Slightly darken background to keep black studio look.
        bg_damped = ImageEnhance.Brightness(rgb).enhance(max(0.05, plan.background_damping))
        toned = Image.composite(toned, bg_damped, background_mask)
    return toned


def _tone_curve(px: int, shadow_strength: float, highlight_strength: float, black_floor: float) -> int:
    """Lift shadows and compress highlights with smooth math."""
    x = px / 255.0
    if x <= black_floor:
        return px
    # Lift dark tones more than midtones.
    shadow_lift = (1.0 - x) ** 2 * 0.28 * shadow_strength
    # Compress highlights close to white.
    highlight_pull = (x**2) * 0.24 * highlight_strength
    y = x + shadow_lift - highlight_pull
    return max(0, min(255, int(round(y * 255))))
