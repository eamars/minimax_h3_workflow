---
name: storyboard
description: Turn a long story, screenplay, or video idea into a generation-ready storyboard of connected sequences, scenes, shots, prompts, continuity locks, keyframes, and ComfyUI handoffs. Use for long-form AI video planning, scene decomposition, character and world consistency, cinematic shot design, transition planning, and packaging scene-by-scene generation jobs.
---

# Continuity storyboard planning

Translate story into visual decisions that a video model can execute and a
ComfyUI pipeline can join. A storyboard is not a decorated synopsis: it is the
contract between narrative intent, shot design, generation prompts, and the
editorial handoff from one clip to the next.

## Produce the planning package

Always produce these layers, even when the user asks only for a prompt:

1. **Story brief:** logline, protagonist desire, obstacle, stakes, emotional
   change, ending state, audience, format, aspect ratio, FPS, and target runtime.
2. **Sequence map:** a small number of dramatic movements, each with a clear
   purpose and turn.
3. **Continuity bible:** canonical character, wardrobe, prop, location,
   lighting, palette, camera language, sound, and negative constraints.
4. **Scene cards:** one card per location/time/objective/turn unit.
5. **Shot cards:** one card per visual beat or generation-sized clip.
6. **Prompt packets:** reusable global anchors plus scene-specific action,
   camera, timing, and audio instructions.
7. **Handoff manifest:** exact tail/head frames, state, transition type, and
   assembly parameters for ComfyUI.

Put the machine-readable fields in the schema from
[scene-handoff-schema.md](references/scene-handoff-schema.md); keep prose only
where it helps a human judge a creative choice.

## Decompose the story

Use this hierarchy:

`project -> sequence -> scene -> shot segment -> frame handoff`

Apply the following tests:

- Start a new **sequence** when the story enters a different dramatic movement.
- Start a new **scene** when location, time, objective, obstacle, or emotional
  state changes enough that the audience needs a new visual unit.
- Start a new **shot segment** when camera position, subject action, or model
  context must reset. Use one primary action and one dominant camera move per
  generated segment unless the selected model has been tested with a timeline
  prompt.
- Create a **frame handoff** whenever the next segment should feel like a
  continuation rather than a deliberate cut.

Give every unit a stable ID, for example `SEQ02_SC03_SH02`. Keep IDs stable when
rewriting prompts so rendered files and manifests remain traceable.

For each scene, state the dramatic change as:

`objective -> obstacle -> action -> turn -> exit state`

If a scene has no change, compress it, use it as a visual breath, or identify
the missing source of tension. Do not split a story into arbitrary equal-length
clips; split at narrative and production boundaries.

## Design a scene card

Record these fields:

- **Story:** purpose, beat, objective, obstacle, turn, emotional entry/exit.
- **World:** location, time, weather, geography, background anchors, props,
  wardrobe, and what must not change.
- **Subjects:** canonical identity tokens, pose, gaze, screen direction,
  relationships, and state carried in from the previous shot.
- **Cinematography:** shot size, angle, lens feel, camera position, movement,
  composition, depth, lighting, palette, and transition intent.
- **Action:** a short ordered list of visible beats with approximate timing.
- **Audio:** dialogue, speaker, sound effects, ambience, music cue, and what
  must continue across the seam.
- **Generation:** mode (`t2v`, `i2v`, `first_last`, `reference`, `edit`), model
  family, duration, endpoint images, references, seed policy, and acceptance
  checks.

Describe visible actions, not abstract outcomes. Replace "show that she feels
betrayed" with an observable choice such as "she lowers the letter, steps out
of the light, and stops answering his gaze."

## Design shots for visual storytelling

Choose a shot because it changes what the audience knows or feels. Use a small
coverage vocabulary deliberately:

- establishing/wide for geography and stakes;
- medium or over-the-shoulder for interaction and screen direction;
- close-up for an irreversible emotional or narrative beat;
- insert/detail for evidence, props, or a match-cut object;
- reaction or held frame for consequence and pacing.

Preserve screen geography within a scene. Establish the axis before crossing
it; if the story needs a crossing, motivate it with a visible camera move or a
neutralizing shot. Track the direction of travel, eyelines, hand used, prop
state, and camera motion. Use a cut, not a generated morph, when discontinuity
is the intended meaning.

Plan duration from the action's readability and the model's tested range. Put
the story beat near the middle of a clip when the next scene must inherit a
stable pose; reserve the final frames for a clean handoff rather than motion
blur, occlusion, or an expression still changing.

## Lock continuity without freezing the story

Separate **immutable anchors** from **variable performance**.

Immutable anchors usually include:

- character identity and distinguishing features;
- wardrobe, carried props, environment architecture, and time of day;
- art direction, palette, texture, aspect ratio, FPS, and rendering style;
- camera grammar, lens feel, axis, and sound-world rules.

Variable performance includes gesture, expression, blocking, camera movement,
weather intensity, and local action. Change only a few variables per scene so a
model has a plausible bridge between states.

Reuse canonical anchor text verbatim. Add scene-specific state after the anchor
instead of rewriting the character description with new synonyms. Pass a short
continuity ledger forward:

`where the subject is -> what the subject is doing -> what the camera is doing ->
what must be true in the final stable frame -> what the next shot must begin with`

Use reference images/videos/audio for a defined job. Prefer one strong identity
reference and one environment/style reference over a pile of conflicting
references. Label references in the same order used by the target model.

## Write a generation prompt packet

Build each packet in this order:

```text
GLOBAL STYLE LOCK: [canonical visual language, palette, aspect, rendering rules]
CHARACTER / WORLD LOCK: [verbatim identity and environment anchors]
SCENE STATE: [location, time, entry pose, prop state, emotional state]
VISIBLE ACTION: [one ordered action arc; use concrete verbs]
CAMERA: [framing, lens feel, angle, movement, screen direction]
TEMPORAL BEATS: [only if the model supports timed beats; keep them sparse]
AUDIO: [dialogue with speaker, ambience, SFX, music, continuation cue]
EXIT / CONTINUITY: [final stable pose, gaze, object state, next-shot handoff]
EXCLUSIONS: [unwanted identity changes, extra limbs, text errors, axis breaks]
```

Keep prompt responsibilities separate. The global lock should not contain new
action; the scene block should not redefine the character; the exit block should
not introduce an unplanned prop. For MiniMax H3, include audio in the same
packet and use its reference tags exactly; for other models, adapt the packet to
their conditioning interface instead of carrying H3 syntax over blindly.

## Plan transitions between scenes

Choose the transition before generating the two clips:

- **continue:** reuse the last stable frame of the prior clip as the next
  first-frame input;
- **bridge:** generate a short first/last-frame transition from the prior tail
  to the next target keyframe;
- **cut:** end on a readable outgoing frame and begin on a deliberate incoming
  frame; use when the story benefits from discontinuity;
- **dissolve/optical flow:** use as editorial punctuation only after matching
  geometry, FPS, and timing; it cannot repair a mismatched subject or scene;
- **match cut:** end and begin on a common shape, motion vector, sound, or prop,
  and record the shared motif in both shot cards.

For a seamless continuation, specify the handoff state rather than saying
"make it seamless." Name the exact outgoing frame, incoming pose, gaze, camera
vector, screen direction, lighting, prop position, and audio beat. Avoid ending
on an occluded face or a fast pan unless the next clip deliberately uses that
occlusion or motion as the bridge.

Read [transition-patterns.md](references/transition-patterns.md) when selecting
the ComfyUI graph and when chaining more than two scenes.

## Prepare the ComfyUI handoff

For each shot segment, export:

- a prompt packet and canonical anchor version;
- source references with stable filenames;
- target width, height, FPS, frame count, audio settings, and seed policy;
- the generation mode and workflow JSON to run;
- a scene output path and a tail-frame extraction path;
- the next shot's required first frame or bridge target;
- acceptance checks and a `pending`, `approved`, or `rejected` status.

Generate sequentially when continuity matters: approve the prior tail before
locking the next shot. Generate in parallel only for independent shots or when
their entry keyframes have already been fixed. Preserve every source clip,
bridge clip, extracted keyframe, workflow, prompt, and manifest so a single bad
scene does not force a full rerender.

## Review before generation

Reject or revise a storyboard when:

- a scene has no objective, obstacle, turn, or visual consequence;
- a prompt asks for several unrelated locations, actions, or camera setups in
  one short generation segment;
- the next scene changes identity, wardrobe, geography, axis, or lighting without
  an intentional transition;
- the outgoing frame has no stable state that the next shot can inherit;
- dialogue lacks a speaker or the audio cue has no timing/continuity note;
- the requested duration, FPS, frame grid, or model mode is unspecified;
- the handoff says "seamless" but contains no concrete state or endpoint.

Return the final storyboard as a compact scene table plus the full manifest and
prompt packets. Explain any creative tradeoff in one sentence per scene, not in
a long unstructured narrative.
