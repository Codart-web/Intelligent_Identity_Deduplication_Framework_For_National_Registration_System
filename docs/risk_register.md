# Risk Register
## Intelligent Identity Deduplication Framework — National Registration System
**Nathan Sachitembe · 2022090446 · UP Inception Phase · Week 2**

---

## 1. Purpose

This document identifies, assesses, and prioritises all known project risks. In the Unified Process (UP), the risk register drives the Elaboration phase schedule — the highest-priority architectural risks are resolved first through proof-of-concept experiments before any full construction begins. A risk that is not resolved in Elaboration will surface in Construction when recovery is costly.

This register is a living document. Every PoC result in Elaboration must update the status column of the relevant risk.

---

## 2. Risk Assessment Criteria

**Likelihood:**
- **High** — Will probably occur if not actively mitigated
- **Medium** — May occur; mitigation reduces probability significantly
- **Low** — Unlikely; mitigation is straightforward

**Impact:**
- **High** — Could prevent the project from meeting its primary SMART metric (F1 ≥ 0.85) or completing on time
- **Medium** — Causes degraded performance or additional recovery work; project still completable
- **Low** — Minor inconvenience; easily absorbed

**Kill Risk:** A risk that, if unresolved, makes the project undeliverable as specified. Kill risks are resolved before any other Elaboration work.

---

## 3. Risk Register

### RISK 01 — FaceNet recall on real facial images (LFW)
**Kill Risk: YES**
**Status: ✅ CLOSED (2026-06-25)** — See poc_results.md for full BR-FAISS-001/002 results.

| Field | Detail |
|-------|--------|
| **Category** | Architectural / Technical |
| **Description** | FaceNet pre-trained weights were trained on real photographic face datasets. Synthetic face images (generated or from permissively licensed synthetic datasets) may not produce well-separated embedding spaces — same-person cosine similarity may not exceed different-person cosine similarity sufficiently for reliable matching. If Channel B cannot achieve ≥ 90% biometric blocking recall on Type 2 pairs, the dual-channel architecture's core value proposition collapses. Type 2 (biometric fraud — same face, different identity) becomes undetectable, dragging overall F1 below 0.85. |
| **Likelihood** | Medium |
| **Impact** | High |
| **Priority** | 1 — Resolve first, Day 1 of Week 3 |
| **Mitigation** | Use genuine synthetic face images run through the actual FaceNet model — not random vectors. Source from permissively licensed datasets (e.g., 100K Faces, FFHQ subset with permissive licence) if generated images produce poor separation. Augment with noise, blur, and lighting variation to simulate field capture conditions. |
| **Fallback** | If biometric F1 < 0.70 after augmentation: revert to demographic-only deduplication with honest documentation. Reframe as a finding: "biometric matching on synthetic images is insufficient for field deployment without real biometric capture data." This is academically valid. |
| **Proof of Concept** | `poc/faiss_poc.ipynb` — feed 20 image pairs (10 same-person, 10 different-person) through FaceNet. Same-person cosine avg must be ≥ 0.80. Different-person cosine avg must be ≤ 0.40. Clear separation required. |
| **Resolution Week** | Week 3, Day 1 |
| **Status** | ⏳ OPEN — resolve in Elaboration |
| **Owner** | Nathan Sachitembe |

---

### RISK 02 — LSH blocking recall on Zambian name corpus
**Kill Risk: NO** (but high impact on Type 1 detection)

| Field | Detail |
|-------|--------|
| **Category** | Architectural / Technical |
| **Description** | MinHash LSH blocking recall depends on the similarity distribution of the name corpus and the band/row configuration chosen. Zambian Bantu names with their specific character distributions (apostrophes, prefix patterns, short names) may produce trigram shingle sets with different characteristics than the corpora datasketch was tuned for. If LSH recall is below 95% on Type 1 pairs, some genuine duplicates escape the blocking stage entirely and can never be detected — regardless of how good the scoring and fusion logic is. |
| **Likelihood** | Low |
| **Impact** | High |
| **Priority** | 2 — Resolve Week 3, Day 2–3 |
| **Mitigation** | Run LSH PoC on a 100-record sample of Zambian names before building the full pipeline. Tune `num_perm` and `threshold` parameters on the validation set. Apply Bantu normalisation before shingle generation — normalised names are closer in character space and produce higher recall naturally. |
| **Fallback** | If recall remains below 95% after tuning: lower the LSH threshold (accept more false positive candidates at the blocking stage — this increases review burden but improves recall). The scoring stage then filters false positive candidates. |
| **Proof of Concept** | `poc/lsh_poc.ipynb` — build index on 100 Zambian name records; query with 20 known variant pairs; measure recall; tune parameters until ≥ 95% achieved. |
| **Resolution Week** | Week 3, Day 2–3 |
| **Status** | ⏳ OPEN — resolve in Elaboration |
| **Owner** | Nathan Sachitembe |

---

### RISK 03 — Bantu normalisation false positives
**Kill Risk: NO** (impacts precisiAon)

| Field | Detail |
|-------|--------|
| **Category** | Technical / Algorithm |
| **Description** | Overly aggressive normalisation rules may treat genuinely different Zambian names as the same. For example, stripping the "Ka-" prefix to handle Mwale/Wale might incorrectly collapse a surname like "Kabwe" (which is a place name used as a surname and should not be stripped). False positives here inflate the candidate set and reduce precision, increasing administrator review burden and potentially causing erroneous merge decisions. |
| **Likelihood** | Medium |
| **Impact** | Medium |
| **Priority** | 3 — Resolve Week 4 |
| **Mitigation** | Document all normalisation rules explicitly in `rules.json` before coding. Test each rule against: (a) 50 held-out true variant pairs — must increase Jaro-Winkler similarity, (b) 20 genuinely different name pairs — must NOT increase Jaro-Winkler beyond 0.85. Rules are configurable at runtime — disable any rule that fails validation without code changes. |
| **Proof of Concept** | `poc/bantu_poc.ipynb` — Jaro-Winkler for Ng'andu vs Ngandu must rise from ≤ 0.82 to ≥ 0.95. Validated on 50 held-out pairs. No false-positive threshold violations. |
| **Resolution Week** | Week 4 |
| **Status** | ⏳ OPEN — resolve in Elaboration |
| **Owner** | Nathan Sachitembe |

---

### RISK 04 — Batch scanner false positives on Type 4 alerts
**Kill Risk: NO** (impacts Type 4 precision)

| Field | Detail |
|-------|--------|
| **Category** | Technical / Algorithm |
| **Description** | The batch scanner may incorrectly classify same-person clerical duplicates (who share an NRC number by error) as genuine identity collisions (two different people sharing an NRC number). Both scenarios result in a shared NRC number — the distinction is made by cosine similarity of their FaceNet embeddings. If the cosine threshold is set incorrectly, same-person pairs may be flagged as Type 4 (different-person collision) when they are actually standard duplicates. |
| **Likelihood** | Low |
| **Impact** | Medium |
| **Priority** | 4 — Resolve Week 10 during scanner implementation |
| **Mitigation** | Calibrate the cosine threshold on D5 Type 4 pairs specifically. Same-person pairs (high similarity, wrong NRC number) should score ≥ 0.55; different-person pairs (low similarity, NRC collision) should score < 0.55. The administrator always reviews before any action — no automated merge for Type 4 alerts. High precision target (≥ 90%) set specifically for this type. |
| **Resolution Week** | Week 10 |
| **Status** | ⏳ OPEN |
| **Owner** | Nathan Sachitembe |

---

### RISK 05 — Implementation scope overrun in 17 weeks
**Kill Risk: NO** (timeline risk)

| Field | Detail |
|-------|--------|
| **Category** | Project Management |
| **Description** | The system has nine objectives, eight deliverables, and five distinct duplicate type detection mechanisms across a 17-week timeline. Scope creep — particularly in the XAI dashboard UI or unexpected integration complexity — could cause Construction to overrun into Transition, leaving insufficient time for the evaluation chapter and final report. |
| **Likelihood** | Medium |
| **Impact** | Medium |
| **Priority** | Ongoing — monitored weekly |
| **Mitigation** | Enforce strict scope boundaries: (1) Dashboard must be functionally minimal — Flask + Jinja2 table views only, no JavaScript frameworks. (2) Batch scanner is ~40 lines — do not extend scope. (3) Tier 3 API is a documented stub — do not implement live integrations. (4) Weekly Friday check: if more than 3 days behind on any module, apply documented mitigation immediately. |
| **Fallback** | If dashboard UI takes too long: implement alert list as a plain HTML table with no styling. XAI fields are data already computed — display only. The academic contribution is the pipeline, not the UI. |
| **Resolution Week** | Ongoing |
| **Status** | ⏳ MONITORED |
| **Owner** | Nathan Sachitembe |

---

### RISK 06 — Synthetic dataset does not reflect real Zambian name variation
**Kill Risk: NO** (impacts evaluation validity)

| Field | Detail |
|-------|--------|
| **Category** | Data Quality |
| **Description** | The synthetic dataset is the sole evaluation ground truth. If the Zambian name corpus used in Faker is not representative of the actual distribution of names in the NRC database, the evaluation results may not generalise. Specifically, if too few apostrophe-containing names or Bantu prefix variants are included, the Bantu normalisation contribution may appear larger than it actually is on real data. |
| **Likelihood** | Medium |
| **Impact** | Medium |
| **Priority** | 5 — Address during dataset generation (Week 4–5) |
| **Mitigation** | Source Zambian name frequency data from: (1) University of Zambia linguistic resources, (2) publicly available census name distribution data, (3) published Zambian administrative datasets. Configure Faker with a custom `zambian_names.csv` that reflects actual name frequency distribution. Include at least 30% apostrophe-containing names and 40% names with common Bantu prefixes. |
| **Resolution Week** | Week 4–5 (dataset generation) |
| **Status** | ⏳ OPEN |
| **Owner** | Nathan Sachitembe |

---

### RISK 07 — Computational resource limitations on development hardware
**Kill Risk: NO** (performance risk)

| Field | Detail |
|-------|--------|
| **Category** | Infrastructure |
| **Description** | Development hardware is a Dell Latitude 3350, Core i3, 4GB RAM running Ubuntu. TensorFlow-CPU + FaceNet model loading consumes approximately 600MB–1GB RAM. Running multiple Flask services simultaneously with FaceNet in memory may cause the system to swap to disk, significantly slowing the evaluation runs. |
| **Likelihood** | Medium |
| **Impact** | Low |
| **Priority** | 6 — Managed by architectural decisions already made |
| **Mitigation** | (1) 4GB swap file added to Ubuntu (`/swapfile`). (2) Swappiness reduced to 10. (3) FaceNet loaded as singleton — one load at startup, all requests reuse. (4) All 1,000 embeddings pre-computed and cached to `dataset/embeddings.npy` — FaceNet runs once, not per evaluation. (5) FAISS index built from cached embeddings and saved to `dataset/faiss.index`. (6) Services run natively (no Docker Desktop overhead). (7) Browser closed during heavy compute sessions. |
| **Resolution Week** | Week 3 (environment setup) |
| **Status** | ⏳ PARTIALLY MITIGATED — swap and swappiness configured; FaceNet singleton pattern to be implemented in Week 8 |
| **Owner** | Nathan Sachitembe |

---

### RISK 08 — pgvector installation failure on Ubuntu
**Kill Risk: NO** (can be worked around)

| Field | Detail |
|-------|--------|
| **Category** | Infrastructure |
| **Description** | pgvector requires compilation from source on Ubuntu and depends on postgresql-server-dev packages matching the PostgreSQL version exactly. Version mismatches between PostgreSQL 15 and server-dev packages may cause compilation failure. |
| **Likelihood** | Low |
| **Impact** | Medium |
| **Priority** | 7 — Verify during environment setup Week 3 |
| **Mitigation** | Follow installation in exact order: install PostgreSQL 15 first, then `postgresql-server-dev-15`, then clone pgvector and compile. If compilation fails: store embeddings as `FLOAT[]` array in PostgreSQL instead of `VECTOR(128)` type — cosine similarity computed in Python rather than SQL. |
| **Fallback** | Store embeddings as numpy arrays in `.npy` files on disk indexed by citizen_id. Load entire embedding matrix at startup — at 1,000 records this is 0.5MB, trivially fits in RAM. |
| **Resolution Week** | Week 3 |
| **Status** | ⏳ OPEN — verify during environment setup |
| **Owner** | Nathan Sachitembe |

---

### RISK 09 — Offline sync conflict test complexity
**Kill Risk: NO** (Type 5 detection)

| Field | Detail |
|-------|--------|
| **Category** | Technical / Testing |
| **Description** | Testing Type 5 (concurrent multi-terminal submission) requires two terminal processes to simultaneously submit the same slot-ID to the central server. In a native process environment without Docker, simulating genuine concurrency is harder — the second submission must arrive while the first is being processed. |
| **Likelihood** | Low |
| **Impact** | Medium |
| **Priority** | 8 — Address during D1 terminal testing Week 7 |
| **Mitigation** | Write a test script `tests/test_type5_conflict.py` that programmatically submits two identical slot-IDs to the central server within the same second using Python threading. Verify that the second submission receives a 409 response and a Type 5 alert appears in the duplicate_alerts table. |
| **Resolution Week** | Week 7 |
| **Status** | ⏳ OPEN |
| **Owner** | Nathan Sachitembe |

---

## 4. Risk Priority Summary

| Priority | Risk ID | Risk Name | Kill Risk | Resolution Week | Status |
|----------|---------|-----------|-----------|-----------------|--------|
| 1 | RISK 01 | FaceNet recall on real LFW images (dual-scenario validated) | **YES** | Week 3 Day 1 | ✅ CLOSED (2026-06-25) |
| 2 | RISK 02 | LSH recall on Zambian names | No | Week 3 Day 2–3 | ⏳ Open |
| 3 | RISK 03 | Bantu normalisation false positives | No | Week 4 | ⏳ Open |
| 4 | RISK 04 | Batch scanner false positives | No | Week 10 | ⏳ Open |
| 5 | RISK 05 | Scope overrun | No | Ongoing | ⏳ Monitored |
| 6 | RISK 06 | Dataset not representative | No | Week 4–5 | ⏳ Open |
| 7 | RISK 07 | Hardware resource limits | No | Week 3 | ⏳ Partial |
| 8 | RISK 08 | pgvector installation failure | No | Week 3 | ⏳ Open |
| 9 | RISK 09 | Type 5 concurrency test | No | Week 7 | ⏳ Open |

---

## 5. Risk Status Update Protocol

After each PoC experiment in Elaboration, update this register:

| Status | Meaning |
|--------|---------|
| ⏳ OPEN | Not yet resolved |
| ✅ CLOSED | Resolved — PoC passed, fallback not needed |
| ⚠️ FALLBACK ACTIVATED | Primary approach failed; fallback in use — document decision |
| 🔄 MONITORED | Ongoing management risk — reviewed weekly |

---

## 6. UP Elaboration — Risk-Driven Schedule

The following is the Day 1 Week 3 sequence. **Do not write literature review or generate data before these experiments complete.**

```
Week 3, Day 1 (Monday):
  → Open poc/faiss_poc.ipynb
  → Load FaceNet, prepare 20 synthetic face pairs
  → Run experiment, record cosine similarity values
  → RESULT: PASS under controlled high-enrollment scenario (BR-FAISS-002:
    same-person 0.8190, gap 0.7095). Robustness also confirmed under
    unconstrained benchmark (BR-FAISS-001: gap 0.6061). RISK 01 CLOSED.
Week 3, Day 2 (Tuesday):
  → Open poc/lsh_poc.ipynb
  → Build 100-record LSH index on Zambian name sample
  → Query with 20 variant pairs, measure recall
B  → Tune parameters until ≥ 95% or fallback activated
  → Record final parameters (num_perm, threshold) in poc_results.md

Week 3, Day 3–5:
  → Begin literature review (risk resolved — safe to document architecture)
  → Design PostgreSQL schema
  → Verify pgvector installation (RISK 08)
  → Add swap file, configure swappiness (RISK 07)
```

---

*Document version: 1.0 · Inception Phase · Week 2*  
*Next review: End of Week 3 — update all OPEN risks with PoC results*
