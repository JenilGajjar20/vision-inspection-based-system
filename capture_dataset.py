import cv2
import os
from datetime import datetime
import argparse

PRODUCTS_DIR = "products"
DEFAULT_PRODUCT = "product_1"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Capture OK/NOT OK training images for a product recipe."
    )
    parser.add_argument(
        "--product",
        default=DEFAULT_PRODUCT,
        help=f"Product recipe folder under {PRODUCTS_DIR}. Default: {DEFAULT_PRODUCT}."
    )
    return parser.parse_args()


args = parse_args()
product_root = os.path.join(PRODUCTS_DIR, args.product)
OK_DIR = os.path.join(product_root, "dataset", "ok")
NG_DIR = os.path.join(product_root, "dataset", "ng")

os.makedirs(OK_DIR, exist_ok=True)
os.makedirs(NG_DIR, exist_ok=True)

print(f"Capturing for product: {args.product} ({product_root})")

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    raise Exception("Could not open camera")

print("Controls:")
print("Press 'o' to save OK image")
print("Press 'n' to save NOT OK image")
print("Press 'q' to quit")

while True:
    ret, frame = camera.read()

    if not ret:
        print("Failed to capture frame")
        break

    cv2.imshow("Capture Dataset", frame)

    key = cv2.waitKey(1) & 0xFF

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    if key == ord("o"):
        path = os.path.join(OK_DIR, f"ok_{timestamp}.jpg")
        cv2.imwrite(path, frame)
        print(f"Saved OK image: {path}")

    elif key == ord("n"):
        path = os.path.join(NG_DIR, f"ng_{timestamp}.jpg")
        cv2.imwrite(path, frame)
        print(f"Saved NG image: {path}")

    elif key == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
