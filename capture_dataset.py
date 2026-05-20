import cv2
import os
from datetime import datetime

OK_DIR = "dataset/ok"
NG_DIR = "dataset/ng"

os.makedirs(OK_DIR, exist_ok=True)
os.makedirs(NG_DIR, exist_ok=True)

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
