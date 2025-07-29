# Workload Identity Federation Setup for GitHub Actions

This guide walks you through setting up Workload Identity Federation for secure authentication between GitHub Actions and Google Cloud, eliminating the need for service account keys.

## Prerequisites

- Google Cloud project with billing enabled
- Google Cloud CLI installed and authenticated
- Repository admin access to configure GitHub secrets

## Step 1: Enable Required APIs

```bash
gcloud services enable iamcredentials.googleapis.com
gcloud services enable sts.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Step 2: Create a Service Account

```bash
# Create service account for Cloud Run deployments
gcloud iam service-accounts create github-actions-deployer \
  --project="YOUR_PROJECT_ID" \
  --display-name="GitHub Actions Deployer" \
  --description="Service account for GitHub Actions to deploy to Cloud Run"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

## Step 3: Create Workload Identity Pool

```bash
# Create the workload identity pool
gcloud iam workload-identity-pools create "github-pool" \
  --project="YOUR_PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool" \
  --description="Identity pool for GitHub Actions"
```

## Step 4: Create Workload Identity Provider

```bash
# Create the OIDC provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="YOUR_PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Actions Provider" \
  --description="OIDC provider for GitHub Actions" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == 'MatthewEngman'" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

## Step 5: Grant Workload Identity User Role

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")

# Grant the external identity permission to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding \
  "github-actions-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --project="YOUR_PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/MatthewEngman/documind"
```

## Step 6: Get Configuration Values

```bash
# Get the Workload Identity Provider resource name
WIF_PROVIDER=$(gcloud iam workload-identity-pools providers describe "github-provider" \
  --project="YOUR_PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)")

echo "WIF_PROVIDER: $WIF_PROVIDER"
echo "WIF_SERVICE_ACCOUNT: github-actions-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com"
echo "GCP_PROJECT_ID: YOUR_PROJECT_ID"
```

## Step 7: Configure GitHub Secrets

In your GitHub repository, go to Settings > Secrets and variables > Actions and add:

- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `WIF_PROVIDER`: The full provider resource name from Step 6
- `WIF_SERVICE_ACCOUNT`: `github-actions-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com`
- `REDIS_HOST`: Your Redis Cloud host URL
- `REDIS_PASSWORD`: Your Redis Cloud password

## Step 8: Test the Setup

Push a change to the `backend/` directory or manually trigger the workflow to test the authentication.

## Troubleshooting

### Common Issues

1. **"Permission denied" errors**: Verify the service account has the correct IAM roles
2. **"Workload identity pool not found"**: Check the provider resource name format
3. **"Token exchange failed"**: Verify the attribute condition matches your repository

### Verification Commands

```bash
# Check workload identity pool
gcloud iam workload-identity-pools describe github-pool \
  --project="YOUR_PROJECT_ID" \
  --location="global"

# Check provider configuration
gcloud iam workload-identity-pools providers describe github-provider \
  --project="YOUR_PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-pool"

# Check service account IAM bindings
gcloud iam service-accounts get-iam-policy \
  github-actions-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --project="YOUR_PROJECT_ID"
```

## Security Benefits

- **No long-lived credentials**: No service account keys to manage or rotate
- **Scoped access**: Authentication is limited to specific repositories and conditions
- **Audit trail**: All authentication events are logged in Google Cloud
- **Automatic rotation**: GitHub's OIDC tokens are short-lived and automatically rotated

## References

- [Google Cloud Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [google-github-actions/auth](https://github.com/google-github-actions/auth)
