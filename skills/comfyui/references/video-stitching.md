# ComfyUI video stitching patterns

Use this file for the boundary between two or more generated scene clips. The
goal is temporal and semantic continuity, not merely a playable MP4.

## Choose a seam

| Seam | Use when | ComfyUI pattern | Main risk |
| --- | --- | --- | --- |
| Continuation | S02 should begin where S01 ends | extract S01 tail -> feed as S02 `first_frame`/I2V input -> generate S02 | copied pose but changed motion, identity, or lighting |
| First/last bridge | S02 has a known entry keyframe | feed S01 tail and S02 target keyframe to a first/last-frame-capable video node -> generate only the bridge | endpoint geometry too different for the bridge duration |
| Reference continuation | identity/style must persist while action changes | pass approved still/video/audio references plus a focused prompt | reference consistency without motion continuity |
| Editorial cut | discontinuity is intentional or generation cannot bridge it | trim and concatenate normalized clips | visible jump if the outgoing/incoming frames are not readable |
| Dissolve or optical-flow blend | short punctuation, time passage, or matching compositions | decode frames, normalize, blend/interpolate, re-encode | double exposure and ghosting on unrelated motion |
| Match cut | a shape, prop, sound, or motion carries meaning across locations | plan a shared motif in both shot cards, then cut or bridge on it | visual similarity without narrative motivation |

Use continuation as the default for an unbroken action. Use a bridge when there
is a real change of state. Use a cut when the story wants a new space, time, or
point of view. Never call a simple crossfade a semantic continuation.

## Single handoff recipe

1. Render and approve S01.
2. Decode S01 to frames and select the last **stable** frame, not an occluded,
   blurred, or mid-blink frame. Save it with a stable name such as
   `S01_SH03_tail.png` and record its source frame index.
3. Write S02's entry state from that actual image: subject position, gaze,
   pose, prop state, lighting, camera direction, and background geometry.
4. Feed the tail frame into S02's first-frame/I2V input. Keep the global style
   and identity anchors identical; change only the new action and camera intent.
5. Generate a short proof and inspect the first 8-12 frames at the target FPS.
   Approve, revise, or regenerate before committing the full shot.
6. Store S02's stable tail as the input candidate for S03.

If the endpoint itself must change, add a target end frame and generate a bridge
clip. Trim the repeated first/last endpoint frame before assembly.

## Bridge recipe

Use a dedicated transition job rather than hiding the transition inside S02:

```text
S01 approved video
  -> decode -> select tail window / final stable frame

S02 planned keyframe
  -> load or generate target entry frame

tail frame + target keyframe + bridge prompt
  -> first/last-frame-capable video conditioning
  -> sample a short bridge
  -> decode and inspect

S01 (trim duplicated tail) + bridge (trim duplicated endpoints) + S02
  -> normalize -> batch/concatenate -> encode -> mux audio -> save
```

For MiniMax H3 in this workspace, the current `MiniMaxH3ImageToVideo` node
accepts optional `first_frame` and `last_frame` inputs. Use the exact live node
schema and valid H3 frame grid; do not assume every installed video model has
the same endpoint behavior. If only I2V is supported, let the bridge begin from
S01's tail and use an editorial cut into S02's target frame.

## Multi-scene chain

Represent a long project as a directed chain, not a single giant graph:

```text
S01 -> H01 -> S02 -> H02 -> S03 -> ... -> H(n-1) -> Sn
```

Each scene job should emit:

- decoded video and final encoded video;
- one or more candidate tail frames;
- prompt, workflow, seed, model stack, FPS, resolution, and frame count;
- a continuity state and an approval status.

Each bridge job should emit its own clip and a record of endpoint frame indices.
This lets one failed seam be regenerated without changing approved scenes.

For an assembly-only graph, use `LoadVideo`/VideoHelperSuite when encoded clips
must be decoded, `ImageFromBatch` to select ranges, `ImageBatch` or `Batch Images`
to stack frames, and `CreateVideo` or `VHS_VideoCombine` to encode. Match width,
height, frame rate, frame order, pixel format, color treatment, and audio sample
rate before stacking. Do not concatenate clips with different timing and hope
the encoder repairs it.

## Boundary QA

Inspect the last 0.5 seconds of S(n), the first 0.5 seconds of the bridge/S(n+1),
and the assembled seam at normal speed and frame-by-frame. Check:

- same character identity, wardrobe, and prop state;
- same gaze, screen direction, motion vector, and camera axis;
- no duplicate or missing frame at the join;
- no flash caused by resizing, color conversion, or VAE mismatch;
- audio does not restart, drift, or click unless intended;
- the transition expresses the story beat rather than only hiding a failure.

Frame interpolation can smooth cadence or create intermediate motion, but it
cannot guarantee identity or physical plausibility. Apply it after semantic
continuity is solved and keep the pre-interpolation render.
