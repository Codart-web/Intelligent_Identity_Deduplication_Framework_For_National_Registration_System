"""
Baseline A — Exact String Matching
====================================
Nathan Sachitembe · 2022090446 · University of Zambia · 2026

The simplest possible deduplication baseline: two records are flagged as
duplicates only if ALL of first_name, last_name, and date_of_birth match
exactly (after lowercasing and stripping whitespace).

Purpose in evaluation:
    - Establishes the floor performance on this dataset
    - Proves the inadequacy of exact matching for Zambian names
    - F1 gain of proposed framework over Baseline A must be ≥ +0.40
      (Proposal Objective 09)

Expected behaviour:
    - Type 1 (typos): MISS — different spelling means no match
    - Type 2 (biometric fraud): MISS — completely different name/DOB
    - Type 3 (DOB error): MISS — different DOB field
    - Type 4 (NRC collision): PARTIAL HIT — same NRC exact match finds these
    - Type 5 (concurrent): HIT — exact same demographic data

This intentionally weak baseline validates why the full system is needed.
"""

import csv
from itertools import combinations
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from pathlib import Path


def load_dataset(citizens_path: str, gt_path: str):
    with open(citizens_path, encoding="utf-8") as f:
        citizens = list(csv.DictReader(f))
    with open(gt_path, encoding="utf-8") as f:
        ground_truth = list(csv.DictReader(f))
    return citizens, ground_truth


def normalise_field(value: str) -> str:
    """Minimal normalisation for exact matching: lowercase + strip."""
    return (value or "").lower().strip()


def exact_match_score(rec_a: dict, rec_b: dict) -> float:
    """
    Returns 1.0 if records are an exact match on all three key fields,
    0.0 otherwise.

    Key fields: first_name, last_name, date_of_birth
    Also checks NRC number collision for Type 4 detection.
    """
    # Primary exact match on demographics
    name_match = (
        normalise_field(rec_a["first_name"]) == normalise_field(rec_b["first_name"]) and
        normalise_field(rec_a["last_name"])  == normalise_field(rec_b["last_name"])
    )
    dob_match = normalise_field(rec_a["date_of_birth"]) == normalise_field(rec_b["date_of_birth"])

    if name_match and dob_match:
        return 1.0

    # NRC collision detection (catches some Type 4 pairs)
    nrc_match = normalise_field(rec_a["nrc_number"]) == normalise_field(rec_b["nrc_number"])
    if nrc_match:
        return 1.0

    return 0.0


def run_baseline_a(citizens: list, ground_truth: list,
                   threshold: float = 1.0) -> dict:
    """
    Run Baseline A over all record pairs.

    For 1000 records this is O(n²) = ~500,000 comparisons.
    Acceptable at prototype scale; in production, blocking is required.

    Args:
        citizens: List of citizen record dicts
        ground_truth: List of ground-truth pair dicts
        threshold: Score threshold for duplicate classification (1.0 for exact)

    Returns:
        dict with precision, recall, f1, confusion_matrix, per_type_results
    """
    # Build ground-truth lookup set
    gt_pairs = set()
    gt_by_type = {}
    for row in ground_truth:
        pair = frozenset([row["record_id_a"], row["record_id_b"]])
        gt_pairs.add(pair)
        dtype = row["duplicate_type"]
        if dtype not in gt_by_type:
            gt_by_type[dtype] = set()
        gt_by_type[dtype].add(pair)

    # Build record lookup
    records = {c["record_id"]: c for c in citizens}

    # Run all-pairs comparison
    predicted_pairs = set()
    record_ids = list(records.keys())

    for i in range(len(record_ids)):
        for j in range(i + 1, len(record_ids)):
            id_a, id_b = record_ids[i], record_ids[j]
            score = exact_match_score(records[id_a], records[id_b])
            if score >= threshold:
                predicted_pairs.add(frozenset([id_a, id_b]))

    # Compute overall metrics
    tp = len(predicted_pairs & gt_pairs)
    fp = len(predicted_pairs - gt_pairs)
    fn = len(gt_pairs - predicted_pairs)
    tn = (len(record_ids) * (len(record_ids) - 1) // 2) - tp - fp - fn

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)

    # Per-type analysis
    per_type = {}
    for dtype, type_gt_pairs in gt_by_type.items():
        type_tp = len(predicted_pairs & type_gt_pairs)
        type_fn = len(type_gt_pairs) - type_tp
        type_fp = len(predicted_pairs - gt_pairs)  # FP shared across types

        type_precision = type_tp / (type_tp + type_fp) if (type_tp + type_fp) > 0 else 0.0
        type_recall    = type_tp / (type_tp + type_fn) if (type_tp + type_fn) > 0 else 0.0
        type_f1        = (2 * type_precision * type_recall /
                          (type_precision + type_recall)
                          if (type_precision + type_recall) > 0 else 0.0)
        per_type[dtype] = {
            "precision": type_precision,
            "recall": type_recall,
            "f1": type_f1,
            "tp": type_tp,
            "fn": type_fn,
        }

    return {
        "system": "Baseline A — Exact Match",
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "total_predicted": len(predicted_pairs),
        "total_ground_truth": len(gt_pairs),
        "per_type": per_type,
    }


def print_results(results: dict):
    print("\n" + "=" * 60)
    print(f"  {results['system']}")
    print("=" * 60)
    print(f"  Precision : {results['precision']:.4f}")
    print(f"  Recall    : {results['recall']:.4f}")
    print(f"  F1-score  : {results['f1']:.4f}")
    print(f"  TP={results['tp']}  FP={results['fp']}  FN={results['fn']}")
    print(f"  Predicted pairs: {results['total_predicted']}  "
          f"GT pairs: {results['total_ground_truth']}")
    print()
    print(f"  Per-type breakdown:")
    print(f"  {'Type':<8} {'Prec':>7} {'Rec':>7} {'F1':>7}  {'TP':>4} {'FN':>4}")
    print(f"  {'-'*8} {'-'*7} {'-'*7} {'-'*7}  {'-'*4} {'-'*4}")
    for dtype in ["Type1", "Type2", "Type3", "Type4", "Type5"]:
        if dtype in results["per_type"]:
            r = results["per_type"][dtype]
            print(f"  {dtype:<8} {r['precision']:>7.4f} {r['recall']:>7.4f} "
                  f"{r['f1']:>7.4f}  {r['tp']:>4} {r['fn']:>4}")
    print("=" * 60)


if __name__ == "__main__":
    import os
    dataset_dir = os.path.join(os.path.dirname(__file__), "..", "dataset")
    citizens, gt = load_dataset(
        os.path.join(dataset_dir, "citizens_1000.csv"),
        os.path.join(dataset_dir, "ground_truth.csv"),
    )
    print(f"Loaded {len(citizens)} citizens, {len(gt)} ground-truth pairs")
    results = run_baseline_a(citizens, gt)
    print_results(results)
