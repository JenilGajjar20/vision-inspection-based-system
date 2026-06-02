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

Product names should use only letters, numbers, and underscores.

Good examples:

```text
product_4
paper_clip
metal_bracket
```

Avoid spaces and special characters.

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

## Database Setup

Phase 2 uses a local MySQL database.

Default database name:

```text
vision_inspection_qms
```

Configure database credentials with environment variables:

```powershell
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
$env:DB_USER="root"
$env:DB_PASSWORD="your_password"
$env:DB_NAME="vision_inspection_qms"
```

Initialize the database schema:

```powershell
python init_database.py
```

This creates:

```text
products
inspection_records
```

Keep real credentials out of Git. Use `.env.example` as a reference only.

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

Show fewer or more recent log rows:

```powershell
python generate_report.py --product <product_name> --recent 5
```

Report outputs:

```text
products/<product_name>/outputs/inspection_report.txt
products/<product_name>/outputs/inspection_report.html
```

Reports include:

```text
generated timestamp
product name
ROI
training image counts
test image count
rejected image count
OK / NOT OK / UNCERTAIN summary
recent inspection rows
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

## Troubleshooting

Camera does not open:

```text
Try a different camera index, for example: --camera 1
Check if another application is already using the camera.
```

ROI is wrong:

```text
Run inspect_images.py with --reset-roi and select the inspection area again.
```

Too many UNCERTAIN results:

```text
Improve lighting, fix camera/product position, and keep the product inside the ROI.
Capture cleaner OK and NOT OK images if needed.
```

inspection_log.csv is missing:

```text
Run live_inspection.py first. The log is created during realtime inspection.
```

Invalid product name:

```text
Use letters, numbers, and underscores only. Example: paper_clip
```

## Roadmap

```text
Phase 1: Vision Inspection MVP - current
Phase 2: Database + dashboard
Phase 3: AI/ML model training
Phase 4: Industrial camera + lighting setup
Phase 5: PLC/MQTT integration
```
