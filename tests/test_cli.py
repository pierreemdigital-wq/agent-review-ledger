import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from agent_review_ledger.cli import main


class CliTests(unittest.TestCase):
    def capture(self, argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(argv)
        return output.getvalue()

    def test_demo_runs_complete_reviewed_workflow(self):
        data = json.loads(self.capture(["demo"]))
        self.assertEqual(data["summary"]["by_status"]["done"], 1)
        self.assertTrue(data["candidate_gate"]["eligible"])
        self.assertEqual(len(data["events"]), 5)

    def test_export_reads_explicit_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.sqlite3"
            data = json.loads(self.capture(["export", "--db", str(path)]))
            self.assertEqual(data["tasks"], [])
            self.assertEqual(data["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
