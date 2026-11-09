#!/usr/bin/env bash
set -euo pipefail
k() { kubectl --context "${KUBE_CONTEXT:-tbonk-homework}" -n tbonk "$@"; }
seconds="${1:-180}"
workers="${2:-2}"
[[ "$seconds" =~ ^[0-9]+$ && "$workers" =~ ^[0-9]+$ ]] || exit 2
(( seconds >= 1 && seconds <= 3600 && workers >= 1 && workers <= 8 )) || exit 2
image="$(k get deployment tbonk -o jsonpath='{.spec.template.spec.containers[0].image}')"
job="tbonk-load-$(date +%s)-$RANDOM"
k create -f - <<YAML
apiVersion: batch/v1
kind: Job
metadata:
  name: $job
spec:
  ttlSecondsAfterFinished: 600
  backoffLimit: 0
  activeDeadlineSeconds: $((seconds + 90))
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: load
          image: $image
          imagePullPolicy: Never
          command: [python, scripts/load.py, --url, "http://tbonk.tbonk.svc.cluster.local:8000", --seconds, "$seconds", --workers, "$workers"]
          resources:
            requests: {cpu: 50m, memory: 32Mi}
            limits: {cpu: 250m, memory: 128Mi}
YAML
k wait --for=condition=complete "job/$job" --timeout="$((seconds + 120))s"
k logs "job/$job"
