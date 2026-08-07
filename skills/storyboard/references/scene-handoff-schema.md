# Scene and handoff schema

Use this as a compact JSON/YAML contract between storyboard planning and ComfyUI
execution. Keep paths relative to the project root and use stable IDs.

```yaml
project:
  id: night_train
  format:
    aspect_ratio: 16:9
    width: 864
    height: 480
    fps: 24
    audio_sample_rate: 32000
  global_style_lock:
    - "grounded cinematic realism"
    - "cool moonlight with warm practical highlights"
  canonical_anchors:
    characters:
      mara: "Mara, 31, short black bob, amber raincoat, brass compass"
    world: "late-night coastal train, wet glass, sodium platform lights"
  continuity_rules:
    - "Mara remains screen-right while the train moves left-to-right"
    - "the compass stays in her right hand until scene 04"

scenes:
  - id: SEQ01_SC01_SH01
    sequence: SEQ01
    story:
      purpose: "Establish the missing-person search"
      objective: "Mara searches the empty carriage"
      obstacle: "The train lights flicker and obscure the seats"
      turn: "The compass points toward the locked rear door"
      entry_state: "Mara is standing by the front door, alert"
      exit_state: "Mara faces the rear door with the compass raised"
    world:
      location: "coastal train carriage"
      time: "after midnight"
      props: ["brass compass", "wet timetable"]
    generation:
      mode: i2v
      workflow: "workflows/video_minimax_h3_i2v.json"
      prompt_packet: "prompts/SEQ01_SC01_SH01.txt"
      duration_seconds: 5
      seed_policy: fixed_for_review
    media:
      input_first_frame: "frames/SEQ01_SC01_SH01_in.png"
      output_video: "renders/SEQ01_SC01_SH01.mp4"
      tail_candidates:
        - "frames/SEQ01_SC01_SH01_tail_a.png"
    handoff:
      transition_to: SEQ01_SC02_SH01
      type: continue
      source_tail: "frames/SEQ01_SC01_SH01_tail_a.png"
      target_head: "frames/SEQ01_SC02_SH01_in.png"
      overlap_frames: 1
      stable_state: "Mara faces rear door, compass raised in right hand"
      camera_vector: "slow track backward, no axis crossing"
      audio_beat: "rail clatter continues; low electrical hum begins"
      status: pending
    checks:
      - "compass remains in right hand"
      - "Mara stays screen-right"
      - "rear door is visible in final stable frame"
```

## Required fields

Every shot must have `id`, `story`, `generation`, `media`, and `checks`. Every
continuation or bridge must have `handoff.type`, source/target frame paths,
`overlap_frames`, stable state, and status. Use `cut` when there is no intended
visual continuation; still record the outgoing and incoming frames for editorial
review.

## Status and file naming

Use `pending`, `approved`, or `rejected` for scenes and handoffs. Keep filenames
deterministic:

```text
<scene-id>_in.png
<scene-id>_out.png
<scene-id>_tail_<candidate>.png
<scene-id>.mp4
<from-id>__<to-id>_bridge.mp4
```

Never overwrite an approved render in place. Add a revision suffix or a new
render directory and update the manifest.
