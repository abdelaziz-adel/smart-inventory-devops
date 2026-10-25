# What goes into GitHub

Commit the **files themselves**, not screenshots or a link to a ZIP:

```text
smart-inventory-devops/
├── README.md
├── .gitignore
├── .dockerignore
├── .env.example
├── docker-compose.yml
├── Jenkinsfile
├── backend/
│   ├── app/{__init__.py,database.py,main.py}
│   ├── tests/test_inventory.py
│   ├── requirements.txt
│   └── Dockerfile
├── alerts/{main.py,requirements.txt,Dockerfile}
├── frontend/{index.html,style.css,app.js,Dockerfile}
├── nginx/default.conf.template
├── kubernetes/{kustomization.yaml,namespace.yaml,postgres.yaml,backend.yaml,alerts.yaml,frontend.yaml}
├── monitoring/{values.yaml,service-monitors.yaml,install.sh}
├── terraform/{main.tf,variables.tf,versions.tf,outputs.tf,terraform.tfvars.example}
├── ansible/{playbook.yml,requirements.yml,inventory.ini.example}
└── docs/{ARCHITECTURE.md,FILES.md,SETUP.md}
```

Never commit `.env`, `.pem`, real `terraform.tfvars`, state files, kubeconfigs or credentials.
