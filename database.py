import mysql.connector
from datetime import date, datetime
from decimal import Decimal

from db_config import get_database_config


VALID_RESULTS = {"OK", "NOT OK", "UNCERTAIN"}
VALID_STATUSES = {"PASS", "FAIL", "REVIEW"}
VALID_REVIEW_RESULTS = {"OK", "NOT OK"}


def get_connection():
    return mysql.connector.connect(**get_database_config())


def ensure_product(cursor, product_name):
    cursor.execute(
        """
        INSERT INTO products (product_name)
        VALUES (%s)
        ON DUPLICATE KEY UPDATE product_name = VALUES(product_name)
        """,
        (product_name,)
    )
    cursor.execute(
        "SELECT id FROM products WHERE product_name = %s",
        (product_name,)
    )
    row = cursor.fetchone()

    if row is None:
        raise Exception(f"Could not find or create product: {product_name}")

    return row[0]


def decision_to_status(decision):
    if decision == "OK":
        return "PASS"

    if decision == "NOT OK":
        return "FAIL"

    return "REVIEW"


def decision_to_defect(decision):
    if decision == "NOT OK":
        return "visual_defect"

    if decision == "UNCERTAIN":
        return "low_confidence"

    return None


def insert_inspection_record(
    product_name,
    result,
    prediction,
    confidence,
    image_path="",
):
    connection = get_connection()
    cursor = connection.cursor()

    product_id = ensure_product(cursor, product_name)
    status = decision_to_status(result)
    defect = decision_to_defect(result)

    cursor.execute(
        """
        INSERT INTO inspection_records (
            product_id,
            product_name,
            result,
            prediction,
            status,
            defect,
            confidence,
            image_path
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            product_id,
            product_name,
            result,
            prediction,
            status,
            defect,
            round(confidence * 100, 2),
            image_path or None,
        )
    )

    connection.commit()
    record_id = cursor.lastrowid
    cursor.close()
    connection.close()

    return record_id


def serialize_database_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ")

    if isinstance(value, Decimal):
        return float(value)

    return value


def serialize_row(row):
    return {
        key: serialize_database_value(value)
        for key, value in row.items()
    }


def fetch_product_names():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT product_name
        FROM products
        ORDER BY product_name ASC
        """
    )
    product_names = [row[0] for row in cursor.fetchall()]

    cursor.close()
    connection.close()

    return product_names


def normalize_end_date(value):
    if value and len(value) == 10:
        return f"{value} 23:59:59"

    return value


def build_inspection_filters(
    product_name=None,
    result=None,
    status=None,
    start_date=None,
    end_date=None,
):
    filters = []
    params = []

    if product_name:
        filters.append("product_name = %s")
        params.append(product_name)

    if result:
        result = result.upper()
        if result not in VALID_RESULTS:
            raise ValueError(
                "Invalid result. Use one of: OK, NOT OK, UNCERTAIN."
            )
        filters.append("result = %s")
        params.append(result)

    if status:
        status = status.upper()
        if status not in VALID_STATUSES:
            raise ValueError(
                "Invalid status. Use one of: PASS, FAIL, REVIEW."
            )
        filters.append("status = %s")
        params.append(status)

    if start_date:
        filters.append("inspected_at >= %s")
        params.append(start_date)

    if end_date:
        filters.append("inspected_at <= %s")
        params.append(normalize_end_date(end_date))

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    return where_clause, params


def fetch_inspection_records(
    product_name=None,
    result=None,
    status=None,
    start_date=None,
    end_date=None,
    limit=100,
    offset=0,
):
    where_clause, params = build_inspection_filters(
        product_name=product_name,
        result=result,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        f"""
        SELECT
            id,
            product_id,
            product_name,
            result,
            prediction,
            status,
            defect,
            confidence,
            image_path,
            final_decision,
            reviewed_status,
            reviewed_by,
            review_notes,
            reviewed_result,
            reviewed_at,
            inspected_at,
            created_at
        FROM inspection_records
        {where_clause}
        ORDER BY inspected_at DESC, id DESC
        LIMIT %s OFFSET %s
        """,
        (*params, limit, offset),
    )
    rows = [serialize_row(row) for row in cursor.fetchall()]

    cursor.close()
    connection.close()

    return rows


def fetch_recent_inspections(limit=10, product_name=None):
    return fetch_inspection_records(
        product_name=product_name,
        limit=limit,
        offset=0,
    )


def fetch_pending_uncertain_records(limit=100, product_name=None):
    filters = ["result = 'UNCERTAIN'", "final_decision IS NULL"]
    params = []

    if product_name:
        filters.append("product_name = %s")
        params.append(product_name)

    where_clause = "WHERE " + " AND ".join(filters)

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        f"""
        SELECT
            id,
            product_id,
            product_name,
            result,
            prediction,
            status,
            defect,
            confidence,
            image_path,
            final_decision,
            reviewed_status,
            reviewed_by,
            review_notes,
            reviewed_result,
            reviewed_at,
            inspected_at,
            created_at
        FROM inspection_records
        {where_clause}
        ORDER BY inspected_at DESC, id DESC
        LIMIT %s
        """,
        (*params, limit),
    )
    rows = [serialize_row(row) for row in cursor.fetchall()]

    cursor.close()
    connection.close()

    return rows


def fetch_inspection_record(record_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            id,
            product_id,
            product_name,
            result,
            prediction,
            status,
            defect,
            confidence,
            image_path,
            final_decision,
            reviewed_status,
            reviewed_by,
            review_notes,
            reviewed_result,
            reviewed_at,
            inspected_at,
            created_at
        FROM inspection_records
        WHERE id = %s
        """,
        (record_id,),
    )
    row = cursor.fetchone()

    cursor.close()
    connection.close()

    return serialize_row(row) if row else None


def update_inspection_review(
    record_id,
    final_decision,
    reviewed_by=None,
    review_notes=None,
):
    final_decision = final_decision.upper()
    if final_decision not in VALID_REVIEW_RESULTS:
        raise ValueError("Invalid review result. Use OK or NOT OK.")

    reviewed_status = decision_to_status(final_decision)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE inspection_records
        SET
            final_decision = %s,
            reviewed_status = %s,
            reviewed_by = %s,
            review_notes = %s,
            reviewed_result = %s,
            reviewed_at = CURRENT_TIMESTAMP
        WHERE id = %s
            AND result = 'UNCERTAIN'
            AND final_decision IS NULL
        """,
        (
            final_decision,
            reviewed_status,
            reviewed_by or None,
            review_notes or None,
            final_decision,
            record_id,
        ),
    )
    updated_count = cursor.rowcount

    connection.commit()
    cursor.close()
    connection.close()

    return updated_count > 0


def fetch_inspection_summary(
    product_name=None,
    result=None,
    status=None,
    start_date=None,
    end_date=None,
):
    where_clause, params = build_inspection_filters(
        product_name=product_name,
        result=result,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        f"""
        SELECT
            COUNT(*) AS total,
            SUM(COALESCE(final_decision, result) = 'OK') AS ok_count,
            SUM(COALESCE(final_decision, result) = 'NOT OK') AS not_ok_count,
            SUM(COALESCE(final_decision, result) = 'UNCERTAIN') AS uncertain_count,
            SUM(COALESCE(reviewed_status, status) = 'PASS') AS pass_count,
            SUM(COALESCE(reviewed_status, status) = 'FAIL') AS fail_count,
            SUM(COALESCE(reviewed_status, status) = 'REVIEW') AS review_count
        FROM inspection_records
        {where_clause}
        """,
        tuple(params),
    )
    totals = serialize_row(cursor.fetchone())

    cursor.execute(
        f"""
        SELECT product_name, COUNT(*) AS total
        FROM inspection_records
        {where_clause}
        GROUP BY product_name
        ORDER BY total DESC, product_name ASC
        """,
        tuple(params),
    )
    by_product = [serialize_row(row) for row in cursor.fetchall()]

    cursor.close()
    connection.close()

    total = int(totals.get("total") or 0)
    not_ok_count = int(totals.get("not_ok_count") or 0)
    uncertain_count = int(totals.get("uncertain_count") or 0)
    reject_percentage = round((not_ok_count / total) * 100, 2) if total else 0.0
    uncertain_percentage = (
        round((uncertain_count / total) * 100, 2) if total else 0.0
    )

    return {
        "total": total,
        "by_result": {
            "OK": int(totals.get("ok_count") or 0),
            "NOT OK": not_ok_count,
            "UNCERTAIN": uncertain_count,
        },
        "by_status": {
            "PASS": int(totals.get("pass_count") or 0),
            "FAIL": int(totals.get("fail_count") or 0),
            "REVIEW": int(totals.get("review_count") or 0),
        },
        "reject_percentage": reject_percentage,
        "uncertain_percentage": uncertain_percentage,
        "by_product": by_product,
    }
