# Setup and deployment (demo)

## 1. Run locally (start here)
Prerequisites: Git, Docker Engine and Docker Compose v2.

```bash
cp .env.example .env
# Edit .env and set a NEW local POSTGRES_PASSWORD (alphanumeric recommended)
docker compose up --build -d
```
Open http://localhost:8080. Add a product with quantity 2 and minimum 5; the dashboard should show a low-stock alert. Change quantity to 10; the alert should disappear.

Backend API reference (if needed):
```bash
docker compose exec backend python -m pytest -q
# API endpoints are inside Docker: GET /products, GET /products/low-stock,
# POST /products, PUT /products/{id}, DELETE /products/{id}.
```
For local test without Compose, install dependencies from `backend/requirements.txt` then `cd backend && pytest -q` (uses SQLite by default). You can run `docker compose down` to stop the app; **avoid** `down -v` if you want to keep data.

## 2. Provision AWS (member 5)
Prerequisites: AWS CLI credentials, Terraform, Ansible, AWS key pair in chosen region, enough EC2 quota. **AWS services cost money**; `t3.large`, EBS and S3 are not a free deployment. Apply/destroy only with the team's permission.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit region, existing key_name, unique bucket name, your exact public IP/32
terraform init
terraform plan
terraform apply
terraform output
cd ..
```
The VPC 10.20.0.0/16 is deliberately different from K3s's default pod CIDR 10.42.0.0/16. Terraform provisions private S3 storage, but the app does not yet write to it.

## 3. Configure server (member 5)
```bash
ansible-galaxy collection install -r ansible/requirements.yml
cp ansible/inventory.ini.example ansible/inventory.ini
# Edit inventory with actual EC2 IP, username, PEM path
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```
`ansible/inventory.ini` is local-only; do not push private host details or key files. Verify `sudo k3s kubectl get nodes` on server.

## 4. Publish Docker images (member 6)
Set up Jenkins with Docker, Compose, Git, Jenkins Pipeline + Credentials plugins and access to GHCR. Add Jenkins credential IDs:
- `ghcr-creds`: GitHub username + access token with package write access.
- `ec2-ssh`: SSH username/key for EC2.
- Set verified SSH `known_hosts` on Jenkins before connecting. Never disable host-key checking.

Create a Jenkins Pipeline using this repository's `Jenkinsfile` and configure a GitHub webhook (or Jenkins SCM polling) to run the pipeline on commits to `main`. Jenkins builds/tests and pushes:
`ghcr.io/abdelaziz-adel/smart-inventory-{backend,alerts,frontend}:latest`.
Set the GHCR package images **Public** for this student demo, or configure a Kubernetes `imagePullSecret` if packages are private.
The Jenkins Deploy stage assumes **you already created the Kubernetes resources once**. It performs rollout restarts, not the initial installation.

## 5. Deploy Kubernetes (members 3/4/5)
On the EC2 server, clone this repo after the images have been pushed, then:

```bash
cd smart-inventory-devops
sudo k3s kubectl apply -f kubernetes/namespace.yaml
# Use a password containing only URL-safe characters for this simple demo:
read -rs POSTGRES_PASSWORD; echo
sudo k3s kubectl -n inventory create secret generic inventory-secrets \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  --from-literal=DATABASE_URL="postgresql+psycopg://inventory:${POSTGRES_PASSWORD}@postgres:5432/inventory"
unset POSTGRES_PASSWORD
sudo k3s kubectl apply -k kubernetes/
sudo k3s kubectl -n inventory get pods
```
The Ansible playbook copies the admin kubeconfig into the EC2 ubuntu user’s `~/.kube/config` with `0600` permissions; it must never be committed or shared. The dashboard is `http://EC2_PUBLIC_IP:30080`, subject to security-group rules.

## 6. Monitoring (member 4)
On EC2, after K3s and Helm are available, and with a working `kubectl` in PATH:
```bash
bash monitoring/install.sh
```
Install via the official community Helm chart. The chart includes Prometheus, Grafana, node-exporter and Kubernetes metrics components. The included ServiceMonitors add FastAPI `/metrics` endpoints. Allow Grafana port 30300 only from your admin IP. Run this as the `ubuntu` user on EC2 after Ansible so Helm and kubectl can read `~/.kube/config`; don't commit the kubeconfig.

Prometheus targets: API and Alerts metrics plus node/Kubernetes/container metrics from kube-prometheus-stack; some K3s control-plane scrapes are disabled since they do not expose standard kubeadm endpoints. Grafana example query: `inventory_operations_total`.

## 7. End-to-end integration test
- Add product from dashboard -> appears in PostgreSQL (through API).
- Quantity below min -> low-stock warning; edit quantity -> warning disappears.
- Run backend tests with `pytest`.
- Check `sudo k3s kubectl -n inventory get pods` and app NodePort 30080.
- Run Jenkins, verify image publication and rolling restart.
- Verify metrics with Grafana, check dashboard and node/exporter targets.

## Team sequence
Day 1: Member 1 defines product fields/endpoints; Members 2/3 build UI and alerts against that contract; Members 4/5/6 prepare their configs.
Day 2: All 3 app components merge; Docker Compose works locally. Member 4 starts K3s tests.
Day 3+: Member 5 provisions EC2 and runs Ansible; Member 4 deploys K3s and monitoring; Member 6 configures Jenkins and final delivery. Integrate via pull requests.

## Cleanup
To avoid unexpected EC2 charges, when demo is over: `cd terraform && terraform destroy` (inspect affected resources before approving). Make backups first: Kubernetes PVC and EC2 volume will be removed, and S3 bucket destruction may fail if nonempty.
