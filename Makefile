# Makefile for mFAA development

.PHONY: help install install-dev test lint format clean docker-build docker-run

help:
	@echo "mFAA Development Commands:"
	@echo "  make install       - Install package"
	@echo "  make install-dev   - Install with dev dependencies"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-run    - Run in Docker"

install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

test:
	pytest

test-cov:
	pytest --cov=mfaa --cov-report=html --cov-report=term

lint:
	flake8 mfaa/ tests/
	mypy mfaa/

format:
	black mfaa/ tests/
	isort mfaa/ tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker-compose build

docker-run:
	docker-compose up mfaa-dev

docker-prod:
	docker build -f Dockerfile.prod -t mfaa:prod .
	docker run --privileged -v $(PWD)/output:/output mfaa:prod --help
