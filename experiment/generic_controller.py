import asyncio
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agent.agent import run_agent


NUM_REPETITIONS = 50


def check_output_files_are_safe(json_file, csv_file):
    existing_files = []

    if json_file.exists():
        existing_files.append(json_file)

    if csv_file.exists():
        existing_files.append(csv_file)

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


def write_config(config_file, config):
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


async def run_condition(
    task,
    server_file,
    scenario,
    condition,
    repetition,
):
    result = await run_agent(
        task,
        server_file=server_file,
    )

    return {
        "repetition": repetition,
        "scenario": scenario,
        "condition": condition,
        "task": result["task"],
        "tool": result["tool"],
        "arguments": json.dumps(
            result["arguments"],
            ensure_ascii=False,
        )
        if result["arguments"]
        else None,
        "server_result": result["server_result"],
        "outcome": result["outcome"],
    }


def save_dataset(results, json_file, csv_file):
    json_file.parent.mkdir(exist_ok=True)

    with open(
        json_file,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            results,
            f,
            indent=4,
            ensure_ascii=False,
        )

    fieldnames = [
        "repetition",
        "scenario",
        "condition",
        "task",
        "tool",
        "arguments",
        "server_result",
        "outcome",
    ]

    with open(
        csv_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)


async def run_experiment(
    scenario,
    server_file,
    config_file,
    baseline_config,
    drift_config,
    test_task,
    json_file,
    csv_file,
):
    check_output_files_are_safe(
        json_file,
        csv_file,
    )

    print("=" * 60)
    print(f"{scenario}")
    print(f"Repetitions: {NUM_REPETITIONS}")
    print("=" * 60)

    results = []

    try:
        for repetition in range(
            1,
            NUM_REPETITIONS + 1,
        ):
            print("\n" + "=" * 60)
            print(
                f"REPETITION "
                f"{repetition}/{NUM_REPETITIONS}"
            )
            print("=" * 60)

            # -------------------------
            # BASELINE
            # -------------------------

            print("\n[BASELINE]")

            write_config(
                config_file,
                baseline_config,
            )

            baseline_result = await run_condition(
                test_task,
                server_file,
                scenario,
                "baseline",
                repetition,
            )

            results.append(baseline_result)

            print(
                f"Baseline outcome: "
                f"{baseline_result['outcome']}"
            )

            # -------------------------
            # DRIFT
            # -------------------------

            print("\n[DRIFT]")

            write_config(
                config_file,
                drift_config,
            )

            drift_result = await run_condition(
                test_task,
                server_file,
                scenario,
                "drift",
                repetition,
            )

            results.append(drift_result)

            print(
                f"Drift outcome: "
                f"{drift_result['outcome']}"
            )

            # Save after every repetition
            save_dataset(
                results,
                json_file,
                csv_file,
            )

            print(
                f"\nDataset updated after "
                f"repetition {repetition}."
            )

    finally:
        # Always restore baseline
        write_config(
            config_file,
            baseline_config,
        )

        print("\n" + "=" * 60)
        print("Baseline configuration restored.")
        print("=" * 60)

        print("\nDataset files:")
        print(json_file)
        print(csv_file)