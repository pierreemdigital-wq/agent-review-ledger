# Security policy

## Supported versions

Agent Review Ledger is experimental. Security fixes are applied to the latest release only.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub private vulnerability reporting when enabled, or contact the maintainer privately through the repository owner's GitHub profile. Include affected version, reproduction steps, impact, and any suggested mitigation. Do not include real credentials or client data.

## Security boundary

The bundled console binds to `127.0.0.1` and is designed for one trusted local operator. It does not provide accounts, authentication, authorization, TLS, tenant isolation, or an immutable audit trail. Do not expose it through a tunnel, proxy, or public interface.

See [docs/threat-model.md](docs/threat-model.md) for assumptions and exclusions.
