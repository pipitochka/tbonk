#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
k() { kubectl --context "${KUBE_CONTEXT:-tbonk-homework}" "$@"; }
k apply -f k8s/logging/00-namespace.yaml -f k8s/logging/10-victorialogs.yaml
k -n monitoring create configmap vector-config --from-file=vector.yaml=k8s/logging/vector.yaml --dry-run=client -o yaml | k apply -f -
k apply -f k8s/logging/20-vector.yaml
k -n monitoring rollout restart daemonset/vector
k -n monitoring rollout status deployment/victorialogs --timeout=300s
k -n monitoring rollout status daemonset/vector --timeout=300s
