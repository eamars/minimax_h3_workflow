# Directing, blocking, and continuity

Use this reference while decomposing the story, designing shots, and planning
transitions. Keep the main skill file as the navigation and decision layer.

## Contents

- [Production hierarchy](#production-hierarchy)
- [Intake and story brief](#intake-and-story-brief)
- [Dramatic decomposition](#dramatic-decomposition)
- [Director’s treatment](#directors-treatment)
- [Spatial design and blocking](#spatial-design-and-blocking)
- [Shot design](#shot-design)
- [Four-track timeline](#four-track-timeline)
- [Coverage and transitions](#coverage-and-transitions)
- [Continuity bible](#continuity-bible)
- [Reference map](#reference-map)

## Production hierarchy

Use:

~~~
project -> sequence -> scene -> shot -> generation segment -> frame handoff
~~~

- **Sequence:** a new dramatic movement, strategy, location cluster, or
  emotional phase.
- **Scene:** a material change in location, time, objective, obstacle,
  dramatic question, relationship state, visual grammar, or sound world.
- **Shot:** a discontinuous camera position or viewpoint. Continuous movement
  and internal reframing remain one shot.
- **Generation segment:** a model-sized unit split for duration, action
  complexity, camera reset, endpoint frame, or continuity checkpoint.
- **Frame handoff:** a named state inherited by the next segment: pose, gaze,
  object state, axis, motion vector, lighting, or sound beat.

Use stable IDs such as SEQ01, SEQ01_SC02, SEQ01_SC02_SH03, and
SEQ01_SC02_SH03_SEG01. Keep them unchanged across prompt revisions.

## Intake and story brief

Extract or infer source type, target runtime, platform, aspect ratio, FPS,
genre, tone, audience, visual medium, dialogue language, model/workflow,
references, endpoint frames, and safety constraints. Ask a question only when
the answer would materially change safety, the central premise, or an
irreversible production choice.

Produce this compact brief:

~~~
logline:
protagonist:
protagonist_desire:
obstacle:
stakes:
central_question:
starting_state:
ending_state:
emotional_change:
point_of_view:
audience_experience:
genre:
tone:
visual_medium:
format:
aspect_ratio:
fps:
target_runtime:
~~~

For non-dramatic material, replace conflict with discovery, demonstration,
transformation, ritual, escalation, contrast, or visual pleasure.

## Dramatic decomposition

For each scene, record:

~~~
objective -> obstacle -> action -> turn -> exit state
~~~

Also record audience knowledge at entry and exit, whose moment it is, and the
image, gesture, line, or sound that carries the turn. A scene without change
must be a deliberate breath, suspense hold, atmospheric bridge, visual/musical
refrain, or a candidate for compression/removal.

For each sequence:

~~~
id:
purpose:
entry_state:
movement:
turn:
exit_state:
approx_runtime:
visual_progression:
sound_progression:
~~~

## Director’s treatment

### Point of view

Choose objective observer, protagonist-aligned, another character’s gaze,
omniscient, surveillance/voyeuristic, first-person POV, or unstable/shifting
POV. State when the camera knows more or less than the character.

### Audience distance

Choose distant/observational, socially present, intimate, invasive, trapped,
playful/invited, detached/clinical, or awed by scale. Use shot size, lens feel,
height, movement, and duration to create the distance.

### Information strategy

State what is hidden, what is revealed, when it is revealed, whether the
audience anticipates or discovers it with the character, and what remains
off-screen.

### Emotional camera arc and motifs

Describe a meaningful progression such as:

~~~
observational wide -> socially present medium -> intimate close-up -> isolating pull-out
~~~

Track recurring shapes, colors, reflections, thresholds, objects, light changes,
camera gestures, and sound motifs.

Choose one dominant sequence grammar unless a change is intentional:
locked/composed, slow controlled, character-led tracking, handheld instability,
formal symmetry, floating/dreamlike, aggressive kinetic, or graphic montage.

## Spatial design and blocking

Record set orientation, doors, windows, mirrors, furniture, props, practical
lights, subject marks, paths, camera-safe zones, axis, eyelines, and depth
anchors. A text floor plan is sufficient:

~~~
NORTH: window and desk
WEST: entrance door
CENTER: subject A seated, facing east
EAST: subject B beside lamp
CAMERA AXIS: south-west to north-east
~~~

Each shot needs:

~~~
entry_pose:
body_orientation:
position_in_frame:
gaze_target:
hand_usage:
prop_state:
movement_path:
interaction_partner:
exit_pose:
screen_direction:
~~~

Motivate movement through intention. Preserve readable silhouettes, let one
critical action complete before another begins, and leave stable final frames
when a handoff requires them. Track stateful facts such as which hand holds a
prop, whether a door is open, a glass is full, clothing is wet, hair is loose,
or a light is on. For mirrors, define camera, subject, mirror plane, reflected
gaze, and visible reflection geometry.

## Shot design

Choose each shot because it changes what the audience knows or feels. Useful
purposes include:

- establishing wide: geography, scale, isolation, stakes;
- master: complete interaction and spatial continuity;
- medium: body language and social relationship;
- over-the-shoulder: eyeline and power relation;
- close-up: an earned irreversible beat;
- extreme close-up: decisive detail or sensory emphasis;
- insert: evidence, object state, or tactile action;
- reaction: consequence and audience alignment;
- POV: subjective information;
- reflection: self-awareness, duality, concealment, or play;
- held frame: consequence, tension, or breathing room.

Describe lens behavior only when it contributes: wide-angle for proximity or
spatial tension, normal perspective for social presence, compressed telephoto
for isolation/surveillance, shallow depth for selective attention, and deep
focus for simultaneous relationships. For animation, prioritize perspective,
depth, scale, and composition over photographic jargon.

Specify angle/height (eye, low, high, overhead, ground, canted, shoulder, or
object level) and composition (placement, headroom, lead room, negative space,
occlusion, depth layers, symmetry/imbalance, frame-within-frame, lines,
off-screen space, reflections, and text-safe area).

Camera motion should name motion type, target or motivation, amplitude when
meaningful, and speed when meaningful. Prefer natural H3 terms: push/pull, pan,
truck, tilt, pedestal, arc, tracking, static, shake, POV, or roll. For example:

~~~
The camera pushes in with small amplitude at slow speed toward the folded letter in her hands.
~~~

Use static framing when there is no reason to move. Preserve the 180-degree
axis and screen direction; cross only through a motivated move, neutral shot,
head-on view, overhead reset, or deliberate disorientation.

## Four-track timeline

Every shot has synchronized tracks:

~~~
TIME | PERFORMANCE | CAMERA | SOUND | EDIT / HANDOFF
~~~

Example:

~~~
0.00–1.20 | She studies the letter | Static medium, eye level | room tone, paper creak | establish geography
1.20–3.40 | Her thumb breaks the seal | Slow push toward hands | envelope tears | attention narrows
3.40–5.00 | Her smile disappears | Push settles into close-up | breath stops | hold expression for handoff
~~~

Put the essential beat early enough to read. Leave time for cause, action, and
reaction. Use a brief settle, readable action body, and stable exit handle by
default. Avoid ending on blur, an occluded face, a half-formed expression, or a
prop mid-transition when the next segment needs continuity.

## Coverage and transitions

Build only the coverage needed for geography, performance, information,
reaction, and editorial flexibility. A cut must change information, emotional
distance, viewpoint, time, location, subject priority, rhythm, or scale. If it
only changes distance or a slight angle, prefer motivated camera motion.

Choose the transition before rendering:

- **Continue:** reuse an approved stable tail as the next first-frame input;
  carry only necessary continuity facts.
- **Bridge:** generate from a source tail to a target keyframe with a short
  first/last-frame clip.
- **Cut:** render independent outgoing/incoming shots with clean handles when
  discontinuity is meaningful or continuity is uncertain.
- **Match cut:** share shape, gaze, motion vector, sound, color, or object and
  record the motif in both cards.
- **Dissolve/optical:** use only as punctuation after geometry, timing, and
  visual state match; it cannot repair identity or space.

Every transition must do one job: reveal, conceal, accelerate, breathe, orient,
reframe, shock, or associate. Replace “seamless” with exact pose, gaze, prop,
light, camera vector, direction, and audio state.

## Continuity bible

Lock immutable anchors: identity and age presentation, facial features, body
proportions, hair/accessories, wardrobe, props, architecture, time/light
direction, medium/palette/rendering style, aspect/FPS, camera grammar/axis,
voice identity, and sound-world rules.

Allow variable performance to change expression, gesture, pose, blocking, local
camera movement, weather intensity, damage/wetness, emotional energy, and
motivated lighting emphasis. Change only a manageable number of variables per
segment.

Pass this ledger forward:

~~~
where the subject is
-> pose and gaze
-> hand and prop state
-> emotional state
-> camera action
-> lighting and screen direction
-> required stable tail
-> next opening state
-> continuing audio beat
~~~

## Reference map

Declare a job for every reference and a priority order when sources conflict:

~~~
references:
  - tag: "<Picture 1>"
    file: "identity_01.png"
    job: identity
    copy: [facial identity, hair design, eye color]
    do_not_copy: [source expression, source pose, source background]
    priority: critical
~~~

Useful jobs are identity, costume, architecture, art style, pose/expression,
body mechanics, camera movement, edit rhythm, voice timbre, and sound texture.
A default priority is direct instruction -> identity -> endpoint frames ->
wardrobe/props -> environment -> blocking/action -> camera -> style -> detail.
Change it when the project requires.
