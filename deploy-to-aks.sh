#!/bin/bash
set -e

echo "=============================================="
echo "🚀 Deploying to AKS"
echo "=============================================="

# Configuration
DOCKER_USER="shankswhite"
FRONTEND_IMAGE="$DOCKER_USER/game-dashboard:latest"
RAG_IMAGE="$DOCKER_USER/rag-service:latest"
NAMESPACE="deep-research"

# Step 1: Build Frontend
echo ""
echo "📦 Step 1: Building Frontend Docker image..."
cd frontend/game-dashboard
docker build --platform linux/amd64 -t $FRONTEND_IMAGE .
echo "✅ Frontend image built"

# Step 2: Build RAG Service
echo ""
echo "📦 Step 2: Building RAG Service Docker image..."
cd ../../backend/rag-service
docker build --platform linux/amd64 -t $RAG_IMAGE .
echo "✅ RAG Service image built"

# Step 3: Push images
echo ""
echo "📤 Step 3: Pushing images to Docker Hub..."
docker push $FRONTEND_IMAGE
docker push $RAG_IMAGE
echo "✅ Images pushed"

# Step 4: Create namespace if not exists
echo ""
echo "🔧 Step 4: Setting up namespace..."
kubectl create namespace $NAMESPACE 2>/dev/null || echo "Namespace already exists"

# Step 5: Create secrets (if not exists)
echo ""
echo "🔐 Step 5: Creating secrets..."
kubectl create secret generic rag-secrets -n $NAMESPACE \
  --from-literal=azure-openai-api-key="DMXvkbbTS5ZsC6m8yzfmAo8cALObxEoke6pjS7ZSeQBXyIWlx7WgJQQJ99BLACYeBjFXJ3w3AAAAACOGS3T5" \
  --from-literal=azure-ai-api-key="DMXvkbbTS5ZsC6m8yzfmAo8cALObxEoke6pjS7ZSeQBXyIWlx7WgJQQJ99BLACYeBjFXJ3w3AAAAACOGS3T5" \
  --from-literal=postgres-password="xYC7xJsll27MoVxr6Sg0LeaueDut+g0OyYf8nR2TOmY=" \
  --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Secrets created"

# Step 6: Deploy RAG Service
echo ""
echo "🚀 Step 6: Deploying RAG Service..."
kubectl apply -f backend/rag-service/k8s/deployment.yaml
echo "✅ RAG Service deployed"

# Step 7: Deploy Frontend
echo ""
echo "🚀 Step 7: Deploying Frontend..."
kubectl apply -f frontend/game-dashboard/k8s/deployment.yaml
echo "✅ Frontend deployed"

# Step 8: Wait for pods
echo ""
echo "⏳ Step 8: Waiting for pods to be ready..."
kubectl rollout status deployment/rag-service -n $NAMESPACE --timeout=120s
kubectl rollout status deployment/game-dashboard -n $NAMESPACE --timeout=120s
echo "✅ All pods ready"

# Step 9: Show status
echo ""
echo "=============================================="
echo "📊 Deployment Status"
echo "=============================================="
kubectl get pods,svc -n $NAMESPACE

echo ""
echo "=============================================="
echo "✅ Deployment Complete!"
echo "=============================================="
echo ""
echo "📌 Next Steps:"
echo "1. Configure Cloudflare Tunnel to route:"
echo "   - dashboard.aiverse.chat → game-dashboard-service.deep-research:80"
echo "   - api.aiverse.chat → rag-service.deep-research:8080"
echo ""
echo "2. Or use kubectl port-forward for testing:"
echo "   kubectl port-forward svc/game-dashboard-service 3000:80 -n deep-research"
echo ""


