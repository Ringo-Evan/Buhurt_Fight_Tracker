# Phase 4B: Infrastructure as Code Implementation Plan

**Created**: 2026-02-20
**Status**: In Progress
**Prerequisites**: Neon database configured ✅, No Azure resources created ✅
**Estimated Time**: 1-2 hours
**Decision**: DD-013 Option B (Terraform First)

---

## Overview

Implement Infrastructure as Code (IaC) using Terraform to provision Azure App Service for the Buhurt Fight Tracker API. This approach provides:
- Reproducible infrastructure (destroy/recreate at will)
- Version-controlled infrastructure (review changes like code)
- Portfolio demonstration of IaC expertise
- Better interview story than manual deployment

---

## Current State

**Completed**:
- ✅ Neon PostgreSQL database configured (Azure East US 2)
- ✅ Database connection string obtained
- ✅ Deployment workflow created (`.github/workflows/deploy.yml`)
- ✅ Startup script created (`startup.sh`)
- ✅ Cost management scripts created (`scripts/az_start.sh`, `scripts/az_stop.sh`)

**Not Created** (clean slate for IaC):
- ❌ Azure App Service
- ❌ Azure Resource Group
- ❌ Any Azure resources

This is the **perfect state** to start with Terraform - no resources to import or reconcile.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  GitHub Actions (CI/CD)                         │
│  - Runs tests on every push                     │
│  - Deploys to Azure on main branch push         │
│  - Uses Terraform for infrastructure            │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Azure App Service (Linux B1)                   │
│  - Python 3.13 runtime                          │
│  - Runs startup.sh on boot                      │
│  - Environment variables from Terraform         │
│  - Can be stopped/started for cost management   │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Neon PostgreSQL (Serverless)                   │
│  - Free tier, always-on                         │
│  - Azure East US 2 region                       │
│  - Connection string in GitHub Secrets          │
└─────────────────────────────────────────────────┘
```

---

## Terraform Basics

### What is Terraform?

Terraform is an Infrastructure as Code tool that lets you define cloud resources in configuration files (`.tf`). Instead of clicking through the Azure Portal, you write:

```hcl
resource "azurerm_linux_web_app" "app" {
  name                = "buhurt-fight-tracker"
  location            = "eastus2"
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id
  # ... more config
}
```

Then run:
- `terraform init` - Download Azure provider
- `terraform plan` - Preview changes
- `terraform apply` - Create resources
- `terraform destroy` - Delete everything

### Benefits for This Project

1. **Reproducibility**: Can recreate exact same infrastructure on demand
2. **Version Control**: Infrastructure changes reviewed like code
3. **Documentation**: `.tf` files document what exists
4. **Portfolio Value**: Shows IaC expertise (required for senior/lead roles)
5. **Cost Management**: Easy to destroy/recreate for demos

---

## File Structure

```
Buhurt_Fight_Tracker/
├── terraform/
│   ├── main.tf                 # Main infrastructure definition
│   ├── variables.tf            # Input variables (region, app name, etc.)
│   ├── outputs.tf              # Outputs (app URL, resource IDs)
│   ├── provider.tf             # Azure provider configuration
│   ├── terraform.tfvars        # Variable values (gitignored)
│   └── .gitignore              # Ignore .tfstate, .tfvars
│
├── .github/workflows/
│   ├── test.yml                # CI workflow (existing)
│   ├── deploy.yml              # CD workflow (update for Terraform)
│   └── terraform-destroy.yml   # Manual workflow to destroy resources
│
└── docs/planning/
    └── PHASE4B_IAC_IMPLEMENTATION.md  # This file
```

---

## Implementation Steps

### Step 1: Install Terraform (Local Machine)

**Why**: Need Terraform CLI to init and validate configurations

**Tasks**:
```bash
# Check if already installed
terraform version

# If not installed, use package manager:
# Windows (Chocolatey): choco install terraform
# macOS (Homebrew): brew install terraform
# Linux (apt): wget + install
```

**Success Criteria**: `terraform version` shows v1.7+

---

### Step 2: Create Terraform Configuration Files

**Why**: Define Azure infrastructure as code

**File 1: `terraform/provider.tf`**
```hcl
terraform {
  required_version = ">= 1.7"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

  # Optional: Remote state storage in Azure (can add later)
  # backend "azurerm" {
  #   resource_group_name  = "terraform-state-rg"
  #   storage_account_name = "buhurttfstate"
  #   container_name       = "tfstate"
  #   key                  = "prod.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {}
}
```

**File 2: `terraform/variables.tf`**
```hcl
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
  default     = "3.13"
}

variable "database_url" {
  description = "PostgreSQL connection string (from Neon)"
  type        = string
  sensitive   = true
}
```

**File 3: `terraform/main.tf`**
```hcl
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
  }

  app_settings = {
    "DATABASE_URL"                    = var.database_url
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "WEBSITE_HTTPLOGGING_RETENTION_DAYS" = "7"
  }

  # Startup command
  startup_command = "bash startup.sh"

  tags = {
    Project     = "Buhurt Fight Tracker"
    Environment = "Production"
  }
}
```

**File 4: `terraform/outputs.tf`**
```hcl
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
```

**File 5: `terraform/.gitignore`**
```
# Terraform state files
*.tfstate
*.tfstate.backup
*.tfstate.lock.info

# Variable files with secrets
terraform.tfvars
*.auto.tfvars

# Terraform directories
.terraform/
.terraform.lock.hcl

# Crash log files
crash.log
crash.*.log

# Override files
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# CLI configuration files
.terraformrc
terraform.rc
```

**File 6: `terraform/terraform.tfvars.example`**
```hcl
# Copy this file to terraform.tfvars and fill in values
# terraform.tfvars is gitignored for security

resource_group_name = "buhurt-fight-tracker-rg"
location            = "eastus2"
app_name            = "buhurt-fight-tracker"
sku_name            = "B1"
python_version      = "3.13"
database_url        = "postgresql+asyncpg://user:pass@host/db"  # Replace with actual
```

**Success Criteria**: All 6 files created, no syntax errors

---

### Step 3: Authenticate with Azure CLI

**Why**: Terraform uses Azure CLI credentials to create resources

**Tasks**:
```bash
# Install Azure CLI if needed
# Windows: winget install Microsoft.AzureCLI
# macOS: brew install azure-cli
# Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Set subscription (if multiple)
az account list --output table
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Verify
az account show
```

**Success Criteria**: `az account show` displays correct subscription

---

### Step 4: Initialize Terraform

**Why**: Download Azure provider, set up working directory

**Tasks**:
```bash
cd terraform/

# Initialize Terraform (downloads providers)
terraform init

# Validate configuration syntax
terraform validate

# Format files (optional, but clean)
terraform fmt
```

**Success Criteria**:
- `terraform init` completes successfully
- `terraform validate` shows "Success! The configuration is valid."

---

### Step 5: Create terraform.tfvars

**Why**: Provide actual values for variables (including DATABASE_URL secret)

**Tasks**:
```bash
cd terraform/

# Copy example
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with actual values
# - database_url: Get from Neon dashboard
# - Other values: Defaults are fine, or customize
```

**Security Note**: `terraform.tfvars` is gitignored - it contains the database password

**Success Criteria**: `terraform.tfvars` exists with real DATABASE_URL

---

### Step 6: Preview Changes with terraform plan

**Why**: See what Terraform will create before actually creating it

**Tasks**:
```bash
cd terraform/

# Generate execution plan
terraform plan -out=tfplan

# Review output - should show:
# - azurerm_resource_group.main will be created
# - azurerm_service_plan.main will be created
# - azurerm_linux_web_app.main will be created
```

**Success Criteria**: Plan shows 3 resources to create, 0 to change, 0 to destroy

---

### Step 7: Apply Infrastructure with terraform apply

**Why**: Actually create the Azure resources

**Tasks**:
```bash
cd terraform/

# Apply the plan
terraform apply tfplan

# Wait for completion (1-3 minutes)
# Terraform will output:
# - app_url
# - app_name
# - resource_group_name
```

**Success Criteria**:
- Apply completes with "Apply complete! Resources: 3 added, 0 changed, 0 destroyed."
- `app_url` output shows: https://buhurt-fight-tracker.azurewebsites.net
- Can curl the health endpoint: `curl https://buhurt-fight-tracker.azurewebsites.net/health`

---

### Step 8: Update GitHub Actions Deployment Workflow

**Why**: Need to deploy code to Terraform-created infrastructure

**Current Issue**: `.github/workflows/deploy.yml` uses `AZURE_WEBAPP_PUBLISH_PROFILE` which requires manual portal download

**Terraform Alternative**: Use Azure CLI deployment with Service Principal

**Option A: Keep Existing Workflow (Simpler)**
- Download publish profile from Azure Portal: App Service → Deployment Center → Manage publish profile
- Add to GitHub Secrets as `AZURE_WEBAPP_PUBLISH_PROFILE`
- No workflow changes needed

**Option B: Use Service Principal (More IaC-pure)**
- Create Azure Service Principal with Terraform
- Use `azure/login@v1` in workflow
- Deploy with `az webapp up`

**Recommendation for Phase 4B**: Use Option A (simpler, workflow already exists)

**Tasks**:
```bash
# In Azure Portal:
# 1. Go to App Service → buhurt-fight-tracker
# 2. Deployment Center → Manage publish profile → Download
# 3. Copy contents of downloaded .PublishSettings XML file

# In GitHub:
# 1. Repo → Settings → Secrets and variables → Actions
# 2. New repository secret:
#    Name: AZURE_WEBAPP_PUBLISH_PROFILE
#    Value: <paste XML contents>
# 3. Add secret: AZURE_WEBAPP_NAME = buhurt-fight-tracker
# 4. Add secret: DATABASE_URL = <Neon connection string>
```

**Success Criteria**: GitHub Secrets configured, workflow can deploy

---

### Step 9: Test Deployment

**Why**: Verify entire pipeline works end-to-end

**Tasks**:
```bash
# Merge master to main to trigger deploy workflow
git checkout main
git merge master
git push origin main

# Monitor GitHub Actions
# - Go to repo → Actions tab
# - Watch deploy workflow run
# - Verify tests pass
# - Verify deployment succeeds

# Test deployed API
curl https://buhurt-fight-tracker.azurewebsites.net/health
curl https://buhurt-fight-tracker.azurewebsites.net/api/v1/countries

# Check logs in Azure Portal
# App Service → Log stream
```

**Success Criteria**:
- GitHub Actions workflow completes successfully
- Health endpoint returns 200 OK
- API endpoints work
- Database migrations ran successfully

---

### Step 10: Test terraform destroy

**Why**: Verify infrastructure can be destroyed and recreated (IaC benefit)

**Tasks**:
```bash
cd terraform/

# Destroy all resources
terraform destroy

# Review what will be deleted (3 resources)
# Type 'yes' to confirm

# Wait for completion (1-2 minutes)

# Verify in Azure Portal - resource group should be gone

# Recreate (verify reproducibility)
terraform apply

# Verify app works again
curl https://buhurt-fight-tracker.azurewebsites.net/health
```

**Success Criteria**:
- Destroy removes all resources
- Apply recreates identical infrastructure
- App works after recreation

---

### Step 11: Create terraform-destroy GitHub Workflow (Optional)

**Why**: Allow manual destruction of resources from GitHub UI (cost management)

**File: `.github/workflows/terraform-destroy.yml`**
```yaml
name: Terraform Destroy

on:
  workflow_dispatch:  # Manual trigger only
    inputs:
      confirmation:
        description: 'Type "destroy" to confirm deletion of all Azure resources'
        required: true

jobs:
  destroy:
    runs-on: ubuntu-latest

    steps:
    - name: Validate confirmation
      if: github.event.inputs.confirmation != 'destroy'
      run: |
        echo "ERROR: Confirmation must be exactly 'destroy'"
        exit 1

    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v3
      with:
        terraform_version: 1.7.0

    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Terraform Init
      run: terraform init
      working-directory: ./terraform

    - name: Terraform Destroy
      run: terraform destroy -auto-approve
      working-directory: ./terraform
      env:
        TF_VAR_database_url: ${{ secrets.DATABASE_URL }}
```

**Success Criteria**: Workflow exists, can be triggered manually from Actions tab

---

### Step 12: Update Documentation

**Why**: Document IaC setup for future reference and portfolio reviewers

**Files to Update**:

1. **README.md** - Add Infrastructure section:
```markdown
## Infrastructure

This project uses **Infrastructure as Code** with Terraform to provision Azure resources.

### Prerequisites
- Azure subscription
- Azure CLI (`az login`)
- Terraform 1.7+

### Deployment

```bash
# Initialize Terraform
cd terraform/
terraform init

# Create terraform.tfvars with DATABASE_URL
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars - add your Neon connection string

# Preview changes
terraform plan

# Create infrastructure
terraform apply

# Destroy infrastructure (when done)
terraform destroy
```

### Architecture
- **App Service**: Linux B1 tier (~$13/mo, can be stopped)
- **Database**: Neon PostgreSQL (free tier, serverless)
- **CI/CD**: GitHub Actions (tests + deploys to main branch)

### Cost Management
```bash
# Stop app service (via Azure CLI)
bash scripts/az_stop.sh

# Start app service
bash scripts/az_start.sh

# Or destroy everything with Terraform
terraform destroy
```
```

2. **PROGRESS.md** - Update Phase 4B status:
```markdown
### Phase 4B: Infrastructure as Code ✅ COMPLETE

**Completed**: 2026-02-20
**Time Spent**: ~2 hours

**Deliverables**:
- ✅ Terraform configuration files (`terraform/*.tf`)
- ✅ Azure App Service created via Terraform
- ✅ GitHub Actions deployment workflow
- ✅ Documentation updated (README.md)
- ✅ Tested destroy/recreate cycle

**Infrastructure**:
- Resource Group: `buhurt-fight-tracker-rg`
- App Service: `buhurt-fight-tracker` (Linux B1, Python 3.13)
- Database: Neon PostgreSQL (Azure East US 2)

**Success Criteria** (all met):
- ✅ Infrastructure defined as code (version controlled)
- ✅ Can destroy and recreate with `terraform apply`
- ✅ GitHub Actions deploys on push to main
- ✅ API accessible at public URL
- ✅ All tests passing in production
```

3. **DECISIONS.md** - Mark DD-013 as decided:
```markdown
### DD-013: Phase 4 Deployment Approach ✅ DECIDED

**Decision**: Option B - Terraform First (Infrastructure as Code from day 1)

**Rationale**:
- Better portfolio story (IaC expertise demonstrated)
- Reproducible infrastructure (destroy/recreate anytime)
- Version-controlled infrastructure changes
- No manual portal clicks to document or reproduce
- Learning investment pays off (Terraform skill applicable to all cloud providers)

**Implemented**: 2026-02-20 - See `terraform/` directory
```

**Success Criteria**: All documentation updated and committed

---

## Testing Checklist

After completing all steps, verify:

- [ ] `terraform plan` shows no changes (infrastructure matches code)
- [ ] `terraform apply` completes in <3 minutes
- [ ] `terraform destroy` removes all resources
- [ ] App accessible at https://buhurt-fight-tracker.azurewebsites.net
- [ ] Health endpoint returns 200: `/health`
- [ ] API endpoints work: `/api/v1/countries`
- [ ] GitHub Actions deploys on push to `main`
- [ ] All tests pass in CI/CD pipeline
- [ ] Database migrations run on deployment
- [ ] Logs visible in Azure Portal
- [ ] Can stop/start app service with scripts
- [ ] `terraform.tfvars` is gitignored (not committed)
- [ ] Documentation updated (README, PROGRESS, DECISIONS)

---

## Success Criteria

Phase 4B is complete when:

1. **Infrastructure as Code**: All Azure resources defined in Terraform
2. **Reproducible**: Can destroy and recreate infrastructure with `terraform apply`
3. **Deployed**: API running at public URL
4. **CI/CD Working**: GitHub Actions deploys on push to main
5. **Documented**: README explains infrastructure setup
6. **Portfolio Ready**: Can demo IaC in interviews

---

## Cost Management

**Monthly Costs**:
- Neon PostgreSQL: $0 (free tier)
- Azure App Service B1 (running): ~$13/month prorated by hour
- Azure App Service B1 (stopped): $0

**Cost Optimization**:
```bash
# Stop when not demoing (saves money)
bash scripts/az_stop.sh

# Start for demos
bash scripts/az_start.sh

# Or destroy completely
cd terraform/
terraform destroy
# Recreate later with: terraform apply
```

**Target**: <$5/month during development (mostly stopped)

---

## Next Steps After Phase 4B

**Immediate**:
- Update LinkedIn with live API URL
- Add to resume: "Deployed production API with Terraform IaC"
- Test API with Postman/curl
- Monitor logs for errors

**Optional Enhancements**:
- Add Azure Application Insights (monitoring)
- Set up remote state backend (Azure Storage)
- Add custom domain name
- Implement blue/green deployment
- Add Terraform workspace (staging vs prod)

**Future Phases**:
- Phase 3B: Tag Expansion (weapon/league/ruleset) - Optional
- Phase 5: Authentication (v2)
- Phase 6: Frontend (v3)

---

## Interview Talking Points

When discussing this project:

**Technical Depth**:
- "I deployed the API using Infrastructure as Code with Terraform"
- "All Azure resources are version-controlled and reproducible"
- "I can destroy and recreate the entire environment in 3 minutes"
- "CI/CD pipeline runs tests and deploys on every merge to main"

**Decision Rationale**:
- "I chose Terraform over manual setup for reproducibility and IaC demonstration"
- "Selected Azure App Service for simplicity - could containerize with AKS later"
- "Used Neon serverless Postgres to minimize costs during development"

**Cost Awareness**:
- "Implemented stop/start scripts to keep costs under $5/month"
- "Can destroy infrastructure when not demoing, recreate with terraform apply"

**Portfolio Value**:
- "Demonstrates full-stack ownership: code → tests → infrastructure → deployment"
- "Shows cloud platform expertise (Azure) and IaC skills (Terraform)"
- "Production-ready deployment, not just local development"

---

## Troubleshooting

**Problem**: `terraform init` fails with "provider not found"
- **Solution**: Check internet connection, verify `required_providers` block syntax

**Problem**: `terraform apply` fails with "name already exists"
- **Solution**: App name must be globally unique, change `app_name` in `terraform.tfvars`

**Problem**: App returns 503 after deployment
- **Solution**: Check startup logs in Azure Portal → App Service → Log stream
- Common causes: Missing DATABASE_URL, migrations failed, gunicorn crash

**Problem**: Database connection fails
- **Solution**: Verify DATABASE_URL in App Settings matches Neon connection string
- Check Neon dashboard - database might be paused (free tier)

**Problem**: GitHub Actions deployment fails
- **Solution**: Verify secrets are configured: AZURE_WEBAPP_PUBLISH_PROFILE, DATABASE_URL

---

**Last Updated**: 2026-02-20
