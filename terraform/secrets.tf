# Secret Manager — API keys and credentials
# Secrets are created empty; populate via:
#   echo -n "value" | gcloud secrets versions add SECRET_NAME --data-file=-

locals {
  secrets = [
    "anthropic-api-key",
    "openai-api-key",
    "google-client-id",
    "google-client-secret",
    "apple-client-id",
    "apple-team-id",
    "apple-key-id",
    "apple-private-key",
    "auth-secret-key",
    "usgs-api-key",
  ]
}

resource "google_secret_manager_secret" "secrets" {
  for_each  = toset(local.secrets)
  secret_id = each.value

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Store the database password in Secret Manager too
resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Grant Cloud Run service account access to all secrets
resource "google_secret_manager_secret_iam_member" "api_access" {
  for_each  = toset(concat(local.secrets, ["db-password"]))
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"

  depends_on = [
    google_secret_manager_secret.secrets,
    google_secret_manager_secret.db_password,
  ]
}

resource "google_secret_manager_secret_iam_member" "pipeline_access" {
  for_each  = toset(concat(local.secrets, ["db-password"]))
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.pipeline.email}"

  depends_on = [
    google_secret_manager_secret.secrets,
    google_secret_manager_secret.db_password,
  ]
}
