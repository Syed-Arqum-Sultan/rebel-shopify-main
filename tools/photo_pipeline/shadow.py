"""Contact shadow synthesis for cutout/composited products."""

from __future__ import annotations

from PIL import Image, ImageFilter

from .helpers import ensure_rgba
from .models import AdjustmentPlan


def apply_contact_shadow(image: Image.Image, plan: AdjustmentPlan) -> Image.Image:
    """Render a soft grounding shadow underneath the product."""
    if plan.contact_shadow_opacity <= 0:
        return ensure_rgba(image)

    rgba = ensure_rgba(image)
    w, h = rgba.size
    alpha = rgba.split()[-1]
    bbox = alpha.getbbox()
    if bbox is None:
        return rgba

    left, top, right, bottom = bbox
    obj_w = right - left
    obj_h = bottom - top

    shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Ellipse mask derived from object footprint.
    ellipse_w = int(obj_w * 0.88)
    ellipse_h = max(8, int(obj_h * 0.12))
    center_x = left + obj_w // 2
    center_y = min(h - 2, bottom + max(2, int(obj_h * 0.03)))

    ellipse_mask = Image.new("L", (w, h), 0)
    ellipse = Image.new("L", (ellipse_w, ellipse_h), 255)
    ellipse = ellipse.filter(ImageFilter.GaussianBlur(radius=max(2, int(ellipse_h * 0.3))))
    paste_x = max(0, center_x - ellipse_w // 2)
    paste_y = max(0, center_y - ellipse_h // 2)
    ellipse_mask.paste(ellipse, (paste_x, paste_y))

    opacity = int(255 * min(1.0, plan.contact_shadow_opacity))
    shadow_alpha = ellipse_mask.point(lambda px: int(px / 255 * opacity))
    shadow_layer.putalpha(shadow_alpha)

    return Image.alpha_composite(shadow_layer, rgba)

