# Artifact Passport Specification 0.7

## 1. Purpose

An Artifact Passport communicates implementation intent across people, software, and AI systems. It complements ordinary metadata by describing the artifact's operating contract: purpose, authority, boundaries, source of truth, procedures, and evidence of correctness.

The durable normative representation is `artifact-passport.json`. The frequently replaced current-state companion is `artifact-handoff.json`. `ARTIFACT.md` is a human-readable projection and must not silently contradict either JSON document. Artifact Passport 0.7 also defines an optional `artifact-passport-run.json` observation receipt for controlled handoff-efficiency experiments. A Run Receipt is benchmark evidence, not artifact authority or durable project truth.

## 2. Design principles

1. **Portable:** JSON plus plain Markdown; no service is required.
2. **Human-verifiable:** Important constraints are readable without specialized software.
3. **Non-executable:** Instructions are data until a human or trusted host authorizes an action.
4. **Deny by default:** Missing permissions do not imply permission.
5. **Evidence over confidence:** Verification checks define how correctness is demonstrated.
6. **Local authority:** The passport identifies who may approve changes; it does not create authority.
7. **Graceful extension:** Namespaced extension fields may add domain-specific meaning.
8. **Honest uncertainty:** An explicit unresolved answer is preferable to a plausible-looking placeholder.
9. **Current state is replaceable:** Durable intent must not be buried inside a chronological status narrative.
10. **Minimum necessary context:** A receiver reads the control pair first, then only the files relevant to its task.
11. **Measured claims over vibes:** Efficiency claims should be grounded in matched observations, and unavailable host telemetry must remain unavailable rather than being guessed.

## 3. Conformance

A conforming 0.7 passport:

- is valid JSON encoded as UTF-8;
- validates against `artifact-passport.schema.json`;
- uses `spec_version` equal to `0.7`;
- has a stable `passport_id`;
- states a purpose and at least one success criterion;
- identifies at least one entry point and one source-of-truth item;
- includes at least one required verification check;
- explicitly states network policy and allowed actions;
- states whether its claims are an AI draft, owner-reviewed, or verified;
- states whether artifact data may leave the device and in which contexts;
- contains no secrets, credentials, private keys, or authentication tokens.

A conforming handoff identifies the same `passport_id`, records the current status, current known-good point, current objective, recommended next move, failed attempts, open questions, a compact `context_snapshot`, and context routes. The context snapshot contains `do_not_break`, `decision_history`, `known_uncertainties`, `recent_delta_from`, and `recent_delta`.

A conforming package places `artifact-passport.json` and `artifact-handoff.json` at its root. A human projection should be placed beside them as `ARTIFACT.md`. Standalone downloads may use identity-prefixed names to prevent collisions, but a handoff bundle uses the predictable root names. Run receipts are intentionally separate from the ordinary three-file handoff bundle so ephemeral benchmark history does not become current-state truth.

## 4. Trust and precedence

The passport is an assertion supplied by the artifact owner. Its contents are not inherently trusted merely because the JSON is valid.

Consumers must apply this precedence order:

1. Law, organizational policy, and platform safety controls.
2. Explicit instructions from an authenticated current owner or authorized operator.
3. Signed and verified policy associated with the artifact.
4. The Artifact Passport.
5. Other bundled documentation.
6. Inferences made from file contents.

No passport field may override a higher-precedence rule. Commands, URLs, and procedures are inert text until separately authorized. Consumers must never treat `allowed_actions` as authorization to exceed their own permissions.

## 5. Required object groups

| Group | Meaning |
| --- | --- |
| `artifact` | Identity, version, kind, and description. |
| `intent` | Purpose, audiences, and observable success. |
| `operation` | Entry points, environment, network policy, and dependencies. |
| `structure` | Source of truth, generated outputs, protected material, and ignored paths. |
| `constraints` | Allowed actions plus mandatory, prohibited, and preservation rules. |
| `procedures` | Ordered setup, edit, build, verify, release, and recovery guidance. |
| `verification` | Required checks and most recent verification record. |
| `authority` | Ownership, approvers, and change policy. |
| `review` | Whether claims are an AI draft, owner-reviewed, or verified. |
| `handoff` | First-reading path, safe initial actions, limitations, and open questions. |

The optional `intake` group records how a draft was produced from existing material.

## 5.1 Artifact Intake

Intake transforms scattered existing metadata into a passport draft without erasing uncertainty. An intake-capable tool must preserve three evidence states:

| State | Meaning | May be treated as established? |
| --- | --- | --- |
| `extracted` | The value was directly present in an identified supplied source. | Only as a claim made by that source. |
| `inferred` | The tool derived a plausible value from filenames, structure, conventions, or other evidence. | No, unless an owner accepts it. |
| `owner-required` | The field depends on intent, authority, policy, or judgment that supplied files cannot establish. | No. |

An inference should include its source and confidence when available. Accepting an inference records owner review; it does not retroactively turn the value into an extracted fact. `reviewed: true` records that the owner considered a suggestion even when `accepted` is false. Rejection is completed review, not missing evidence.

An intake tool must not automatically establish ownership, approval authority, network policy, data classification, or permission to act. It may ask for those decisions and keep the passport unready until they are answered.

`intake.owner_questions` contains questions discovered during intake. Answered questions must be removed or reconciled. `intake.inventory` may record package-relative filenames observed during JSON, folder, or ZIP intake. `intake.file_candidates` may attach conservative, non-authoritative role suggestions such as `passport`, `handoff`, `entry-point`, `editable-source`, `protected-input`, `generated-output`, `evidence`, or `instructions`. The optional top-level `unresolved` array records a field, the unanswered owner question, and an optional reason.

A passport can be structurally conforming while still operationally unready. Interfaces must report these dimensions separately:

- **Structure:** required shape and values are present.
- **Evidence:** claims are traceable to supplied material or explicit owner review.
- **Handoff:** another human could operate or maintain the artifact without material guessing.

Clarity and relationship warnings may identify deterministic placeholder patterns, non-observable success criteria, declared paths absent from the intake inventory, likely source/output confusion, stale confirmation language, or contradictions between related fields. They are prompts for review, not proof that an answer is false.

### 5.2 ZIP intake and repair

ZIP intake is an inventory operation, not execution. A conforming local Studio rejects absolute and `..` traversal paths; does not decrypt entries; bounds entry count and selectively extracted text size; reads only recognized small text candidates; never runs bundled programs or follows bundled URLs; and reports skipped material instead of pretending it was inspected.

An intake tool may recognize a damaged passport from its filename, schema identifier, passport ID, and surviving standard groups. Repair fills structural defaults only so the file can be reviewed. It must set `review.status` to `ai-draft`, identify missing groups as unresolved, and never claim absent owner decisions were established.

### 5.3 Current-state handoff

`artifact-handoff.json` is a replaceable snapshot, not a historical log. Its `working_state` records what is currently true, the latest owner-confirmed known-good point, the latest material change, the current objective, the recommended next move, and failed or misleading paths that should not be repeated blindly.

`context_routes.always_read` names the minimal control material. `by_task` maps a task to additional files. `avoid_by_default` identifies generated, irrelevant, misleading, or costly context that should be skipped unless the task requires it. Routing is reading guidance, not access authority.

The `context_snapshot` exists to preserve high-value continuity without importing a whole prior conversation. `do_not_break` contains fragile current boundaries; `decision_history` records concise decisions and rationale-relevant facts; `known_uncertainties` records uncertainty already discovered; `recent_delta_from` identifies the baseline for the most recent change set; and `recent_delta` records material differences from that baseline. These fields may be empty when no such context exists, but tools must preserve them during migration and handoff export.

### 5.4 Review and drift

`review.status` is one of `ai-draft`, `owner-reviewed`, or `verified`. A tool-created draft begins as `ai-draft`. Only a current owner or authorized reviewer may advance it. `verified` means the recorded checks were actually performed; it does not mean every statement is universally true.

The optional `artifact_fingerprint` uses `sha256-inventory-v1`: SHA-256 over sorted package-relative path and byte-size pairs, excluding `artifact-passport.json`, `artifact-handoff.json`, and `ARTIFACT.md`. It detects inventory drift without reading large binary contents. It is not a cryptographic content signature.

### 5.5 Measured handoff run receipt

`artifact-passport-run.json` is an optional observational record for one controlled evaluator run. It is not required for ordinary artifact use and must not be treated as owner-reviewed artifact truth.

A conforming 0.7 Run Receipt records:

- the companion `passport_id`, artifact identity, control-or-Passport condition, and benchmark prompt identifier;
- evaluator host/model metadata sufficient to identify materially different run conditions;
- observable timing, with unavailable timing represented explicitly rather than invented;
- mutually exclusive orientation, verification, and other action counts whose sum equals `total_tool_actions`;
- unique and unnecessary file-read counts;
- outcome counts including independently verified claims, incorrect assumptions, clarification loops, backtracking, and unsafe proposed actions;
- optional rubric score; and
- optional host-reported token, cache, credit, or usage counters.

Host usage values may be populated only when the host actually exposes them. `reported` means a numeric host value was observed; `unavailable` means the host did not expose it; `not-recorded` means it was not captured. Character-count estimates and other inferred token approximations must not be written into measured host-usage fields.

The canonical A/B procedure is defined in `HANDOFF_TEST.md`. A comparison must use one control and one Passport receipt for the same underlying artifact and prompt. Differences in host, model, reasoning mode, tool surface, prompt, artifact identity, or inventory digest are comparability warnings.

`tools/compare_handoff_runs.py` reports observed reductions or increases and applies a quality gate. The quality gate is not a universal product score; it prevents a faster but materially worse project model from being presented as clean efficiency evidence.

## 6. Key semantics

### Paths and URLs

Package-relative paths use forward slashes. A path must not escape the package root. URLs should be used only for external references and dependencies.

### Source of truth

Every `structure.source_of_truth` entry declares material that must be edited directly. Generated outputs must not be represented as source of truth unless they genuinely are the only maintainable form.

### Network policy

`operation.network_policy` is one of:

- `forbidden` — normal use and maintenance require no network access.
- `optional` — the artifact works without a network, but named optional capabilities may use it.
- `required` — the artifact cannot fulfill its purpose without network access.

This describes intended behavior; it does not grant network permission.

### Allowed actions

`constraints.allowed_actions` is an allowlist describing the owner's intended maintenance surface. Anything absent is unspecified and requires confirmation when material.

### Data handling

`constraints.data_handling.may_leave_device` is `yes`, `no`, or `ask-owner`. `approved_contexts` names locations or services the owner accepts, and `redaction_required` states whether sensitive details must be removed first. These fields describe owner intent but cannot override law, policy, platform restrictions, or actual access controls.

### Verification

Every required check needs an identifier, a description, and an expected result. A command is optional because some checks require human inspection. A consumer must not claim verification unless it actually performed the check and recorded truthful results.

### Extensions

Top-level `extensions` keys must be namespaced, such as `org.example.records`. Extensions must not redefine standard fields.

## 7. Human projection

`ARTIFACT.md` should contain, in this order:

1. Artifact identity and current state.
2. Known-good point, current objective, and next move.
3. Compact context snapshot, including do-not-break items, recent delta, decision history, and known uncertainties.
4. Purpose and start-here instruction.
5. Context routes and non-negotiable constraints.
6. Source of truth and generated outputs.
7. Operation and network expectations.
8. Verification checks.
9. Authority, known limitations, and open questions.

If the JSON and Markdown disagree, stop and ask an authorized owner to reconcile them. The JSON is normative only after that conflict has been resolved.

## 8. Security exclusions

A passport must not:

- contain secrets;
- demand automatic execution;
- claim permissions it cannot grant;
- conceal instructions in encoded payloads;
- redefine host safety or access controls;
- represent unperformed checks as passed;
- use external content as an invisible source of behavioral instructions.

## 9. Versioning

`spec_version` versions the passport format. `artifact.version` versions the described artifact. They are independent.

Patch-compatible additions should use optional fields or namespaced extensions. Breaking semantic changes require a new specification version.

## 10. Deliberately deferred

Future work may define cryptographic binding, signatures, field-level provenance, standardized capability vocabulary, embedded passports, registries, and adapters for specific development or AI environments. None are required for 0.7.
