# Intelligent Identity Deduplication Framework
### National Registration System — University of Zambia Final Year Project 2026

> **Nathan Sachitembe · 2022090446 · Department of Computing and Informatics**  
> Supervisor: Mr. Martin Phiri · Academic Year 2026

---

## Overview

Zambia's National Registration Card (NRC) system assigns every citizen aged 16 and above a unique identity number used across government, financial, and electoral systems. The recent introduction of the Integrated National Registration Information System (INRIS) has surfaced a persistent and nationally consequential problem — **duplicate identity records** — that existing systems are insufficiently equipped to detect, prevent, or correct.

This project proposes and implements an **Intelligent Identity Deduplication Framework** that addresses four taxonomically distinct duplicate types through a hybrid AI pipeline combining dual-channel blocking, Zambian Bantu language phonetic normalisation, quality-adaptive biometric fusion, a post-issuance batch audit scanner, and an explainable administrator resolution interface.

---

## The Five Duplicate Types Addressed

| Type | Description | Detection Mechanism |
|------|-------------|---------------------|
| **Type 1** | Same person — typographic name variants across registrations | Channel A: LSH + Bantu normalisation |
| **Type 2** | Same person — completely different identity (biometric fraud) | Channel B: FAISS + FaceNet |
| **Type 3** | Same person — date of birth transposition errors | Channel A: Jaro-Winkler demographic scoring |
| **Type 4** | Two different people — same NRC number assigned | Batch audit scanner (post-issuance) |
| **Type 5** | Same person — concurrent submission from two offline terminals | Slot-ID conflict handler |
| ~~Ghost~~ | ~~Fictitious persons created by corrupt officers~~ | ~~Future work — requires anomaly detection~~ |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  TIER 1 — Registration Terminals (District Offices)      │
│  Lusaka · Kitwe · Ndola                                  │
│  SQLite local cache · Slot-ID · Exponential backoff sync │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTPS · TLS 1.3
┌───────────────────▼─────────────────────────────────────┐
│  TIER 2 — Central Server (NRPCA Headquarters)            │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Deduplication Engine                           │    │
│  │                                                 │    │
│  │  Step 0: Biometric quality assessment (OpenCV)  │    │
│  │                                                 │    │
│  │  Channel A              Channel B               │    │
│  │  Bantu normalisation    FaceNet encoder          │    │
│  │  LSH/MinHash blocking   FAISS ANN index          │    │
│  │  Jaro-Winkler scoring   Cosine similarity        │    │
│  │           │                    │                │    │
│  │           └────────┬───────────┘                │    │
│  │               Candidate union                   │    │
│  │           Quality-adaptive fusion               │    │
│  │     w_bio = 0.4 + (0.3 × q) · composite score  │    │
│  │           Decision: Clear / Review / Block      │    │
│  │                                                 │    │
│  │  [NEW] Batch Audit Scanner (Type 4)             │    │
│  │  SQL GROUP BY nrc_number → biometric scorer     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  PostgreSQL + pgvector · XAI Admin Dashboard            │
└───────────────────┬─────────────────────────────────────┘
                    │ OAuth 2.0
┌───────────────────▼─────────────────────────────────────┐
│  TIER 3 — Interoperability Layer (Verification API)      │
│  ECZ · Banks/KYC · Social Welfare · ZICTA/NHIMA         │
└─────────────────────────────────────────────────────────┘
```

---

## Project Aim

> To design, implement, and evaluate a prototype Intelligent Identity Deduplication Framework that detects, prevents, and assists in correcting duplicate citizen identity records in Zambia's National Registration System — achieving an overall **F1-score of ≥ 0.85** on a structured synthetic dataset of 1,000 Zambian citizen records containing 50 ground-truth duplicate pairs across five taxonomically distinct duplicate types, within a **17-week development timeline**.

---

## Success Measures

| Layer | Metric | Target |
|-------|--------|--------|
| Blocking | LSH recall (Channel A) | ≥ 95% |
| Blocking | FAISS recall (Channel B) | ≥ 90% |
| Blocking | Combined union recall | ≥ 97% |
| Detection | Overall F1-score | ≥ 0.85 |
| Detection | Type 2 recall (biometric fraud) | ≥ 85% |
| Detection | Type 4 precision (batch scanner) | ≥ 90% |
| Detection | Type 5 detection (slot-ID) | 100% |
| Baseline | F1 gain over exact-match baseline | ≥ +0.40 |
| Baseline | F1 gain over demographic-only baseline | ≥ +0.15 |
| Original contribution | Bantu normalisation Jaro-Winkler improvement | ≥ +0.10 |
| Performance | Registration-time pipeline latency | < 2 seconds/record |
| Performance | Batch scanner latency (1,000 records) | < 30 seconds |

---

## Original Academic Contribution

> **Zambian Bantu Phonetic Normalisation** — No published work has addressed phonetic normalisation specifically for Zambian Bantu language names in the context of identity deduplication. This module addresses three failure modes of standard algorithms on Zambian data:
>
> - **Apostrophe tonal markers** — Ng'andu → Ngandu (Jaro-Winkler rises from ≤ 0.82 to ≥ 0.95)
> - **Bantu name prefixes** — Mwale / Wale inconsistency across registration terminals
> - **Dialect consonant equivalences** — Mwamba / Mvamba across Bemba, Nyanja, Tonga, Luvale

---

## Development Methodology

This project follows the **Unified Process (UP)** — an iterative, risk-driven, use-case-driven methodology. The highest architectural risk (FaceNet biometric recall on synthetic images) is resolved on **Day 1 of Elaboration** before any full construction begins.

| UP Phase | Weeks | Key Output |
|----------|-------|------------|
| **Inception** | 1–2 | Proposal, use case model, architecture vision, risk register |
| **Elaboration** | 3–7 | FAISS PoC, LSH PoC, D5 dataset, D1 terminals |
| **Construction** | 8–13 | D2 engine, D3 dashboard, D4 Bantu module, D6 evaluation, D7 scanner |
| **Transition** | 14–16 | Final report, user guide, demo video, submission |

---

## Project Structure

```
Intelligent_Identity_Deduplication_Framework_For_National_Registration_System/
│
├── poc/                          # Elaboration phase proof-of-concepts
│   ├── faiss_poc.ipynb           # KILL RISK — run Day 1 Week 3
│   ├── lsh_poc.ipynb             # LSH recall on Zambian name variants
│   ├── bantu_poc.ipynb           # Jaro-Winkler before/after normalisation
│   └── poc_results.md            # PoC findings documented for report
│
├── tier1_terminals/              # Registration terminal app
│   ├── app.py
│   ├── slot_id.py
│   ├── local_db.py
│   ├── sync_worker.py
│   └── conflict_handler.py       # Type 5 alert routing
│
├── tier2_central/                # Central server — deduplication engine
│   ├── api_gateway/
│   ├── deduplication_engine/
│   │   ├── pipeline.py           # Steps 0–4 orchestration
│   │   ├── quality_assessment.py
│   │   ├── channel_a_lsh.py
│   │   ├── channel_b_faiss.py
│   │   ├── facenet_encoder.py
│   │   ├── demographic_scorer.py
│   │   ├── biometric_scorer.py
│   │   ├── fusion.py
│   │   ├── decision.py
│   │   └── xai_payload.py
│   ├── bantu_normalisation/      # Original contribution — standalone module
│   │   ├── normaliser.py
│   │   ├── rules.json
│   │   └── test_normaliser.py
│   ├── batch_audit_scanner/      # [NEW] Type 4 post-issuance detection
│   │   ├── scanner.py
│   │   └── test_scanner.py
│   ├── database/
│   └── admin_dashboard/
│
├── tier3_api/                    # Interoperability stub
│
├── dataset/                      # Synthetic evaluation dataset (D5)
│   ├── duplicate_injector.py
│   ├── zambian_names.csv
│   ├── citizens_1000.csv
│   └── ground_truth.csv
│
├── evaluation/                   # Baselines and metrics (D6)
│   ├── baseline_a.py
│   ├── baseline_b.py
│   ├── evaluate_framework.py
│   └── results/
│
├── tests/                        # Unit and integration tests
├── docs/                         # All project documentation
│
├── config.json                   # Runtime-configurable thresholds
├── start.sh                      # Starts all services natively
├── requirements.txt
└── README.md
```

---

## Technology Stack

| Category | Technology | Reason |
|----------|------------|--------|
| Language | Python 3.11 | ML/AI ecosystem |
| Framework | Flask | Lightweight REST API |
| Face Embeddings | FaceNet (pre-trained) | 128-dim, proven generalisation |
| ANN Index | FAISS CPU | Sub-second retrieval at prototype scale |
| LSH Blocking | datasketch | MinHash LSH, configurable parameters |
| Demographic Similarity | jellyfish | Jaro-Winkler implementation |
| Name Normalisation | Custom Python module | Original contribution — no library exists |
| Image Quality | OpenCV | Laplacian variance for blur detection |
| Primary Database | PostgreSQL 15 + pgvector | ACID + vector storage |
| Edge Database | SQLite | Offline terminal local storage |
| Deep Learning | TensorFlow-CPU | GPU-optional, FaceNet compatible |

---

## Deliverables

| ID | Deliverable | Due |
|----|-------------|-----|
| D1 | Three simulated offline registration terminals | Wk 7 |
| D2 | Full dual-channel deduplication engine | Wk 10 |
| D3 | XAI administrator dashboard | Wk 11 |
| D4 | Bantu phonetic normalisation module (original contribution) | Wk 8 |
| D5 | Synthetic evaluation dataset — 1,000 records, 50 pairs, 5 types | Wk 5 |
| D6 | Evaluation report — confusion matrices, per-type F1, baseline comparison | Wk 14 |
| D7 | Post-issuance batch audit scanner | Wk 11 |
| D8 | Tier 3 verification API stub | Wk 11 |

---

## Scope Boundaries

**In scope:** Types 1–5 duplicate detection · Dual-channel blocking · Bantu normalisation · Quality-adaptive fusion · Batch audit scanner · XAI dashboard · Synthetic evaluation · Tier 3 stub

**Out of scope:** Live NRPCA deployment · Fingerprint biometrics · Real citizen data · Production security hardening · Ghost identity detection *(future work — requires registration behaviour anomaly detection, not record collision detection)*

---

## docs/ Index

| Document | Purpose | UP Phase |
|----------|---------|----------|
| [Use Case Model](docs/use_case_model.md) | Actors and primary use cases | Inception |
| [Architecture Vision](docs/architecture_vision.md) | Three-tier system overview and tech stack | Inception |
| [Risk Register](docs/risk_register.md) | Ranked risks with kill-risk identification | Inception |
| [PoC Results](poc/poc_results.md) | FAISS and LSH proof-of-concept findings | Elaboration |
| [Database Schema](docs/database_schema.md) | PostgreSQL schema design | Elaboration |
| [Bantu Normalisation Rules](docs/bantu_rules.md) | All normalisation rules documented | Elaboration |

---

## Getting Started (Development Environment)

```bash
# 1. Clone the repository
git clone https://github.com/nathansachitembe/Intelligent_Identity_Deduplication_Framework_For_National_Registration_System.git
cd Intelligent_Identity_Deduplication_Framework_For_National_Registration_System

# 2. Create virtual environment (Ubuntu)
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies (install heavy packages first)
pip install numpy
pip install tensorflow-cpu
pip install facenet-pytorch
pip install faiss-cpu
pip install opencv-python-headless
pip install flask sqlalchemy psycopg2-binary pgvector
pip install datasketch jellyfish faker scikit-learn requests python-dotenv jupyter

# 4. Set up PostgreSQL (Ubuntu native — no Docker needed on 4GB RAM)
sudo systemctl start postgresql
# See docs/database_schema.md for schema setup

# 5. Start all services
chmod +x start.sh
./start.sh

# Services available at:
# localhost:5000 — Admin dashboard
# localhost:5001 — Lusaka terminal
# localhost:5002 — Kitwe terminal
# localhost:5003 — Ndola terminal
# localhost:5004 — Tier 3 API
```

> **Hardware note:** Developed on Ubuntu 22.04, Core i3, 4GB RAM. Add 4GB swap (`sudo fallocate -l 4G /swapfile`) and set swappiness to 10 before running. Use `tensorflow-cpu` — GPU not required.

---

## Current Status


| Component | Status | Details |
|---|---|---|
| **Inception** | ✅ Complete | Proposal, use case model, architecture vision, risk register, supervisor sign-off |
| **Elaboration — Documentation** | ✅ Complete | Database schema, Bantu rules, PoC results template, Elaboration Iteration Plan |
| **Elaboration — Bantu Normaliser (D4)** | ✅ Complete | normaliser.py, rules.json, 30 unit tests passing, 50 held-out pairs ALL PASS |
| **Elaboration — Dataset D5** | ✅ Complete | 990 records, 50 ground-truth pairs, all 5 duplicate types, seed=42 deterministic |
| **Elaboration — Baselines** | ✅ Complete | Baseline A: F1=0.8889, Baseline B: F1=0.2524 — both verified |
| **Elaboration — FAISS PoC** | 🔴 Kill risk — must run next | faiss_poc.ipynb — 20 face pairs through FaceNet, cosine similarity check |
| **Elaboration — LSH PoC** | ⏳ Pending | lsh_poc.ipynb — 100-record index, recall >= 95% on Zambian variants |
| **Elaboration — PostgreSQL** | ⏳ Pending | nrc_db setup, pgvector extension, schema initialisation |
| **Elaboration — Terminals D1** | ⏳ Pending | Three Flask terminals, SQLite, slot-ID, sync worker |
| **Construction** | ⏳ Pending — starts Week 8 | Requires all Elaboration gates cleared |
| **Transition** | ⏳ Pending | Weeks 14–16 |
---

## References

1. P. Christen, *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection.* Berlin: Springer, 2012.
2. P. Indyk and R. Motwani, "Approximate nearest neighbors," *Proc. 30th ACM STOC*, 1998.
3. J. Li and H. Wang, "Efficient identity matching using static pruning q-gram indexing," *Decision Support Systems*, 2015.
4. K. Mala and S. Chinnadurai, "Efficient record de-duplication using FEBRL," *IOSR J. Computer Engineering*, 2013.
5. F. Oladipo et al., "Use of biometrics for records deduplication: Nigeria national data repository," *Online J. Public Health Informatics*, 2025.
6. M. A. Ribeiro, S. Singh, C. Guestrin, "'Why should I trust you?'", *Proc. 22nd ACM SIGKDD*, 2016.
7. F. Schroff, D. Kalenichenko, J. Philbin, "FaceNet," *Proc. IEEE CVPR*, 2015.
8. S. Surana et al., "Deduplication of identities using scalable vector databases," *arXiv*, 2024.
9. United Nations, *2030 Agenda for Sustainable Development*, A/RES/70/1, 2015.
10. W. E. Winkler, "String comparator metrics," *Proc. ASA Survey Research Methods*, 1990.
11. X. Zhang et al., "Siamese neural networks for privacy-preserving record linkage," *J. Information Security and Applications*, 2023.

---

*University of Zambia · School of Natural and Applied Sciences · Department of Computing and Informatics · 2026*
