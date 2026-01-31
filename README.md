# Telegraf Configuration Manager - Deployment Guide

## Prerequisites

Before starting, ensure you have the following installed:
- Docker (or compatible container runtime)
- A running Kubernetes cluster (minikube, kind, or any local cluster)
- kubectl configured to communicate with your cluster
- Access to the project directory: `/project/telegraf-config-app`

**Important Note:** The Telegraf Configuration Manager has been updated to use the dedicated `telegraf-config-mgr` namespace for better resource isolation and management. Ensure this namespace exists:

```bash
kubectl create namespace telegraf-config-mgr
```

All deployments and kubectl commands must include the `-n telegraf-config-mgr` flag to target the correct namespace.

### Namespace Migration Notes

**If you previously deployed this application in the `default` namespace:**

1. **Clean up old resources:**
   ```bash
   kubectl delete deployment telegraf-config-manager -n default
   kubectl delete service telegraf-config-manager-service -n default
   kubectl delete service telegraf-config-manager-access -n default
   ```

2. **Why the namespace change?**
   - Better resource isolation and organization
   - Prevents NodePort conflicts when multiple services use the same ports
   - Easier to manage application lifecycle and permissions
   - Follows Kubernetes best practices for multi-tenant environments

3. **Service Port Considerations:**
   - NodePort 30080 is now allocated exclusively to this namespace
   - No conflicts with other services in the cluster
   - Consistent access regardless of cluster state changes

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
kubectl apply -f k8s/pod.yaml -n telegraf-config-mgr
```

**Access the pod:**
```bash
kubectl port-forward pod/telegraf-config-manager-pod -n telegraf-config-mgr 5000:5000
```
Then access at: http://localhost:5000

#### Option B: Deployment with Service (Recommended for Production)

```bash
kubectl apply -f k8s/deployment.yaml -n telegraf-config-mgr
kubectl apply -f k8s/service.yaml -n telegraf-config-mgr
```

**Access via NodePort:**
```bash
kubectl get service telegraf-config-manager-service -n telegraf-config-mgr
```
The service exposes port 30080 on the node. Access at: http://<NODE_IP>:30080

#### Option C: Deployment with LoadBalancer

```bash
kubectl apply -f k8s/deployment.yaml -n telegraf-config-mgr
kubectl apply -f k8s/loadbalancer-service.yaml -n telegraf-config-mgr
```

**Access via LoadBalancer:**
```bash
kubectl get service telegraf-config-manager-access -n telegraf-config-mgr
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
kubectl port-forward deployment/telegraf-config-manager -n telegraf-config-mgr 5000:5000
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
kubectl delete -f k8s/pod.yaml -n telegraf-config-mgr
kubectl delete -f k8s/service.yaml -n telegraf-config-mgr
kubectl delete -f k8s/deployment.yaml -n telegraf-config-mgr

# Or remove everything at once
kubectl delete all -l app=telegraf-config-manager -n telegraf-config-mgr
```

---

## Troubleshooting

### Issue: Pod is not starting

Check pod status and events:
```bash
kubectl describe pod -l app=telegraf-config-manager -n telegraf-config-mgr
```

Common fixes:
- Ensure image is loaded in the cluster
- Check `imagePullPolicy: Never` is set for local images
- Verify pod tolerations if node has resource constraints

### Issue: Cannot access the application

1. Check pod is running:
   ```bash
   kubectl get pods -l app=telegraf-config-manager -n telegraf-config-mgr
   ```

2. Check service endpoints:
   ```bash
   kubectl get endpoints telegraf-config-manager-service -n telegraf-config-mgr
   ```

3. Test connectivity from inside cluster:
   ```bash
   kubectl run curl-test --image=curlimages/curl -i --rm --restart=Never -n telegraf-config-mgr -- curl http://telegraf-config-manager-service:80
   ```

4. Check port-forward if using local access:
   ```bash
   kubectl port-forward deployment/telegraf-config-manager -n telegraf-config-mgr 5000:5000
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
