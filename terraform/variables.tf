variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-west1"
}

variable "environment" {
  description = "Environment name (production, staging)"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name prefix for all resources"
  type        = string
  default     = "riversignal"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "riversignal"
}

variable "db_user" {
  description = "PostgreSQL application user"
  type        = string
  default     = "riversignal_app"
}

variable "scheduler_timezone" {
  description = "Timezone for Cloud Scheduler cron jobs"
  type        = string
  default     = "America/Los_Angeles"
}

variable "docker_image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

# ── Cloud SQL ──

variable "db_tier" {
  description = "Cloud SQL machine tier (db-f1-micro for budget, db-g1-small for production, db-custom-2-4096 for scale)"
  type        = string
  default     = "db-g1-small"
}

variable "db_disk_size_gb" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 20
}

variable "db_ha_enabled" {
  description = "Enable Cloud SQL high availability (regional failover)"
  type        = bool
  default     = false
}

variable "db_backup_retention_days" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 14
}

# ── Cloud Run ──

variable "cloud_run_cpu" {
  description = "Cloud Run CPU allocation"
  type        = string
  default     = "2"
}

variable "cloud_run_memory" {
  description = "Cloud Run memory allocation"
  type        = string
  default     = "2Gi"
}

variable "cloud_run_min_instances" {
  description = "Minimum Cloud Run instances (0 = scale to zero)"
  type        = number
  default     = 1
}

variable "cloud_run_max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 10
}

# ── Networking ──

variable "vpc_connector_machine_type" {
  description = "VPC connector machine type"
  type        = string
  default     = "e2-micro"
}

# ── Optional features ──

variable "enable_load_balancer" {
  description = "Enable Cloud Load Balancer with managed SSL"
  type        = bool
  default     = false
}

variable "enable_cloud_armor" {
  description = "Enable Cloud Armor WAF (requires load balancer)"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Custom domain name (leave empty for Cloud Run URL)"
  type        = string
  default     = ""
}
