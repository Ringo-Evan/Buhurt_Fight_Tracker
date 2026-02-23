#!/bin/bash
# Stop Azure App Service (use when you don't need the API running)
# Stopped apps cost $0/month on consumption billing
#
# Usage: ./scripts/az_stop.sh
# Prerequisites: Azure CLI installed and logged in (`az login`)

RESOURCE_GROUP="buhurt-rg"
APP_NAME="buhurt-fight-tracker"

echo "Stopping $APP_NAME..."
az webapp stop --name "$APP_NAME" --resource-group "$RESOURCE_GROUP"
echo "Done. App stopped. No compute charges while stopped."
