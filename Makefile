SHELL:=/bin/bash

help:
	@echo "Available commands:"
	@echo "  backend  - Start backend services (Django + DB + Redis + MinIO)"
	@echo "  celery   - Start Celery services (worker + beat + flower)"
	@echo "  web      - Start web frontend"
	@echo "  full     - Start all services"
	@echo "  clean    - Clean up containers and volumes"

backend:
	docker-compose --profile backend up

celery:
	docker-compose --profile celery up

android:
	cd frontend && npm run start:android

web:
	cd frontend && npm run start:web

full:
	docker-compose --profile full up

build:
	docker-compose --profile full up --build

clean:
	docker-compose down -v
	docker system prune -f

dev:
	@echo "Starting App"
	@docker-compose --profile backend up -d
	@sleep 5
	@cd frontend && npm run start:dev

dev-backend:
	@echo "Starting Backend"
	@docker-compose --profile backend up -d

dev-frontend:
	@echo "Starting Frontend"
	@cd frontend && npm run start:dev

stop-dev:
	@echo "Stopping App"
	@docker-compose --profile backend down
	@pkill -f "npx expo start" || true
