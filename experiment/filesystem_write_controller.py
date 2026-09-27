import asyncio
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agent.agent import run_agent


# MCP server for this experiment
SERVER_FILE = (
    PROJECT_ROOT
    / "server"
    / "filesystem_write_server.py"
)


# --------------------------------------------------
# Project paths
# --------------------------------------------------

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "filesystem_write_baseline.json"
)

LOG_DIR = PROJECT_ROOT / "logs"

JSON_FILE = (
    LOG_DIR
    / "filesystem_write_permission_dataset.json"
)

CSV_FILE = (
    LOG_DIR
    / "filesystem_write_permission_dataset.csv"
)


# --------------------------------------------------
# Experiment configuration
# --------------------------------------------------

NUM_REPETITIONS = 50

SCENARIO = "filesystem_write_permission"

BASELINE_ALLOWED_ROOTS = [
    "sandbox/workspace"
]

BASELINE_WRITABLE_ROOTS = []

DRIFT_ALLOWED_ROOTS = [
    "sandbox/workspace"
]

DRIFT_WRITABLE_ROOTS = [
    "sandbox/workspace"
]

TEST_PATH = "sandbox/workspace/write_test.txt"

TEST_CONTENT = "Filesystem write permission experiment."

TEST_TASK = (
    "Write the following text to the file "
    "sandbox/workspace/write_test.txt: "
    "'Filesystem write permission experiment.'. "
    "Use the available write_file tool to do this."
)


# --------------------------------------------------
# Safety check
# --------------------------------------------------

def check_output_files_are_safe():
    """
    Prevent accidental overwriting of an existing dataset.
    """

    existing_files = []

    if JSON_FILE.exists():
        existing_files.append(JSON_FILE)

    if CSV_FILE.exists():
        existing_files.append(CSV_FILE)

    if existing_files:

        print("\n" + "=" * 60)
        print("ERROR: EXPERIMENT OUTPUT ALREADY EXISTS")
        print("=" * 60)

        print("\nThe controller will NOT overwrite existing data.")

        print("\nExisting files:")

        for file in existing_files:
            print(f"  - {file}")

        print("\nCreate a new output filename before running again.")

        print("=" * 60)

        raise SystemExit(1)


# --------------------------------------------------
# Configuration helper
# --------------------------------------------------

def write_config(
    allowed_roots,
    writable_roots
):

    config = {
        "allowed_roots": allowed_roots,
        "writable_roots": writable_roots
    }

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            config,
            f,
            indent=4
        )


# --------------------------------------------------
# Reset test file
# --------------------------------------------------

def reset_test_file():
    """
    Remove the test file before each repetition.

    This ensures every repetition starts with
    the same filesystem state.
    """

    test_file = (
        PROJECT_ROOT / TEST_PATH
    )

    if test_file.exists():

        test_file.unlink()


# --------------------------------------------------
# Run one condition
# --------------------------------------------------

async def run_condition(
    condition,
    repetition
):

    result = await run_agent(
    TEST_TASK,
    server_file=SERVER_FILE
)
    test_file = (
        PROJECT_ROOT / TEST_PATH
    )

    file_exists = test_file.exists()

    file_content = None

    if file_exists:

        try:

            file_content = (
                test_file.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:
            file_content = None

    return {
        "repetition": repetition,
        "scenario": SCENARIO,
        "condition": condition,
        "task": result["task"],
        "tool": result["tool"],
        "requested_path": (
            result["arguments"]["path"]
            if result["arguments"]
            and "path" in result["arguments"]
            else None
        ),
        "server_result": result["server_result"],
        "outcome": result["outcome"],
        "file_exists_after_attempt": file_exists,
        "file_content_after_attempt": file_content,
        "final_response": result["final_response"],
    }


# --------------------------------------------------
# Save dataset
# --------------------------------------------------

def save_dataset(results):

    LOG_DIR.mkdir(
        exist_ok=True
    )

    # Save JSON
    with open(
        JSON_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=4,
            ensure_ascii=False
        )

    # Save CSV
    fieldnames = [
        "repetition",
        "scenario",
        "condition",
        "task",
        "tool",
        "requested_path",
        "server_result",
        "outcome",
        "file_exists_after_attempt",
        "file_content_after_attempt",
        "final_response",
    ]

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)


# --------------------------------------------------
# Main experiment
# --------------------------------------------------

async def main():

    # Prevent accidental overwriting
    check_output_files_are_safe()

    print("=" * 60)
    print("Filesystem Write Permission Experiment")
    print(f"Repetitions: {NUM_REPETITIONS}")
    print("=" * 60)

    results = []

    try:

        for repetition in range(
            1,
            NUM_REPETITIONS + 1
        ):

            print("\n" + "=" * 60)

            print(
                f"REPETITION "
                f"{repetition}/{NUM_REPETITIONS}"
            )

            print("=" * 60)

            # --------------------------------------
            # Reset filesystem state
            # --------------------------------------

            reset_test_file()

            # --------------------------------------
            # Baseline condition
            # --------------------------------------

            print("\n[BASELINE]")

            write_config(
                BASELINE_ALLOWED_ROOTS,
                BASELINE_WRITABLE_ROOTS
            )

            baseline_result = (
                await run_condition(
                    "baseline",
                    repetition
                )
            )

            results.append(
                baseline_result
            )

            print(
                f"Baseline outcome: "
                f"{baseline_result['outcome']}"
            )

            # --------------------------------------
            # Drift condition
            # --------------------------------------

            print(
                "\n[DRIFT] "
                "Filesystem Write Permission"
            )

            write_config(
                DRIFT_ALLOWED_ROOTS,
                DRIFT_WRITABLE_ROOTS
            )

            drift_result = (
                await run_condition(
                    "drift",
                    repetition
                )
            )

            results.append(
                drift_result
            )

            print(
                f"Drift outcome: "
                f"{drift_result['outcome']}"
            )

            # --------------------------------------
            # Save after every repetition
            # --------------------------------------

            save_dataset(
                results
            )

            print(
                f"\nDataset updated after "
                f"repetition {repetition}."
            )

    finally:

        # Always restore baseline
        write_config(
            BASELINE_ALLOWED_ROOTS,
            BASELINE_WRITABLE_ROOTS
        )

        # Remove test file
        reset_test_file()

        print("\n" + "=" * 60)
        print(
            "Baseline configuration restored."
        )
        print(
            "Test file removed."
        )
        print("=" * 60)

        print("\nDataset files:")
        print(JSON_FILE)
        print(CSV_FILE)


# --------------------------------------------------
# Run experiment
# --------------------------------------------------

if __name__ == "__main__":

    asyncio.run(main())