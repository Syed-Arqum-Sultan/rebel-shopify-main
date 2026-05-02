"""Subject relighting stage for dark-theme presentation."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

from .helpers import ensure_rgba
from .models import AdjustmentPlan


def apply_relight(image: Image.Image, plan: AdjustmentPlan) -> Image.Image:
    """Add gentle directional light and subtle rim separation."""
    if plan.relight_strength <= 0:
        return ensure_rgba(image)

    rgba = ensure_rgba(image)
    w, h = rgba.size

    # Large soft light from upper-left.
    light = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(light)
    radius = int(max(w, h) * 0.72)
    center = (int(w * 0.18), int(h * 0.22))
    draw.ellipse(
        (
            center[0] - radius,
            center[1] - radius,
            center[0] + radius,
            center[1] + radius,
        ),
        fill=255,
    )
    light = light.filter(ImageFilter.GaussianBlur(radius=max(8, int(radius * 0.18))))

    # Warmth influences tint channel mix.
    warmth = max(-1.0, min(1.0, plan.relight_warmth))
    max_alpha = int(90 * plan.relight_strength)
    r_tint = int(255 if warmth >= 0 else 245)
    g_tint = int(246 if warmth >= 0 else 248)
    b_tint = int(228 if warmth >= 0 else 255)

    tint = Image.new("RGBA", (w, h), (r_tint, g_tint, b_tint, 0))
    tint.putalpha(light.point(lambda px: int(px / 255 * max_alpha)))
    lit = Image.alpha_composite(rgba, tint)

    # Subtle rim-light from right edge to separate dark objects.
    rim = Image.new("L", (w, h), 0)
    rim_draw = ImageDraw.Draw(rim)
    rim_draw.rectangle((int(w * 0.76), int(h * 0.08), w, int(h * 0.94)), fill=255)
    rim = rim.filter(ImageFilter.GaussianBlur(radius=max(4, int(w * 0.04))))
    rim_alpha = rim.point(lambda px: int(px / 255 * 46 * plan.relight_strength))
    rim_layer = Image.new("RGBA", (w, h), (255, 245, 220, 0))
    rim_layer.putalpha(rim_alpha)

    return Image.alpha_composite(lit, rim_layer)

