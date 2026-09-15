import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from uuid import UUID

from agent_review_ledger import SCHEMA_VERSION, Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "state.sqlite3"
        self.store = Store(self.path)

    def create(self, budget=100):
        return self.store.create_task("demo", "Synthetic task", "operator", "Tests pass", budget)

    def test_create_persists_filters_and_exports(self):
        task = self.create()
        self.assertEqual(str(UUID(task["id"])), task["id"])
        self.assertEqual(Store(self.path).list_tasks(), [task])
        self.assertEqual(self.store.list_tasks("absent"), [])
        exported = self.store.export()
        self.assertEqual(exported["schema_version"], SCHEMA_VERSION)
        self.assertEqual(exported["tasks"], [task])
        self.assertEqual(exported["events"][0]["details"]["title"], "Synthetic task")

    def test_invalid_creation_is_rejected_without_writes(self):
        for path in (None, "", " ", ":memory:", 123, b"file"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                Store(path)
        valid = {"project": "demo", "title": "Task", "owner": "operator", "acceptance": "Test"}
        for field in valid:
            for bad in ("", "  ", None, 1, True, []):
                with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                    self.store.create_task(**dict(valid, **{field: bad}))
        for bad in (-1, True, 1.0, "1", None, 2**63):
            with self.assertRaises(ValueError):
                self.store.create_task(**valid, budget_cents=bad)
        self.assertEqual(self.store.list_tasks(), [])

    def test_transition_requires_review_and_evidence(self):
        task = self.create()
        with self.assertRaises(ValueError):
            self.store.transition(task["id"], "done", "cannot skip")
        self.store.transition(task["id"], "in_progress")
        self.store.transition(task["id"], "review")
        with self.assertRaises(ValueError):
            self.store.transition(task["id"], "done")
        self.store.transition(task["id"], "in_progress")
        self.store.transition(task["id"], "review", "Synthetic test log")
        done = self.store.transition(task["id"], "done")
        self.assertEqual(done["status"], "done")
        self.assertEqual(done["evidence"], "Synthetic test log")

    def test_cost_ceiling_is_atomic(self):
        task = self.create(100)
        self.assertEqual(self.store.add_cost(task["id"], 40)["cost_cents"], 40)
        self.assertEqual(self.store.add_cost(task["id"], 60)["cost_cents"], 100)
        with self.assertRaises(ValueError):
            self.store.add_cost(task["id"], 1)
        self.assertEqual(Store(self.path).list_tasks()[0]["cost_cents"], 100)

    def test_ledger_rolls_back_when_event_write_fails(self):
        task = self.create(10)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER fail_event BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END")
        before = self.store.list_tasks()
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.add_cost(task["id"], 1)
        self.assertEqual(self.store.list_tasks(), before)

    def test_summary_reports_all_statuses(self):
        self.assertEqual(self.store.summary()["total_tasks"], 0)
        task = self.create(100)
        self.store.add_cost(task["id"], 10)
        summary = self.store.summary()
        self.assertEqual(summary["total_tasks"], 1)
        self.assertEqual(summary["cost_cents"], 10)
        self.assertEqual(summary["remaining_cents"], 90)

    def test_unknown_schema_is_rejected(self):
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE metadata SET value = '999' WHERE key = 'schema_version'")
        with self.assertRaisesRegex(RuntimeError, "unsupported schema"):
            Store(self.path)

    def test_event_filter_validates_uuid(self):
        task = self.create()
        self.assertEqual(len(self.store.list_events(task["id"])), 1)
        with self.assertRaises(ValueError):
            self.store.list_events("not-a-uuid")


if __name__ == "__main__":
    unittest.main()
