"""
Baseline B — Demographic Jaro-Winkler (No Bantu Normalisation)
================================================================
Nathan Sachitembe · 2022090446 · University of Zambia · 2026

Second baseline: uses Jaro-Winkler similarity on raw (un-normalised)
demographic fields to score record pairs. No biometric channel.
No Bantu phonetic normalisation.

This baseline represents the state-of-the-art approach in many existing
African identity systems — standard string similarity without language-
specific adaptation.

Purpose in evaluation:
    - Demonstrates the performance ceiling of demographic-only systems
    - Proves that Bantu normalisation provides measurable F1 improvement
    - F1 gain of proposed framework over Baseline B must be ≥ +0.15
      (Proposal Objective 09)

Expected behaviour:
    - Type 1 (typos): PARTIAL HIT — JW catches some variants, misses
      Bantu-specific variants (Ng'andu/Ngandu, Mvamba/Mwamba)
    - Type 2 (biometric fraud): MISS — completely different demographics
    - Type 3 (DOB error): PARTIAL HIT — catches name match, may miss DOB
    - Type 4 (NRC collision): HIT — NRC exact match
    - Type 5 (concurrent): HIT — near-identical demographics

Demographic score formula (without Bantu normalisation):
    S_demo = 0.4 × JW(first_name) + 0.4 × JW(last_name) +
             0.2 × DOB_similarity
"""

import csv
import jellyfish
from datetime import date


def load_dataset(citizens_path: str, gt_path: str):
    with open(citizens_path, encoding="utf-8") as f:
        citizens = list(csv.DictReader(f))
    with open(gt_path, encoding="utf-8") as f:
        ground_truth = list(csv.DictReader(f))
    return citizens, ground_truth


def dob_similarity(dob_a: str, dob_b: str) -> float:
    """
    Date of birth similarity score.
    Returns 1.0 for exact match, partial credit for transpositions.
    """
    if dob_a == dob_b:
        return 1.0
    try:
        d_a = date.fromisoformat(dob_a)
        d_b = date.fromisoformat(dob_b)
        delta = abs((d_a - d_b).days)
        if delta == 0:
            return 1.0
        elif delta <= 31:    # within a month (day/month swap)
            return 0.85
        elif delta <= 366:   # within a year (year digit swap)
            return 0.70
        else:
            return max(0.0, 1.0 - (delta / 3650))  # decay over 10 years
    except (ValueError, TypeError):
        return jellyfish.jaro_winkler_similarity(
            str(dob_a or ""), str(dob_b or "")
        )


def demographic_score_raw(rec_a: dict, rec_b: dict) -> float:
    """
    Compute demographic similarity WITHOUT Bantu normalisation.

    Weighted combination:
        40% first_name JW
        40% last_name JW
        20% DOB similarity

    Also checks NRC exact match as a hard override (catches Type 4).
    """
    # NRC collision hard override
    nrc_a = (rec_a.get("nrc_number") or "").strip()
    nrc_b = (rec_b.get("nrc_number") or "").strip()
    if nrc_a and nrc_b and nrc_a == nrc_b:
        return 0.95  # High score but not 1.0 — still needs human review

    fn_a = (rec_a.get("first_name") or "").lower().strip()
    fn_b = (rec_b.get("first_name") or "").lower().strip()
    ln_a = (rec_a.get("last_name") or "").lower().strip()
    ln_b = (rec_b.get("last_name") or "").lower().strip()

    jw_first = jellyfish.jaro_winkler_similarity(fn_a, fn_b)
    jw_last  = jellyfish.jaro_winkler_similarity(ln_a, ln_b)

    # Also check name swap (first↔last transposition is a common clerking error)
    jw_cross_a = jellyfish.jaro_winkler_similarity(fn_a, ln_b)
    jw_cross_b = jellyfish.jaro_winkler_similarity(ln_a, fn_b)
    if (jw_cross_a + jw_cross_b) / 2 > (jw_first + jw_last) / 2:
        jw_first = jw_cross_a
        jw_last  = jw_cross_b

    dob_sim = dob_similarity(
        rec_a.get("date_of_birth", ""),
        rec_b.get("date_of_birth", ""),
    )

    return 0.4 * jw_first + 0.4 * jw_last + 0.2 * dob_sim


def run_baseline_b(citizens: list, ground_truth: list,
                   threshold: float = 0.82) -> dict:
    """
    Run Baseline B over all record pairs.

    Threshold 0.82: chosen empirically as the standard JW threshold
    for identity matching in existing literature (Christen, 2012).
    This is the value at which Ng'andu and Ngandu score without
    normalisation — demonstrating why the threshold alone is insufficient.

    Args:
        citizens: List of citizen record dicts
        ground_truth: List of ground-truth pair dicts
        threshold: Score threshold above which pair is classified as duplicate

    Returns:
        dict with precision, recall, f1, confusion_matrix, per_type_results
    """
    gt_pairs = set()
    gt_by_type = {}
    for row in ground_truth:
        pair = frozenset([row["record_id_a"], row["record_id_b"]])
        gt_pairs.add(pair)
        dtype = row["duplicate_type"]
        if dtype not in gt_by_type:
            gt_by_type[dtype] = set()
        gt_by_type[dtype].add(pair)

    records = {c["record_id"]: c for c in citizens}
    record_ids = list(records.keys())

    predicted_pairs = set()
    score_log = []  # For dissertation analysis

    for i in range(len(record_ids)):
        for j in range(i + 1, len(record_ids)):
            id_a, id_b = record_ids[i], record_ids[j]
            score = demographic_score_raw(records[id_a], records[id_b])
            if score >= threshold:
                pair = frozenset([id_a, id_b])
                predicted_pairs.add(pair)
                score_log.append((id_a, id_b, score, pair in gt_pairs))

    tp = len(predicted_pairs & gt_pairs)
    fp = len(predicted_pairs - gt_pairs)
    fn = len(gt_pairs - predicted_pairs)
    tn = (len(record_ids) * (len(record_ids) - 1) // 2) - tp - fp - fn

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)

    per_type = {}
    for dtype, type_gt_pairs in gt_by_type.items():
        type_tp = len(predicted_pairs & type_gt_pairs)
        type_fn = len(type_gt_pairs) - type_tp
        type_fp = len(predicted_pairs - gt_pairs)

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
        "system": "Baseline B — Demographic JW (No Bantu Norm)",
        "threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "total_predicted": len(predicted_pairs),
        "total_ground_truth": len(gt_pairs),
        "per_type": per_type,
        "score_log": score_log,
    }


def print_results(results: dict):
    print("\n" + "=" * 60)
    print(f"  {results['system']}")
    print(f"  Threshold: {results.get('threshold', 'N/A')}")
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
    results = run_baseline_b(citizens, gt)
    print_results(results)
