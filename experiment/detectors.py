import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "logs" / "master_pairs.csv"
OUTPUT_FILE = PROJECT_ROOT / "logs" / "detector_results.csv"


# Configuration fields that represent security-sensitive controls.
SECURITY_CONFIG_FIELDS = {
    "allowed_roots",
    "writable_roots",
    "read_allowed",
    "write_allowed",
    "allowed_databases",
    "allowed_destinations",
    "network_access_allowed",
    "authentication_required",
    "role",
}


def load_dataset():
    with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_config(config_string):
    return json.loads(config_string)


def configuration_changed(baseline_config, drift_config):
    return baseline_config != drift_config


def get_changed_fields(baseline_config, drift_config):
    all_fields = set(baseline_config) | set(drift_config)

    changed_fields = []

    for field in sorted(all_fields):
        baseline_value = baseline_config.get(field)
        drift_value = drift_config.get(field)

        if baseline_value != drift_value:
            changed_fields.append(field)

    return changed_fields


def configuration_only_detector(
    baseline_config,
    drift_config,
):
    """
    Configuration-only detection.

    Uses only the configuration difference.
    It does NOT use:
        - ground_truth
        - baseline outcome
        - drift outcome
        - server result
    """

    changed_fields = get_changed_fields(
        baseline_config,
        drift_config,
    )

    security_fields_changed = [
        field
        for field in changed_fields
        if field in SECURITY_CONFIG_FIELDS
    ]

    if security_fields_changed:
        prediction = "SECURITY_RELEVANT"
    else:
        prediction = "BENIGN"

    return prediction, changed_fields


def behaviour_only_detector(
    baseline_outcome,
    drift_outcome,
):
    """
    Behaviour-only detection.

    Uses only the observed baseline and drift outcomes.
    It does NOT use configuration information.
    """

    if (
        baseline_outcome == "DENIED"
        and drift_outcome == "ALLOWED"
    ):
        return "SECURITY_RELEVANT"

    return "BENIGN"


def hybrid_detector(
    configuration_prediction,
    behaviour_prediction,
):
    """
    Hybrid detection.

    Requires both configuration and behaviour
    to indicate a security-relevant change.
    """

    if (
        configuration_prediction == "SECURITY_RELEVANT"
        and behaviour_prediction == "SECURITY_RELEVANT"
    ):
        return "SECURITY_RELEVANT"

    return "BENIGN"


def run_detectors(rows):
    results = []

    for row in rows:

        baseline_config = parse_config(
            row["baseline_config"]
        )

        drift_config = parse_config(
            row["drift_config"]
        )

        configuration_prediction, changed_fields = (
            configuration_only_detector(
                baseline_config,
                drift_config,
            )
        )

        behaviour_prediction = behaviour_only_detector(
            row["outcome_baseline"],
            row["outcome_drift"],
        )

        hybrid_prediction = hybrid_detector(
            configuration_prediction,
            behaviour_prediction,
        )

        results.append({
            "repetition": row["repetition"],
            "scenario": row["scenario"],
            "security_boundary": row["security_boundary"],
            "ground_truth": row["ground_truth"],

            "outcome_baseline": row["outcome_baseline"],
            "outcome_drift": row["outcome_drift"],

            "changed_configuration_fields": json.dumps(
                changed_fields
            ),

            "configuration_prediction": (
                configuration_prediction
            ),

            "behaviour_prediction": (
                behaviour_prediction
            ),

            "hybrid_prediction": (
                hybrid_prediction
            ),
        })

    return results


def save_results(results):

    fieldnames = [
        "repetition",
        "scenario",
        "security_boundary",
        "ground_truth",
        "outcome_baseline",
        "outcome_drift",
        "changed_configuration_fields",
        "configuration_prediction",
        "behaviour_prediction",
        "hybrid_prediction",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)


def print_summary(results):

    print("\n" + "=" * 60)
    print("DETECTOR SUMMARY")
    print("=" * 60)

    total = len(results)

    print(f"Total paired experiments: {total}")

    for detector_name, field in [
        (
            "Configuration-only",
            "configuration_prediction",
        ),
        (
            "Behaviour-only",
            "behaviour_prediction",
        ),
        (
            "Hybrid",
            "hybrid_prediction",
        ),
    ]:

        security_predictions = sum(
            1
            for row in results
            if row[field] == "SECURITY_RELEVANT"
        )

        benign_predictions = sum(
            1
            for row in results
            if row[field] == "BENIGN"
        )

        print(f"\n{detector_name}:")
        print(
            f"  SECURITY_RELEVANT: "
            f"{security_predictions}"
        )
        print(
            f"  BENIGN: "
            f"{benign_predictions}"
        )

    print("\nResults saved to:")
    print(OUTPUT_FILE)

    print("=" * 60)


def main():

    print("=" * 60)
    print("RUNNING SECURITY DRIFT DETECTORS")
    print("=" * 60)

    rows = load_dataset()

    print(f"Loaded {len(rows)} paired experiments.")

    results = run_detectors(rows)

    save_results(results)

    print_summary(results)


if __name__ == "__main__":
    main()