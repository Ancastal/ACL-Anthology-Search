.PHONY: install install-dev test test-unit test-integration lint format clean run-ui run-server

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing
test: test-unit test-integration

test-unit:
	python -m pytest tests/unit/ -v

test-integration:
	python -m pytest tests/integration/ -v

# Code quality
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/

# Cleanup
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run applications
run-backend:
	python -m uvicorn src.acl_search.ui.api_server:app --reload --port 8000

run-frontend:
	cd frontend/react-app && npm run dev

run-server: run-backend

# Start both backend and frontend
run:
	@echo "🚀 Starting ACL Anthology Search..."
	@echo "📡 Starting backend API server on port 8000..."
	@python -m uvicorn src.acl_search.ui.api_server:app --reload --port 8000 &
	@sleep 3
	@echo "🌐 Starting frontend development server on port 3000..."
	@echo "✅ Open http://localhost:3000 in your browser"
	@cd frontend/react-app && npm run dev

# Full development setup (alias for run)
dev: run

# Setup frontend
setup-frontend:
	cd frontend/react-app && npm install

# Stop all services
stop:
	@scripts/stop.sh

# Development
dev-setup: install-dev
	pre-commit install