# Adaptive product photo pipeline

Modular Python pipeline that analyzes each photo and applies adaptive corrections before export.

## What it does

- Per-image analysis (`analyze.py`):
  - luminance mean/stddev
  - shadow/highlight ratio
  - saturation mean
  - edge density
  - RGB channel balance
- Adaptive plan generation:
  - computes image-specific effect strengths from metrics + preset bias
- Modular stages:
  - `background.py` (optional `rembg` removal)
  - `normalize.py` (white balance, exposure, contrast, saturation)
  - `grade.py` (shadow lift, highlight compression, clarity, sharpening)
  - `relight.py` (soft directional light + rim light)
  - `shadow.py` (contact shadow grounding)
- Export:
  - square fit with padding color or transparency
  - multi-size and multi-format output
  - JSON processing report with metrics + applied plan

## Folder structure

- `cli.py` - batch CLI
- `pipeline.py` - orchestration, preset loading, export
- `analyze.py` - metrics extraction + adaptive plan
- `normalize.py` - global correction stage
- `grade.py` - tonal/micro-contrast stage
- `relight.py` - subject relighting stage
- `shadow.py` - contact shadow stage
- `background.py` - optional background removal
- `models.py` - dataclasses
- `helpers.py` - utilities
- `config/preset_pdp_dark.json` - PDP dark-theme profile
- `config/preset_card_portrait.json` - portrait card profile
- `config/preset_square_reco.json` - recommendation square profile

## Install

From repository root:

`python -m pip install -r tools/photo_pipeline/requirements.txt`

## Usage

Run on a folder:

`python -m tools.photo_pipeline.cli --input /path/to/input --output /path/to/output --preset tools/photo_pipeline/config/preset_pdp_dark.json`

Optional:

- `--limit 20`
- `--report-json /path/to/report.json`

## Preset notes

- `preset_pdp_dark.json`
  - 4:5-friendly PDP style grading, dark padding (`#141210`)
  - output sizes: `3000`, `2500`
- `preset_card_portrait.json`
  - stronger relight/clarity for product cards
  - background removal enabled
  - output sizes: `2000`, `1600`, `1200`
- `preset_square_reco.json`
  - square recommendation style
  - background removal enabled
  - output sizes: `2000`, `1200`, `600`

## Report format

JSON report includes:

- source/output file paths
- measured photo metrics
- computed adaptive adjustment plan
- warnings (e.g. `very_dark_input`, `rembg_not_installed_background_removal_skipped`)

