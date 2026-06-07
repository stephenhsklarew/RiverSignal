# Design note: Riverkeeper per-watershed access control

| | |
|---|---|
| **Date** | 2026-06-07 |
| **Status** | **Proposed** — design of record for FEAT-025; not yet built. |
| **Origin** | `00-discover/riverkeeper-role.md` (role one-pager) + alignment-review observation that `/admin` is gated by a single global `is_admin` flag. |
| **Related** | FEAT-025, FEAT-019 (auth), FEAT-023/024 (admin content), ADR-006. Recommends promoting the core decision to **ADR-010** on acceptance. |

## Problem

`/admin/*` is gated by `app/lib/admin_auth.py::get_current_admin`, which checks a single
boolean `users.is_admin` — all-or-nothing. To let a trusted local steward edit *only their*
watershed's content (FEAT-023/024) we need **resource-scoped authorization**: edit rights
bound to specific watersheds, granted/revoked by an admin, effective immediately.

## Decision (proposed → ADR-010)

Introduce a **scoped content-editor role** backed by a `riverkeeper_assignments` table
(many-to-many user↔watershed). Authorization for a watershed-scoped admin write succeeds
when the caller is `is_admin` **OR** holds an active assignment for that watershed.
Authorization is resolved **live per request** (mirroring how `is_admin` is checked today,
so revocation is immediate and nothing is baked into the JWT). This is a single purpose-built
role — **not** a general RBAC system (YAGNI); the table is the extension point if more
capabilities arrive.

## Data model

```sql
-- migration rk01_riverkeeper_assignments (down_revision = current head)
CREATE TABLE IF NOT EXISTS riverkeeper_assignments (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id            uuid NOT NULL,
  watershed          varchar(64) NOT NULL,
  granted_by_user_id uuid NOT NULL,
  granted_at         timestamptz NOT NULL DEFAULT now(),
  revoked_at         timestamptz NULL          -- NULL = active
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_rk_active
  ON riverkeeper_assignments (user_id, watershed) WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_rk_user ON riverkeeper_assignments (user_id);
```

Additive, non-destructive. Revoke = set `revoked_at` (keeps history); the partial unique
index allows re-granting after revocation.

## Authorization layer (`app/lib/admin_auth.py`)

Two helpers, composed so route-gating stays declarative and the per-watershed check is explicit:

- `get_current_content_editor(request) -> dict` — authenticated **and** (`is_admin` OR has
  ≥1 active assignment). Gates watershed-scoped write routes at the dependency level (401 if
  anonymous, 403 if signed-in but neither admin nor keeper).
- `assert_can_edit_watershed(user, watershed)` — called inside each handler with the
  resolved watershed: allow if `user.is_admin`; else require an active assignment for
  `(user.id, watershed)`; **always 403 for `watershed='*'`** unless `is_admin`. Raises 403 otherwise.

`get_current_admin` is unchanged and stays on global/cross-watershed routes.

Why a two-step (route gate + in-handler check) rather than one dependency: the watershed
arrives in different places per endpoint (path vs query) — see the table — so the precise
authorization must run where the watershed is known. The route-level `content_editor` gate
keeps anonymous/non-editor callers out cheaply first.

## Endpoint changes (`app/routers/admin.py`)

| Endpoint | Watershed from | Authorization after change |
|---|---|---|
| `PUT/DELETE /admin/watershed-splash/{ws}`, `POST .../{ws}/image` | path | content_editor + `assert_can_edit_watershed(ws)` |
| `PUT /admin/river-stories/{ws}/{level}`, `POST .../regenerate-audio` | path | content_editor + assert |
| `PUT/DELETE /admin/curated-photos/{species_key}?watershed=<ws>` | query | content_editor + assert (reject `'*'` unless admin) |
| `PUT/DELETE /admin/curated-insect-photos/{species_key}?watershed=<ws>` | query | content_editor + assert |
| `GET /admin/watershed-splash/{ws}`, `GET .../river-stories/{ws}/{level}`, fish/insect lists | path | content_editor + assert (read of *that* watershed) |
| `GET /admin/watershed-splash`, `/admin/curated-photos`, `/admin/river-stories`, `/admin/inat/photos` (lists/search/global) | — | **`get_current_admin` (unchanged)** |
| curating `watershed='*'` (global defaults) | query | **admin-only** |
| `POST/GET/DELETE /admin/riverkeepers` (grant/list/revoke) | body/path | **admin-only** (new, below) |

## Grant / revoke API (new, admin-only)

- `GET /admin/riverkeepers` → list active assignments (+ user email, watershed).
- `POST /admin/riverkeepers` `{email | user_id, watershed}` → upsert active assignment;
  audit-logged with `granted_by_user_id`.
- `DELETE /admin/riverkeepers/{id}` → set `revoked_at = now()`.

Riverkeepers cannot call these (admin-only). A Riverkeeper assigning Riverkeepers is out of scope.

## `/auth/me` + frontend

- `app/routers/auth.py::get_me` adds `riverkeeper_watersheds: string[]` (active assignments
  for the caller) alongside the existing live `is_admin`.
- `frontend/src/components/AuthContext.tsx` exposes `riverkeeperWatersheds` + `isContentEditor
  = is_admin || riverkeeperWatersheds.length > 0`.
- `frontend/src/components/AdminRoute.tsx` admits `isContentEditor` (not just `is_admin`).
- `frontend/src/pages/AdminPhotosPage.tsx`: the watershed picker shows all watersheds for a
  global admin, else only `riverkeeperWatersheds`; the global-defaults card is admin-only.

## Security considerations

- **Least privilege**: a Riverkeeper can act only on assigned watersheds; everything else 403.
- **Immediate revocation**: live per-request lookup (consistent with `is_admin`); no JWT change.
- **ADR-001 (anonymous-first)**: unaffected — these are authenticated *writes*, already gated.
- **ADR-006 (federated-auth-only)**: Riverkeepers authenticate via existing OAuth; no new credential path.
- **ADR-004/007**: Riverkeepers edit the *human* narrative + curated photos; visibility
  filtering and AI grounding are unchanged.
- **Audit**: existing `audit.*` tables already record `changed_by_user_id`; grant/revoke gets its own log.
- **Server-authoritative**: frontend gating is convenience only; every write re-checks on the server.

## Alternatives considered

| Option | Verdict |
|---|---|
| `users.riverkeeper_watersheds` JSONB column | Rejected: no grant history/audit; clunky many-to-many |
| Full RBAC (roles + permissions + grants) | Rejected (YAGNI): one scoped role doesn't justify the machinery |
| Reuse `is_admin` but filter watersheds only in the UI | Rejected: not server-authoritative; trivially bypassable |
| **`riverkeeper_assignments` table + live per-watershed check** | **Selected**: least privilege, audited, immediate revoke, minimal + extensible |

## Verification plan

- pytest: a keeper of WS-A → 200 editing WS-A, 403 editing WS-B and `'*'`; a global admin →
  200 on both; anonymous → 401; grant/revoke admin-only; `/auth/me` returns the assignment set.
- Playwright (forged sessions, as in `tests/admin-splash.spec.ts`): keeper sees only assigned
  watershed(s) in `/admin/photos`; non-assigned watershed not editable.
- Migration applies on a clean DB; partial unique index allows re-grant after revoke.

## Rollout

1. Migration + authorization layer + grant/revoke API (backend, behind admin).
2. `/auth/me` + frontend gating.
3. Seed early-adopter assignments via the grant API.
4. (Later) promote this decision to ADR-010 and add a `riverkeeper` concern if the role grows.
