# Cloud SQL PostgreSQL 17 with PostGIS

resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "google_sql_database_instance" "db" {
  name             = "${var.app_name}-db"
  database_version = "POSTGRES_17"
  region           = var.region

  settings {
    tier              = var.db_tier
    disk_size         = var.db_disk_size_gb
    disk_autoresize   = true
    disk_type         = "PD_SSD"
    availability_type = var.db_ha_enabled ? "REGIONAL" : "ZONAL"

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.vpc.id
      enable_private_path_for_google_cloud_services = true
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "04:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = var.db_backup_retention_days

      backup_retention_settings {
        retained_backups = var.db_backup_retention_days
      }
    }

    maintenance_window {
      day  = 7 # Sunday
      hour = 4 # 4 AM
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  deletion_protection = true

  depends_on = [google_service_networking_connection.private_vpc]
}

resource "google_sql_database" "app" {
  name     = var.db_name
  instance = google_sql_database_instance.db.name
}

resource "google_sql_user" "app" {
  name     = var.db_user
  instance = google_sql_database_instance.db.name
  password = random_password.db_password.result
}
