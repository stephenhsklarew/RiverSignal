# Remaining RiverPath AI Features

## 6. River Health Alerts — Personalized Notifications
**Description**: Threshold-based alerts — hatch starting, temp dropping, invasive detected, stocking happened. Per-user, per-watershed configuration.

**Why deferred**: Needs notification infrastructure (service worker push or polling mechanism). No user accounts yet for persistence.

**Where in UI**: Saved tab — "My Alerts" section with toggle switches per alert type per watershed. Alert badge on bottom nav.

**Data needed**: gold.anomaly_flags + gold.hatch_fly_recommendations + gold.cold_water_refuges + gold.stocking_schedule

---

## 10. River DNA — Shareable Watershed Fingerprint
**Description**: A unique visual fingerprint for each watershed — like Spotify Wrapped for rivers. Combines species richness, thermal profile, restoration progress, geology into a shareable image card.

**Why deferred**: Needs canvas/SVG image generation (server-side or client-side). Share-worthy design requires iteration.

**Where in UI**: Steward tab — "Share Your River's Story" generates an image card. Share via Web Share API.

**Data needed**: gold.watershed_scorecard + gold.species_trends + gold.cold_water_refuges + silver.geologic_context
