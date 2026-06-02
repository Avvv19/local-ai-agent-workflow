.PHONY: install test eval lint fmt api ui run migrate docker

install:
	pip install -r requirements.txt

test:
	pytest --cov=app --cov-report=term-missing

eval:
	python run_eval.py

lint:
	ruff check app tests

fmt:
	ruff check app tests --fix

migrate:
	alembic upgrade head

api:
	python -m app.main

ui:
	streamlit run ui/streamlit_app.py

docker:
	docker compose up --build
