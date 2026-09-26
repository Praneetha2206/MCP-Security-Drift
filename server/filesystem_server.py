from pathlib import Path
import json

from mcp.server import MCPServer


# Create the MCP server
mcp = MCPServer("Filesystem Security Server")


# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configuration file
CONFIG_FILE = PROJECT_ROOT / "config" / "filesystem_baseline.json"


def load_config():
    """Load the current filesystem security configuration."""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def is_allowed(path: Path) -> bool:
    """Check whether the requested path is inside an allowed root."""

    config = load_config()
    resolved_path = path.resolve()

    for root in config["allowed_roots"]:
        allowed_root = (PROJECT_ROOT / root).resolve()

        try:
            resolved_path.relative_to(allowed_root)
            return True
        except ValueError:
            continue

    return False


@mcp.tool()
def read_file(path: str) -> str:
    """
    Read a file subject to the configured filesystem security boundary.
    """

    requested_path = (PROJECT_ROOT / path).resolve()

    if not is_allowed(requested_path):
        return (
            f"DENIED: Access to '{path}' "
            "is outside the allowed filesystem scope."
        )

    if not requested_path.is_file():
        return f"ERROR: File '{path}' does not exist."

    try:
        return requested_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"ERROR: Could not read file: {e}"


if __name__ == "__main__":
    mcp.run()