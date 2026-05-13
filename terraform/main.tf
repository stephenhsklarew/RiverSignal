terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Backend configured at init time:
  #   terraform init -backend-config="bucket=YOUR-STATE-BUCKET" -backend-config="prefix=production"
  backend "gcs" {}
}

provider "google" {
  project = var.project_id
  region  = var.region
  # Bill API calls to this project's quota so user-creds ADC doesn't fall
  # back to a default billing project (which may not have the required
  # APIs enabled — manifests as 403 SERVICE_DISABLED on Service Usage).
  billing_project       = var.project_id
  user_project_override = true
}

provider "google-beta" {
  project               = var.project_id
  region                = var.region
  billing_project       = var.project_id
  user_project_override = true
}

# Enable required GCP APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "compute.googleapis.com",
    "vpcaccess.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "servicenetworking.googleapis.com",
    "essentialcontacts.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}
