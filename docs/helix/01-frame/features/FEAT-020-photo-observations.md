---
dun:
  id: FEAT-020
  depends_on:
    - helix.prd
    - FEAT-019
---
# Feature Specification: FEAT-020 -- Photo Observations

**Feature ID**: FEAT-020
**Status**: Implemented (spec retroactive)
**Priority**: P0
**Owner**: Core Engineering
**Date**: 2026-05-08

## Overview

User-generated photo observation system allowing authenticated users to submit geotagged photos with species identification, contributing to the platform's observation dataset. Includes camera interface, EXIF metadata extraction, species typeahead search, GCS storage in production, and security hardening (rate limiting, image validation, input sanitization).

## Problem Statement

- **Current situation**: All observation data came from external sources (iNaturalist, USGS, etc.). Users had no way to contribute their own observations.
- **Desired outcome**: Users can submit geotagged photos from the field, enriching the observation dataset with real-time user-generated content.

## Requirements

### Functional Requirements

#### FR-01: Camera FAB with Source Picker
- Floating action button (FAB) on RiverPath map pages triggers photo submission
- Source picker: "Take Photo" (camera) or "Choose from Library" (gallery)
- `PhotoObservation.tsx` component handles the full submission flow
- Acceptance criteria: FAB is visible on map pages; tapping opens source picker; both camera and gallery options work on mobile

#### FR-02: EXIF GPS and DateTime Extraction
- Automatically extract GPS coordinates and capture datetime from photo EXIF metadata
- If EXIF GPS is unavailable, fall back to device GPS or manual entry
- Acceptance criteria: GPS coordinates are extracted from photos taken with location-enabled cameras; datetime is parsed from EXIF and used as observation timestamp

#### FR-03: Species Typeahead Search
- `/species/typeahead` endpoint for searching species by common or scientific name
- Autocomplete suggestions as user types
- Minimum 3 characters before search triggers
- Acceptance criteria: Typing "steel" returns "Steelhead (Oncorhynchus mykiss)" and related species within 200ms

#### FR-04: Category Selection Chips
- Predefined category chips for quick classification (Fish, Insect, Bird, Plant, Mammal, Other)
- Category selection narrows typeahead results
- Acceptance criteria: Selecting a category chip filters typeahead to that taxonomic group

#### FR-05: GCS Photo Storage in Production
- Photos uploaded as base64, validated, and stored in Google Cloud Storage
- Thumbnail generation for gallery views
- Local filesystem storage in development mode
- Acceptance criteria: Photos are retrievable via GCS URL after submission; thumbnails are generated at 200px width

#### FR-06: Security
- **Rate limiting**: 10 submissions per 5 minutes per IP address
- **Image validation**: Magic byte checking (JPEG/PNG only); reject non-image files regardless of extension
- **Input sanitization**: HTML tag stripping, null byte removal, field length limits
- **File size limit**: Maximum upload size enforced
- Acceptance criteria: 11th submission within 5 minutes returns 429; uploading a renamed .txt file as .jpg is rejected; HTML in notes field is stripped

#### FR-07: Bronze Observations Table Integration
- Submitted observations stored in the `observations` table with source = 'user'
- Observations include: lat, lon, datetime, species, category, photo URL, user ID, notes
- Acceptance criteria: User observations appear in the observations table and are queryable via existing gold views

#### FR-08: My Observations Toggle on RiverSignal Map
- `/observations/mine` endpoint returns current user's submitted observations
- Toggle on map to show/hide user's own observations as pins
- Acceptance criteria: Authenticated users see their own observations as distinct pins on the map; toggle hides/shows them

## Implementation Evidence

- `app/routers/user_observations.py` — submission endpoint with rate limiting, image validation, EXIF parsing, GCS upload, species typeahead
- `frontend/src/components/PhotoObservation.tsx` — camera FAB and submission flow

## Dependencies

- **Other features**: FEAT-019 (authentication for observation ownership), FEAT-018 (GCS storage in production)
- **Data**: Species table for typeahead search (18,500+ species)

## Out of Scope

- Observation moderation workflow (all submissions currently accepted)
- Community observation feed (viewing others' observations)
- iNaturalist write-back (submitting to iNaturalist API)
- Photo annotation or markup tools
- Video observations
- Batch upload

## Review Checklist

- [x] Overview connects this feature to a specific PRD requirement
- [x] Every functional requirement is testable
- [x] Non-functional requirements have specific numeric targets
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes things someone might reasonably assume are in scope
