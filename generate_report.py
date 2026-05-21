import argparse
import csv
import os
from collections import Counter


PRODUCTS_DIR = "products"
DEFAULT_PRODUCT = "product_1"
LOG_FILE_NAME = "inspection_log.csv"
REPORT_FILE_NAME = "inspection_report.txt"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a simple inspection summary report from CSV logs."
    )
    parser.add_argument(
        "--product",
        default=DEFAULT_PRODUCT,
        help=f"Product recipe folder under {PRODUCTS_DIR}. Default: {DEFAULT_PRODUCT}."
    )
    parser.add_argument(
        "--recent",
        type=int,
        default=10,
        help="Number of recent log rows to display. Default: 10."
    )
    return parser.parse_args()


def read_log_rows(log_path):
    if not os.path.exists(log_path):
        raise Exception(f"Inspection log not found: {log_path}")

    with open(log_path, newline="") as file:
        return list(csv.DictReader(file))


def percent(part, total):
    if total == 0:
        return 0.0

    return (part / total) * 100


def build_report_lines(product_name, rows, recent_count):
    decision_counts = Counter(row["stable_decision"] for row in rows)
    event_counts = Counter(row["event"] for row in rows)
    decision_change_rows = [
        row for row in rows if row["event"] == "decision_change"
    ]
    saved_image_rows = [
        row for row in rows if row["event"] == "image_saved"
    ]

    ok_count = decision_counts["OK"]
    ng_count = decision_counts["NOT OK"]
    uncertain_count = decision_counts["UNCERTAIN"]
    total_rows = len(rows)
    lines = []

    lines.append("")
    lines.append("Inspection Report")
    lines.append("-----------------")
    lines.append(f"Product: {product_name}")
    lines.append(f"Total log rows: {total_rows}")
    lines.append(f"Decision changes: {len(decision_change_rows)}")
    lines.append(f"Saved images: {len(saved_image_rows)}")
    lines.append("")
    lines.append("Decision Summary:")
    lines.append(f"OK: {ok_count}")
    lines.append(f"NOT OK: {ng_count}")
    lines.append(f"UNCERTAIN: {uncertain_count}")
    lines.append(f"Reject percentage: {percent(ng_count, total_rows):.1f}%")
    lines.append(f"Uncertain percentage: {percent(uncertain_count, total_rows):.1f}%")
    lines.append("")
    lines.append("Event Summary:")
    for event, count in event_counts.items():
        lines.append(f"{event}: {count}")

    if not rows:
        return lines

    lines.append("")
    lines.append(f"Recent {min(recent_count, total_rows)} Log Rows:")
    for row in rows[-recent_count:]:
        image_text = row["image_path"] if row["image_path"] else "-"
        lines.append(
            f"{row['timestamp']} | "
            f"Decision={row['stable_decision']} | "
            f"Confidence={row['confidence_percent']}% | "
            f"Event={row['event']} | "
            f"Image={image_text}"
        )

    return lines


def save_report(report_path, lines):
    with open(report_path, "w") as file:
        file.write("\n".join(lines))
        file.write("\n")


def main():
    args = parse_args()
    output_dir = os.path.join(PRODUCTS_DIR, args.product, "outputs")
    log_path = os.path.join(
        output_dir,
        LOG_FILE_NAME
    )
    report_path = os.path.join(output_dir, REPORT_FILE_NAME)

    rows = read_log_rows(log_path)
    report_lines = build_report_lines(args.product, rows, args.recent)
    print("\n".join(report_lines))
    save_report(report_path, report_lines)
    print()
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    main()
