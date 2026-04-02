"""Evaluation script: classify test images and score against ground truth.

Usage:
    python eval/run_eval.py              # Full run (calls Claude, ~$1-2)
    python eval/run_eval.py --skip-classify  # Re-score from cached predictions
    python eval/run_eval.py --images 5   # Quick test on first 5 images
"""

import argparse
import asyncio
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.backend.services.classifier import ClassificationError, classify_image  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent
IMAGE_DIR = EVAL_DIR / "test_images"
GROUND_TRUTH_PATH = EVAL_DIR / "ground_truth.csv"
RESULTS_DIR = EVAL_DIR / "results"
PREDICTIONS_PATH = RESULTS_DIR / "predictions.json"
REPORT_PATH = RESULTS_DIR / "accuracy_report.json"
SUMMARY_PATH = RESULTS_DIR / "eval_summary.md"

SCORED_ATTRIBUTES = ["garment_type", "style", "material", "occasion", "location_country"]


def load_ground_truth(csv_path: Path) -> list[dict]:
    """Load ground truth labels from CSV."""
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_cached_predictions(json_path: Path) -> dict:
    """Load cached predictions, or return empty dict."""
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    return {}


def save_predictions(predictions: dict, json_path: Path) -> None:
    """Save predictions cache to disk."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(predictions, f, indent=2)


async def run_classification(
    ground_truth: list[dict],
    cache: dict,
    limit: int | None = None,
) -> dict:
    """Classify images, updating cache. Returns updated cache."""
    rows = ground_truth[:limit] if limit else ground_truth
    total = len(rows)

    for i, row in enumerate(rows, 1):
        filename = row["filename"]
        if filename in cache:
            print(f"  [{i}/{total}] {filename} — cached, skipping")
            continue

        image_path = str(IMAGE_DIR / filename)
        print(f"  [{i}/{total}] {filename} — classifying...", end=" ", flush=True)

        start = time.time()
        try:
            result = await classify_image(image_path)
            elapsed = time.time() - start
            print(f"done ({elapsed:.1f}s)")

            # Store all fields for analysis
            cache[filename] = {
                "garment_type": result.garment_type,
                "style": result.style,
                "material": result.material,
                "color_palette": result.color_palette,
                "pattern": result.pattern,
                "season": result.season,
                "occasion": result.occasion,
                "consumer_profile": result.consumer_profile,
                "designer_brand": result.designer_brand,
                "trend_notes": result.trend_notes,
                "description": result.description,
                "location_country": (
                    result.location.inferred_country if result.location else None
                ),
                "location_continent": (
                    result.location.inferred_continent if result.location else None
                ),
            }

        except ClassificationError as e:
            elapsed = time.time() - start
            print(f"FAILED ({elapsed:.1f}s): {e}")
            cache[filename] = {"error": str(e)}

        # Save after each image (crash-safe)
        save_predictions(cache, PREDICTIONS_PATH)

    return cache


def normalize(value: str | None) -> str:
    """Normalize a value for comparison."""
    if value is None or value == "":
        return ""
    return value.strip().lower()


def score(
    ground_truth: list[dict], predictions: dict
) -> dict:
    """Compare predictions to ground truth, return accuracy metrics."""
    per_attr: dict[str, dict] = {}

    for attr in SCORED_ATTRIBUTES:
        correct = 0
        total = 0
        confusions: list[tuple[str, str]] = []

        for row in ground_truth:
            filename = row["filename"]
            if filename not in predictions:
                continue
            pred = predictions[filename]
            if "error" in pred:
                continue

            gt_val = normalize(row.get(attr, ""))
            pred_val = normalize(pred.get(attr, ""))

            total += 1
            if gt_val == pred_val:
                correct += 1
            else:
                confusions.append((row.get(attr, ""), pred.get(attr, "")))

        # Count top confusion pairs
        confusion_counts = Counter(confusions).most_common(5)
        top_confusions = [
            {"ground_truth": gt, "predicted": pr, "count": c}
            for (gt, pr), c in confusion_counts
        ]

        accuracy = (correct / total * 100) if total > 0 else 0.0
        per_attr[attr] = {
            "correct": correct,
            "total": total,
            "accuracy": round(accuracy, 1),
            "top_confusions": top_confusions,
        }

    # Overall accuracy (average of per-attribute)
    accuracies = [v["accuracy"] for v in per_attr.values() if v["total"] > 0]
    overall = round(sum(accuracies) / len(accuracies), 1) if accuracies else 0.0

    return {"overall_accuracy": overall, "per_attribute": per_attr}


def write_report(scores: dict, ground_truth: list[dict], predictions: dict) -> None:
    """Write accuracy_report.json and eval_summary.md."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # JSON report
    with open(REPORT_PATH, "w") as f:
        json.dump(scores, f, indent=2)
    print(f"\n  Report saved: {REPORT_PATH}")

    # Markdown summary
    lines = [
        "# Evaluation Summary",
        "",
        f"**Test set**: {len(ground_truth)} images",
        f"**Predictions available**: {sum(1 for p in predictions.values() if 'error' not in p)}",
        f"**Overall accuracy**: {scores['overall_accuracy']}%",
        "",
        "## Per-Attribute Accuracy",
        "",
        "| Attribute | Correct | Total | Accuracy |",
        "|-----------|---------|-------|----------|",
    ]

    for attr in SCORED_ATTRIBUTES:
        data = scores["per_attribute"][attr]
        lines.append(
            f"| {attr} | {data['correct']} | {data['total']} | {data['accuracy']}% |"
        )

    lines.append("")
    lines.append("## Top Confusion Pairs")
    lines.append("")

    for attr in SCORED_ATTRIBUTES:
        data = scores["per_attribute"][attr]
        if data["top_confusions"]:
            lines.append(f"### {attr}")
            lines.append("")
            for conf in data["top_confusions"][:3]:
                gt = conf["ground_truth"] or "(empty)"
                pr = conf["predicted"] or "(empty)"
                lines.append(f"- **{gt}** misclassified as **{pr}** ({conf['count']}x)")
            lines.append("")

    # Preserve existing analysis section if it has real content
    analysis_section = None
    if SUMMARY_PATH.exists():
        existing = SUMMARY_PATH.read_text()
        marker = "## Analysis"
        if marker in existing and "placeholder" not in existing.split(marker, 1)[1].lower():
            analysis_section = marker + existing.split(marker, 1)[1]

    if analysis_section:
        lines.append(analysis_section.rstrip())
        lines.append("")
    else:
        lines.append("## Analysis")
        lines.append("")
        lines.append("### Where the model excels")
        lines.append("")
        lines.append("_Auto-generated placeholder — will be updated after results review._")
        lines.append("")
        lines.append("### Failure modes")
        lines.append("")
        lines.append("_Auto-generated placeholder — will be updated after results review._")
        lines.append("")
        lines.append("### Improvements with more time")
        lines.append("")
        lines.append("- _Placeholder_")
        lines.append("")

    with open(SUMMARY_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  Summary saved: {SUMMARY_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run garment classification evaluation")
    parser.add_argument(
        "--skip-classify",
        action="store_true",
        help="Skip classification, re-score from cached predictions",
    )
    parser.add_argument(
        "--images",
        type=int,
        default=None,
        help="Limit to first N images (for quick testing)",
    )
    args = parser.parse_args()

    # Load data
    print("Loading ground truth...")
    ground_truth = load_ground_truth(GROUND_TRUTH_PATH)
    print(f"  Found {len(ground_truth)} entries")

    predictions = load_cached_predictions(PREDICTIONS_PATH)
    print(f"  Cached predictions: {len(predictions)}")

    # Classify (unless skipped)
    if not args.skip_classify:
        print("\nRunning classification...")
        predictions = asyncio.run(
            run_classification(ground_truth, predictions, limit=args.images)
        )
    else:
        print("\nSkipping classification (using cached predictions)")

    # Score
    limit_rows = ground_truth[: args.images] if args.images else ground_truth
    print("\nScoring predictions...")
    scores = score(limit_rows, predictions)

    # Report
    print("\nWriting reports...")
    write_report(scores, limit_rows, predictions)

    # Print summary to console
    print(f"\n{'='*50}")
    print(f"Overall accuracy: {scores['overall_accuracy']}%")
    print(f"{'='*50}")
    for attr in SCORED_ATTRIBUTES:
        data = scores["per_attribute"][attr]
        print(f"  {attr:25s} {data['accuracy']:5.1f}%  ({data['correct']}/{data['total']})")


if __name__ == "__main__":
    main()
