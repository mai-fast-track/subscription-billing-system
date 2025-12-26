.PHONY: help build dev dev-up dev-down dev-restart dev-logs dev-shell db-shell \
        migrate migrate-create migrate-upgrade migrate-downgrade \
        prod-start prod-stop prod-logs clean

# ===== HELP =====
help:
	@echo "🚀 Billing Core - Available Commands"
	@echo ""
	@echo "📦 BUILD"
	@echo "  make build              - Build Docker images"
	@echo ""
	@echo "🔧 LOCAL DEVELOPMENT"
	@echo "  make dev                - Start development (alias for dev-up)"
	@echo "  make dev-up             - Start all services"
	@echo "  make dev-down           - Stop all services"
	@echo "  make dev-restart        - Restart all services"
	@echo "  make dev-logs           - Show logs (follow)"
	@echo "  make dev-shell          - Open shell in backend container"
	@echo "  make db-shell           - Open PostgreSQL shell"
	@echo "  make clean              - Stop and remove volumes (clean state)"
	@echo ""
	@echo "🗄️  DATABASE MIGRATIONS"
	@echo "  make migrate            - Apply pending migrations"
	@echo "  make migrate-create     - Create new migration (name=description)"
	@echo "  make migrate-upgrade    - Apply all migrations"
	@echo "  make migrate-downgrade  - Rollback one migration"
	@echo ""
	@echo "Examples:"
	@echo "  make migrate-create name='Add user subscription'"
	@echo "  make dev-logs"
	@echo "  make prod-start"

# ===== BUILD =====
build:
	docker-compose -f docker-compose.yml build

# ===== LOCAL DEVELOPMENT =====
dev: dev-up

dev-up:
	docker-compose -f docker-compose.yml up

dev-backend:
	docker-compose -f docker-compose.yml up db backend redis celery_worker celery_beat flower

dev-up-d:
	docker-compose -f docker-compose.yml up -d
	@echo "✓ Services started in background"

dev-down:
	docker-compose -f docker-compose.yml down
	@echo "✓ Services stopped"

dev-restart:
	docker-compose -f docker-compose.yml restart
	@echo "✓ Services restarted"

dev-logs:
	docker-compose -f docker-compose.yml logs -f

dev-shell:
	docker-compose -f docker-compose.yml exec backend /bin/bash

db-shell:
	docker-compose -f docker-compose.yml exec db psql -U billing_user -d billing_db

clean:
	docker-compose -f docker-compose.yml down -v
	@echo "✓ All containers and volumes removed"

# ===== DATABASE MIGRATIONS =====
migrate: migrate-upgrade

migrate-create:
	@if [ -z "$(name)" ]; then \
		echo "❌ Error: Please provide migration name"; \
		echo "Usage: make migrate-create name='Your migration name'"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.yml run --rm backend alembic revision --autogenerate -m "$(name)"
	@echo "✓ Migration created"

migrate-upgrade:
	docker-compose -f docker-compose.yml run --rm api alembic upgrade head
	@echo "✓ Migrations applied"

migrate-downgrade:
	docker-compose -f docker-compose.yml run --rm backend alembic downgrade -1
	@echo "✓ Migration rolled back"

migrate-status:
	docker-compose -f docker-compose.yml run --rm backend alembic current
