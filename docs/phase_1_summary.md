# Phase 1 Summary

Phase 1 delivers a lightweight OpenCV-based vision inspection MVP for product quality checking.

## Scope

Phase 1 includes:

- Product-wise folder structure
- Dataset capture for OK, NOT OK, and test images
- Manual ROI selection per product
- ROI-based feature extraction
- Lightweight OK / NOT OK classifier
- Confidence scoring
- UNCERTAIN handling for low-confidence results
- Image-based training and test evaluation
- Annotated output images
- Realtime camera inspection
- Multi-frame realtime smoothing
- CSV inspection logging
- Text and HTML inspection reports
- Basic project setup and documentation

## Main Commands

```powershell
python capture_dataset.py --product <product_name>
python inspect_images.py --product <product_name> --reset-roi
python inspect_images.py --product <product_name>
python live_inspection.py --product <product_name>
python generate_report.py --product <product_name>
```

## Outputs

Each product writes outputs under:

```text
products/<product_name>/outputs
```

Important output files:

```text
roi_preview.jpg
inspection_log.csv
inspection_report.txt
inspection_report.html
```

## Status

Phase 1 is complete as an MVP workflow.

The system is suitable for controlled image-based and realtime inspection experiments. It is not production-certified and requires stable camera position, stable lighting, and repeatable product placement.

## Next Phases

```text
Phase 2: Database + dashboard
Phase 3: AI/ML model training
Phase 4: Industrial camera + lighting setup
Phase 5: PLC/MQTT integration
```
