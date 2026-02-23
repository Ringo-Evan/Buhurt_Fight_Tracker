variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "buhurt-fight-tracker-rg"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "canadaeast"  # Match Neon database region
}

variable "app_name" {
  description = "Name of the Azure App Service (must be globally unique)"
  type        = string
  default     = "buhurt-fight-tracker"
}

variable "sku_name" {
  description = "App Service SKU (F1 = Free, B1 = Basic ~$13/mo)"
  type        = string
  default     = "F1"  # Free tier - no cost, may avoid quota issues
}

variable "python_version" {
  description = "Python runtime version"
  type        = string
  default     = "3.12"  # Azure App Service supports: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
}

variable "database_url" {
  description = "PostgreSQL connection string (from Neon)"
  type        = string
  sensitive   = true
}
