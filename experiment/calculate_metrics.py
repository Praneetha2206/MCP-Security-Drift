import csv


FILE = "logs/detector_results.csv"


with open(FILE, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))


print("=" * 60)
print("ORIGINAL 11-SCENARIO METRICS")
print("=" * 60)

print(f"\nTotal paired experiments: {len(rows)}")

security = sum(
    r["ground_truth"] == "SECURITY_RELEVANT"
    for r in rows
)

benign = sum(
    r["ground_truth"] == "BENIGN"
    for r in rows
)

print(f"Security-relevant: {security}")
print(f"Benign: {benign}")


detectors = {
    "Configuration-only": "configuration_prediction",
    "Behaviour-only": "behaviour_prediction",
    "Hybrid": "hybrid_prediction",
}


for name, column in detectors.items():

    tp = sum(
        r["ground_truth"] == "SECURITY_RELEVANT"
        and r[column] == "SECURITY_RELEVANT"
        for r in rows
    )

    fp = sum(
        r["ground_truth"] == "BENIGN"
        and r[column] == "SECURITY_RELEVANT"
        for r in rows
    )

    tn = sum(
        r["ground_truth"] == "BENIGN"
        and r[column] == "BENIGN"
        for r in rows
    )

    fn = sum(
        r["ground_truth"] == "SECURITY_RELEVANT"
        and r[column] == "BENIGN"
        for r in rows
    )

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0
    )

    fnr = fn / (tp + fn) if (tp + fn) else 0

    print("\n" + "-" * 60)
    print(name)
    print("-" * 60)

    print(f"TP:        {tp}")
    print(f"FP:        {fp}")
    print(f"TN:        {tn}")
    print(f"FN:        {fn}")
    print(f"Precision: {precision:.4f} ({precision * 100:.2f}%)")
    print(f"Recall:    {recall:.4f} ({recall * 100:.2f}%)")
    print(f"F1-score:  {f1:.4f} ({f1 * 100:.2f}%)")
    print(f"FNR:       {fnr:.4f} ({fnr * 100:.2f}%)")