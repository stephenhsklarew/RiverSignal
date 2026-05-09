---
dun:
  id: FEAT-018
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-018 -- Production Infrastructure

**Feature ID**: FEAT-018
**Status**: Implemented (spec retroactive)
**Priority**: P0
**Owner**: Core Engineering
**Date**: 2026-05-08

## Overview

Production infrastructure for deploying the RiverSignal platform to Google Cloud Platform using Terraform infrastructure-as-code, Docker containerization, GitHub Actions CI/CD, and Cloud Scheduler pipeline automation. This enables the platform to run in production with automated deployments, database migrations, and scheduled data pipeline execution.

## Problem Statement

- **Current situation**: Development ran on local PostgreSQL. No production deployment, no CI/CD, no automated pipeline scheduling.
- **Desired outcome**: Fully automated production deployment where pushing to main triggers build, migration, and deploy; data pipelines run on schedule without manual intervention.

## Requirements

### Functional Requirements

#### FR-01: GCP Terraform Infrastructure
- Terraform configuration for all GCP resources: Cloud Run, Cloud SQL, VPC, Secret Manager, Artifact Registry, Cloud Storage, Cloud Scheduler, Cloud Build
- 14 `.tf` files in `terraform/` directory
- Resources: Cloud Run service (2 vCPU, 2GB RAM), Cloud SQL instance (PostgreSQL 17 + PostGIS, db-g1-small, 20GB SSD), VPC with serverless connector for private Cloud SQL access, 3 service accounts with least-privilege IAM
- Acceptance criteria: `terraform plan` succeeds with no errors; `terraform apply` provisions a fully functional production environment

#### FR-02: Database Migration Scripts
- `migrate-to-production.sh` for migrating local development data to Cloud SQL
- `restore-production.sh` for restoring production database from backups
- Acceptance criteria: Migration script successfully transfers schema + data from local PostgreSQL to Cloud SQL; restore script recovers from GCS backup within 30 minutes

#### FR-03: Docker Containerization
- Single Dockerfile serving both API (FastAPI) and pipeline execution
- Image published to Artifact Registry
- Acceptance criteria: Docker image builds in under 5 minutes; container starts and serves API within 30 seconds; health endpoint responds at `/health`

#### FR-04: GitHub Actions CI/CD
- `.github/workflows/deploy.yml` triggered on push to main
- Steps: build Docker image, push to Artifact Registry, run database migrations, deploy to Cloud Run
- Workload Identity Federation for GitHub Actions (no stored credentials)
- Acceptance criteria: Push to main triggers automated deployment; deployment completes within 10 minutes; rollback possible by re-deploying previous image

#### FR-05: Cloud Scheduler Pipeline Automation
- Daily light refresh: update observations, time series, weather data
- Weekly heavy refresh: full pipeline run including all adapters
- Monthly prediction model retraining
- Cloud Run Jobs for batch pipeline execution
- Acceptance criteria: Scheduled jobs execute on time; pipeline completion logged; failure alerts sent via Essential Contacts

#### FR-06: GCS Asset Storage
- Cloud Storage buckets for: user-uploaded photos, audio story files, database backups
- CDN-ready asset serving for images and audio
- Acceptance criteria: Photo uploads stored in GCS and retrievable via public URL; audio files cached and served with appropriate headers

#### FR-07: Optimized Pipeline Refresh
- Light daily refresh (observations, time series, weather) completes in under 30 minutes
- Heavy weekly refresh (all adapters, materialized view rebuild) completes in under 2 hours
- Prediction model refresh runs after data pipeline completion
- Acceptance criteria: Daily pipeline completes within time budget; no data gaps between refresh cycles

## Implementation Evidence

- `terraform/main.tf` — GCP provider, API enablement
- `terraform/cloud_sql.tf` — PostgreSQL 17 + PostGIS instance
- `terraform/cloud_run.tf` — FastAPI service (2 vCPU, 2GB)
- `terraform/cloud_run_jobs.tf` — Pipeline batch jobs
- `terraform/cloud_storage.tf` — Assets + backups buckets
- `terraform/cloud_scheduler.tf` — Cron triggers
- `terraform/secrets.tf` — Secret Manager (11 secrets)
- `terraform/networking.tf` — VPC, serverless connector
- `terraform/iam.tf` — 3 service accounts
- `terraform/artifact_registry.tf` — Docker image repo
- `terraform/cloud_build.tf` — Workload Identity Federation
- `terraform/notifications.tf` — Essential Contacts
- `terraform/variables.tf` — Configurable inputs
- `terraform/outputs.tf` — Deployment outputs
- `.github/workflows/deploy.yml` — CI/CD workflow
- `Dockerfile` — Single image for API + pipeline

## Dependencies

- **External services**: Google Cloud Platform account with billing, GitHub repository with Actions enabled
- **Other features**: FEAT-005 (pipeline adapters executed by Cloud Run Jobs), FEAT-017 (prediction models scheduled via Cloud Scheduler)

## Out of Scope

- Multi-region deployment
- Auto-scaling beyond Cloud Run defaults
- Monitoring dashboards (Cloud Monitoring/Logging used directly)
- PostHog analytics infrastructure (planned but not implemented)
- Staging environment (single production environment for MVP)

## Review Checklist

- [x] Overview connects this feature to a specific PRD requirement
- [x] Every functional requirement is testable
- [x] Non-functional requirements have specific numeric targets
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes things someone might reasonably assume are in scope
