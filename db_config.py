import os


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "vision_inspection_qms"),
}


def get_server_config():
    config = DB_CONFIG.copy()
    config.pop("database")
    return config


def get_database_config():
    return DB_CONFIG.copy()
