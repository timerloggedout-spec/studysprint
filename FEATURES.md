# StudySprint — features a user would want (UI/UX first)

Owner-requested 2026-10-30. User = a first-gen college student with a
syllabus, a phone, a job, and no family playbook for college.
Priorities: **Now** = fits the pre-submission iteration window
(before Nov 4) · **Next** = v0.2–v0.3 · **Later** = v1.x.
Status tags: ✓ built · ◐ partial · ○ planned.

## The one-screen promise
Drop a syllabus → see *today's* plan in under 10 seconds. Every
feature below serves that screen or the daily loop around it.

## 1. Intake (getting a syllabus in)
- ✓ Syllabus file → verified evidence set → plan (`study_tools`)
- ○ PDF syllabus upload + parse (the concept's original input;
  today = structured JSON) — **Next**
- ○ Photo/screenshot of a paper syllabus → OCR → same pipeline — Later
- ◐ Trust receipt before planning: the UI shows *what was fetched*
  (course, weeks, due dates, hash) and only plans after the student
  confirms — the evidence gate made visible — **Now** (receipt data
  exists; surface it)
- ○ Paste-a-link intake (LMS page / Google Doc) — Next
- ○ Multi-course intake: 4–5 syllabi → one merged calendar with
  conflict flags (two midterms, same week) — **Next, high value**

## 2. The plan (the core screen)
- ✓ Week-by-week plan: learn + retrieve block per topic
- ✓ Re-plan on missed week (sessions carried forward, flagged)
- ○ **Today view**: one card — today's sessions, one tap to start,
  one tap "I missed this" → instant re-plan, no guilt UI — **Now**
  (re-plan logic exists; render it)
- ○ Time-budget slider: "I have 25 min today, not 45" → plan
  re-flows around the student's real day (job shifts, commute) — **Now**
- ○ Exam countdown mode: inside 7 days of a due date the plan
  shifts weight to retrieval + practice sets automatically — Next
- ○ Drag-to-edit sessions; the agent re-balances the rest of the
  week around the edit ("view, edit, and act on its work") — Next
  (judges' usefulness axis)
- ○ Calendar export (.ics / Google Calendar) — Next
- ○ Print / share a week (PDF) for a study group or advisor — Later

## 3. Daily loop (retention lives here)
- ◐ Recall quizzes per week (generated from topics) ✓ ·
  practice-set quiz path ✓
- ○ Daily check-in (30 seconds): done / partial / missed per
  session → feeds re-plan; streaks shown as *recovered weeks*,
  never as broken chains — **Now** (data model), Next (UI)
- ○ Spaced repetition: quiz misses resurface at 1d / 3d / 7d — Next
- ○ "Explain it back" voice/text answer → agent checks against the
  topic and stamps what was missed — Later
- ○ Gentle nudges (push/SMS) at the student's chosen hour, quiet
  by default, off during exams week unless asked — Next

## 4. Trust + accessibility (why first-gen users stay)
- ✓ Hashed receipts: every decision shows its evidence set —
  in UI terms: "Planned from *your* BIO 101 syllabus, fetched
  09:12, 3 weeks, 6 topics" — **Now** (surface existing receipts)
- ○ Plain-language mode: no jargon anywhere; every agent action
  explains itself in one sentence ("I moved Tuesday's session
  because you marked it missed") — **Now** (copy standard)
- ○ Spanish + multilingual UI and quiz prompts — Next
- ○ Works offline / low-end Android: plan + quizzes cached,
  sync when back — Next (our users' actual devices)
- ○ Screen-reader + large-text clean; color never the only signal
  (ABSTAIN/ALLOW states also carry icons + words) — **Now** (standard)
- ○ Privacy plainly stated: syllabus stays yours; no account
  needed to try; delete = one tap, actually deletes — **Now** (copy),
  Next (impl)

## 5. Social proof + help
- ○ Study-buddy mode: share a week's plan, co-check-in — Later
- ○ Advisor/tutor view: read-only plan + progress for a mentor
  the student invites — Later
- ○ "I'm lost" button → maps the current topic to campus resources
  (tutoring center hours, office hours from the syllabus itself) — Next

## UX principles (binding on every screen)
1. Today first. The plan is a means; *today* is the product.
2. No guilt mechanics. Missed = re-planned, never red, never a
   broken streak.
3. Evidence visible. If the agent claims it, the receipt is one
   tap away (the D0 pattern, as a UI rule).
4. One thumb, one hand, on a bus. Primary actions bottom-reach,
   ≥48px targets.
5. Plain words. If a first-gen freshman needs a dictionary, the
   copy is wrong.

## Anti-features (deliberately never)
- No leaderboard / no comparing students.
- No paywall on re-planning or quizzes (the core loop is the
  social-good surface).
- No planning from an unverified syllabus claim (gate ABSTAINs —
  a feature, surfaced honestly, not an error state).
