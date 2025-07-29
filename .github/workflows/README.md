# GitHub Actions Workflows

## deploy-backend.yml

Automatically deploys the FastAPI backend to Google Cloud Run when:
- Changes are pushed to `master`/`main` branch in the `backend/` directory
- Pull requests affecting `backend/` are merged

### Required Secrets

Configure these in your GitHub repository settings under Settings > Secrets and variables > Actions:

- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `WIF_PROVIDER`: Workload Identity Federation provider (format: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID`)
- `WIF_SERVICE_ACCOUNT`: Service account email for impersonation (format: `SERVICE_ACCOUNT_NAME@PROJECT_ID.iam.gserviceaccount.com`)
- `REDIS_HOST`: Redis Cloud host URL
- `REDIS_PASSWORD`: Redis Cloud password

### Workload Identity Federation Setup

The recommended authentication method uses Workload Identity Federation instead of service account keys:

1. **Create a Workload Identity Pool:**
   ```bash
   gcloud iam workload-identity-pools create "github-pool" \
     --project="YOUR_PROJECT_ID" \
     --location="global" \
     --display-name="GitHub Actions Pool"
   ```

2. **Create a Workload Identity Provider:**
   ```bash
   gcloud iam workload-identity-pools providers create-oidc "github-provider" \
     --project="YOUR_PROJECT_ID" \
     --location="global" \
     --workload-identity-pool="github-pool" \
     --display-name="GitHub Actions Provider" \
     --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
     --issuer-uri="https://token.actions.githubusercontent.com"
   ```

3. **Grant permissions to the external identity:**
   ```bash
   gcloud iam service-accounts add-iam-policy-binding "YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --project="YOUR_PROJECT_ID" \
     --role="roles/iam.workloadIdentityUser" \
     --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/MatthewEngman/documind"
   ```

4. **Get the Workload Identity Provider resource name:**
   ```bash
   gcloud iam workload-identity-pools providers describe "github-provider" \
     --project="YOUR_PROJECT_ID" \
     --location="global" \
     --workload-identity-pool="github-pool" \
     --format="value(name)"
   ```

### Service Account Permissions

The service account needs these IAM roles:
- Cloud Run Admin
- Service Account User
- Storage Admin (for container registry)

### Manual Setup

1. Follow the Workload Identity Federation setup steps above
2. Add the required secrets to GitHub repository settings
3. Push changes to trigger deployment

The workflow will automatically deploy the backend and test the health endpoint.
