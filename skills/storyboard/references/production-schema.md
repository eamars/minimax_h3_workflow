# Production cards, manifest, and acceptance review

Use this reference to package the approved storyboard for ComfyUI, preserve
reproducibility, and review generated media.

## Contents

- [Scene card](#scene-card)
- [Shot and segment card](#shot-and-segment-card)
- [Production manifest](#production-manifest)
- [Seed policy and paths](#seed-policy-and-paths)
- [Generation order](#generation-order)
- [Acceptance review](#acceptance-review)
- [Final response](#final-response)

## Scene card

Create one per location/time/objective/turn unit:

~~~
id:
sequence:
story:
  purpose:
  objective:
  obstacle:
  action:
  turn:
  entry_emotion:
  exit_emotion:
  audience_entry_knowledge:
  audience_exit_knowledge:
world:
  location:
  time:
  weather:
  architecture:
  background_anchors:
  props:
  wardrobe:
  lighting:
  palette:
  immutable_facts:
direction:
  pov_owner:
  audience_distance:
  dominant_feeling:
  information_strategy:
  camera_energy:
  visual_motif:
  transition_intent:
geography:
  axis:
  screen_direction:
  eyelines:
  subject_marks:
  camera_zone:
audio:
  dialogue_language:
  ambience:
  motif:
  music_strategy:
generation:
  h3_mode:
  model_family:
  target_duration:
  references:
  endpoint_frames:
  workflow:
~~~

## Shot and segment card

Use one card for every shot or generation-sized segment:

~~~
id:
parent_scene:
dramatic_job:
information_change:
emotional_change:
entry_state:
exit_state:
blocking:
  entry_pose:
  body_orientation:
  gaze:
  hand_usage:
  prop_state:
  movement_path:
  screen_direction:
camera:
  shot_size:
  angle:
  height:
  lens_feel:
  position:
  axis:
  composition:
  depth:
  movement:
  movement_motivation:
  amplitude:
  speed:
  horizon:
  reframing_rule:
beat_timeline:
  - time:
    performance:
    camera:
    sound:
    edit_handoff:
audio:
  speakers:
  dialogue:
  diegetic_events:
  soundscape:
  non_diegetic_music:
generation:
  mode:
  h3_prompt_family:
  model_family:
  duration_seconds:
  effective_duration_seconds:
  width:
  height:
  fps:
  frame_count:
  audio_sample_rate:
  seed_policy:
  workflow_json:
  prompt_file:
  references:
  first_frame:
  last_frame:
media:
  output_video:
  output_audio:
  tail_candidates:
  approved_tail:
handoff:
  transition_to:
  type:
  source_tail:
  target_head:
  stable_state:
  camera_vector:
  screen_direction:
  lighting_state:
  prop_state:
  audio_beat:
  overlap_frames:
  status:
checks:
  - testable acceptance criterion
~~~

## Production manifest

Return one YAML or JSON manifest for the complete production contract. Use
relative paths and deterministic filenames.

~~~
project:
  id: project_slug
  title:
  format:
    aspect_ratio: "16:9"
    width: 1344
    height: 768
    fps: 24
    audio_sample_rate: 32000
    audio_channels: stereo
  model_profile:
    model: MiniMax-H3
    comfyui_version:
    h3_node_version:
    prompt_limit_chars: 7000
    resolution_multiple: 32
  global_style_lock:
    - canonical style statement
  canonical_anchors:
    characters: {}
    worlds: {}
    props: {}
    sound: {}
  continuity_rules: []
  assumptions: []
  reference_order:
    pictures: []
    videos: []
    audio: []

sequences: []

shots:
  - id: SEQ01_SC01_SH01_SEG01
    scene_id: SEQ01_SC01
    story:
      purpose:
      objective:
      obstacle:
      turn:
      entry_state:
      exit_state:
    direction:
      pov_owner:
      audience_distance:
      shot_purpose:
      movement_motivation:
    blocking:
      entry_pose:
      exit_pose:
      gaze:
      hand_prop_state:
      screen_direction:
    camera:
      framing:
      angle:
      lens_feel:
      movement:
      axis:
      composition:
    generation:
      mode: t2va
      model_family: fl2va
      workflow: workflows/video_minimax_h3_t2v.json
      prompt_packet: prompts/SEQ01_SC01_SH01_SEG01.txt
      duration_seconds: 5
      effective_duration_seconds:
      width: 1344
      height: 768
      fps: 24
      frame_count:
      seed_policy: fixed_for_review
      ref_image_size:
    media:
      input_first_frame:
      input_last_frame:
      output_video: renders/draft/SEQ01_SC01_SH01_SEG01_r01.mp4
      tail_candidates:
        - frames/SEQ01_SC01_SH01_SEG01_tail_a.png
    handoff:
      transition_to:
      type: cut
      source_tail:
      target_head:
      overlap_frames: 0
      stable_state:
      camera_vector:
      screen_direction:
      lighting_state:
      prop_state:
      audio_beat:
      status: pending
    checks: []
~~~

## Seed policy and paths

Use exploratory for discovery, fixed_for_review while refining a shot,
locked_for_continuity only when it demonstrably helps related segments, and
new_seed_revision after an intentional reset. A shared seed does not guarantee
continuity.

Recommended project structure:

~~~
project_root/
  brief/ bible/ references/ keyframes/ prompts/ workflows/ manifests/
  frames/ renders/draft/ renders/approved/ bridges/ audio/ edit/
~~~

Use deterministic names:

~~~
<segment-id>_in.png
<segment-id>_out.png
<segment-id>_tail_<candidate>.png
<segment-id>_r<revision>.mp4
<from-id>__<to-id>_bridge_r<revision>.mp4
~~~

Never overwrite an approved render; create a revision and update the manifest.

## Generation order

When continuity matters:

1. approve story and shot plan;
2. approve reference assignments;
3. create or approve endpoint keyframes;
4. render the first continuity-critical segment;
5. review identity, blocking, camera, action, sound, and tail;
6. approve one tail frame;
7. lock the next entry state;
8. continue through the chain;
9. generate bridges only after both adjacent shots are approved;
10. assemble the edit and review sound continuity and pacing.

Generate in parallel only for independent shots, fixed entry keyframes,
intentional cuts, or low continuity risk. Preserve workflows, prompts, seeds,
source clips, bridges, extracted frames, and manifest revisions.

## Acceptance review

Review every generation against these testable checks:

### Story and performance

- Dramatic job and intended turn are visible.
- Entry/exit poses, gaze, hand usage, and prop interactions are correct.
- The exit state is readable.

### Identity and world

- Identity, design elements, wardrobe, props, architecture, and light direction
  match the continuity ledger.

### Camera and timing

- Shot size, angle, axis, horizon, move type, target, amplitude, and speed are
  correct.
- Actions occur in order; cut times are legible; cause and reaction have time.
- Movement does not introduce an unintended orbit, zoom, or axis crossing.

### Sound and handoff

- Dialogue belongs to the correct speaker and lip movement matches, or lips
  remain closed for voiceover.
- Physical sounds align; ambience continues where required; music is correctly
  diegetic or non-diegetic.
- Tail/head frames match pose, gaze, prop, light, camera vector, direction, and
  audio beat.

Reject or revise when the shot has no purpose; tracks contradict; a short
segment contains unrelated setups; a camera move is unmotivated/impossible; an
anchor changes unintentionally; a reference has no declared job; H3 tags do not
match connection order; endpoint and reference modes are mixed incorrectly;
speaker identity is unstable; “seamless” has no concrete state; or duration,
frame grid, resolution, workflow, or model family is unspecified.

## Final response

Return the approved work in this order unless prompt-only output is requested:

1. Assumptions
2. Story brief
3. Sequence map
4. Continuity bible and reference map
5. Director’s treatment
6. Scene and blocking cards
7. Compact shot table
8. Four-track beat timelines
9. H3 prompt packets
10. ComfyUI manifest
11. Acceptance checklist

Explain creative tradeoffs in one concise sentence per scene. The final package
must let a director judge intent, a ComfyUI operator select files/settings and
generation order, and an editor identify handles, transitions, sound
continuity, and approved handoff frames.
