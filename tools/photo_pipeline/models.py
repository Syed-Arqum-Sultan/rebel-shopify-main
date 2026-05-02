"""Typed models for adaptive photo enhancement."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class PhotoMetrics:
    """Extracted image statistics used for adaptive processing."""

    luminance_mean: float
    luminance_std: float
    shadow_ratio: float
    highlight_ratio: float
    saturation_mean: float
    edge_density: float
    red_mean: float
    green_mean: float
    blue_mean: float
    aspect_ratio: float


@dataclass(slots=True)
class AdjustmentPlan:
    """Computed, bounded adjustments per photo."""

    preset_name: str
    exposure: float
    contrast: float
    saturation: float
    shadow_lift: float
    highlight_compress: float
    clarity: float
    sharpen: float
    relight_strength: float
    relight_warmth: float
    contact_shadow_opacity: float
    white_balance_shift: float
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProcessResult:
    """Output metadata for reporting."""

    source_path: str
    output_path: str
    preset_name: str
    metrics: PhotoMetrics
    plan: AdjustmentPlan
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "output_path": self.output_path,
            "preset_name": self.preset_name,
            "metrics": asdict(self.metrics),
            "plan": {
                **asdict(self.plan),
                "notes": list(self.plan.notes),
            },
            "warnings": list(self.warnings),
        }
