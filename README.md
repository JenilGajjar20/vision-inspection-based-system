# Vision Inspection MVP

Small OpenCV-based vision inspection MVP for checking whether a product passes a simple OK/NG condition.

Current validated use case:

- Bottle with cap = `OK`
- Bottle without cap = `NOT OK`
- Low-confidence result = `UNCERTAIN`

The project uses classical computer vision features and a lightweight classifier. It does not use deep learning.

## Folder Structure

Each product has its own recipe folder:

```text
products/
|-- product_1/
|   |-- dataset/
|   |   |-- ok/
|   |   |-- ng/
|   |   `-- rejected/
|   |       |-- ok/
|   |       |-- ng/
|   |       `-- test/
|   |-- test/
|   |-- outputs/
|   `-- roi.json
|
`-- product_2/
    |-- dataset/
    |   |-- ok/
    |   |-- ng/
    |   `-- rejected/
    |-- test/
    |-- outputs/
    `-- roi.json
```

Use a separate product folder for each product/SKU because each product may need a different ROI, camera position, and inspection model.

## Main Scripts

```text
capture_dataset.py   Capture training images from camera
inspect_images.py    Train, evaluate, test, and save annotated outputs
live_inspection.py   Run realtime camera inspection
```

## Capture Training Images

Capture for product 1:

```powershell
python capture_dataset.py --product product_1
```

Capture for product 2:

```powershell
python capture_dataset.py --product product_2
```

Controls:

```text
o = save OK image
n = save NOT OK image
q = quit
```

## Inspect Images

Run product 1:

```powershell
python inspect_images.py --product product_1
```

Run product 2:

```powershell
python inspect_images.py --product product_2
```

Select/reset ROI:

```powershell
python inspect_images.py --product product_1 --reset-roi
```

Set ROI manually:

```powershell
python inspect_images.py --product product_1 --roi X Y W H
```

## Realtime Inspection

After the product has enough OK/NG training images and a saved ROI, run live inspection from the camera:

```powershell
python live_inspection.py --product product_1
```

For another product:

```powershell
python live_inspection.py --product product_2
```

If the wrong camera opens, change the camera index:

```powershell
python live_inspection.py --product product_1 --camera 1
```

Realtime controls:

```text
s = save current annotated frame to the product outputs folder
q = quit
```

Realtime inspection uses simple smoothing:

```text
Last 10 frames are checked.
If 7 or more frames are OK, final stable decision = OK.
If 7 or more frames are NOT OK, final stable decision = NOT OK.
Otherwise, final stable decision = UNCERTAIN.
```

For reliable realtime inspection, keep the camera fixed, keep the lighting stable, and place the product in the same position used when the ROI was selected.

## Workflow

1. Place or capture OK training images in:

```text
products/product_1/dataset/ok
```

2. Place or capture NOT OK training images in:

```text
products/product_1/dataset/ng
```

3. Place separate test images in:

```text
products/product_1/test
```

4. Select ROI around the inspection area:

```powershell
python inspect_images.py --product product_1 --reset-roi
```

5. Run image inspection:

```powershell
python inspect_images.py --product product_1
```

6. Run realtime inspection:

```powershell
python live_inspection.py --product product_1
```

7. Review annotated outputs in:

```text
products/product_1/outputs
```

## Rejected Images

Do not delete bad images. Move them into the rejected folder so they are preserved but excluded from training/testing.

Examples:

```text
products/product_1/dataset/rejected/ok
products/product_1/dataset/rejected/ng
products/product_1/dataset/rejected/test
```

Reject images when:

- ROI is not on the cap/mouth/inspection area
- image is blurry
- lighting is poor
- camera angle is inconsistent
- product is not positioned correctly
- test image is copied from training data

## Output Meaning

The scripts print both prediction and final decision.

```text
Prediction = raw model output
Decision   = final factory-style decision
```

Decision values:

```text
OK         Product passed inspection
NOT OK     Product failed inspection
UNCERTAIN  Confidence is too low; manual review or recapture needed
```

Low-confidence results are marked `UNCERTAIN` instead of forcing an OK/NOT OK decision.

## Important Notes

- Training accuracy alone is not production accuracy.
- Test images must be separate from training images.
- The bottle/product must stay in the same position for ROI-based inspection.
- Camera position, lighting, and product placement are critical.
- More images help only if they are clean and consistently aligned.
- Bad images should be moved to `rejected`, not kept in active training folders.
- Realtime inspection depends on a fixed camera, fixed lighting, and repeatable product placement.

## Current Product Status

`product_1` contains the current bottle cap inspection dataset and ROI.

`product_2` is ready for a second product. Capture its own OK/NG images, select its own ROI, and evaluate it separately.
