from pathlib import Path
import json
import psycopg2


def load_config():
    relative_path_to_config = Path("config.json")
    absolute_path_to_config = relative_path_to_config.resolve()
    with open(absolute_path_to_config, 'r', encoding='utf-8') as config_file:
        return json.load(config_file)


def db_connect(config, database_name="postgres"):
    return psycopg2.connect(
        dbname=database_name,
        user=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"]
    )


def create_database():
    try:
        config = load_config()
        db_name = config["database"]

        conn = db_connect(config)  # подключаемся к postgres
        conn.autocommit = True

        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE {db_name};")

        conn.close()
        print(f"Database '{db_name}' created successfully")
    except psycopg2.errors.DuplicateDatabase:
        print(f"Database '{db_name}' already exists.")
    except Exception as e:
        print(f"Error: {e}")


def create_tables_in_database():
    config = load_config()
    conn = db_connect(config, database_name=config["database"])

    try:
        relative_path_to_sql = Path("create_db_for_smart_storage.sql")
        absolute_path_to_sql = relative_path_to_sql.resolve()

        with open(absolute_path_to_sql, 'r', encoding='utf-8') as sql_file:
            sql_script = sql_file.read()

        with conn.cursor() as cur:
            cur.execute(sql_script)
            conn.commit()

        print("Tables created successfully!")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()


create_database()
create_tables_in_database()