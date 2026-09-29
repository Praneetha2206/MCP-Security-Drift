import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

METADATA_FILE = PROJECT_ROOT / "config" / "scenario_metadata.json"
LOGS_DIR = PROJECT_ROOT / "logs"

MASTER_DATASET_FILE = LOGS_DIR / "master_dataset.csv"
MASTER_PAIRS_FILE = LOGS_DIR / "master_pairs.csv"


SCENARIO_FILES = {
    "filesystem_scope_expansion": "filesystem_scope_expansion_dataset.csv",
    "filesystem_write_permission": "filesystem_write_permission_dataset.csv",
    "database_privilege_expansion": "database_privilege_expansion_dataset.csv",
    "database_scope_expansion": "database_scope_expansion_dataset.csv",
    "network_allowlist_expansion": "network_allowlist_expansion_dataset.csv",
    "network_restriction_removal": "network_restriction_removal_dataset.csv",
    "authentication_requirement_removal": "authentication_requirement_removal_dataset.csv",
    "role_permission_expansion": "role_permission_expansion_dataset.csv",
    "logging_level_change": "logging_level_change_dataset.csv",
    "request_timeout_change": "request_timeout_change_dataset.csv",
    "log_retention_change": "log_retention_change_dataset.csv",
}


def load_metadata():
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_scenario_csv(filename):
    filepath = LOGS_DIR / filename

    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_master_dataset(metadata):
    all_rows = []

    for scenario, filename in SCENARIO_FILES.items():

        print(f"Loading: {filename}")

        if scenario not in metadata:
            raise ValueError(
                f"Scenario '{scenario}' is missing from scenario_metadata.json"
            )

        scenario_metadata = metadata[scenario]
        rows = load_scenario_csv(filename)

        for row in rows:
            enriched_row = dict(row)

            enriched_row["security_boundary"] = (
                scenario_metadata["security_boundary"]
            )

            enriched_row["ground_truth"] = (
                scenario_metadata["ground_truth"]
            )

            enriched_row["baseline_config"] = json.dumps(
                scenario_metadata["baseline_config"],
                ensure_ascii=False,
                sort_keys=True,
            )

            enriched_row["drift_config"] = json.dumps(
                scenario_metadata["drift_config"],
                ensure_ascii=False,
                sort_keys=True,
            )

            enriched_row["configuration_change"] = (
                scenario_metadata["configuration_change"]
            )

            enriched_row["expected_baseline_behavior"] = (
                scenario_metadata["expected_behavior"]["baseline"]
            )

            enriched_row["expected_drift_behavior"] = (
                scenario_metadata["expected_behavior"]["drift"]
            )

            all_rows.append(enriched_row)

    return all_rows


def save_master_dataset(rows):
    if not rows:
        raise ValueError("No rows found.")

    fieldnames = [
        "repetition",
        "scenario",
        "condition",
        "task",
        "tool",
        "arguments",
        "requested_path",
        "server_result",
        "outcome",
        "final_response",
        "security_boundary",
        "ground_truth",
        "baseline_config",
        "drift_config",
        "configuration_change",
        "expected_baseline_behavior",
        "expected_drift_behavior",
    ]

    # Keep only columns that actually exist in the source data.
    fieldnames = [
        field for field in fieldnames
        if any(field in row for row in rows)
    ]

    with open(
        MASTER_DATASET_FILE,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def build_master_pairs(rows):
    pairs = {}

    for row in rows:

        key = (
            row["scenario"],
            row["repetition"],
        )

        if key not in pairs:
            pairs[key] = {}

        condition = row["condition"]

        if condition == "baseline":
            pairs[key]["baseline"] = row

        elif condition == "drift":
            pairs[key]["drift"] = row

    paired_rows = []

    for (scenario, repetition), pair in sorted(
        pairs.items(),
        key=lambda item: (
            item[0][0],
            int(item[0][1]),
        ),
    ):

        if "baseline" not in pair:
            raise ValueError(
                f"Missing baseline observation for "
                f"{scenario}, repetition {repetition}"
            )

        if "drift" not in pair:
            raise ValueError(
                f"Missing drift observation for "
                f"{scenario}, repetition {repetition}"
            )

        baseline = pair["baseline"]
        drift = pair["drift"]

        paired_rows.append({
            "repetition": repetition,
            "scenario": scenario,

            "security_boundary": baseline["security_boundary"],
            "ground_truth": baseline["ground_truth"],

            "task": baseline["task"],

            "tool_baseline": baseline.get("tool"),
            "tool_drift": drift.get("tool"),

            "arguments_baseline": baseline.get("arguments"),
            "arguments_drift": drift.get("arguments"),

            "outcome_baseline": baseline["outcome"],
            "outcome_drift": drift["outcome"],

            "server_result_baseline": baseline["server_result"],
            "server_result_drift": drift["server_result"],

            "baseline_config": baseline["baseline_config"],
            "drift_config": baseline["drift_config"],

            "configuration_change": baseline["configuration_change"],

            "expected_baseline_behavior": (
                baseline["expected_baseline_behavior"]
            ),

            "expected_drift_behavior": (
                baseline["expected_drift_behavior"]
            ),
        })

    return paired_rows


def save_master_pairs(pairs):
    if not pairs:
        raise ValueError("No paired observations found.")

    fieldnames = list(pairs[0].keys())

    with open(
        MASTER_PAIRS_FILE,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(pairs)


def print_summary(rows, pairs):
    print("\n" + "=" * 60)
    print("MASTER DATASET SUMMARY")
    print("=" * 60)

    scenarios = sorted(
        set(row["scenario"] for row in rows)
    )

    print(f"Scenarios: {len(scenarios)}")
    print(f"Observations: {len(rows)}")
    print(f"Paired experiments: {len(pairs)}")

    print("\nObservations per scenario:")

    for scenario in scenarios:
        count = sum(
            1
            for row in rows
            if row["scenario"] == scenario
        )

        print(f"  {scenario}: {count}")

    print("\nGround truth:")

    security_count = sum(
        1
        for row in pairs
        if row["ground_truth"] == "SECURITY_RELEVANT"
    )

    benign_count = sum(
        1
        for row in pairs
        if row["ground_truth"] == "BENIGN"
    )

    print(f"  SECURITY_RELEVANT: {security_count}")
    print(f"  BENIGN: {benign_count}")

    print("\nExpected behavior:")

    behavior_counts = {}

    for pair in pairs:
        behavior = (
            pair["outcome_baseline"],
            pair["outcome_drift"],
        )

        behavior_counts[behavior] = (
            behavior_counts.get(behavior, 0) + 1
        )

    for behavior, count in sorted(behavior_counts.items()):
        print(
            f"  {behavior[0]} -> {behavior[1]}: "
            f"{count}"
        )

    print("\nFiles created:")
    print(f"  {MASTER_DATASET_FILE}")
    print(f"  {MASTER_PAIRS_FILE}")

    print("=" * 60)


def main():

    print("=" * 60)
    print("BUILDING MASTER DATASETS")
    print("=" * 60)

    metadata = load_metadata()

    rows = build_master_dataset(metadata)

    save_master_dataset(rows)

    pairs = build_master_pairs(rows)

    save_master_pairs(pairs)

    print_summary(rows, pairs)


if __name__ == "__main__":
    main()