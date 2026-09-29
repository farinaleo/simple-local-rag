# Docker commands for local development, grouped by usage.
# Run `make help` to list the available targets.

COMPOSE := docker compose

.PHONY: help
help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# --- Lifecycle ----------------------------------------------------------------

.PHONY: up
up: ## Build and start the v2 backend stack (postgres + redis + api + worker)
	$(COMPOSE) up -d --build postgres redis api worker


.PHONY: up-all
up-all: ## Build and start every service (v2 backend stack)
	$(COMPOSE) up -d --build

.PHONY: down
down: ## Stop all services, keep the volumes
	$(COMPOSE) down

.PHONY: down-clean
down-clean: ## Stop all services and delete the volumes (data loss)
	$(COMPOSE) down -v

.PHONY: rebuild
rebuild: ## Rebuild the api image from scratch, without cache
	$(COMPOSE) build --no-cache api

.PHONY: ps
ps: ## Show the running services
	$(COMPOSE) ps

.PHONY: logs
logs: ## Follow the api logs (Ctrl+C to exit)
	$(COMPOSE) logs -f api

.PHONY: logs-worker
logs-worker: ## Follow the ingestion worker logs (Ctrl+C to exit)
	$(COMPOSE) logs -f worker

# --- Database -----------------------------------------------------------------

.PHONY: migrate
migrate: ## Apply Django migrations (incl. pgvector extension + HNSW index)
	$(COMPOSE) exec api uv run manage.py migrate

.PHONY: db-check
db-check: ## Inspect the pgvector extension, embedding column and HNSW index
	@echo "--- extensions ---"
	$(COMPOSE) exec postgres psql -U postgres -d rag -c "\dx"
	@echo "--- documents_chunk ---"
	$(COMPOSE) exec postgres psql -U postgres -d rag -c "\d documents_chunk"

.PHONY: db-shell
db-shell: ## Open a psql shell on the rag database
	$(COMPOSE) exec postgres psql -U postgres -d rag

# --- Quality ------------------------------------------------------------------

.PHONY: test
test: ## Run the backend test suite against the compose postgres
	$(COMPOSE) exec api uv run pytest -q

.PHONY: lint
lint: ## Run ruff lint + format checks on the backend
	$(COMPOSE) exec api uvx ruff check .
	$(COMPOSE) exec api uvx ruff format --check .

.PHONY: check
check: ## Django system check
	$(COMPOSE) exec api uv run manage.py check

.PHONY: health
health: ## Curl the api health endpoint
	@curl -s http://localhost:8000/api/health/ && echo

# --- Admin --------------------------------------------------------------------

.PHONY: superuser
superuser: ## Create a Django superuser (interactive)
	$(COMPOSE) exec api uv run manage.py createsuperuser

