# Description
AI Agents built with ADK with A2A. The Plotwriter agent is an orchestrator of 4 sub agents, one of which is a remote A2A capable agent. Plotwriter creates a movie plot from user input on a historical figure. The remote A2A agent is the wiki researcher that performs wikipedia searches on the topic and returns results to Plotwriter. All other sub agents are locally integrated within Plotwriter agent.py code.

![Plotwriter](images/Plotwriter-agent.png)


# Deployemnt
These agents can be deloyed on both Agent Engine or GKE

## Agent Engine
Run the following CLI commands from the root directory of each agent.

```bash
cd plotwriter

adk deploy agent_engine --project [YOUR PROJECT NAME] --region [REGION] movie_plotwriter

cd researcher

adk deploy agent_engine --project [YOUR PROJECT NAME] --region [REGION] wiki_researcher
```

## GKE
The Deployment.yaml creates a Gateway API that serves traffic on port 80.

### Pre-requisits
Ensure you have setup an Artifact Registry and created a repository to store the container images.

### Build & push container images
```bash
cd researcher

docker build --platform linux/amd64 -t [REGION]-docker.pkg.dev/[GCP-PROJECT-ID]/[REPO-NAME]/researcher-agent:latest .

docker push [REGION]-docker.pkg.dev/[GCP-PROJECT-ID]/[REPO-NAME]/researcher-agent:latest

cd plotwriter

docker build --platform linux/amd64 -t [REGION]-docker.pkg.dev/[GCP-PROJECT-ID]/[REPO-NAME]/plotwriter-agent:latest .

docker push [REGION]-docker.pkg.dev/[GCP-PROJECT-ID]/[REPO-NAME]/plotwriter-agent:latest

cd mcp-server

docker build --platform linux/amd64 -t [REGION]-docker.pkg.dev/[GCP-PROJECT-ID]/[REPO-NAME]/movie-db-mcp-server:latest .

docker push [REGION]-docker.pkg.dev/[GCP-PROJECT-ID]/[REPO-NAME]/movie-db-mcp-server:latest

```

### Create Kubernetes service accounts
These script create a service account for each agent and bind it to the AI Platform user role via Google workload identity mechanism.

```bash
./plotwriter/K8s/create-service-account.sh
./researcher/K8s/create-service-account.sh
./mcp-server/K8s/create-service-account.sh
```

### Create static IP address
You'll need a static IP address for the load balancer so that it can be referenced in the ADK agent cards. You can create one using the following command:

```bash
gcloud compute addresses create [IP_ADDRESS_NAME] --global
```


### Create Kubernetes config map for env variables for agents
```bash
kubectl create configmap agent-config \
  --from-literal=PORT=8080 \
  --from-literal=GOOGLE_CLOUD_PROJECT="YOUR PROJECT ID" \
  --from-literal=PLOTWRITER_URL="http://[STATIC_IP_ADDRESS]/plotwriter" \
  --from-literal=RESEARCHER_URL="http://[STATIC_IP_ADDRESS]/researcher" \
  --from-literal=MOVIE_DB_MCP_URL="http://[STATIC_IP_ADDRESS]/movie-db-mcp" \
  --from-literal=GOOGLE_CLOUD_LOCATION="YOUR REGION" \
  --from-literal=GOOGLE_GENAI_USE_VERTEXAI="true" \
  --from-literal=MODEL="gemini-2.5-flash"
```

### Deploy to GKE 
(run it from the project root directory)
```bash
# 1. Export the environment variables
export PLOTWRITER_IMAGE="[YOUR-REGION]-docker.pkg.dev/[YOUR PROJECT ID]/[YOUR REPO]/plotwriter-agent:latest"
export RESEARCHER_IMAGE="[YOUR-REGION]-docker.pkg.dev/[YOUR PROJECT ID]/[YOUR REPO]/researcher-agent:latest"
export MCP_SERVER_IMAGE="[YOUR-REGION]-docker.pkg.dev/[YOUR PROJECT ID]/[YOUR REPO]/mcp-server-movie-db:latest"
export STATIC_IP_NAME="[YOUR STATIC IP NAME]"

envsubst < Deployment.yaml | kubectl apply -f -

```
