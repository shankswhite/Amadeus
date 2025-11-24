# Ingress and HTTPS Configuration Guide

## 📋 Overview

This guide explains how to configure Ingress Controller and HTTPS certificates for your services in Kubernetes.

---

## 🎯 What is Ingress Controller?

**Ingress Controller** is a Kubernetes standard component that provides:
- ✅ **Unified entry point** - Single URL/IP for all services
- ✅ **Path-based routing** - Different paths for different services
- ✅ **HTTPS termination** - Handles SSL/TLS certificates
- ✅ **Load balancing** - Distributes traffic

**It's NOT Azure-specific** - it's a standard K8s component that works on any Kubernetes cluster.

---

## 🔒 HTTPS Certificate Basics

### What is a Certificate?

**Certificate = Digital ID card** that proves your website is legitimate and encrypts traffic.

**Why needed:**
- Modern browsers require HTTPS
- Some APIs only accept HTTPS requests
- Security policies require encrypted connections

### Where is Certificate Installed?

**Certificate is stored in Kubernetes Secret** and used by Ingress Controller:

```
User → Ingress Controller (uses certificate) → Your Service
```

**You don't need to:**
- ❌ Manually download certificate files
- ❌ Upload to servers
- ❌ Configure certificates manually

**cert-manager does it automatically!**

---

## 🚀 Installation Steps

### Step 1: Install NGINX Ingress Controller

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for it to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

# Get External IP
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

### Step 2: Install cert-manager (Automatic Certificate Manager)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for it to be ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/instance=cert-manager \
  -n cert-manager \
  --timeout=90s
```

### Step 3: Configure Let's Encrypt Issuer

```bash
# Edit k8s/cert-manager-issuer.yaml
# Change email: your-email@example.com

# Apply
kubectl apply -f k8s/cert-manager-issuer.yaml

# Verify
kubectl get clusterissuer
```

### Step 4: Configure HTTPS Ingress

```bash
# Edit k8s/searxng-ingress-https.yaml
# Change domain: your-domain.com

# Apply
kubectl apply -f k8s/searxng-ingress-https.yaml

# Check certificate status
kubectl get certificate

# Wait for certificate issuance (1-5 minutes)
kubectl get certificate -w
```

### Step 5: Configure DNS

**Point your domain to Ingress IP:**

```bash
# Get Ingress IP
INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Add A record in DNS:
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

---

## 📊 How cert-manager Works

### Automatic Process

```
1. You configure Ingress: "Use HTTPS for your-domain.com"
   ↓
2. cert-manager sees the configuration
   ↓
3. cert-manager automatically:
   - Contacts Let's Encrypt: "I need a certificate for your-domain.com"
   - Let's Encrypt validates: "Is this domain yours?"
     * Uses HTTP-01 challenge (automatic)
   - Let's Encrypt issues certificate
   - cert-manager installs to K8s Secret
   - Ingress Controller uses the certificate
   ↓
4. User visits https://your-domain.com
   - Browser sees certificate ✅
   - Shows "Secure" lock icon ✅
```

**You only configure once, cert-manager handles everything automatically!**

---

## 🔧 Configuration Options

### Option 1: HTTP (Development/Testing)

**Use when:**
- No domain yet
- Quick testing
- Development environment

**Configuration:**
```yaml
# k8s/searxng-ingress-http.yaml
annotations:
  nginx.ingress.kubernetes.io/ssl-redirect: "false"
```

**Access:** `http://<ingress-ip>/searxng`

### Option 2: HTTPS with Let's Encrypt (Recommended)

**Use when:**
- Have domain name
- Production environment
- Need secure connections

**Configuration:**
```yaml
# k8s/searxng-ingress-https.yaml
annotations:
  cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: searxng-tls-secret
```

**Access:** `https://your-domain.com/searxng`

---

## 🔍 Certificate Storage

### Where Certificates are Stored

**In Kubernetes Secret:**

```bash
# View certificate secret
kubectl get secret searxng-tls-secret

# Certificate contains:
# - tls.crt (certificate file)
# - tls.key (private key file)
```

**Ingress Controller automatically reads and uses this secret.**

---

## 🐛 Troubleshooting

### Problem 1: Certificate Not Issued

**Check:**
```bash
# Check certificate status
kubectl describe certificate searxng-tls-secret

# Check cert-manager logs
kubectl logs -n cert-manager -l app.kubernetes.io/instance=cert-manager
```

**Common issues:**
- DNS not configured correctly
- Port 80 not accessible (needed for Let's Encrypt validation)
- Domain doesn't point to Ingress IP

### Problem 2: Certificate Expired

**Solution:**
cert-manager automatically renews certificates. Check:
```bash
kubectl get certificate
```

### Problem 3: HTTPS Redirect Loop

**Solution:**
Ensure `ssl-redirect` is set correctly:
```yaml
annotations:
  nginx.ingress.kubernetes.io/ssl-redirect: "true"  # For HTTPS
  # or
  nginx.ingress.kubernetes.io/ssl-redirect: "false"  # For HTTP
```

---

## 📝 Summary

### Ingress Controller

- **NGINX Ingress** - Standard K8s component, works everywhere
- **AGIC** - Azure-specific, better Azure integration

### HTTPS Certificates

- **Let's Encrypt** - Free, automatic, recommended
- **Azure Key Vault** - Enterprise-grade, for production
- **Self-signed** - Development/testing only

### Certificate Installation

- **Stored in:** Kubernetes Secret
- **Used by:** Ingress Controller
- **Managed by:** cert-manager (automatic)

---

## 🔗 Related Documents

- [Deploy SearXNG](./DEPLOY_SEARXNG.md)
- [Deploy SearCrawl](./DEPLOY_SEARCRAWL.md)

---

**💡 Key Point: cert-manager automatically handles certificate application, installation, and renewal. You just configure once!**

