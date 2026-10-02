import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


ORIGINAL_RESULTS_CSV = (
    BASE_DIR
    / "logs"
    / "detector_results.csv"
)


EXTENSION_FILES = {
    "filesystem": (
        BASE_DIR
        / "logs"
        / "filesystem_unexercised_50rep.csv"
    ),
    "database": (
        BASE_DIR
        / "logs"
        / "database_scope_unexercised_50rep.csv"
    ),
    "network": (
        BASE_DIR
        / "logs"
        / "network_allowlist_unexercised_50rep.csv"
    ),
}


def calculate_metrics(
    name,
    predictions,
    ground_truth
):
    tp = fp = tn = fn = 0

    for predicted, actual in zip(
        predictions,
        ground_truth
    ):

        if (
            actual == "SECURITY_RELEVANT"
            and predicted == "SECURITY_RELEVANT"
        ):
            tp += 1

        elif (
            actual == "BENIGN"
            and predicted == "SECURITY_RELEVANT"
        ):
            fp += 1

        elif (
            actual == "BENIGN"
            and predicted == "BENIGN"
        ):
            tn += 1

        elif (
            actual == "SECURITY_RELEVANT"
            and predicted == "BENIGN"
        ):
            fn += 1

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall)
        else 0
    )

    fnr = (
        fn / (tp + fn)
        if (tp + fn)
        else 0
    )

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

with open(
    ORIGINAL_RESULTS_CSV,
    newline="",
    encoding="utf-8"
) as f:

    original_rows = list(
        csv.DictReader(f)
    )


print("=" * 70)
print("FINAL 700-PAIR METRICS")
print("=" * 70)


print(
    "\nOriginal detector results loaded:"
)

print(
    f"  Rows: {len(original_rows)}"
)


if len(original_rows) != 550:
    raise RuntimeError(
        "Expected 550 original paired experiments, "
        f"got {len(original_rows)}."
    )


# =========================================================
# CHECK ORIGINAL COLUMNS
# =========================================================

required_columns = {
    "ground_truth",
    "configuration_prediction",
    "behaviour_prediction",
    "hybrid_prediction",
}


actual_columns = set(
    original_rows[0].keys()
)


missing = (
    required_columns
    - actual_columns
)


if missing:
    raise RuntimeError(
        "Missing columns in detector_results.csv: "
        f"{sorted(missing)}"
    )


# =========================================================
# EXTRACT ORIGINAL RESULTS
# =========================================================

original_ground_truth = [
    row["ground_truth"]
    .strip()
    .upper()
    for row in original_rows
]


original_configuration = [
    row["configuration_prediction"]
    .strip()
    .upper()
    for row in original_rows
]


original_behaviour = [
    row["behaviour_prediction"]
    .strip()
    .upper()
    for row in original_rows
]


original_hybrid = [
    row["hybrid_prediction"]
    .strip()
    .upper()
    for row in original_rows
]


# =========================================================
# LOAD ALL THREE UNEXERCISED EXTENSIONS
# =========================================================

extension_data = {}


for name, csv_file in EXTENSION_FILES.items():

    print("\n" + "-" * 70)

    print(
        f"Loading {name} extension:"
    )

    print(
        f"  File: {csv_file}"
    )


    if not csv_file.exists():

        raise FileNotFoundError(
            f"Missing extension file: "
            f"{csv_file}"
        )


    with open(
        csv_file,
        newline="",
        encoding="utf-8"
    ) as f:

        rows = list(
            csv.DictReader(f)
        )


    if not rows:

        raise RuntimeError(
            f"{name}: CSV file is empty."
        )


    # -----------------------------------------------------
    # SUPPORT BOTH CSV FORMATS
    # -----------------------------------------------------
    #
    # Filesystem extension:
    #     condition
    #
    # Database/network extensions:
    #     phase
    #
    # -----------------------------------------------------

    if "phase" in rows[0]:

        condition_column = "phase"

    elif "condition" in rows[0]:

        condition_column = "condition"

    else:

        raise RuntimeError(
            f"{name}: CSV must contain either "
            "'phase' or 'condition'."
        )


    if "outcome" not in rows[0]:

        raise RuntimeError(
            f"{name}: CSV is missing "
            "'outcome' column."
        )


    if "security_metadata" not in rows[0]:

        raise RuntimeError(
            f"{name}: CSV is missing "
            "'security_metadata' column."
        )


    print(
        f"  Condition column: "
        f"{condition_column}"
    )

    print(
        f"  Total observations: "
        f"{len(rows)}"
    )


    # -----------------------------------------------------
    # SPLIT BASELINE / DRIFT
    # -----------------------------------------------------

    baseline_rows = [
        row
        for row in rows
        if row[condition_column]
        .strip()
        .upper()
        == "BASELINE"
    ]


    drift_rows = [
        row
        for row in rows
        if row[condition_column]
        .strip()
        .upper()
        == "DRIFT"
    ]


    # -----------------------------------------------------
    # VALIDATE 50 + 50
    # -----------------------------------------------------

    if len(baseline_rows) != 50:

        raise RuntimeError(
            f"{name}: expected 50 baseline rows, "
            f"got {len(baseline_rows)}."
        )


    if len(drift_rows) != 50:

        raise RuntimeError(
            f"{name}: expected 50 drift rows, "
            f"got {len(drift_rows)}."
        )


    extension_data[name] = {
        "all": rows,
        "baseline": baseline_rows,
        "drift": drift_rows,
    }


    print(
        "  Baseline observations: 50"
    )

    print(
        "  Drift observations:    50"
    )

    print(
        "  Paired experiments:    50"
    )


# =========================================================
# CREATE EXTENSION PREDICTIONS
# =========================================================

all_extension_ground_truth = []

all_extension_configuration = []

all_extension_behaviour = []

all_extension_hybrid = []

all_extension_extended_behaviour = []


# Also keep results separately for validation.
extension_results = {}


for name, data in extension_data.items():

    baseline_rows = data["baseline"]

    drift_rows = data["drift"]


    # -----------------------------------------------------
    # GROUND TRUTH
    # -----------------------------------------------------
    #
    # Each extension expands a security boundary:
    #
    # Filesystem:
    # workspace
    # ->
    # workspace + private
    #
    # Database:
    # experiment.db
    # ->
    # experiment.db + restricted.db
    #
    # Network:
    # internal-service
    # ->
    # internal-service + external-service
    #
    # Therefore each of the 50 pairs is
    # SECURITY_RELEVANT.
    # -----------------------------------------------------

    ground_truth = [
        "SECURITY_RELEVANT"
    ] * 50


    # -----------------------------------------------------
    # CONFIGURATION-ONLY
    # -----------------------------------------------------
    #
    # The configuration changed in every pair,
    # therefore SECURITY_RELEVANT.
    # -----------------------------------------------------

    configuration = [
        "SECURITY_RELEVANT"
    ] * 50


    behaviour = []

    hybrid = []

    extended_behaviour = []


    # -----------------------------------------------------
    # PROCESS PAIRED OBSERVATIONS
    # -----------------------------------------------------

    for baseline, drift in zip(
        baseline_rows,
        drift_rows
    ):

        baseline_outcome = (
            baseline["outcome"]
            .strip()
            .upper()
        )


        drift_outcome = (
            drift["outcome"]
            .strip()
            .upper()
        )


        baseline_metadata = (
            baseline["security_metadata"]
            .strip()
        )


        drift_metadata = (
            drift["security_metadata"]
            .strip()
        )


        # =================================================
        # BINARY BEHAVIOUR-ONLY
        # =================================================
        #
        # Original behaviour detector:
        #
        # DENIED -> ALLOWED
        #     = SECURITY_RELEVANT
        #
        # Otherwise:
        #     = BENIGN
        #
        # For unexercised drift:
        #
        # ALLOWED -> ALLOWED
        #
        # therefore BENIGN.
        # =================================================

        if (
            baseline_outcome == "DENIED"
            and drift_outcome == "ALLOWED"
        ):

            behaviour_prediction = (
                "SECURITY_RELEVANT"
            )

        else:

            behaviour_prediction = "BENIGN"


        behaviour.append(
            behaviour_prediction
        )


        # =================================================
        # BINARY HYBRID
        # =================================================
        #
        # Requires both:
        #
        # 1. configuration changed
        # 2. observed behaviour changed
        #
        # =================================================

        config_changed = (
            baseline_metadata
            != drift_metadata
        )


        behaviour_changed = (
            baseline_outcome == "DENIED"
            and drift_outcome == "ALLOWED"
        )


        if (
            config_changed
            and behaviour_changed
        ):

            hybrid_prediction = (
                "SECURITY_RELEVANT"
            )

        else:

            hybrid_prediction = "BENIGN"


        hybrid.append(
            hybrid_prediction
        )


        # =================================================
        # EXTENDED BEHAVIOUR-ONLY
        # =================================================
        #
        # Uses SECURITY_METADATA instrumentation.
        #
        # If the effective security boundary changes,
        # classify as SECURITY_RELEVANT.
        # =================================================

        if (
            baseline_metadata
            != drift_metadata
        ):

            extended_prediction = (
                "SECURITY_RELEVANT"
            )

        else:

            extended_prediction = "BENIGN"


        extended_behaviour.append(
            extended_prediction
        )


    # -----------------------------------------------------
    # STORE EXTENSION RESULTS
    # -----------------------------------------------------

    extension_results[name] = {
        "ground_truth": ground_truth,
        "configuration": configuration,
        "behaviour": behaviour,
        "hybrid": hybrid,
        "extended_behaviour": (
            extended_behaviour
        ),
    }


    # -----------------------------------------------------
    # ADD TO COMBINED DATA
    # -----------------------------------------------------

    all_extension_ground_truth.extend(
        ground_truth
    )


    all_extension_configuration.extend(
        configuration
    )


    all_extension_behaviour.extend(
        behaviour
    )


    all_extension_hybrid.extend(
        hybrid
    )


    all_extension_extended_behaviour.extend(
        extended_behaviour
    )


# =========================================================
# COMBINE ORIGINAL + ALL EXTENSIONS
# =========================================================

combined_ground_truth = (
    original_ground_truth
    + all_extension_ground_truth
)


combined_configuration = (
    original_configuration
    + all_extension_configuration
)


combined_behaviour = (
    original_behaviour
    + all_extension_behaviour
)


combined_hybrid = (
    original_hybrid
    + all_extension_hybrid
)


# =========================================================
# DATASET SUMMARY
# =========================================================

print("\n" + "=" * 70)

print(
    "DATASET SUMMARY"
)

print("=" * 70)


print(
    f"\nOriginal paired experiments: "
    f"{len(original_ground_truth)}"
)


print(
    "Filesystem extension pairs: 50"
)


print(
    "Database extension pairs:   50"
)


print(
    "Network extension pairs:    50"
)


print(
    f"Combined paired experiments: "
    f"{len(combined_ground_truth)}"
)


security_total = (
    combined_ground_truth.count(
        "SECURITY_RELEVANT"
    )
)


benign_total = (
    combined_ground_truth.count(
        "BENIGN"
    )
)


print(
    "\nCombined ground truth:"
)


print(
    f"  SECURITY_RELEVANT: "
    f"{security_total}"
)


print(
    f"  BENIGN:            "
    f"{benign_total}"
)


# =========================================================
# FINAL DATASET VALIDATION
# =========================================================

if len(combined_ground_truth) != 700:

    raise RuntimeError(
        "Expected exactly 700 paired experiments."
    )


if security_total != 550:

    raise RuntimeError(
        "Expected exactly 550 "
        "SECURITY_RELEVANT pairs."
    )


if benign_total != 150:

    raise RuntimeError(
        "Expected exactly 150 BENIGN pairs."
    )


# =========================================================
# FINAL COMBINED METRICS
# =========================================================

print("\n" + "=" * 70)

print(
    "FINAL COMBINED RESULTS — 700 PAIRS"
)

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
# EXTENDED BEHAVIOUR
# =========================================================
#
# IMPORTANT:
#
# This detector is calculated only for the 150
# unexercised extension pairs because the additional
# SECURITY_METADATA instrumentation was introduced
# specifically for these extensions.
#
# It is therefore NOT presented as a 700-pair detector
# result.
# =========================================================

print("\n" + "=" * 70)

print(
    "EXTENDED BEHAVIOUR — "
    "150 UNEXERCISED PAIRS"
)

print("=" * 70)


calculate_metrics(
    "Extended behaviour-only",
    all_extension_extended_behaviour,
    all_extension_ground_truth,
)


# =========================================================
# EXTENSION CLASSIFICATION COUNTS
# =========================================================

print("\n" + "=" * 70)

print(
    "EXTENSION CLASSIFICATION COUNTS"
)

print("=" * 70)


for name, predictions in [

    (
        "Configuration-only",
        all_extension_configuration
    ),

    (
        "Binary behaviour-only",
        all_extension_behaviour
    ),

    (
        "Binary hybrid",
        all_extension_hybrid
    ),

    (
        "Extended behaviour-only",
        all_extension_extended_behaviour
    ),

]:

    security_count = (
        predictions.count(
            "SECURITY_RELEVANT"
        )
    )


    benign_count = (
        predictions.count(
            "BENIGN"
        )
    )


    print(
        f"{name}: "
        f"SECURITY_RELEVANT="
        f"{security_count}, "
        f"BENIGN="
        f"{benign_count}"
    )


# =========================================================
# EXTENSION-BY-EXTENSION VALIDATION
# =========================================================

print("\n" + "=" * 70)

print(
    "EXTENSION VALIDATION"
)

print("=" * 70)


for name, data in extension_data.items():

    baseline_outcomes = [
        row["outcome"]
        .strip()
        .upper()
        for row in data["baseline"]
    ]


    drift_outcomes = [
        row["outcome"]
        .strip()
        .upper()
        for row in data["drift"]
    ]


    baseline_metadata = [
        row["security_metadata"]
        .strip()
        for row in data["baseline"]
    ]


    drift_metadata = [
        row["security_metadata"]
        .strip()
        for row in data["drift"]
    ]


    metadata_changed = sum(
        baseline != drift
        for baseline, drift
        in zip(
            baseline_metadata,
            drift_metadata
        )
    )


    baseline_allowed = (
        baseline_outcomes.count(
            "ALLOWED"
        )
    )


    drift_allowed = (
        drift_outcomes.count(
            "ALLOWED"
        )
    )


    print(
        f"\n{name.capitalize()}:"
    )


    print(
        f"  Baseline ALLOWED: "
        f"{baseline_allowed}/50"
    )


    print(
        f"  Drift ALLOWED: "
        f"{drift_allowed}/50"
    )


    print(
        f"  Metadata changed in: "
        f"{metadata_changed}/50 pairs"
    )


    # -----------------------------------------------------
    # Validate expected unexercised pattern
    # -----------------------------------------------------

    if baseline_allowed != 50:

        raise RuntimeError(
            f"{name}: baseline did not have "
            "50 ALLOWED outcomes."
        )


    if drift_allowed != 50:

        raise RuntimeError(
            f"{name}: drift did not have "
            "50 ALLOWED outcomes."
        )


    if metadata_changed != 50:

        raise RuntimeError(
            f"{name}: metadata did not change "
            "in all 50 pairs."
        )


# =========================================================
# FINAL NOTE
# =========================================================

print("\n" + "=" * 70)

print(
    "DONE"
)

print("=" * 70)


print(
    "\nOriginal 550-pair detector results were "
    "read only and were not modified."
)


print(
    "Three unexercised extensions were included:"
)


print(
    "  - Filesystem scope expansion: 50 pairs"
)


print(
    "  - Database scope expansion:   50 pairs"
)


print(
    "  - Network allowlist expansion: 50 pairs"
)


print(
    "\nThe extended behavioural detector uses "
    "additional SECURITY_METADATA instrumentation "
    "and is reported separately."
)