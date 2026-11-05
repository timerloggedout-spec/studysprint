# StudySprint 0.6.0 — Parallel Product Track

Status: proposal + implementation contract  
Baseline: production foundation 1.0.0; webApp 0.5.2; APK 0.5.2  
Branch: `experiment/0.6.0`  
Rule: this track MUST NOT mutate `main`, production tags, or existing 0.5.x release assets.

## Product objective

Make StudySprint adapt to a student's real week rather than asking the student to adapt to a static plan. Preserve the product's defining trust boundary: no study plan is generated from unconfirmed or unverified course evidence.

Primary user: a first-generation college student balancing classes, work, commuting, family responsibilities, and limited study time.

## Version topology

- `main`: protected production baseline; current foundation and independently versioned surfaces remain authoritative.
- `experiment/0.6.0`: integration branch for the next product line.
- `feature/0.6.0-intelligent-intake`
- `feature/0.6.0-adaptive-planner`
- `feature/0.6.0-learning-intelligence`
- `feature/0.6.0-student-command-center`
- `feature/0.6.0-study-companion`
- `release/0.6.0`: cut only after integration gates pass.

The webApp, APK, and TUI keep independent SemVer lines as required by VERSIONING.md. A product milestone does not force all surfaces to ship simultaneously.

## Product increments

### 1. Intelligent course intake

- Accept structured syllabus data first; add PDF/text extraction as a separate, testable adapter.
- Normalize course, term, weeks, learning outcomes, readings, assessments, due dates, and estimated workload into a canonical course model.
- Attach source location, extraction method, content hash, confidence, and verification state to each extracted fact.
- Show a trust receipt and require student confirmation before any extracted facts can influence a plan.
- Flag missing dates, ambiguous time zones, contradictory assessment dates, and duplicate course records.
- Never silently invent a due date, reading range, or workload estimate.

Acceptance: fixture-based parser tests; malformed/ambiguous input tests; evidence provenance tests; explicit confirmation gate tests; no-network offline path remains supported.

### 2. Adaptive study planner

- Build weekly plans from confirmed course evidence, available time, fixed commitments, due dates, and student-selected session length.
- Support a manual time budget and protected unavailable periods.
- Rebalance missed sessions without guilt language; retain a visible explanation of what moved and why.
- Prioritize imminent assessments and overdue high-value retrieval practice without deleting the student's other commitments.
- Keep manual overrides stable until the student asks to re-plan.

Acceptance: deterministic planner fixtures; no-overlap scheduling; workload-cap tests; missed-session recovery tests; stable manual override tests; explainable prioritization receipts.

### 3. Learning intelligence

- Use existing FSRS/SM-2 review history as the primary evidence for review scheduling.
- Add topic-level mastery only when backed by explicit answers, confidence ratings, or review events.
- Distinguish observed performance from inferred mastery; display sample size and recency.
- Recommend the next review using retrieval difficulty, recency, assessment proximity, and available time.
- Provide an explain-back prompt and short formative checks; do not label a student as having mastered a topic from a single response.

Acceptance: scheduler parity with current core; reproducible mastery aggregation; low-sample warnings; explainable recommendation tests; no ungrounded mastery claims.

### 4. Student command center

- A compact Today surface: next best action, available study time, deadlines, and a one-tap recovery action.
- A week view that shows workload distribution and collisions across courses.
- Course switcher and current course context stay visible.
- Accessible keyboard navigation, responsive mobile layout, reduced-motion support, and offline-readable state.
- Progress reporting emphasizes recovered consistency and useful work, not punitive streak loss.

Acceptance: responsive viewport tests; keyboard and screen-reader checks; offline shell regression; multi-course isolation tests; persisted state migration tests.

### 5. Grounded study companion

- Tutor only from confirmed course evidence, selected readings, and the student's own review history.
- Every course-specific answer carries a source reference or clearly says when the available evidence is insufficient.
- Offer Socratic hints, worked examples, recall questions, and explain-back checks.
- Never fabricate quotations, page numbers, syllabus requirements, or instructor intent.
- Keep external model/network use opt-in and fail closed when unavailable; the existing offline product remains usable.

Acceptance: source-grounding tests; abstention tests; prompt-injection/content-boundary tests; privacy and network opt-in tests; offline fallback tests.

## Shared domain model

Keep core business logic in the Python domain layer; surfaces are adapters.

- `CourseEvidence`: course_id, source_id, source_hash, locator, evidence_kind, extracted_value, confidence, verification_status.
- `AvailabilityWindow`: start, end, timezone, recurrence, source, protected.
- `StudyTask`: course_id, topic_id, evidence_refs, estimated_minutes, due_at, priority_inputs, status.
- `StudySession`: task_refs, start, end, duration, plan_revision, origin, override_reason.
- `LearningSignal`: topic_id, signal_kind, observed_at, score_or_grade, sample_size, source_ref.
- `RecommendationReceipt`: recommendation_id, inputs, rationale, evidence_refs, generated_at, model_or_algorithm_version.

Do not persist derived mastery as if it were observed evidence. Derived values must be reproducible from source signals.

## Architecture and compatibility

1. Keep existing trust receipt, evidence gate, course isolation, scheduler implementations, and offline mode as non-regression invariants.
2. Implement domain logic in core modules with typed inputs/outputs and deterministic tests.
3. Expose versioned adapters for webApp, APK (shared web bundle where applicable), and TUI.
4. Keep experimental API work behind an adapter; no new hosted dependency is required for the core experience.
5. Prefer local-first persistence. Any sync or AI provider integration must be opt-in, scoped, documented, and removable without data loss.
6. Migrations must be additive, idempotent, and tested against copies of v0.5.x data.

## Delivery sequence

| Stage | Work | Exit gate |
|---|---|---|
| 0 | Baseline audit + parity snapshot | Current main tests and parity matrix captured |
| 1 | Canonical evidence/task models | Schema + migration + fixtures green |
| 2 | Adaptive planner core | Deterministic scheduling and recovery suite green |
| 3 | Today/Week command center | Accessibility, mobile, offline, and course isolation gates green |
| 4 | Learning signals + explainability | Provenance, sample-size, and scheduler parity gates green |
| 5 | Intelligent intake adapters | Parse/ambiguity/confirmation gates green |
| 6 | Grounded companion adapter | Citation, abstention, privacy, and offline gates green |
| 7 | Surface parity + release candidate | Full tests, demo, parity matrix, artifact reproducibility |
| 8 | Independent surface cuts | Release-cut workflow per surface and version |

## Release gates

A 0.6.0 release candidate is blocked unless all are true:

- Existing production 0.5.2 tags and assets remain unchanged.
- Full offline suite passes: `python3 -m pytest tests/`.
- `python3 demo.py` completes and its evidence snapshot is committed when decisions change.
- Surface parity matrix is updated with bound/partial/absent evidence, not marketing claims.
- Data migrations are tested from a representative 0.5.x fixture.
- WebApp, APK, and TUI have independent version decisions and artifact checksums.
- No secrets, API tokens, student records, or sensitive learning signals enter fixtures or telemetry.
- Release notes state known gaps, offline behavior, data handling, and rollback instructions.

## Rollout and rollback

- First ship behind opt-in feature flags on the experimental branch.
- Dogfood with synthetic courses and deterministic fixture data.
- Promote only after the release candidate gates pass.
- Keep the last stable data format readable; disable new planner/companion behavior without deleting student data.
- Roll back by disabling the feature flag and restoring the prior surface artifact; never rewrite or move a published tag.

## Explicit non-goals for 0.6.0

- Replacing the existing evidence/trust gate.
- Making cloud AI mandatory.
- Claiming cognitive or clinical diagnoses.
- Ranking students or comparing them to other students.
- Automatically sharing student data with instructors, employers, or third parties.
- Breaking the current TUI, webApp, or APK version lines.

## Initial implementation issues

1. [P0] Capture v0.5.2 baseline tests, parity matrix, and data fixtures.
2. [P0] Add canonical evidence and availability models with migration tests.
3. [P0] Implement deterministic adaptive planner core and recovery receipts.
4. [P1] Build Today/Week command center on the existing webApp shell.
5. [P1] Add topic learning signals with evidence and sample-size display.
6. [P1] Add syllabus document intake adapter with explicit confirmation.
7. [P2] Add grounded companion behind opt-in provider adapter.
8. [P1] Port and verify each accepted capability across TUI/APK/webApp.
9. [P0] Run full release gates and cut each surface independently.

---
This document defines the parallel product track; it is not a release declaration. A release exists only after the repository's VERSIONING.md release process completes on the relevant release ref.
