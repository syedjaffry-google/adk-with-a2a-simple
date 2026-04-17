export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project 2> /dev/null)

export GOOGLE_CLOUD_PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project 2>/dev/null) --format="value(projectNumber)")

kubectl create serviceaccount mcp-server-sa

gcloud projects add-iam-policy-binding projects/${GOOGLE_CLOUD_PROJECT}     --role=roles/aiplatform.user     --member=principal://iam.googleapis.com/projects/${GOOGLE_CLOUD_PROJECT_NUMBER}/locations/global/workloadIdentityPools/${GOOGLE_CLOUD_PROJECT}.svc.id.goog/subject/ns/default/sa/mcp-server-sa    --condition=None