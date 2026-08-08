---
name: storyboard
description: Convert a story, screenplay, treatment, scene idea, or reference pack into a generation-ready audiovisual storyboard for ComfyUI and MiniMax H3. Use for dramatic decomposition, directing intent, blocking, camera language, synchronized sound, continuity control, H3 prompt writing, keyframe planning, shot chaining, and machine-readable production handoffs.
---

# Continuity storyboard planner

Direct the story rather than merely describing it. Treat the storyboard as the
production contract between narrative intent, performance, camera, sound,
editing, generation, and handoff.

## Core rule

Action and camera are parallel timelines. Every action beat must say what the
audience sees, while the camera track says how the audience experiences it.

## Use this workflow

Follow these passes in order. Keep the human-facing plan compact, but do not
skip a pass when the user asks for only a prompt.

1. **Intake and assumptions.** Extract the source type, premise, runtime,
   platform, aspect ratio, frame rate, genre, tone, visual medium, language,
   model/workflow constraints, references, endpoint frames, and safety limits.
   Infer minor omissions and list them under **Assumptions**.
2. **Story brief.** State the logline, protagonist, desire, obstacle, stakes,
   central question, starting and ending states, emotional change, point of
   view, audience experience, format, and target runtime.
3. **Dramatic decomposition.** Map each scene as
   objective -> obstacle -> action -> turn -> exit state. Group scenes into
   sequences by dramatic movement, strategy, location cluster, or emotional
   phase; do not divide the story into equal-duration clips.
4. **Director’s treatment.** Decide point of view, audience distance,
   information strategy, emotional camera arc, visual motifs, and dominant
   camera energy before choosing coverage.
5. **Spatial design and blocking.** Establish geography, axis, eyelines,
   screen direction, subject marks, prop states, movement paths, and readable
   entry/exit poses before placing the camera.
6. **Shot and segment design.** Give every shot a dramatic job, information
   change, emotional change, camera motivation, and readable exit state. Split
   generation segments when duration, action complexity, camera position,
   endpoint frames, or continuity risk requires a reset.
7. **Generation routing.** Select the H3 family before writing the prompt.
   Keep endpoint-frame modes separate from full-reference mode unless a tested
   custom workflow explicitly supports both.
8. **Prompt construction.** Assemble reference assignment, global style lock,
   character/world lock, intent, entry state, blocking, visible action, camera,
   timed beats, dialogue/diegetic sound, exit handoff, and exclusions. Then
   render the H3-specific syntax.
9. **Production handoff.** Export the prompt packet, references, workflow,
   settings, deterministic paths, seed policy, media paths, tail/head frames,
   transition type, and testable checks in a YAML or JSON manifest.
10. **Acceptance review.** Reject any shot whose dramatic purpose, camera
    motivation, reference job, speaker identity, continuity state, or model
    routing is unclear.

Read the detailed guidance only when needed:

- [Directing, blocking, and continuity](references/directing-and-continuity.md)
- [MiniMax H3 routing and prompt syntax](references/h3-prompting.md)
- [Production cards, manifest, and acceptance review](references/production-schema.md)

## Non-negotiable operating rules

- Describe observable actions and sounds. Replace abstract emotions with
  visible behavior and replace vague camera language with a concrete move or
  hold.
- Give every camera move and edit a reason: orient, reveal, conceal, redirect
  attention, alter emotional distance, register consequence, create rhythm, or
  prepare a transition. Use a static shot when no move is motivated.
- Keep a generation segment bounded: one primary performance arc, one dominant
  camera move, one coherent location/lighting state, and one readable exit.
- Declare every reference’s job, copied attributes, permitted variation, and
  exclusions. Never say only “use the references.”
- Write canonical identity, world, style, wardrobe, prop, and sound anchors
  once; reuse them verbatim. Keep variable performance separate from immutable
  continuity facts.
- Preserve the 180-degree axis, screen direction, eyelines, lighting state,
  and prop state unless the change is intentional and visible.
- Use a cut when discontinuity is meaningful or generative continuity is
  unreliable. Do not force a morph between editorially separate shots.
- Use explicit handoffs: outgoing pose, gaze, prop state, lighting, camera
  vector, screen direction, audio beat, and next opening state. Do not write
  “make it seamless” without those conditions.
- Keep dialogue, diegetic action sounds, ambience, and non-diegetic music in
  their distinct fields. Use stable speaker IDs across shots.
- Keep IDs stable across prompt revisions and renders:
  SEQ01_SC02_SH03_SEG01.

## Defaults and constraints

Use these defaults unless the project or installed workflow says otherwise:

~~~
aspect_ratio: "16:9"
fps: 24
generation_segment_seconds: 5
prompt_language: English
draft_resolution: native_768_short_edge
final_resolution: 2K_when_supported
audio: native_stereo_32000_hz
camera_energy: restrained
music: none_unless_narratively_useful
~~~

For MiniMax H3, request 4–15 second integer durations, record the actual frame
count and effective duration after frame-grid snapping, and keep API-compatible
prompt packets within 7000 characters unless the installed node documents a
different limit.

## Required output order

Unless the user explicitly requests prompt-only output, return:

1. Assumptions
2. Story brief
3. Sequence map
4. Continuity bible and reference map
5. Director’s treatment
6. Scene and blocking cards
7. Compact shot table
8. Four-track beat timelines
9. Final H3 prompt packet for each generation segment
10. ComfyUI production manifest
11. Acceptance checklist

For a short single-scene request, return at minimum the director intent,
blocking, shot/beat timeline, final H3 prompt, settings, and handoff state.

## Final internal check

Before finalizing, answer these questions for every shot:

1. Why does it exist?
2. What changes during it?
3. Whose experience controls the frame?
4. What are the subjects doing at each beat?
5. What is the camera doing at the same time, and why?
6. What does the audience learn or feel?
7. What exact state ends the shot?
8. How does the next shot begin?
9. What observable failure would cause rejection?

If an answer is vague, revise the storyboard before generation.
