# Minimal note example

This example is included so you can inspect a complete, small handoff before making one for a larger project.

## Read the files

1. [note.txt](note.txt) is the artifact: one sentence of UTF-8 text.
2. [artifact-passport.json](artifact-passport.json) records its lasting purpose, authoritative file, constraints, and verification.
3. [artifact-handoff.json](artifact-handoff.json) records its current state, next move, decision history, and reading routes.

The example's name is **Example Note**, version **1.0**, in both JSON documents. The owner and review entries are illustrative sample data, not authentication of a real person.

## Try it in the Studio

1. Open `tools/Artifact-Passport-Studio-v0.7.html` from the toolkit's root folder.
2. Use the folder picker to select this `examples/minimal` folder.
3. Review the imported Passport and Handoff.
4. Select **Validate**, then **Export handoff bundle**.

You can also attach this example's files to a fresh AI conversation and ask it to inspect the artifact, identify the authoritative file, state the constraints, and explain how it would verify a change. For a measured comparison, use the separate `HANDOFF_TEST.md` protocol.

## Current state

The note is present and remains the only canonical editable content. The next move is to read the Passport and inspect the note. Preserve its meaning and UTF-8 readability. No build or network connection is required.

This tiny example explains the format. It is not evidence of an efficiency improvement on a larger project.
