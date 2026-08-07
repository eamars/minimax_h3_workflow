# Storyboard transition patterns

Use these patterns to make a boundary legible before choosing ComfyUI nodes.

## Continuation matrix

| Story relationship | Outgoing frame | Incoming frame | Recommended transition |
| --- | --- | --- | --- |
| Same action, same space | stable pose in motion's direction | same pose and direction | shared-tail first-frame continuation |
| Same subject, new action | completed old action | target pose/keyframe | short first/last bridge |
| Passage of time | readable held image or object | changed state with a visual cue | match cut, dissolve, or motivated cut |
| New location, same emotional beat | expressive outgoing close-up | analogous incoming composition | match cut on shape/gaze/sound |
| Deliberate shock or revelation | stable outgoing frame | contrastive incoming frame | hard cut with clean handles |
| Uncertain model continuity | approved end frame | independent start frame | editorial cut; do not pretend it is seamless |

## Handoff language

Write a handoff in state terms:

```text
S01 exits with Mara screen-right, right hand holding the compass at chest height,
eyes fixed on the rear door, camera tracking backward along the carriage axis,
cool moonlight on her left cheek, rail clatter continuous.

S02 begins on that same stable pose and camera axis. The compass needle trembles,
Mara takes one step toward the door, and the warm platform light enters from
screen-left. Preserve the raincoat, brass compass, carriage geometry, and gaze.
```

Avoid vague terms such as "seamless," "same character," or "cinematic flow"
without the observable state that makes them testable.

## Multi-scene planning rules

- Carry only the continuity facts needed by the next scene; keep the full bible
  as a separate source of truth.
- Design a stable outgoing pose every time a future scene must continue the shot.
- Make bridge duration proportional to the state change: a small gesture can
  use a short bridge; a change of location, costume, or time needs a cut, a
  motif, or a longer transition beat.
- Give each transition a narrative job: reveal, conceal, accelerate, breathe,
  orient, or reframe.
- Keep transition jobs separate from scene jobs so one seam can be regenerated.
