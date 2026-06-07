from flask import Flask, jsonify, request
from mysql.connector import Error as MySQLError

from database import (
    fetch_inspection_records,
    fetch_inspection_summary,
    fetch_recent_inspections,
)


app = Flask(__name__)


def parse_int_query(name, default, minimum=0, maximum=None):
    raw_value = request.args.get(name)
    if raw_value is None or raw_value == "":
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number.") from exc

    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")

    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}.")

    return value


def product_query_value():
    return request.args.get("product") or request.args.get("product_name")


def error_response(message, status_code):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


@app.errorhandler(ValueError)
def handle_value_error(error):
    return error_response(str(error), 400)


@app.errorhandler(MySQLError)
def handle_mysql_error(error):
    return error_response(f"Database error: {error}", 500)


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/inspection-records")
def inspection_records():
    limit = parse_int_query("limit", default=100, minimum=1, maximum=500)
    offset = parse_int_query("offset", default=0, minimum=0)

    records = fetch_inspection_records(
        product_name=product_query_value(),
        result=request.args.get("result"),
        status=request.args.get("status"),
        start_date=request.args.get("start_date"),
        end_date=request.args.get("end_date"),
        limit=limit,
        offset=offset,
    )

    return jsonify(
        {
            "count": len(records),
            "limit": limit,
            "offset": offset,
            "records": records,
        }
    )


@app.get("/api/inspection-records/recent")
def recent_inspections():
    limit = parse_int_query("limit", default=10, minimum=1, maximum=100)

    records = fetch_recent_inspections(
        limit=limit,
        product_name=product_query_value(),
    )

    return jsonify(
        {
            "count": len(records),
            "limit": limit,
            "records": records,
        }
    )


@app.get("/api/inspection-records/summary")
def inspection_summary():
    summary = fetch_inspection_summary(
        product_name=product_query_value(),
        start_date=request.args.get("start_date"),
        end_date=request.args.get("end_date"),
    )

    return jsonify(summary)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
