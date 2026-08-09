# Plot package semantics

Treat `schemas/plot-package.schema.json` as the sole shape authority. This file explains field meaning only.

- `artifact`: immutable provenance and exact request/canon source hashes.
- `input_contract`: the normalized premise, runtime, requirements, assumptions, unknowns, and canon revision.
- `story_core`: the premise, function, opening, progression driver, central visible change, and closing state.
- `story_events`: chronological causality. `presentation_order`: what the audience receives and when.
- `information_ledger` and `attention_progression`: knowledge and audience focus, never camera instructions.
- `state_ledger`: story-relevant character, activity, prop, and environment deltas.
- `beats`: ordered numeric `{start,end}` seconds. `entry_state` is the state at the start; `visible_change` is the single externally readable change; `exit_state` is the settled handoff to the next beat.
- `beat_priority`: indispensable, supporting, and optional texture beat IDs.
- `storyboard_handoff`: story/sequence/scene seeds and unresolved staging or transition questions; never a shot plan.
- `traceability`: requirement IDs resolve to project request; canon IDs resolve to canon lock; assumptions and inventions remain separate.
- `invention_log`: every added material element, its rationale, source, authorization, and beat scope.
- `risk_indicators`: advisory plot/generation complexity, never a prescribed production solution.
- `planning_policy`: exact 10-second advisory for later stages.
- `validation`: deterministic checks and plot-owned failure codes.

Do not emit the legacy `story_audio`, `model_handoff`, MiniMax, H3, ComfyUI, camera, or workflow fields.
