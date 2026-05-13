# Cloud Scheduler — Cron triggers for pipeline jobs

resource "google_cloud_scheduler_job" "daily_pipeline" {
  name        = "${var.app_name}-daily-pipeline"
  region      = var.region
  schedule    = "0 2 * * *"
  time_zone   = var.scheduler_timezone
  description = "Daily: iNaturalist, SNOTEL, USGS"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.pipeline_daily.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "weekly_pipeline" {
  name        = "${var.app_name}-weekly-pipeline"
  region      = var.region
  schedule    = "0 4 * * 1"
  time_zone   = var.scheduler_timezone
  description = "Weekly (Monday): fishing, WQP, Washington"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.pipeline_weekly.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "monthly_pipeline" {
  name        = "${var.app_name}-monthly-pipeline"
  region      = var.region
  schedule    = "0 5 1 * *"
  time_zone   = var.scheduler_timezone
  description = "Monthly (1st): biodata, WQP bugs, GBIF, recreation, PBDB, restoration, PRISM, StreamNet, iDigBio"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.pipeline_monthly.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "refresh_views" {
  name        = "${var.app_name}-refresh-views"
  region      = var.region
  schedule    = "0 10 * * *"
  time_zone   = var.scheduler_timezone
  description = "Daily: refresh silver + light gold views (fast)"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.refresh_views.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "tqs_daily_refresh" {
  name        = "${var.app_name}-tqs-daily-refresh"
  region      = var.region
  schedule    = "30 10 * * *"
  time_zone   = var.scheduler_timezone
  description = "Daily: refresh gold.trip_quality_daily + append history snapshot"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.tqs_daily_refresh.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "refresh_heavy" {
  name        = "${var.app_name}-refresh-heavy"
  region      = var.region
  schedule    = "0 3 * * 0"
  time_zone   = var.scheduler_timezone
  description = "Weekly (Sunday 3am): refresh heavy gold views"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.refresh_heavy.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [google_project_service.apis]
}
