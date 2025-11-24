# Deploy SearXNG to Kubernetes

## 📋 Overview

This guide walks you through deploying SearXNG to Kubernetes step by step.

**SearXNG** is a metasearch engine that SearCrawl uses to get search results. It needs to be deployed separately.

---

## 🎯 Prerequisites

- Kubernetes cluster (1.20+)
- `kubectl` configured and connected to your cluster
- Access to pull Docker images from Docker Hub

---

## Step 0: Connect to AKS Cluster

**If you haven't connected yet or need to reconnect:**

```bash
# Connect to AKS cluster
az aks get-credentials \
  --resource-group <your-resource-group-name> \
  --name <your-aks-cluster-name>

# Verify connection
kubectl get nodes
```

**If you don't remember the cluster name:**
```bash
# List all AKS clusters
az aks list --output table
```

See [Connect to AKS](./CONNECT_TO_AKS.md) for detailed instructions.

---

## Step 1: Deploy SearXNG

### 1.1 Apply the Deployment

```bash
# Navigate to project directory (where k8s folder is located)
cd /Users/zhaoxiaofeng/SynologyDrive/Drive/Projects/DeepResearch/searCrawl-main

# Deploy SearXNG
kubectl apply -f k8s/searxng-deployment.yaml
```

### 1.2 Verify Deployment

```bash
# Check Pod status
kubectl get pods -l app=searxng

# Check Service
kubectl get svc searxng-service

# Expected output:
# NAME              TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)
# searxng-service   ClusterIP   10.x.x.x      <none>        8080/TCP
```

### 1.3 Test SearXNG (Temporary Port Forward)

```bash
# Port forward for testing (temporary, will use Ingress later)
kubectl port-forward svc/searxng-service 8080:8080

# In another terminal, test
curl http://localhost:8080

# Or open in browser: http://localhost:8080
```

**If you see the SearXNG search page, deployment is successful!**

---

## Step 2: Install Ingress Controller

### 2.1 Install NGINX Ingress Controller

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for it to be ready (may take 1-2 minutes)
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### 2.2 Get Ingress External IP

```bash
# Get the External IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Expected output:
# NAME                       TYPE           EXTERNAL-IP
# ingress-nginx-controller   LoadBalancer   20.xxx.xxx.xxx
```

**Save this IP address - you'll need it for DNS configuration.**

---

## Step 3: Configure Ingress (URL Routing)

### 3.1 Choose Your Approach

**Option A: HTTP (Development/Testing)**

Use this if you don't have a domain yet or want to test quickly.

```bash
# Edit k8s/searxng-ingress-http.yaml
# Then apply
kubectl apply -f k8s/searxng-ingress-http.yaml
```

**Access:** `http://<ingress-ip>/searxng`

**Option B: HTTPS (Production)**

Use this for production with a domain.

---

## Step 4: Configure HTTPS (Optional but Recommended)

### 4.1 Install cert-manager

```bash
# Install cert-manager (automatic certificate manager)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for it to be ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/instance=cert-manager \
  -n cert-manager \
  --timeout=90s
```

### 4.2 Configure Let's Encrypt Issuer

```bash
# Edit k8s/cert-manager-issuer.yaml
# Change email: your-email@example.com
# Then apply
kubectl apply -f k8s/cert-manager-issuer.yaml

# Verify
kubectl get clusterissuer
```

### 4.3 Configure HTTPS Ingress

```bash
# Edit k8s/searxng-ingress-https.yaml
# Change domain: your-domain.com
# Then apply
kubectl apply -f k8s/searxng-ingress-https.yaml

# Check certificate status
kubectl get certificate

# Wait for certificate to be issued (1-5 minutes)
kubectl get certificate -w
```

### 4.4 Configure DNS

**Point your domain to the Ingress IP:**

```bash
# Get Ingress IP
INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Add A record in your DNS:
# your-domain.com → $INGRESS_IP
```

**For Azure DNS:**
```bash
az network dns record-set a create \
  --resource-group <dns-rg> \
  --zone-name your-domain.com \
  --name @ \
  --target-resource <ingress-ip-resource-id>
```

### 4.5 Verify HTTPS Access

```bash
# Test HTTPS access
curl https://your-domain.com/searxng

# Check certificate
curl -v https://your-domain.com/searxng 2>&1 | grep -i certificate
```

---

## Step 5: Verify Deployment

### 5.1 Check All Resources

```bash
# Check Pods
kubectl get pods -l app=searxng

# Check Service
kubectl get svc searxng-service

# Check Ingress
kubectl get ingress searxng-ingress

# Check Certificate (if using HTTPS)
kubectl get certificate
```

### 5.2 Test Access

**HTTP (if using HTTP Ingress):**
```bash
INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$INGRESS_IP/searxng
```

**HTTPS (if using HTTPS Ingress):**
```bash
curl https://your-domain.com/searxng
```

### 5.3 Browser Test

Open in browser:
- HTTP: `http://<ingress-ip>/searxng`
- HTTPS: `https://your-domain.com/searxng`

You should see the SearXNG search interface.

---

## 🔧 Troubleshooting

### Problem 1: Pod Not Starting

```bash
# Check Pod status
kubectl describe pod -l app=searxng

# Check logs
kubectl logs -l app=searxng
```

### Problem 2: Cannot Access via Ingress

```bash
# Check Ingress
kubectl describe ingress searxng-ingress

# Check backend endpoints
kubectl get endpoints searxng-service

# Test from inside cluster
kubectl run test-pod --image=curlimages/curl --rm -it -- curl http://searxng-service:8080
```

### Problem 3: Certificate Not Issued

```bash
# Check certificate status
kubectl describe certificate searxng-tls-secret

# Check cert-manager logs
kubectl logs -n cert-manager -l app.kubernetes.io/instance=cert-manager

# Common issues:
# - DNS not configured correctly
# - Port 80 not accessible (needed for Let's Encrypt validation)
```

---

## 📝 Deployment Checklist

### Before Deployment

- [ ] Kubernetes cluster is ready
- [ ] `kubectl` is configured
- [ ] Have domain name (for HTTPS) or Ingress IP (for HTTP)

### Deployment Steps

- [ ] Deploy SearXNG (`kubectl apply -f k8s/searxng-deployment.yaml`)
- [ ] Verify Pod is running
- [ ] Install Ingress Controller
- [ ] Get Ingress External IP
- [ ] Configure Ingress (HTTP or HTTPS)
- [ ] Configure DNS (if using domain)
- [ ] Verify access

### After Deployment

- [ ] SearXNG Pod is running
- [ ] Service is created
- [ ] Ingress is configured
- [ ] Can access via URL
- [ ] HTTPS works (if configured)

---

## 🎯 Next Steps

After SearXNG is deployed and accessible:

1. **Deploy SearCrawl** - See `docs/DEPLOY_SEARCRAWL.md`
2. **Add SearCrawl to Ingress** - Use `/searcrawl` path
3. **Configure Other Services** - Add more paths as needed

---

## 📚 Related Documents

- [Deploy SearCrawl](./DEPLOY_SEARCRAWL.md)
- [Ingress and HTTPS Guide](./INGRESS_HTTPS.md)
- [Azure K8s Deployment](../AZURE_K8S_DEPLOYMENT.md)

---

## 🔗 Quick Reference

### Common Commands

```bash
# Deploy
kubectl apply -f k8s/searxng-deployment.yaml

# Check status
kubectl get pods,svc,ingress -l app=searxng

# View logs
kubectl logs -f deployment/searxng

# Port forward (temporary)
kubectl port-forward svc/searxng-service 8080:8080

# Delete (if needed)
kubectl delete -f k8s/searxng-deployment.yaml
```

---

**✅ Once SearXNG is accessible via URL, proceed to deploy SearCrawl!**

