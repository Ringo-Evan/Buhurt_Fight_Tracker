# Terraform Infrastructure Configuration

This directory contains Infrastructure as Code (IaC) for deploying the Buhurt Fight Tracker API to Azure.

## Prerequisites

1. **Azure CLI**: Installed and authenticated
   ```bash
   az login
   az account show
   ```

2. **Terraform**: Version 1.7 or higher
   ```bash
   terraform version
   ```

3. **Neon Database**: Connection string from Neon dashboard

## Quick Start

### 1. Configure Variables

```bash
# Copy example file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars - add your Neon DATABASE_URL
# database_url = "postgresql+asyncpg://user:password@ep-xxx.us-east-2.aws.neon.tech/buhurt_db?sslmode=require"
```

### 2. Initialize Terraform

```bash
terraform init
```

This downloads the Azure provider and sets up the working directory.

### 3. Preview Changes

```bash
terraform plan
```

Review the resources that will be created:
- Resource Group: `buhurt-fight-tracker-rg`
- App Service Plan: `buhurt-fight-tracker-plan` (Linux B1)
- Web App: `buhurt-fight-tracker` (Python 3.13)

### 4. Create Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. Wait 1-3 minutes for completion.

Outputs:
- `app_url`: https://buhurt-fight-tracker.azurewebsites.net
- `app_name`: buhurt-fight-tracker
- `resource_group_name`: buhurt-fight-tracker-rg

### 5. Verify Deployment

```bash
# Test health endpoint
curl https://buhurt-fight-tracker.azurewebsites.net/health

# Test API
curl https://buhurt-fight-tracker.azurewebsites.net/api/v1/countries
```

## File Structure

```
terraform/
├── provider.tf              # Terraform and provider configuration
├── variables.tf             # Input variable definitions
├── main.tf                  # Main infrastructure resources
├── outputs.tf               # Output values
├── terraform.tfvars.example # Example variable values
├── terraform.tfvars         # Actual values (gitignored)
├── .gitignore               # Ignore state files and secrets
└── README.md                # This file
```

## Resources Created

| Resource | Name | Type | Purpose |
|----------|------|------|---------|
| Resource Group | `buhurt-fight-tracker-rg` | azurerm_resource_group | Container for all resources |
| App Service Plan | `buhurt-fight-tracker-plan` | azurerm_service_plan | Compute plan (Linux B1) |
| Web App | `buhurt-fight-tracker` | azurerm_linux_web_app | Python 3.13 app hosting |

## Configuration

### App Settings

The following environment variables are automatically configured:

- `DATABASE_URL`: Neon PostgreSQL connection string
- `SCM_DO_BUILD_DURING_DEPLOYMENT`: Enables build on deploy
- `WEBSITE_HTTPLOGGING_RETENTION_DAYS`: Log retention (7 days)

### Startup Command

```bash
bash startup.sh
```

This script:
1. Runs Alembic migrations (`alembic upgrade head`)
2. Starts Gunicorn with Uvicorn workers

## Cost Management

### Monthly Costs

- **Neon PostgreSQL**: $0 (free tier)
- **Azure App Service B1 (running)**: ~$13/month (prorated hourly)
- **Azure App Service B1 (stopped)**: $0

### Stop App Service

```bash
# From project root
bash scripts/az_stop.sh
```

### Start App Service

```bash
bash scripts/az_start.sh
```

### Destroy Infrastructure

```bash
terraform destroy
```

Type `yes` to confirm. All resources will be deleted.

### Recreate Later

```bash
terraform apply
```

Infrastructure is code - recreate anytime!

## Deployment Workflow

After infrastructure is created, code deployment uses GitHub Actions:

1. Push to `main` branch triggers `.github/workflows/deploy.yml`
2. Workflow runs tests
3. Workflow deploys code to Azure App Service
4. Azure runs `startup.sh` (migrations + app start)

## Troubleshooting

### App name already exists

**Error**: `A resource with the ID "/subscriptions/.../buhurt-fight-tracker" already exists`

**Solution**: App names must be globally unique. Change `app_name` in `terraform.tfvars`:
```hcl
app_name = "buhurt-fight-tracker-yourname"
```

### Database connection fails

**Error**: App returns 503 or database errors in logs

**Solution**: Verify `DATABASE_URL` in `terraform.tfvars` matches Neon connection string exactly:
```hcl
database_url = "postgresql+asyncpg://user:password@ep-xxx.us-east-2.aws.neon.tech/buhurt_db?sslmode=require"
```

Check Neon dashboard - database might be paused (free tier auto-pauses after inactivity).

### Terraform init fails

**Error**: `Failed to install provider`

**Solution**: Check internet connection, verify `required_providers` syntax in `provider.tf`

### Permission denied

**Error**: `The client does not have authorization`

**Solution**:
```bash
# Re-login to Azure
az login

# Verify subscription
az account list --output table
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

## Viewing Logs

### Azure Portal

1. Go to Azure Portal → App Services → buhurt-fight-tracker
2. Left menu → Log stream
3. View real-time logs

### Azure CLI

```bash
az webapp log tail --name buhurt-fight-tracker --resource-group buhurt-fight-tracker-rg
```

## Updating Infrastructure

1. Edit `.tf` files
2. Run `terraform plan` to preview changes
3. Run `terraform apply` to apply changes
4. Terraform will only modify changed resources

## Terraform State

State is stored locally in `terraform.tfstate` (gitignored).

For team collaboration, consider remote state backend (Azure Storage):
- Uncomment `backend "azurerm"` block in `provider.tf`
- Create storage account and container
- Run `terraform init -migrate-state`

## Interview Talking Points

**IaC Benefits**:
- "Infrastructure is version-controlled like application code"
- "Can destroy and recreate production environment in 3 minutes"
- "No manual portal clicks - everything is reproducible"

**Cost Awareness**:
- "Implemented stop/start scripts to keep costs under $5/month"
- "Can destroy with `terraform destroy` when not demoing"

**Portfolio Value**:
- "Demonstrates cloud platform expertise (Azure)"
- "Shows IaC proficiency (Terraform)"
- "Production deployment, not just local development"

## Next Steps

After infrastructure is running:

1. **Configure GitHub Secrets**:
   - `AZURE_WEBAPP_PUBLISH_PROFILE`: Download from Azure Portal → App Service → Deployment Center
   - `AZURE_WEBAPP_NAME`: `buhurt-fight-tracker`
   - `DATABASE_URL`: Your Neon connection string

2. **Deploy Code**:
   ```bash
   git checkout main
   git merge master
   git push origin main
   ```

3. **Verify**:
   ```bash
   curl https://buhurt-fight-tracker.azurewebsites.net/health
   curl https://buhurt-fight-tracker.azurewebsites.net/api/v1/countries
   ```

## Additional Resources

- [Terraform Azure Provider Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure App Service Linux Docs](https://docs.microsoft.com/en-us/azure/app-service/quickstart-python)
- [Neon PostgreSQL Docs](https://neon.tech/docs/introduction)
