# Architecture

Agent Review Ledger separates deterministic workflow state from agent or model behavior.

```text
operator / agent adapter
          |
          v
  public Python API or CLI
          |
          v
 Store + deterministic gates
          |
          v
     local SQLite
   tasks + events
```

The optional console is a thin loopback HTTP interface over the same `Store`. The core never calls a model provider or performs an external action.

## State machine

```text
backlog ──> in_progress ──> review ──> done
   |             |            |
   v             v            v
blocked <────────┴────────────┘
   └────────> backlog or in_progress
```

A task can reach `done` only from `review`, and only with nonblank evidence. Task mutations and their event entries commit in one SQLite transaction.

## Candidate gate

`evaluate_candidate` is a pure function. Eligibility requires strict score improvement, zero regressions, cost within budget, independent review, and a passing holdout. It does not run evaluations or verify the supplied values.

## Data format

Schema version `1` contains `metadata`, `tasks`, and append-only-by-convention `events` tables. `Store.export()` returns a versioned JSON-serializable snapshot. SQLite itself does not prevent a user with filesystem access from altering records.
