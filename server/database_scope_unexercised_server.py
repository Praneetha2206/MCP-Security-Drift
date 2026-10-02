from pathlib import Path
import json
import sqlite3

from mcp.server import MCPServer


mcp = MCPServer("Database Scope Unexercised Security Server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "database_scope_unexercised_baseline.json"
)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_database(database):
    return (PROJECT_ROOT / database).resolve()


def is_database_allowed(database):
    config = load_config()

    requested_database = resolve_database(database)

    for allowed_database in config.get(
        "allowed_databases",
        []
    ):
        allowed_path = resolve_database(
            allowed_database
        )

        if requested_database == allowed_path:
            return True

    return False


def initialize_database(database):
    database_path = resolve_database(database)

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
def read_records(database: str) -> str:

    if not is_database_allowed(database):
        return (
            f"DENIED: Access to database "
            f"'{database}' is not permitted."
        )

    initialize_database(database)

    database_path = resolve_database(database)

    try:
        connection = sqlite3.connect(database_path)

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, value FROM records ORDER BY id"
        )

        rows = cursor.fetchall()

        connection.close()

        config = load_config()

        security_metadata = (
            "SECURITY_METADATA: "
            f"effective_allowed_databases="
            f"{config.get('allowed_databases', [])}"
        )

        return (
            f"ALLOWED: {rows}\n"
            f"{security_metadata}"
        )

    except Exception as e:
        return (
            f"ERROR: Could not read database: {e}"
        )


if __name__ == "__main__":
    mcp.run()