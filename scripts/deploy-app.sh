#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
k() { kubectl --context "${KUBE_CONTEXT:-tbonk-homework}" "$@"; }
k apply -f k8s/app/00-namespace.yaml -f k8s/app/10-config.yaml -f k8s/app/20-postgres.yaml
k -n tbonk rollout status statefulset/postgres --timeout=300s
# A Job's pod template is immutable. Recreate only the one-off schema command.
k -n tbonk delete job tbonk-init-db --ignore-not-found --wait=true
k apply -f k8s/app/30-init-db.yaml
k -n tbonk wait --for=condition=complete job/tbonk-init-db --timeout=300s
k apply -f k8s/app/40-web.yaml
k -n tbonk rollout status deployment/tbonk --timeout=300s
k -n tbonk get pods,svc,pvc,jobs
