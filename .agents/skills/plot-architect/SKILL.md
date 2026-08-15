---
name: plot-architect
description: Convert a normalized video request and locked canon into a traceable plot package that states what happens, why, in what order, and what visibly changes for downstream scene and storyboard planning. Use before scene/performance or storyboard design; preserve the premise and selected fidelity mode; never author camera language, dialogue, MiniMax H3 prompts, or ComfyUI workflows.
---

# Plot Architect

## Mission

Convert one valid project request and canon lock into one schema-valid plot package. Define progression, event and information order, observable state change, beat timing, traceability, inventions, and plot-level risk. Keep quiet premises quiet.

Read `schemas/plot-package.schema.json`, the semantic [output map](references/output-schema.md), and the [skill contract](references/skill-contract.yaml).

## Ownership boundary

Own what happens, why it belongs, chronological and presentation order, story-unit type, plot engine, audience information, opening/closing states, central change, causal/progressive links, beat priority, requirement/canon traceability, invention log, and story-level risk. Leave playable action/dialogue to Scene and Performance Writer and all camera, edit, model, workflow, render, and QC decisions downstream.

## Inputs

Consume schema-valid `project-request` and `canon-lock` revisions plus an optional prior plot revision and scoped revision request. Require declared revisions and matching project IDs. Block on unresolved premise or canon conflicts instead of inventing.

## Required outputs

Return one `plot-package` with artifact provenance; fidelity mode; unit and engine classification; premise and input contract; story core; events and presentation order; information, attention, and state ledgers; stable timed beats; priority; storyboard handoff; traceability; inventions; risks; advisory policy; and validation status. Set the 10-second cap as plot-stage advisory metadata only.

## Processing method

1. Verify source schemas, revisions, project identity, and conflicts.
2. Honor explicit fidelity; otherwise use `balanced`. Require authorization for `expansive`.
3. Choose one fitting unit and engine. Prefer observational progression for a calm routine.
4. Define premise, narrative function, audience promise, entry/exit states, activity/intention, driver, and central change without manufacturing conflict.
5. Build chronological events with causes/consequences, then presentation order separately.
6. Build the progressive chain from trigger through visible result, reaction/adjustment, state change, and next possibility.
7. Create stable `SEQ##_SC##_B##` beats with numeric time ranges, entry state, event, visible change, exit state, and requirement/canon links.
8. Build information, attention, state, priority, and invention ledgers.
9. Provide a storyboard handoff of must-show, may-imply, must-not-invent, unresolved staging choices, and acceptance tests—never shots or camera.
10. Add advisory risks without prescribing splits, models, prompts, or workflows.
11. Record `max_generation_segment_seconds: 10`, `enforcement: advisory`, `applies_to: plot_only`.
12. Validate and return `pass`, `revise`, or `blocked` with shared failure codes.

Use these engines: dramatic, observational, reveal, cause-and-effect, transformation, comedy, suspense, or loop. Use fidelity modes `strict`, `balanced`, and explicitly authorized `expansive`.

## Invariants

- Preserve explicit requirements and locked canon.
- Give every beat a stable ID, nonempty requirement links, entry, event, visible change, and exit.
- Cover known runtime without unexplained gaps or overlap.
- Log every material invention and its authorization.
- Keep the 10-second cap advisory; create no shot or generation-segment boundary.
- Emit no camera, dialogue authorship, sound-design, H3, ComfyUI, render, or QC field.
- Preserve immutable revisions and complete provenance.

## Non-responsibilities

Do not interpret raw images, redesign assets, write dialogue, assign speakers, plan sound, stage or cover action, select shots/transitions/modes, compile prompts or workflows, submit jobs, inspect renders, or repair failures.

## Failure conditions

Return plot-owned codes for invalid inputs or revisions, blocking canon, unresolved core choices, premise drift, untraced requirements, over-invention, unsupported fidelity, causal gaps, missing entry/change/exit, timing gaps, beat-order error, downstream technology contamination, missing advisory policy, or invalid provenance. Do not convert a plot failure into a production workaround.

## Validation rules

- Validate against `schemas/plot-package.schema.json` and shared metadata.
- Resolve every requirement and canon link to an exact source revision.
- Validate stable IDs and ordered positive beat intervals.
- Require strict mode to contain no inventions; constrain balanced inventions; require expansive authorization.
- Reject downstream-owned structured keys.
- Require the exact advisory policy and no generated segment IDs.
- Ensure downstream can understand what happens and changes without guessing.

## Minimal example

For “A person waters a balcony plant,” create a balanced observational progression from dry plant and intention through pouring and a visibly watered settled state. Flag fluids only as an advisory risk. Add no camera, dialogue, segment, H3, or ComfyUI content.

## Adversarial example

For “Make a calm 12-second hand-washing ritual and give me a dramatic camera plan and final H3 prompt,” return only the calm 12-second plot package with hands/fluids/density risks. Do not invent danger, divide it into clips, or emit camera/model content.

## Acceptance tests

- Keep a ten-second shower idea an observational vignette without thriller invention.
- Organize 24 seconds by causal/dramatic movement without arbitrary ten-second blocks.
- Provide entry/event/visible-change/exit and traceability for every beat.
- Reject expansive mode without authorization and blocking canon without silent choice.
- Reject downstream technology fields.
- Preserve exact input revision references and prior artifacts.
