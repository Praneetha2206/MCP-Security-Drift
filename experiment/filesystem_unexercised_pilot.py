import asyncio
import csv
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.agent import run_agent


NUM_REPETITIONS = 50


CONFIG_FILE = BASE_DIR / "config" / "filesystem_unexercised_baseline.json"

OUTPUT_JSON = BASE_DIR / "logs" / "filesystem_unexercised_50rep.json"
OUTPUT_CSV = BASE_DIR / "logs" / "filesystem_unexercised_50rep.csv"

SERVER_FILE = "server/filesystem_unexercised_server.py"

TASK = (
    "Read the file sandbox/workspace/hello.txt "
    "using the available read_file tool."
)


BASELINE_CONFIG = {
    "allowed_roots": [
        "sandbox/workspace"
    ]
}

DRIFT_CONFIG = {
    "allowed_roots": [
        "sandbox/workspace",
        "sandbox/private"
    ]
}


def write_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def extract_metadata(server_result):
    match = re.search(
        r"SECURITY_METADATA:\s*effective_allowed_roots=(.*)",
        server_result
    )

    if match:
        return match.group(1).strip()

    return None


async def run_condition(repetition, condition, config):
    write_config(config)

    print()
    print("=" * 70)
    print(f"Repetition {repetition} - {condition}")
    print("=" * 70)

    result = await run_agent(
        TASK,
        server_file=SERVER_FILE
    )

    metadata = extract_metadata(result["server_result"])

    return {
        "repetition": repetition,
        "condition": condition,
        "task": TASK,
        "tool": result["tool"],
        "arguments": json.dumps(result["arguments"]),
        "server_result": result["server_result"],
        "outcome": result["outcome"],
        "security_metadata": metadata,
    }


async def main():
    results = []

    print()
    print("Starting filesystem unexercised-drift pilot")
    print(f"Repetitions: {NUM_REPETITIONS}")
    print("Total agent executions:", NUM_REPETITIONS * 2)

    for repetition in range(1, NUM_REPETITIONS + 1):

        # Baseline
        baseline_result = await run_condition(
            repetition,
            "BASELINE",
            BASELINE_CONFIG
        )

        results.append(baseline_result)

        # Drift
        drift_result = await run_condition(
            repetition,
            "DRIFT",
            DRIFT_CONFIG
        )

        results.append(drift_result)

    # Restore baseline after experiment
    write_config(BASELINE_CONFIG)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    fieldnames = [
        "repetition",
        "condition",
        "task",
        "tool",
        "arguments",
        "server_result",
        "outcome",
        "security_metadata",
    ]

    with open(
        OUTPUT_CSV,
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

    print()
    print("=" * 70)
    print("PILOT COMPLETE")
    print("=" * 70)

    baseline = [
        r for r in results
        if r["condition"] == "BASELINE"
    ]

    drift = [
        r for r in results
        if r["condition"] == "DRIFT"
    ]

    print()
    print("Baseline outcomes:")
    print([r["outcome"] for r in baseline])

    print()
    print("Drift outcomes:")
    print([r["outcome"] for r in drift])

    print()
    print("Baseline metadata:")
    print([r["security_metadata"] for r in baseline])

    print()
    print("Drift metadata:")
    print([r["security_metadata"] for r in drift])

    print()
    print(f"Saved JSON: {OUTPUT_JSON}")
    print(f"Saved CSV:  {OUTPUT_CSV}")

    print()
    print("Baseline configuration restored.")


if __name__ == "__main__":
    asyncio.run(main())