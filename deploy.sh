#!/bin/bash
set -e

PROJECT_ID=$(gcloud config get-value project)
REGION='us-central1'
SERVICE_NAME="tattoo-web"

echo "Using Project ID: $PROJECT_ID"

# Read Client IDs from .env
GOOGLE_CLIENT_ID=$(grep VITE_GOOGLE_CLIENT_ID .env | cut -d '=' -f2)
FB_APP_ID=$(grep VITE_FB_APP_ID .env | cut -d '=' -f2)
LINE_CLIENT_ID=$(grep VITE_LINE_CLIENT_ID .env | cut -d '=' -f2)
LINE_CLIENT_SECRET=$(grep LINE_CLIENT_SECRET .env | cut -d '=' -f2)

echo "Building Docker image for $SERVICE_NAME..."
# Build from root context using the unified Dockerfile
docker build --platform linux/amd64 \
    --build-arg VITE_GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
    --build-arg VITE_FB_APP_ID="$FB_APP_ID" \
    --build-arg VITE_LINE_CLIENT_ID="$LINE_CLIENT_ID" \
    -t "gcr.io/$PROJECT_ID/$SERVICE_NAME" .

echo "Configuring Docker authentication..."
gcloud auth configure-docker --quiet

echo "Pushing Docker image..."
docker push "gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 2Gi \
    --port 8080 \
    --set-env-vars LINE_CLIENT_SECRET="$LINE_CLIENT_SECRET"

# Get Service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo "------------------------------------------------"
echo "Deployment Complete!"
echo "Service URL: $SERVICE_URL"
echo "------------------------------------------------"
echo "IMPORTANT: Please add $SERVICE_URL to your Authorized JavaScript origins in Google Cloud Console."
echo "------------------------------------------------"
