# Changelog

## 0.7.1 — 2026-10-03

- Prepared the existing v0.7 toolkit for public sharing under the owner-approved MIT license.
- Rewrote README with a browser-first quick start, existing examples, current limits, and feedback instructions.
- Added a guide to the existing minimal example and aligned its Passport/Handoff name and version.
- Refreshed the toolkit’s own handoff and inventory fingerprint for this public package.
- Kept Studio, Python tools, schemas, templates, and regression tests unchanged.

## 0.7.0 — 2026-09-17

- Added an optional `artifact-passport-run.json` observation receipt for controlled handoff-efficiency measurement.
- Added `artifact-passport-run.schema.json` and a conforming run-receipt template.
- Standardized platform-agnostic metrics: orientation actions, verification actions, total tool actions, unique files read, unnecessary reads, clarification loops, backtracking, and observable timing.
- Added optional host-reported token, cache, reasoning-token, credit, and usage fields with explicit unavailable/not-recorded states; missing host telemetry must not be guessed.
- Added `tools/compare_handoff_runs.py`, including matched-pair comparability checks, a conservative quality gate, JSON output, and a dependency-free self-test.
- Reworked `HANDOFF_TEST.md` around the same neutral unfamiliar-project inspection prompt for both control and Passport conditions.
- Preserved the v0.6 `context_snapshot` contract and surfaced it in the Studio and generated `ARTIFACT.md`.
- Extended the Python validator and Studio regression suite for 0.7 handoffs, context snapshots, and run receipts.

## 0.6.0 — 2026-09-17

- Added `context_snapshot` to the current-state Handoff with `do_not_break`, `decision_history`, `known_uncertainties`, `recent_delta_from`, and `recent_delta`.
- Kept `working_state.current_status`, `working_state.current_objective`, and `context_routes` as the main orientation structure while giving the next AI compact project-continuity context.
- Updated Studio input/export, generated `ARTIFACT.md`, schemas, validator behavior, and migration defaults so v0.5 handoffs can move forward without silently inventing missing context.
- Expanded A/B evaluation to observe wrong assumptions, unnecessary file reading, clarification loops, backtracking, and time to a usable project model rather than scoring final correctness alone.

## 0.5.0 — 2026-09-13

- Reframed the product as an AI-to-AI continuity layer with explicit human review gates.
- Added local ZIP intake with central-directory bounds, path-traversal rejection, selective small-text extraction, and no execution.
- Added `artifact-handoff.json` for current state, known-good checkpoint, objective, next move, failed attempts, open questions, and context routes.
- Added conservative recognition and repair of partial passports; repaired claims return to `ai-draft`.
- Added `review` states and explicit data-handling policy to the durable passport.
- Added inventory fingerprints for drift detection without hashing large binary contents.
- Added `always_read`, task-specific, and `avoid_by_default` context routing.
- Added identity-based standalone export names and a predictable three-file handoff sidecar ZIP.
- Versioned the Studio filename and made its browser title include the opened artifact name.
- Extended the Python validator and regression suite to cover both contracts, ZIP safety, repair, routing, drift inputs, and export naming.

## 0.4.0 — 2026-09-12

- Added plain-language example menus for purpose, audience, success, scope, environment, and change policy.
- Added detected-file roles and one-click placement as first-run entry point, editable source, protected input, or output.
- Added cross-field diagnostics for inventory mismatches, source/output confusion, generic verification, empty procedures, stale confirmations, and misplaced success criteria.
- Added automatic reconciliation so answered owner questions disappear and rejected suggestions count as reviewed.
- Preserved prior intake inventories and observations during passport migration.
- Reworked Handoff scoring around specific, mutually consistent, evidence-backed answers rather than field completion alone.
- Added a rough-versus-revised regression case based on the Digimon patch handoff trial.

## 0.3.0 — 2026-09-11

- Reframed Guided Passport as a plain-language owner interview while retaining technical field names as secondary labels.
- Added explicit `unresolved` owner answers instead of treating “I don't know” as completion.
- Split readiness into Structure, Evidence, and Handoff scores.
- Added deterministic clarity warnings for common placeholders and non-observable answers.
- Added Python script, README, batch file, executable, and browser-entry detection during folder intake.
- Added package-relative file inventory and selectable source/output helpers.
- Added migration from 0.1 and 0.2 without re-verifying preserved claims.
- Added regression coverage for the real failure mode discovered in the Digimon patch test.

## 0.2.0 — 2026-09-11

- Added arbitrary-JSON intake and explicit file-type detection.
- Added local project-folder inventory through the browser folder picker.
- Added extracted, inferred, and owner-required evidence states.
- Added conversion from package manifests, lockfiles, build-info files, TypeScript configuration, and generic JSON into passport drafts.
- Added Artifact Passport 0.1 migration without silently re-verifying preserved claims.
- Separated structural conformance from unresolved intake confirmations.
- Added intake provenance to JSON and human-readable exports.

## 0.1.0 — 2026-09-11

- Defined the portable Artifact Passport contract and security model.
- Added a JSON Schema and dependency-free validator.
- Added an offline Passport Studio for creation, import, validation, and export.
- Added minimal and Officer Reference examples.
- Added a repeatable fresh-handoff evaluation rubric.
