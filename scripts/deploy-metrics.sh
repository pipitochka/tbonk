#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
context="${KUBE_CONTEXT:-tbonk-homework}"
helm repo add vm https://victoriametrics.github.io/helm-charts/ --force-update
helm repo update vm
helm upgrade --install vm-single vm/victoria-metrics-single \
  --version 0.29.0 --kube-context "$context" --namespace monitoring --create-namespace \
  -f k8s/metrics/values.yaml --wait --timeout 5m
kubectl --context "$context" -n monitoring get pods,svc
