"""Image analysis and adaptive plan creation."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageFilter, ImageOps, ImageStat

from .helpers import clamp, ensure_rgb
from .models import AdjustmentPlan, PhotoMetrics, SceneProfile


@dataclass(slots=True)
class PresetConfig:
    """Subset of preset fields needed to compute adaptive plan."""

    name: str
    exposure_bias: float
    contrast_bias: float
    saturation_bias: float
    shadow_bias: float
    highlight_bias: float
    clarity_bias: float
    sharpen_bias: float
    relight_bias: float
    relight_warmth: float
    shadow_opacity: float
    white_balance_bias: float
    max_adjustment: float


def analyze_photo(image: Image.Image) -> PhotoMetrics:
    """Extract scalar metrics from image for adaptive processing."""
    rgb = ensure_rgb(image)
    luminance = ImageOps.grayscale(rgb)
    lum_stat = ImageStat.Stat(luminance)
    lum_mean = lum_stat.mean[0] / 255.0
    lum_std = lum_stat.stddev[0] / 255.0

    # Pixel histogram-based ratios.
    hist = luminance.histogram()
    total = max(1, sum(hist))
    shadows = sum(hist[:40]) / total
    highlights = sum(hist[215:]) / total

    hsv = rgb.convert("HSV")
    hsv_stat = ImageStat.Stat(hsv)
    saturation_mean = hsv_stat.mean[1] / 255.0

    edges = luminance.filter(ImageFilter.FIND_EDGES)
    edge_stat = ImageStat.Stat(edges)
    edge_density = edge_stat.mean[0] / 255.0

    rgb_stat = ImageStat.Stat(rgb)
    r, g, b = (channel / 255.0 for channel in rgb_stat.mean[:3])

    width, height = rgb.size
    aspect_ratio = width / max(1, height)

    return PhotoMetrics(
        luminance_mean=lum_mean,
        luminance_std=lum_std,
        shadow_ratio=shadows,
        highlight_ratio=highlights,
        saturation_mean=saturation_mean,
        edge_density=edge_density,
        red_mean=r,
        green_mean=g,
        blue_mean=b,
        aspect_ratio=aspect_ratio,
    )


def profile_scene(image: Image.Image) -> SceneProfile:
    """Profile border darkness and rough subject coverage."""
    rgb = ensure_rgb(image)
    gray = ImageOps.grayscale(rgb)
    width, height = gray.size
    border_px = max(2, int(min(width, height) * 0.06))

    top = gray.crop((0, 0, width, border_px))
    bottom = gray.crop((0, height - border_px, width, height))
    left = gray.crop((0, 0, border_px, height))
    right = gray.crop((width - border_px, 0, width, height))

    border_strip = Image.new("L", (width * 2 + border_px * 2, border_px))
    border_strip.paste(top, (0, 0))
    border_strip.paste(bottom, (width, 0))
    # Reduce left/right to strip-height to keep memory low.
    left_small = left.resize((border_px, border_px), Image.Resampling.BILINEAR)
    right_small = right.resize((border_px, border_px), Image.Resampling.BILINEAR)
    border_strip.paste(left_small, (width * 2, 0))
    border_strip.paste(right_small, (width * 2 + border_px, 0))

    border_stat = ImageStat.Stat(border_strip)
    border_mean = border_stat.mean[0] / 255.0
    border_std = border_stat.stddev[0] / 255.0
    hist = border_strip.histogram()
    total = max(1, sum(hist))
    border_dark_ratio = sum(hist[:22]) / total
    is_dark_background = border_mean < 0.09 and border_dark_ratio > 0.82 and border_std < 0.06

    # Rough subject coverage: threshold over border baseline.
    threshold = int(max(14, min(64, (border_mean * 255) + 18)))
    subject_mask = gray.point(lambda px: 255 if px > threshold else 0)
    mask_stat = ImageStat.Stat(subject_mask)
    subject_coverage = mask_stat.mean[0] / 255.0

    return SceneProfile(
        border_luma_mean=border_mean,
        border_luma_std=border_std,
        border_dark_ratio=border_dark_ratio,
        is_dark_background=is_dark_background,
        subject_coverage=subject_coverage,
    )


def build_adjustment_plan(
    metrics: PhotoMetrics,
    preset: PresetConfig,
    scene: SceneProfile | None = None,
) -> AdjustmentPlan:
    """Create bounded per-photo adjustment plan from metrics + preset bias."""
    notes: list[str] = []

    # Exposure: lift dark frames, reduce very bright.
    exposure_target = 0.52
    exposure_delta = (exposure_target - metrics.luminance_mean) * 0.65
    exposure = clamp(
        preset.exposure_bias + exposure_delta,
        -preset.max_adjustment,
        preset.max_adjustment,
    )
    if metrics.luminance_mean < 0.35:
        notes.append("dark_frame_detected")
    if metrics.highlight_ratio > 0.18:
        notes.append("highlights_at_risk")

    # Contrast: if image is flat (low stddev), increase; if already harsh, tame.
    contrast_target = 0.24
    contrast_delta = (contrast_target - metrics.luminance_std) * 0.8
    contrast = clamp(
        preset.contrast_bias + contrast_delta,
        -preset.max_adjustment,
        preset.max_adjustment,
    )

    # Saturation: slightly lift low-sat images; pull back oversaturated.
    sat_target = 0.32
    sat_delta = (sat_target - metrics.saturation_mean) * 0.7
    saturation = clamp(
        preset.saturation_bias + sat_delta,
        -preset.max_adjustment,
        preset.max_adjustment,
    )

    # Shadow/highlight balancing.
    shadow_lift = clamp(
        preset.shadow_bias + (metrics.shadow_ratio - 0.16) * 0.8,
        0.0,
        preset.max_adjustment,
    )
    highlight_compress = clamp(
        preset.highlight_bias + (metrics.highlight_ratio - 0.08) * 0.85,
        0.0,
        preset.max_adjustment,
    )

    # Clarity and sharpening based on edge density.
    clarity = clamp(
        preset.clarity_bias + (0.18 - metrics.edge_density) * 0.6,
        0.0,
        preset.max_adjustment,
    )
    sharpen = clamp(
        preset.sharpen_bias + (0.16 - metrics.edge_density) * 0.5,
        0.0,
        preset.max_adjustment,
    )

    # White balance shift from channel imbalance.
    warm_minus_cool = (metrics.red_mean - metrics.blue_mean) * 0.5
    white_balance_shift = clamp(
        preset.white_balance_bias - warm_minus_cool,
        -preset.max_adjustment,
        preset.max_adjustment,
    )

    # Relight stronger for dark + low edge separation.
    relight_strength = clamp(
        preset.relight_bias
        + max(0.0, 0.42 - metrics.luminance_mean) * 0.7
        + max(0.0, 0.15 - metrics.edge_density) * 0.45,
        0.0,
        preset.max_adjustment,
    )

    black_floor = 0.03
    background_damping = 0.85
    force_black_output = False
    if scene and scene.is_dark_background:
        notes.append("dark_background_detected")
        # Keep black backgrounds deep; dampen operations that haze the backdrop.
        shadow_lift = shadow_lift * 0.35
        relight_strength = relight_strength * 0.45
        contact_shadow = 0.0 if scene.subject_coverage > 0.62 else 0.06
        black_floor = 0.055
        background_damping = 0.35
        force_black_output = True
    else:
        contact_shadow = clamp(preset.shadow_opacity, 0.0, 1.0)

    return AdjustmentPlan(
        preset_name=preset.name,
        exposure=exposure,
        contrast=contrast,
        saturation=saturation,
        shadow_lift=shadow_lift,
        highlight_compress=highlight_compress,
        clarity=clarity,
        sharpen=sharpen,
        relight_strength=relight_strength,
        relight_warmth=preset.relight_warmth,
        contact_shadow_opacity=contact_shadow,
        white_balance_shift=white_balance_shift,
        black_floor=black_floor,
        background_damping=background_damping,
        force_black_output=force_black_output,
        notes=notes,
    )

