# Agent Review Ledger

[![CI](https://github.com/pierreemdigital-wq/agent-review-ledger/actions/workflows/ci.yml/badge.svg)](https://github.com/pierreemdigital-wq/agent-review-ledger/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

A local-first, provider-neutral control plane for evidence-backed, human-reviewed AI work.

Agent Review Ledger records work items, enforces explicit state transitions, tracks declared costs against task budgets, and prevents work from being marked done without review and evidence. It also provides a deterministic gate for comparing candidate changes against a baseline and holdout.

It does **not** execute agents, call model providers, or perform external actions.

## Why

AI-assisted workflows often blur the difference between:

- an agent saying that work is complete;
- a reviewer accepting the result;
- evidence that the acceptance criteria were met;
- a change being safe to promote.

Agent Review Ledger keeps those concepts separate and inspectable.

## Features

- local SQLite storage with no runtime dependencies;
- atomic task and event writes;
- explicit `backlog → in_progress → review → done` workflow;
- evidence required before completion;
- integer budget and declared-cost tracking;
- deterministic baseline, regression, budget, review, and holdout gate;
- JSON export for inspection and integration;
- optional loopback-only operator console;
- synthetic tests with no network or model credentials.

## Quick start

Requires Python 3.9 or newer.

```bash
python -m pip install .
arl demo
```

The demo creates a database in a temporary directory, runs a complete reviewed workflow, prints the resulting JSON, and deletes the temporary data.

### Python API

```python
from agent_review_ledger import Store, evaluate_candidate

store = Store("work.sqlite3")
task = store.create_task(
    project="demo",
    title="Evaluate a candidate workflow",
    owner="operator",
    acceptance="The synthetic test suite passes",
    budget_cents=100,
)
store.transition(task["id"], "in_progress")
store.add_cost(task["id"], 10)
store.transition(task["id"], "review", evidence="Synthetic test log: all checks passed")
done = store.transition(task["id"], "done")

result = evaluate_candidate(
    baseline_score=0.50,
    candidate_score=0.60,
    regressions=0,
    cost_cents=10,
    budget_cents=100,
    independent_review=True,
    holdout_passed=True,
)
assert done["status"] == "done"
assert result == {"eligible": True, "reasons": []}
```

### Local console

```bash
arl console --db ./work.sqlite3 --port 8767
```

Open `http://127.0.0.1:8767`. The console is for a trusted, single-user local machine only. Do not expose it through a proxy, tunnel, container port, or public interface.

### Export

```bash
arl export --db ./work.sqlite3 > ledger.json
```

## Design principles

1. Observable state over agent narration.
2. Deterministic gates before model judgment.
3. Review before completion.
4. Evidence references, not invented certainty.
5. Local-first storage and provider neutrality.
6. No external side effects in the core.
7. Explicit limitations over implied guarantees.

## Non-goals and limits

This project is not an agent framework, autonomous executor, production authorization system, tamper-proof audit log, or proof that submitted evidence is true. Declared costs do not limit real provider spend. See [docs/limitations.md](docs/limitations.md) and [docs/threat-model.md](docs/threat-model.md).

## Development

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests examples
python -m agent_review_ledger demo
```

All tests use temporary files, synthetic data, and loopback-only ephemeral ports.

## Project status

Experimental, pre-1.0. Suitable for local evaluation and integration prototyping; not production-ready for multi-user, multi-tenant, or external-action workflows.

## Contributing

Bug reports, documentation improvements, portability fixes, schema migration work, and synthetic test cases are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
