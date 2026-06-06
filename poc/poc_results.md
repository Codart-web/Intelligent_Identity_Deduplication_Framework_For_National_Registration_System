# Proof-of-Concept Results
## Intelligent Identity Deduplication Framework — National Registration System
**Nathan Sachitembe · 2022090446 · UP Elaboration Phase · Week 3**

> This document is completed during Elaboration, not Inception. It is created as a template during Inception so it is ready to fill in on Day 1 of Week 3. The PoC results recorded here become evidence in the methodology chapter of the final report that UP's risk-driven approach was followed correctly.

---

## PoC 1 — FAISS Biometric Recall (Kill Risk)
**Notebook:** `poc/faiss_poc.ipynb`
**Date run:** __________________
**Week:** 3, Day 1

### Experiment Setup

| Parameter | Value |
|-----------|-------|
| FaceNet model | InceptionResnetV1 pretrained='vggface2' |
| Embedding dimensions | 512 |
| Test pairs — same person | 10 |
| Test pairs — different person | 10 |
| Face image source | Procedurally generated synthetic images (160x160 RGB) |
| FAISS index type | IndexFlatIP (inner product on L2-normalised vectors) |

### Results

**Same-person pairs:**

| Pair | Person Seed | Variation | Cosine Similarity | Pass (≥ 0.80)? |
|------|-------------|-----------|-------------------|----------------|
| 1 | 328 | 1 | 0.5557 | ✗ |
| 2 | 58 | 2 | 0.8815 | ✓ |
| 3 | 13 | 3 | 0.7827 | ✗ |
| 4 | 380 | 4 | 0.7167 | ✗ |
| 5 | 141 | 5 | 0.7473 | ✗ |
| 6 | 126 | 6 | 0.7368 | ✗ |
| 7 | 115 | 7 | 0.9082 | ✓ |
| 8 | 72 | 8 | 0.6484 | ✗ |
| 9 | 378 | 9 | 0.7110 | ✗ |
| 10 | 53 | 10 | 0.9200 | ✓ |
| **Average** | | | **0.7608** | **FAIL** |

**Different-person pairs:**

| Pair | Seed A | Seed B | Cosine Similarity | Pass (≤ 0.40)? |
|------|--------|--------|-------------------|----------------|
| 1 | 674 | 806 | 0.7993 | ✗ |
| 2 | 690 | 810 | 0.8250 | ✗ |
| 3 | 729 | 880 | 0.6920 | ✗ |
| 4 | 640 | 905 | 0.7496 | ✗ |
| 5 | 523 | 757 | 0.7131 | ✗ |
| 6 | 652 | 894 | 0.8914 | ✗ |
| 7 | 609 | 801 | 0.8042 | ✗ |
| 8 | 509 | 934 | 0.8676 | ✗ |
| 9 | 508 | 917 | 0.8437 | ✗ |
| 10 | 524 | 930 | 0.6202 | ✗ |
| **Average** | | | **0.7806** | **FAIL** |

### Verdict

| Criterion | Target | Actual | Pass/Fail |
|-----------|--------|--------|-----------|
| Same-person cosine average | ≥ 0.80 | 0.7608 | ✗ FAIL |
| Different-person cosine average | ≤ 0.40 | 0.7806 | ✗ FAIL |
| Separation gap | ≥ 0.40 | -0.0198 | ✗ FAIL |
| FAISS recall @ top-3 | ≥ 0.90 | 0.20 | ✗ FAIL |

**Overall PoC 1 Result:** [x] FAIL — Fallback activated

**If FAIL — Action taken:**
```
Procedurally generated synthetic images (geometric shapes) do not contain
sufficient facial geometry for FaceNet to produce separable embeddings.
Same-person and different-person cosine similarities were indistinguishable
(0.7608 vs 0.7806, gap = -0.02). Fallback activated per Elaboration
Iteration Plan Section 3.2: switching to Labeled Faces in the Wild (LFW)
dataset which provides real photographic face images. Architecture is
unchanged — only the image source changes. Kill risk remains open pending
rerun with LFW data.
```

**Risk Register Update:** RISK 01 status changed to [x] ⚠️ FALLBACK ACTIVATED

**Date:** 2026-06-05
**Rerun scheduled:** Immediately — faiss_poc_v2.ipynb with LFW embeddings

---

## PoC 2 — LSH Demographic Blocking Recall
**Notebook:** `poc/lsh_poc.ipynb`
**Date run:** __________________
**Week:** 3, Day 2–3

### Experiment Setup

| Parameter | Value |
|-----------|-------|
| datasketch version | __________ |
| Initial num_perm | 128 |
| Initial threshold | 0.5 |
| Shingle type | Trigram (3-character) |
| Normalisation applied before shinging | Yes / No |
| Index size | 100 records |
| Test variant pairs | 20 |

### Tuning Iterations

| Iteration | num_perm | threshold | Recall | Notes |
|-----------|----------|-----------|--------|-------|
| 1 | 128 | 0.5 | | Initial run |
| 2 | | | | |
| 3 | | | | |
| Final | | | | |

### Results — Final Parameters

| Criterion | Target | Actual | Pass/Fail |
|-----------|--------|--------|-----------|
| Blocking recall on variant pairs | ≥ 95% | __________% | |
| False positive rate (candidates per query) | Acceptable | __________ | |

**Final LSH Parameters chosen:**
- `num_perm` = __________
- `threshold` = __________

**Overall PoC 2 Result:** [ ] PASS — RISK 02 CLOSED &nbsp;&nbsp;&nbsp; [ ] FAIL — Fallback activated

**Risk Register Update:** RISK 02 status changed to [ ] ✅ CLOSED / [ ] ⚠️ FALLBACK ACTIVATED

---

## PoC 3 — Bantu Normalisation Effectiveness
**Notebook:** `poc/bantu_poc.ipynb`
**Date run:** __________________
**Week:** 4

### Acceptance Criterion
Jaro-Winkler similarity for Ng'andu vs Ngandu must rise from ≤ 0.82 (without normalisation) to ≥ 0.95 (after normalisation).

### Key Test Pairs Results

| Pair | Raw JW Score | Normalised JW Score | Improvement | Pass? |
|------|-------------|---------------------|-------------|-------|
| Ng'andu / Ngandu | | | | |
| Mwamba / Mvamba | | | | |
| Mwale / Wale | | | | |
| Ng'ona / Ngona | | | | |
| Chibwe / Thibwe | | | | |

### Held-out Validation Set (50 pairs)

| Metric | Value |
|--------|-------|
| Pairs with JW improvement > 0.10 | __ / 50 |
| Average JW improvement | __________ |
| False positives (genuinely different names incorrectly raised > 0.85) | __ / 20 |

**Overall PoC 3 Result:** [ ] PASS — RISK 03 CLOSED &nbsp;&nbsp;&nbsp; [ ] FAIL — Rules adjusted

**Rules requiring modification:**
```
____________________________________________________________
____________________________________________________________
```

**Risk Register Update:** RISK 03 status changed to [ ] ✅ CLOSED / [ ] ⚠️ FALLBACK ACTIVATED

---

## PoC 4 — Environment Setup Verification
**Date:** __________________
**Week:** 3

### Checklist

| Item | Status | Notes |
|------|--------|-------|
| Python 3.11 installed | [ ] ✅ / [ ] ❌ | |
| venv created and activated | [ ] ✅ / [ ] ❌ | |
| tensorflow-cpu installed | [ ] ✅ / [ ] ❌ | |
| facenet-pytorch installed | [ ] ✅ / [ ] ❌ | |
| faiss-cpu installed | [ ] ✅ / [ ] ❌ | |
| datasketch installed | [ ] ✅ / [ ] ❌ | |
| jellyfish installed | [ ] ✅ / [ ] ❌ | |
| opencv-python-headless installed | [ ] ✅ / [ ] ❌ | |
| PostgreSQL 15 running | [ ] ✅ / [ ] ❌ | |
| pgvector compiled and installed | [ ] ✅ / [ ] ❌ | |
| nrc_db database created | [ ] ✅ / [ ] ❌ | |
| vector extension enabled | [ ] ✅ / [ ] ❌ | |
| 4GB swap file active | [ ] ✅ / [ ] ❌ | |
| swappiness set to 10 | [ ] ✅ / [ ] ❌ | |
| VS Code + Jupyter extension installed | [ ] ✅ / [ ] ❌ | |
| GitHub repo cloned to ~/... | [ ] ✅ / [ ] ❌ | |
| First commit pushed | [ ] ✅ / [ ] ❌ | |

**pgvector installation method used:**
```
[ ] Compiled from source (preferred)
[ ] Fallback: FLOAT[] array in PostgreSQL
[ ] Fallback: NumPy .npy files on disk
```

**RISK 08 status:** [ ] ✅ CLOSED / [ ] ⚠️ FALLBACK ACTIVATED

---

## Summary — Elaboration Entry Gate

All items below must be confirmed before Construction begins:

| Gate | Criterion | Status |
|------|-----------|--------|
| G1 | FAISS PoC — fallback activated, rerun with LFW pending | ⚠️ FALLBACK |
| G2 | LSH PoC passed — blocking recall ≥ 95% on variant sample | [ ] PASS / [ ] FALLBACK |
| G3 | Bantu PoC passed — Ng'andu/Ngandu score rises to ≥ 0.95 | [ ] PASS / [ ] FALLBACK |
| G4 | Environment fully set up including pgvector | [ ] DONE |
| G5 | D5 dataset generated with all five types | [ ] DONE |
| G6 | D1 terminals syncing to central server | [ ] DONE |
| G7 | Literature review chapter drafted | [ ] DONE |

**Elaboration exit confirmed:** __________________ (date)

---

*Document version: 1.0 · Template created Inception Week 2 · To be completed Elaboration Week 3–7*
