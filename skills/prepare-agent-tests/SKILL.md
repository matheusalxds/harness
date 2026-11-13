---
name: prepare-agent-tests
description: Prepares the local Tilt environment for agent-service testing — verifies sandbox mode (OCROLUS_ENV) and wipes the agent-service and loan-application-service local databases. Destructive; only for the local cluster.
disable-model-invocation: true
---

# Prepare Agent Tests

Prepare the local Tilt environment for agent-service testing. Ensures sandbox mode is active, then clears databases.

## Steps

### 0. Verify kubectl points at the LOCAL cluster (mandatory)

```bash
kubectl config current-context
```

The context must be a known local cluster (`docker-desktop`, `orbstack`, `minikube`, `kind-*`, `rancher-desktop`). If it is anything else — or you are not 100% sure it is local — **STOP immediately and ask the user**. Steps 4–5 run `deleteMany({})` on entire databases; against a staging/production context this destroys real data. Never proceed on an ambiguous context.

### 1. Verify Tilt pods are running

```bash
kubectl get pods | grep -E 'agent-app|document-data-extractor|mongo|loan-application'
```

All pods must be `Running`. If any are missing or in `Error`, warn the user.

### 2. Ensure OCROLUS_ENV is `only-sandbox`

Find the data-extractor pod dynamically:

```bash
kubectl get pods -o name | grep document-data-extractor
```

Check the env var:

```bash
kubectl exec <data-extractor-pod> -c document-data-extractor-service-app -- printenv OCROLUS_ENV
```

**If the value is `only-sandbox`**: proceed to step 3.

**If the value is missing or different**: fix it automatically by editing the deployment patch file at `k8s/overlays/local/services/document-data-extractor-service/deployment-patch.yaml`. Add this env var to the container's env list:

```yaml
            - name: OCROLUS_ENV
              value: "only-sandbox"
```

Place it after the `LOGGER_BLACKLIST` entry. After editing, Tilt should detect the change and recreate the pod automatically. Wait a few seconds and verify the new pod has the correct env var.

### 3. Find the mongo pod

The mongo pod name changes on restarts. Find it dynamically:

```bash
kubectl get pods -o name | grep mongo
```

Strip the `pod/` prefix for subsequent commands.

### 4. Clear agent-service database

```bash
kubectl exec <mongo-pod> -- mongosh --quiet --eval "use('agent-service'); db.getCollectionNames().forEach(c => { const r = db.getCollection(c).deleteMany({}); print(c + ': ' + r.deletedCount + ' deleted'); })"
```

### 5. Clear loan-application-service database

```bash
kubectl exec <mongo-pod> -- mongosh --quiet --eval "use('loan-application-service'); db.getCollectionNames().forEach(c => { const r = db.getCollection(c).deleteMany({}); print(c + ': ' + r.deletedCount + ' deleted'); })"
```

### 6. Report summary

Print a concise summary:
- kubectl context used (confirming it was local)
- OCROLUS_ENV status (was it already correct or was it fixed?)
- Documents deleted per database
- "Environment ready for agent testing"
