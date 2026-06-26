.PHONY: install dev test lint format mypy clean run docker-up docker-down

install:
	pip install -r requirements.txt

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src --cov-report=term

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

lint:
	flake8 src/ tests/

format:
	black src/ tests/

mypy:
	mypy src/

check: lint format-check mypy

format-check:
	black --check src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/
	rm -rf *.egg-info dist/ build/

run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker-compose -f docker/docker-compose.yml up -d

docker-down:
	docker-compose -f docker/docker-compose.yml down

docker-build:
	docker-compose -f docker/docker-compose.yml build
