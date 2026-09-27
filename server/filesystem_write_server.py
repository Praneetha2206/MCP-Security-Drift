from pathlib import Path
import json

from mcp.server import MCPServer


# Create the MCP server
mcp = MCPServer("Filesystem Write Permission Server")


# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Scenario-specific configuration
CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "filesystem_write_baseline.json"
)


def load_config():
    """Load the current filesystem write configuration."""

    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def is_allowed(path: Path) -> bool:
    """Check whether a path is inside an allowed filesystem root."""

    config = load_config()
    resolved_path = path.resolve()

    for root in config.get("allowed_roots", []):

        allowed_root = (
            PROJECT_ROOT / root
        ).resolve()

        try:
            resolved_path.relative_to(
                allowed_root
            )
            return True

        except ValueError:
            continue

    return False


def is_writable(path: Path) -> bool:
    """Check whether a path is inside a writable filesystem root."""

    config = load_config()
    resolved_path = path.resolve()

    for root in config.get("writable_roots", []):

        writable_root = (
            PROJECT_ROOT / root
        ).resolve()

        try:
            resolved_path.relative_to(
                writable_root
            )
            return True

        except ValueError:
            continue

    return False


@mcp.tool()
def read_file(path: str) -> str:
    """Read a file subject to the filesystem security configuration."""

    requested_path = (
        PROJECT_ROOT / path
    ).resolve()

    if not is_allowed(requested_path):

        return (
            f"DENIED: Access to '{path}' "
            "is outside the allowed filesystem scope."
        )

    if not requested_path.is_file():

        return (
            f"ERROR: File '{path}' does not exist."
        )

    try:

        return requested_path.read_text(
            encoding="utf-8"
        )

    except Exception as e:

        return (
            f"ERROR: Could not read file: {e}"
        )


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write a file subject to the filesystem write permission."""

    requested_path = (
        PROJECT_ROOT / path
    ).resolve()

    # First check whether the path itself is allowed.
    if not is_allowed(requested_path):

        return (
            f"DENIED: Access to '{path}' "
            "is outside the allowed filesystem scope."
        )

    # Then check whether writing is permitted.
    if not is_writable(requested_path):

        return (
            f"DENIED: Write access to '{path}' "
            "is not permitted by the current configuration."
        )

    try:

        requested_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        requested_path.write_text(
            content,
            encoding="utf-8"
        )

        return (
            f"ALLOWED: Successfully wrote to '{path}'."
        )

    except Exception as e:

        return (
            f"ERROR: Could not write file: {e}"
        )


if __name__ == "__main__":
    mcp.run()