"""Deterministic tests for the StudySprint 0.6.0 adaptive planner."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402
from study_adaptive import build_adaptive_plan, replan_after_missed  # noqa: E402

NOW = "2026-11-04T08:00:00Z"
WINDOWS = [
    {"start": "2026-11-04T09:00:00-08:00",
     "end": "2026-11-04T11:00:00-08:00", "source": "student-calendar"},
    {"start": "2026-11-05T09:00:00-08:00",
     "end": "2026-11-05T10:30:00-08:00", "source": "student-calendar"},
]
TASKS = [
    {"task_id": "bio-quiz", "course": "BIO 101", "topic": "cells",
     "estimated_minutes": 50, "due_at": "2026-11-05T17:00:00-08:00",
     "priority": 4, "evidence_refs": ["syllabus:bio:w2"],
     "evidence_verified": True, "student_confirmed": True},
    {"task_id": "history-reading", "course": "HIST 210", "topic": "WWI",
     "estimated_minutes": 25, "priority": 2,
     "evidence_refs": ["syllabus:hist:w1"],
     "evidence_verified": True, "student_confirmed": True},
]


def test_plan_is_deterministic_and_evidence_carrying():
    a = build_adaptive_plan(TASKS, WINDOWS, now=NOW)
    b = build_adaptive_plan(TASKS, WINDOWS, now=NOW)
    assert a == b
    assert a["schema"] == "studysprint-adaptive-plan/v1"
    assert all(s["evidence_refs"] for s in a["sessions"])
    assert a["scheduled_minutes"] == 75


def test_due_first_and_session_chunks_respect_budgets():
    plan = build_adaptive_plan(TASKS, WINDOWS, now=NOW,
                               session_minutes=25, daily_budget_minutes=50)
    assert plan["sessions"][0]["task_id"] == "bio-quiz"
    assert all(s["duration_minutes"] <= 25 for s in plan["sessions"])
    assert all(v <= 50 for v in plan["daily_minutes"].values())
    assert sum(1 for s in plan["sessions"] if s["task_id"] == "bio-quiz") == 2


def test_unconfirmed_or_unreferenced_tasks_never_enter_plan():
    tasks = [
        {**TASKS[0], "task_id": "unconfirmed", "student_confirmed": False},
        {**TASKS[0], "task_id": "unverified", "evidence_verified": False},
        {**TASKS[0], "task_id": "no-ref", "evidence_refs": []},
    ]
    plan = build_adaptive_plan(tasks, WINDOWS, now=NOW)
    assert plan["sessions"] == []
    assert {x["reason"] for x in plan["excluded"]} == {
        "evidence-not-confirmed", "missing-evidence-reference"}


def test_insufficient_time_is_explicit_not_silently_dropped():
    plan = build_adaptive_plan(
        [{**TASKS[0], "estimated_minutes": 300}],
        WINDOWS, now=NOW, daily_budget_minutes=60)
    assert plan["scheduled_minutes"] < 300
    assert plan["unscheduled"][0]["remaining_minutes"] > 0
    assert plan["unscheduled"][0]["reason"]


def test_rejects_naive_or_overlapping_availability():
    with pytest.raises(ValueError, match="explicit UTC offset"):
        build_adaptive_plan(TASKS, [{"start": "2026-11-04T09:00:00",
                                     "end": "2026-11-04T10:00:00"}], now=NOW)
    with pytest.raises(ValueError, match="must not overlap"):
        build_adaptive_plan(TASKS, [
            WINDOWS[0],
            {"start": "2026-11-04T10:00:00-08:00",
             "end": "2026-11-04T12:00:00-08:00"}], now=NOW)


def test_replan_restores_missed_open_task_and_records_policy():
    plan = replan_after_missed(
        TASKS, WINDOWS, missed_task_ids=["history-reading"], now=NOW)
    assert plan["recovery"]["missed_task_ids"] == ["history-reading"]
    assert plan["recovery"]["policy"] == "recompute-from-current-availability"
    assert "history-reading" in {s["task_id"] for s in plan["sessions"]}
