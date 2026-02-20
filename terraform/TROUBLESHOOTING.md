# Terraform Troubleshooting Guide

## Error: "Operation cannot be completed without additional quota" (Basic VMs)

### Symptoms
```
Error: creating App Service Plan
Current Limit (Basic VMs): 0
```

### Root Cause
Your Azure subscription doesn't have quota allocated for Basic tier (B1) App Service Plans. This is common with:
- **Free/trial subscriptions** - Limited resources
- **Student subscriptions** - Restricted SKUs
- **New subscriptions** - Need quota requests
- **Certain regions** - Quota varies by region

### Solution 1: Use Free Tier (F1) - Recommended

The Free tier usually doesn't have quota restrictions.

**Update your `terraform.tfvars`:**
```hcl
sku_name = "F1"  # Free tier, $0/month
```

**Then retry:**
```bash
terraform apply
```

**Free tier limitations**:
- 60 CPU minutes per day
- 1 GB RAM
- 1 GB storage
- Always-on NOT supported (app sleeps after inactivity)
- Good for: Portfolio demos, development, low-traffic APIs

**Comparison**:
| Feature | F1 (Free) | B1 (Basic) |
|---------|-----------|------------|
| Cost | $0/month | ~$13/month |
| RAM | 1 GB | 1.75 GB |
| CPU | Shared | Dedicated |
| Always-on | ❌ No | ✅ Yes |
| Daily CPU | 60 min limit | Unlimited |
| Storage | 1 GB | 10 GB |

### Solution 2: Request Quota Increase

If you need Basic tier features (always-on, more resources):

1. **Check current quota**:
   ```bash
   az account show
   ```

2. **Request quota increase**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Search: "Quotas"
   - Select: "App Service"
   - Region: "East US 2"
   - Request: Increase "Basic VMs" from 0 to 1
   - Submit request (can take 24-48 hours)

3. **After approval**, update `terraform.tfvars`:
   ```hcl
   sku_name = "B1"
   ```

### Solution 3: Try Different Region

Some regions have different quota availability.

**Update `terraform.tfvars`:**
```hcl
location = "eastus"      # Try East US instead of East US 2
# or
location = "westus2"     # Try West US 2
# or
location = "centralus"   # Try Central US
```

**Note**: If changing region, also update Neon database region for best performance (or accept slight latency).

### Solution 4: Verify Subscription Type

Check if you're using a student/trial subscription:

```bash
az account show --query '{name:name, state:state, type:subscriptionPolicies.quotaId}' -o table
```

**Subscription types**:
- `PayAsYouGo` - Full access, request quota
- `MSDN` - Limited resources
- `FreeTrial` - Very limited, upgrade to Pay-As-You-Go
- `AzureForStudents` - Restricted SKUs, F1 works

**If trial/student**: Upgrade to Pay-As-You-Go for full quota access.

### Solution 5: Use Different Deployment Platform

If Azure quota is blocked, consider alternatives for portfolio:

**Option A: Azure Container Instances (ACI)**
- No App Service quota needed
- Docker-based deployment
- Similar cost (~$10-15/month)

**Option B: Other Cloud Providers**
- **Google Cloud Run** - Free tier generous, serverless
- **AWS App Runner** - Similar to Azure App Service
- **Fly.io** - Developer-friendly, generous free tier
- **Railway** - Simple deployment, $5/month

**Option C: Serverless**
- **Azure Functions** - Different quota pool
- **AWS Lambda** - Free tier 1M requests/month
- **Vercel** - Great for APIs, free tier

## Current State After Error

Your resource group was created successfully:
```
azurerm_resource_group.main: Creation complete
```

**You have two options**:

### Option A: Continue with Free Tier
```bash
# Update terraform.tfvars: sku_name = "F1"
terraform apply
```
Terraform will create the remaining resources using Free tier.

### Option B: Clean Up and Start Over
```bash
terraform destroy  # Removes resource group
# Then request quota or try different region
terraform apply
```

## Recommended Path for Portfolio

**For a portfolio project, F1 (Free tier) is perfectly acceptable**:

✅ **Pros**:
- Demonstrates deployment skills
- API is accessible via public URL
- Zero cost when not demoing
- IaC still shows Terraform proficiency

❌ **Cons**:
- App sleeps after 20 min inactivity (first request slower)
- CPU limits (60 min/day)

**Interview talking point**:
> "I deployed to Azure App Service Free tier for cost optimization during development. For production, I'd scale to Basic or Standard tier for dedicated resources and always-on capability. The Terraform configuration makes this a one-line change."

## Next Steps

**Quick fix (recommended for portfolio)**:
1. Update `terraform.tfvars`: `sku_name = "F1"`
2. Run: `terraform apply`
3. Test: API should be accessible

**Long-term fix (if needed)**:
1. Request quota increase for Basic tier
2. Update `terraform.tfvars`: `sku_name = "B1"`
3. Run: `terraform apply` (Terraform will upgrade in-place)

## Verification

After successful apply, test the deployment:

```bash
# Get app URL from Terraform output
terraform output app_url

# Test health endpoint
curl $(terraform output -raw app_url)/health

# Expected: {"status": "healthy"}
```

## Cost Management

**Free tier (F1)**:
- Cost: $0/month permanently
- No need to stop/start
- No destroy/recreate dance

**Basic tier (B1)** (after quota approval):
- Cost: ~$13/month when running
- Stop when not demoing: `bash ../scripts/az_stop.sh`
- Start for demos: `bash ../scripts/az_start.sh`
- Or destroy: `terraform destroy` ($0), recreate later

## Additional Help

- [Azure App Service Pricing](https://azure.microsoft.com/pricing/details/app-service/linux/)
- [Request Quota Increase](https://learn.microsoft.com/azure/azure-portal/supportability/regional-quota-requests)
- [Azure Free Services](https://azure.microsoft.com/free/free-account-faq/)
