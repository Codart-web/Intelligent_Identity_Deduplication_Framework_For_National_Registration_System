# Inception Phase — Supervisor Sign-Off Meeting
## Intelligent Identity Deduplication Framework — National Registration System
**Nathan Sachitembe · 2022090446 · Week 2**

---

## Meeting Details

| Field | Detail |
|-------|--------|
| **Date** | __________________ |
| **Time** | __________________ |
| **Location** | __________________ |
| **Supervisor** | Mr. Martin Phiri |
| **Student** | Nathan Sachitembe (2022090446) |
| **Purpose** | Inception phase sign-off — confirm scope, architecture, and risk priority before Elaboration begins |

---

## Agenda

1. Revised proposal summary — what changed from original submission
2. Five duplicate types — confirm all four addressable types and ghost identity boundary
3. Architecture vision — three-tier system, dual-channel pipeline, batch audit scanner
4. Risk priority — confirm FAISS kill risk is Day 1 of Elaboration
5. Technology stack confirmation
6. Development environment — native processes on Ubuntu (no Docker on 4GB RAM)
7. Sign-off and Elaboration start authorisation

---

## 1. Revised Proposal Summary — Changes from Original

Presented to supervisor for awareness:

| Change | Reason |
|--------|--------|
| Five duplicate types now formally defined and named (Types 1–5) | Examiner feedback at presentation — problem statement needed clarity |
| Type 4 (shared NRC collision) added — batch audit scanner | Most common real-world duplicate type; detected post-issuance not at registration time |
| Type 5 (concurrent terminal submission) added | Slot-ID mechanism already existed; now formally typed and routed as alert |
| Ghost identity detection explicitly scoped OUT | Requires anomaly detection on officer behaviour — different problem class; future work |
| Objective O8 added — batch audit scanner | New deliverable D7 |
| Nine objectives total (was eight) | O9 is evaluation (was O8) |
| Technology adjusted for 4GB RAM hardware | tensorflow-cpu, no Docker Desktop, native processes, 4GB swap |

---

## 2. Scope Confirmation

**In scope — supervisor to confirm:**
- [ ] Three simulated offline registration terminals (Lusaka, Kitwe, Ndola)
- [ ] Dual-channel blocking: LSH/MinHash + FAISS/FaceNet
- [ ] Zambian Bantu phonetic normalisation module (original contribution)
- [ ] Quality-adaptive fusion (w_bio = 0.4 + 0.3q)
- [ ] Decision module — Clear / Review / Block thresholds from config.json
- [ ] Batch audit scanner — Type 4 shared NRC collision detection
- [ ] XAI admin dashboard — six fields per alert, merge/reject/approve
- [ ] Synthetic evaluation dataset — 1,000 records, 50 pairs, five types
- [ ] Three-system evaluation — framework vs Baseline A vs Baseline B
- [ ] Tier 3 API stub — demonstrative only

**Out of scope — supervisor to confirm:**
- [ ] Live NRPCA/INRIS deployment
- [ ] Fingerprint biometrics
- [ ] Real citizen data
- [ ] Production security hardening
- [ ] Ghost identity detection (future work)
- [ ] GRO birth register integration (future work)

---

## 3. Architecture Vision Confirmed

**Supervisor comments on architecture:**

```
____________________________________________________________
____________________________________________________________
____________________________________________________________
____________________________________________________________
```

---

## 4. Risk Priority Confirmed

**Kill risk — RISK 01 (FaceNet on synthetic images) — to be resolved Day 1 of Week 3:**

- [ ] Supervisor agrees FAISS PoC must be run before literature review begins
- [ ] Supervisor agrees fallback plan is acceptable if PoC fails

**Supervisor comments on risks:**

```
____________________________________________________________
____________________________________________________________
____________________________________________________________
```

---

## 5. Technology Stack Confirmed

| Technology | Supervisor approved? |
|------------|---------------------|
| Python 3.11 + Flask | [ ] Yes / [ ] No |
| FaceNet (facenet-pytorch) | [ ] Yes / [ ] No |
| FAISS-CPU | [ ] Yes / [ ] No |
| datasketch MinHash LSH | [ ] Yes / [ ] No |
| jellyfish Jaro-Winkler | [ ] Yes / [ ] No |
| PostgreSQL 15 + pgvector | [ ] Yes / [ ] No |
| SQLite (edge terminals) | [ ] Yes / [ ] No |
| OpenCV (headless) | [ ] Yes / [ ] No |
| tensorflow-cpu | [ ] Yes / [ ] No |
| Native processes (no Docker) | [ ] Yes / [ ] No |

---

## 6. Elaboration Plan Confirmed

Week 3 priority order confirmed with supervisor:
1. Day 1: FAISS PoC (kill risk resolution)
2. Day 2–3: LSH PoC
3. Day 3–5: Literature review begins (parallel with PoCs)
4. Week 4: Bantu normalisation PoC + database schema
5. Week 4–5: Synthetic dataset generation
6. Week 6–7: Registration terminal infrastructure

- [ ] Supervisor confirms this order is correct
- [ ] Supervisor agrees literature review can be written after PoCs, not before

---

## 7. Supervisor Feedback and Instructions

```
____________________________________________________________
____________________________________________________________
____________________________________________________________
____________________________________________________________
____________________________________________________________
____________________________________________________________
____________________________________________________________
____________________________________________________________
```

---

## 8. Inception Phase Sign-Off

By signing below, the supervisor confirms that:
- The revised project scope is approved
- The five duplicate type taxonomy is accepted
- The ghost identity exclusion is understood and agreed
- The student may proceed to Elaboration phase

**Supervisor Name:** ___________________________

**Signature:** ___________________________

**Date:** ___________________________

**Next meeting scheduled:** ___________________________

---

## 9. Student Action Items from This Meeting

| Action | Due |
|--------|-----|
| [ ] Run FAISS PoC — Day 1 of Week 3 | Week 3 Mon |
| [ ] Run LSH PoC — Day 2–3 of Week 3 | Week 3 Wed |
| [ ] Update risk register with PoC results | Week 3 Fri |
| [ ] Begin literature review | Week 3 |
| [ ] Design PostgreSQL schema | Week 3 |
| [ ] Verify pgvector installation | Week 3 |
| [ ] Add swap file to Ubuntu | Before Week 3 |

---

*Document version: 1.0 · Inception Phase · Week 2*
