# Outputs — URLs, connection strings, and next steps

output "cloud_run_url" {
  description = "Cloud Run API URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection name (for Cloud SQL Proxy)"
  value       = google_sql_database_instance.db.connection_name
}

output "cloud_sql_private_ip" {
  description = "Cloud SQL private IP address"
  value       = google_sql_database_instance.db.private_ip_address
}

output "assets_bucket" {
  description = "Cloud Storage assets bucket name"
  value       = google_storage_bucket.assets.name
}

output "assets_bucket_url" {
  description = "Public URL for assets bucket"
  value       = "https://storage.googleapis.com/${google_storage_bucket.assets.name}"
}

output "backups_bucket" {
  description = "Cloud Storage backups bucket name"
  value       = google_storage_bucket.backups.name
}

output "artifact_registry" {
  description = "Docker image push target"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.app_name}/api"
}

output "database_url" {
  description = "DATABASE_URL for Cloud SQL (via Unix socket)"
  value       = local.db_url
  sensitive   = true
}

output "next_steps" {
  description = "Manual steps after terraform apply"
  value       = <<-EOT

    ═══════════════════════════════════════════════
    RiverSignal Production — Next Steps
    ═══════════════════════════════════════════════

    1. Populate secrets:
       echo -n "sk-ant-..." | gcloud secrets versions add anthropic-api-key --data-file=-
       echo -n "sk-..."     | gcloud secrets versions add openai-api-key --data-file=-
       echo -n "..."        | gcloud secrets versions add google-client-id --data-file=-
       echo -n "..."        | gcloud secrets versions add google-client-secret --data-file=-
       echo -n "..."        | gcloud secrets versions add auth-secret-key --data-file=-
       echo -n "..."        | gcloud secrets versions add usgs-api-key --data-file=-
       # Repeat for apple-* secrets if using Apple OAuth

    2. Build and push Docker image:
       docker build -t ${var.region}-docker.pkg.dev/${var.project_id}/riversignal/api:latest .
       docker push ${var.region}-docker.pkg.dev/${var.project_id}/riversignal/api:latest

    3. Migrate data:
       ./scripts/migrate-to-production.sh ${google_storage_bucket.assets.name} ${google_storage_bucket.backups.name}

    4. Restore database (from Cloud Shell or with Cloud SQL Proxy):
       export DATABASE_URL="<from terraform output -raw database_url>"
       ./scripts/restore-production.sh ${google_storage_bucket.backups.name}

    5. Deploy frontend:
       cd frontend
       VITE_API_BASE=${google_cloud_run_v2_service.api.uri}/api/v1 npm run build
       firebase deploy --only hosting

    6. Verify:
       curl ${google_cloud_run_v2_service.api.uri}/health
  EOT
}
