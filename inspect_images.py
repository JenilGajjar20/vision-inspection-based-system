import cv2
import os
import json
import numpy as np
import argparse
import re
import hashlib

PRODUCTS_DIR = "products"
DEFAULT_PRODUCT = "product_1"
LOW_CONFIDENCE_LIMIT = 0.10
UNCERTAIN_LABEL = "UNCERTAIN"

OK_DIR = None
NG_DIR = None
TEST_DIR = None
OUTPUT_DIR = None
REJECTED_OK_DIR = None
REJECTED_NG_DIR = None
REJECTED_TEST_DIR = None
ROI_FILE = None


def setup_product_paths(product_name):
    global OK_DIR
    global NG_DIR
    global TEST_DIR
    global OUTPUT_DIR
    global REJECTED_OK_DIR
    global REJECTED_NG_DIR
    global REJECTED_TEST_DIR
    global ROI_FILE

    product_root = os.path.join(PRODUCTS_DIR, product_name)

    OK_DIR = os.path.join(product_root, "dataset", "ok")
    NG_DIR = os.path.join(product_root, "dataset", "ng")
    TEST_DIR = os.path.join(product_root, "test")
    OUTPUT_DIR = os.path.join(product_root, "outputs")
    REJECTED_OK_DIR = os.path.join(product_root, "dataset", "rejected", "ok")
    REJECTED_NG_DIR = os.path.join(product_root, "dataset", "rejected", "ng")
    REJECTED_TEST_DIR = os.path.join(product_root, "dataset", "rejected", "test")
    ROI_FILE = os.path.join(product_root, "roi.json")

    for folder in [
        OK_DIR,
        NG_DIR,
        TEST_DIR,
        OUTPUT_DIR,
        REJECTED_OK_DIR,
        REJECTED_NG_DIR,
        REJECTED_TEST_DIR,
    ]:
        os.makedirs(folder, exist_ok=True)

    return product_root


def natural_key(path):
    name = os.path.basename(path).lower()
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


def get_image_files(folder):
    valid_ext = [".jpg", ".jpeg", ".png"]
    if not os.path.exists(folder):
        return []

    files = [
        os.path.join(folder, file)
        for file in os.listdir(folder)
        if os.path.splitext(file.lower())[1] in valid_ext
    ]
    return sorted(files, key=natural_key)


def print_rejected_summary():
    rejected_ok = len(get_image_files(REJECTED_OK_DIR))
    rejected_ng = len(get_image_files(REJECTED_NG_DIR))
    rejected_test = len(get_image_files(REJECTED_TEST_DIR))
    total_rejected = rejected_ok + rejected_ng + rejected_test

    print(
        "Rejected images excluded from training/testing: "
        f"{total_rejected} "
        f"(OK={rejected_ok}, NOT OK={rejected_ng}, Test={rejected_test})"
    )


def file_hash(path):
    hasher = hashlib.md5()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def check_test_train_separation(training_paths, test_paths):
    training_hashes = {}

    for path in training_paths:
        training_hashes[file_hash(path)] = path

    duplicates = []

    for path in test_paths:
        digest = file_hash(path)

        if digest in training_hashes:
            duplicates.append((path, training_hashes[digest]))

    if not duplicates:
        print("Train/test separation check: PASS")
        return

    print("Train/test separation check: FAIL")
    print("The following test images are exact copies of training images:")

    for test_path, training_path in duplicates:
        print(f"- Test={test_path}, Training={training_path}")


def select_roi_from_sample():
    ok_images = get_image_files(OK_DIR)

    if not ok_images:
        raise Exception(f"No OK images found. Add images in {OK_DIR} first.")

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


def save_roi(roi):
    x, y, w, h = roi
    with open(ROI_FILE, "w") as file:
        json.dump({"x": x, "y": y, "w": w, "h": h}, file)


def load_roi(reset=False, explicit_roi=None):
    if explicit_roi is not None:
        save_roi(explicit_roi)
        return explicit_roi

    if reset or not os.path.exists(ROI_FILE):
        return select_roi_from_sample()

    with open(ROI_FILE, "r") as file:
        data = json.load(file)

    return data["x"], data["y"], data["w"], data["h"]


def get_label_color(result):
    if result == "OK":
        return (0, 255, 0)

    if result == "NOT OK":
        return (0, 0, 255)

    return (0, 255, 255)


def draw_prediction(image, roi, result, color=None):
    x, y, w, h = roi
    color = color or get_label_color(result)

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

    return image


def draw_info_lines(image, lines, start_y=90, color=(255, 255, 255)):
    y = start_y

    for line in lines:
        cv2.putText(
            image,
            line,
            (30, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2
        )
        y += 35

    return image


def save_roi_preview(roi):
    ok_images = get_image_files(OK_DIR)

    if not ok_images:
        return

    sample = cv2.imread(ok_images[0])

    if sample is None:
        return

    preview = sample.copy()
    x, y, w, h = roi
    cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 255), 3)
    cv2.putText(
        preview,
        "ROI",
        (x, max(35, y - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 255, 255),
        3
    )
    output_path = os.path.join(OUTPUT_DIR, "roi_preview.jpg")
    cv2.imwrite(output_path, preview)
    print(f"ROI preview saved: {output_path}")


def extract_features(image, roi):
    x, y, w, h = roi
    crop = image[y:y+h, x:x+w]

    if crop.size == 0:
        raise Exception("Invalid crop. Check ROI.")

    crop = cv2.GaussianBlur(crop, (5, 5), 0)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    # Use a few fixed zones inside the selected ROI. This stays simple, but it
    # captures where cap/mouth differences normally appear.
    zones = [
        (0.00, 0.72, 0.00, 1.00),  # upper cap/mouth area
        (0.00, 0.55, 0.15, 0.85),  # center of cap
        (0.15, 0.75, 0.20, 0.80),  # middle opening/metal region
        (0.45, 1.00, 0.00, 1.00),  # lower ROI/neck contrast
    ]

    features = []

    for y1, y2, x1, x2 in zones:
        zone_gray = gray[
            int(h * y1):int(h * y2),
            int(w * x1):int(w * x2)
        ]
        zone_hsv = hsv[
            int(h * y1):int(h * y2),
            int(w * x1):int(w * x2)
        ]

        edges = cv2.Canny(zone_gray, 50, 150)
        metal_mask = (
            (zone_hsv[:, :, 1] < 75) &
            (zone_hsv[:, :, 2] > 90) &
            (zone_gray > 75)
        )

        features.extend([
            np.mean(zone_gray),
            np.std(zone_gray),
            np.percentile(zone_gray, 10),
            np.percentile(zone_gray, 90),
            np.count_nonzero(zone_gray < 55) / zone_gray.size,
            np.count_nonzero(zone_gray > 180) / zone_gray.size,
            np.count_nonzero(metal_mask) / metal_mask.size,
            np.count_nonzero(edges) / edges.size,
        ])

    return np.array(features)


def build_training_data(roi):
    features = []
    labels = []
    paths = []

    for path in get_image_files(OK_DIR):
        image = cv2.imread(path)
        if image is not None:
            features.append(extract_features(image, roi))
            labels.append("OK")
            paths.append(path)

    for path in get_image_files(NG_DIR):
        image = cv2.imread(path)
        if image is not None:
            features.append(extract_features(image, roi))
            labels.append("NOT OK")
            paths.append(path)

    if len(features) == 0:
        raise Exception("No training images found.")

    return np.array(features), np.array(labels), paths


def train_simple_classifier(features, labels):
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0) + 1e-6

    normalized = (features - mean) / std

    ok_features = normalized[labels == "OK"]
    ng_features = normalized[labels == "NOT OK"]
    ok_center = np.mean(ok_features, axis=0)
    ng_center = np.mean(ng_features, axis=0)

    # Fisher linear discriminant: a tiny classical classifier, no deep learning.
    # It learns which ROI features best separate OK from NOT OK.
    regularization = np.eye(normalized.shape[1]) * 0.5
    scatter = (
        np.cov(ok_features, rowvar=False) +
        np.cov(ng_features, rowvar=False) +
        regularization
    )
    weights = np.linalg.pinv(scatter).dot(ok_center - ng_center)
    threshold = 0.5 * weights.dot(ok_center + ng_center)

    model = {
        "mean": mean,
        "std": std,
        "ok_center": ok_center,
        "ng_center": ng_center,
        "weights": weights,
        "threshold": threshold,
        "train_features": normalized,
        "train_labels": labels
    }

    return model


def calculate_confidence(ok_distance, ng_distance):
    total_distance = ok_distance + ng_distance

    if total_distance == 0:
        return 0

    return abs(ok_distance - ng_distance) / total_distance


def final_decision(prediction, confidence):
    if confidence < LOW_CONFIDENCE_LIMIT:
        return UNCERTAIN_LABEL

    return prediction


def predict_from_normalized(normalized, model):
    ok_distance = np.linalg.norm(normalized - model["ok_center"])
    ng_distance = np.linalg.norm(normalized - model["ng_center"])

    score = normalized.dot(model["weights"]) - model["threshold"]
    result = "OK" if score > 0 else "NOT OK"
    confidence = calculate_confidence(ok_distance, ng_distance)

    return result, ok_distance, ng_distance, confidence


def predict(image, roi, model):
    feature = extract_features(image, roi)
    normalized = (feature - model["mean"]) / model["std"]

    return predict_from_normalized(normalized, model)


def evaluate_training_data(features, labels, paths, roi, model):
    correct = 0
    total = len(labels)
    failed_images = []
    low_confidence_images = []
    uncertain_images = []
    training_output_dir = os.path.join(OUTPUT_DIR, "training")
    os.makedirs(training_output_dir, exist_ok=True)

    print("\nTraining Data Evaluation:")
    print("-------------------------")

    for i in range(total):
        normalized = (features[i] - model["mean"]) / model["std"]

        predicted, ok_distance, ng_distance, confidence = predict_from_normalized(
            normalized, model)
        decision = final_decision(predicted, confidence)
        actual = labels[i]
        filename = os.path.basename(paths[i])

        status = "PASS" if predicted == actual else "FAIL"
        confidence_text = f"{confidence * 100:.1f}%"

        print(
            f"{filename}: Actual={actual}, Predicted={predicted}, Decision={decision}, "
            f"Confidence={confidence_text}, "
            f"OK_Distance={ok_distance:.2f}, NG_Distance={ng_distance:.2f}, {status}"
        )

        if predicted == actual:
            correct += 1
        else:
            failed_images.append(filename)

        if confidence < LOW_CONFIDENCE_LIMIT:
            low_confidence_images.append(filename)
            uncertain_images.append(filename)

        image = cv2.imread(paths[i])
        if image is not None:
            color = get_label_color(decision)
            annotated = draw_prediction(image, roi, f"{decision} / {actual}", color)
            annotated = draw_info_lines(
                annotated,
                [
                    f"Status: {status}",
                    f"Prediction: {predicted}",
                    f"Confidence: {confidence * 100:.1f}%",
                    f"OK dist: {ok_distance:.2f}",
                    f"NG dist: {ng_distance:.2f}"
                ],
                color=color
            )
            cv2.imwrite(os.path.join(training_output_dir, filename), annotated)

    accuracy = (correct / total) * 100

    print("-------------------------")
    print(f"Training accuracy: {accuracy:.2f}%")
    print(f"Annotated training images saved: {training_output_dir}")

    if failed_images:
        print("Failed training images:")
        for filename in failed_images:
            print(f"- {filename}")
    else:
        print("Failed training images: None")

    if low_confidence_images:
        print(f"Low confidence training images (< {LOW_CONFIDENCE_LIMIT * 100:.0f}%):")
        for filename in low_confidence_images:
            print(f"- {filename}")

    if uncertain_images:
        print("Training images marked UNCERTAIN for factory decision:")
        for filename in uncertain_images:
            print(f"- {filename}")

    return accuracy


def test_images(roi, model):
    test_images_list = get_image_files(TEST_DIR)
    ok_count = 0
    ng_count = 0
    uncertain_count = 0
    total = 0

    if not test_images_list:
        print("No images found in test folder.")
        return

    print("\nTest Image Results:")
    print("-------------------")

    for path in test_images_list:
        image = cv2.imread(path)

        if image is None:
            continue

        result, ok_distance, ng_distance, confidence = predict(image, roi, model)
        decision = final_decision(result, confidence)

        image = draw_prediction(image, roi, decision)
        image = draw_info_lines(
            image,
            [
                f"Prediction: {result}",
                f"Confidence: {confidence * 100:.1f}%",
                f"OK dist: {ok_distance:.2f}",
                f"NG dist: {ng_distance:.2f}"
            ],
            color=get_label_color(decision)
        )

        filename = os.path.basename(path)
        output_path = os.path.join(OUTPUT_DIR, filename)

        cv2.imwrite(output_path, image)

        total += 1
        if decision == "OK":
            ok_count += 1
        elif decision == "NOT OK":
            ng_count += 1
        else:
            uncertain_count += 1

        print(
            f"{filename} => Decision={decision}, Prediction={result}, "
            f"Confidence={confidence * 100:.1f}%, Output={output_path}"
        )

    print("-------------------")
    print(f"Total test images: {total}")
    print(f"OK count: {ok_count}")
    print(f"NOT OK count: {ng_count}")
    print(f"UNCERTAIN count: {uncertain_count}")
    print(f"Saved output path: {OUTPUT_DIR}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate bottle cap inspection images."
    )
    parser.add_argument(
        "--product",
        default=DEFAULT_PRODUCT,
        help=f"Product recipe folder to use under {PRODUCTS_DIR}. Default: {DEFAULT_PRODUCT}."
    )
    parser.add_argument(
        "--reset-roi",
        action="store_true",
        help="Select a new ROI from the first OK image and save it to roi.json."
    )
    parser.add_argument(
        "--roi",
        nargs=4,
        type=int,
        metavar=("X", "Y", "W", "H"),
        help="Set ROI directly and save it to roi.json."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    product_root = setup_product_paths(args.product)
    print(f"Using product: {args.product} ({product_root})")

    roi = load_roi(reset=args.reset_roi, explicit_roi=tuple(args.roi) if args.roi else None)
    print(f"Using ROI: x={roi[0]}, y={roi[1]}, w={roi[2]}, h={roi[3]}")
    print_rejected_summary()
    save_roi_preview(roi)

    features, labels, paths = build_training_data(roi)
    test_paths = get_image_files(TEST_DIR)
    check_test_train_separation(paths, test_paths)
    model = train_simple_classifier(features, labels)

    accuracy = evaluate_training_data(features, labels, paths, roi, model)

    if accuracy < 85:
        print("Warning: Accuracy is low.")
        print("Check outputs/roi_preview.jpg and outputs/training first.")
        print("If the rectangle is not on the cap or bottle mouth, run: python inspect_images.py --reset-roi")
        print("For best results, recapture OK and NOT OK images with the bottle in the same position.")

    test_images(roi, model)


if __name__ == "__main__":
    main()
