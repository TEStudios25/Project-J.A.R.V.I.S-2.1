import threading
import time
from datetime import datetime

from core.scheduler import get_due_reminders, mark_reminder_notified
from senses.tts_engine import speak


class ReminderService:
    """Background daemon that speaks reminders when scheduled times arrive."""

    def __init__(self, on_reminder=None, poll_seconds: int = 20):
        self.on_reminder = on_reminder
        self.poll_seconds = poll_seconds
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[⏰ Reminder service online.]")

    def stop(self):
        self._stop_event.set()

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                due_items = get_due_reminders()
                for item in due_items:
                    message = (
                        f"Sir, this is your scheduled reminder. "
                        f"At {item['time']}, you asked me to remind you: {item['task']}."
                    )
                    print(f"\n[⏰ REMINDER]: {message}")
                    if self.on_reminder:
                        self.on_reminder(message)
                    speak(message)
                    time.sleep(1.0)
                    mark_reminder_notified(item["id"])
            except Exception as exc:
                print(f"[Reminder service warning]: {exc}")

            self._stop_event.wait(self.poll_seconds)
