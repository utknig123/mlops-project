"""Checks the MLOps files point at the same services the app exposes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_api_exposes_prometheus_metrics():
    main = read("backend/main.py")
    assert '/metrics' in main
    assert "http_requests_total" in main
    assert "prometheus-client" in read("backend/requirements.txt")


def test_prometheus_scrapes_the_api():
    config = read("monitoring/prometheus.yml")
    assert "metrics_path: /metrics" in config
    assert "api:8000" in config


def test_grafana_dashboard_uses_those_metrics():
    dashboard = read("monitoring/grafana/dashboards/dashboard.json")
    assert "http_requests_total" in dashboard
    assert "prometheus" in dashboard


def test_streamlit_is_deployed_in_kubernetes():
    frontend = read("k8s/frontend.yaml")
    assert "kind: Deployment" in frontend
    assert "containerPort: 8501" in frontend
    assert "/_stcore/health" in frontend


def test_terraform_applies_the_manifests():
    terraform = read("infra/terraform/versions.tf")
    assert "kubectl_manifest" in terraform
    assert "k8s/*.yaml" in terraform


def test_azure_terraform_deploys_streamlit():
    azure = read("infra/terraform/azure/main.tf")
    assert "azurerm_container_app" in azure
    assert "target_port      = 8501" in azure
    workflow = read(".github/workflows/ci.yml")
    assert "infra/terraform/azure" in workflow
    assert "mlops-project-streamlit" in workflow


def test_compose_still_runs_streamlit_and_grafana():
    compose = read("docker-compose.yml")
    assert "8501:8501" in compose
    assert "grafana/grafana" in compose
    assert "prom/prometheus" in compose


if __name__ == "__main__":
    test_api_exposes_prometheus_metrics()
    test_prometheus_scrapes_the_api()
    test_grafana_dashboard_uses_those_metrics()
    test_streamlit_is_deployed_in_kubernetes()
    test_terraform_applies_the_manifests()
    test_azure_terraform_deploys_streamlit()
    test_compose_still_runs_streamlit_and_grafana()
    print("mlops layout ok")
