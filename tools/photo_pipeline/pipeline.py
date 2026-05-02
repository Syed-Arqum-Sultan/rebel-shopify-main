"""High-level orchestration for adaptive image enhancement pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from .analyze import PresetConfig, analyze_photo, build_adjustment_plan
from .background import apply_background_removal
from .grade import apply_grade
from .helpers import choose_output_ext, ensure_rgb, ensure_rgba
from .models import ProcessResult
from .normalize import apply_normalization
from .relight import apply_relight
from .shadow import apply_contact_shadow


@dataclass(slots=True)
class PipelinePreset:
    """Loaded preset and output options."""

    config: PresetConfig
    output_formats: list[str]
    output_sizes: list[int]
    pad_color: str
    background_mode: str
    quality: int
    remove_background: bool


def process_image(
    source_path: Path,
    output_dir: Path,
    preset: PipelinePreset,
) -> ProcessResult:
    """Analyze, plan, enhance and export a single image."""
    image = Image.open(source_path)
    image, bg_warnings = apply_background_removal(image, enabled=preset.remove_background)
    metrics = analyze_photo(image)
    plan = build_adjustment_plan(metrics, preset.config)
    warnings: list[str] = list(bg_warnings)

    normalized = apply_normalization(image, plan)
    graded = apply_grade(normalized, plan)
    relit = apply_relight(graded, plan)
    final_rgba = apply_contact_shadow(relit, plan)

    saved_path = export_outputs(
        final_rgba,
        source_path=source_path,
        output_dir=output_dir,
        output_formats=preset.output_formats,
        output_sizes=preset.output_sizes,
        pad_color=preset.pad_color,
        background_mode=preset.background_mode,
        quality=preset.quality,
    )

    if metrics.luminance_mean < 0.23:
        warnings.append("very_dark_input")
    if metrics.highlight_ratio > 0.25:
        warnings.append("high_highlight_ratio")

    return ProcessResult(
        source_path=str(source_path),
        output_path=str(saved_path),
        preset_name=preset.config.name,
        metrics=metrics,
        plan=plan,
        warnings=warnings,
    )


def export_outputs(
    image: Image.Image,
    source_path: Path,
    output_dir: Path,
    output_formats: list[str],
    output_sizes: list[int],
    pad_color: str,
    background_mode: str,
    quality: int,
) -> Path:
    """Write one or more size/format variants and return primary path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = source_path.stem
    primary_ext = choose_output_ext(output_formats)
    first_path = output_dir / f"{stem}{primary_ext}"

    for size in output_sizes:
        framed = fit_to_square(image, size=size, pad_color=pad_color, background_mode=background_mode)
        for fmt in output_formats:
            normalized_fmt = fmt.lower().strip()
            ext = ".jpg" if normalized_fmt == "jpeg" else f".{normalized_fmt}"
            suffix = "" if size == output_sizes[0] else f"_{size}"
            out_path = output_dir / f"{stem}{suffix}{ext}"
            save_image(framed, out_path, normalized_fmt, quality=quality)
            if out_path == first_path:
                continue

    return first_path


def fit_to_square(
    image: Image.Image,
    size: int,
    pad_color: str,
    background_mode: str,
) -> Image.Image:
    """Resize with padding to square canvas."""
    rgba = ensure_rgba(image)
    w, h = rgba.size
    scale = min(size / max(w, 1), size / max(h, 1))
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    resized = rgba.resize((new_w, new_h), Image.Resampling.LANCZOS)
    if background_mode == "transparent":
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    else:
        rgb = _hex_to_rgb(pad_color)
        canvas = Image.new("RGBA", (size, size), (*rgb, 255))

    offset = ((size - new_w) // 2, (size - new_h) // 2)
    canvas.alpha_composite(resized, offset)
    return canvas


def save_image(image: Image.Image, out_path: Path, fmt: str, quality: int) -> None:
    """Persist image with sensible per-format options."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if fmt in {"jpg", "jpeg"}:
        rgb = ensure_rgb(image)
        rgb.save(out_path, format="JPEG", quality=quality, optimize=True)
        return
    if fmt == "webp":
        rgb = ensure_rgb(image)
        rgb.save(out_path, format="WEBP", quality=quality, method=6)
        return
    # default PNG keeps alpha
    image.save(out_path, format="PNG", optimize=True)


def load_preset(raw: dict[str, Any]) -> PipelinePreset:
    """Deserialize JSON preset to pipeline objects."""
    adapt = raw["adaptive"]
    output = raw["output"]
    stages = raw.get("stages", {})
    background_removal = raw.get("background_removal", {})
    remove_background = bool(
        stages.get("remove_background", background_removal.get("enabled", output.get("background_remove", False)))
    )
    return PipelinePreset(
        config=PresetConfig(
            name=raw["name"],
            exposure_bias=float(adapt["exposure_bias"]),
            contrast_bias=float(adapt["contrast_bias"]),
            saturation_bias=float(adapt["saturation_bias"]),
            shadow_bias=float(adapt["shadow_bias"]),
            highlight_bias=float(adapt["highlight_bias"]),
            clarity_bias=float(adapt["clarity_bias"]),
            sharpen_bias=float(adapt["sharpen_bias"]),
            relight_bias=float(adapt["relight_bias"]),
            relight_warmth=float(adapt["relight_warmth"]),
            shadow_opacity=float(adapt["shadow_opacity"]),
            white_balance_bias=float(adapt["white_balance_bias"]),
            max_adjustment=float(adapt["max_adjustment"]),
        ),
        output_formats=[str(v) for v in output["formats"]],
        output_sizes=[int(v) for v in output["sizes"]],
        pad_color=str(output["pad_color"]),
        background_mode=str(output["background_mode"]),
        quality=int(output["quality"]),
        remove_background=remove_background,
    )


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    stripped = value.strip().lstrip("#")
    if len(stripped) == 3:
        stripped = "".join(ch * 2 for ch in stripped)
    if len(stripped) != 6:
        return (20, 18, 16)
    return tuple(int(stripped[i : i + 2], 16) for i in (0, 2, 4))

