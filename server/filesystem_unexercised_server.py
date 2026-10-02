from pathlib import Path
import json

from mcp.server import MCPServer


mcp = MCPServer("Filesystem Unexercised Drift Server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "filesystem_unexercised_baseline.json"
)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def is_allowed(path: Path) -> bool:
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
    requested_path = (PROJECT_ROOT / path).resolve()

    config = load_config()

    if not is_allowed(requested_path):
        return (
            f"DENIED: Access to '{path}' "
            "is outside the allowed filesystem scope."
        )

    if not requested_path.is_file():
        return f"ERROR: File '{path}' does not exist."

    try:
        content = requested_path.read_text(
            encoding="utf-8"
        )

        # Additional observable evidence for the
        # unexercised-drift experiment.
        effective_scope = config["allowed_roots"]

        return (
            f"ALLOWED: {content}\n"
            f"SECURITY_METADATA: "
            f"effective_allowed_roots={effective_scope}"
        )

    except Exception as e:
        return f"ERROR: Could not read file: {e}"


if __name__ == "__main__":
    mcp.run()