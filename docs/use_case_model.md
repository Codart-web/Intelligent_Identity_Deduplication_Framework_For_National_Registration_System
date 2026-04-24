# Use Case Model
## Intelligent Identity Deduplication Framework — National Registration System
**Nathan Sachitembe · 2022090446 · UP Inception Phase · Week 1**

---

## 1. Purpose

This document defines the actors and primary use cases of the Intelligent Identity Deduplication Framework. In the Unified Process (UP), the use case model is the foundation of the entire system — every module built during Construction must trace back to a use case defined here. This document is produced during Inception and referenced throughout all subsequent UP phases.

---

## 2. System Boundary

The system boundary is the Intelligent Identity Deduplication Framework prototype. It includes:
- Three simulated offline-capable registration terminals (Tier 1)
- The central deduplication engine and batch audit scanner (Tier 2)
- The XAI administrator dashboard (Tier 2)
- The Tier 3 verification API stub

It **excludes**: live NRPCA/INRIS infrastructure, real citizen data, fingerprint biometrics, and ghost identity detection (future work).

---

## 3. Actors

### Primary Actors (interact directly with the system)

| Actor | Description | Tier |
|-------|-------------|------|
| **Registration Officer** | A NRPCA district office officer who captures citizen demographic details and facial images at a registration terminal. The officer does not interact with the deduplication engine directly — they submit registrations and observe sync status. | Tier 1 |
| **Administrator** | A NRPCA headquarters officer who reviews duplicate alerts, examines XAI explanations, makes resolution decisions (merge / reject / approve), and triggers the batch audit scanner. The Administrator is the primary human-in-the-loop for AI-flagged decisions. | Tier 2 |
| **External Verifier** | An authorised officer at an external institution (Electoral Commission, bank KYC officer, NHIMA, ZICTA, ZRA) who queries the Tier 3 API to verify whether an NRC number is valid and unique. | Tier 3 |

### Secondary Actors (system actors — no human interaction)

| Actor | Description |
|-------|-------------|
| **Sync Worker** | Background process on each terminal that monitors connectivity and transmits queued records to the Central API Gateway. Triggers Type 5 conflict detection on slot-ID collision. |
| **Deduplication Engine** | Automated pipeline that processes incoming records through quality assessment, dual-channel blocking, scoring, quality-adaptive fusion, and decision routing. |
| **Batch Audit Scanner** | Scheduled/on-demand module that queries the master database for shared NRC number conflicts and generates Type 4 alerts. |

---

## 4. Use Case Diagram (Text Representation)

```
┌──────────────────────────────────────────────────────────────────────┐
│                INTELLIGENT DEDUPLICATION FRAMEWORK                    │
│                                                                        │
│  ┌──────────────┐     UC01 Register Citizen                           │
│  │ Registration │────────────────────────────────────────────────┐    │
│  │   Officer    │     UC02 View Sync Status                       │    │
│  └──────────────┘────────────────────────────────────────────┐   │    │
│                                                              │   │    │
│  ┌──────────────┐     UC03 Review Duplicate Alert            │   │    │
│  │              │────────────────────────────────────────┐   │   │    │
│  │              │     UC04 Resolve Duplicate Alert        │   │   │    │
│  │ Administrator│────────────────────────────────────┐   │   │   │    │
│  │              │     UC05 Trigger Batch Audit Scan   │   │   │   │    │
│  │              │────────────────────────────────┐   │   │   │   │    │
│  └──────────────┘     UC06 View Audit Log        │   │   │   │   │    │
│  └──────────────┘────────────────────────────┐  │   │   │   │   │    │
│                                              │  │   │   │   │   │    │
│  ┌──────────────┐     UC07 Verify NRC Number  │  │   │   │   │   │    │
│  │   External   │────────────────────────┐   │  │   │   │   │   │    │
│  │   Verifier   │     UC08 Query Risk     │   │  │   │   │   │   │    │
│  └──────────────┘─────────────────────┐  │   │  │   │   │   │   │    │
│                                       │  │   │  │   │   │   │   │    │
│  [System] Sync Worker ── UC09 Sync Records to Central Server         │
│  [System] Dedup Engine ── UC10 Process Incoming Registration          │
│  [System] Batch Scanner ── UC11 Scan Database for NRC Conflicts       │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. Use Case Specifications

---

### UC01 — Register Citizen

| Field | Detail |
|-------|--------|
| **Actor** | Registration Officer |
| **Goal** | Capture a citizen's demographic details and facial image at a district terminal and submit for registration |
| **Precondition** | Terminal is powered on; officer is logged in; citizen presents themselves with required documents |
| **Trigger** | Officer begins a new registration session |
| **Main Flow** | 1. Officer enters first name, surname, date of birth, gender, district · 2. Officer captures facial image via webcam · 3. System generates cryptographic slot-ID (uuid4 + hashlib) · 4. Record is stored to local SQLite database · 5. System confirms local save to officer · 6. Sync worker queues record for transmission |
| **Alternative Flow** | A3a. Camera unavailable → officer notes low-quality image; system stores record with quality flag q = 0.0; biometric weight reduced at scoring stage |
| **Exception Flow** | A5a. SQLite write fails → system displays error; officer retries |
| **Postcondition** | Record stored in local SQLite; slot-ID generated; sync worker queue updated |
| **Linked Objective** | O2 |
| **Duplicate Type Addressed** | Types 1, 2, 3 (detected downstream); Type 5 (triggered if same slot-ID submitted from another terminal) |

---

### UC02 — View Sync Status

| Field | Detail |
|-------|--------|
| **Actor** | Registration Officer |
| **Goal** | Check whether locally queued records have successfully synced to the central server |
| **Precondition** | Terminal app is running |
| **Main Flow** | 1. Officer views sync dashboard panel · 2. System displays count of queued records, last successful sync timestamp, and connectivity status · 3. If connectivity is unavailable, exponential backoff timer is displayed |
| **Postcondition** | Officer has visibility of sync state without needing to contact headquarters |
| **Linked Objective** | O2 |

---

### UC03 — Review Duplicate Alert

| Field | Detail |
|-------|--------|
| **Actor** | Administrator |
| **Goal** | Examine a flagged duplicate alert and understand why the system flagged it |
| **Precondition** | At least one alert exists in the duplicate_alerts queue; Administrator is logged into the dashboard |
| **Trigger** | Administrator opens the alert list view |
| **Main Flow** | 1. Administrator views alert list sorted by composite score (highest first) · 2. Administrator selects an alert · 3. System displays both candidate records side by side · 4. System displays all six XAI fields: first-name Jaro-Winkler score, surname Jaro-Winkler score, DOB Jaro-Winkler score, FaceNet cosine similarity, quality score q, quality-adaptive weight breakdown (w_bio / w_demo) · 5. System displays duplicate type label (Type 1–5) · 6. System displays natural language system assessment explaining why this pair was flagged |
| **Alternative Flow** | A4a. Type 4 alert (batch scanner) → demographic scores may be low or absent; cosine similarity is the primary evidence; system notes "Shared NRC number conflict — different biometric profiles detected" |
| **Alternative Flow** | A4b. Type 5 alert (slot-ID conflict) → system displays both terminal IDs and submission timestamps |
| **Postcondition** | Administrator has full evidence to make a resolution decision |
| **Linked Objective** | O7 |
| **Duplicate Types** | All five types — each has a distinct alert presentation |

---

### UC04 — Resolve Duplicate Alert

| Field | Detail |
|-------|--------|
| **Actor** | Administrator |
| **Goal** | Take a resolution action on a flagged duplicate alert and record the decision in the audit log |
| **Precondition** | Administrator has reviewed the alert (UC03) |
| **Trigger** | Administrator clicks Merge, Reject, or Approve |
| **Main Flow — Merge** | 1. Administrator selects canonical record · 2. System marks other record as archived · 3. System writes audit_log entry: officer_id, timestamp, alert_id, action=MERGE, duplicate_type, rationale |
| **Main Flow — Reject** | 1. Administrator confirms rejection of incoming record · 2. System marks record as rejected in master DB · 3. Audit log entry written |
| **Main Flow — Approve Both** | 1. Administrator confirms both records represent distinct individuals · 2. System writes both records to master DB as cleared · 3. Audit log entry written |
| **Exception Flow** | E1. Administrator is unsure → no action taken; alert remains in queue for later review |
| **Postcondition** | Alert resolved; audit_log updated with full decision trail |
| **Linked Objective** | O7 |

---

### UC05 — Trigger Batch Audit Scan

| Field | Detail |
|-------|--------|
| **Actor** | Administrator |
| **Goal** | Initiate a post-issuance scan of the master database to find all NRC numbers assigned to more than one citizen |
| **Precondition** | Administrator is logged into the dashboard; master database has records loaded |
| **Trigger** | Administrator clicks "Run Audit Scan" button on the dashboard |
| **Main Flow** | 1. System executes: `SELECT nrc_number, COUNT(*) FROM citizens GROUP BY nrc_number HAVING COUNT(*) > 1` · 2. For each conflicting NRC number, system retrieves both records · 3. System runs biometric_scorer.py — computes cosine similarity between stored FaceNet embeddings · 4. Low cosine similarity (< 0.55) → confirmed Type 4 identity collision → alert created and routed to dashboard · 5. High cosine similarity (≥ 0.55) → same-person clerical duplicate → standard duplicate alert · 6. System displays count of conflicts found and time taken |
| **Alternative Flow** | A1a. No conflicts found → system displays "Audit complete — no shared NRC conflicts detected" |
| **Postcondition** | All Type 4 alerts added to duplicate_alerts queue; administrator can now review each via UC03 |
| **Linked Objective** | O8 |
| **Duplicate Type** | Type 4 exclusively |
| **Performance Target** | < 30 seconds for 1,000 records |

---

### UC06 — View Audit Log

| Field | Detail |
|-------|--------|
| **Actor** | Administrator |
| **Goal** | Review a complete history of all resolution decisions made on duplicate alerts |
| **Precondition** | At least one resolution has been made |
| **Main Flow** | 1. Administrator opens audit log view · 2. System displays all entries: officer_id, timestamp, alert_id, action, duplicate_type, composite_score, rationale · 3. Administrator can filter by date, type, or action · 4. Log is tamper-proof — no delete or edit operations are permitted |
| **Postcondition** | Administrator has a complete auditable trail — satisfies governance transparency requirement |
| **Linked Objective** | O7 |

---

### UC07 — Verify NRC Number

| Field | Detail |
|-------|--------|
| **Actor** | External Verifier |
| **Goal** | Check whether a presented NRC number is valid, active, and not associated with a duplicate record |
| **Precondition** | Verifier has a valid OAuth 2.0 API token; NRC number is known |
| **Main Flow** | 1. Verifier sends GET /verify/{nrc_number} with Bearer token · 2. System validates token · 3. System queries master DB for NRC number · 4. System returns: {status: "valid" \| "invalid" \| "duplicate-flagged", message: "..."} · 5. API call is logged to audit_log with institution_id and timestamp |
| **Exception Flow** | E1. Invalid token → 401 Unauthorized · E2. Rate limit exceeded → 429 Too Many Requests |
| **Postcondition** | Verifier receives status without accessing raw citizen data |
| **Linked Objective** | D8 (Tier 3 stub) |

---

### UC08 — Query Duplicate Risk Score

| Field | Detail |
|-------|--------|
| **Actor** | External Verifier |
| **Goal** | Retrieve the duplicate risk score associated with an NRC number for AML/KYC compliance purposes |
| **Main Flow** | 1. Verifier sends GET /risk/{nrc_number} · 2. System returns: {nrc: "...", risk_score: 0.0–1.0, flagged: true\|false} · 3. Logged to audit_log |
| **Linked Objective** | D8 |

---

### UC09 — Sync Records to Central Server (System)

| Field | Detail |
|-------|--------|
| **Actor** | Sync Worker (system) |
| **Goal** | Transmit locally queued SQLite records to the Central API Gateway over HTTPS |
| **Trigger** | Connectivity detected by background worker |
| **Main Flow** | 1. Worker checks SQLite queue for unsynchronised records · 2. For each record: encode facial image as Base64 · 3. POST JSON payload to Central API Gateway · 4. On 200 response: mark record as synced in SQLite · 5. On failure: exponential backoff (1s, 2s, 4s, 8s...) before retry |
| **Slot-ID Conflict** | If central server returns 409 Conflict (slot-ID already registered): worker creates Type 5 alert entry locally and notifies dashboard |
| **Linked Objective** | O2 |

---

### UC10 — Process Incoming Registration (System)

| Field | Detail |
|-------|--------|
| **Actor** | Deduplication Engine (system) |
| **Goal** | Run a newly synced record through the full deduplication pipeline |
| **Trigger** | Central API Gateway receives and validates a sync payload |
| **Main Flow** | Step 0: OpenCV Laplacian variance → quality score q ∈ [0,1] · Step 1A: Bantu normalisation → MinHash → LSH query → demographic candidates · Step 1B: FaceNet encode → FAISS query → biometric candidates · Candidate union · Step 2A: Jaro-Winkler per field → S_demo · Step 2B: Cosine similarity → S_bio · Step 3: w_bio = 0.4 + (0.3×q), composite = w_demo×S_demo + w_bio×S_bio · Step 4: composite < 0.55 → write to master DB; 0.55–0.85 → review queue; > 0.85 → block |
| **Linked Objectives** | O3, O4, O5, O6 |
| **Performance Target** | < 2 seconds per record |

---

### UC11 — Scan Database for NRC Conflicts (System)

| Field | Detail |
|-------|--------|
| **Actor** | Batch Audit Scanner (system) |
| **Goal** | Identify all shared NRC number conflicts in the master database |
| **Trigger** | Administrator clicks "Run Audit Scan" (UC05) |
| **Main Flow** | SQL GROUP BY → conflict pairs → biometric scorer → Type 4 alerts |
| **Linked Objective** | O8 |

---

## 6. Use Case to Objective Traceability Matrix

| Use Case | O1 | O2 | O3 | O4 | O5 | O6 | O7 | O8 | O9 |
|----------|----|----|----|----|----|----|----|----|----|
| UC01 Register Citizen | | ✓ | | | | | | | |
| UC02 View Sync Status | | ✓ | | | | | | | |
| UC03 Review Duplicate Alert | | | | | | | ✓ | | |
| UC04 Resolve Duplicate Alert | | | | | | | ✓ | | |
| UC05 Trigger Batch Audit Scan | | | | | | | | ✓ | |
| UC06 View Audit Log | | | | | | | ✓ | | |
| UC07 Verify NRC Number | | | | | | | | | |
| UC08 Query Risk Score | | | | | | | | | |
| UC09 Sync Records (System) | | ✓ | | | | | | | |
| UC10 Process Registration (System) | | | ✓ | ✓ | ✓ | ✓ | | | ✓ |
| UC11 Scan NRC Conflicts (System) | | | | | | | | ✓ | ✓ |

---

## 7. Use Case Priority for UP Elaboration

In UP, use cases driving the highest architectural risk are elaborated first. The priority order for this project is:

1. **UC10 — Process Incoming Registration** — drives the FAISS kill-risk PoC. Must be partially implemented (embedding + FAISS query) in Week 3 to resolve Risk 1.
2. **UC11 — Scan NRC Conflicts** — drives LSH PoC validation in Week 3.
3. **UC01 — Register Citizen** — drives D1 terminal implementation in Weeks 6–7.
4. **UC03/UC04 — Review and Resolve Alert** — drives D3 dashboard in Weeks 10–11.
5. **UC05 — Trigger Batch Audit Scan** — drives D7 scanner in Week 10.

---

*Document version: 1.0 · Inception Phase · Week 1*  
*Next review: End of Elaboration (Week 7) — update with any scope changes identified during PoC phase*
