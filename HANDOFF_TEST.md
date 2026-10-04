# Artifact Passport 0.7 — Measured Fresh Handoff Test

This test measures whether an Artifact Passport reduces the work required for a fresh evaluator to build an accurate, usable model of an unfamiliar project.

The purpose is not to prove that Passport always saves tokens or time. The purpose is to turn a handoff into a repeatable A/B observation instead of relying on “that felt faster.”

## 1. Prepare matched conditions

Use the same non-sensitive artifact in both conditions.

- **Control:** ordinary artifact files and whatever ordinary documentation genuinely belongs to the project. Remove `artifact-passport.json`, `artifact-handoff.json`, and `ARTIFACT.md` if those files exist only because of Passport.
- **Passport:** the identical underlying artifact plus its current `artifact-passport.json`, `artifact-handoff.json`, and `ARTIFACT.md`.

Do not simplify the control package to make Passport look better. The control should represent how the project would actually be handed off without Passport.

Where possible, keep the following identical between runs:

- AI host and model;
- reasoning/effort setting;
- tool surface and permissions;
- exact prompt;
- artifact version;
- fresh conversation or evaluator state;
- no extra verbal explanation from the operator.

If an inventory fingerprint is available, record the same underlying `artifact_inventory_digest` in both receipts. Passport control files are excluded from the inventory fingerprint by design.

## 2. Use the same prompt

Use this prompt for both conditions:

> Inspect this unfamiliar project without modifying it. Tell me: what the project is; which files are authoritative; which files are outputs/backups/obsolete; what important constraints must be preserved; what you would need to touch; how you would verify a future change; what you are uncertain about. Base every conclusion on evidence from the project. Do not invent missing information.

Do not tell the Passport evaluator to read the Passport first. Discovery of the control files is itself part of the handoff behavior being measured.

## 3. Start the clock before project inspection

Start measurement immediately before the evaluator's first project-reading action. End it when the final orientation answer is delivered.

Record a **usable project model** at the earliest point where the evaluator has enough evidence to correctly state all of the following without material guessing:

1. what the artifact is;
2. which material is authoritative versus generated/backed-up/obsolete;
3. the current known-good/current objective when that state is available;
4. the important constraints that must survive a change;
5. the likely change surface for a representative future edit;
6. a concrete verification approach;
7. the material uncertainties it still cannot establish.

That milestone defines `time_to_usable_model_ms`.

## 4. Count evaluator-visible actions consistently

A **tool action** is one evaluator-visible invocation of a tool, shell step, file-open action, or equivalent host action. Do not count hidden reasoning. Do not split a single compound host action into imaginary internal actions merely because it contains several shell subcommands.

Classify each tool action exactly once:

- **orientation action** — primarily establishes project identity, layout, source of truth, current state, constraints, or where to read next;
- **verification action** — primarily tests or independently confirms a project claim;
- **other action** — neither of the above.

`total_tool_actions` must equal those three categories added together.

A **unique file read** means file contents were actually inspected. Directory listings, filename inventories, and archive manifests do not count as file reads unless their content is the evidence being inspected.

An **unnecessary file read** is a file read the evaluator later determines did not contribute to orientation, verification, or the requested task. Do not label a useful negative check as unnecessary merely because it did not contain the answer.

A **clarification loop** is a question to the operator that could not be resolved from the supplied project and delayed the usable project model.

A **backtracking event** occurs when the evaluator materially reverses an earlier project interpretation and re-reads or re-traces the project because the earlier model was wrong or incomplete.

`time_to_first_verified_claim_ms` ends when the evaluator first independently confirms a project claim rather than merely repeating documentation.

## 5. Record one run receipt per condition

Copy `templates/artifact-passport-run.template.json` twice and fill it as:

```text
control.run.json
passport.run.json
```

The receipt records:

- condition, prompt, host, model, and artifact identity;
- orientation, verification, other, and total tool actions;
- unique and unnecessary file reads;
- time to usable project model, first verified claim, and total runtime when observable;
- claims independently verified;
- contradictions found;
- incorrect assumptions;
- clarification loops;
- backtracking events;
- unsafe proposed actions;
- optional rubric score;
- host-reported input, cached-input, output, reasoning, total tokens, or credit/usage counters when actually exposed.

### Host usage rule

Do **not** reverse-engineer missing token counts from characters, words, elapsed time, screenshots, or subscription percentage and put the estimate in a measured field.

Use:

- `host_usage.status = "reported"` only when the host exposes the number;
- `"unavailable"` when the host does not expose it;
- `"not-recorded"` when it might have been available but was not captured.

Keep missing numeric values `null`.

## 6. Score answer quality

Efficiency is not useful if the evaluator simply does less work and ends with a worse project model. Score each answer from 0 to 2 on the same rubric used in earlier Passport tests.

| Category | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Purpose | Incorrect or invented | Broadly correct | Precise and bounded |
| Entry point | Wrong or absent | Correct with uncertainty | Correct with role/tool |
| Source of truth | Confuses output and source | Partly correct | Correctly distinguishes both |
| Constraints | Misses important boundary | Finds some boundaries | Finds all material boundaries |
| Network/data policy | Invents or omits | Uncertain | Correct and bounded |
| Authority | Assumes permission | Notes ambiguity | Correctly identifies approval boundary |
| Verification | Generic “test it” | Some relevant checks | Concrete checks with expected results |
| Unknowns | Hallucinates completeness | Mentions gaps | Names material missing evidence |
| Safe change plan | Risks protected behavior | Mostly safe | Uses canonical source, rebuild, and checks |
| Traceability | No evidence trail | Refers to docs generally | Maps claims to project evidence |
| Current state | Invents or misses it | Broadly identifies it | Correctly states known good/objective when available |
| Context economy | Reads indiscriminately | Mostly relevant reading | Reaches the model with narrowly relevant context |

Maximum score: **24**. Record the result as `rubric_score` and `rubric_max` in each receipt.

## 7. Compare the pair

Validate both receipts:

```text
python tools/validate_passport.py control.run.json passport.run.json
```

Then compare them:

```text
python tools/compare_handoff_runs.py control.run.json passport.run.json
```

The comparator reports the observed change for:

- orientation actions;
- verification actions;
- total tool actions;
- unique files read;
- unnecessary file reads;
- clarification loops;
- backtracking events;
- time to usable project model;
- time to first independently verified claim;
- total runtime;
- host-reported token/credit usage when both runs contain it.

## 8. Quality gate

The comparator marks the pair **CAUTION** instead of treating speed as a clean efficiency signal when the Passport condition:

- fails to reach a usable project model;
- records more incorrect assumptions than control;
- proposes more unsafe actions than control;
- independently verifies fewer claims than control; or
- records a lower comparable rubric score.

This is deliberately conservative. The goal is less orientation overhead **without buying that reduction by understanding the project worse**.

## 9. Interpretation

A matched pair is evidence about that artifact, evaluator, host, model, and prompt. It is not proof of a universal token or context-window reduction.

Repeat the test across different artifacts and evaluators. Prefer medians across repeated pairs when enough data exists. Preserve raw run receipts so later versions of the comparator can re-analyze the same observations.

Useful aggregate questions include:

- How much did Passport reduce orientation actions before a usable project model existed?
- How many fewer project files had to be opened?
- Did verification remain equally strong or improve?
- Did clarification and backtracking fall?
- When the host exposed usage, did input-token or credit consumption fall as well?
- Did v0.6 `context_snapshot` fields reduce repeated rediscovery on multi-session projects?

## 10. Optional phase two: representative change plan

After the orientation answer, give both evaluators the same representative change request and ask for a plan only. The request should touch a real constraint, such as modifying a user-visible behavior while preserving offline operation and a known-good release.

Record phase-two observations separately rather than mixing them into the orientation receipt. This keeps the core handoff benchmark comparable even when future change requests differ.
