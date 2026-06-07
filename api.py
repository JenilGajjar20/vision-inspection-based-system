from flask import Flask, jsonify, render_template_string, request
from mysql.connector import Error as MySQLError

from database import (
    fetch_inspection_records,
    fetch_inspection_summary,
    fetch_product_names,
)


app = Flask(__name__)


DASHBOARD_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>QMS Inspection Dashboard</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f4f7f6;
            --panel: #ffffff;
            --text: #16201d;
            --muted: #60706a;
            --border: #dbe5e1;
            --ok: #0f8f5f;
            --ng: #c73838;
            --unc: #a66a00;
            --accent: #2d6cdf;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            background: var(--bg);
            color: var(--text);
            font-family: Arial, Helvetica, sans-serif;
        }

        main {
            width: min(1180px, calc(100% - 32px));
            margin: 28px auto;
        }

        header {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 20px;
        }

        h1 {
            margin: 0 0 6px;
            font-size: 30px;
            line-height: 1.15;
        }

        .subtitle {
            color: var(--muted);
            font-size: 14px;
        }

        form {
            display: grid;
            grid-template-columns: repeat(6, minmax(120px, 1fr));
            gap: 10px;
            padding: 14px;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 18px;
        }

        label {
            display: grid;
            gap: 6px;
            color: var(--muted);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }

        input,
        select {
            width: 100%;
            min-height: 38px;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 8px 10px;
            color: var(--text);
            font: inherit;
        }

        button {
            align-self: end;
            min-height: 38px;
            border: 0;
            border-radius: 6px;
            background: var(--accent);
            color: #ffffff;
            font-weight: 700;
            cursor: pointer;
        }

        .metrics {
            display: grid;
            grid-template-columns: repeat(6, minmax(130px, 1fr));
            gap: 12px;
            margin-bottom: 18px;
        }

        .metric {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
        }

        .metric span {
            display: block;
            color: var(--muted);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }

        .metric strong {
            display: block;
            margin-top: 10px;
            font-size: 28px;
        }

        .ok strong {
            color: var(--ok);
        }

        .ng strong {
            color: var(--ng);
        }

        .unc strong {
            color: var(--unc);
        }

        section {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }

        h2 {
            margin: 0;
            padding: 16px;
            font-size: 18px;
            border-bottom: 1px solid var(--border);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        th,
        td {
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            text-align: left;
            vertical-align: top;
        }

        th {
            color: var(--muted);
            font-size: 12px;
            text-transform: uppercase;
        }

        tr:last-child td {
            border-bottom: 0;
        }

        .badge {
            display: inline-block;
            min-width: 76px;
            padding: 4px 8px;
            border-radius: 999px;
            color: #ffffff;
            font-size: 12px;
            font-weight: 700;
            text-align: center;
        }

        .badge-ok {
            background: var(--ok);
        }

        .badge-ng {
            background: var(--ng);
        }

        .badge-unc {
            background: var(--unc);
        }

        .empty {
            padding: 18px;
            color: var(--muted);
        }

        @media (max-width: 920px) {
            header {
                display: block;
            }

            form,
            .metrics {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            table {
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }
        }

        @media (max-width: 560px) {
            main {
                width: min(100% - 20px, 1180px);
                margin: 18px auto;
            }

            form,
            .metrics {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <main>
        <header>
            <div>
                <h1>QMS Inspection Dashboard</h1>
                <div class="subtitle">
                    {% if product_name %}
                    Product: {{ product_name }}
                    {% else %}
                    All products
                    {% endif %}
                </div>
            </div>
            <div class="subtitle">Recent limit: {{ recent_limit }}</div>
        </header>

        <form method="get" action="/dashboard">
            <label>
                Product
                <select name="product">
                    <option value="">All Products</option>
                    {% for product in product_names %}
                    <option value="{{ product }}" {% if product == product_name %}selected{% endif %}>{{ product }}</option>
                    {% endfor %}
                </select>
            </label>
            <label>
                Start Date
                <input type="date" name="start_date" value="{{ start_date or '' }}">
            </label>
            <label>
                End Date
                <input type="date" name="end_date" value="{{ end_date or '' }}">
            </label>
            <label>
                Result
                <select name="result">
                    <option value="">All Results</option>
                    {% for option in ["OK", "NOT OK", "UNCERTAIN"] %}
                    <option value="{{ option }}" {% if option == result %}selected{% endif %}>{{ option }}</option>
                    {% endfor %}
                </select>
            </label>
            <label>
                Status
                <select name="status">
                    <option value="">All Statuses</option>
                    {% for option in ["PASS", "FAIL", "REVIEW"] %}
                    <option value="{{ option }}" {% if option == status %}selected{% endif %}>{{ option }}</option>
                    {% endfor %}
                </select>
            </label>
            <button type="submit">Apply Filters</button>
        </form>

        <div class="metrics">
            <div class="metric">
                <span>Total</span>
                <strong>{{ summary.total }}</strong>
            </div>
            <div class="metric ok">
                <span>OK</span>
                <strong>{{ summary.by_result["OK"] }}</strong>
            </div>
            <div class="metric ng">
                <span>NOT OK</span>
                <strong>{{ summary.by_result["NOT OK"] }}</strong>
            </div>
            <div class="metric unc">
                <span>UNCERTAIN</span>
                <strong>{{ summary.by_result["UNCERTAIN"] }}</strong>
            </div>
            <div class="metric ng">
                <span>Reject %</span>
                <strong>{{ "%.2f"|format(summary.reject_percentage) }}%</strong>
            </div>
            <div class="metric unc">
                <span>Uncertain %</span>
                <strong>{{ "%.2f"|format(summary.uncertain_percentage) }}%</strong>
            </div>
        </div>

        <section>
            <h2>Recent Inspection Records</h2>
            {% if recent_records %}
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Product</th>
                        <th>Result</th>
                        <th>Prediction</th>
                        <th>Status</th>
                        <th>Confidence</th>
                        <th>Image</th>
                    </tr>
                </thead>
                <tbody>
                    {% for record in recent_records %}
                    <tr>
                        <td>{{ record.inspected_at }}</td>
                        <td>{{ record.product_name }}</td>
                        <td>
                            <span class="badge {% if record.result == 'OK' %}badge-ok{% elif record.result == 'NOT OK' %}badge-ng{% else %}badge-unc{% endif %}">
                                {{ record.result }}
                            </span>
                        </td>
                        <td>{{ record.prediction }}</td>
                        <td>{{ record.status }}</td>
                        <td>{{ "%.2f"|format(record.confidence or 0) }}%</td>
                        <td>{{ record.image_path or "-" }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty">No inspection records found for the selected filters.</div>
            {% endif %}
        </section>
    </main>
</body>
</html>
"""


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


def empty_query_value(name):
    return request.args.get(name) or None


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


@app.get("/")
def dashboard_home():
    return dashboard()


@app.get("/dashboard")
def dashboard():
    recent_limit = parse_int_query("limit", default=10, minimum=1, maximum=100)
    product_name = product_query_value()
    start_date = empty_query_value("start_date")
    end_date = empty_query_value("end_date")
    result = empty_query_value("result")
    status = empty_query_value("status")

    summary = fetch_inspection_summary(
        product_name=product_name,
        result=result,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )
    recent_records = fetch_inspection_records(
        limit=recent_limit,
        product_name=product_name,
        result=result,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )
    product_names = fetch_product_names()

    return render_template_string(
        DASHBOARD_TEMPLATE,
        summary=summary,
        recent_records=recent_records,
        product_names=product_names,
        product_name=product_name,
        start_date=start_date,
        end_date=end_date,
        result=result,
        status=status,
        recent_limit=recent_limit,
    )


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

    records = fetch_inspection_records(
        limit=limit,
        product_name=product_query_value(),
        result=request.args.get("result"),
        status=request.args.get("status"),
        start_date=request.args.get("start_date"),
        end_date=request.args.get("end_date"),
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
        result=request.args.get("result"),
        status=request.args.get("status"),
        start_date=request.args.get("start_date"),
        end_date=request.args.get("end_date"),
    )

    return jsonify(summary)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
