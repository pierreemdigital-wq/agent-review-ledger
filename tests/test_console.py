import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from agent_review_ledger import Store
from agent_review_ledger.console import create_server


class ConsoleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "console.sqlite3"
        self.server = create_server(Store(self.path), port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:%s" % self.server.server_port
        self.addCleanup(self.close_server)

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def post(self, route, payload, headers):
        return urlopen(Request(self.base + route, data=json.dumps(payload).encode(), headers=headers))

    def test_real_store_flow_and_security_headers(self):
        with urlopen(self.base + "/api/state") as response:
            state = json.load(response)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
        headers = {"Origin": self.base, "Content-Type": "application/json", "X-Console-Token": state["csrf"]}
        with self.post("/api/tasks", {
            "project": "synthetic", "title": "Fixture", "owner": "test",
            "acceptance": "Assertions pass", "budget_cents": 100,
        }, headers) as response:
            task = json.load(response)
        self.post("/api/transition", {"task_id": task["id"], "status": "in_progress"}, headers).close()
        self.post("/api/transition", {"task_id": task["id"], "status": "review", "evidence": "synthetic pass"}, headers).close()
        self.post("/api/transition", {"task_id": task["id"], "status": "done"}, headers).close()
        self.assertEqual(Store(self.path).list_tasks()[0]["status"], "done")

    def test_rejects_foreign_origin_host_and_path_traversal(self):
        state = json.load(urlopen(self.base + "/api/state"))
        payload = {"project": "x"}
        with self.assertRaises(HTTPError) as error:
            self.post("/api/tasks", payload, {"Origin": "https://evil.example"})
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base + "/api/state", headers={"Host": "evil.example"}))
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + "/../store.py")
        self.assertEqual(error.exception.code, 404)

    def test_serves_packaged_console_assets(self):
        with urlopen(self.base + "/") as response:
            self.assertIn(b"Agent Review Ledger", response.read())
        with urlopen(self.base + "/app.js") as response:
            self.assertIn(b"use strict", response.read())


if __name__ == "__main__":
    unittest.main()
