"""Complete synthetic workflow using only a temporary local database."""

from pathlib import Path
import tempfile

from agent_review_ledger import Store, evaluate_candidate

with tempfile.TemporaryDirectory() as directory:
    store = Store(Path(directory) / "example.sqlite3")
    task = store.create_task("example", "Verify change", "maintainer", "All synthetic tests pass", 50)
    store.transition(task["id"], "in_progress")
    store.add_cost(task["id"], 5)
    store.transition(task["id"], "review", evidence="Synthetic test report: pass")
    store.transition(task["id"], "done")
    print(store.export())

print(evaluate_candidate(0.7, 0.8, 0, 5, 50, True, True))
