# Architecture Vision Document
## Intelligent Identity Deduplication Framework — National Registration System
**Nathan Sachitembe · 2022090446 · UP Inception Phase · Week 1**

---

## 1. Purpose

This document defines the architectural vision of the Intelligent Identity Deduplication Framework. In the Unified Process (UP), the architecture vision is produced during Inception to establish a shared understanding of the system's structure before any construction begins. It is a living document — updated at the end of each UP phase as the architecture is refined through proof-of-concept experiments.

---

## 2. Architectural Goals

The architecture is designed to satisfy four non-negotiable requirements derived directly from Zambia's national registration environment:

| Goal | Architectural Response |
|------|------------------------|
| **Offline-first operation** | Tier 1 terminals use SQLite local storage with a background sync worker — registration continues without network connectivity |
| **Dual-failure-mode detection** | Two independent blocking channels — Channel A (demographic) and Channel B (biometric) — each capable of catching duplicates the other cannot |
| **Variable biometric quality** | Quality-adaptive fusion dynamically adjusts biometric weight based on OpenCV Laplacian variance score — poor lighting does not cause false rejections |
| **Post-issuance auditability** | Batch audit scanner operates independently of the registration-time pipeline — finds shared NRC collisions already resident in the database |

---

## 3. Three-Tier Architecture

### Tier 1 — Registration Terminals (Edge Layer)

**Physical equivalent:** District offices (Lusaka, Kitwe, Ndola) and mobile registration units in rural/field locations.

**Prototype implementation:** Three Python Flask applications running as separate processes, each with its own SQLite database file, simulating independent district offices.

| Component | Implementation | Purpose |
|-----------|----------------|---------|
| Registration form | HTML5/CSS3/JS | Captures name, DOB, gender, district, face image |
| SQLite local cache | SQLite 3 | Offline record storage |
| Slot-ID generator | uuid4 + hashlib | Globally unique reservation — prevents concurrent duplicates |
| Sync worker | Python threading + requests | Background HTTPS transmission with exponential backoff |
| Conflict handler | conflict_handler.py | Routes slot-ID collisions to Type 5 alerts |

**Key architectural decision:** The slot-ID is generated at the moment of capture — before any network connectivity is required. It is a hash of terminal ID + timestamp + a random UUID. This means even if two terminals are completely offline, they cannot generate the same slot-ID, and any collision detected during sync is definitively a duplicate submission.

---

### Tier 2 — Central Server (Intelligence Hub)

**Physical equivalent:** NRPCA Headquarters, Lusaka.

**Prototype implementation:** One Python Flask application handling the API gateway, deduplication engine, batch audit scanner, and admin dashboard. PostgreSQL with pgvector for the master identity database.

#### 2A: Central API Gateway

| Component | Purpose |
|-----------|---------|
| Authentication | Token-based request validation |
| Rate limiting | Prevents terminal flooding |
| WAF | Basic request validation |
| Router | Directs synced records to deduplication pipeline |

#### 2B: Intelligent Deduplication Engine — Pipeline Steps

```
Incoming record (demographics + face image)
           │
           ▼
   ┌───────────────────────────────────┐
   │  Step 0: Biometric Quality        │
   │  OpenCV Laplacian variance        │
   │  q ∈ [0.0, 1.0] stored with record│
   └──────────────┬────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
   Channel A             Channel B
        │                    │
   ┌────▼────┐          ┌────▼────┐
   │ Bantu   │          │ FaceNet │
   │ normal. │          │ encoder │
   └────┬────┘          └────┬────┘
        │                    │
   ┌────▼────┐          ┌────▼────┐
   │ MinHash │          │  FAISS  │
   │   LSH   │          │  ANN    │
   │ (≥95%)  │          │ (≥90%)  │
   └────┬────┘          └────┬────┘
        │                    │
   ┌────▼────┐          ┌────▼────┐
   │Jaro-    │          │ Cosine  │
   │Winkler  │          │ simil.  │
   │ S_demo  │          │ S_bio   │
   └────┬────┘          └────┬────┘
        │                    │
        └─────────┬──────────┘
                  │
   ┌──────────────▼──────────────────┐
   │  Candidate union & deduplication │
   └──────────────┬──────────────────┘
                  │
   ┌──────────────▼──────────────────┐
   │  Step 3: Quality-Adaptive Fusion │
   │  w_bio = 0.4 + (0.3 × q)        │
   │  w_demo = 1.0 − w_bio            │
   │  composite = w_demo×S_demo       │
   │            + w_bio×S_bio         │
   └──────────────┬──────────────────┘
                  │
   ┌──────────────▼──────────────────┐
   │  Step 4: Decision Module + XAI  │
   │  composite < 0.55  → Clear      │
   │  0.55 – 0.85       → Review     │
   │  composite > 0.85  → Block      │
   └──────────────┬──────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
   Write       Review      Block
   master DB   queue     fraud flag
```

#### 2C: Batch Audit Scanner (Type 4 — NEW)

Operates entirely independently of the registration-time pipeline. Triggered on demand by the Administrator.

```
Administrator clicks "Run Audit Scan"
           │
           ▼
   SQL: SELECT nrc_number, COUNT(*)
        FROM citizens
        GROUP BY nrc_number
        HAVING COUNT(*) > 1
           │
           ▼
   For each conflicting pair:
   biometric_scorer.py → cosine similarity
           │
           ├── cosine < 0.55 → Different people
           │                   → Type 4 alert → dashboard
           │
           └── cosine ≥ 0.55 → Same person, clerical duplicate
                               → Standard duplicate alert
```

**Key architectural decision:** The batch scanner reuses `biometric_scorer.py` from the deduplication engine. No new algorithmic infrastructure is required — this is a 40-line SQL + loop module that calls existing code.

#### 2D: XAI Administrator Dashboard

| View | Content |
|------|---------|
| Alert list | All pending alerts, sorted by composite score, with Type badge (1–5) |
| Alert detail | Side-by-side records, six XAI fields, natural language rationale, action buttons |
| Audit log | Complete tamper-proof resolution history |
| Scan trigger | "Run Audit Scan" button → UC05 |

**Six XAI fields per alert:**
1. First-name Jaro-Winkler similarity score
2. Surname Jaro-Winkler similarity score
3. Date of birth Jaro-Winkler similarity score
4. FaceNet cosine similarity score (S_bio)
5. Image quality score (q)
6. Quality-adaptive weight breakdown (w_bio / w_demo applied)

---

### Tier 3 — Interoperability Layer

**Physical equivalent:** External institutions querying NRPCA for NRC validation.

**Prototype implementation:** Flask REST API stub — three endpoints, OAuth 2.0 token validation, audit logging. No live NRPCA connection.

| Endpoint | Response |
|----------|---------|
| GET /verify/{nrc} | valid / invalid / duplicate-flagged |
| GET /risk/{nrc} | risk score 0.0–1.0 |
| GET /status/{nrc} | active / blocked |

---

## 4. Data Architecture

### PostgreSQL Schema (Tier 2)

```sql
-- Master citizen identity table
CREATE TABLE citizens (
    id              SERIAL PRIMARY KEY,
    nrc_number      VARCHAR(20) NOT NULL,   -- indexed for batch scanner
    first_name      VARCHAR(100),
    surname         VARCHAR(100),
    date_of_birth   DATE,
    gender          VARCHAR(10),
    district        VARCHAR(100),
    quality_score   FLOAT,                  -- OpenCV Laplacian variance q
    terminal_id     VARCHAR(50),
    slot_id         UUID UNIQUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    status          VARCHAR(20) DEFAULT 'active'
);

CREATE INDEX idx_nrc_number ON citizens(nrc_number);  -- critical for batch scanner

-- Face embeddings (pgvector)
CREATE TABLE face_embeddings (
    id          SERIAL PRIMARY KEY,
    citizen_id  INTEGER REFERENCES citizens(id),
    embedding   VECTOR(128),               -- FaceNet 128-dim
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Duplicate alerts queue
CREATE TABLE duplicate_alerts (
    id              SERIAL PRIMARY KEY,
    record_id_1     INTEGER REFERENCES citizens(id),
    record_id_2     INTEGER REFERENCES citizens(id),
    duplicate_type  INTEGER,               -- 1, 2, 3, 4, or 5
    composite_score FLOAT,
    s_demo          FLOAT,
    s_bio           FLOAT,
    quality_score   FLOAT,
    w_bio           FLOAT,
    w_demo          FLOAT,
    xai_rationale   TEXT,
    status          VARCHAR(20) DEFAULT 'pending',
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Tamper-proof audit log
CREATE TABLE audit_log (
    id              SERIAL PRIMARY KEY,
    officer_id      VARCHAR(100),
    alert_id        INTEGER REFERENCES duplicate_alerts(id),
    action          VARCHAR(20),           -- MERGE, REJECT, APPROVE
    duplicate_type  INTEGER,
    rationale       TEXT,
    timestamp       TIMESTAMP DEFAULT NOW()
);
```

### SQLite Schema (Tier 1 — per terminal)

```sql
CREATE TABLE queued_records (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id     TEXT UNIQUE,
    first_name  TEXT,
    surname     TEXT,
    dob         TEXT,
    gender      TEXT,
    district    TEXT,
    face_image  BLOB,                      -- Base64 encoded
    quality     REAL,
    synced      INTEGER DEFAULT 0,         -- 0 = queued, 1 = synced
    created_at  TEXT
);
```

---

## 5. Technology Stack — Confirmed

| Category | Technology | Version | Justification |
|----------|------------|---------|---------------|
| Language | Python | 3.11 | ML/AI ecosystem; venv isolation on Ubuntu |
| Framework | Flask | 3.0.0 | Lightweight REST API; compatible with Python ML stack |
| Face Embeddings | FaceNet (facenet-pytorch) | 2.5.3 | 128-dim embeddings; pre-trained; FAISS compatible |
| Deep Learning | TensorFlow-CPU | 2.15.0 | CPU-only build; suitable for 4GB RAM hardware |
| ANN Index | FAISS-CPU | 1.7.4 | Sub-second retrieval; fits 1,000-record index in RAM |
| LSH Blocking | datasketch | 1.6.4 | MinHash LSH; configurable band/row parameters |
| Demographic Similarity | jellyfish | 1.0.3 | Jaro-Winkler; well-tested |
| Image Processing | OpenCV (headless) | 4.9.0 | Laplacian variance quality scoring; no GUI needed |
| Primary Database | PostgreSQL 15 + pgvector | 15 / 0.2.4 | ACID; vector storage; nrc_number index |
| Edge Database | SQLite | 3 | Zero-config; offline terminal storage |
| Development | VS Code + Jupyter | Latest | PoC notebooks + application code |
| Infrastructure | Native processes + start.sh | — | No Docker on 4GB RAM; services run as Python processes |
| Name Normalisation | Custom module | 1.0 | Original contribution; no library exists |
| Synthetic Data | Faker + custom corpus | 24.0.0 | Realistic Zambian records; five duplicate type injection |

---

## 6. Architectural Risks — Priority Order

This section is the foundation of UP's risk-driven Elaboration phase. These risks must be resolved in this exact order.

| Priority | Risk | Consequence if unresolved | Resolution Week | Method |
|----------|------|--------------------------|-----------------|--------|
| **1 — KILL RISK** | FaceNet produces non-separable embeddings on synthetic images | Channel B fails; Type 2 detection impossible; F1 < 0.85 | Week 3, Day 1 | `poc/faiss_poc.ipynb` — same-person cosine avg ≥ 0.80 |
| **2** | LSH recall insufficient on Zambian name corpus | Type 1 pairs escape blocking stage; never scored | Week 3, Day 2–3 | `poc/lsh_poc.ipynb` — recall ≥ 95% on variant sample |
| **3** | Bantu normalisation introduces false positives | Precision degraded; unrelated names merged | Week 4 | `poc/bantu_poc.ipynb` — validated on 50 held-out pairs |
| **4** | Scope overrun in 17 weeks | Incomplete system; evaluation chapter invalid | Ongoing | Weekly timeline check; batch scanner is 40 lines |
| **5** | Batch scanner false positives on Type 4 | Legitimate NRC holders incorrectly flagged | Week 10 | Cosine threshold calibrated on D5 Type 4 pairs |

---

## 7. Key Architectural Decisions and Rationale

### Decision 1: No Docker on development hardware
**Decision:** Run services natively as Python processes via `start.sh` rather than Docker Compose.  
**Rationale:** Docker Desktop consumes 1–2GB RAM on its own. On a 4GB Core i3 machine this leaves insufficient RAM for TensorFlow + FaceNet. Native processes on Ubuntu achieve identical multi-service simulation at zero overhead.  
**Impact:** Methodology chapter updated to document this as a resource-constraint-driven decision.

### Decision 2: FAISS-CPU over FAISS-GPU
**Decision:** Use `faiss-cpu` package.  
**Rationale:** At 1,000 records the FAISS index is approximately 0.5MB. CPU retrieval is under 1ms. GPU version requires CUDA drivers not available on this hardware. No performance benefit at this scale.

### Decision 3: tensorflow-cpu over tensorflow
**Decision:** Install `tensorflow-cpu`.  
**Rationale:** Full TensorFlow includes GPU support libraries consuming ~500MB additional RAM. CPU-only build is functionally identical for FaceNet inference without a GPU.

### Decision 4: Singleton FaceNet model loading
**Decision:** Load FaceNet weights once at module import time; all requests reuse the same loaded model.  
**Rationale:** Model loading takes 2–3 seconds and ~600MB RAM. Per-request loading would exhaust available RAM within seconds.

### Decision 5: Pre-compute and cache all embeddings
**Decision:** Run FaceNet over all D5 records once during dataset setup; save to `dataset/embeddings.npy`; load at startup.  
**Rationale:** Avoids re-running FaceNet on every evaluation run. Batch encoding of 1,000 images takes 3–5 minutes on this hardware; loading from disk takes < 1 second.

---

## 8. Architecture Confidence Assessment

| Component | Confidence | Basis |
|-----------|-----------|-------|
| Flask API gateway | High | Well-established; no unknowns |
| SQLite offline storage | High | Trivially simple; no unknowns |
| LSH/MinHash blocking | High | datasketch is production-quality; PoC will confirm |
| FAISS ANN biometric index | **Medium** | Depends on FaceNet embedding quality on synthetic images — **KILL RISK to be resolved Week 3** |
| Bantu normalisation | High | Pure string manipulation; no algorithmic unknowns |
| Quality-adaptive fusion | High | Formula fully specified; unit-testable |
| Batch audit scanner | High | SQL + existing biometric scorer; ~40 lines |
| XAI dashboard | High | Flask + Jinja2; display-only for pre-computed values |
| PostgreSQL + pgvector | Medium | pgvector installation on Ubuntu requires compilation — verify in Week 3 setup |

---

*Document version: 1.0 · Inception Phase · Week 1*  
*Next review: End of Elaboration (Week 7) — update confidence assessment based on PoC results*
