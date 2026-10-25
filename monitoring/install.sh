#!/usr/bin/env bash
set -euo pipefail
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring -f monitoring/values.yaml
kubectl apply -f monitoring/service-monitors.yaml
printf '\nGrafana: http://<EC2_PUBLIC_IP>:30300 (restrict access via AWS security group)\n'
printf 'Password: kubectl -n monitoring get secret monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d; echo\n'
