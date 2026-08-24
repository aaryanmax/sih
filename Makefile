.PHONY: up down ingest logs setup clean

# One-click environment setup commands

setup:
	@echo "Setting up local environment..."
	npm install
	cd apps/web && npm install
	@echo "Setup complete. You can now run 'make up'."

up:
	@echo "Starting the full SIH Advanced Video Search stack..."
	docker compose up -d
	@echo "Stack is running. Frontend: http://localhost:3001, API: http://localhost:8000"

down:
	@echo "Stopping the stack..."
	docker compose down

logs:
	@echo "Tailing logs for all services..."
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-vlm:
	docker compose logs -f vlm-engine

ingest:
	@echo "Triggering video ingestion process..."
	@# This would curl the local API to ingest a sample video
	curl -X POST http://localhost:8000/api/v1/ingest/video -F "file=@./data/sample.mp4"

index-batch:
	@echo "Running local batch indexer script..."
	python -m packages.pipeline.batch_indexer

test:
	@echo "Running backend pytest suite..."
	pytest tests/ -v

lint:
	@echo "Running linters..."
	ruff check apps/api packages/ scripts/
	black --check apps/api packages/ scripts/
	cd apps/web && npm run lint

clean:
	@echo "Cleaning up containers and volumes..."
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
