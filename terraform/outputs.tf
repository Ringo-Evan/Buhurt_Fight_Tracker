output "app_url" {
  description = "URL of the deployed application"
  value       = "https://${azurerm_linux_web_app.main.default_hostname}"
}

output "app_name" {
  description = "Name of the Azure App Service"
  value       = azurerm_linux_web_app.main.name
}

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}
