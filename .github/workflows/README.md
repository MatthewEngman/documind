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

### Service Account Permissions

The service account needs these IAM roles:
- Cloud Run Source Developer (comprehensive permissions for source deployments)
- Service Account User (for impersonation)

### Manual Setup

1. Follow the Workload Identity Federation setup guide in `docs/deployment/WORKLOAD_IDENTITY_SETUP.md`
2. Add the required secrets to GitHub repository settings
3. Push changes to trigger deployment

The workflow will automatically deploy the backend and test the health endpoint.
