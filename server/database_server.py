from pathlib import Path
import json
import sqlite3

from mcp.server import MCPServer


mcp = MCPServer("Database Security Server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "database_privilege_baseline.json"
)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_database_path():
    config = load_config()
    return (PROJECT_ROOT / config["database"]).resolve()


def initialize_database():
    database_path = get_database_path()

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(database_path)

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


@mcp.tool()
def read_records() -> str:
    initialize_database()

    config = load_config()

    if not config.get("read_allowed", False):
        return "DENIED: Database read access is not permitted."

    database_path = get_database_path()

    try:
        connection = sqlite3.connect(database_path)

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, value FROM records ORDER BY id"
        )

        rows = cursor.fetchall()

        connection.close()

        return f"ALLOWED: {rows}"

    except Exception as e:
        return f"ERROR: Could not read database: {e}"


@mcp.tool()
def insert_record(value: str) -> str:
    initialize_database()

    config = load_config()

    if not config.get("write_allowed", False):
        return "DENIED: Database write access is not permitted."

    database_path = get_database_path()

    try:
        connection = sqlite3.connect(database_path)

        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO records (value) VALUES (?)",
            (value,),
        )

        connection.commit()

        record_id = cursor.lastrowid

        connection.close()

        return (
            f"ALLOWED: Successfully inserted record "
            f"with id {record_id}."
        )

    except Exception as e:
        return f"ERROR: Could not write to database: {e}"


if __name__ == "__main__":
    mcp.run()