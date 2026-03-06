# StockNews — GCP/GKE Deployment

## Architecture

StockNews runs as a Kubernetes **CronJob** on the `voicebuddy-standard` GKE cluster (us-west1-b), in the `stocknews` namespace. It executes Mon–Fri at 8:00 AM Pacific, fetches market news, and sends a digest email. The job runs to completion and exits.

## One-time setup

### 1. Build and push the container image

```bash
gcloud builds submit --config cloudbuild.yaml .
```

### 2. Create the Kubernetes secret (with real values)

```bash
kubectl create secret generic stocknews-secrets -n stocknews \
  --from-literal=RECIPIENTS='lichendong@gmail.com' \
  --from-literal=AGENTMAIL_API_KEY='...' \
  --from-literal=ANTHROPIC_API_KEY='...' \
  --from-literal=BRAVE_API_KEY='...'
```

### 3. Apply Kubernetes manifests

```bash
kubectl apply -f k8s/
```

> Cloud Build already runs `kubectl apply` during builds, but you may need to apply manually the first time or when updating manifests without a code change.

## Checking status

```bash
# CronJob status
kubectl get cronjob -n stocknews

# Recent jobs
kubectl get jobs -n stocknews

# Logs from the latest job
kubectl logs -n stocknews job/$(kubectl get jobs -n stocknews --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
```

## Note

The GitHub Actions schedule (`daily.yml`) has been disabled in favour of this GKE CronJob. Manual runs via `workflow_dispatch` are still available.
