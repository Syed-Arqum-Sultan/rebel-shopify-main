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
- Solid backgrounds (`background_mode: solid`): cutouts from `rembg` are flattened onto `pad_color` **before** grading so corrections match infinite black / charcoal PDPs (not premultiplied black fringes).

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
- `config/preset_pdp_dark.json` - PDP dark-theme profile (pure black pad `#000000`)
- `config/preset_pdp_charcoal.json` - same grading as PDP dark, warm charcoal pad `#141210`
- `config/preset_pdp_infinite_black.json` - **rembg on**, `#000000` pad — fabric/messy BG → subject on infinite black (expect manual fixes on translucent acetate)
- `config/preset_card_portrait.json` - portrait card profile
- `config/preset_square_reco.json` - recommendation square profile
- `config/preset_black_bg_clean.json` - black-background cleanup profile

## Install

**Windows (`rembg` / ONNX):** If reports show `rembg_not_ready_background_removal_skipped` but `pip show rembg` works, `onnxruntime` often failed to load native DLLs. Install **[Microsoft Visual C++ Redistributable (x64)](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)** (latest supported), reopen the terminal, then verify:

`tools/photo_pipeline/.venv/Scripts/python.exe -c "import onnxruntime; print(onnxruntime.__version__)"`

Recommended (creates `tools/photo_pipeline/.venv` and installs into it):

`powershell -ExecutionPolicy Bypass -File tools/photo_pipeline/install.ps1`

Or manually from repository root:

`python -m venv tools/photo_pipeline/.venv`

`tools\photo_pipeline\.venv\Scripts\python.exe -m pip install -r tools/photo_pipeline/requirements.txt`

## Usage

Run on a folder (use the venv interpreter if you installed via `install.ps1`):

`tools/photo_pipeline/.venv/Scripts/python.exe -m tools.photo_pipeline.cli --input /path/to/input --output /path/to/output --preset tools/photo_pipeline/config/preset_pdp_dark.json` (Windows; on macOS/Linux use `tools/photo_pipeline/.venv/bin/python`)

Optional:

- `--limit 20`
- `--report-json /path/to/report.json`

## Preset notes

- `preset_pdp_dark.json`
  - 4:5-friendly PDP style grading, solid **black** padding (`#000000`) — matches luxury eyewear on pure black
  - output sizes: `3000`, `2500`
- `preset_pdp_charcoal.json`
  - identical adaptive tuning to `pdp_dark`, padding `#141210` if you want a slightly softer dark surround
- `preset_pdp_infinite_black.json`
  - **Infinite black:** removes background with `rembg`, composites onto `#000000`, then same grading family as PDP dark (slightly softer relight vs `pdp_dark` for flatter void). Use when originals show fabric/tabletop but you want a uniform black field.
- `preset_card_portrait.json`
  - stronger relight/clarity for product cards
  - background removal enabled
  - output sizes: `2000`, `1600`, `1200`
- `preset_square_reco.json`
  - square recommendation style
  - background removal enabled
  - output sizes: `2000`, `1200`, `600`
- `preset_black_bg_clean.json`
  - tuned for already-black studio backgrounds
  - lighter relight and shadow bias to prevent haze
  - output sizes: `2000`, `1600`, `1200`

## Black background quality upgrades

The pipeline now includes dark-scene safeguards:

- subject/background masks are derived before grading and relighting
- tone/clarity/relight are applied primarily on subject regions
- black-floor protection prevents lifting near-black pixels
- contact shadow auto-skips when image alpha covers most of the frame
- dark-background detection can force pure-black output padding

## Report format

JSON report includes:

- source/output file paths
- measured photo metrics
- computed adaptive adjustment plan
- warnings (e.g. `very_dark_input`, `rembg_not_installed_background_removal_skipped`)

