# SearCrawl Deployment Documentation

## 📚 Documentation Index

### Getting Started

0. **[Create AKS Cluster](./CREATE_AKS_CLUSTER.md)** - Create AKS cluster in Azure
1. **[Connect to AKS](./CONNECT_TO_AKS.md)** - How to connect to Azure Kubernetes Service

### Deployment Guides

2. **[Deploy SearXNG](./DEPLOY_SEARXNG.md)** - Step-by-step guide to deploy SearXNG
3. **[Deploy SearCrawl](./DEPLOY_SEARCRAWL.md)** - Step-by-step guide to deploy SearCrawl
4. **[Ingress and HTTPS](./INGRESS_HTTPS.md)** - Configure Ingress Controller and HTTPS certificates

### Usage Guides

5. **[Service Usage Guide](./SERVICE_USAGE_GUIDE.md)** - Complete guide: Input, Output, and Configurable Parameters
6. **[API Usage](./API_USAGE.md)** - How to use the SearCrawl API

---

## 🚀 Quick Start

### Step 1: Deploy SearXNG

```bash
kubectl apply -f k8s/searxng-deployment.yaml
```

See [Deploy SearXNG](./DEPLOY_SEARXNG.md) for detailed steps.

### Step 2: Deploy SearCrawl

```bash
# Build and push image
docker build -t your-registry/searcrawl:latest .
docker push your-registry/searcrawl:latest

# Deploy
kubectl apply -f k8s/deployment.yaml
```

See [Deploy SearCrawl](./DEPLOY_SEARCRAWL.md) for detailed steps.

---

## 📖 Documentation Structure

```
docs/
├── README.md              # This file
├── DEPLOY_SEARXNG.md      # SearXNG deployment guide
├── DEPLOY_SEARCRAWL.md    # SearCrawl deployment guide
├── INGRESS_HTTPS.md       # Ingress and HTTPS configuration
└── API_USAGE.md           # API usage examples
```

---

## 🔗 Related Resources

- [Main README](../README.md)
- [Quick Start Guide](../QUICKSTART.md)
- [Deployment Guide](../DEPLOYMENT.md)

