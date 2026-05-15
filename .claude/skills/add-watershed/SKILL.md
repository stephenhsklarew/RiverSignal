---
name: add-watershed
description: 'Onboard a new US watershed end-to-end across RiverSignal / RiverPath / DeepTrail. Inventory, ingest, curate, wire, test, and deploy. Public command surface: /add-watershed.'
argument-hint: "<WATERSHED_SLUG> [WATERSHED_DISPLAY] [STATES] [BBOX_HINT]"
disable-model-invocation: true
---

# Add Watershed

Drive a new US watershed through the full data-platform pipeline: source inventory + gap report,
bronze/silver/gold ingestion, frontend wiring, terraform args, tests, and approved prod deploy.

The canonical execution plan is the runbook at
[`docs/helix/runbooks/add-watershed-prompt.md`](../../../docs/helix/runbooks/add-watershed-prompt.md).
This skill is the launcher. The runbook is the source of truth — when this skill and the runbook
disagree, the runbook wins.

## Arguments

The user invoked `/add-watershed $ARGUMENTS`. Parse the arguments in order. Only the first
(slug) is required; ask for any others before proceeding:

| Position | Name | Required | Example |
|---|---|---|---|
| 1 | `WATERSHED_SLUG` | yes | `yellowstone_upper` |
| 2 | `WATERSHED_DISPLAY` | optional (ask if missing) | `Upper Yellowstone River` |
| 3 | `WATERSHED_STATES` | optional (ask if missing) | `MT,WY` |
| 4 | `BBOX_HINT` | optional (agent refines later anyway) | `north=46.05, south=44.50, east=-108.30, west=-110.95` |

If only the slug was given, ask the user for `WATERSHED_DISPLAY`, `WATERSHED_STATES`,
`HEADWATERS_DESCRIPTION`, and `MOUTH_DESCRIPTION` before reading the runbook. These five values
form the runbook's "Required arguments" block.

## What this skill does

1. **Read the runbook.** Open
   `docs/helix/runbooks/add-watershed-prompt.md` and read it end-to-end. The runbook is
   ~900 lines but the structure is stable — don't skip sections.
2. **Read the operating-context files** the runbook's §"Operating context" section lists
   (watershed config, ingest base class, CLI, freshness wiring, frontend dicts, terraform,
   prior TQS plan, recent watershed-onboarding commits). 5 minutes; don't shortcut.
3. **Read the McKenzie reference example** (§"Reference example: McKenzie watershed") to
   ground what "fully loaded" looks like for the new watershed.
4. **Execute Step 0** — pre-flight clarification. Ask the user every question in the runbook's
   STEP 0 table, echo the answers back, and get explicit acknowledgement before any
   inventory / code / ingest work. Six questions: HUC level, paid-API tolerance, B2B license
   filter, confluence-into-existing-watershed permission, curation pace, ship date.
5. **Execute Step 1** — write `docs/helix/06-iterate/watershed-add/<SLUG>-source-inventory-<DATE>.md`.
6. **Execute Step 2** — implementation, with the runbook's per-phase commit cadence.
7. **Execute Step 3** — verification report at
   `docs/helix/06-iterate/watershed-add/<SLUG>-verification-<DATE>.md`.

## Hard rules (mirror of the runbook's "Cross-cutting requirements")

- **Never destroy data.** Backup before any infra change.
- **Migrations are append-only.**
- **License + commercial-use declared per ADR-008** for every new adapter.
- **No silent failure** — every ingest failure logs to `ingestion_jobs`.
- **Production gates require explicit user approval** — four explicit asks in §2.8 of the
  runbook (push / job-execute / freshness-POST / any other prod write). Do not bundle them.
- **Curation flags must be greppable** — anything marked `needs_review=true` lands in a known
  notes/source field.

## Stop and ask the user when

- A required-for-v1 source needs a paid API key the agent cannot obtain.
- Terraform plan shows any change to `google_sql_database_instance.db` settings, network, or
  IAM bindings.
- A bbox refinement would force resizing of an *existing* watershed's bbox (overlap).
- Migrations conflict with the current head revision.
- Any of the four explicit prod-deployment gates in runbook §2.8 is reached.

Everything else is flag-and-continue per the runbook's "Pause policy".

## Output deliverables checklist

By the end of a successful run:

- [ ] `docs/helix/06-iterate/watershed-add/<SLUG>-source-inventory-<DATE>.md`
- [ ] Watershed entry in `pipeline/config/watersheds.py`
- [ ] Existing adapters run; rows landed in bronze
- [ ] New state adapters (if any) merged with tests + ADR-008 license docstrings
- [ ] Alembic seed migrations: river_reaches, flow_quality_bands, hatch_chart placeholders,
      fly_shops_guides, mineral_shops, rockhounding_sites
- [ ] `gold.trip_quality_daily` populated for the new watershed
- [ ] Frontend dicts updated (all `WATERSHED_LABELS`/`WATERSHED_ORDER`/`WS_COORDS`/`WS_GAUGES`
      occurrences — runbook §2.6 has the file table)
- [ ] Terraform args updated for any new adapter scheduling
- [ ] Commits pushed (with user approval); CI deploy succeeded
- [ ] Manual one-shot ingest runs on prod completed (with user approval)
- [ ] `/data-status/refresh` POST'd on prod (with user approval)
- [ ] `docs/helix/06-iterate/watershed-add/<SLUG>-verification-<DATE>.md` with the
      feature-coverage grid mirroring the McKenzie reference

Any unchecked box at the end requires the agent to explain why and what's needed to close it.

## When NOT to use this skill

- Adding a new *reach* to an existing watershed (use a focused alembic seed + commit; no full
  runbook).
- Re-running a state adapter against an existing watershed (just
  `python -m pipeline.cli ingest <source> -w <ws>`).
- Authoring a new adapter without onboarding a watershed (the adapter checklist in §2.2 of the
  runbook stands alone; cherry-pick that section).
- Renaming or splitting an existing watershed (no current runbook covers this safely —
  stop and ask).
