# Essential Contacts — route all GCP notifications to the correct email

resource "google_essential_contacts_contact" "owner" {
  parent                              = "projects/${var.project_id}"
  email                               = var.notification_email
  language_tag                        = "en"
  notification_category_subscriptions = ["ALL"]
}
