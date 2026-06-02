import argparse
import csv
import html
import json
import os
import re
from collections import Counter
from datetime import datetime


PRODUCTS_DIR = "products"
DEFAULT_PRODUCT = "product_1"
LOG_FILE_NAME = "inspection_log.csv"
REPORT_FILE_NAME = "inspection_report.txt"
HTML_REPORT_FILE_NAME = "inspection_report.html"
PRODUCT_NAME_PATTERN = r"^[a-zA-Z0-9_]+$"
VALID_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"]


def validate_product_name(product_name):
    if re.match(PRODUCT_NAME_PATTERN, product_name):
        return product_name

    raise argparse.ArgumentTypeError(
        "Invalid product name. Use only letters, numbers, and underscores. "
        "Examples: product_4, paper_clip, metal_bracket"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a simple inspection summary report from CSV logs."
    )
    parser.add_argument(
        "--product",
        type=validate_product_name,
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


def read_roi(roi_path):
    if not os.path.exists(roi_path):
        return None

    with open(roi_path) as file:
        return json.load(file)


def format_roi(roi):
    if not roi:
        return "Not available"

    return (
        f"x={roi['x']}, y={roi['y']}, "
        f"w={roi['w']}, h={roi['h']}"
    )


def count_images(folder):
    if not os.path.exists(folder):
        return 0

    return sum(
        1
        for file_name in os.listdir(folder)
        if os.path.splitext(file_name.lower())[1] in VALID_IMAGE_EXTENSIONS
    )


def get_product_summary(product_root):
    return {
        "ok_training_images": count_images(
            os.path.join(product_root, "dataset", "ok")
        ),
        "ng_training_images": count_images(
            os.path.join(product_root, "dataset", "ng")
        ),
        "test_images": count_images(
            os.path.join(product_root, "test")
        ),
        "rejected_ok_images": count_images(
            os.path.join(product_root, "dataset", "rejected", "ok")
        ),
        "rejected_ng_images": count_images(
            os.path.join(product_root, "dataset", "rejected", "ng")
        ),
        "rejected_test_images": count_images(
            os.path.join(product_root, "dataset", "rejected", "test")
        ),
    }


def total_rejected(product_summary):
    return (
        product_summary["rejected_ok_images"] +
        product_summary["rejected_ng_images"] +
        product_summary["rejected_test_images"]
    )


def percent(part, total):
    if total == 0:
        return 0.0

    return (part / total) * 100


def build_report_lines(
    product_name,
    rows,
    recent_count,
    generated_at,
    roi,
    product_summary,
    log_path,
    report_path,
    html_report_path,
):
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
    lines.append(f"Generated at: {generated_at}")
    lines.append(f"Product: {product_name}")
    lines.append(f"ROI: {format_roi(roi)}")
    lines.append(f"Log file: {log_path}")
    lines.append(f"Text report: {report_path}")
    lines.append(f"HTML report: {html_report_path}")
    lines.append(f"Total log rows: {total_rows}")
    lines.append(f"Decision changes: {len(decision_change_rows)}")
    lines.append(f"Saved images: {len(saved_image_rows)}")
    lines.append("")
    lines.append("Product Folder Summary:")
    lines.append(f"OK training images: {product_summary['ok_training_images']}")
    lines.append(f"NOT OK training images: {product_summary['ng_training_images']}")
    lines.append(f"Test images: {product_summary['test_images']}")
    lines.append(f"Rejected images: {total_rejected(product_summary)}")
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


def summarize_rows(rows):
    decision_counts = Counter(row["stable_decision"] for row in rows)
    event_counts = Counter(row["event"] for row in rows)
    decision_change_rows = [
        row for row in rows if row["event"] == "decision_change"
    ]
    saved_image_rows = [
        row for row in rows if row["event"] == "image_saved"
    ]
    total_rows = len(rows)

    return {
        "total_rows": total_rows,
        "decision_changes": len(decision_change_rows),
        "saved_images": len(saved_image_rows),
        "ok_count": decision_counts["OK"],
        "ng_count": decision_counts["NOT OK"],
        "uncertain_count": decision_counts["UNCERTAIN"],
        "reject_percent": percent(decision_counts["NOT OK"], total_rows),
        "uncertain_percent": percent(decision_counts["UNCERTAIN"], total_rows),
        "event_counts": event_counts,
    }


def badge_class(decision):
    if decision == "OK":
        return "ok"

    if decision == "NOT OK":
        return "ng"

    return "uncertain"


def build_html_report(
    product_name,
    rows,
    recent_count,
    generated_at,
    roi,
    product_summary,
    log_path,
    report_path,
    html_report_path,
):
    summary = summarize_rows(rows)
    recent_rows = rows[-recent_count:] if rows else []
    event_items = "\n".join(
        f"<li><strong>{html.escape(event)}:</strong> {count}</li>"
        for event, count in summary["event_counts"].items()
    )
    recent_table_rows = []

    for row in recent_rows:
        decision = row["stable_decision"]
        image_path = row["image_path"] if row["image_path"] else "-"
        recent_table_rows.append(
            "<tr>"
            f"<td>{html.escape(row['timestamp'])}</td>"
            f"<td><span class=\"badge {badge_class(decision)}\">{html.escape(decision)}</span></td>"
            f"<td>{html.escape(row['frame_decision'])}</td>"
            f"<td>{html.escape(row['confidence_percent'])}%</td>"
            f"<td>{html.escape(row['event'])}</td>"
            f"<td>{html.escape(image_path)}</td>"
            "</tr>"
        )

    recent_rows_html = "\n".join(recent_table_rows)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Inspection Report - {html.escape(product_name)}</title>
  <style>
    body {{
      margin: 32px;
      color: #1f2933;
      font-family: Arial, sans-serif;
      background: #f5f7fa;
    }}
    h1, h2 {{
      color: #102a43;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin: 20px 0;
    }}
    .card {{
      background: #ffffff;
      border: 1px solid #d9e2ec;
      border-radius: 6px;
      padding: 14px;
    }}
    .label {{
      color: #52606d;
      font-size: 12px;
      text-transform: uppercase;
    }}
    .value {{
      font-size: 24px;
      font-weight: 700;
      margin-top: 6px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #ffffff;
      border: 1px solid #d9e2ec;
    }}
    th, td {{
      border-bottom: 1px solid #d9e2ec;
      padding: 10px;
      text-align: left;
      font-size: 14px;
      vertical-align: top;
    }}
    th {{
      background: #e4e7eb;
    }}
    .badge {{
      border-radius: 999px;
      display: inline-block;
      font-weight: 700;
      padding: 4px 10px;
    }}
    .ok {{
      background: #d9f9e6;
      color: #0b6b35;
    }}
    .ng {{
      background: #ffe3e3;
      color: #b42318;
    }}
    .uncertain {{
      background: #fff3c4;
      color: #7c5e10;
    }}
    .note {{
      color: #52606d;
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <h1>Inspection Report</h1>
  <p><strong>Generated at:</strong> {html.escape(generated_at)}</p>
  <p><strong>Product:</strong> {html.escape(product_name)}</p>
  <p><strong>ROI:</strong> {html.escape(format_roi(roi))}</p>
  <p><strong>Log file:</strong> {html.escape(log_path)}</p>
  <p><strong>Text report:</strong> {html.escape(report_path)}</p>
  <p><strong>HTML report:</strong> {html.escape(html_report_path)}</p>
  <p class="note">Generated from realtime inspection log data.</p>

  <div class="cards">
    <div class="card"><div class="label">Total rows</div><div class="value">{summary['total_rows']}</div></div>
    <div class="card"><div class="label">Decision changes</div><div class="value">{summary['decision_changes']}</div></div>
    <div class="card"><div class="label">Saved images</div><div class="value">{summary['saved_images']}</div></div>
    <div class="card"><div class="label">OK</div><div class="value">{summary['ok_count']}</div></div>
    <div class="card"><div class="label">NOT OK</div><div class="value">{summary['ng_count']}</div></div>
    <div class="card"><div class="label">UNCERTAIN</div><div class="value">{summary['uncertain_count']}</div></div>
    <div class="card"><div class="label">Reject %</div><div class="value">{summary['reject_percent']:.1f}%</div></div>
    <div class="card"><div class="label">Uncertain %</div><div class="value">{summary['uncertain_percent']:.1f}%</div></div>
    <div class="card"><div class="label">OK training images</div><div class="value">{product_summary['ok_training_images']}</div></div>
    <div class="card"><div class="label">NOT OK training images</div><div class="value">{product_summary['ng_training_images']}</div></div>
    <div class="card"><div class="label">Test images</div><div class="value">{product_summary['test_images']}</div></div>
    <div class="card"><div class="label">Rejected images</div><div class="value">{total_rejected(product_summary)}</div></div>
  </div>

  <h2>Event Summary</h2>
  <ul>
    {event_items}
  </ul>

  <h2>Recent {min(recent_count, len(rows))} Log Rows</h2>
  <table>
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>Stable Decision</th>
        <th>Frame Decision</th>
        <th>Confidence</th>
        <th>Event</th>
        <th>Image</th>
      </tr>
    </thead>
    <tbody>
      {recent_rows_html}
    </tbody>
  </table>
</body>
</html>
"""


def save_report(report_path, lines):
    with open(report_path, "w") as file:
        file.write("\n".join(lines))
        file.write("\n")


def save_html_report(report_path, html_report):
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(html_report)


def main():
    args = parse_args()
    product_root = os.path.join(PRODUCTS_DIR, args.product)
    output_dir = os.path.join(product_root, "outputs")
    roi_path = os.path.join(product_root, "roi.json")
    log_path = os.path.join(
        output_dir,
        LOG_FILE_NAME
    )
    report_path = os.path.join(output_dir, REPORT_FILE_NAME)
    html_report_path = os.path.join(output_dir, HTML_REPORT_FILE_NAME)
    generated_at = datetime.now().isoformat(timespec="seconds")

    rows = read_log_rows(log_path)
    roi = read_roi(roi_path)
    product_summary = get_product_summary(product_root)
    report_lines = build_report_lines(
        args.product,
        rows,
        args.recent,
        generated_at,
        roi,
        product_summary,
        log_path,
        report_path,
        html_report_path,
    )
    html_report = build_html_report(
        args.product,
        rows,
        args.recent,
        generated_at,
        roi,
        product_summary,
        log_path,
        report_path,
        html_report_path,
    )
    print("\n".join(report_lines))
    save_report(report_path, report_lines)
    save_html_report(html_report_path, html_report)
    print()
    print(f"Report saved: {report_path}")
    print(f"HTML report saved: {html_report_path}")


if __name__ == "__main__":
    main()
