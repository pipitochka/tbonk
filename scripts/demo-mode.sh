#!/usr/bin/env bash
set -euo pipefail
k() { kubectl --context "${KUBE_CONTEXT:-tbonk-homework}" -n tbonk "$@"; }
case "${1:-}" in
  latency) k set env deployment/tbonk DEMO_MODE=true DEMO_DELAY_SECONDS=0.8 DEMO_ERROR_EVERY=0 ;;
  errors) k set env deployment/tbonk DEMO_MODE=true DEMO_DELAY_SECONDS=0 DEMO_ERROR_EVERY=4 ;;
  off) k set env deployment/tbonk DEMO_MODE- DEMO_DELAY_SECONDS- DEMO_ERROR_EVERY- ;;
  *) echo 'Usage: bash scripts/demo-mode.sh latency|errors|off' >&2; exit 2 ;;
esac
k rollout status deployment/tbonk --timeout=180s
