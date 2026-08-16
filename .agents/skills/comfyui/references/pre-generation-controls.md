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
  "wardrobe_surface_contract": {
    "contract_id": "WSC_CHARACTER_01_R03",
    "canon_revision": "CANON_R03",
    "canonical_source": "references/character.png",
    "wardrobe_lock": [
      {"component_id": "GARMENT_01", "region": "torso", "observable_description": "exact garment construction", "material_or_texture": "declared material", "color_or_markings": "declared color/markings", "visibility_policy": "occluded_preserve"}
    ],
    "surface_state_lock": [
      {"region_id": "SURFACE_01", "region": "left_sleeve", "state": "muddy", "extent_or_intensity": "declared extent", "confidence": "exact", "source_evidence": "references/character.png"}
    ],
    "transition_policy": {"default": "inherit", "allowed_deltas": [{"from": "muddy", "to": "dry_muddy", "reason": "declared elapsed time", "scope": "shot_02"}]},
    "occlusion_policy": "occluded_preserve",
    "forbidden_implicit_changes": ["category_swap", "recolor", "missing_accessory", "clean_reset", "dropped_surface_region"]
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
- Require the versioned canonical `wardrobe_surface_contract` for every
  recurring character or prop. Record visible garment/accessory regions and
  region-level dirt, mud, wetness, or damage; repeat the full opening state in
  every shot prompt, endpoint reference, and compiled graph. Later segments may
  apply only typed, scoped transitions. Generic “uniform” wording, a clean
  reset, recolor, alternate costume, missing accessory, dropped region, or
  undeclared removal is a blocking semantic failure.

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
- `WARDROBE_SURFACE_STATE_UNBOUND`
- `WARDROBE_SURFACE_CONTRACT_STALE`
- `SURFACE_STATE_TRANSITION_UNDECLARED`

Post-render inspection may find stochastic failures that survive these controls,
but it must not be used to excuse a missing pre-generation control.
