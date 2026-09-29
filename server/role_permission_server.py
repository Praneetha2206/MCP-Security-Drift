from pathlib import Path
import json

from mcp.server import MCPServer

mcp = MCPServer("Role Permission Security Server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "role_permission_baseline.json"
)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
def modify_resource(resource: str) -> str:
    """
    Simulate modifying a protected resource.

    The operation is permitted only when the configured
    role has write permission.
    """

    config = load_config()

    role = config.get("role", "reader")

    if role != "writer":
        return (
            f"DENIED: Role '{role}' does not have "
            f"permission to modify '{resource}'."
        )

    return (
        f"ALLOWED: Role '{role}' is permitted "
        f"to modify '{resource}'."
    )


if __name__ == "__main__":
    mcp.run()