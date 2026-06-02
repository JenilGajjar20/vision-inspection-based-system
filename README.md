# Vision Inspection MVP

Lightweight Python/OpenCV vision inspection MVP for product quality checking.

The system supports product-wise inspection recipes, ROI-based image inspection, realtime camera inspection, confidence handling, CSV logging, and QMS-style report generation.

It uses classical computer vision features and a lightweight classifier. It does not use deep learning.

## Main Demo

Current main demo product:

```text
product_3
```

Current demo use case:

```text
OK         = product is not broken
NOT OK     = product is broken/damaged
UNCERTAIN  = confidence is too low; review or recapture needed
```

`product_1` and `product_2` are kept as examples of multi-product support. Do not mix images between products.

## Folder Structure

Each product has its own recipe folder:

```text
products/
|-- product_1/
|-- product_2/
`-- product_3/
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

Each product can have a different ROI, dataset, outputs, and inspection behavior.

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

## Demo Flow

Use this flow for `product_3`:

```powershell
python capture_dataset.py --product product_3
python inspect_images.py --product product_3 --reset-roi
python inspect_images.py --product product_3
python live_inspection.py --product product_3
python generate_report.py --product product_3
```

Capture controls:

```text
o = save training OK image
n = save training NOT OK image
t = save test image
q = quit
```

Realtime controls:

```text
s = save current annotated frame to the product outputs folder
q = quit
```

## Image Inspection

Run image-based inspection:

```powershell
python inspect_images.py --product product_3
```

Select or reset ROI:

```powershell
python inspect_images.py --product product_3 --reset-roi
```

Set ROI manually:

```powershell
python inspect_images.py --product product_3 --roi X Y W H
```

Image inspection saves annotated output images in:

```text
products/product_3/outputs
```

## Realtime Inspection

Run realtime inspection:

```powershell
python live_inspection.py --product product_3
```

If the wrong camera opens, change the camera index:

```powershell
python live_inspection.py --product product_3 --camera 1
```

Realtime inspection uses simple smoothing:

```text
Last 10 frames are checked.
If 6 or more frames are OK, final stable decision = OK.
If 6 or more frames are NOT OK, final stable decision = NOT OK.
If confident frames agree and the rest are UNCERTAIN, the confident result is used.
Otherwise, final stable decision = UNCERTAIN.
```

The current low-confidence threshold is 8%.

## Logs And Reports

Realtime inspection writes a CSV log:

```text
products/product_3/outputs/inspection_log.csv
```

The log records:

```text
timestamp
product
stable decision
frame decision
prediction
confidence
OK/NG distance values
smoothing history counts
event type
saved image path
```

Generate a report:

```powershell
python generate_report.py --product product_3
```

The report is saved to:

```text
products/product_3/outputs/inspection_report.txt
products/product_3/outputs/inspection_report.html
```

## Current Product 3 Status

For the current captured `product_3` dataset:

```text
Image inspection completed successfully.
Train/test separation check passed.
35 separate test images were evaluated.
Test output summary: 15 OK, 20 NOT OK, 0 UNCERTAIN.
Realtime inspection works for MVP demo under controlled setup.
CSV inspection logging works.
Text and HTML report generation works.
```

Training accuracy is useful for debugging, but it is not production accuracy.

## Rejected Images

Do not delete bad images. Move them into the rejected folder so they are preserved but excluded from training/testing.

Examples:

```text
products/product_3/dataset/rejected/ok
products/product_3/dataset/rejected/ng
products/product_3/dataset/rejected/test
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
- The camera and product position must stay fixed.
- Lighting must be stable.
- Laptop camera quality can cause low-confidence frames.
- `UNCERTAIN` is expected when the image is unclear.
- This is an MVP, not a production-certified quality system.

## Future Roadmap

Useful future improvements:

- Add product recipe/config files for per-product thresholds and smoothing settings.
- Store inspection logs in a database.
- Add batch, shift, operator, and line information.
- Build a dashboard for OK/NG trends and rejection percentage.
- Add user review workflow for `UNCERTAIN` results.
- Integrate industrial camera and controlled lighting.
- Add PLC/SCADA/MES integration.
- Evaluate classical ML models such as SVM, Random Forest, or Logistic Regression.
- Consider deep learning later only if ROI/OpenCV inspection is not enough.
