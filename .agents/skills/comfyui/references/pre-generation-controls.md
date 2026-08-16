# H3 pre-generation semantic controls

Run these controls before emitting a READY workflow or submitting `/prompt`.
Treat rendered-media QC as verification, never as the first protection against a
known semantic risk.

## Required control document

For a seamless-chain build, declare one top-level `identity_control` and one
`quality_controls` object per shot.

```json
{
  "identity_control": {
    "mode": "persistent_reference",
    "subject_id": "CHARACTER_01",
    "source_path": "references/character.png",
    "input_name": "PROJECT_character.png",
    "prompt_tokens": ["<Picture 1>"],
    "use_as_start_image": true
  },
  "shots": [
    {
      "quality_controls": {
        "subject_instances": [
          {"subject_id": "CHARACTER_01", "max_visible_instances": 1}
        ],
        "dialogue_cues": [
          {
            "speaker_id": "CHARACTER_01",
            "start_seconds": 2.25,
            "end_seconds": 3.50,
            "visibility": "on_screen",
            "visible_from_seconds": 2.00
          }
        ],
        "motion": {
          "mode": "path",
          "subject_id": "CHARACTER_01",
          "from_zone": "doorway-inner-threshold",
          "to_zone": "radio-table",
          "direction": "inward, away from the exterior",
          "forbidden_directions": ["reverse toward the exterior", "re-enter the source zone"],
          "endpoint_state": "standing at the radio table"
        },
        "visual_reset": {"mode": "no_reset"}
      }
    }
  ]
}
```

The simple seamless multishot builder always requires `persistent_reference`
because its continuity contract always contains an identity lock. If no
canonical reference exists, compile independently controlled shots instead.
Use `identity_control.mode: not_applicable` only for a separate single-shot or
catalog workflow whose canon and plan contain no recurring identity requirement;
include a concrete reason. Use `endpoint_image` only in a separately compiled
I2VA/FL2VA endpoint workflow.

## Hard routing rules

- Reject a recurring canonical subject without `persistent_reference` or a
  declared endpoint-image binding appropriate to the selected H3 mode.
- Bind a persistent identity reference to `reference_images`, repeat its exact
  `<Picture N>` role in every prompt, and use a reference-capable checkpoint.
  A first frame or predecessor tail alone is not a persistent identity binding.
- Require `dialogue_cues: []` when no speech is intended. If the prompt contains
  `<d>...</d>`, require a finite speaker window and on-screen/off-screen/J-cut/
  L-cut state. For on-screen speech, require the speaker to be visible no later
  than dialogue onset.
- Require every translational actor move to declare origin, destination,
  direction, forbidden reversal/exit directions, and endpoint state.
- Require a per-subject visible-instance maximum. Use a maximum of one for a
  single canonical character unless the story explicitly calls for duplicates.
- Reject `scene_change`, `shot_cut`, `match_cut`, or `dissolve` inside the simple
  `H3MultishotSampler` seamless-chain builder. Route them to an endpoint bridge,
  reference re-establish, or deterministic editorial assembly graph whose
  destination anchor is validated before generation.
- Treat seed policy as reproducibility/stochastic control, not identity control.
  A fixed or per-shot seed never substitutes for a bound identity reference.

## Queue gate

Allow queueing only when the builder or workflow compiler records
`PRE_GENERATION_VALIDATED`. Block on:

- `PREGEN_CONTROLS_MISSING`
- `CANON_IDENTITY_BINDING_MISSING`
- `SUBJECT_MULTIPLICITY_UNBOUNDED`
- `DIALOGUE_WINDOW_MISSING`
- `SPEAKER_VISIBILITY_UNBOUND`
- `DIALOGUE_TIMING_MISMATCH`
- `ACTOR_PATH_UNSIGNED`
- `TEXT_ONLY_SCENE_RESET_UNSAFE`
- `TEXT_ONLY_VISUAL_RESET_UNSAFE`

Post-render inspection may find stochastic failures that survive these controls,
but it must not be used to excuse a missing pre-generation control.
