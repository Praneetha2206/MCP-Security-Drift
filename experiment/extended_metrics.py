import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

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
# LOAD EXTENSION DATA
# =========================================================

with open(EXTENSION_CSV, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))


baseline_rows = [
    row for row in rows
    if row["condition"].strip().upper() == "BASELINE"
]

drift_rows = [
    row for row in rows
    if row["condition"].strip().upper() == "DRIFT"
]


# =========================================================
# VALIDATE DATA
# =========================================================

if len(baseline_rows) != 50:
    raise RuntimeError(
        f"Expected 50 baseline rows, got {len(baseline_rows)}."
    )

if len(drift_rows) != 50:
    raise RuntimeError(
        f"Expected 50 drift rows, got {len(drift_rows)}."
    )


print("=" * 70)
print("EXTENDED UNEXERCISED-DRIFT METRICS")
print("=" * 70)

print("\nLoaded:")
print(f"  Baseline observations: {len(baseline_rows)}")
print(f"  Drift observations:    {len(drift_rows)}")
print(f"  Paired experiments:    {len(baseline_rows)}")


# =========================================================
# GROUND TRUTH
# =========================================================
#
# The configuration expands the filesystem security boundary:
#
# Baseline:
#   sandbox/workspace
#
# Drift:
#   sandbox/workspace
#   sandbox/private
#
# The tested task remains inside the original workspace.
# Therefore the task outcome stays ALLOWED -> ALLOWED.
#
# However, the configuration change itself is security-relevant
# because it expands the permitted filesystem boundary.
#
# Therefore:
#
#   GT = SECURITY_RELEVANT
#
# for all 50 paired experiments.
# =========================================================

ground_truth = ["SECURITY_RELEVANT"] * 50


print("\nGround truth:")
print("  SECURITY_RELEVANT: 50")
print("  BENIGN: 0")
print("  Reason: filesystem security boundary expanded.")


# =========================================================
# 1. CONFIGURATION-ONLY DETECTOR
# =========================================================
#
# The configuration changed from:
#
#   ['sandbox/workspace']
#
# to:
#
#   ['sandbox/workspace', 'sandbox/private']
#
# Therefore configuration-only detects all 50.
# =========================================================

configuration_predictions = [
    "SECURITY_RELEVANT"
] * 50


# =========================================================
# 2. ORIGINAL BINARY BEHAVIOUR-ONLY DETECTOR
# =========================================================
#
# The original behaviour detector only considers the
# ALLOWED/DENIED outcome.
#
# Baseline:
#   ALLOWED
#
# Drift:
#   ALLOWED
#
# Therefore there is no DENIED -> ALLOWED transition.
#
# All 50 are classified as BENIGN.
# =========================================================

binary_behaviour_predictions = []

for baseline, drift in zip(baseline_rows, drift_rows):

    baseline_outcome = baseline["outcome"].strip().upper()
    drift_outcome = drift["outcome"].strip().upper()

    if (
        baseline_outcome == "DENIED"
        and drift_outcome == "ALLOWED"
    ):
        prediction = "SECURITY_RELEVANT"
    else:
        prediction = "BENIGN"

    binary_behaviour_predictions.append(prediction)


# =========================================================
# 3. ORIGINAL BINARY HYBRID DETECTOR
# =========================================================
#
# Hybrid requires:
#
#   configuration change
#   AND
#   DENIED -> ALLOWED behaviour change
#
# In this extension:
#
#   configuration changed = TRUE
#   DENIED -> ALLOWED      = FALSE
#
# Therefore all 50 are classified as BENIGN.
#
# NOTE:
# security_metadata is used here as the observed
# configuration/effective-boundary evidence for this
# instrumented extension.
# =========================================================

hybrid_predictions = []

for baseline, drift in zip(baseline_rows, drift_rows):

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

    hybrid_predictions.append(prediction)


# =========================================================
# 4. EXTENDED BEHAVIOUR-ONLY DETECTOR
# =========================================================
#
# The MCP server in this extension is instrumented to expose
# security metadata describing the effective filesystem scope.
#
# Baseline:
#   ['sandbox/workspace']
#
# Drift:
#   ['sandbox/workspace', 'sandbox/private']
#
# Although the task outcome remains:
#
#   ALLOWED -> ALLOWED
#
# the security metadata changes.
#
# Therefore the extended behavioural evidence detects the
# security-relevant configuration drift.
#
# IMPORTANT:
# This metadata is instrumentation introduced for this
# experiment. It is NOT being claimed as a standard MCP
# protocol feature.
# =========================================================

extended_behaviour_predictions = []

for baseline, drift in zip(baseline_rows, drift_rows):

    baseline_metadata = baseline["security_metadata"].strip()
    drift_metadata = drift["security_metadata"].strip()

    metadata_changed = (
        baseline_metadata != drift_metadata
    )

    if metadata_changed:
        prediction = "SECURITY_RELEVANT"
    else:
        prediction = "BENIGN"

    extended_behaviour_predictions.append(prediction)


# =========================================================
# CALCULATE METRICS
# =========================================================

results = {}


results["Configuration-only"] = calculate_metrics(
    "Configuration-only",
    configuration_predictions,
    ground_truth,
)


results["Binary behaviour-only"] = calculate_metrics(
    "Binary behaviour-only",
    binary_behaviour_predictions,
    ground_truth,
)


results["Binary hybrid"] = calculate_metrics(
    "Binary hybrid",
    hybrid_predictions,
    ground_truth,
)


results["Extended behaviour-only"] = calculate_metrics(
    "Extended behaviour-only",
    extended_behaviour_predictions,
    ground_truth,
)


# =========================================================
# CLASSIFICATION COUNTS
# =========================================================

print("\n" + "=" * 70)
print("CLASSIFICATION COUNTS")
print("=" * 70)


all_predictions = [
    (
        "Configuration-only",
        configuration_predictions,
    ),
    (
        "Binary behaviour-only",
        binary_behaviour_predictions,
    ),
    (
        "Binary hybrid",
        hybrid_predictions,
    ),
    (
        "Extended behaviour-only",
        extended_behaviour_predictions,
    ),
]


for name, predictions in all_predictions:

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
# DATA CONSISTENCY CHECK
# =========================================================

print("\n" + "=" * 70)
print("DATA CONSISTENCY CHECK")
print("=" * 70)


baseline_outcomes = [
    row["outcome"].strip().upper()
    for row in baseline_rows
]

drift_outcomes = [
    row["outcome"].strip().upper()
    for row in drift_rows
]


baseline_metadata = [
    row["security_metadata"].strip()
    for row in baseline_rows
]

drift_metadata = [
    row["security_metadata"].strip()
    for row in drift_rows
]


print(
    "\nBaseline outcomes:"
    f" ALLOWED={baseline_outcomes.count('ALLOWED')},"
    f" DENIED={baseline_outcomes.count('DENIED')}"
)

print(
    "Drift outcomes:"
    f" ALLOWED={drift_outcomes.count('ALLOWED')},"
    f" DENIED={drift_outcomes.count('DENIED')}"
)

print(
    "\nUnique baseline security metadata:"
)

for value in sorted(set(baseline_metadata)):
    print(f"  {value}")


print(
    "\nUnique drift security metadata:"
)

for value in sorted(set(drift_metadata)):
    print(f"  {value}")


print("\n" + "=" * 70)
print("DONE")
print("=" * 70)