# Cloud Run Jobs — Pipeline ingestion and view refresh

resource "google_cloud_run_v2_job" "migrate" {
  name     = "${var.app_name}-migrate"
  location = var.region

  lifecycle {
    # CI rewrites the image tag on every deploy via
    # `gcloud run jobs update riversignal-migrate --image <sha>`.
    # Without this, terraform would constantly revert it.
    ignore_changes = [
      template[0].template[0].containers[0].image,
      client,
      client_version,
    ]
  }

  template {
    task_count  = 1
    parallelism = 1

    template {
      max_retries = 0
      timeout     = "600s"

      service_account = google_service_account.pipeline.email

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = local.image
        command = ["alembic", "upgrade", "head"]

        resources {
          limits = {
            cpu    = "1"
            memory = "1Gi"
          }
        }

        env {
          name  = "DATABASE_URL"
          value = local.db_url
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [local.db_connection_name]
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_job" "pipeline_daily" {
  name     = "${var.app_name}-pipeline-daily"
  location = var.region

  template {
    task_count  = 1
    parallelism = 1

    template {
      max_retries = 1
      # 14400s (4h) headroom — was 3600s but hit the wall every day from
      # 2026-05-16 onward when Shenandoah onboarded with a ~1M-observation
      # iNaturalist backfill. Drop back to 3600s once the adapter
      # checkpoints last_sync progressively (separate bead).
      timeout = "14400s"

      service_account = google_service_account.pipeline.email

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = local.image
        command = ["/bin/bash", "-c"]
        # NWS observations + 7-day forecast capture appended at the END so an
        # NWS outage doesn't short-circuit inaturalist/snotel/usgs above.
        args = ["python -m pipeline.cli ingest inaturalist -w all && python -m pipeline.cli ingest snotel -w all && python -m pipeline.cli ingest usgs -w all && python -m pipeline.ingest.nws_observations && python -m pipeline.ingest.nws_observations forecasts"]

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }

        env {
          name  = "DATABASE_URL"
          value = local.db_url
        }

        env {
          name  = "GCS_BUCKET_ASSETS"
          value = google_storage_bucket.assets.name
        }

        dynamic "env" {
          for_each = {
            ANTHROPIC_API_KEY = "anthropic-api-key"
            USGS_API_KEY      = "usgs-api-key"
          }
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value
                version = "latest"
              }
            }
          }
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [local.db_connection_name]
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_job" "pipeline_weekly" {
  name     = "${var.app_name}-pipeline-weekly"
  location = var.region

  template {
    task_count  = 1
    parallelism = 1

    template {
      max_retries = 1
      timeout     = "3600s"

      service_account = google_service_account.pipeline.email

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = local.image
        command = ["/bin/bash", "-c"]
        args    = ["python -m pipeline.cli ingest fishing -w all && python -m pipeline.cli ingest wqp -w all && python -m pipeline.cli ingest washington -w all && python -m pipeline.cli ingest utah -w green_river && python -m pipeline.cli ingest virginia -w shenandoah && python -m pipeline.cli ingest west_virginia -w shenandoah && python -m pipeline.cli ingest ohio_stocking -w mad_river_oh && python -m pipeline.cli ingest massachusetts -w ipswich_river_ma"]

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }

        env {
          name  = "DATABASE_URL"
          value = local.db_url
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [local.db_connection_name]
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_job" "pipeline_monthly" {
  name     = "${var.app_name}-pipeline-monthly"
  location = var.region

  template {
    task_count  = 1
    parallelism = 1

    template {
      max_retries = 1
      timeout     = "7200s"

      service_account = google_service_account.pipeline.email

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = local.image
        command = ["/bin/bash", "-c"]
        args = [
          "python -m pipeline.cli ingest biodata -w all && python -m pipeline.cli ingest wqp_bugs -w all && python -m pipeline.cli ingest gbif -w all && python -m pipeline.cli ingest recreation -w all && python -m pipeline.cli ingest pbdb -w all && python -m pipeline.cli ingest restoration -w all && python -m pipeline.cli ingest prism -w all && python -m pipeline.cli ingest streamnet -w all && python -m pipeline.cli ingest idigbio -w all && python -m pipeline.cli ingest mrds -w all && python -m pipeline.cli ingest odgs -w mad_river_oh && python -m pipeline.cli ingest wbd -w all"
        ]

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }

        env {
          name  = "DATABASE_URL"
          value = local.db_url
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [local.db_connection_name]
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_job" "refresh_views" {
  name     = "${var.app_name}-refresh-views"
  location = var.region

  template {
    task_count  = 1
    parallelism = 1

    template {
      max_retries = 1
      # 14400s (4h) safety margin — bumped 2026-05-24 after gold.post_fire_recovery
      # started taking ~37min for ~459 rows (likely a sequential scan; tracked
      # in a separate bead). Was 3600s — set to 1800s originally, bumped after
      # 2026-04 timeout incident, bumped again here for the May 2026 cliff.
      timeout = "14400s"

      service_account = google_service_account.pipeline.email

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = local.image
        command = ["python", "-m", "pipeline.cli", "refresh", "--mode", "light"]

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }

        env {
          name  = "DATABASE_URL"
          value = local.db_url
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [local.db_connection_name]
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_job" "tqs_daily_refresh" {
  name     = "${var.app_name}-tqs-daily-refresh"
  location = var.region

  template {
    task_count  = 1
    parallelism = 1

    template {
      max_retries = 1
      timeout     = "1800s"

      service_account = google_service_account.pipeline.email

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = local.image
        command = ["python", "-m", "pipeline.jobs.tqs_daily_refresh"]

        resources {
          limits = {
            cpu    = "1"
            memory = "1Gi"
          }
        }

        env {
          name  = "DATABASE_URL"
          value = local.db_url
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [local.db_connection_name]
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_job" "sms_dispatcher" {
  name     = "${var.app_name}-sms-dispatcher"
  location = var.region

  template {
    task_count  = 1
    parallelism = 1

    template {
      max_retries = 0
      timeout     = "900s"

      service_account = google_service_account.pipeline.email

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = local.image
        command = ["python", "-m", "pipeline.sms.dispatcher"]

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        env {
          name  = "DATABASE_URL"
          value = local.db_url
        }

        dynamic "env" {
          for_each = {
            TELNYX_API_KEY              = "telnyx-api-key"
            TELNYX_VERIFY_PROFILE_ID    = "telnyx-verify-profile-id"
            TELNYX_MESSAGING_PROFILE_ID = "telnyx-messaging-profile-id"
            TELNYX_FROM_NUMBER          = "telnyx-from-number"
            TELNYX_PUBLIC_KEY           = "telnyx-public-key"
            SMS_ENCRYPTION_KEY          = "sms-encryption-key"
          }
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value
                version = "latest"
              }
            }
          }
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [local.db_connection_name]
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_job" "refresh_heavy" {
  name     = "${var.app_name}-refresh-heavy"
  location = var.region

  template {
    task_count  = 1
    parallelism = 1

    template {
      max_retries = 1
      timeout     = "7200s"

      service_account = google_service_account.pipeline.email

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = local.image
        command = ["python", "-m", "pipeline.cli", "refresh", "--mode", "heavy"]

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }

        env {
          name  = "DATABASE_URL"
          value = local.db_url
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [local.db_connection_name]
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

# fossil-images: backfill specimen photos via iDigBio media, MorphoSource,
# Smithsonian, Wikimedia Commons, and PhyloPic. The job iterates every row
# with image_url IS NULL across all watersheds; new watersheds get covered
# automatically. Was previously a manual `python -m pipeline.cli fossil-images`
# step that fell off the runbook after Green River and left Shenandoah's
# 2,926 fossil rows photo-less.
#
# Scheduled monthly because the bulk of the work converges on the first run
# after a new watershed lands; subsequent runs only touch new arrivals.
resource "google_cloud_run_v2_job" "fossil_images" {
  name     = "${var.app_name}-fossil-images"
  location = var.region

  template {
    task_count  = 1
    parallelism = 1

    template {
      max_retries = 1
      # 7200s (2h) — backfill is rate-limited to be polite to upstream
      # (Wikimedia, PhyloPic, MorphoSource, iDigBio). Empirically ~15-30
      # min per net-new watershed; idempotent re-runs are fast.
      timeout = "7200s"

      service_account = google_service_account.pipeline.email

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = local.image
        command = ["python", "-m", "pipeline.cli", "fossil-images"]

        resources {
          limits = {
            cpu    = "1"
            memory = "1Gi"
          }
        }

        env {
          name  = "DATABASE_URL"
          value = local.db_url
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [local.db_connection_name]
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}
