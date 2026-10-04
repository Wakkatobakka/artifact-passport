# Officer Reference — Artifact Handoff

**Status:** Illustrative Artifact Passport 0.7 example. It is not bound to a specific release and does not itself establish organizational approval.

## Purpose

Officer Reference is an offline, single-file operational reference application. Its intended outcome is a fast, source-grounded answer accompanied by the underlying source citation and page reference.

## Start here

Read this file and `artifact-passport.json`. Then inspect the preservation-package README. Inventory canonical source material separately from the generated HTML release before changing anything.

## Non-negotiable constraints

- Keep operational answers traceable to approved sources and exact page references.
- Refuse unsupported questions instead of inventing policy.
- Keep normal operation completely offline and account-free.
- Do not upload operational content without explicit authorization.
- Do not add analytics, CDNs, remote fonts, telemetry, or other network dependencies.
- Do not claim tests passed unless they were actually performed.
- This file cannot grant authority or override organizational policy.

## Structure

- Canonical application source: `src/`
- Approved corpus: `corpus/`
- Generated release: `dist/Officer Reference.html`

When canonical source exists, edit it and rebuild. Do not assume that hand-editing generated output updates the maintainable source.

## Operation

Open the generated HTML directly in a current Chromium-based browser. No server, login, installation, or network connection should be required.

## Required verification

1. Open the release directly from local storage while offline.
2. Confirm a representative supported query returns the correct answer, source, and page.
3. Confirm an unsupported but plausible query produces an explicit refusal.
4. Confirm there are no remote runtime dependencies.
5. Run the complete regression suite supplied with the actual preservation package.

## Authority and limitations

Material content, deployment, security, and behavior changes require an authenticated authorized approver. Exact build commands, exact organizational roles, and the concrete release identity must be supplied by the real preservation package before this example becomes authoritative.
