# Cloud Run service — FastAPI backend

locals {
  db_connection_name = google_sql_database_instance.db.connection_name
  db_url             = "postgresql+psycopg://${var.db_user}:${random_password.db_password.result}@/${var.db_name}?host=/cloudsql/${local.db_connection_name}"
  image              = "${var.region}-docker.pkg.dev/${var.project_id}/${var.app_name}/api:${var.docker_image_tag}"
}

resource "google_cloud_run_v2_service" "api" {
  name     = "${var.app_name}-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = var.cloud_run_min_instances
      max_instance_count = var.cloud_run_max_instances
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    service_account = google_service_account.api.email

    containers {
      image = local.image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
        cpu_idle = var.cloud_run_min_instances == 0
      }

      # Direct environment variables
      env {
        name  = "DATABASE_URL"
        value = local.db_url
      }

      env {
        name  = "GCS_BUCKET_ASSETS"
        value = google_storage_bucket.assets.name
      }

      env {
        name  = "STORAGE_BACKEND"
        value = "gcs"
      }

      env {
        name  = "CORS_ORIGIN"
        value = "*"
      }

      env {
        name  = "AUTH_FRONTEND_URL"
        value = var.public_base_url
      }

      env {
        name  = "GOOGLE_REDIRECT_URI"
        value = "${var.public_base_url}/api/v1/auth/google/callback"
      }

      env {
        name  = "APPLE_REDIRECT_URI"
        value = "${var.public_base_url}/api/v1/auth/apple/callback-async"
      }

      # Secrets from Secret Manager
      dynamic "env" {
        for_each = {
          ANTHROPIC_API_KEY    = "anthropic-api-key"
          OPENAI_API_KEY       = "openai-api-key"
          GOOGLE_CLIENT_ID     = "google-client-id"
          GOOGLE_CLIENT_SECRET = "google-client-secret"
          APPLE_CLIENT_ID      = "apple-client-id"
          APPLE_TEAM_ID        = "apple-team-id"
          APPLE_KEY_ID         = "apple-key-id"
          APPLE_PRIVATE_KEY    = "apple-private-key"
          AUTH_SECRET_KEY      = "auth-secret-key"
          USGS_API_KEY         = "usgs-api-key"
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

      # Cloud SQL connection via Unix socket
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 10
        period_seconds        = 15
        # Cold-start budget = 10 + (failure_threshold * period_seconds).
        # Bumped from 5 -> 20 (~85s -> ~310s) on 2026-05-15 after Cloud Run
        # killed three consecutive newly-scaled instances during
        # /path/now/shenandoah traffic — the FastAPI import chain
        # (geopandas, sqlalchemy, GDAL, vite SPA mount) was exceeding the
        # 85s budget on cold starts. Tracked in
        # bead RiverSignal-7ea2ac57 (Cloud Run /health probe budget vs
        # FastAPI cold-start time — the real fix is making cold-start
        # finish faster; this is the short-term band-aid).
        failure_threshold     = 20
        timeout_seconds       = 10
      }

      liveness_probe {
        http_get {
          path = "/health"
        }
        period_seconds    = 30
        # Default timeout_seconds is 1s on Cloud Run; under DB-connection
        # contention or MV-refresh load that's too tight and the API
        # gets reaped mid-flight. Give /health 5s of slack.
        timeout_seconds   = 5
        failure_threshold = 6
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [local.db_connection_name]
      }
    }
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret.secrets,
    google_secret_manager_secret_iam_member.api_access,
  ]

  # CI deploys (.github/workflows/deploy.yml) push specific SHAs and call
  # `gcloud run services update --image <sha>`. Without this, every
  # `terraform apply` would revert the image to `:latest`/the template value
  # and undo the most-recent deploy. Same logic applies to the migrate /
  # daily jobs (handled inline in the gcloud commands), but the API service
  # is the one terraform contests on every run.
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }
}

# Allow unauthenticated access (public API)
resource "google_cloud_run_v2_service_iam_member" "public" {
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
