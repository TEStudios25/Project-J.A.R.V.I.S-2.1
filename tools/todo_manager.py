import os
import json

TODO_PATH = os.path.join("data", "todos.json")

def load_todos() -> list:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(TODO_PATH):
        # Default starter tasks
        default_todos = [
            {"task": "Synchronize J.A.R.V.I.S. Core controls", "completed": True},
            {"task": "Establish active mobile link node", "completed": True},
            {"task": "Run storage cleaner routine", "completed": False}
        ]
        with open(TODO_PATH, "w", encoding="utf-8") as f:
            json.dump(default_todos, f, indent=2)
        return default_todos
    try:
        with open(TODO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_todos(todos: list):
    with open(TODO_PATH, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2)

def add_todo_item(task: str) -> str:
    """Adds a new task to your active system todo checklist."""
    task = task.strip()
    if not task:
        return "Error: Cannot add an empty task, sir."
    todos = load_todos()
    todos.append({"task": task, "completed": False})
    save_todos(todos)
    return f"Successfully added task: '{task}' to your active todo list."

def complete_todo_item(task_keyword: str) -> str:
    """Marks a task matching the given keyword as completed on your todo list."""
    task_keyword = task_keyword.lower().strip()
    todos = load_todos()
    found = False
    for t in todos:
        if task_keyword in t["task"].lower() and not t["completed"]:
            t["completed"] = True
            found = True
            save_todos(todos)
            return f"Successfully completed task: '{t['task']}'."
    if found:
        return "Task marked as completed, sir."
    return f"I could not find any active, uncompleted task matching the keyword '{task_keyword}'."

def get_todo_list() -> str:
    """Returns a formatted list of all pending and completed items on your checklist."""
    todos = load_todos()
    if not todos:
        return "Your todo checklist is currently empty, Mr. Pranav."
    report = "Active System Todo Checklist:\n"
    for idx, t in enumerate(todos, 1):
        status = "[x]" if t["completed"] else "[ ]"
        report += f"{idx}. {status} {t['task']}\n"
    return report
