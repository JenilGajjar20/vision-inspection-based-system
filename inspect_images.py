import cv2
import os
import json
import numpy as np

OK_DIR = "dataset/ok"
NG_DIR = "dataset/ng"
TEST_DIR = "test"
OUTPUT_DIR = "outputs"
ROI_FILE = "roi.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_image_files(folder):
    valid_ext = [".jpg", ".jpeg", ".png"]
    return [
        os.path.join(folder, file)
        for file in os.listdir(folder)
        if os.path.splitext(file.lower())[1] in valid_ext
    ]


def select_roi_from_sample():
    ok_images = get_image_files(OK_DIR)

    if not ok_images:
        raise Exception("No OK images found. Add images in dataset/ok first.")

    sample = cv2.imread(ok_images[0])

    if sample is None:
        raise Exception("Could not read sample image.")

    print("Select the cap area using mouse, then press ENTER.")
    roi = cv2.selectROI("Select Cap ROI", sample, showCrosshair=True)
    cv2.destroyWindow("Select Cap ROI")

    x, y, w, h = roi

    if w == 0 or h == 0:
        raise Exception("Invalid ROI selected.")

    with open(ROI_FILE, "w") as file:
        json.dump({"x": x, "y": y, "w": w, "h": h}, file)

    return x, y, w, h


def load_roi():
    if not os.path.exists(ROI_FILE):
        return select_roi_from_sample()

    with open(ROI_FILE, "r") as file:
        data = json.load(file)

    return data["x"], data["y"], data["w"], data["h"]


def extract_features(image, roi):
    x, y, w, h = roi
    crop = image[y:y+h, x:x+w]

    if crop.size == 0:
        raise Exception("Invalid crop. Check ROI.")

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    mean_gray = np.mean(gray)
    std_gray = np.std(gray)

    mean_h = np.mean(hsv[:, :, 0])
    mean_s = np.mean(hsv[:, :, 1])
    mean_v = np.mean(hsv[:, :, 2])

    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = np.count_nonzero(edges) / edges.size

    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    object_ratio = np.count_nonzero(thresh) / thresh.size

    features = np.array([
        mean_gray,
        std_gray,
        mean_h,
        mean_s,
        mean_v,
        edge_ratio,
        object_ratio
    ])

    return features


def build_training_data(roi):
    features = []
    labels = []

    for path in get_image_files(OK_DIR):
        image = cv2.imread(path)
        if image is not None:
            features.append(extract_features(image, roi))
            labels.append("OK")

    for path in get_image_files(NG_DIR):
        image = cv2.imread(path)
        if image is not None:
            features.append(extract_features(image, roi))
            labels.append("NOT OK")

    if len(features) == 0:
        raise Exception("No training images found.")

    return np.array(features), np.array(labels)


def train_simple_classifier(features, labels):
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0) + 1e-6

    normalized = (features - mean) / std

    ok_center = np.mean(normalized[labels == "OK"], axis=0)
    ng_center = np.mean(normalized[labels == "NOT OK"], axis=0)

    model = {
        "mean": mean,
        "std": std,
        "ok_center": ok_center,
        "ng_center": ng_center
    }

    return model


def predict(image, roi, model):
    feature = extract_features(image, roi)
    normalized = (feature - model["mean"]) / model["std"]

    ok_distance = np.linalg.norm(normalized - model["ok_center"])
    ng_distance = np.linalg.norm(normalized - model["ng_center"])

    if ok_distance < ng_distance:
        return "OK", ok_distance, ng_distance
    else:
        return "NOT OK", ok_distance, ng_distance


def evaluate_training_data(features, labels, roi, model):
    correct = 0
    total = len(labels)

    print("\nTraining Data Evaluation:")
    print("-------------------------")

    for i in range(total):
        normalized = (features[i] - model["mean"]) / model["std"]

        ok_distance = np.linalg.norm(normalized - model["ok_center"])
        ng_distance = np.linalg.norm(normalized - model["ng_center"])

        predicted = "OK" if ok_distance < ng_distance else "NOT OK"
        actual = labels[i]

        status = "PASS" if predicted == actual else "FAIL"

        print(
            f"Image {i + 1}: Actual={actual}, Predicted={predicted}, "
            f"OK_Distance={ok_distance:.2f}, NG_Distance={ng_distance:.2f}, {status}"
        )

        if predicted == actual:
            correct += 1

    accuracy = (correct / total) * 100

    print("-------------------------")
    print(f"Training accuracy: {accuracy:.2f}%")

    return accuracy


def test_images(roi, model):
    test_images_list = get_image_files(TEST_DIR)

    if not test_images_list:
        print("No images found in test folder.")
        return

    for path in test_images_list:
        image = cv2.imread(path)

        if image is None:
            continue

        result, ok_distance, ng_distance = predict(image, roi, model)

        x, y, w, h = roi

        color = (0, 255, 0) if result == "OK" else (0, 0, 255)

        cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            image,
            result,
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            color,
            3
        )

        filename = os.path.basename(path)
        output_path = os.path.join(OUTPUT_DIR, filename)

        cv2.imwrite(output_path, image)

        print(f"{filename} => {result}")


def main():
    roi = load_roi()

    features, labels = build_training_data(roi)
    model = train_simple_classifier(features, labels)

    accuracy = evaluate_training_data(features, labels, roi, model)

    if accuracy < 85:
        print("Warning: Accuracy is low.")
        print("Improve camera position, lighting, ROI, or collect more images.")

    test_images(roi, model)


if __name__ == "__main__":
    main()
