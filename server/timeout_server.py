import json
from pathlib import Path

from mcp.server import MCPServer

mcp = MCPServer("Request Timeout Configuration Server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "timeout_baseline.json"
)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
def process_request(resource: str) -> str:
    """
    Simulate processing a request.

    The configured timeout changes request handling
    parameters but does not change access permissions.
    """

    config = load_config()

    request_timeout = config.get(
        "request_timeout",
        30
    )

    return (
        f"ALLOWED: Request for '{resource}' was processed. "
        f"Timeout: {request_timeout} seconds."
    )


if __name__ == "__main__":
    mcp.run()