# Real-Cinematic Development Plan — Execution Revision

Status: executed and independently reviewed
Version: v03
Supersedes: [real-cinematic-development-plan-v02.md](real-cinematic-development-plan-v02.md)
Reference failure case: `projects/PRJ01`

## Objective

Make the planning system behave like a real film workflow: editorial shots own
camera and cut decisions; model-sized generation segments implement those shots;
character, geography, performance, and state references stay stable while camera
position and viewpoint are allowed to change with motivation.

## Reviewer-driven corrective steps executed

1. Refreshed all active installed skill packages and added
   `scripts/validate_skill_parity.py`, which compares installed files against the
   workspace package hashes.
2. Strengthened storyboard admission validation for typed geography/zones,
   staging, camera setup/look-at/keyframes/motion/risk, camera interval coverage,
   three time domains, record assembly, bilateral editorial boundaries, J/L audio
   edits, generation handoffs, moving-endpoint evidence, and continuity deltas.
3. Made production-plan validation reuse the same graph-aware v2 storyboard
   validator instead of accepting shallow objects.
4. Added strict downstream v2 schemas for ComfyUI jobs, generation DAGs, QC,
   keyframes, and sound; compiler bindings now require camera/continuity hashes,
   generation relationship/policy, and moving-endpoint capability evidence.
5. Corrected migration to produce a fresh, schema-shaped superseding revision with
   preserved segment timing/IDs, explicit unresolved creative markers, `--dry-run`,
   and a review-blocking migration status. It never reuses the old approval hash.
6. Corrected approval invalidation so technical model-grid resegmentation can be
   non-creative only when camera, continuity, editorial boundaries, generation
   topology, and prompt intent remain unchanged; creative changes still require
   reapproval.
7. Added sanitized PRJ01 baseline/corrected-board examples and expanded the
   executable fixture suite, including sparse single-take acceptance and negative
   cases for the previously accepted malformed topologies.
8. Added test package initializers so default unittest discovery executes unit and
   integration suites together.

## Acceptance evidence

- `python -m unittest discover -s tests -v`: 17 tests passed.
- `python scripts/validate_production_system.py`: passed.
- `python scripts/validate_skill_parity.py --installed-root <active-skill-root>`: 17 active packages matched.
- `python scripts/validate_cinematic_package.py --storyboard tests/fixtures/storyboard-v2-real-cinematic.yaml`: passed.
- `python scripts/migrate_storyboard_v1_to_v2.py --dry-run ...`: passed; migration remains admission-blocked until creative review.
- `git diff --check`: passed; only normal repository line-ending warnings remain.

## Operating rule after implementation

The system may change camera position, viewpoint, optics, and framing between
editorial shots. It may also move the camera inside a shot when the path,
keyframes, motivation, and continuity risk are explicit. Reference bindings lock
the declared character/environment properties and timeline scope; they do not
freeze the camera. A cut, dissolve, or J/L audio decision is never inferred from
the generation relationship.

The next production-specific step is a new approved v2 PRJ01 storyboard revision;
the historical PRJ01 plan and its media remain untouched.
