import os
import json
import uuid
from datetime import datetime

SCHEDULE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "schedule.json")


def _ensure_schedule_file():
    os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)


def _load_schedule() -> dict:
    _ensure_schedule_file()
    if not os.path.exists(SCHEDULE_FILE):
        return {}
    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


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
    """Saves a reminder task with a time in HH:MM or 05:00 PM format."""
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


def get_today_schedule() -> str:
    """Returns all tasks scheduled for today."""
    print("\n[📆 J.A.R.V.I.S. is checking today's calendar...]")
    schedule_data = _load_schedule()
    today = datetime.now().strftime("%Y-%m-%d")
    today_tasks = schedule_data.get(today, [])

    if not today_tasks:
        return "You have no tasks scheduled for today, Mr. Pranav."

    report = "Here is your scheduled itinerary for today:\n"
    for item in today_tasks:
        report += f"- [{item['time']}] {item['task']} ({item['status']})\n"
    return report


def get_due_reminders() -> list[dict]:
    """Returns pending reminders whose scheduled time has arrived."""
    schedule_data = _load_schedule()
    today = datetime.now().strftime("%Y-%m-%d")
    now_minutes = datetime.now().hour * 60 + datetime.now().minute
    due = []
    changed = False

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

    if changed:
        _save_schedule(schedule_data)

    return due


def mark_reminder_notified(reminder_id: str) -> None:
    schedule_data = _load_schedule()
    today = datetime.now().strftime("%Y-%m-%d")

    for item in schedule_data.get(today, []):
        if item.get("id") == reminder_id:
            item["status"] = "notified"
            break

    _save_schedule(schedule_data)
