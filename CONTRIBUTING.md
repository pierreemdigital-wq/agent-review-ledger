# Contributing

Thank you for helping improve Agent Review Ledger.

## Before opening a change

- Search existing issues and discussions.
- Keep changes provider-neutral and local-first unless an issue explicitly expands scope.
- Never include credentials, personal data, client data, production records, or proprietary evaluation sets.
- Use synthetic fixtures in tests and examples.

## Development

```bash
python -m pip install .
python -m unittest discover -s tests -v
python -m compileall -q src tests examples
python -m agent_review_ledger demo
```

The runtime has no third-party dependencies. Tests must not call external networks or model providers.

## Pull requests

1. Explain the problem and the smallest change that solves it.
2. Add or update tests for behavior changes.
3. Update documentation when the public API or security boundary changes.
4. Confirm the test suite passes.
5. Certify the contribution with a Developer Certificate of Origin sign-off:

```bash
git commit -s -m "type: concise description"
```

By signing off, you certify the contribution under the [Developer Certificate of Origin 1.1](https://developercertificate.org/).

## Scope

Good first contributions include portability fixes, documentation, synthetic edge cases, export formats, and schema-migration design. External execution, credentials, production authentication, and multi-tenancy require prior design discussion.
