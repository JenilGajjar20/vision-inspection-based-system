import argparse
import os
from datetime import datetime

import cv2

import inspect_images


SMOOTHING_WINDOW = 10
STABLE_REQUIRED_COUNT = 7


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run realtime product inspection from a camera."
    )
    parser.add_argument(
        "--product",
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
    return parser.parse_args()


def get_stable_decision(decision_history):
    ok_count = decision_history.count("OK")
    ng_count = decision_history.count("NOT OK")

    if ok_count >= STABLE_REQUIRED_COUNT:
        return "OK"

    if ng_count >= STABLE_REQUIRED_COUNT:
        return "NOT OK"

    return inspect_images.UNCERTAIN_LABEL


def save_live_frame(image, product_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"live_{product_name}_{timestamp}.jpg"
    output_path = os.path.join(inspect_images.OUTPUT_DIR, filename)
    cv2.imwrite(output_path, image)
    print(f"Saved live frame: {output_path}")


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
    print(
        f"Smoothing: last {SMOOTHING_WINDOW} frames, "
        f"{STABLE_REQUIRED_COUNT} matching frames required"
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
            print(
                f"Stable decision={stable_decision}, "
                f"Frame decision={frame_decision}, "
                f"Prediction={prediction}, "
                f"Confidence={confidence * 100:.1f}%, "
                f"History OK={ok_count}, NG={ng_count}, UNC={uncertain_count}"
            )
            last_stable_decision = stable_decision

        cv2.imshow("Realtime Vision Inspection", annotated)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            save_live_frame(annotated, args.product)
        elif key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
