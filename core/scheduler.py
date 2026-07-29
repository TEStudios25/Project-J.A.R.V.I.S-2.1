import os
import sys
import json
import uuid
from datetime import datetime

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

SCHEDULE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "schedule.json")


def _ensure_schedule_file():
    os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)


def _load_schedule() -> dict:
    _ensure_schedule_file()
    if not os.path.exists(SCHEDULE_FILE):
        return {"recurring": []}
    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "recurring" not in data:
                data["recurring"] = []
            return data
    except json.JSONDecodeError:
        return {"recurring": []}


def _save_schedule(data: dict) -> None:
    _ensure_schedule_file()
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _parse_time_to_minutes(time_str: str) -> int | None:
    raw = time_str.strip().upper().replace(".", "")
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p", "%I %p", "%I%p"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue
    return None


def add_reminder(task: str, time_str: str) -> str:
    """Saves a single reminder task with a time in HH:MM or 05:00 PM format for today."""
    print(f"\n[📆 J.A.R.V.I.S. is logging a new reminder: '{task}' at {time_str}...]")

    schedule_data = _load_schedule()
    today = datetime.now().strftime("%Y-%m-%d")

    if today not in schedule_data:
        schedule_data[today] = []

    schedule_data[today].append(
        {
            "id": str(uuid.uuid4()),
            "time": time_str,
            "task": task,
            "status": "pending",
        }
    )
    _save_schedule(schedule_data)
    return f"Successfully logged reminder: '{task}' scheduled for {time_str} today."


def add_recurring_task(task: str, time_str: str, days_filter: str = "daily") -> str:
    """
    Saves a recurring cron routine (e.g. 'every weekday at 8 PM', 'every Sunday at midnight').
    days_filter options: 'daily', 'weekdays', 'weekends', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
    """
    print(f"\n[🔁 J.A.R.V.I.S. is setting up a recurring routine: '{task}' ({days_filter} at {time_str})...]")

    schedule_data = _load_schedule()
    schedule_data["recurring"].append(
        {
            "id": str(uuid.uuid4()),
            "time": time_str,
            "task": task,
            "days": days_filter.lower(),
            "last_notified_date": ""
        }
    )
    _save_schedule(schedule_data)
    return f"Successfully established recurring routine: '{task}' set for {days_filter} at {time_str}."


def get_today_schedule() -> str:
    """Returns all tasks (one-time and recurring) scheduled for today."""
    print("\n[📆 J.A.R.V.I.S. is checking today's calendar...]")
    schedule_data = _load_schedule()
    today = datetime.now().strftime("%Y-%m-%d")
    today_tasks = schedule_data.get(today, [])
    recurring_tasks = schedule_data.get("recurring", [])

    weekday_name = datetime.now().strftime("%A").lower()
    is_weekend = weekday_name in ["saturday", "sunday"]

    active_recurring = []
    for r in recurring_tasks:
        d = r.get("days", "daily")
        if d == "daily":
            active_recurring.append(r)
        elif d == "weekdays" and not is_weekend:
            active_recurring.append(r)
        elif d == "weekends" and is_weekend:
            active_recurring.append(r)
        elif d == weekday_name:
            active_recurring.append(r)

    if not today_tasks and not active_recurring:
        return "You have no tasks or recurring routines scheduled for today, Mr. Pranav."

    report = "Here is your scheduled itinerary for today:\n"
    for item in today_tasks:
        report += f"- [{item['time']}] {item['task']} ({item['status']})\n"
    for item in active_recurring:
        report += f"- [{item['time']}] 🔁 Recurring: {item['task']}\n"

    return report


def get_due_reminders() -> list[dict]:
    """Returns pending reminders and due recurring routines whose scheduled time has arrived."""
    schedule_data = _load_schedule()
    today = datetime.now().strftime("%Y-%m-%d")
    now_minutes = datetime.now().hour * 60 + datetime.now().minute
    weekday_name = datetime.now().strftime("%A").lower()
    is_weekend = weekday_name in ["saturday", "sunday"]

    due = []
    changed = False

    # 1. One-time reminders
    for item in schedule_data.get(today, []):
        if not item.get("id"):
            item["id"] = str(uuid.uuid4())
            changed = True
        if item.get("status") != "pending":
            continue
        target = _parse_time_to_minutes(item.get("time", ""))
        if target is None:
            continue
        if target <= now_minutes:
            due.append(item)

    # 2. Recurring tasks
    for r in schedule_data.get("recurring", []):
        d = r.get("days", "daily")
        is_today = (
            d == "daily" or
            (d == "weekdays" and not is_weekend) or
            (d == "weekends" and is_weekend) or
            (d == weekday_name)
        )
        if is_today and r.get("last_notified_date") != today:
            target = _parse_time_to_minutes(r.get("time", ""))
            if target is not None and target <= now_minutes:
                due.append({
                    "id": r["id"],
                    "time": r["time"],
                    "task": f"Recurring Routine: {r['task']}",
                    "is_recurring": True
                })

    if changed:
        _save_schedule(schedule_data)

    return due


def mark_reminder_notified(reminder_id: str) -> None:
    schedule_data = _load_schedule()
    today = datetime.now().strftime("%Y-%m-%d")

    for item in schedule_data.get(today, []):
        if item.get("id") == reminder_id:
            item["status"] = "notified"
            _save_schedule(schedule_data)
            return

    for item in schedule_data.get("recurring", []):
        if item.get("id") == reminder_id:
            item["last_notified_date"] = today
            _save_schedule(schedule_data)
            return
