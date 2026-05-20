Product recipes live here.

Each product has its own dataset, test images, outputs, rejected images, and
roi.json. Keep different products separate because each product may need a
different ROI and inspection model.

Run product 1:
python inspect_images.py --product product_1

Run product 2:
python inspect_images.py --product product_2

Capture images for product 1:
python capture_dataset.py --product product_1

Capture images for product 2:
python capture_dataset.py --product product_2
