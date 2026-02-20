# Setting Up Terraform Manual Workflow in GitHub Actions

This guide explains how to configure the manual Terraform workflow so you can run `terraform apply/plan/destroy` from the GitHub Actions UI.

---

## Overview

The manual workflow (`.github/workflows/terraform-manual.yml`) allows you to:
- Run `terraform plan` to preview changes
- Run `terraform apply` to create/update infrastructure
- Run `terraform destroy` to delete all resources

All from the GitHub Actions UI - no local Terraform needed!

---

## Prerequisites

1. **Azure CLI** installed and authenticated
2. **Azure subscription** with permissions to create Service Principals
3. **GitHub repository** with admin access to manage secrets

---

## Step 1: Create Azure Service Principal

A Service Principal is an identity that GitHub Actions will use to authenticate with Azure.

### Option A: Using Azure CLI (Recommended)

```bash
# Login to Azure
az login

# Get your subscription ID
az account show --query id -o tsv

# Create Service Principal with Contributor role
# Replace YOUR_SUBSCRIPTION_ID with actual value
az ad sp create-for-rbac \
  --name "github-buhurt-terraform" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth
```

**Output** (save this - you'll need it for GitHub Secrets):
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

**Copy the ENTIRE JSON output** - you'll paste it into GitHub Secrets.

### Option B: Using Azure Portal

1. Go to Azure Active Directory → App registrations → New registration
2. Name: `github-buhurt-terraform`
3. After creation, go to Certificates & secrets → New client secret
4. Copy the secret value (you can't see it again!)
5. Go to Subscriptions → Your subscription → Access control (IAM)
6. Add role assignment → Contributor → Select the app you created
7. Manually construct JSON with clientId, clientSecret, subscriptionId, tenantId

---

## Step 2: Configure GitHub Secrets

Go to your GitHub repository:

**Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### Required Secrets

| Secret Name | Value | Where to Get It |
|-------------|-------|-----------------|
| `AZURE_CREDENTIALS` | Entire JSON output from Step 1 | Service Principal creation command |
| `DATABASE_URL` | Your Neon connection string | Neon dashboard (already have this) |

**Example AZURE_CREDENTIALS**:
```json
{
  "clientId": "12345678-1234-1234-1234-123456789012",
  "clientSecret": "your-secret-here",
  "subscriptionId": "87654321-4321-4321-4321-210987654321",
  "tenantId": "abcdefab-cdef-abcd-efab-cdefabcdefab",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

**Example DATABASE_URL**:
```
postgresql+asyncpg://user:password@ep-xxx.us-east-2.aws.neon.tech/buhurt_db?sslmode=require
```

---

## Step 3: Configure Remote State Backend (Optional but Recommended)

If you're using GitHub Actions for Terraform, you should use remote state storage. This prevents conflicts if you run Terraform both locally and in GitHub.

### Create Azure Storage for Terraform State

```bash
# Set variables
RESOURCE_GROUP="terraform-state-rg"
STORAGE_ACCOUNT="buhurttfstate"  # Must be globally unique, lowercase, no hyphens
CONTAINER="tfstate"
LOCATION="eastus2"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
az storage account create \
  --resource-group $RESOURCE_GROUP \
  --name $STORAGE_ACCOUNT \
  --sku Standard_LRS \
  --encryption-services blob

# Get storage account key
ACCOUNT_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query '[0].value' -o tsv)

# Create blob container
az storage container create \
  --name $CONTAINER \
  --account-name $STORAGE_ACCOUNT \
  --account-key $ACCOUNT_KEY

echo "Storage account: $STORAGE_ACCOUNT"
echo "Container: $CONTAINER"
```

### Update terraform/provider.tf

Uncomment the backend block and fill in values:

```hcl
terraform {
  required_version = ">= 1.7"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "buhurttfstate"  # Your storage account name
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}
```

### Migrate Local State to Remote

```bash
cd terraform/

# Re-initialize with backend
terraform init -migrate-state

# Terraform will ask: "Do you want to copy existing state to the new backend?"
# Type: yes
```

Now your state is stored in Azure, accessible from both local and GitHub Actions!

---

## Step 4: Test the Workflow

### From GitHub UI

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Click **Terraform (Manual)** workflow (left sidebar)
4. Click **Run workflow** button (right side)
5. Choose action:
   - **plan**: Preview what will be created (safe, read-only)
   - **apply**: Create infrastructure (writes changes)
   - **destroy**: Delete all infrastructure (destructive!)
6. Click **Run workflow**
7. Watch the logs

### Expected Output

**For `plan`**:
```
Terraform will perform the following actions:

  # azurerm_resource_group.main will be created
  + resource "azurerm_resource_group" "main" {
      + id       = (known after apply)
      + location = "eastus2"
      + name     = "buhurt-fight-tracker-rg"
    }

  # ... more resources

Plan: 3 to add, 0 to change, 0 to destroy.
```

**For `apply`**:
```
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

app_url = "https://buhurt-fight-tracker.azurewebsites.net"
app_name = "buhurt-fight-tracker"
resource_group_name = "buhurt-fight-tracker-rg"
```

---

## Step 5: Local vs. GitHub Workflow

You now have **two options** for running Terraform:

### Option A: Local Terraform

```bash
cd terraform/

# Create terraform.tfvars with DATABASE_URL
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars

# Run commands
terraform init
terraform plan
terraform apply
terraform destroy
```

**Pros**: Full control, faster feedback
**Cons**: Requires Terraform installed locally

### Option B: GitHub Actions Workflow

1. Go to Actions → Terraform (Manual) → Run workflow
2. Choose action (plan/apply/destroy)
3. Wait for completion

**Pros**: No local Terraform needed, runs in cloud
**Cons**: Slower, uses GitHub Actions minutes

**Recommended**: Use local for development, GitHub for team collaboration or when you don't have Terraform installed.

---

## Troubleshooting

### "Error: Failed to get existing workspaces"

**Solution**: Remote state backend not configured. Either:
1. Set up remote backend (Step 3), OR
2. Remove backend block from `provider.tf` and use local state only

### "Error: Unauthorized"

**Solution**: Service Principal credentials incorrect.
- Verify `AZURE_CREDENTIALS` secret is correct JSON
- Check Service Principal has Contributor role
- Try re-creating Service Principal

### "Error: Subscription ID not found"

**Solution**: Update `AZURE_CREDENTIALS` with correct `subscriptionId`:
```bash
az account show --query id -o tsv
```

### "Error: storage account already exists"

**Solution**: Storage account names must be globally unique. Change `buhurttfstate` to something unique like `buhurttfstate<yourname>`.

---

## Security Best Practices

1. **Service Principal**: Use minimal required permissions (Contributor on subscription)
2. **Secrets**: Never commit `AZURE_CREDENTIALS` or `DATABASE_URL` to git
3. **State File**: State file contains secrets - keep backend secure (Azure Storage has encryption by default)
4. **Destroy Protection**: Consider adding `prevent_destroy` lifecycle rule for production

---

## Cost Management

**With Manual Workflow, you can**:
- Run `destroy` from GitHub Actions when not demoing ($0 cost)
- Run `apply` before interviews (recreate in 3 minutes)
- No need to keep infrastructure running 24/7

**Monthly Cost**:
- Infrastructure destroyed: $0
- Infrastructure running: ~$13/month (App Service B1)
- Target: <$5/month (mostly destroyed)

---

## Next Steps

After setup is complete:

1. **Test plan**: Run workflow with `plan` action
2. **Create infrastructure**: Run workflow with `apply` action
3. **Verify deployment**: Check app URL in workflow output
4. **Configure code deployment**: Set up `AZURE_WEBAPP_PUBLISH_PROFILE` for deploy.yml
5. **Test destroy**: Run workflow with `destroy` action (optional)

---

## Reference

- [Azure Service Principal Docs](https://learn.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli)
- [Terraform Azure Backend](https://www.terraform.io/language/settings/backends/azurerm)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
