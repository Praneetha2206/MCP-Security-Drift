from pathlib import Path
import json

from mcp.server import MCPServer

mcp = MCPServer("Network Allowlist Unexercised Security Server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "network_allowlist_unexercised_baseline.json"
)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def is_destination_allowed(destination: str) -> bool:
    config = load_config()

    allowed_destinations = config.get(
        "allowed_destinations",
        []
    )

    return destination in allowed_destinations


@mcp.tool()
def access_destination(destination: str) -> str:
    if not is_destination_allowed(destination):
        return (
            f"DENIED: Network access to "
            f"'{destination}' is not permitted."
        )

    config = load_config()

    security_metadata = (
        "SECURITY_METADATA: "
        f"effective_allowed_destinations="
        f"{config.get('allowed_destinations', [])}"
    )

    return (
        f"ALLOWED: Network access to "
        f"'{destination}' is permitted.\n"
        f"{security_metadata}"
    )


if __name__ == "__main__":
    mcp.run()