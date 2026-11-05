"""StudySprint 0.6.0 adaptive planner — deterministic, evidence-gated MVP.

The planner is deliberately pure Python: no model/network dependency, no
implicit clock, and no mutation of source tasks. Availability timestamps must
be ISO-8601 values with an explicit UTC offset. Tasks are schedulable only
when their evidence is explicitly verified and confirmed.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


SCHEMA = "studysprint-adaptive-plan/v1"


def _aware(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include an explicit UTC offset")
    return parsed


def _deadline(task: dict[str, Any]) -> datetime | None:
    value = task.get("due_at")
    if value in (None, ""):
        return None
    return _aware(value, "task.due_at").astimezone(timezone.utc)


def _validate_windows(windows: list[dict]) -> list[dict]:
    normalized = []
    for index, window in enumerate(windows or []):
        start = _aware(window.get("start"), f"availability[{index}].start")
        end = _aware(window.get("end"), f"availability[{index}].end")
        if end <= start:
            raise ValueError(f"availability[{index}] end must follow start")
        normalized.append({"start": start, "end": end,
                           "source": window.get("source", "student")})
    normalized.sort(key=lambda item: item["start"].astimezone(timezone.utc))
    for previous, current in zip(normalized, normalized[1:]):
        if current["start"].astimezone(timezone.utc) < previous["end"].astimezone(timezone.utc):
            raise ValueError("availability windows must not overlap")
    return normalized


def build_adaptive_plan(
    tasks: list[dict],
    availability: list[dict],
    *,
    session_minutes: int = 25,
    daily_budget_minutes: int = 120,
    break_minutes: int = 5,
    now: str,
) -> dict:
    """Allocate verified tasks into available windows without overbooking.

    Each task requires: task_id, estimated_minutes, evidence_refs,
    evidence_verified=True, student_confirmed=True. Optional fields:
    course, topic, due_at (ISO-8601 with offset), priority (1..5).

    `now` is explicit and offset-aware so the result is reproducible.
    Sessions are emitted in UTC with the original local date retained.
    """
    instant = _aware(now, "now").astimezone(timezone.utc)
    if session_minutes < 1 or daily_budget_minutes < 1 or break_minutes < 0:
        raise ValueError("session, budget, and break values must be positive")
    if session_minutes > daily_budget_minutes:
        raise ValueError("session_minutes cannot exceed daily_budget_minutes")

    windows = _validate_windows(availability)
    eligible, excluded = [], []
    seen = set()
    for index, raw in enumerate(tasks or []):
        task = dict(raw)
        task_id = str(task.get("task_id") or "").strip()
        if not task_id:
            raise ValueError(f"tasks[{index}] requires task_id")
        if task_id in seen:
            raise ValueError(f"duplicate task_id: {task_id}")
        seen.add(task_id)
        estimate = task.get("estimated_minutes")
        if not isinstance(estimate, int) or isinstance(estimate, bool) or estimate < 1:
            raise ValueError(f"task {task_id} estimated_minutes must be a positive integer")
        if task.get("status") in {"complete", "cancelled"}:
            excluded.append({"task_id": task_id, "reason": "not-open"})
            continue
        if task.get("evidence_verified") is not True or task.get("student_confirmed") is not True:
            excluded.append({"task_id": task_id, "reason": "evidence-not-confirmed"})
            continue
        refs = task.get("evidence_refs")
        if not isinstance(refs, list) or not refs or not all(str(ref).strip() for ref in refs):
            excluded.append({"task_id": task_id, "reason": "missing-evidence-reference"})
            continue
        priority = task.get("priority", 3)
        if not isinstance(priority, int) or isinstance(priority, bool) or not 1 <= priority <= 5:
            raise ValueError(f"task {task_id} priority must be an integer from 1 to 5")
        task["_deadline"] = _deadline(task)
        task["_remaining"] = estimate
        task["_priority"] = priority
        eligible.append(task)

    # Due date first, then priority, then stable id. No random or wall-clock input.
    eligible.sort(key=lambda task: (
        task["_deadline"] or datetime.max.replace(tzinfo=timezone.utc),
        -task["_priority"], str(task["task_id"])))

    cursors = [window["start"] for window in windows]
    sessions, daily_used = [], {}
    unscheduled = []
    for task in eligible:
        remaining = task["_remaining"]
        task_sessions = 0
        for index, window in enumerate(windows):
            cursor = cursors[index]
            end = window["end"]
            while remaining > 0:
                utc_cursor = cursor.astimezone(timezone.utc)
                utc_end = end.astimezone(timezone.utc)
                if utc_cursor >= utc_end:
                    break
                if utc_cursor < instant:
                    cursor = instant.astimezone(cursor.tzinfo)
                    utc_cursor = cursor.astimezone(timezone.utc)
                local_day = cursor.date().isoformat()
                budget_left = daily_budget_minutes - daily_used.get(local_day, 0)
                if budget_left <= 0:
                    break
                available = int((utc_end - utc_cursor).total_seconds() // 60)
                if available <= 0:
                    break
                duration = min(session_minutes, remaining, budget_left, available)
                if duration <= 0:
                    break
                finish = cursor + timedelta(minutes=duration)
                deadline = task["_deadline"]
                if deadline and finish.astimezone(timezone.utc) > deadline:
                    break
                sessions.append({
                    "session_id": f"{task['task_id']}:{task_sessions + 1}",
                    "task_id": task["task_id"],
                    "course": task.get("course"),
                    "topic": task.get("topic"),
                    "start": cursor.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "end": finish.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "local_date": local_day,
                    "duration_minutes": duration,
                    "evidence_refs": list(task["evidence_refs"]),
                    "rationale": {
                        "priority": task["_priority"],
                        "due_at": task.get("due_at"),
                        "availability_source": window["source"],
                    },
                })
                daily_used[local_day] = daily_used.get(local_day, 0) + duration
                remaining -= duration
                task_sessions += 1
                cursor = finish + timedelta(minutes=break_minutes)
            cursors[index] = cursor
            if remaining <= 0:
                break
        if remaining > 0:
            unscheduled.append({
                "task_id": task["task_id"],
                "remaining_minutes": remaining,
                "reason": "insufficient-available-time-or-deadline-window",
            })

    sessions.sort(key=lambda item: item["start"])
    return {
        "schema": SCHEMA,
        "as_of": instant.isoformat().replace("+00:00", "Z"),
        "sessions": sessions,
        "scheduled_minutes": sum(s["duration_minutes"] for s in sessions),
        "unscheduled": unscheduled,
        "excluded": excluded,
        "daily_minutes": dict(sorted(daily_used.items())),
        "constraints": {
            "session_minutes": session_minutes,
            "daily_budget_minutes": daily_budget_minutes,
            "break_minutes": break_minutes,
            "availability_windows": len(windows),
        },
    }


def replan_after_missed(
    tasks: list[dict],
    availability: list[dict],
    *,
    missed_task_ids: list[str],
    now: str,
    **planner_options,
) -> dict:
    """Rebuild a plan with missed tasks returned to the open queue.

    The caller supplies current availability and the remaining estimates;
    completed tasks must remain marked complete. A receipt records exactly
    which task ids were reintroduced.
    """
    missed = {str(task_id) for task_id in (missed_task_ids or [])}
    updated = []
    for raw in tasks or []:
        task = dict(raw)
        if str(task.get("task_id")) in missed and task.get("status") != "complete":
            task["status"] = "open"
        updated.append(task)
    result = build_adaptive_plan(
        updated, availability, now=now, **planner_options)
    result["recovery"] = {
        "missed_task_ids": sorted(missed),
        "policy": "recompute-from-current-availability",
    }
    return result
