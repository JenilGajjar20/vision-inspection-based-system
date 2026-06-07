import argparse
import csv
import os
from datetime import datetime

import cv2

import database
import inspect_images


SMOOTHING_WINDOW = 10
STABLE_REQUIRED_COUNT = 6
LOG_FILE_NAME = "inspection_log.csv"
LOG_FIELDS = [
    "timestamp",
    "product",
    "stable_decision",
    "frame_decision",
    "prediction",
    "confidence_percent",
    "ok_distance",
    "ng_distance",
    "history_ok",
    "history_ng",
    "history_uncertain",
    "event",
    "image_path",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run realtime product inspection from a camera."
    )
    parser.add_argument(
        "--product",
        type=inspect_images.validate_product_name,
        default=inspect_images.DEFAULT_PRODUCT,
        help=(
            f"Product recipe folder under {inspect_images.PRODUCTS_DIR}. "
            f"Default: {inspect_images.DEFAULT_PRODUCT}."
        )
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera index. Default: 0."
    )
    parser.add_argument(
        "--disable-db-log",
        action="store_true",
        help="Disable database logging and keep only CSV logging."
    )
    return parser.parse_args()


def get_stable_decision(decision_history):
    ok_count = decision_history.count("OK")
    ng_count = decision_history.count("NOT OK")
    confident_count = ok_count + ng_count

    if ok_count >= STABLE_REQUIRED_COUNT:
        return "OK"

    if ng_count >= STABLE_REQUIRED_COUNT:
        return "NOT OK"

    # If uncertain frames are mixed in, trust the confident frames only
    # when every confident frame agrees on the same result.
    if confident_count >= 3 and ng_count == 0:
        return "OK"

    if confident_count >= 3 and ok_count == 0:
        return "NOT OK"

    return inspect_images.UNCERTAIN_LABEL


def save_live_frame(image, product_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"live_{product_name}_{timestamp}.jpg"
    output_path = os.path.join(inspect_images.OUTPUT_DIR, filename)
    cv2.imwrite(output_path, image)
    print(f"Saved live frame: {output_path}")
    return output_path


def append_inspection_log(row):
    log_path = os.path.join(inspect_images.OUTPUT_DIR, LOG_FILE_NAME)
    file_exists = os.path.exists(log_path)

    with open(log_path, "a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=LOG_FIELDS)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def append_database_log(
    product_name,
    stable_decision,
    prediction,
    confidence,
    image_path="",
):
    return database.insert_inspection_record(
        product_name=product_name,
        result=stable_decision,
        prediction=prediction,
        confidence=confidence,
        image_path=image_path,
    )


def should_auto_save_decision_image(image_path):
    return not image_path


def build_log_row(
    product_name,
    stable_decision,
    frame_decision,
    prediction,
    confidence,
    ok_distance,
    ng_distance,
    ok_count,
    ng_count,
    uncertain_count,
    event,
    image_path="",
):
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "product": product_name,
        "stable_decision": stable_decision,
        "frame_decision": frame_decision,
        "prediction": prediction,
        "confidence_percent": f"{confidence * 100:.1f}",
        "ok_distance": f"{ok_distance:.2f}",
        "ng_distance": f"{ng_distance:.2f}",
        "history_ok": ok_count,
        "history_ng": ng_count,
        "history_uncertain": uncertain_count,
        "event": event,
        "image_path": image_path,
    }


def main():
    args = parse_args()
    product_root = inspect_images.setup_product_paths(args.product)

    print(f"Realtime inspection product: {args.product} ({product_root})")

    roi = inspect_images.load_roi()
    print(f"Using ROI: x={roi[0]}, y={roi[1]}, w={roi[2]}, h={roi[3]}")

    features, labels, _ = inspect_images.build_training_data(roi)
    model = inspect_images.train_simple_classifier(features, labels)

    camera = cv2.VideoCapture(args.camera)

    if not camera.isOpened():
        raise Exception(f"Could not open camera index {args.camera}")

    print("Realtime controls:")
    print("Press 's' to save current annotated frame")
    print("Press 'q' to quit")
    print(f"Inspection log: {os.path.join(inspect_images.OUTPUT_DIR, LOG_FILE_NAME)}")
    print(
        "Database logging: "
        f"{'disabled' if args.disable_db_log else 'enabled'}"
    )
    print(
        f"Smoothing: last {SMOOTHING_WINDOW} frames, "
        f"{STABLE_REQUIRED_COUNT} matching frames required, "
        "uncertain frames ignored when confident frames agree"
    )

    decision_history = []
    last_stable_decision = None

    while True:
        ret, frame = camera.read()

        if not ret:
            print("Failed to capture frame")
            break

        prediction, ok_distance, ng_distance, confidence = inspect_images.predict(
            frame, roi, model
        )
        frame_decision = inspect_images.final_decision(prediction, confidence)

        decision_history.append(frame_decision)
        decision_history = decision_history[-SMOOTHING_WINDOW:]

        stable_decision = get_stable_decision(decision_history)
        color = inspect_images.get_label_color(stable_decision)

        ok_count = decision_history.count("OK")
        ng_count = decision_history.count("NOT OK")
        uncertain_count = decision_history.count(inspect_images.UNCERTAIN_LABEL)

        annotated = frame.copy()
        inspect_images.draw_prediction(annotated, roi, stable_decision, color)
        inspect_images.draw_info_lines(
            annotated,
            [
                f"Product: {args.product}",
                f"Stable decision: {stable_decision}",
                f"Frame decision: {frame_decision}",
                f"Prediction: {prediction}",
                f"Confidence: {confidence * 100:.1f}%",
                f"History: OK={ok_count}, NG={ng_count}, UNC={uncertain_count}",
                f"OK dist: {ok_distance:.2f}",
                f"NG dist: {ng_distance:.2f}",
            ],
            color=color
        )

        if stable_decision != last_stable_decision:
            image_path = ""

            if should_auto_save_decision_image(image_path):
                image_path = save_live_frame(annotated, args.product)

            print(
                f"Stable decision={stable_decision}, "
                f"Frame decision={frame_decision}, "
                f"Prediction={prediction}, "
                f"Confidence={confidence * 100:.1f}%, "
                f"History OK={ok_count}, NG={ng_count}, UNC={uncertain_count}"
            )
            append_inspection_log(
                build_log_row(
                    args.product,
                    stable_decision,
                    frame_decision,
                    prediction,
                    confidence,
                    ok_distance,
                    ng_distance,
                    ok_count,
                    ng_count,
                    uncertain_count,
                    event="decision_change",
                    image_path=image_path,
                )
            )
            if not args.disable_db_log:
                record_id = append_database_log(
                    args.product,
                    stable_decision,
                    prediction,
                    confidence,
                    image_path=image_path,
                )
                print(f"Database inspection record saved: {record_id}")
            last_stable_decision = stable_decision

        cv2.imshow("Realtime Vision Inspection", annotated)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            image_path = save_live_frame(annotated, args.product)
            append_inspection_log(
                build_log_row(
                    args.product,
                    stable_decision,
                    frame_decision,
                    prediction,
                    confidence,
                    ok_distance,
                    ng_distance,
                    ok_count,
                    ng_count,
                    uncertain_count,
                    event="image_saved",
                    image_path=image_path,
                )
            )
            if not args.disable_db_log:
                record_id = append_database_log(
                    args.product,
                    stable_decision,
                    prediction,
                    confidence,
                    image_path=image_path,
                )
                print(f"Database inspection record saved: {record_id}")
        elif key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
