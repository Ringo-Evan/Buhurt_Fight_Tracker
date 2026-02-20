variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "buhurt-fight-tracker-rg"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus2"  # Match Neon database region
}

variable "app_name" {
  description = "Name of the Azure App Service (must be globally unique)"
  type        = string
  default     = "buhurt-fight-tracker"
}

variable "sku_name" {
  description = "App Service SKU (B1 = Basic, ~$13/mo prorated)"
  type        = string
  default     = "B1"
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
