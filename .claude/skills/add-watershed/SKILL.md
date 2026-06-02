---
name: add-watershed
description: 'Onboard a new US watershed end-to-end across RiverSignal / RiverPath / DeepTrail. Inventory, ingest, curate, wire, test, and deploy. Public command surface: /add-watershed.'
argument-hint: "<WATERSHED_SLUG> [WATERSHED_DISPLAY] [STATES] [BBOX_HINT]"
disable-model-invocation: true
---

# Add Watershed

Drive a new US watershed through the full data-platform pipeline: source inventory + gap report,
bronze/silver/gold ingestion, frontend wiring, terraform args, tests, and approved prod deploy.

**This file is only a launcher. The single source of truth is the runbook:**
`docs/helix/runbooks/add-watershed-prompt.md` (relative to the RiverSignal repo root — run this
skill from inside that repo). The runbook owns *all* of the actual content — the steps, the
operating-context file list, the McKenzie reference, the hard rules / cross-cutting requirements,
the pause/escalation triggers, the prod-deploy approval gates, and the deliverables checklist.

This launcher **intentionally does not duplicate** any of that, so it can never drift out of sync
(it used to embed mirrored copies of the rules and the deliverables checklist, and they went
stale). **Read the runbook fresh every run; when anything here and the runbook disagree, the
runbook wins.**

## Arguments

The user invoked `/add-watershed $ARGUMENTS`. Parse the arguments in order; only the first (slug)
is required:

| Position | Name | Required | Example |
|---|---|---|---|
| 1 | `WATERSHED_SLUG` | yes | `yellowstone_upper` |
| 2 | `WATERSHED_DISPLAY` | optional (ask if missing) | `Upper Yellowstone River` |
| 3 | `WATERSHED_STATES` | optional (ask if missing) | `MT,WY` |
| 4 | `BBOX_HINT` | optional (agent refines later anyway) | `north=46.05, south=44.50, east=-108.30, west=-110.95` |

If only the slug was given, ask the user for `WATERSHED_DISPLAY`, `WATERSHED_STATES`,
`HEADWATERS_DESCRIPTION`, and `MOUTH_DESCRIPTION` before reading the runbook — these form the
runbook's "Required arguments" block.

## What this skill does

1. **Open and read the runbook end-to-end** — `docs/helix/runbooks/add-watershed-prompt.md`
   (~1000 lines; the structure is stable, don't skip sections).
2. **Read the operating-context files** the runbook's "Operating context" section enumerates.
3. **Read the McKenzie reference example** in the runbook to ground what "fully loaded" means.
4. **Execute STEP 0 → 1 → 2 → 3 exactly as the runbook defines them**, honoring its per-phase
   commit cadence, its pause/escalation policy, and its explicit prod-deploy approval gates. Do not
   work from any step list, rule set, or checklist embedded in this launcher — there isn't one on
   purpose. Follow the runbook.

## When NOT to use this skill (routing)

- Adding a new *reach* to an existing watershed → focused alembic seed + commit; no full runbook.
- Re-running a state adapter against an existing watershed → `python -m pipeline.cli ingest <source> -w <ws>`.
- Authoring a new adapter without onboarding a watershed → cherry-pick the adapter checklist (runbook §2.2).
- Renaming or splitting an existing watershed → no safe runbook exists; stop and ask.
