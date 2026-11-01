# StockGod MLOps

This folder is a copy of StockGod with the release path filled in. The product is the same: a Streamlit dashboard and a FastAPI service that score news and social posts for an NSE or BSE name. The MLOps layer is how that product is built, deployed, and watched.

## What you are presenting

StockGod is a sentiment product. A person types a company. The API collects posts, FinBERT scores them, and Streamlit shows the sentiment, the themes, the named entities, and the live price.

Around that product:

| Piece | Where it lives | What it does |
| --- | --- | --- |
| Git | this repository | The version you can point at. The original app stays in `Stockgod`. |
| GitHub Actions | `.github/workflows/ci.yml` | On every push: compile the Python, check the wiring, dry-run the Kubernetes manifests, validate Terraform, build the Streamlit image and hit its health check, then build the API image. |
| Docker | `frontend/Dockerfile`, `backend/Dockerfile`, `docker-compose.yml` | Images for Streamlit and the API. Compose also starts Postgres, MongoDB, Redis, Kafka, the Spark processor, Prometheus, and Grafana. That Compose file was already in StockGod. |
| Kubernetes | `k8s/` | Runs Streamlit, the API, Postgres, MongoDB, Redis, Prometheus, and Grafana. Streamlit is a NodePort on 30501. Grafana is a NodePort on 30300. |
| Terraform | `infra/terraform/` | Applies every file in `k8s/` through the kubectl provider. Terraform is the infrastructure step. The YAML is what the cluster receives. |
| Prometheus | `monitoring/prometheus.yml` and `GET /metrics` | Scrapes the API every 15 seconds. The API counts `http_requests_total` by method and path. |
| Grafana | `monitoring/grafana/` | Opens on port 3000 in Compose. Login `admin` / `admin`. The dashboard is "StockGod API". |
| Streamlit | `frontend/app.py` | Served on port 8501. Inside Docker it calls the API at `http://api:8000`. |

## How a request moves

1. Streamlit calls the API.
2. The API reads Postgres, MongoDB, and Redis. Scoring uses FinBERT. The streaming path, when Compose is up, also uses Kafka and the Spark processor.
3. Every API response except `/metrics` increments `http_requests_total`.
4. Prometheus scrapes `http://api:8000/metrics`.
5. Grafana graphs that series.

`/health` is the readiness probe. It stays up even if Postgres is still starting, so Kubernetes does not kill the pod during boot. `/metrics` is the Prometheus target. Those are different URLs. Prometheus does not scrape `/health`.

## What was already in StockGod

Dockerfiles, `docker-compose.yml`, a Prometheus config, and a Grafana dashboard were already there. Two things in that setup did not line up, and this copy fixes them:

- Prometheus was scraping `/health`, which returns JSON, not Prometheus text. It now scrapes `/metrics`.
- The dashboard asked for series the API never emitted. It now graphs `http_requests_total` and the API process memory.

Kafka, Spark, and the scrapers stay in Compose. They are the existing streaming path. The Kubernetes manifests are the serving path: dashboard, API, databases, cache, and monitoring.

## Commands

From this folder.

Full product, the way StockGod already ran:

```text
docker compose up --build
```

Then open:

- Streamlit: http://localhost:8501
- API docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (`admin` / `admin`)

Images for Kubernetes, after Docker is running:

```text
docker build -t stockgod-frontend:latest frontend
docker build -t stockgod-api:latest backend
```

Apply the cluster. This needs a local cluster such as Docker Desktop Kubernetes or kind, and the two images above.

```text
kubectl apply -f k8s/
```

Or, the same manifests through Terraform:

```text
cd infra/terraform
terraform init
terraform apply
```

Streamlit on the cluster is NodePort 30501. Grafana is NodePort 30300. On Docker Desktop those are `localhost:30501` and `localhost:30300`.

Local passwords in Compose and the manifests are `admin` / `admin123` for the databases and `admin` / `admin` for Grafana. They are for a laptop demo, not a public server.

## What to say

Use this order. It is about two minutes, then the demo.

"StockGod scores public posts and news for any Indian listed name and shows that against the live price. I kept the application and added the release path around it.

The code is in Git. GitHub Actions compiles it, checks that Prometheus, Grafana, Kubernetes, and Terraform still point at the same ports, dry-runs the manifests, and builds two images. The Streamlit image has to answer `/_stcore/health` before the workflow goes green. The API image is the second build.

Docker Compose is the full stack I use on a laptop: API, Streamlit, Postgres, MongoDB, Redis, Kafka, Spark, Prometheus, and Grafana. Kubernetes is the serving deploy: the same dashboard and API, plus the databases and the monitoring. Terraform applies those manifests, so the cluster is not a pile of one-off kubectl commands.

Prometheus scrapes `/metrics` on the API. The counter is `http_requests_total`. Grafana is the dashboard I open in a review. The health probe is separate, so a scrape and a liveness check are not the same thing."

Then show, in this order: the Streamlit page, `/docs`, the `/metrics` text, Prometheus targets (the API target should be UP), and the Grafana panel moving after you refresh Streamlit a few times.

## What you can defend

- Streamlit and the API are real StockGod code, with Dockerfiles that were already in the project. The Streamlit image pins pyarrow 15 so it stays compatible with NumPy 1.26. I built both images locally. Streamlit answered `/_stcore/health`. The API answered `/health` and `/metrics`.
- The GitHub workflow builds the Streamlit image and curls its health endpoint.
- Terraform validates, and `terraform apply` is the apply step for the YAML in `k8s/`.
- The metric on the dashboard is emitted by the API.

## What you should not claim

- Do not say this is running in a cloud account. Terraform targets whatever cluster is in your kubeconfig.
- Do not say Kafka metrics are on the Grafana board. The board is the API.
- Do not say the Kubernetes deploy includes the Spark processor and the scrapers. Those stay in Docker Compose.
- The database passwords in the repo are demo passwords.
