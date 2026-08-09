# New project workspace

Copy this directory to `projects/<project-id>/` and keep all project-specific
inputs, plans, generated artifacts, logs, and helper scripts inside that
directory.

Recommended first directories:

```text
seeding_material/
inputs/references/
plan/
compiled/
orchestrator/runs/
orchestrator/state/
scripts/
renders/
```

Use a stable unique project ID such as `PRJ02`. Keep reusable behavior in the
repository root rather than copying toolkit code into the project workspace.
