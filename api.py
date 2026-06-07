from pathlib import Path

from flask import (
    abort,
    Flask,
    jsonify,
    redirect,
    render_template_string,
    request,
    send_file,
    url_for,
)
from mysql.connector import Error as MySQLError

from database import (
    fetch_inspection_record,
    fetch_inspection_records,
    fetch_inspection_summary,
    fetch_pending_uncertain_records,
    fetch_product_names,
    update_inspection_review,
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
                        <th>AI Result</th>
                        <th>Final Decision</th>
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
                        <td>{{ record.final_decision or "-" }}</td>
                        <td>{{ record.prediction }}</td>
                        <td>{{ record.reviewed_status or record.status }}</td>
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


REVIEW_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>UNCERTAIN Review</title>
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

        a {
            color: var(--accent);
            text-decoration: none;
            font-weight: 700;
        }

        .subtitle,
        .meta {
            color: var(--muted);
            font-size: 14px;
        }

        form.filters {
            display: grid;
            grid-template-columns: minmax(180px, 1fr) auto;
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

        select,
        textarea,
        input,
        button {
            min-height: 38px;
            border-radius: 6px;
            font: inherit;
        }

        select,
        textarea,
        input {
            width: 100%;
            border: 1px solid var(--border);
            padding: 8px 10px;
            color: var(--text);
            background: #ffffff;
        }

        textarea {
            min-height: 70px;
            resize: vertical;
        }

        button {
            border: 0;
            padding: 8px 14px;
            color: #ffffff;
            font-weight: 700;
            cursor: pointer;
        }

        .apply {
            align-self: end;
            background: var(--accent);
        }

        .ok-button {
            background: var(--ok);
        }

        .ng-button {
            background: var(--ng);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 14px;
        }

        .case {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }

        .case img {
            display: block;
            width: 100%;
            aspect-ratio: 4 / 3;
            object-fit: contain;
            background: #101513;
        }

        .missing-image {
            display: grid;
            place-items: center;
            width: 100%;
            aspect-ratio: 4 / 3;
            background: #edf3f0;
            color: var(--muted);
            font-weight: 700;
        }

        .case-body {
            padding: 14px;
        }

        .case h2 {
            margin: 0 0 8px;
            font-size: 18px;
        }

        .details {
            display: grid;
            gap: 6px;
            margin: 10px 0 14px;
            color: var(--muted);
            font-size: 14px;
        }

        .actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }

        .review-fields {
            display: grid;
            gap: 8px;
            margin-bottom: 10px;
        }

        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 999px;
            background: var(--unc);
            color: #ffffff;
            font-size: 12px;
            font-weight: 700;
        }

        .empty {
            padding: 18px;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--muted);
        }

        @media (max-width: 620px) {
            main {
                width: min(100% - 20px, 1180px);
                margin: 18px auto;
            }

            header,
            form.filters {
                display: block;
            }

            .apply {
                width: 100%;
                margin-top: 10px;
            }
        }
    </style>
</head>
<body>
    <main>
        <header>
            <div>
                <h1>UNCERTAIN Case Review</h1>
                <div class="subtitle">Pending cases: {{ records|length }}</div>
            </div>
            <a href="/dashboard">Dashboard</a>
        </header>

        <form class="filters" method="get" action="/review">
            <label>
                Product
                <select name="product">
                    <option value="">All Products</option>
                    {% for product in product_names %}
                    <option value="{{ product }}" {% if product == product_name %}selected{% endif %}>{{ product }}</option>
                    {% endfor %}
                </select>
            </label>
            <button class="apply" type="submit">Apply Filter</button>
        </form>

        {% if records %}
        <div class="grid">
            {% for record in records %}
            <article class="case">
                {% if record.image_path %}
                <img src="{{ url_for('review_image', record_id=record.id) }}" alt="Inspection record {{ record.id }}">
                {% else %}
                <div class="missing-image">No image saved</div>
                {% endif %}
                <div class="case-body">
                    <h2>Record #{{ record.id }}</h2>
                    <span class="badge">{{ record.result }}</span>
                    <div class="details">
                        <div>Product: {{ record.product_name }}</div>
                        <div>Original AI decision: {{ record.result }}</div>
                        <div>Prediction: {{ record.prediction }}</div>
                        <div>Confidence: {{ "%.2f"|format(record.confidence or 0) }}%</div>
                        <div>Inspected: {{ record.inspected_at }}</div>
                    </div>
                    <form method="post" action="{{ url_for('review_record', record_id=record.id) }}">
                        {% if product_name %}
                        <input type="hidden" name="product" value="{{ product_name }}">
                        {% endif %}
                        <div class="review-fields">
                            <label>
                                Reviewed By
                                <input name="reviewed_by" placeholder="operator or reviewer name">
                            </label>
                            <label>
                                Review Notes
                                <textarea name="review_notes" placeholder="optional notes"></textarea>
                            </label>
                        </div>
                        <div class="actions">
                            <button class="ok-button" type="submit" name="final_decision" value="OK">Mark OK</button>
                            <button class="ng-button" type="submit" name="final_decision" value="NOT OK">Mark NOT OK</button>
                        </div>
                    </form>
                </div>
            </article>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty">No pending UNCERTAIN records found.</div>
        {% endif %}
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


def safe_workspace_path(path_value):
    if not path_value:
        return None

    path = Path(path_value)
    if not path.is_absolute():
        path = Path.cwd() / path

    resolved_path = path.resolve()
    workspace_path = Path.cwd().resolve()

    try:
        resolved_path.relative_to(workspace_path)
    except ValueError:
        return None

    return resolved_path


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


@app.get("/review")
def review_cases():
    product_name = product_query_value()
    product_names = fetch_product_names()
    records = fetch_pending_uncertain_records(
        limit=100,
        product_name=product_name,
    )

    return render_template_string(
        REVIEW_TEMPLATE,
        records=records,
        product_names=product_names,
        product_name=product_name,
    )


@app.get("/review/<int:record_id>/image")
def review_image(record_id):
    record = fetch_inspection_record(record_id)
    if not record:
        abort(404)

    image_path = safe_workspace_path(record.get("image_path"))
    if not image_path or not image_path.exists():
        abort(404)

    return send_file(image_path)


@app.post("/review/<int:record_id>")
def review_record(record_id):
    final_decision = request.form.get("final_decision", "")
    was_updated = update_inspection_review(
        record_id,
        final_decision,
        reviewed_by=request.form.get("reviewed_by"),
        review_notes=request.form.get("review_notes"),
    )
    if not was_updated:
        abort(404)

    product_name = request.form.get("product")
    if product_name:
        return redirect(url_for("review_cases", product=product_name))

    return redirect(url_for("review_cases"))


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
