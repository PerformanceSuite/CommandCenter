.PHONY: help start stop restart logs clean build test check-ports

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Command Center - Available commands:'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ''

check-ports: ## Check if required ports are available
	@./scripts/check-ports.sh

start: check-ports ## Start all services (with port check)
	@echo "Starting Command Center..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from template..."; \
		cp .env.template .env; \
		echo "⚠️  Please edit .env with your configuration"; \
		exit 1; \
	fi
	docker-compose up -d
	@echo "✅ Command Center started!"
	@echo ""
	@echo "Access:"
	@echo "  Frontend:  http://localhost:$$(grep FRONTEND_PORT .env | cut -d '=' -f 2 || echo 3000)"
	@echo "  Backend:   http://localhost:$$(grep BACKEND_PORT .env | cut -d '=' -f 2 || echo 8000)"
	@echo "  API Docs:  http://localhost:$$(grep BACKEND_PORT .env | cut -d '=' -f 2 || echo 8000)/docs"

start-traefik: ## Start with Traefik (zero port conflicts)
	@if [ ! -f docker-compose.traefik.yml ]; then \
		echo "❌ docker-compose.traefik.yml not found"; \
		echo "See docs/TRAEFIK_SETUP.md for setup instructions"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.traefik.yml up -d
	@echo "✅ Command Center started with Traefik!"
	@echo ""
	@echo "Access:"
	@echo "  Frontend:  http://commandcenter.localhost"
	@echo "  Backend:   http://api.commandcenter.localhost"
	@echo "  API Docs:  http://api.commandcenter.localhost/docs"

stop: ## Stop all services
	docker-compose down
	@echo "✅ Command Center stopped"

restart: stop start ## Restart all services

logs: ## Show logs (follow mode)
	docker-compose logs -f

logs-backend: ## Show backend logs only
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs only
	docker-compose logs -f frontend

logs-db: ## Show database logs only
	docker-compose logs -f postgres

build: ## Rebuild all containers
	docker-compose build

rebuild: ## Rebuild and restart all containers
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "✅ Rebuilt and restarted"

clean: ## Stop and remove all containers, volumes, and networks
	@echo "⚠️  This will delete all data. Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	docker-compose down -v --remove-orphans
	@echo "✅ Cleaned up"

ps: ## Show running containers
	docker-compose ps

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U commandcenter -d commandcenter

db-backup: ## Backup database to file
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U commandcenter commandcenter > backups/backup-$$(date +%Y%m%d-%H%M%S).sql
	@echo "✅ Database backed up to backups/"

db-restore: ## Restore database from latest backup
	@if [ ! -d backups ] || [ -z "$$(ls -A backups)" ]; then \
		echo "❌ No backups found in backups/"; \
		exit 1; \
	fi
	@LATEST=$$(ls -t backups/*.sql | head -1); \
	echo "Restoring from $$LATEST..."; \
	docker-compose exec -T postgres psql -U commandcenter commandcenter < $$LATEST
	@echo "✅ Database restored"

migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head
	@echo "✅ Migrations applied"

migrate-create: ## Create a new migration (provide MESSAGE variable)
	@if [ -z "$(MESSAGE)" ]; then \
		echo "Usage: make migrate-create MESSAGE='description'"; \
		exit 1; \
	fi
	docker-compose exec backend alembic revision --autogenerate -m "$(MESSAGE)"
	@echo "✅ Migration created"

test: ## Run all tests
	@echo "Running backend tests..."
	docker-compose exec backend pytest
	@echo "Running frontend tests..."
	docker-compose exec frontend npm test

test-backend: ## Run backend tests only
	docker-compose exec backend pytest

test-frontend: ## Run frontend tests only
	docker-compose exec frontend npm test

test-e2e: ## Run E2E tests with Playwright
	@echo "Running E2E tests..."
	@if [ ! -d e2e/node_modules ]; then \
		echo "Installing E2E dependencies..."; \
		cd e2e && npm install && npx playwright install --with-deps; \
	fi
	cd e2e && npm test

test-e2e-ui: ## Run E2E tests in UI mode
	@if [ ! -d e2e/node_modules ]; then \
		echo "Installing E2E dependencies..."; \
		cd e2e && npm install && npx playwright install --with-deps; \
	fi
	cd e2e && npm run test:ui

test-e2e-headed: ## Run E2E tests in headed mode (visible browser)
	cd e2e && npm run test:headed

test-e2e-debug: ## Run E2E tests in debug mode
	cd e2e && npm run test:debug

test-all: test test-e2e ## Run all tests (unit, integration, E2E)

lint: ## Run linters
	@echo "Linting backend..."
	docker-compose exec backend black --check app/
	docker-compose exec backend flake8 app/
	@echo "Linting frontend..."
	docker-compose exec frontend npm run lint

format: ## Format code
	@echo "Formatting backend..."
	docker-compose exec backend black app/
	@echo "Formatting frontend..."
	docker-compose exec frontend npm run format

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -sf http://localhost:$$(grep BACKEND_PORT .env | cut -d '=' -f 2 || echo 8000)/health > /dev/null && echo "✅ Backend healthy" || echo "❌ Backend unhealthy"
	@curl -sf http://localhost:$$(grep FRONTEND_PORT .env | cut -d '=' -f 2 || echo 3000) > /dev/null && echo "✅ Frontend healthy" || echo "❌ Frontend unhealthy"
	@docker-compose exec postgres pg_isready -U commandcenter > /dev/null && echo "✅ Database healthy" || echo "❌ Database unhealthy"
	@docker-compose exec redis redis-cli ping > /dev/null && echo "✅ Redis healthy" || echo "❌ Redis unhealthy"

setup: ## Initial setup (install dependencies)
	@if [ ! -f .env ]; then \
		echo "Creating .env from template..."; \
		cp .env.template .env; \
		echo "✅ Created .env - please edit with your configuration"; \
	fi
	@chmod +x scripts/check-ports.sh
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env with your configuration"
	@echo "  2. Run: make start"

dev: ## Start in development mode with live reload
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

prod: ## Start in production mode
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

stats: ## Show container resource usage
	docker stats $$(docker-compose ps -q)

prune: ## Remove unused Docker resources
	docker system prune -f
	@echo "✅ Pruned unused resources"

update: ## Pull latest images and restart
	git pull
	docker-compose pull
	docker-compose up -d --build
	@echo "✅ Updated to latest version"

.env: ## Create .env from template if it doesn't exist
	cp .env.template .env
	@echo "✅ Created .env - please edit with your configuration"
