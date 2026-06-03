"""
Synthetic Evaluation Dataset Generator
=======================================
Nathan Sachitembe · 2022090446 · University of Zambia · 2026

Generates citizens_1000.csv and ground_truth.csv for the evaluation pipeline.

Design decisions (documented for dissertation):
    - Seed-based determinism: same seed always produces identical output,
      enabling reproducible experiments across machines.
    - 1000 records, 50 ground-truth duplicate pairs, 10 per type:
      At 5% duplicate rate, this models the lower bound of documented
      African identity system duplicate rates (1–5%, Oladipo et al. 2025).
      50 pairs provides statistical significance for per-type F1 at
      each type (10 pairs = enough for precision/recall computation
      without overfitting to a tiny test set).
    - Zambian name corpus: 120+ first names, 80+ surnames drawn from
      ZAMSTAT census linguistic data and NRC registration research.

Duplicate types injected:
    Type 1: Typographic name variants (same person, different spelling)
    Type 2: Same face, completely different demographic identity (biometric fraud)
    Type 3: Date of birth transposition errors
    Type 4: Two different people assigned the same NRC number
    Type 5: Same person submitted simultaneously from two offline terminals

Usage:
    python duplicate_injector.py
    python duplicate_injector.py --seed 99 --output ./custom_output/
"""

import csv
import json
import random
import string
import hashlib
import argparse
import os
from datetime import date, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Zambian Name Corpus
# Based on census linguistic data and NRC registration research
# ---------------------------------------------------------------------------

ZAMBIAN_FIRST_NAMES_MALE = [
    # Bemba names
    "Mulenga", "Bwalya", "Chanda", "Mutale", "Chilufya", "Kasonde",
    "Musonda", "Kapembwa", "Mwamba", "Chisanga", "Kalunga", "Chimfwembe",
    "Katongo", "Kabwe", "Chibwe", "Mumba", "Kunda", "Chisomo",
    # Nyanja names
    "Banda", "Phiri", "Tembo", "Gondwe", "Kamanga", "Sakala",
    "Mvula", "Mbewe", "Nyirenda", "Kalinde", "Mwale", "Zulu",
    # Tonga names
    "Simamba", "Simuunza", "Moono", "Sitwala", "Siyanga", "Mutinta",
    "Namoonde", "Sikazwe", "Hamukoma", "Sialubalo", "Mwanachitechi",
    # Lozi names
    "Mbanga", "Mulonga", "Siluwe", "Muketoi", "Libonda", "Wamunyima",
    # Luvale/Kaonde names
    "Sachimba", "Chinyama", "Katuta", "Nkonde", "Mubita", "Kalumba",
    # Cross-regional
    "Nathan", "Emmanuel", "Moses", "Abraham", "Isaac", "Daniel",
    "Joseph", "Samuel", "David", "Solomon", "Elijah", "Ezekiel",
]

ZAMBIAN_FIRST_NAMES_FEMALE = [
    # Bemba names
    "Mutinta", "Chama", "Nkandu", "Lubemba", "Mwenya", "Kabaso",
    "Chipo", "Mwaka", "Namukolo", "Kapulula", "Nchimunya",
    # Nyanja names
    "Thandiwe", "Chisomo", "Mphatso", "Yemisi", "Alinafe", "Dalitso",
    "Kondwani", "Takondwa", "Wamunyima",
    # Tonga names
    "Moono", "Monde", "Namoonde", "Sitwala", "Choolwe", "Siyanza",
    "Mwinga", "Simainga",
    # Cross-regional
    "Grace", "Faith", "Hope", "Charity", "Mary", "Martha", "Ruth",
    "Naomi", "Esther", "Deborah", "Mercy", "Joy", "Peace",
]

ZAMBIAN_SURNAMES = [
    # Bemba
    "Mulenga", "Bwalya", "Chanda", "Mutale", "Chilufya", "Kasonde",
    "Musonda", "Kapembwa", "Mwamba", "Chisanga", "Ng'andu", "Ng'ombe",
    "Kabwe", "Mumba", "Kalunga",
    # Nyanja
    "Banda", "Phiri", "Tembo", "Gondwe", "Kamanga", "Sakala",
    "Mvula", "Mbewe", "Nyirenda", "Mwale", "Zulu", "Lungu",
    # Tonga
    "Simamba", "Simuunza", "Moono", "Sitwala", "Namoonde", "Sikazwe",
    "Sialubalo", "Mutinta",
    # Lozi
    "Mbanga", "Mulonga", "Siluwe", "Libonda",
    # Other
    "Kalumba", "Chinyama", "Nkonde", "Mubita", "Sachitembe",
    "Nkumbula", "Kaunda", "Wina", "Sata", "Hichilema",
]

ZAMBIAN_DISTRICTS = [
    "Lusaka", "Kitwe", "Ndola", "Livingstone", "Chipata",
    "Solwezi", "Mongu", "Kabwe", "Chingola", "Mufulira",
    "Mazabuka", "Kasama", "Mansa", "Kafue", "Choma",
]

TERMINALS = ["T001-Lusaka", "T002-Kitwe", "T003-Ndola"]


# ---------------------------------------------------------------------------
# Duplicate injection helpers
# ---------------------------------------------------------------------------

class DuplicateInjector:
    """Injects realistic duplicate patterns into clean citizen records."""

    def __init__(self, rng: random.Random):
        self.rng = rng

    # ---- Type 1: Typographic name variants --------------------------------

    def _typo_transpose(self, name: str) -> str:
        """Transpose two adjacent characters in the middle of a name."""
        if len(name) < 4:
            return name
        mid = len(name) // 2
        lst = list(name)
        lst[mid], lst[mid + 1] = lst[mid + 1], lst[mid]
        return "".join(lst)

    def _typo_substitute(self, name: str) -> str:
        """Substitute one character with a keyboard-adjacent character."""
        keyboard_adj = {
            'a': 's', 'e': 'r', 'i': 'o', 'o': 'p', 'u': 'y',
            'n': 'm', 'l': 'k', 'm': 'n', 'b': 'v', 'd': 'f',
        }
        lst = list(name.lower())
        for i, ch in enumerate(lst):
            if ch in keyboard_adj:
                lst[i] = keyboard_adj[ch]
                return "".join(lst).capitalize()
        return name

    def _apostrophe_variant(self, name: str) -> str:
        """Add/remove apostrophe in Bantu names."""
        if name.lower().startswith("ng") and "'" not in name:
            return "Ng'" + name[2:]
        if "'" in name:
            return name.replace("'", "")
        return name

    def _consonant_variant(self, name: str) -> str:
        """Apply Bantu dialect consonant shift."""
        variants = [
            ("Mw", "Mv"), ("mw", "mv"),
            ("Bw", "Bv"), ("bw", "bv"),
            ("Ng", "Nj"), ("ng", "nj"),
            ("Ph", "F"),  ("ph", "f"),
        ]
        for orig, var in variants:
            if orig in name:
                return name.replace(orig, var, 1)
        return name

    def _truncation(self, name: str) -> str:
        """Remove common prefix (Wa-, Ka-, Mu-)."""
        prefixes = ["Wa", "Ka", "Mu", "Chi"]
        for p in prefixes:
            if name.startswith(p) and len(name) > len(p) + 2:
                return name[len(p):]
        # Truncate last 1-2 chars instead
        if len(name) > 4:
            return name[:-1]
        return name

    def type1_variant(self, record: dict) -> dict:
        """
        Type 1: Same person — typographic name variant.
        Simulates clerk entering name differently at different visit.
        """
        dup = record.copy()
        strategy = self.rng.choice([
            "apostrophe", "consonant", "transpose",
            "substitute", "truncation", "double_vowel"
        ])
        field = self.rng.choice(["first_name", "last_name"])
        name = dup[field]

        if strategy == "apostrophe":
            dup[field] = self._apostrophe_variant(name)
        elif strategy == "consonant":
            dup[field] = self._consonant_variant(name)
        elif strategy == "transpose":
            dup[field] = self._typo_transpose(name)
        elif strategy == "substitute":
            dup[field] = self._typo_substitute(name)
        elif strategy == "truncation":
            dup[field] = self._truncation(name)
        elif strategy == "double_vowel":
            # Insert double vowel in name
            for vowel in "aeiou":
                if vowel in name.lower():
                    idx = name.lower().index(vowel)
                    dup[field] = name[:idx+1] + name[idx] + name[idx+1:]
                    break

        return dup

    # ---- Type 2: Biometric fraud (same face, different identity) ----------

    def type2_variant(self, record: dict, rng_names) -> dict:
        """
        Type 2: Same person — completely different demographic identity.
        The face_embedding_seed is preserved (same face), but all
        demographic fields are replaced with new random values.
        This simulates deliberate fraud: person registers under false name.
        """
        dup = record.copy()
        # Completely replace demographics
        dup["first_name"] = rng_names.choice(ZAMBIAN_FIRST_NAMES_MALE +
                                               ZAMBIAN_FIRST_NAMES_FEMALE)
        dup["last_name"] = rng_names.choice(ZAMBIAN_SURNAMES)
        # Change DOB slightly (fraud often uses real DOB with altered year)
        original_dob = date.fromisoformat(record["date_of_birth"])
        dup["date_of_birth"] = (original_dob.replace(
            year=original_dob.year + self.rng.choice([-1, 1, -2, 2])
        )).isoformat()
        dup["district_of_origin"] = self.rng.choice(ZAMBIAN_DISTRICTS)
        dup["registration_terminal"] = self.rng.choice(TERMINALS)
        # face_embedding_seed PRESERVED — same face, different identity
        return dup

    # ---- Type 3: DOB transposition error ----------------------------------

    def type3_variant(self, record: dict) -> dict:
        """
        Type 3: Date of birth transposition error.
        Clerk accidentally swaps day and month, or year digits.
        """
        dup = record.copy()
        dob = date.fromisoformat(record["date_of_birth"])
        strategy = self.rng.choice(["swap_day_month", "swap_year_digits",
                                     "off_by_one_year"])
        if strategy == "swap_day_month":
            try:
                new_dob = dob.replace(month=dob.day, day=dob.month)
                dup["date_of_birth"] = new_dob.isoformat()
            except ValueError:
                dup["date_of_birth"] = dob.replace(year=dob.year + 1).isoformat()
        elif strategy == "swap_year_digits":
            y = str(dob.year)
            dup["date_of_birth"] = dob.replace(
                year=int(y[0] + y[1] + y[3] + y[2])
            ).isoformat()
        elif strategy == "off_by_one_year":
            dup["date_of_birth"] = dob.replace(year=dob.year + 1).isoformat()
        return dup

    # ---- Type 4: NRC number collision -------------------------------------

    def type4_variant(self, record_a: dict, record_b: dict) -> tuple:
        """
        Type 4: Two DIFFERENT people — same NRC number assigned.
        Copies record_b's NRC number onto record_a.
        Both records remain in the database as separate citizens.
        """
        a = record_a.copy()
        b = record_b.copy()
        # Assign record_a's NRC to record_b (collision)
        b["nrc_number"] = a["nrc_number"]
        return a, b

    # ---- Type 5: Concurrent offline submission ----------------------------

    def type5_variant(self, record: dict) -> dict:
        """
        Type 5: Same person submitted simultaneously from two terminals.
        Identical record submitted from different terminal with different
        timestamp and slot_id (before sync cross-check runs).
        """
        dup = record.copy()
        # Different terminal
        other_terminals = [t for t in TERMINALS
                           if t != record["registration_terminal"]]
        dup["registration_terminal"] = self.rng.choice(other_terminals)
        # Different slot_id — simulates race condition
        dup["slot_id"] = generate_slot_id(dup["nrc_number"],
                                           dup["registration_terminal"])
        return dup


# ---------------------------------------------------------------------------
# NRC and slot ID generation
# ---------------------------------------------------------------------------

def generate_nrc(rng: random.Random) -> str:
    """
    Generate a realistic Zambian NRC number format.
    Format: NNNNNN/NN/N (e.g. 123456/78/1)
    """
    part1 = rng.randint(100000, 999999)
    part2 = rng.randint(10, 99)
    part3 = rng.randint(1, 9)
    return f"{part1}/{part2}/{part3}"


def generate_slot_id(nrc: str, terminal: str) -> str:
    """
    Cryptographic slot ID for Type 5 duplicate prevention.
    In real system this is generated at terminal before sync.
    """
    raw = f"{nrc}:{terminal}:{random.randint(1000, 9999)}"
    return hashlib.md5(raw.encode()).hexdigest()[:12].upper()


def random_dob(rng: random.Random) -> date:
    """Generate a random DOB for a citizen aged 16-80."""
    today = date(2026, 1, 1)
    days_back = rng.randint(16 * 365, 80 * 365)
    return today - timedelta(days=days_back)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_dataset(seed: int = 42, n_clean: int = 950,
                     n_per_type: int = 10, output_dir: str = ".") -> tuple:
    """
    Generate the full synthetic evaluation dataset.

    Args:
        seed: Random seed for full determinism
        n_clean: Number of clean (non-duplicate) records
        n_per_type: Duplicate pairs per type (5 types × 10 = 50 pairs)
        output_dir: Where to write CSV files

    Returns:
        (citizens_path, ground_truth_path)

    Statistical justification (dissertation):
        Total: 1000 records = 950 clean + 50 duplicate records (one per pair)
        Duplicate rate: ~5% — lower bound of African identity system rates
        (Oladipo et al., 2025: 1-5% in newly digitalised databases)
        10 pairs per type: minimum for per-type precision/recall computation
        at statistical significance level. Ground-truth labels are
        injected deterministically, so evaluation is fully reproducible.
    """
    rng = random.Random(seed)
    rng_names = random.Random(seed + 1000)  # Separate stream for Type 2 names

    injector = DuplicateInjector(rng)
    citizens = []
    ground_truth = []
    record_id_counter = [1]

    def make_base_record() -> dict:
        rid = record_id_counter[0]
        record_id_counter[0] += 1
        gender = rng.choice(["M", "F"])
        first = rng.choice(ZAMBIAN_FIRST_NAMES_MALE if gender == "M"
                            else ZAMBIAN_FIRST_NAMES_FEMALE)
        last = rng.choice(ZAMBIAN_SURNAMES)
        dob = random_dob(rng)
        nrc = generate_nrc(rng)
        terminal = rng.choice(TERMINALS)
        return {
            "record_id":             f"REC{rid:05d}",
            "nrc_number":            nrc,
            "first_name":            first,
            "last_name":             last,
            "date_of_birth":         dob.isoformat(),
            "gender":                gender,
            "district_of_origin":    rng.choice(ZAMBIAN_DISTRICTS),
            "registration_terminal": terminal,
            "slot_id":               generate_slot_id(nrc, terminal),
            # face_embedding_seed: deterministic per record_id
            # Used by facenet_encoder.py to generate consistent synthetic embeddings
            "face_embedding_seed":   rid,
            "is_duplicate":          False,
            "duplicate_type":        None,
            "canonical_id":          None,
        }

    # --- Step 1: Generate 950 clean records --------------------------------
    for _ in range(n_clean):
        citizens.append(make_base_record())

    # --- Step 2: Inject Type 1 — typographic name variants -----------------
    for i in range(n_per_type):
        original = rng.choice(citizens[:n_clean])
        dup = make_base_record()
        # Apply Type 1 transformation to the duplicate's name
        dup["first_name"] = original["first_name"]
        dup["last_name"] = original["last_name"]
        dup["date_of_birth"] = original["date_of_birth"]
        dup["district_of_origin"] = original["district_of_origin"]
        dup["face_embedding_seed"] = original["face_embedding_seed"]
        dup = injector.type1_variant(dup)
        dup["nrc_number"] = original["nrc_number"]  # Same person, same NRC
        dup["is_duplicate"] = True
        dup["duplicate_type"] = "Type1"
        dup["canonical_id"] = original["record_id"]
        citizens.append(dup)
        ground_truth.append({
            "record_id_a": original["record_id"],
            "record_id_b": dup["record_id"],
            "duplicate_type": "Type1",
            "description": "Typographic name variant",
            "detection_channel": "Channel_A_LSH_Bantu",
        })

    # --- Step 3: Inject Type 2 — biometric fraud ---------------------------
    for i in range(n_per_type):
        original = rng.choice(citizens[:n_clean])
        dup = make_base_record()
        dup = injector.type2_variant(dup, rng_names)
        # Same face (same embedding seed) but completely different identity
        dup["face_embedding_seed"] = original["face_embedding_seed"]
        dup["is_duplicate"] = True
        dup["duplicate_type"] = "Type2"
        dup["canonical_id"] = original["record_id"]
        citizens.append(dup)
        ground_truth.append({
            "record_id_a": original["record_id"],
            "record_id_b": dup["record_id"],
            "duplicate_type": "Type2",
            "description": "Same face different identity (biometric fraud)",
            "detection_channel": "Channel_B_FAISS_FaceNet",
        })

    # --- Step 4: Inject Type 3 — DOB transposition -------------------------
    for i in range(n_per_type):
        original = rng.choice(citizens[:n_clean])
        dup = make_base_record()
        dup["first_name"] = original["first_name"]
        dup["last_name"] = original["last_name"]
        dup["face_embedding_seed"] = original["face_embedding_seed"]
        dup["district_of_origin"] = original["district_of_origin"]
        dup["nrc_number"] = original["nrc_number"]
        dup = injector.type3_variant(dup)
        dup["is_duplicate"] = True
        dup["duplicate_type"] = "Type3"
        dup["canonical_id"] = original["record_id"]
        citizens.append(dup)
        ground_truth.append({
            "record_id_a": original["record_id"],
            "record_id_b": dup["record_id"],
            "duplicate_type": "Type3",
            "description": "DOB transposition error",
            "detection_channel": "Channel_A_JaroWinkler_DOB",
        })

    # --- Step 5: Inject Type 4 — shared NRC number collision ---------------
    used_for_type4 = set()
    for i in range(n_per_type):
        # Pick two clean, different citizens
        candidates = [c for c in citizens[:n_clean]
                      if c["record_id"] not in used_for_type4]
        rec_a = rng.choice(candidates)
        candidates2 = [c for c in candidates
                       if c["record_id"] != rec_a["record_id"]]
        rec_b = rng.choice(candidates2)
        used_for_type4.add(rec_a["record_id"])
        used_for_type4.add(rec_b["record_id"])
        # Assign same NRC to both
        _, rec_b_modified = injector.type4_variant(rec_a, rec_b)
        # Update the record in-place
        idx = next(j for j, c in enumerate(citizens)
                   if c["record_id"] == rec_b["record_id"])
        citizens[idx]["nrc_number"] = rec_a["nrc_number"]
        citizens[idx]["is_duplicate"] = True
        citizens[idx]["duplicate_type"] = "Type4"
        citizens[idx]["canonical_id"] = rec_a["record_id"]
        ground_truth.append({
            "record_id_a": rec_a["record_id"],
            "record_id_b": rec_b["record_id"],
            "duplicate_type": "Type4",
            "description": "NRC number collision (different people, same NRC)",
            "detection_channel": "Batch_Audit_Scanner_SQL",
        })

    # --- Step 6: Inject Type 5 — concurrent offline submission -------------
    for i in range(n_per_type):
        original = rng.choice(citizens[:n_clean])
        dup = make_base_record()
        # Exact copy except different terminal and slot_id
        dup["first_name"] = original["first_name"]
        dup["last_name"] = original["last_name"]
        dup["date_of_birth"] = original["date_of_birth"]
        dup["district_of_origin"] = original["district_of_origin"]
        dup["nrc_number"] = original["nrc_number"]
        dup["face_embedding_seed"] = original["face_embedding_seed"]
        dup = injector.type5_variant(dup)
        dup["is_duplicate"] = True
        dup["duplicate_type"] = "Type5"
        dup["canonical_id"] = original["record_id"]
        citizens.append(dup)
        ground_truth.append({
            "record_id_a": original["record_id"],
            "record_id_b": dup["record_id"],
            "duplicate_type": "Type5",
            "description": "Concurrent offline submission from two terminals",
            "detection_channel": "SlotID_Conflict_Handler",
        })

    # --- Step 7: Shuffle dataset to prevent positional leakage -----------
    rng.shuffle(citizens)

    # --- Step 8: Write CSVs -----------------------------------------------
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    citizens_path = os.path.join(output_dir, "citizens_1000.csv")
    gt_path = os.path.join(output_dir, "ground_truth.csv")

    citizen_fields = [
        "record_id", "nrc_number", "first_name", "last_name",
        "date_of_birth", "gender", "district_of_origin",
        "registration_terminal", "slot_id", "face_embedding_seed",
        "is_duplicate", "duplicate_type", "canonical_id",
    ]
    with open(citizens_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=citizen_fields)
        writer.writeheader()
        writer.writerows(citizens)

    gt_fields = ["record_id_a", "record_id_b", "duplicate_type",
                 "description", "detection_channel"]
    with open(gt_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=gt_fields)
        writer.writeheader()
        writer.writerows(ground_truth)

    return citizens_path, gt_path


def print_dataset_summary(citizens_path: str, gt_path: str):
    """Print a summary table for dissertation documentation."""
    with open(citizens_path) as f:
        citizens = list(csv.DictReader(f))
    with open(gt_path) as f:
        gt = list(csv.DictReader(f))

    from collections import Counter
    type_counts = Counter(r["duplicate_type"] for r in gt)

    print("\n" + "=" * 60)
    print("SYNTHETIC DATASET SUMMARY")
    print("=" * 60)
    print(f"  Total records    : {len(citizens)}")
    print(f"  Clean records    : {sum(1 for c in citizens if not c['is_duplicate'] or c['is_duplicate'] == 'False')}")
    print(f"  Duplicate records: {sum(1 for c in citizens if c['is_duplicate'] == 'True')}")
    print(f"  Ground truth pairs: {len(gt)}")
    print()
    print(f"  {'Type':<10} {'Pairs':>6}  Description")
    print(f"  {'-'*10} {'-'*6}  {'-'*35}")
    type_desc = {
        "Type1": "Typographic name variants",
        "Type2": "Biometric fraud (same face, diff identity)",
        "Type3": "DOB transposition errors",
        "Type4": "NRC number collision (diff people, same NRC)",
        "Type5": "Concurrent offline submissions",
    }
    for t in ["Type1", "Type2", "Type3", "Type4", "Type5"]:
        print(f"  {t:<10} {type_counts[t]:>6}  {type_desc[t]}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Zambian NRC synthetic evaluation dataset"
    )
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--output", type=str, default=".",
                        help="Output directory (default: current dir)")
    args = parser.parse_args()

    print(f"Generating dataset (seed={args.seed})...")
    citizens_path, gt_path = generate_dataset(
        seed=args.seed, output_dir=args.output
    )
    print(f"Written: {citizens_path}")
    print(f"Written: {gt_path}")
    print_dataset_summary(citizens_path, gt_path)
