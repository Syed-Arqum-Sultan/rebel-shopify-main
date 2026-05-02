"""Image analysis and adaptive plan creation."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageFilter, ImageOps, ImageStat

from .helpers import clamp, ensure_rgb
from .models import AdjustmentPlan, PhotoMetrics


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


def build_adjustment_plan(metrics: PhotoMetrics, preset: PresetConfig) -> AdjustmentPlan:
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
        contact_shadow_opacity=clamp(preset.shadow_opacity, 0.0, 1.0),
        white_balance_shift=white_balance_shift,
        notes=notes,
    )

