# Artifact Passport Toolkit — Current Handoff

**Version:** 0.7.1  
**Status:** Experimental public package. New descriptions are an AI draft; Wakka approved public distribution and MIT licensing.

## Purpose

Carry durable project identity, intent, constraints, and verification alongside a replaceable current-state Handoff. The optional Run Receipt supports measured handoff comparisons.

## Start here

Read `AP-PROTOCOL.md`, `artifact-passport.json`, and `artifact-handoff.json`. Use `README.md` to try the toolkit and see the included example.

## Current state

**Status:** Release 0.7.1 is prepared for public sharing under MIT. Application sources are unchanged. Automated checks pass; manual Studio browser interaction remains outstanding.

**Known good:** Validator and comparator self-tests, headless Studio regression, JavaScript syntax, JSON parsing, and core root-document validation pass. Tools, tests, templates, and schemas match the supplied v0.7.0 bytes. Manual Studio browser interaction remains outstanding. See VERIFICATION.md.

**Latest change:** Added MIT licensing, public README, minimal-example guide, and aligned the sample Passport/Handoff name and version.

**Objective:** Publish the prepared public repository and release so people can try Artifact Passport.

**Next move:** Create the public artifact-passport repository, upload the prepared files, and publish the packaged release. The maintainer upload kit provides exact browser steps.

## Context snapshot

### Do not break

- Passports, handoffs, and run receipts remain descriptive and non-executable.
- The v0.6 context fields remain first-class: do_not_break, decision_history, known_uncertainties, recent_delta_from, and recent_delta.
- Host token, credit, timing, and action data must be recorded only when observed; unavailable values stay null or unavailable.
- Efficiency claims require a matched control and Passport condition over the same underlying artifact and prompt.

### Decision history

- v0.5 separated durable Passport intent from replaceable current-state Handoff and added context routing.
- v0.6 added an explicit context_snapshot to carry fragile decisions, deltas, and uncertainties without forcing the next AI to rediscover them.
- v0.7 treats benchmark telemetry as an optional observation receipt rather than embedding historical measurements into the durable Passport or current-state Handoff.
- On 2026-10-03, Wakka chose a public repository with MIT licensing; forks are independent of the official repository.

### Known uncertainties

- Cross-host action counting is only comparable when the evaluator follows the same counting rules.
- Token and credit counters are host-specific and may be unavailable; they are secondary metrics rather than the core benchmark.
- More repeated trials are needed before claiming a general efficiency effect outside the tested artifacts and models.

### Recent changes

From: Artifact Passport Toolkit v0.7.0

- Added MIT license at the owner’s request.
- Rewrote the front page for people encountering Passport for the first time.
- Featured the existing examples and handoff test.
- Aligned the minimal example’s name and version between its Passport and Handoff.
- Preserved all Studio, validator, comparator, schema, and regression-test sources.

## Reading routes

- **Use or evaluate the toolkit:** `README.md`, `HANDOFF_TEST.md`
- **Change the contract:** `SPECIFICATION.md`, `artifact-passport.schema.json`, `artifact-handoff.schema.json`
- **Change the Studio:** `tools/Artifact-Passport-Studio-v0.7.html`, `tools/passport-studio-v0.7.js`, `tests/test_studio_intake.js`
- **Verify or package a release:** `README.md`, `tools/validate_passport.py`, `tests/test_studio_intake.js`
- **Measure handoff efficiency:** `HANDOFF_TEST.md`, `artifact-passport-run.schema.json`, `templates/artifact-passport-run.template.json`, `tools/compare_handoff_runs.py`
- **Understand public permissions and release checks:** `LICENSE`, `README.md`, `VERIFICATION.md`, `CHANGELOG.md`

## Authority and permissions

Wakka maintains the official repository and decides which contributions enter it. Independent use, modification, and redistribution are permitted under LICENSE. A Passport never grants access or execution authority for other artifacts.

Public sharing of this toolkit does not authorize disclosure or modification of private artifacts supplied to it.

## Verification

See `VERIFICATION.md` for checks performed on release 0.7.1. Run the existing validator, comparator, and Studio regression suites before changing application logic.

## Boundaries

- No cryptographic binding or authenticated owner identity.
- Inventory fingerprints detect file-list and size drift, not byte-level integrity of every artifact file.
- ZIP intake does not support encrypted, multi-disk, ZIP64, or unsupported-compression entries.
- Intake uses deterministic metadata recognition rather than remote semantic AI analysis.
- The Python validator validates core semantics; the JSON Schemas remain normative.
- A visual A/B field test has been observed, but no complete v0.7 paired Run Receipt has yet been recorded.
- The working name has not been cleared for trademark or product use.

Passports, Handoffs, and Run Receipts are descriptive, not executable. No signing keys are generated or distributed.
