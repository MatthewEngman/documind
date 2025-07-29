# GitHub Actions Workflows

## deploy-backend.yml

Automatically deploys the FastAPI backend to Google Cloud Run when:
- Changes are pushed to `master`/`main` branch in the `backend/` directory
- Pull requests affecting `backend/` are merged

### Required Secrets

Configure these in your GitHub repository settings under Settings > Secrets and variables > Actions:

- `GCP_SERVICE_ACCOUNT_KEY`: JSON key for Google Cloud service account with Cloud Run deployment permissions
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `REDIS_HOST`: Redis Cloud host URL
- `REDIS_PASSWORD`: Redis Cloud password

### Service Account Permissions

The service account needs these IAM roles:
- Cloud Run Admin
- Service Account User
- Storage Admin (for container registry)

### Manual Setup

1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Add the key content as `GCP_SERVICE_ACCOUNT_KEY` secret in GitHub
4. Add other required secrets
5. Push changes to trigger deployment

The workflow will automatically deploy the backend and test the health endpoint.
