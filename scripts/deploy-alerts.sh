#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
k() { kubectl --context "${KUBE_CONTEXT:-tbonk-homework}" "$@"; }
k -n monitoring create configmap tbonk-alert-rules --from-file=rules.yaml=k8s/alerts/rules.yaml --dry-run=client -o yaml | k apply -f -
k -n monitoring create configmap tbonk-alertmanager-config --from-file=alertmanager.yaml=k8s/alerts/alertmanager.yaml --dry-run=client -o yaml | k apply -f -
k apply -f k8s/alerts/deployments.yaml
for deployment in vmalert alertmanager alert-inbox; do
  k -n monitoring rollout restart deployment/"$deployment"
  k -n monitoring rollout status deployment/"$deployment" --timeout=300s
done
