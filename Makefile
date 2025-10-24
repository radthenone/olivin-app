.PHONY: help backend celery web ios android full clean

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

web:
	cd frontend && npm run web

ios:
	cd frontend && npm run ios

android:
	cd frontend && npm run android

full:
	docker-compose --profile full up

build:
	docker-compose --profile full up --build

clean:
	docker-compose down -v
	docker system prune -f