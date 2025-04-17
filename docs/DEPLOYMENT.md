# CognisGraph Deployment Guide

## Prerequisites

Before deploying CognisGraph, ensure you have the following prerequisites:

1. **Kubernetes Cluster**
   - A running Kubernetes cluster (tested with minikube v1.32.0)
   - kubectl configured to access the cluster
   - Helm 3 installed

2. **Storage**
   - A default StorageClass configured in your cluster
   - For minikube, the `standard` StorageClass is automatically configured

3. **Required Components**
   - cert-manager CRDs (v1.13.3)
   - Ingress controller (nginx-ingress)

## Installation Steps

### 1. Install cert-manager CRDs

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.crds.yaml
```

### 2. Deploy CognisGraph

```bash
# Install the Helm chart
helm install cognisgraph ./helm/cognisgraph --namespace cognisgraph --create-namespace
```

### 3. Verify Installation

Check the status of the deployment:

```bash
# Check pods
kubectl get pods -n cognisgraph

# Check services
kubectl get services -n cognisgraph

# Check ingress
kubectl get ingress -n cognisgraph
```

### 4. Accessing the Application

#### For minikube users:

1. Start the minikube tunnel in a separate terminal:
   ```bash
   minikube tunnel
   ```

2. Get the external IP:
   ```bash
   kubectl get service cognisgraph-ingress-nginx-controller -n cognisgraph
   ```

3. Access the application using the external IP and configured ports (80/443)

## Troubleshooting

### Common Issues

1. **Cert-manager Startup Issues**
   - Ensure cert-manager CRDs are properly installed
   - Check cert-manager pod logs for errors
   ```bash
   kubectl logs -n cognisgraph -l app.kubernetes.io/instance=cognisgraph,app.kubernetes.io/name=cert-manager
   ```

2. **Ingress Controller Issues**
   - Verify the LoadBalancer service is properly configured
   - Check ingress controller logs
   ```bash
   kubectl logs -n cognisgraph -l app.kubernetes.io/instance=cognisgraph,app.kubernetes.io/name=ingress-nginx
   ```

3. **Storage Issues**
   - Verify PVCs are bound
   ```bash
   kubectl get pvc -n cognisgraph
   ```

### Cleanup

To completely remove CognisGraph:

```bash
# Uninstall Helm release
helm uninstall cognisgraph -n cognisgraph

# Delete namespace
kubectl delete namespace cognisgraph

# Remove cluster-wide resources
kubectl delete clusterrole,clusterrolebinding -l app.kubernetes.io/instance=cognisgraph
kubectl delete validatingwebhookconfiguration,mutatingwebhookconfiguration -l app.kubernetes.io/instance=cognisgraph
```

## Monitoring

Monitor the deployment progress:

```bash
# Watch pod status
kubectl get pods -n cognisgraph -w

# Check events
kubectl get events -n cognisgraph --sort-by='.lastTimestamp'
```

## Configuration

The deployment can be customized using Helm values. See `helm/cognisgraph/values.yaml` for available options.

## Support

For additional support:
- Check the [GitHub Issues](https://github.com/your-repo/cognisgraph/issues)
- Join our [Discord Community](https://discord.gg/your-invite)
- Contact the development team at support@cognisgraph.com 