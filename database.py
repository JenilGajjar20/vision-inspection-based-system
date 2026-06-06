import mysql.connector

from db_config import get_database_config


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
