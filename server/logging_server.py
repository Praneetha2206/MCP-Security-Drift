import json
from pathlib import Path

from mcp.server import MCPServer

mcp = MCPServer("Logging Configuration Server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "logging_baseline.json"
)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
def read_resource(resource: str) -> str:
    """
    Read a controlled resource.

    The logging configuration changes the amount of
    diagnostic information recorded, but does not
    change access permissions.
    """

    config = load_config()

    logging_level = config.get(
        "logging_level",
        "INFO"
    )

    return (
        f"ALLOWED: Resource '{resource}' was read. "
        f"Logging level: {logging_level}."
    )


if __name__ == "__main__":
    mcp.run()