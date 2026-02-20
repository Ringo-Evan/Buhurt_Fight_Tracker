# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Project     = "Buhurt Fight Tracker"
    Environment = "Production"
    ManagedBy   = "Terraform"
  }
}

# App Service Plan (Linux)
resource "azurerm_service_plan" "main" {
  name                = "${var.app_name}-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = var.sku_name

  tags = {
    Project     = "Buhurt Fight Tracker"
    Environment = "Production"
  }
}

# Linux Web App (App Service)
resource "azurerm_linux_web_app" "main" {
  name                = var.app_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    always_on = false  # Save costs (B1 can auto-sleep)

    application_stack {
      python_version = var.python_version
    }

    # Health check endpoint
    health_check_path = "/health"

    # Startup command
    app_command_line = "bash startup.sh"
  }

  app_settings = {
    "DATABASE_URL"                   = var.database_url
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
  }

  logs {
    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 35
      }
    }
  }

  tags = {
    Project     = "Buhurt Fight Tracker"
    Environment = "Production"
  }
}
