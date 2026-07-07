import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
MAX_TURNS = 40


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_memory() -> dict:
    _ensure_data_dir()
    if not os.path.exists(MEMORY_FILE):
        return {"profile": {}, "conversations": []}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"profile": {}, "conversations": []}


def save_memory(data: dict) -> None:
    _ensure_data_dir()
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def remember_turn(user_text: str, assistant_text: str) -> None:
    data = load_memory()
    data.setdefault("conversations", []).append(
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "user": user_text,
            "assistant": assistant_text,
        }
    )
    if len(data["conversations"]) > MAX_TURNS:
        data["conversations"] = data["conversations"][-MAX_TURNS:]
    save_memory(data)


def remember_fact(key: str, value: str) -> str:
    data = load_memory()
    profile = data.setdefault("profile", {})
    profile[key.strip().lower()] = value.strip()
    save_memory(data)
    return f"Noted, sir. I will remember that your {key} is {value}."


def get_memory_context(limit: int = 8) -> str:
    data = load_memory()
    lines = []

    profile = data.get("profile", {})
    if profile:
        lines.append("Known user facts:")
        for key, value in profile.items():
            lines.append(f"- {key}: {value}")

    recent = data.get("conversations", [])[-limit:]
    if recent:
        lines.append("Recent conversation context:")
        for turn in recent:
            lines.append(f"User: {turn.get('user', '')}")
            lines.append(f"JARVIS: {turn.get('assistant', '')}")

    return "\n".join(lines) if lines else "No stored memory yet."
