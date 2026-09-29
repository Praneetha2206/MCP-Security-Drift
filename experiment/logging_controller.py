import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generic_controller import run_experiment


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SERVER_FILE = (
    PROJECT_ROOT
    / "server"
    / "logging_server.py"
)

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "logging_baseline.json"
)

LOG_DIR = PROJECT_ROOT / "logs"

JSON_FILE = (
    LOG_DIR
    / "logging_level_change_dataset.json"
)

CSV_FILE = (
    LOG_DIR
    / "logging_level_change_dataset.csv"
)

SCENARIO = "logging_level_change"


BASELINE_CONFIG = {
    "logging_level": "INFO"
}


DRIFT_CONFIG = {
    "logging_level": "DEBUG"
}


TEST_TASK = (
    "Read the resource 'system-status'. "
    "Use the available read_resource tool to do this."
)


if __name__ == "__main__":
    asyncio.run(
        run_experiment(
            scenario=SCENARIO,
            server_file=SERVER_FILE,
            config_file=CONFIG_FILE,
            baseline_config=BASELINE_CONFIG,
            drift_config=DRIFT_CONFIG,
            test_task=TEST_TASK,
            json_file=JSON_FILE,
            csv_file=CSV_FILE,
        )
    )