# MiniMax H3 routing and prompt syntax

Read this reference after the director plan and shot cards are locked. Do not
let model syntax replace dramatic decomposition, blocking, or continuity work.

## Contents

- [Route selection](#route-selection)
- [Technical profile](#technical-profile)
- [Base prompt family](#base-prompt-family)
- [Full-reference prompt family](#full-reference-prompt-family)
- [Dialogue and sound](#dialogue-and-sound)
- [Prompt construction](#prompt-construction)

## Route selection

Select the family before writing the prompt:

| Family | Use | ComfyUI route |
| --- | --- | --- |
| T2VA | No visual endpoint or reference media | H3 T2V, fl2va |
| I2VA | Fixed opening image, forward motion | H3 I2V, first_frame, fl2va |
| FL2VA | Fixed opening and ending images | H3 first/last-frame workflow, first_frame + last_frame, fl2va |
| L2VA | Fixed ending image only | Supported I2V workflow, last_frame, fl2va |
| R2VA | Identity, world, style, motion, camera, rhythm, voice, or sound references | H3 R2V, ref2va, ordered Picture/Video/Audio tags |

Use R2VA for source-video editing, structural reference, or continuation, but
state whether the source supplies footage, a continuation point, camera motion,
rhythm, action, copied audio, or audio reference.

Do not mix official endpoint-frame and full-reference roles in one request or
native workflow unless a tested custom graph supports it. When both identity
references and precise endpoints are required, create identity-consistent
endpoint stills, approve them, and use those stills in FL2VA.

H3-Context-IR may enhance a locked prompt, but compare its result with the
approved shot card and reject changes to shot order, identity, blocking, camera
intent, dialogue, reference jobs, or ending state.

## Technical profile

Use the installed workflow’s values when they differ. Otherwise record:

~~~
model: MiniMax-H3
fps: 24
audio_sample_rate: 32000
audio_channels: stereo
duration_seconds: 4_to_15_integer
resolution:
  draft: native_768_short_edge
  final: 2K_when_supported
resolution_multiple: 32
prompt_language: English
prompt_limit_chars: 7000
~~~

Practical reference limits are usually up to 9 images, 3 videos, 3 audio files,
and 12 mixed reference files; treat these as environment-dependent and record
the actual node/API limits in the manifest.

## Base prompt family

Use for T2VA, I2VA, FL2VA, and L2VA. Write in English except for dialogue,
user-supplied lyrics, and visible text.

### Three core fields

~~~
integrated_multimodal_description: [Shot 1] ...

[Shot 2] At 00:03.500, the camera cuts to...

overall_soundscape: ...

non_diegetic_music: ...
~~~

integrated_multimodal_description must cover visual medium/style, initial
composition, subject appearance/placement, environment/props, blocking/state
changes, camera framing/movement, cuts and timestamps, dialogue/singing, and
synchronized diegetic sound. The first shot has no timestamp; later timestamps
must increase strictly and remain inside the effective duration. Use ordinary
cut language unless a dissolve, fade, or wipe is deliberate.

overall_soundscape is one paragraph of one to four sentences covering
ambience, physical action sounds, environmental sounds, and non-verbal human
sounds. Do not repeat dialogue or score. Use N/A only for complete silence.

non_diegetic_music is one to three sentences describing audience-only music
through instrumentation, tempo, rhythm, and dynamic development. Use N/A if
there is no score.

### Endpoint prefixes

For I2VA, put this exact structural line before the three fields:

~~~
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.
~~~

Start from the image’s actual composition and describe the forward motion
instead of repeatedly redescribing a static frame.

For FL2VA:

~~~
How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video.
~~~

Describe first-frame state, observable intermediate changes, narrowing
differences, and exact last-frame landing.

For L2VA:

~~~
How the reference pictures align with the target video — <Picture 1> (from [Shot N]) aligns with the S.SS-second mark of the target video.
~~~

Infer a plausible earlier state and describe convergence in subject, object,
camera, lighting, and composition.

## Full-reference prompt family

Use for R2VA. Keep this exact section order:

~~~
subject_definitions:

summary:

retention_analysis:

detailed_description:

overall_soundscape:

non_diegetic_music:
~~~

### Reference labels

- **Subject N:** reusable visible content abstracted from one or more
  references: person, animal, object, environment, clothing, prop, interface,
  effect, style, action, expression, or pose.
- **Picture N:** standalone only when the image is a concrete frame, storyboard,
  composition, viewpoint, or shot-planning anchor. If it only defines identity,
  costume, environment, or style, cite it inside a subject.
- **Video N:** whole-video editing, continuation, camera movement, cuts, rhythm,
  or temporal structure. Visible content from it still receives a subject label.
- **Audio N:** copied audio, voice timbre/delivery, music, lyrics, sound
  texture, rhythm, or audio continuity. Number each category separately.

### Section requirements

subject_definitions gives every tracked asset one line stating what it is, its
source, its job, and the features that matter.

summary begins with one or more applicable prefixes, joined with +:
reference generation, keyframe completion, video editing, video continuation,
audio reuse, and audio reference. Do not call a camera/rhythm reference editing
or continuation when it is only reference generation.

retention_analysis gives one testable line per label. Visible relationships are
fully_preserved, partially_preserved, attribute_transfer, and weak_reference;
audio relationships are fully_copy, partially_copy, reference, and
weak_reference.

detailed_description is the playback-order prompt. State the overall medium
and style before Shot 1; for each shot cover composition, subject,
environment/light, action/state change, camera, current sound, and where each
reference applies. Remove redundancy before removing blocking, camera, or
timing information.

## Dialogue and sound

Assign stable speaker IDs in order of actual vocal events: (S1), (S2), and so
on. Keep IDs across shots. When a referenced subject speaks, write for example
Subject 2 (S1).

Put only words and language inside the d tag:

~~~
The young woman with a quiet, breathy voice (S1) says, <d>[English] I get off at the next station.</d>
~~~

Preserve user-supplied dialogue verbatim. For voiceover, say “in an off-screen
voiceover”; if the character remains visible, state that the lips remain
closed. If a line crosses a cut, use the scenetrans tag, state that audio
continues, and preserve the speaker ID. Use the cutoff tag when speech ends
abruptly at the video boundary. Put visible text in English double quotation
marks, preserving requested characters and punctuation.

Keep layers separate:

1. dialogue, singing, and timed diegetic events in the shot description;
2. ambience and physical sounds in overall_soundscape;
3. audience-only music in non_diegetic_music.

## Prompt construction

Build each packet in this order, then convert it to the selected H3 family:

~~~
REFERENCE ASSIGNMENT
GLOBAL STYLE LOCK
CHARACTER / WORLD LOCK
DIRECTORIAL INTENT
ENTRY STATE
BLOCKING
VISIBLE ACTION
CAMERA
TIMED SHOT OR BEAT STRUCTURE
DIALOGUE AND DIEGETIC SOUND
EXIT / HANDOFF
EXCLUSIONS
~~~

Use concrete nouns and verbs, put the overall scene before timed shots, keep
camera and audio inside the same temporal structure as action, reuse canonical
anchors verbatim, and do not redefine a character in every shot. Avoid
contradictory commands and vague phrases such as “cinematic flow,” “dynamic
camera,” or “same character” without observable conditions. State exclusions
only when they resolve likely failure modes.
