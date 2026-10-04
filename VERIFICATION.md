# Verification — release 0.7.1

Checked during public-release preparation on October 3, 2026 (America/Chicago).

| Check | Result |
| --- | --- |
| Dependency-free validator self-test | PASS; positive fixtures accepted and intentionally invalid fixtures rejected. |
| Paired-run comparator self-test | PASS. |
| Headless Studio regression suite | PASS for intake, ZIP safety, repair, context snapshot, routing, and naming. |
| JavaScript syntax | PASS. |
| Root Passport, root Handoff, and run-receipt template | Accepted by the dependency-free validator. The root Passport has one expected warning because revised descriptions remain an AI draft. |
| All toolkit JSON files | Parse successfully. |
| Application-source preservation | Tools, tests, templates, and schemas are byte-for-byte identical to the supplied v0.7.0 archive. |
| Local Markdown links | Resolve to included files. |

The tests exercise the Studio logic in a headless JavaScript environment. They do not establish that every browser control, folder picker, or download works end to end in a real browser.

Manual Studio browser interaction remains outstanding. The current environment did not provide an installed browser executable for a browser smoke test. No manual browser verification is claimed.

No fresh controlled A/B trial was run while preparing this release. The bundled comparison tool and test protocol are available for that evaluation; no general efficiency result is claimed.

## Reproduce the core checks

From the project folder:

```text
python tools/validate_passport.py --self-test
python tools/compare_handoff_runs.py --self-test
node tests/test_studio_intake.js
node --check tools/passport-studio-v0.7.js
python tools/validate_passport.py artifact-passport.json artifact-handoff.json templates/artifact-passport-run.template.json
```

The original release's historical evidence is retained in the project Handoff. It is separate from checks performed on this public package.
