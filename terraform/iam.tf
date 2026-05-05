# Service accounts for Cloud Run, pipeline jobs, and scheduler

resource "google_service_account" "api" {
  account_id   = "${var.app_name}-api"
  display_name = "${var.app_name} API (Cloud Run)"
}

resource "google_service_account" "pipeline" {
  account_id   = "${var.app_name}-pipeline"
  display_name = "${var.app_name} Pipeline (Cloud Run Jobs)"
}

resource "google_service_account" "scheduler" {
  account_id   = "${var.app_name}-scheduler"
  display_name = "${var.app_name} Scheduler"
}

# API service account permissions
resource "google_project_iam_member" "api_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_storage" {
  project = var.project_id
  role    = "roles/storage.objectUser"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Pipeline service account permissions
resource "google_project_iam_member" "pipeline_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_project_iam_member" "pipeline_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

# Scheduler can invoke Cloud Run Jobs
resource "google_project_iam_member" "scheduler_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler.email}"
}
