import csv
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

# Read v1.2 sensitivity summary
summary_file = RESULTS / "v1_2_sensitivity_summary.csv"
with summary_file.open(newline="") as handle:
	rows = list(csv.DictReader(handle))

# Keep the overview focused on the main sensitivity conclusions
parameter_order = [
	"Ag+ mobility",
	"Activation energy",
	"Maximum filament radius",
	"Dissolution rate factor",
	"Positive-bias time limit",
]

rows.sort(key=lambda row: parameter_order.index(row["parameter"]))

# Convert qualitative classification to numerical score
classification_score = {
	"High": 3,
	"Conditional": 2,
}

scores = [classification_score[row["sensitivity_category"]] for row in rows]

# Create overview plot
plt.figure(figsize=(10, 6))

plt.bar(
	[row["parameter"] for row in rows],
	scores,
)

plt.ylabel("Sensitivity Classification")
plt.title("v1.2 Parameter Sensitivity Overview")

plt.yticks(
	[1, 2, 3],
	["Low", "Conditional", "High"],
)

plt.xticks(rotation=20, ha="right")
plt.tight_layout()

output_file = RESULTS / "v1_2_results_overview.png"
plt.savefig(output_file, dpi=300)
plt.close()

print(f"Created: {output_file}")
