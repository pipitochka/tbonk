#!/usr/bin/env bash
set -euo pipefail
k() { kubectl --context "${KUBE_CONTEXT:-tbonk-homework}" -n tbonk "$@"; }
delay=0 errors=0 cpu=0 memory=0
case "${1:-}" in
  latency) delay=0.8 ;;
  errors) errors=4 ;;
  memory) memory=128 ;;
  cpu) cpu=0.3 ;;
  off)
    k set env deployment/tbonk DEMO_MODE- DEMO_DELAY_SECONDS- DEMO_ERROR_EVERY- DEMO_CPU_SECONDS- DEMO_MEMORY_MB-
    k rollout status deployment/tbonk --timeout=180s
    exit 0 ;;
  *) echo 'Usage: bash scripts/demo-mode.sh latency|errors|memory|cpu|off' >&2; exit 2 ;;
esac
k set env deployment/tbonk DEMO_MODE=true DEMO_DELAY_SECONDS="$delay" DEMO_ERROR_EVERY="$errors" DEMO_CPU_SECONDS="$cpu" DEMO_MEMORY_MB="$memory"
k rollout status deployment/tbonk --timeout=180s
