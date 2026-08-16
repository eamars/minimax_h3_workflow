# Wardrobe and Surface-State Contract

Use this contract for every recurring character or prop whose visible design or
physical surface must persist across shots. It is deliberately domain-neutral:
the same rules cover clothing, accessories, stains, mud, wetness, dust, blood,
tears, scratches, wear, and other observable states.

## Required contract

Emit one versioned `wardrobe_surface_contract` per recurring subject:

- `contract_id` and `canon_revision` — stable provenance for downstream parity.
- `wardrobe_lock` — an inventory of every observable component. Each component
  has a stable ID, body/object region, observable description, material/texture,
  color or markings, and a visibility policy.
- `surface_state_lock` — a region-level map of observable state, extent or
  intensity, confidence, and source evidence. “Dirty” or “wet” alone is not a
  sufficient map.
- `transition_policy` — default `inherit`; enumerate every permitted delta
  (`add`, `dry`, `wet`, `clean`, `repair`, `tear`, `remove`, or equivalent) with
  its source state, destination state, reason, and phase/shot scope.
- `occlusion_policy` — `occluded_preserve` by default. Out of frame, blur, or
  lighting loss never means removed, clean, or unknown unless explicitly stated.
- `forbidden_implicit_changes` — at minimum costume category swaps, recolors,
  missing accessories, unannounced cleaning, and dropped surface regions.

Keep design identity separate from temporal surface state. A character may dry,
tear, or remove a garment during an explicitly authored action without changing
the canonical design; the transition must still be declared and carried into
the next state snapshot.

## Propagation and gates

1. Carry the same `contract_id` and `canon_revision` through performance,
   storyboard, preflight controls, prompt packets, compiled graphs, and endpoint
   roles. A copied sentence without the structured contract is insufficient.
2. Serialize the full opening state for every shot/segment and the full closing
   state for every handoff. A successor may add a declared delta, but may not
   rely on the previous prompt or model memory to supply omitted garments or
   surface state.
3. Require semantic parity between the canon inventory, machine-readable
   controls, prompt text, and endpoint evidence. Hashes prove file identity;
   they do not prove wardrobe or surface parity.
4. Block compilation/queueing when the contract is missing, generic, stale,
   contradictory, or only present as post-render acceptance criteria. Use
   `WARDROBE_SURFACE_STATE_UNBOUND` or a more specific transition code.
5. Use post-render QC to detect stochastic drift that survives a passing gate;
   never use it to waive a missing pre-generation lock.

## Minimal acceptance test

For each recurring subject, an independent reviewer can answer: what exact
components are present, where is each visible surface state, what may change in
this segment, and where is the same answer represented in the endpoint and
compiled controls? If any answer depends on a generic noun or hidden model
memory, return `BLOCKED` before generation.
