from pathlib import Path
import json

from mcp.server import MCPServer

mcp = MCPServer("Authentication Security Server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "authentication_baseline.json"
)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
def access_protected_resource(resource: str) -> str:
    """
    Simulate access to a protected resource.

    Access is permitted only when authentication
    is not required or when the request is
    authenticated.
    """

    config = load_config()

    authentication_required = config.get(
        "authentication_required",
        True
    )

    request_authenticated = False

    if authentication_required and not request_authenticated:
        return (
            f"DENIED: Authentication is required "
            f"to access '{resource}'."
        )

    return (
        f"ALLOWED: Access to protected resource "
        f"'{resource}' is permitted."
    )


if __name__ == "__main__":
    mcp.run()