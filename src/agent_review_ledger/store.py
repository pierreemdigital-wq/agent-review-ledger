"""Local task and event storage. No execution or external integrations."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import UUID, uuid4

SCHEMA_VERSION = 1
TRANSITIONS = {
    "backlog": ("in_progress", "blocked"),
    "in_progress": ("review", "blocked"),
    "review": ("done", "in_progress", "blocked"),
    "blocked": ("backlog", "in_progress"),
    "done": (),
}


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + " must be nonblank text")


def _cents(value, name):
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError(name + " must be an integer in [0, 2**63-1]")


class Store:
    """Persistent SQLite ledger for reviewed work items."""

    def __init__(self, path):
        if not isinstance(path, (str, Path)):
            raise ValueError("path must be a string or pathlib.Path")
        _text(str(path), "path")
        if str(path) == ":memory:" or "\x00" in str(path):
            raise ValueError("path must name a persistent SQLite file")
        self.path = str(Path(path).expanduser().absolute())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            row = db.execute("SELECT value FROM metadata WHERE key = 'schema_version'").fetchone()
            if row is None:
                db.execute("INSERT INTO metadata VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
            elif row[0] != str(SCHEMA_VERSION):
                raise RuntimeError("unsupported schema version: " + row[0])
            db.execute("""CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, project TEXT NOT NULL, title TEXT NOT NULL,
                owner TEXT NOT NULL, acceptance TEXT NOT NULL,
                budget_cents INTEGER NOT NULL, cost_cents INTEGER NOT NULL,
                status TEXT NOT NULL, evidence TEXT)""")
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
                task_id TEXT NOT NULL, project TEXT NOT NULL,
                action TEXT NOT NULL, details TEXT NOT NULL)""")

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def create_task(self, project, title, owner, acceptance, budget_cents=0, evidence=None):
        for name, value in (
            ("project", project),
            ("title", title),
            ("owner", owner),
            ("acceptance", acceptance),
        ):
            _text(value, name)
        _cents(budget_cents, "budget_cents")
        if evidence is not None:
            _text(evidence, "evidence")
        task = {
            "id": str(uuid4()),
            "project": project,
            "title": title,
            "owner": owner,
            "acceptance": acceptance,
            "budget_cents": budget_cents,
            "cost_cents": 0,
            "status": "backlog",
            "evidence": evidence,
        }
        with self._connection() as db:
            db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(task.values()))
            self._event(db, task, "create_task", task)
        return task

    def list_tasks(self, project=None):
        if project is not None:
            _text(project, "project")
        with self._connection() as db:
            if project is None:
                rows = db.execute("SELECT * FROM tasks ORDER BY rowid")
            else:
                rows = db.execute("SELECT * FROM tasks WHERE project = ? ORDER BY rowid", (project,))
            return [dict(row) for row in rows]

    def list_events(self, task_id=None):
        with self._connection() as db:
            if task_id is None:
                rows = db.execute("SELECT * FROM events ORDER BY id")
            else:
                self._validate_task_id(task_id)
                rows = db.execute("SELECT * FROM events WHERE task_id = ? ORDER BY id", (task_id,))
            result = []
            for row in rows:
                item = dict(row)
                item["details"] = json.loads(item["details"])
                result.append(item)
            return result

    def summary(self):
        tasks = self.list_tasks()
        counts = dict.fromkeys(TRANSITIONS, 0)
        for task in tasks:
            counts[task["status"]] += 1
        budget = sum(task["budget_cents"] for task in tasks)
        cost = sum(task["cost_cents"] for task in tasks)
        return {
            "total_tasks": len(tasks),
            "by_status": counts,
            "budget_cents": budget,
            "cost_cents": cost,
            "remaining_cents": budget - cost,
        }

    def export(self):
        return {
            "schema_version": SCHEMA_VERSION,
            "tasks": self.list_tasks(),
            "events": self.list_events(),
            "summary": self.summary(),
        }

    def _event(self, db, task, action, details):
        db.execute(
            "INSERT INTO events (timestamp, task_id, project, action, details) VALUES (?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                task["id"],
                task["project"],
                action,
                json.dumps(details, ensure_ascii=False, sort_keys=True),
            ),
        )

    def _validate_task_id(self, task_id):
        _text(task_id, "task_id")
        try:
            canonical = str(UUID(task_id))
        except (ValueError, AttributeError, TypeError):
            raise ValueError("task_id must be a canonical lowercase UUID")
        if canonical != task_id:
            raise ValueError("task_id must be a canonical lowercase UUID")

    def _task(self, db, task_id):
        self._validate_task_id(task_id)
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(task_id)
        return dict(row)

    def add_cost(self, task_id, cents):
        _cents(cents, "cents")
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            task = self._task(db, task_id)
            total = task["cost_cents"] + cents
            if total > task["budget_cents"]:
                raise ValueError("cost exceeds task budget")
            db.execute("UPDATE tasks SET cost_cents = ? WHERE id = ?", (total, task_id))
            self._event(db, task, "add_cost", {"cents": cents, "cost_cents": total})
            return self._task(db, task_id)

    def transition(self, task_id, status, evidence=None):
        _text(status, "status")
        if status not in TRANSITIONS:
            raise ValueError("unknown status")
        if evidence is not None:
            _text(evidence, "evidence")
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            task = self._task(db, task_id)
            if status not in TRANSITIONS[task["status"]]:
                raise ValueError("transition not allowed")
            resolved_evidence = task["evidence"] if evidence is None else evidence
            if status == "done" and not resolved_evidence:
                raise ValueError("done requires evidence")
            db.execute(
                "UPDATE tasks SET status = ?, evidence = ? WHERE id = ?",
                (status, resolved_evidence, task_id),
            )
            self._event(
                db,
                task,
                "transition",
                {"from_status": task["status"], "to_status": status, "evidence": resolved_evidence},
            )
            return self._task(db, task_id)
