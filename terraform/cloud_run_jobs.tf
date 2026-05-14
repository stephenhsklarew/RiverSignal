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
      timeout     = "3600s"

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
        args    = ["python -m pipeline.cli ingest inaturalist -w all && python -m pipeline.cli ingest snotel -w all && python -m pipeline.cli ingest usgs -w all && python -m pipeline.ingest.nws_observations && python -m pipeline.ingest.nws_observations forecasts"]

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
        args    = ["python -m pipeline.cli ingest fishing -w all && python -m pipeline.cli ingest wqp -w all && python -m pipeline.cli ingest washington -w all && python -m pipeline.cli ingest utah -w green_river"]

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
          "python -m pipeline.cli ingest biodata -w all && python -m pipeline.cli ingest wqp_bugs -w all && python -m pipeline.cli ingest gbif -w all && python -m pipeline.cli ingest recreation -w all && python -m pipeline.cli ingest pbdb -w all && python -m pipeline.cli ingest restoration -w all && python -m pipeline.cli ingest prism -w all && python -m pipeline.cli ingest streamnet -w all && python -m pipeline.cli ingest idigbio -w all"
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
      # 3600s safety margin — silver refresh can spike when sub-views recompute
      # against large recent windows. Set to 1800s originally; bumped after a
      # 2026-04 timeout incident.
      timeout     = "3600s"

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

resource "google_cloud_run_v2_job" "refresh_heavy" {
  name     = "${var.app_name}-refresh-heavy"
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
