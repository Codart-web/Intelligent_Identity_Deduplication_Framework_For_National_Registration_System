"""
Zambian Bantu Phonetic Normalisation Module
============================================
Nathan Sachitembe · 2022090446 · University of Zambia · 2026

Original Academic Contribution:
    No published work has addressed phonetic normalisation specifically for
    Zambian Bantu language names in the context of identity deduplication.
    This module addresses three primary failure modes of standard similarity
    algorithms (Jaro-Winkler, Soundex, Metaphone) on Zambian name data:

    1. Apostrophe tonal markers — Ng'andu vs Ngandu
       Standard JW treats the apostrophe as a character mismatch, reducing
       similarity from the true ≥0.95 to ≤0.82.

    2. Bantu name prefix variations — Mwale vs Wale, Kalumba vs Lumba
       Inconsistent prefix attachment across Lusaka/Copperbelt/Eastern
       Province district offices produces false non-matches.

    3. Dialect consonant equivalences — Mwamba vs Mvamba (Bemba/Tonga),
       Njovu vs Ngovu (Nyanja/Tonga), Phiri vs Firi (Nyanja)
       Regional phonetic shifts create systematic JW mismatches.

Languages covered: Bemba, Nyanja, Tonga, Lozi, Luvale, Kaonde, Lunda

Usage:
    from normaliser import BantuNormaliser
    n = BantuNormaliser()
    n.normalise("Ng'andu")   # → "ngandu"
    n.normalise("Mvamba")    # → "mwamba"
    n.similarity("Ng'andu", "Ngandu")  # → float ≥ 0.95
"""

import re
import json
import unicodedata
from pathlib import Path
import jellyfish


class BantuNormaliser:
    """
    Zambian Bantu phonetic normaliser for identity deduplication.

    Applies a deterministic, rule-ordered transformation pipeline to
    produce canonical forms of Zambian names, improving downstream
    Jaro-Winkler similarity scores for genuine duplicate pairs.

    Pipeline order (critical — do not reorder without testing):
        1. Unicode normalisation and lowercase
        2. Apostrophe/tonal marker removal
        3. Double-vowel reduction
        4. Consonant equivalence substitution
        5. Common spelling variant normalisation
        6. Bantu prefix stripping (optional, see strip_prefixes param)
        7. Whitespace normalisation
    """

    # Ordered list of (pattern, replacement) tuples.
    # ORDER MATTERS: longer patterns before shorter to avoid partial replacement.
    # All patterns operate on lowercased input.
    _APOSTROPHE_RULES = [
        # Specific digraph+apostrophe combinations first
        (r"ng'([aeiou])", r"ng\1"),
        (r"nk'([aeiou])", r"nk\1"),
        (r"ch'([aeiou])", r"ch\1"),
        (r"sh'([aeiou])", r"sh\1"),
        # Generic apostrophe removal last
        (r"'", r""),
    ]

    _CONSONANT_EQUIVALENCES = [
        # Longer patterns first to prevent partial match errors
        ("ndj", "nj"),
        ("tch", "ch"),
        ("mv",  "mw"),
        ("bv",  "bw"),
        ("fv",  "fw"),
        ("pv",  "pw"),
        ("nv",  "nw"),
        ("dz",  "z"),
        # nh → ng: Tonga/Lozi variant (e.g. Nhliziyo → Ngliziyo)
        ("nh",  "ng"),
        # nj → ng: Nyanja/Tonga variant (e.g. Njovu → Ngovu, elephant)
        ("nj",  "ng"),
    ]

    _SPELLING_VARIANTS = [
        # ph → f: very common in Nyanja names (Phiri → firi)
        ("ph", "f"),
        # ck → k
        ("ck", "k"),
        # gh → g
        ("gh", "g"),
    ]

    _DOUBLE_VOWEL = [
        ("aa", "a"),
        ("ee", "e"),
        ("oo", "o"),
        ("uu", "u"),
        ("ii", "i"),
    ]

    # Bantu prefixes to strip (ordered longest → shortest)
    _PREFIXES = [
        "chi", "mwa", "mwe", "ngo", "nda", "nde",
        "wa", "ka", "mu", "ba", "ma", "bu", "lu",
        "tu", "ku", "pa", "ha",
    ]

    def __init__(self, rules_path: str = None, strip_prefixes: bool = False):
        """
        Args:
            rules_path: Optional path to rules.json (for documentation).
                        Programmatic rules above take precedence.
            strip_prefixes: If True, attempt to strip Bantu prefixes to
                            reduce names to root form. Disabled by default
                            because prefix-stripping on short names
                            (< 5 chars) produces false root collisions.
        """
        self.strip_prefixes = strip_prefixes
        self._prefix_min_length = 5  # Never strip from names shorter than this

        if rules_path:
            with open(rules_path) as f:
                self._rules_doc = json.load(f)

    def normalise(self, name: str) -> str:
        """
        Apply full normalisation pipeline to a single name string.

        Args:
            name: Raw name string (any case, may contain apostrophes,
                  hyphens, accented characters)

        Returns:
            Normalised canonical string (lowercase, ASCII-safe)

        Example:
            >>> n = BantuNormaliser()
            >>> n.normalise("Ng'andu")
            'ngandu'
            >>> n.normalise("Mvamba")
            'mwamba'
            >>> n.normalise("Moono")
            'mono'
        """
        if not name or not isinstance(name, str):
            return ""

        # Step 1: Unicode normalisation → ASCII-safe lowercase
        s = unicodedata.normalize("NFKD", name)
        s = s.encode("ascii", "ignore").decode("ascii")
        s = s.lower().strip()

        # Step 2: Apostrophe and tonal marker removal
        for pattern, replacement in self._APOSTROPHE_RULES:
            s = re.sub(pattern, replacement, s)

        # Step 3: Double-vowel reduction
        for double, single in self._DOUBLE_VOWEL:
            s = s.replace(double, single)

        # Step 4: Consonant equivalence substitution
        for variant, canonical in self._CONSONANT_EQUIVALENCES:
            s = s.replace(variant, canonical)

        # Step 5: Common spelling variants
        for variant, canonical in self._SPELLING_VARIANTS:
            s = s.replace(variant, canonical)

        # Step 6: Optional Bantu prefix stripping
        if self.strip_prefixes and len(s) >= self._prefix_min_length:
            for prefix in self._PREFIXES:
                if s.startswith(prefix) and len(s) - len(prefix) >= 3:
                    s = s[len(prefix):]
                    break  # Strip at most one prefix

        # Step 7: Whitespace/hyphen normalisation
        s = re.sub(r"[-_]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()

        return s

    def normalise_fullname(self, fullname: str) -> str:
        """
        Normalise a full name (may include multiple tokens).
        Each token is normalised independently then rejoined.

        Example:
            >>> n.normalise_fullname("Ng'andu Mvamba")
            'ngandu mwamba'
        """
        tokens = fullname.strip().split()
        return " ".join(self.normalise(t) for t in tokens)

    def similarity(self, name_a: str, name_b: str) -> float:
        """
        Compute Jaro-Winkler similarity between two names after
        applying full Bantu normalisation to both.

        This is the primary metric used by demographic_scorer.py.

        Returns:
            float in [0.0, 1.0] — higher is more similar

        Objective (from proposal):
            Jaro-Winkler for "Ng'andu" vs "Ngandu" rises from
            ≤0.82 (raw) to ≥0.95 (after normalisation).
        """
        norm_a = self.normalise(name_a)
        norm_b = self.normalise(name_b)
        return jellyfish.jaro_winkler_similarity(norm_a, norm_b)

    def similarity_raw(self, name_a: str, name_b: str) -> float:
        """
        Compute Jaro-Winkler WITHOUT normalisation.
        Used for baseline comparison and ablation study.
        """
        a = name_a.lower().strip() if name_a else ""
        b = name_b.lower().strip() if name_b else ""
        return jellyfish.jaro_winkler_similarity(a, b)

    def explain(self, name: str) -> dict:
        """
        Return step-by-step transformation trace for XAI dashboard.

        Returns:
            dict with keys: original, after_apostrophe, after_vowel,
                           after_consonant, after_spelling, final
        """
        if not name or not isinstance(name, str):
            return {"original": name, "final": ""}

        s = unicodedata.normalize("NFKD", name)
        s = s.encode("ascii", "ignore").decode("ascii").lower().strip()
        trace = {"original": name, "step_0_lowercase": s}

        for pattern, replacement in self._APOSTROPHE_RULES:
            s = re.sub(pattern, replacement, s)
        trace["step_1_apostrophe"] = s

        for double, single in self._DOUBLE_VOWEL:
            s = s.replace(double, single)
        trace["step_2_vowel"] = s

        for variant, canonical in self._CONSONANT_EQUIVALENCES:
            s = s.replace(variant, canonical)
        trace["step_3_consonant"] = s

        for variant, canonical in self._SPELLING_VARIANTS:
            s = s.replace(variant, canonical)
        trace["step_4_spelling"] = s

        trace["final"] = s
        return trace


# ---------------------------------------------------------------------------
# Module-level convenience functions (for import without instantiation)
# ---------------------------------------------------------------------------

_default_normaliser = BantuNormaliser()


def normalise(name: str) -> str:
    """Convenience wrapper around BantuNormaliser().normalise()."""
    return _default_normaliser.normalise(name)


def similarity(name_a: str, name_b: str) -> float:
    """Convenience wrapper — normalised Jaro-Winkler similarity."""
    return _default_normaliser.similarity(name_a, name_b)


if __name__ == "__main__":
    # Quick smoke test when run directly
    n = BantuNormaliser()
    tests = [
        ("Ng'andu", "Ngandu"),
        ("Mvamba",  "Mwamba"),
        ("Phiri",   "Firi"),
        ("Moono",   "Mono"),
        ("Ng'ombe", "Ngombe"),
        ("Kalumba", "Lumba"),
        ("Bwalya",  "Bvalya"),
        ("Njovu",   "Ngovu"),
    ]
    print(f"{'Name A':<15} {'Name B':<15} {'Raw JW':>8} {'Norm JW':>9}")
    print("-" * 52)
    for a, b in tests:
        raw  = n.similarity_raw(a, b)
        norm = n.similarity(a, b)
        flag = "✓" if norm >= 0.95 else ("~" if norm >= 0.85 else "✗")
        print(f"{a:<15} {b:<15} {raw:>8.4f} {norm:>8.4f} {flag}")
