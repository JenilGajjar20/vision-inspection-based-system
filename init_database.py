import mysql.connector

from db_config import DB_CONFIG, get_database_config, get_server_config


CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    status ENUM('ACTIVE', 'INACTIVE') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
"""


CREATE_INSPECTION_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS inspection_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    product_name VARCHAR(100) NOT NULL,
    result ENUM('OK', 'NOT OK', 'UNCERTAIN') NOT NULL,
    prediction ENUM('OK', 'NOT OK') NOT NULL,
    status ENUM('PASS', 'FAIL', 'REVIEW') NOT NULL,
    defect VARCHAR(100),
    confidence DECIMAL(6, 2),
    image_path VARCHAR(500),
    final_decision ENUM('OK', 'NOT OK'),
    reviewed_status ENUM('PASS', 'FAIL'),
    reviewed_by VARCHAR(100),
    review_notes TEXT,
    reviewed_result ENUM('OK', 'NOT OK'),
    reviewed_at TIMESTAMP NULL,
    inspected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inspection_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE SET NULL
);
"""


CREATE_INSPECTION_PRODUCT_INDEX = """
CREATE INDEX idx_inspection_records_product_name
ON inspection_records(product_name);
"""


CREATE_INSPECTION_TIME_INDEX = """
CREATE INDEX idx_inspection_records_inspected_at
ON inspection_records(inspected_at);
"""


ADD_PREDICTION_COLUMN = """
ALTER TABLE inspection_records
ADD COLUMN prediction ENUM('OK', 'NOT OK') NOT NULL AFTER result;
"""


ADD_REVIEWED_RESULT_COLUMN = """
ALTER TABLE inspection_records
ADD COLUMN reviewed_result ENUM('OK', 'NOT OK') NULL AFTER image_path;
"""


ADD_FINAL_DECISION_COLUMN = """
ALTER TABLE inspection_records
ADD COLUMN final_decision ENUM('OK', 'NOT OK') NULL AFTER image_path;
"""


ADD_REVIEWED_STATUS_COLUMN = """
ALTER TABLE inspection_records
ADD COLUMN reviewed_status ENUM('PASS', 'FAIL') NULL AFTER final_decision;
"""


ADD_REVIEWED_BY_COLUMN = """
ALTER TABLE inspection_records
ADD COLUMN reviewed_by VARCHAR(100) NULL AFTER reviewed_status;
"""


ADD_REVIEW_NOTES_COLUMN = """
ALTER TABLE inspection_records
ADD COLUMN review_notes TEXT NULL AFTER reviewed_by;
"""


ADD_REVIEWED_AT_COLUMN = """
ALTER TABLE inspection_records
ADD COLUMN reviewed_at TIMESTAMP NULL AFTER reviewed_result;
"""


def execute_ignore_duplicate(cursor, sql):
    try:
        cursor.execute(sql)
    except mysql.connector.Error as error:
        if error.errno != 1061:
            raise


def execute_ignore_existing_column(cursor, sql):
    try:
        cursor.execute(sql)
    except mysql.connector.Error as error:
        if error.errno != 1060:
            raise


def create_database():
    server_connection = mysql.connector.connect(**get_server_config())
    server_cursor = server_connection.cursor()

    database_name = DB_CONFIG["database"]
    server_cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    )

    server_cursor.close()
    server_connection.close()


def create_tables():
    database_connection = mysql.connector.connect(**get_database_config())
    database_cursor = database_connection.cursor()

    database_cursor.execute(CREATE_PRODUCTS_TABLE)
    database_cursor.execute(CREATE_INSPECTION_RECORDS_TABLE)
    execute_ignore_existing_column(database_cursor, ADD_PREDICTION_COLUMN)
    execute_ignore_existing_column(database_cursor, ADD_FINAL_DECISION_COLUMN)
    execute_ignore_existing_column(database_cursor, ADD_REVIEWED_STATUS_COLUMN)
    execute_ignore_existing_column(database_cursor, ADD_REVIEWED_BY_COLUMN)
    execute_ignore_existing_column(database_cursor, ADD_REVIEW_NOTES_COLUMN)
    execute_ignore_existing_column(database_cursor, ADD_REVIEWED_RESULT_COLUMN)
    execute_ignore_existing_column(database_cursor, ADD_REVIEWED_AT_COLUMN)
    execute_ignore_duplicate(database_cursor, CREATE_INSPECTION_PRODUCT_INDEX)
    execute_ignore_duplicate(database_cursor, CREATE_INSPECTION_TIME_INDEX)

    database_connection.commit()
    database_cursor.close()
    database_connection.close()


def main():
    create_database()
    create_tables()
    print(f"Database initialized successfully: {DB_CONFIG['database']}")


if __name__ == "__main__":
    main()
