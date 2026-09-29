import json
from pathlib import Path

from mcp.server import MCPServer

mcp = MCPServer("Log Retention Configuration Server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "retention_baseline.json"
)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
def read_resource(resource: str) -> str:
    """
    Read a controlled resource.

    The configured log retention period changes
    operational logging behaviour but does not
    change access permissions.
    """

    config = load_config()

    log_retention_days = config.get(
        "log_retention_days",
        30
    )

    return (
        f"ALLOWED: Resource '{resource}' was read. "
        f"Log retention: {log_retention_days} days."
    )


if __name__ == "__main__":
    mcp.run()