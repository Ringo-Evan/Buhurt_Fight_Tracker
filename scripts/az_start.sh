#!/bin/bash
# Start Azure App Service (use when you need the API running)
# Cost: ~$0.018/hour on B1 tier
#
# Usage: ./scripts/az_start.sh
# Prerequisites: Azure CLI installed and logged in (`az login`)

RESOURCE_GROUP="buhurt-rg"
APP_NAME="buhurt-fight-tracker"

echo "Starting $APP_NAME..."
az webapp start --name "$APP_NAME" --resource-group "$RESOURCE_GROUP"
echo "Done. API available shortly at: https://$APP_NAME.azurewebsites.net"
