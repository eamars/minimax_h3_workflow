# Compact worked example

Use this reference when a concrete end-to-end example helps. It is intentionally compact; real outputs must still populate the complete `plot_package` contract and leave non-applicable categories explicitly empty.

## Contents

- [Input](#input)
- [Interpretation](#interpretation)
- [Story core](#story-core)
- [Timed beats](#timed-beats)
- [Storyboard handoff](#storyboard-handoff)

### Input

```text
A 10-second video showing Kazusa having a shower.
```

### Interpretation

```yaml
interpretation:
  fidelity_mode: balanced
  primary_unit_type: ritual_or_procedure
  secondary_unit_types: [vignette, micro_arc]
  plot_engine: observational
  invention_log:
    - "added small shower actions to create readable progression"
    - "added a subtle change from relaxed contentment to playful satisfaction"
```

### Story core

```yaml
story_core:
  premise: "Kazusa enjoys a relaxed shower and becomes briefly playful with her reflection."
  narrative_function: "character intimacy, relaxation, and playful personality"
  primary_unit_type: ritual_or_procedure
  plot_engine: observational
  audience_promise: "a calm, tactile, self-contained shower moment"
  opening_state: "Kazusa is already showering, relaxed, with foam on one shoulder"
  subject_intention_or_activity: "continue washing and enjoy the shower"
  progression_driver: "ordered shower actions and an attention shift toward her reflection"
  central_change: "quiet contentment becomes playful self-awareness"
  closing_state: "a small splash completes and Kazusa settles into playful satisfaction"
  emotional_entry: "relaxed contentment"
  emotional_exit: "playful satisfaction"
  external_stakes: null
  internal_stakes: null
  larger_context_required: false
```

### Timed beats

```yaml
beats:
  - id: SEQ01_SC01_B01
    time_range_seconds: "0.0-2.5"
    plot_jobs: [establish, characterize]
    trigger: "the scene begins while the shower is already running"
    subject_intention_or_attention: "enjoy the shower"
    required_visible_event: "Kazusa remains relaxed under running water and hums softly"
    action: "she settles under the water with foam visible on one shoulder"
    immediate_result: "the activity and mood become clear"
    reaction: "her expression remains content"
    emotional_entry: "content"
    emotional_exit: "content"
    information_change: "the audience understands this is a relaxed private routine"
    physical_state_change: "hair and shoulders continue becoming wet"
    must_show: ["Kazusa", "active shower", "relaxed state", "foam on shoulder"]
    may_imply: ["steam", "secondary bathroom detail"]
    story_audio_cue: "continuous shower and soft wordless humming"
    continuity_in: "already showering"
    continuity_out: "foam remains available for the next action"
    next_beat_link: "her attention moves to the foam"
    generation_risks: ["water continuity", "hair wetness continuity"]
    model_handoff:
      timeline_ready: true
      single_primary_action: true
      stable_entry_state_defined: true
      stable_exit_state_defined: true
      story_audio_timed: true
      likely_generation_group: [SEQ01_SC01_B01, SEQ01_SC01_B02]
      split_reason: null
      reference_dependencies: []

  - id: SEQ01_SC01_B02
    time_range_seconds: "2.5-5.0"
    plot_jobs: [progress, characterize]
    trigger: "foam remains on her shoulder"
    subject_intention_or_attention: "continue washing"
    required_visible_event: "Kazusa wipes foam from her shoulder"
    action: "one hand clears part of the foam"
    immediate_result: "foam decreases and wet trails remain"
    reaction: "she follows the movement with mild interest"
    emotional_entry: "content"
    emotional_exit: "content with emerging playfulness"
    information_change: "the routine becomes tactile and specific"
    physical_state_change: "foam decreases; wetness increases"
    must_show: ["clear hand-to-shoulder action", "visible foam-state change"]
    may_imply: ["small bubbles continuing downward"]
    story_audio_cue: "continuous shower"
    continuity_in: "foam present"
    continuity_out: "foam partly removed and hand action completed"
    next_beat_link: "the result redirects her attention toward the mirror"
    generation_risks: ["hand anatomy", "foam motion"]
    model_handoff:
      timeline_ready: true
      single_primary_action: true
      stable_entry_state_defined: true
      stable_exit_state_defined: true
      story_audio_timed: true
      likely_generation_group: [SEQ01_SC01_B01, SEQ01_SC01_B02]
      split_reason: null
      reference_dependencies: []

  - id: SEQ01_SC01_B03
    time_range_seconds: "5.0-7.5"
    plot_jobs: [turn, characterize]
    trigger: "Kazusa notices her reflection during the routine"
    subject_intention_or_attention: "enjoy the playful moment"
    required_visible_event: "she acknowledges the reflection with a subtle teasing expression"
    action: "her attention shifts and she responds playfully"
    immediate_result: "the mood becomes self-aware and teasing"
    reaction: "she holds the expression long enough to read"
    emotional_entry: "soft contentment"
    emotional_exit: "playful satisfaction"
    information_change: "the audience sees a mischievous side of her personality"
    physical_state_change: "no major reset"
    must_show: ["mirror relevance", "readable playful response"]
    may_imply: ["minor pose adjustment"]
    story_audio_cue: "humming gives way to quiet breathing"
    continuity_in: "foam partly cleared; shower active"
    continuity_out: "playful mood established"
    next_beat_link: "playfulness motivates a final splash"
    generation_risks: ["reflection consistency", "identity consistency"]
    model_handoff:
      timeline_ready: true
      single_primary_action: true
      stable_entry_state_defined: true
      stable_exit_state_defined: true
      story_audio_timed: true
      likely_generation_group: [SEQ01_SC01_B03]
      split_reason: "reflection consistency may require isolation"
      reference_dependencies: ["mirror staging"]

  - id: SEQ01_SC01_B04
    time_range_seconds: "7.5-10.0"
    plot_jobs: [pay_off, release, resolve]
    trigger: "the playful mood is established"
    subject_intention_or_attention: "finish the moment with one expressive action"
    required_visible_event: "Kazusa cups water, splashes her shoulders, and settles"
    action: "she performs one deliberate splash"
    immediate_result: "fresh droplets spread across her shoulders and hair"
    reaction: "she ends with a satisfied playful expression"
    emotional_entry: "playful satisfaction"
    emotional_exit: "settled playful satisfaction"
    information_change: "the character beat receives a visible payoff"
    physical_state_change: "shoulders and hair become freshly wetter"
    must_show: ["one intentional splash", "stable ending"]
    may_imply: ["secondary droplets", "small follow-through"]
    story_audio_cue: "one clear splash over continuous shower sound"
    continuity_in: "playful expression established"
    continuity_out: "splash completed; stable final state"
    next_beat_link: null
    generation_risks: ["two-hand interaction", "dynamic water", "stable exit"]
    model_handoff:
      timeline_ready: true
      single_primary_action: true
      stable_entry_state_defined: true
      stable_exit_state_defined: true
      story_audio_timed: true
      likely_generation_group: [SEQ01_SC01_B04]
      split_reason: "two-hand splash and fluid motion may require isolation"
      reference_dependencies: []
```

### Storyboard handoff

```yaml
storyboard_handoff:
  story_brief:
    logline: "During a relaxed shower, Kazusa moves from quiet contentment to a playful moment with her reflection and ends with a light splash."
    narrative_function: "character vignette and sensory interlude"
    unit_type: "ritual vignette with a micro emotional arc"
    runtime_seconds: 10
    emotional_change: "contentment -> playful satisfaction"
    ending_state: "splash completed, Kazusa settled, shower still running"

  sequence_map:
    - id: SEQ01
      purpose: "develop a relaxed routine into playful self-awareness"
      entry_condition: "Kazusa is already showering"
      progression: "routine -> tactile action -> mirror awareness -> playful release"
      turn_or_attention_shift: "she notices and responds to her reflection"
      exit_condition: "the splash completes and the expression settles"

  scene_seeds:
    - id: SEQ01_SC01
      sequence_id: SEQ01
      purpose: "deliver the shower vignette in one place and continuous time"
      entry_state: "relaxed, foam present, shower active"
      required_events:
        - "relaxed shower establishment"
        - "foam-wiping action"
        - "playful mirror acknowledgment"
        - "intentional splash and stable ending"
      progression_or_turn: "quiet contentment becomes playful self-awareness"
      exit_state: "freshly wet, playful expression settled, shower active"
      story_audio_events: ["continuous shower", "soft humming early", "one final splash"]
      continuity_requirements:
        - "hair becomes progressively wetter"
        - "foam decreases after wiping"
        - "the mirror remains available for the reflection beat"
        - "the emotional direction does not become negative"

  beat_order:
    - beat_id: SEQ01_SC01_B01
      required_order: 1
      can_combine_with_next: true
      split_candidate: {value: false, reason: null}
    - beat_id: SEQ01_SC01_B02
      required_order: 2
      can_combine_with_next: true
      split_candidate: {value: false, reason: null}
    - beat_id: SEQ01_SC01_B03
      required_order: 3
      can_combine_with_next: true
      split_candidate: {value: true, reason: "reflection consistency may require isolation"}
    - beat_id: SEQ01_SC01_B04
      required_order: 4
      can_combine_with_next: false
      split_candidate: {value: true, reason: "two-hand splash and fluid motion may require isolation"}

  must_show:
    - "Kazusa is recognizably showering"
    - "the actions occur in order"
    - "the mood remains relaxed and becomes playful"
    - "foam and wetness change continuously"
    - "the final action completes before the clip ends"

  may_imply:
    - "secondary washing motions"
    - "steam density"
    - "minor transitional gestures"

  must_not_invent:
    - "external danger"
    - "unexpected visitor"
    - "hidden message"
    - "negative emotional turn"
    - "location change"
    - "new narrative prop"

  open_directorial_choices:
    - "framing and shot size"
    - "camera position and movement"
    - "lens and depth strategy"
    - "precise blocking and screen direction"
    - "continuous take versus connected generation segments"
    - "how the mirror beat is visually staged"

  generation_risks:
    - element: "water and foam"
      risk: "fluid-state drift"
      downstream_note: "keep each beat's fluid action simple and preserve state changes"
    - element: "mirror reflection"
      risk: "identity and pose mismatch"
      downstream_note: "choose a staging method that protects reflection continuity"
    - element: "two-handed splash"
      risk: "hand anatomy and uncontrolled water motion"
      downstream_note: "consider isolating the payoff action"

  acceptance_tests:
    - "the storyboard preserves a vignette rather than inventing conflict"
    - "the first beat establishes showering and relaxed mood"
    - "each beat follows naturally from the previous beat"
    - "foam and wetness states remain consistent"
    - "the mirror beat communicates playfulness, not a new revelation"
    - "the splash completes before a stable final state"
    - "camera choices remain downstream director decisions"
```

This example is one balanced interpretation, not a mandatory shower plot. Rebuild it whenever the user supplies a different mood, action, or story purpose.
