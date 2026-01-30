# Telegraf Configuration Manager - Deployment Guide

## Prerequisites

Before starting, ensure you have the following installed:
- Docker (or compatible container runtime)
- A running Kubernetes cluster (minikube, kind, or any local cluster)
- kubectl configured to communicate with your cluster
- Access to the project directory: `/project/telegraf-config-app`

---

## Step-by-Step Deployment Instructions

### Step 1: Build the Docker Image

Navigate to the project directory and build the Docker image:

```bash
cd /project/telegraf-config-app
docker build -t telegraf-config-manager:latest .
```

**Note:** This builds a Flask-based web application with Python 3.11 and all required dependencies.

---

### Step 2: Load Image into Local Kubernetes Cluster

If you're using containerd (native Kubernetes runtime) or a local cluster that doesn't share the Docker daemon:

```bash
# Save the Docker image
docker save telegraf-config-manager:latest | sudo ctr -n k8s.io images import -
```

**Alternative for minikube:**
```bash
eval $(minikube docker-env)
docker build -t telegraf-config-manager:latest .
```

---

### Step 3: Deploy to Kubernetes

You have three deployment options. Choose one:

#### Option A: Simple Pod Deployment (Quick Start)

```bash
kubectl apply -f k8s/pod.yaml
```

**Access the pod:**
```bash
kubectl port-forward pod/telegraf-config-manager-pod 5000:5000
```
Then access at: http://localhost:5000

#### Option B: Deployment with Service (Recommended for Production)

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

**Access via NodePort:**
```bash
kubectl get service telegraf-config-manager-service
```
The service exposes port 30080 on the node. Access at: http://<NODE_IP>:30080

#### Option C: Deployment with LoadBalancer

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/loadbalancer-service.yaml
```

**Access via LoadBalancer:**
```bash
kubectl get service telegraf-config-manager-service
```
Look for the EXTERNAL-IP and access at: http://<EXTERNAL-IP>:80

---

### Step 4: Verify Deployment

Check that the pod is running:

```bash
kubectl get pods -l app=telegraf-config-manager
```

Expected output:
```
NAME                                        READY   STATUS    RESTARTS   AGE
telegraf-config-manager-xxxxxxxxxx-xxxxx    1/1     Running   0          1m
```

Check the pod logs:

```bash
kubectl logs -l app=telegraf-config-manager
```

---

### Step 5: Access the Application

Once the pod is running, access the web interface:

**If using port-forward:**
```bash
kubectl port-forward deployment/telegraf-config-manager 5000:5000
```
Open: http://localhost:5000

**If using NodePort service:**
Find your node's IP:
```bash
kubectl get nodes -o wide
```
Open: http://<NODE_IP>:30080

**If using LoadBalancer service:**
```bash
minikube tunnel  # for minikube
```
Then check service for external IP.

---

### Step 6: Test the Application

Navigate to the web interface and verify:

1. Main page loads with configuration templates
2. Click "Load Template" to preview a template
3. Create a new configuration:
   - Enter a name (e.g., "test-config")
   - Select a template or edit manually
   - Click "Save Configuration"
4. Verify the configuration appears in the list
5. Download a configuration to test TOML export

---

## Cleanup

To remove the deployment:

```bash
# Remove pod and service
kubectl delete -f k8s/pod.yaml
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/deployment.yaml

# Or remove everything at once
kubectl delete all -l app=telegraf-config-manager
```

---

## Troubleshooting

### Issue: Pod is not starting

Check pod status and events:
```bash
kubectl describe pod -l app=telegraf-config-manager
```

Common fixes:
- Ensure image is loaded in the cluster
- Check `imagePullPolicy: Never` is set for local images
- Verify pod tolerations if node has resource constraints

### Issue: Cannot access the application

1. Check pod is running:
   ```bash
   kubectl get pods -l app=telegraf-config-manager
   ```

2. Check service endpoints:
   ```bash
   kubectl get endpoints telegraf-config-manager-service
   ```

3. Test connectivity from inside cluster:
   ```bash
   kubectl run curl-test --image=curlimages/curl -i --rm --restart=Never -- curl http://telegraf-config-manager-service:80
   ```

4. Check port-forward if using local access:
   ```bash
   kubectl port-forward deployment/telegraf-config-manager 5000:5000
   ```

### Issue: Image pull errors

If using local image, ensure:
```yaml
imagePullPolicy: Never  # in deployment.yaml or pod.yaml
```

### Issue: Disk pressure on node

The deployment includes tolerations for disk pressure. If still failing:

Check node resources:
```bash
kubectl top nodes
kubectl describe node <node-name>
```

---

## Application Features

Once deployed, the application provides:

- **6 Pre-built Templates:**
  1. Basic CPU Monitoring
  2. Memory and Disk Monitoring
  3. Network Interface Monitoring
  4. Docker Container Monitoring
  5. Disk I/O Monitoring
  6. Comprehensive Disk Monitoring

- **Configuration Management:**
  - Create, view, edit, and delete configurations
  - Validate TOML syntax
  - Download configurations as `.conf` files

- **API Endpoints:**
  - `GET /` - Web interface
  - `GET /api/templates` - List templates
  - `POST /api/config` - Save configuration
  - `GET /api/configs` - List saved configs
  - `DELETE /api/config/<name>` - Delete config
  - `GET /api/config/<name>/download` - Download TOML

---

## Resource Requirements

The deployment is configured with:
- **CPU:** 100m (request) / 250m (limit)
- **Memory:** 128Mi (request) / 512Mi (limit)
- **Port:** 5000 (HTTP)

---

## Next Steps

After successful deployment:

1. Create custom Telegraf configurations for your monitoring needs
2. Download configurations as TOML files
3. Deploy configurations to your Telegraf instances:
   ```bash
   telegraf --config your-config.conf
   ```

---
