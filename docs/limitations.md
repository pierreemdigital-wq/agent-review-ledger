# Limitations

- Evidence is text supplied by a caller; the project does not verify that it is true.
- The event ledger is transactional but not tamper-proof or cryptographically signed.
- Budgets and costs are declared local records; they do not control provider billing.
- Project filters are organizational conveniences, not tenant isolation.
- Reviewer identity is not authenticated.
- The console is single-user and loopback-only, with no accounts, RBAC, or TLS.
- SQLite schema migration support is limited to rejecting unknown versions in v0.1.
- No connector, model provider, external executor, or autonomous action is included.
- Concurrent multi-process workloads and high availability are outside the current scope.
- This project is not a compliance certification or production authorization boundary.
