# Deploy SearCrawl to Kubernetes

## 📋 Overview

This guide walks you through deploying SearCrawl to Kubernetes after SearXNG is already deployed.

**Prerequisites:** SearXNG must be deployed and accessible first.

---

## 🎯 Prerequisites

- ✅ SearXNG is deployed and running
- ✅ SearXNG Service is accessible at `searxng-service:8080`
- ✅ Kubernetes cluster is ready
- ✅ Container registry access (ACR, Docker Hub, etc.)

---

## Step 0: Connect to AKS Cluster

**If not already connected:**

```bash
az aks get-credentials --resource-group <rg> --name <aks-name>
kubectl get nodes  # Verify connection
```

See [Connect to AKS](./CONNECT_TO_AKS.md) for details.

---

## Step 1: Build and Push Docker Image

### 1.1 Build Image

```bash
# Navigate to project directory
cd /Users/zhaoxiaofeng/SynologyDrive/Drive/Projects/DeepResearch/searCrawl-main

# Build image
docker build -t your-registry/searcrawl:latest .
```

### 1.2 Push to Registry

**For Azure Container Registry (ACR):**

```bash
# Login to ACR
az acr login --name your-acr-name

# Build and push
az acr build --registry your-acr-name --image searcrawl:latest .

# Or push existing image
docker tag searcrawl:latest your-acr-name.azurecr.io/searcrawl:latest
docker push your-acr-name.azurecr.io/searcrawl:latest
```

**For Docker Hub:**

```bash
docker tag searcrawl:latest your-dockerhub-username/searcrawl:latest
docker push your-dockerhub-username/searcrawl:latest
```

### 1.3 Configure AKS to Access ACR (Azure only)

```bash
# Attach ACR to AKS
az aks update -n <aks-name> -g <resource-group> --attach-acr <acr-name>
```

---

## Step 2: Update Deployment Configuration

### 2.1 Edit deployment.yaml

Edit `k8s/deployment.yaml`:

```yaml
spec:
  template:
    spec:
      containers:
      - name: searcrawl
        image: your-registry/searcrawl:latest  # ⚠️ Update this
        imagePullPolicy: Always
        env:
        - name: SEARXNG_HOST
          value: "searxng-service"  # ✅ Already configured
        - name: SEARXNG_PORT
          value: "8080"  # ✅ Already configured
```

**Key points:**
- Update `image` to your registry path
- `SEARXNG_HOST` is already set to `searxng-service` (K8s Service name)
- `SEARXNG_PORT` is already set to `8080`

---

## Step 3: Deploy SearCrawl

### 3.1 Apply Deployment

```bash
# Deploy SearCrawl
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -l app=searcrawl-api
kubectl get svc searcrawl-service
```

### 3.2 Verify Deployment

```bash
# Check Pod logs
kubectl logs -f deployment/searcrawl-api

# Look for:
# - "SearCrawl service starting..."
# - "Crawler initialized"
# - "Hybrid scorer initialized" (if dependencies installed)
```

### 3.3 Test Connection to SearXNG

```bash
# Test from SearCrawl Pod
kubectl exec -it <searcrawl-pod-name> -- curl http://searxng-service:8080

# Should return HTML response
```

---

## Step 4: Configure Ingress (Add to Existing)

### 4.1 Update Ingress Configuration

**If using HTTP Ingress:**

Edit `k8s/searxng-ingress-http.yaml` (or create new file):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: searcrawl-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /searxng
        pathType: Prefix
        backend:
          service:
            name: searxng-service
            port:
              number: 8080
      - path: /searcrawl  # Add SearCrawl path
        pathType: Prefix
        backend:
          service:
            name: searcrawl-service
            port:
              number: 80
```

**If using HTTPS Ingress:**

Edit `k8s/searxng-ingress-https.yaml`:

```yaml
spec:
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /searxng
        pathType: Prefix
        backend:
          service:
            name: searxng-service
            port:
              number: 8080
      - path: /searcrawl  # Add SearCrawl path
        pathType: Prefix
        backend:
          service:
            name: searcrawl-service
            port:
              number: 80
```

### 4.2 Apply Ingress

```bash
# Apply updated Ingress
kubectl apply -f k8s/searxng-ingress-http.yaml
# or
kubectl apply -f k8s/searxng-ingress-https.yaml

# Check Ingress
kubectl get ingress
kubectl describe ingress searcrawl-ingress
```

---

## Step 5: Verify Deployment

### 5.1 Check All Resources

```bash
# Check Pods
kubectl get pods -l app=searcrawl-api

# Check Service
kubectl get svc searcrawl-service

# Check Ingress
kubectl get ingress

# Check HPA (if configured)
kubectl get hpa searcrawl-hpa
```

### 5.2 Test API

**Health Check:**

```bash
# HTTP
INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$INGRESS_IP/searcrawl/health

# HTTPS
curl https://your-domain.com/searcrawl/health
```

**Search API:**

```bash
curl -X POST http://$INGRESS_IP/searcrawl/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python programming",
    "limit": 3
  }'
```

### 5.3 Browser Test

- Health: `http://<ingress-ip>/searcrawl/health`
- API Docs: `http://<ingress-ip>/searcrawl/docs`
- Search: Use the `/search` endpoint

---

## 🔧 Troubleshooting

### Problem 1: Cannot Connect to SearXNG

**Error:**
```
SearXNG request failed: Connection refused
```

**Check:**
```bash
# 1. Verify SearXNG is running
kubectl get pods -l app=searxng

# 2. Test service discovery
kubectl exec -it <searcrawl-pod> -- nslookup searxng-service

# 3. Test connection
kubectl exec -it <searcrawl-pod> -- curl http://searxng-service:8080

# 4. Check environment variables
kubectl exec <searcrawl-pod> -- env | grep SEARXNG
```

**Solution:**
- Ensure SearXNG is deployed
- Verify Service name is `searxng-service`
- Check they're in the same namespace

### Problem 2: Image Pull Failed

**Error:**
```
ImagePullBackOff
```

**Check:**
```bash
# Check image name
kubectl describe pod -l app=searcrawl-api | grep Image

# Verify image exists
az acr repository list --name <acr-name>
# or
docker pull your-registry/searcrawl:latest
```

**Solution:**
- Verify image name in deployment.yaml
- Check registry permissions
- For ACR, ensure AKS is attached: `az aks update --attach-acr`

### Problem 3: Pod OOMKilled

**Error:**
```
OOMKilled
```

**Solution:**
```yaml
# Increase memory limit in deployment.yaml
resources:
  limits:
    memory: "4Gi"  # Increase from 1Gi
```

---

## 📊 Resource Planning

### Minimum Configuration

- CPU: 500m
- Memory: 1Gi
- Replicas: 2

### Production Configuration

- CPU: 1000m
- Memory: 2Gi
- Replicas: 3-5

---

## 🎯 Next Steps

After SearCrawl is deployed:

1. **Test Search API** - Verify it works with SearXNG
2. **Monitor Performance** - Check resource usage
3. **Configure Auto-scaling** - HPA is already configured
4. **Add More Services** - Add other services to Ingress

---

## 📚 Related Documents

- [Deploy SearXNG](./DEPLOY_SEARXNG.md)
- [Ingress and HTTPS Guide](./INGRESS_HTTPS.md)
- [API Usage Examples](./API_USAGE.md)

---

## 🔗 Quick Reference

### Common Commands

```bash
# Deploy
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods,svc -l app=searcrawl-api

# View logs
kubectl logs -f deployment/searcrawl-api

# Scale
kubectl scale deployment searcrawl-api --replicas=5

# Restart
kubectl rollout restart deployment/searcrawl-api

# Update image
kubectl set image deployment/searcrawl-api searcrawl=your-registry/searcrawl:v1.1.0
```

---

**✅ Once SearCrawl is deployed and accessible, you can start using the search API!**

