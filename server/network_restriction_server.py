from pathlib import Path
import json

from mcp.server import MCPServer

mcp = MCPServer("Network Restriction Security Server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "network_restriction_baseline.json"
)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
def access_network(resource: str) -> str:
    """
    Simulate access to a network resource.

    Access is controlled by the configured network
    restriction.
    """

    config = load_config()

    network_access_allowed = config.get(
        "network_access_allowed",
        False
    )

    if not network_access_allowed:
        return (
            f"DENIED: Network access to "
            f"'{resource}' is restricted."
        )

    return (
        f"ALLOWED: Network access to "
        f"'{resource}' is permitted."
    )


if __name__ == "__main__":
    mcp.run()