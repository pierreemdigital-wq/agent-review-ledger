# Threat model

## Intended environment

A trusted developer or researcher runs the library and optional console on a single local machine. Inputs and test data are synthetic or explicitly approved for local storage.

## Protected properties

- Task and event mutations are committed atomically.
- Invalid state transitions, over-budget costs, and completion without evidence are rejected.
- The console listens only on IPv4 loopback.
- Browser mutations require an exact local Origin, Host, JSON content type, and per-process random token.
- Responses disable caching and apply a restrictive Content Security Policy.

## Not protected against

- A local process or user that can read or modify the database file.
- Malware, a compromised browser, or a compromised operating system.
- Exposure introduced by a reverse proxy, tunnel, port forward, or container mapping.
- False, misleading, sensitive, or malicious text submitted as evidence.
- Replay or duplication after a client loses a response.
- Real spending by an external model or cloud provider.
- Multi-user or multi-tenant access.

## Safe use

Do not store secrets, personal information, client records, production prompts, or credentials. Keep database permissions restrictive. Back up only when the data is appropriate to retain. Integrators adding external actions must implement authentication, authorization, approval, idempotency, read-back verification, and rollback outside this core.
