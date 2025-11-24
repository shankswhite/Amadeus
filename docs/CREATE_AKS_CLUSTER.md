# Create AKS Cluster Step by Step

## 📋 Overview

This guide walks you through creating an Azure Kubernetes Service (AKS) cluster in the `ai-analyst-rg` resource group.

**⚠️ Important:** You will need to choose your own cluster name and configuration. All commands below are templates that you should customize.

---

## 🎯 Prerequisites

- Azure CLI installed and logged in
- Resource group: `ai-analyst-rg` (already exists)
- Sufficient Azure subscription quota

---

## 🚀 Quick Start (Do It Yourself)

### Step 0: Register Resource Provider (First Time Only)

**Run this command first if you haven't created AKS before:**

```bash
az provider register --namespace Microsoft.ContainerService
```

**Wait for registration to complete (1-3 minutes):**

```bash
# Check status
az provider show -n Microsoft.ContainerService --query "registrationState"

# Wait until it shows "Registered"
```

### Step 1: Choose Your Configuration

**Before creating, decide:**

1. **Cluster name** - Choose your own name (e.g., `my-aks-cluster`, `production-k8s`, etc.)
   - Must be lowercase alphanumeric and hyphens only
   - Must be 1-63 characters
   - Example: `my-aks-cluster`

2. **Node count** - How many nodes?
   - `1` - Testing only (not recommended)
   - `2` - Minimum for high availability (recommended for start)
   - `3+` - Production

3. **VM size** - How powerful?
   - `Standard_B2s` - 2 vCPU, 4GB RAM (cost-effective, good for testing)
   - `Standard_D2s_v3` - 2 vCPU, 8GB RAM (better performance)
   - `Standard_D4s_v3` - 4 vCPU, 16GB RAM (production)

### Step 2: Create Your Cluster

**Replace `<YOUR-CLUSTER-NAME>` with your chosen name:**

```bash
az aks create \
  --resource-group ai-analyst-rg \
  --name <YOUR-CLUSTER-NAME> \
  --location westus2 \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --enable-managed-identity \
  --generate-ssh-keys
```

**This will take 5-10 minutes. Wait for completion.**

### Step 3: Connect to Your Cluster

**Replace `<YOUR-CLUSTER-NAME>` with your cluster name:**

```bash
az aks get-credentials \
  --resource-group ai-analyst-rg \
  --name <YOUR-CLUSTER-NAME>
```

### Step 4: Verify Connection

```bash
kubectl get nodes
```

**You should see your nodes listed.**

---

## 📖 Detailed Steps (Reference)

### Step 1: Check Current Status

### 1.1 Verify Resource Group

```bash
# Check resource group exists
az group show --name ai-analyst-rg --output table

# Should show:
# Location    Name
# ----------  -------------
# westus2     ai-analyst-rg
```

### 1.2 Check Azure Login

```bash
# Check if logged in
az account show

# If not logged in, run:
az login
```

---

## Step 2: Create AKS Cluster

### 2.1 Basic AKS Creation (Recommended for Start)

**⚠️ Customize the `--name` parameter with your own cluster name!**

```bash
# Create AKS cluster with basic configuration
# Replace <YOUR-CLUSTER-NAME> with your chosen name
az aks create \
  --resource-group ai-analyst-rg \
  --name <YOUR-CLUSTER-NAME> \
  --location westus2 \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --enable-managed-identity \
  --generate-ssh-keys
```

**Parameters explained:**
- `--resource-group ai-analyst-rg` - Your existing resource group (keep this)
- `--name <YOUR-CLUSTER-NAME>` - **YOUR cluster name** (choose your own!)
- `--location westus2` - Same location as resource group (keep this)
- `--node-count 2` - Number of nodes (you can change: 1, 2, 3, etc.)
- `--node-vm-size Standard_B2s` - VM size (you can change: Standard_B2s, Standard_D2s_v3, etc.)
- `--enable-managed-identity` - Use managed identity (recommended, keep this)
- `--generate-ssh-keys` - Auto-generate SSH keys (keep this)

**This will take 5-10 minutes to complete.**

### 2.2 Alternative: Smaller Configuration (For Testing)

If you want a smaller cluster for testing:

**⚠️ Replace `<YOUR-CLUSTER-NAME>` with your chosen name!**

```bash
az aks create \
  --resource-group ai-analyst-rg \
  --name <YOUR-CLUSTER-NAME> \
  --location westus2 \
  --node-count 1 \
  --node-vm-size Standard_B2s \
  --enable-managed-identity \
  --generate-ssh-keys
```

**Note:** Single node is not recommended for production but fine for testing.

### 2.3 Alternative: Larger Configuration (For Production)

For production with better performance:

**⚠️ Replace `<YOUR-CLUSTER-NAME>` with your chosen name!**

```bash
az aks create \
  --resource-group ai-analyst-rg \
  --name <YOUR-CLUSTER-NAME> \
  --location westus2 \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --enable-managed-identity \
  --generate-ssh-keys
```

---

## Step 3: Wait for Creation

**The creation process takes 5-10 minutes.**

You can monitor progress:

**⚠️ Replace `<YOUR-CLUSTER-NAME>` with your actual cluster name!**

```bash
# Check cluster status
az aks show --resource-group ai-analyst-rg --name <YOUR-CLUSTER-NAME> --query "provisioningState"

# Or watch the creation
watch -n 10 'az aks show --resource-group ai-analyst-rg --name <YOUR-CLUSTER-NAME> --query "provisioningState"'
```

**Wait until you see:** `"provisioningState": "Succeeded"`

---

## Step 4: Connect to AKS Cluster

### 4.1 Get Credentials

**⚠️ Replace `<YOUR-CLUSTER-NAME>` with your actual cluster name!**

```bash
# Connect to the cluster
az aks get-credentials \
  --resource-group ai-analyst-rg \
  --name <YOUR-CLUSTER-NAME>
```

**This will:**
- Download cluster credentials
- Configure `kubectl` to use this cluster
- Save to `~/.kube/config`

### 4.2 Verify Connection

```bash
# Check cluster info
kubectl cluster-info

# List nodes
kubectl get nodes

# Expected output:
# NAME                                STATUS   ROLES   AGE   VERSION
# aks-nodepool1-xxxxx-vmss000000     Ready    agent   5m    v1.28.0
# aks-nodepool1-xxxxx-vmss000001     Ready    agent   5m    v1.28.0
```

---

## Step 5: Verify Cluster is Ready

### 5.1 Check All Resources

```bash
# Check nodes
kubectl get nodes

# Check system pods
kubectl get pods -n kube-system

# Check cluster info
kubectl cluster-info
```

### 5.2 Test with a Simple Pod

```bash
# Create a test pod
kubectl run test-pod --image=nginx --restart=Never

# Check if it's running
kubectl get pods

# Delete test pod
kubectl delete pod test-pod
```

---

## 📊 Configuration Options

### VM Size Options

| Size | vCPU | RAM | Cost | Use Case |
|------|------|-----|------|----------|
| `Standard_B2s` | 2 | 4GB | Low | Development/Testing |
| `Standard_D2s_v3` | 2 | 8GB | Medium | Production (small) |
| `Standard_D4s_v3` | 4 | 16GB | High | Production (medium) |

### Node Count

- **1 node** - Testing only (not recommended)
- **2 nodes** - Minimum for high availability
- **3+ nodes** - Production recommended

---

## 💰 Cost Estimation

### Basic Configuration (2 nodes, Standard_B2s)

- **Node cost:** ~$30-40/month per node
- **Total:** ~$60-80/month
- **Plus:** Load balancer, storage, etc.

### Tips to Reduce Cost

1. **Use smaller VM size** - Standard_B2s instead of larger
2. **Reduce node count** - 1-2 nodes for development
3. **Use Spot instances** - Add `--enable-node-public-ip false` and spot nodes
4. **Stop when not in use** - Scale down to 0 nodes when not needed

---

## 🔧 Advanced Options (Optional)

### Enable Add-ons

```bash
# Enable monitoring (optional)
az aks create \
  ... \
  --enable-addons monitoring

# Enable HTTP application routing (for Ingress)
az aks create \
  ... \
  --enable-addons http_application_routing
```

### Configure Network

```bash
# Use custom virtual network
az aks create \
  ... \
  --vnet-subnet-id /subscriptions/.../resourceGroups/.../providers/Microsoft.Network/virtualNetworks/.../subnets/...
```

---

## 🐛 Troubleshooting

### Problem 1: Quota Exceeded

**Error:**
```
Operation could not be completed as it results in exceeding approved quota
```

**Solution:**
```bash
# Check quota
az vm list-usage --location westus2 --output table

# Request quota increase in Azure Portal
# Or use smaller VM size
```

### Problem 2: Creation Takes Too Long

**Normal:** 5-10 minutes is normal
**If > 15 minutes:** Check Azure Portal for errors

### Problem 3: Cannot Connect After Creation

**⚠️ Replace `<YOUR-CLUSTER-NAME>` with your actual cluster name!**

```bash
# Re-download credentials
az aks get-credentials --resource-group ai-analyst-rg --name <YOUR-CLUSTER-NAME> --overwrite-existing

# Check context
kubectl config current-context
```

---

## 📝 Complete Command Template (Customize Before Running)

**⚠️ IMPORTANT: Replace `<YOUR-CLUSTER-NAME>` with your own cluster name before running!**

**For development/testing (recommended to start):**

```bash
# Step 0: Register resource provider (first time only)
az provider register --namespace Microsoft.ContainerService

# Wait for registration (check status):
az provider show -n Microsoft.ContainerService --query "registrationState"
# Wait until it shows "Registered"

# Step 1: Create AKS cluster
# ⚠️ REPLACE <YOUR-CLUSTER-NAME> with your chosen name!
az aks create \
  --resource-group ai-analyst-rg \
  --name <YOUR-CLUSTER-NAME> \
  --location westus2 \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --enable-managed-identity \
  --generate-ssh-keys

# Step 2: Wait for completion (5-10 minutes)
# Check status (replace <YOUR-CLUSTER-NAME>):
az aks show --resource-group ai-analyst-rg --name <YOUR-CLUSTER-NAME> --query "provisioningState"

# Step 3: Once "Succeeded", connect (replace <YOUR-CLUSTER-NAME>):
az aks get-credentials --resource-group ai-analyst-rg --name <YOUR-CLUSTER-NAME>

# Step 4: Verify:
kubectl get nodes
```

**Example with a real name:**

```bash
# Example: If you choose "my-k8s-cluster" as the name
az aks create \
  --resource-group ai-analyst-rg \
  --name my-k8s-cluster \
  --location westus2 \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --enable-managed-identity \
  --generate-ssh-keys
```

---

## ✅ Verification Checklist

After creation:

- [ ] Cluster creation completed (`provisioningState: Succeeded`)
- [ ] Credentials downloaded successfully
- [ ] `kubectl get nodes` shows nodes
- [ ] Nodes are in `Ready` status
- [ ] Can create and delete test pods

---

## 🎯 Next Steps

Once AKS cluster is created and connected:

1. **Deploy SearXNG** - See [Deploy SearXNG](./DEPLOY_SEARXNG.md)
2. **Deploy SearCrawl** - See [Deploy SearCrawl](./DEPLOY_SEARCRAWL.md)

---

## 🔗 Related Documents

- [Connect to AKS](./CONNECT_TO_AKS.md)
- [Deploy SearXNG](./DEPLOY_SEARXNG.md)
- [Deploy SearCrawl](./DEPLOY_SEARCRAWL.md)

---

**💡 Tip: The cluster creation takes 5-10 minutes. You can monitor progress in Azure Portal or using `az aks show` command.**

