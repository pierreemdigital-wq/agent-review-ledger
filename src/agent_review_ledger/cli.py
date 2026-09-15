"""Command-line interface for local evaluation and export."""

import argparse
import json
from pathlib import Path
import tempfile

from .gates import evaluate_candidate
from .store import Store


def run_demo():
    with tempfile.TemporaryDirectory() as directory:
        store = Store(Path(directory) / "demo.sqlite3")
        task = store.create_task(
            project="demo",
            title="Evaluate a candidate workflow",
            owner="operator",
            acceptance="Synthetic checks pass",
            budget_cents=100,
        )
        store.transition(task["id"], "in_progress")
        store.add_cost(task["id"], 10)
        store.transition(task["id"], "review", evidence="Synthetic demo checks passed")
        store.transition(task["id"], "done")
        result = store.export()
        result["candidate_gate"] = evaluate_candidate(0.5, 0.6, 0, 10, 100, True, True)
        print(json.dumps(result, indent=2, sort_keys=True))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="arl",
        description="Evidence-backed, human-reviewed local work ledger.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="run a complete synthetic workflow in a temporary database")
    export = sub.add_parser("export", help="export tasks, events, and summary as JSON")
    export.add_argument("--db", required=True, help="local SQLite database path")
    console = sub.add_parser("console", help="run the single-user loopback console")
    console.add_argument("--db", required=True, help="local SQLite database path")
    console.add_argument("--port", default=8767, type=int, help="loopback port (default: 8767)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        run_demo()
    elif args.command == "export":
        print(json.dumps(Store(args.db).export(), indent=2, sort_keys=True))
    elif args.command == "console":
        from .console import create_server

        server = create_server(Store(args.db), port=args.port)
        print("Local console: http://127.0.0.1:%s" % server.server_port, flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
