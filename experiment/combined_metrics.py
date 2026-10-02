import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ORIGINAL_RESULTS_CSV = BASE_DIR / "logs" / "detector_results.csv"
EXTENSION_CSV = BASE_DIR / "logs" / "filesystem_unexercised_50rep.csv"


def calculate_metrics(name, predictions, ground_truth):
    tp = fp = tn = fn = 0

    for predicted, actual in zip(predictions, ground_truth):

        if actual == "SECURITY_RELEVANT" and predicted == "SECURITY_RELEVANT":
            tp += 1

        elif actual == "BENIGN" and predicted == "SECURITY_RELEVANT":
            fp += 1

        elif actual == "BENIGN" and predicted == "BENIGN":
            tn += 1

        elif actual == "SECURITY_RELEVANT" and predicted == "BENIGN":
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0
    )

    fnr = fn / (tp + fn) if (tp + fn) else 0

    print(f"\n{name}:")
    print(f"  TP: {tp}")
    print(f"  FP: {fp}")
    print(f"  TN: {tn}")
    print(f"  FN: {fn}")
    print(f"  Precision: {precision * 100:.2f}%")
    print(f"  Recall:    {recall * 100:.2f}%")
    print(f"  F1:        {f1 * 100:.2f}%")
    print(f"  FNR:       {fnr * 100:.2f}%")

    return {
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "FNR": fnr,
    }


# =========================================================
# LOAD ORIGINAL 550-PAIR RESULTS
# =========================================================

with open(ORIGINAL_RESULTS_CSV, newline="", encoding="utf-8") as f:
    original_rows = list(csv.DictReader(f))

print("=" * 70)
print("COMBINED 600-PAIR METRICS")
print("=" * 70)

print("\nOriginal detector results loaded:")
print(f"  Rows: {len(original_rows)}")


# =========================================================
# EXTRACT ORIGINAL RESULTS
# =========================================================

required_columns = {
    "ground_truth",
    "configuration_prediction",
    "behaviour_prediction",
    "hybrid_prediction",
}

actual_columns = set(original_rows[0].keys())

missing = required_columns - actual_columns

if missing:
    raise RuntimeError(
        f"Missing columns in detector_results.csv: {sorted(missing)}"
    )


original_ground_truth = [
    row["ground_truth"].strip().upper()
    for row in original_rows
]

original_configuration = [
    row["configuration_prediction"].strip().upper()
    for row in original_rows
]

original_behaviour = [
    row["behaviour_prediction"].strip().upper()
    for row in original_rows
]

original_hybrid = [
    row["hybrid_prediction"].strip().upper()
    for row in original_rows
]


# =========================================================
# LOAD 50 EXTENSION PAIRS
# =========================================================

with open(EXTENSION_CSV, newline="", encoding="utf-8") as f:
    extension_rows = list(csv.DictReader(f))


extension_baseline = [
    row
    for row in extension_rows
    if row["condition"].strip().upper() == "BASELINE"
]

extension_drift = [
    row
    for row in extension_rows
    if row["condition"].strip().upper() == "DRIFT"
]


if len(extension_baseline) != 50:
    raise RuntimeError(
        f"Expected 50 extension baseline rows, "
        f"got {len(extension_baseline)}."
    )

if len(extension_drift) != 50:
    raise RuntimeError(
        f"Expected 50 extension drift rows, "
        f"got {len(extension_drift)}."
    )


print("\nExtension results loaded:")
print(f"  Baseline observations: {len(extension_baseline)}")
print(f"  Drift observations:    {len(extension_drift)}")
print(f"  New paired experiments: 50")


# =========================================================
# EXTENSION GROUND TRUTH
# =========================================================
#
# Filesystem scope expands from:
#
#   sandbox/workspace
#
# to:
#
#   sandbox/workspace + sandbox/private
#
# This is classified as SECURITY_RELEVANT even though the
# selected task remains inside the original workspace.
# =========================================================

extension_ground_truth = [
    "SECURITY_RELEVANT"
] * 50


# =========================================================
# EXTENSION CONFIGURATION-ONLY PREDICTION
# =========================================================

extension_configuration = [
    "SECURITY_RELEVANT"
] * 50


# =========================================================
# EXTENSION BINARY BEHAVIOUR-ONLY PREDICTION
# =========================================================
#
# Original behaviour detector only considers ALLOWED/DENIED.
#
# ALLOWED -> ALLOWED
# therefore:
# BENIGN
# =========================================================

extension_behaviour = []

for baseline, drift in zip(
    extension_baseline,
    extension_drift
):

    baseline_outcome = baseline["outcome"].strip().upper()
    drift_outcome = drift["outcome"].strip().upper()

    if (
        baseline_outcome == "DENIED"
        and drift_outcome == "ALLOWED"
    ):
        prediction = "SECURITY_RELEVANT"
    else:
        prediction = "BENIGN"

    extension_behaviour.append(prediction)


# =========================================================
# EXTENSION BINARY HYBRID PREDICTION
# =========================================================
#
# Hybrid requires:
#
#   configuration change
#   AND
#   DENIED -> ALLOWED
#
# The configuration changes, but the task remains:
#
#   ALLOWED -> ALLOWED
#
# Therefore:
# BENIGN
# =========================================================

extension_hybrid = []

for baseline, drift in zip(
    extension_baseline,
    extension_drift
):

    baseline_outcome = baseline["outcome"].strip().upper()
    drift_outcome = drift["outcome"].strip().upper()

    baseline_metadata = baseline["security_metadata"].strip()
    drift_metadata = drift["security_metadata"].strip()

    config_changed = (
        baseline_metadata != drift_metadata
    )

    behaviour_changed = (
        baseline_outcome == "DENIED"
        and drift_outcome == "ALLOWED"
    )

    if config_changed and behaviour_changed:
        prediction = "SECURITY_RELEVANT"
    else:
        prediction = "BENIGN"

    extension_hybrid.append(prediction)


# =========================================================
# COMBINE ORIGINAL + EXTENSION
# =========================================================

combined_ground_truth = (
    original_ground_truth
    + extension_ground_truth
)

combined_configuration = (
    original_configuration
    + extension_configuration
)

combined_behaviour = (
    original_behaviour
    + extension_behaviour
)

combined_hybrid = (
    original_hybrid
    + extension_hybrid
)


# =========================================================
# DATASET SUMMARY
# =========================================================

print("\n" + "=" * 70)
print("DATASET SUMMARY")
print("=" * 70)

print(f"\nOriginal paired experiments:  {len(original_ground_truth)}")
print(f"Extension paired experiments: {len(extension_ground_truth)}")
print(f"Combined paired experiments:  {len(combined_ground_truth)}")


security_total = combined_ground_truth.count(
    "SECURITY_RELEVANT"
)

benign_total = combined_ground_truth.count(
    "BENIGN"
)

print("\nCombined ground truth:")
print(f"  SECURITY_RELEVANT: {security_total}")
print(f"  BENIGN:            {benign_total}")


if len(combined_ground_truth) != 600:
    raise RuntimeError(
        "Expected exactly 600 paired experiments."
    )


# =========================================================
# COMBINED METRICS
# =========================================================

print("\n" + "=" * 70)
print("COMBINED RESULTS")
print("=" * 70)


calculate_metrics(
    "Configuration-only",
    combined_configuration,
    combined_ground_truth,
)


calculate_metrics(
    "Binary behaviour-only",
    combined_behaviour,
    combined_ground_truth,
)


calculate_metrics(
    "Binary hybrid",
    combined_hybrid,
    combined_ground_truth,
)


# =========================================================
# EXTENSION-SPECIFIC EXTENDED BEHAVIOUR
# =========================================================
#
# This is kept separate because it uses the additional
# security_metadata instrumentation introduced for the
# extension.
# =========================================================

extended_behaviour = []

for baseline, drift in zip(
    extension_baseline,
    extension_drift
):

    baseline_metadata = baseline["security_metadata"].strip()
    drift_metadata = drift["security_metadata"].strip()

    if baseline_metadata != drift_metadata:
        prediction = "SECURITY_RELEVANT"
    else:
        prediction = "BENIGN"

    extended_behaviour.append(prediction)


print("\n" + "=" * 70)
print("EXTENSION-SPECIFIC EXTENDED BEHAVIOUR")
print("=" * 70)

calculate_metrics(
    "Extended behaviour-only (50 extension pairs)",
    extended_behaviour,
    extension_ground_truth,
)


# =========================================================
# EXTENSION CLASSIFICATION COUNTS
# =========================================================

print("\n" + "=" * 70)
print("EXTENSION CLASSIFICATION COUNTS")
print("=" * 70)

for name, predictions in [
    ("Configuration-only", extension_configuration),
    ("Binary behaviour-only", extension_behaviour),
    ("Binary hybrid", extension_hybrid),
    ("Extended behaviour-only", extended_behaviour),
]:

    security_count = predictions.count(
        "SECURITY_RELEVANT"
    )

    benign_count = predictions.count(
        "BENIGN"
    )

    print(
        f"{name}: "
        f"SECURITY_RELEVANT={security_count}, "
        f"BENIGN={benign_count}"
    )


# =========================================================
# FINAL NOTE
# =========================================================

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)

print(
    "\nOriginal 550-pair detector results were read only "
    "and were not modified."
)

print(
    "The 50 unexercised filesystem pairs were added "
    "for the combined evaluation."
)

print(
    "The metadata-based extended behavioural detector "
    "is reported separately because it uses additional "
    "instrumentation."
)