# Connect to Azure Kubernetes Service (AKS)

## 📋 Overview

This guide shows how to connect to your Azure AKS cluster using `kubectl`.

---

## 🔗 Connect to AKS Cluster

### Method 1: Using Azure CLI (Recommended)

```bash
# Connect to AKS cluster
az aks get-credentials \
  --resource-group <your-resource-group-name> \
  --name <your-aks-cluster-name>

# Example:
# az aks get-credentials --resource-group searcrawl-rg --name searcrawl-aks
```

### Method 2: If You Don't Remember Resource Group/Cluster Name

```bash
# List all AKS clusters in your subscription
az aks list --output table

# Output will show:
# Name          ResourceGroup    Location    KubernetesVersion    CurrentKubernetesVersion    ProvisioningState    Fqdn
# ------------  ---------------  ----------  -------------------  --------------------------  -------------------  ------------------------------------------------
# searcrawl-aks searcrawl-rg     eastus      1.28.0               1.28.0                     Succeeded            searcrawl-aks-xxxxx.hcp.eastus.azmk8s.io
```

Then use the resource group and name from the output:

```bash
az aks get-credentials \
  --resource-group <resource-group-from-list> \
  --name <cluster-name-from-list>
```

### Method 3: List All Resource Groups First

```bash
# List all resource groups
az group list --output table

# Then list AKS clusters in a specific resource group
az aks list --resource-group <resource-group-name> --output table
```

---

## ✅ Verify Connection

### Check Cluster Connection

```bash
# Check if connected
kubectl cluster-info

# Expected output:
# Kubernetes control plane is running at https://xxxxx.hcp.eastus.azmk8s.io:443
```

### Check Nodes

```bash
# List nodes
kubectl get nodes

# Expected output:
# NAME                                STATUS   ROLES   AGE   VERSION
# aks-nodepool1-xxxxx-vmss000000     Ready    agent   5d    v1.28.0
# aks-nodepool1-xxxxx-vmss000001     Ready    agent   5d    v1.28.0
```

### Check Current Context

```bash
# Show current context
kubectl config current-context

# List all contexts
kubectl config get-contexts

# Switch context (if needed)
kubectl config use-context <context-name>
```

---

## 🔍 Find Your AKS Cluster Information

### If You Don't Remember Details

```bash
# Option 1: List all AKS clusters
az aks list --output table

# Option 2: Search by name pattern
az aks list --query "[?contains(name, 'search') || contains(name, 'crawl')]" --output table

# Option 3: List all resources with "aks" in name
az resource list --resource-type "Microsoft.ContainerService/managedClusters" --output table
```

---

## 📝 Quick Reference

### Common Commands

```bash
# Connect
az aks get-credentials --resource-group <rg> --name <aks-name>

# Verify
kubectl get nodes

# Check current context
kubectl config current-context

# List all contexts
kubectl config get-contexts
```

### If Connection Fails

```bash
# Check Azure login
az account show

# Login if needed
az login

# Check subscription
az account list --output table

# Set subscription if needed
az account set --subscription <subscription-id>
```

---

## 🎯 Next Steps

After connecting to AKS:

1. **Verify connection** - `kubectl get nodes`
2. **Deploy SearXNG** - See [Deploy SearXNG](./DEPLOY_SEARXNG.md)
3. **Deploy SearCrawl** - See [Deploy SearCrawl](./DEPLOY_SEARCRAWL.md)

---

**💡 Tip: The connection is saved in `~/.kube/config`. You don't need to reconnect every time unless you switch clusters.**




