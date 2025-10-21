#!/bin/bash

# Script to set up email secrets in Google Cloud Secret Manager
# Run this after getting your Gmail App Password

PROJECT_ID="mythic-aloe-467602-t4"
GMAIL_USER="sbayer2@gmail.com"

echo "This script will help you set up email secrets for password reset functionality."
echo "You need a Gmail App Password (not your regular password)."
echo "Get it from: https://myaccount.google.com/apppasswords"
echo ""

read -p "Enter your Gmail App Password (16 characters, no spaces): " GMAIL_APP_PASSWORD

# Create the secrets
echo "Creating SMTP_USER secret..."
echo -n "$GMAIL_USER" | gcloud secrets create SMTP_USER --data-file=- --project=$PROJECT_ID 2>/dev/null || \
  echo -n "$GMAIL_USER" | gcloud secrets versions add SMTP_USER --data-file=- --project=$PROJECT_ID

echo "Creating SMTP_PASSWORD secret..."
echo -n "$GMAIL_APP_PASSWORD" | gcloud secrets create SMTP_PASSWORD --data-file=- --project=$PROJECT_ID 2>/dev/null || \
  echo -n "$GMAIL_APP_PASSWORD" | gcloud secrets versions add SMTP_PASSWORD --data-file=- --project=$PROJECT_ID

echo "Creating FROM_EMAIL secret..."
echo -n "$GMAIL_USER" | gcloud secrets create FROM_EMAIL --data-file=- --project=$PROJECT_ID 2>/dev/null || \
  echo -n "$GMAIL_USER" | gcloud secrets versions add FROM_EMAIL --data-file=- --project=$PROJECT_ID

# Grant the Cloud Run service account access to the secrets
SERVICE_ACCOUNT="129438231958-compute@developer.gserviceaccount.com"

echo "Granting access to service account..."
gcloud secrets add-iam-policy-binding SMTP_USER \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding SMTP_PASSWORD \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding FROM_EMAIL \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID

echo ""
echo "Secrets created successfully!"
echo "Now you need to update the Cloud Run service to use these secrets."
echo ""
echo "The deploy script will handle linking these secrets to environment variables."