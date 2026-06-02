# Vision Inspection MVP

Lightweight Python/OpenCV vision inspection system for product quality checking.

The project supports product-wise datasets, ROI-based image inspection, realtime camera inspection, confidence handling, CSV logging, and text/HTML report generation.

This phase uses classical OpenCV feature extraction and a lightweight classifier. It does not use deep learning.

## Phase 1 Scope

Phase 1 covers the MVP workflow:

```text
1. Capture product images
2. Select inspection ROI
3. Train/evaluate image inspection
4. Run realtime inspection
5. Save inspection logs
6. Generate inspection reports
```

Phase 1 details are documented in:

```text
docs/phase_1_summary.md
```

## Product Structure

Each product has its own recipe folder:

```text
products/
`-- <product_name>/
    |-- dataset/
    |   |-- ok/
    |   |-- ng/
    |   `-- rejected/
    |       |-- ok/
    |       |-- ng/
    |       `-- test/
    |-- test/
    |-- outputs/
    `-- roi.json
```

Use a separate product folder for each product/SKU. Do not mix images between products.

## Main Scripts

```text
capture_dataset.py   Capture OK, NOT OK, and test images from camera
inspect_images.py    Train, evaluate, test, and save annotated outputs
live_inspection.py   Run realtime camera inspection with smoothing and logging
generate_report.py   Summarize realtime inspection CSV logs
```

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Workflow

Replace `<product_name>` with the product folder name, for example `product_3` or `product_4`.

```powershell
python capture_dataset.py --product <product_name>
python inspect_images.py --product <product_name> --reset-roi
python inspect_images.py --product <product_name>
python live_inspection.py --product <product_name>
python generate_report.py --product <product_name>
```

## Capture Controls

```text
o = save training OK image
n = save training NOT OK image
t = save test image
q = quit
```

Captured images are saved under:

```text
products/<product_name>/dataset/ok
products/<product_name>/dataset/ng
products/<product_name>/test
```

## Image Inspection

Run inspection:

```powershell
python inspect_images.py --product <product_name>
```

Select/reset ROI:

```powershell
python inspect_images.py --product <product_name> --reset-roi
```

Set ROI manually:

```powershell
python inspect_images.py --product <product_name> --roi X Y W H
```

Annotated outputs are saved in:

```text
products/<product_name>/outputs
```

## Realtime Inspection

Run realtime inspection:

```powershell
python live_inspection.py --product <product_name>
```

If the wrong camera opens:

```powershell
python live_inspection.py --product <product_name> --camera 1
```

Realtime controls:

```text
s = save current annotated frame
q = quit
```

Realtime smoothing:

```text
Last 10 frames are checked.
If 6 or more frames are OK, final stable decision = OK.
If 6 or more frames are NOT OK, final stable decision = NOT OK.
If confident frames agree and the rest are UNCERTAIN, the confident result is used.
Otherwise, final stable decision = UNCERTAIN.
```

The current low-confidence threshold is 8%.

## Logs And Reports

Realtime inspection writes:

```text
products/<product_name>/outputs/inspection_log.csv
```

Generate reports:

```powershell
python generate_report.py --product <product_name>
```

Report outputs:

```text
products/<product_name>/outputs/inspection_report.txt
products/<product_name>/outputs/inspection_report.html
```

## Decision Labels

```text
OK         Product passed inspection
NOT OK     Product failed inspection
UNCERTAIN  Confidence is too low; review or recapture needed
```

## Rejected Images

Do not delete bad images. Move them into the rejected folder so they are preserved but excluded from training/testing:

```text
products/<product_name>/dataset/rejected/ok
products/<product_name>/dataset/rejected/ng
products/<product_name>/dataset/rejected/test
```

Reject images when:

- ROI is not on the inspection area
- image is blurry
- lighting is poor
- camera angle is inconsistent
- product is not positioned correctly
- test image is copied from training data

## Limitations

- The ROI is fixed; the product must be placed under the same ROI during live inspection.
- Camera position, product position, and lighting must stay stable.
- Laptop camera quality can cause low-confidence frames.
- `UNCERTAIN` is expected when the image is unclear.
- Training accuracy is useful for debugging, but it is not production accuracy.
- This is an MVP, not a production-certified quality system.

## Roadmap

```text
Phase 1: Vision Inspection MVP - current
Phase 2: Database + dashboard
Phase 3: AI/ML model training
Phase 4: Industrial camera + lighting setup
Phase 5: PLC/MQTT integration
```
