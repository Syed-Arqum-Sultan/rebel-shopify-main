"""CLI entrypoint for adaptive product photo enhancement."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from .helpers import list_images
from .pipeline import load_preset, process_image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adaptive product photo enhancement pipeline.",
    )
    parser.add_argument("--input", required=True, help="Input folder with photos.")
    parser.add_argument("--output", required=True, help="Output folder for processed files.")
    parser.add_argument(
        "--preset",
        required=True,
        help="Path to preset JSON config.",
    )
    parser.add_argument(
        "--report-json",
        default="",
        help="Optional report file path. Defaults to output/report_<timestamp>.json",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional max number of files to process.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_dir = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    preset_path = Path(args.preset).expanduser().resolve()

    if not input_dir.exists():
        parser.error(f"Input directory does not exist: {input_dir}")
    if not preset_path.exists():
        parser.error(f"Preset JSON does not exist: {preset_path}")

    with preset_path.open("r", encoding="utf-8") as f:
        raw_preset = json.load(f)
    preset = load_preset(raw_preset)
    images = list_images(input_dir)
    if args.limit > 0:
        images = images[: args.limit]

    if not images:
        print("No images found. Nothing to process.")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    failures = []

    for img_path in images:
        rel = img_path.relative_to(input_dir)
        img_output_dir = output_dir / rel.parent
        try:
            result = process_image(
                source_path=img_path,
                output_dir=img_output_dir,
                preset=preset,
            )
            results.append(result.to_dict())
            print(f"[ok] {img_path.name} -> {result.output_path}")
        except Exception as exc:
            failures.append({"source_path": str(img_path), "error": str(exc)})
            print(f"[fail] {img_path.name}: {exc}")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    if args.report_json:
        report_path = Path(args.report_json).expanduser().resolve()
    else:
        report_path = output_dir / f"report_{timestamp}.json"

    report = {
        "preset": raw_preset.get("name"),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "processed_count": len(results),
        "failed_count": len(failures),
        "results": results,
        "failures": failures,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Report written: {report_path}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
