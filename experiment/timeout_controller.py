import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generic_controller import run_experiment


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SERVER_FILE = (
    PROJECT_ROOT
    / "server"
    / "timeout_server.py"
)

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "timeout_baseline.json"
)

LOG_DIR = PROJECT_ROOT / "logs"

JSON_FILE = (
    LOG_DIR
    / "request_timeout_change_dataset.json"
)

CSV_FILE = (
    LOG_DIR
    / "request_timeout_change_dataset.csv"
)

SCENARIO = "request_timeout_change"


BASELINE_CONFIG = {
    "request_timeout": 30
}


DRIFT_CONFIG = {
    "request_timeout": 60
}


TEST_TASK = (
    "Process the resource 'service-status'. "
    "Use the available process_request tool to do this."
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