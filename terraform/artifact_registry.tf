# Artifact Registry for Docker images

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.app_name
  format        = "DOCKER"
  description   = "${var.app_name} API and pipeline Docker images"

  depends_on = [google_project_service.apis]
}
