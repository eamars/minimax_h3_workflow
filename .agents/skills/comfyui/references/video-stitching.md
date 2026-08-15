# ComfyUI video stitching patterns

Use this reference at the boundary between generated clips. The goal is
temporal and semantic continuity, not merely a playable MP4.

## Choose a seam

| Seam | Use when | ComfyUI pattern | Main risk |
| --- | --- | --- | --- |
| Serial continuation | The next segment continues the same shot | relay the predecessor's actual decoded final frame into the successor first-frame input | copied pose but changed motion, identity, or lighting |
| First/last bridge | The successor has a distinct declared entry keyframe | condition a short bridge on the predecessor endpoint and target entry frame | endpoint geometry too different for the bridge duration |
| Reference re-establish | A scene cut should reset drift while preserving canon | start from the declared character/environment reference set | reference consistency without motion continuity |
| Editorial cut | Discontinuity is intentional | normalize, trim, and concatenate clips | an unreadable outgoing or incoming frame |
| Dissolve | Time passage or punctuation is intended | decode, normalize, blend, and re-encode | ghosting on unrelated motion |

Use serial continuation for unbroken action, a bridge for a real state change,
and a cut when the story changes space, time, or point of view. A crossfade is
not semantic continuation.

## Serial continuation recipe

1. Render and decode the predecessor.
2. Inspect the full clip and the last 12 frames for identity, anatomy, props,
   environment, lighting, camera, motion, and audio continuity.
3. Extract the **actual final decoded frame**. Do not silently substitute an
   earlier attractive frame; revise or rerender a bad endpoint.
4. Bind that image exactly to the successor first-frame/I2V input and require
   successor frame zero to equal the bound endpoint.
5. Repeat the character description and room/lighting description verbatim.
6. Give later shots an approximately two-second opening airlock with only
   micro-motion, then land in a settled state about two seconds before the end.
7. Keep each spoken line inside one shot. Camera cuts may occur within a shot;
   continuity state transfers between shots.
8. For long chains, restart from the reference set at a scene cut before drift
   compounds.

If the chain changes scene, shot setup, lens, or visual context, never encode
that change at a generation boundary. Preserve the old context through the
opening airlock, execute one declared transition in the 40–60% middle of the
transition-bearing segment, and use the remaining time to establish the new
context. The successor must begin from that established final frame and must
not repeat the transition.

These prompt and timing rules follow the MiniMax H3 multishot workflow at
<https://huggingface.co/joeygambino/MiniMax-H3-Multishot-Workflow>.

## Bridge recipe

```text
predecessor decoded endpoint
  + declared successor entry keyframe
  + focused bridge prompt
  -> first/last-frame-capable conditioning
  -> short bridge render
  -> endpoint and full-clip QC
  -> ordered assembly
```

The local `MiniMaxH3ImageToVideo` node may expose optional `first_frame` and
`last_frame` inputs. Always inspect the live node schema and use the valid H3
frame grid; do not assume every installed video model supports both endpoints.

## Assembly

Represent a long project as a directed chain:

```text
S01 -> S02 -> S03 -> ... -> Sn
```

Each segment records its workflow revision, seed, model stack, FPS, resolution,
frame count, continuity state, endpoint frame, and QC result. Normalize width,
height, frame rate, frame order, color, codec, and audio before concatenation.
Remove a shared boundary frame only when the two decoded frames are pixel
identical; never hide a discontinuity with an unconditional frame drop.

## Boundary QA

Inspect the last half-second of the predecessor, the first half-second of the
successor or bridge, and the assembled seam at normal speed and frame by frame.
Check identity, wardrobe, limb/prop state, gaze, screen direction, motion
vector, camera axis, lighting, duplicate/missing frames, audio restarts, drift,
and clicks. Frame interpolation may smooth cadence after semantic continuity is
correct; it cannot repair identity or physical plausibility.
