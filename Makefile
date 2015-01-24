all: run

run:
	@python app.py

dev:
	@gunicorn app:app -b 0.0.0.0:5000

test:
	@python test.py

panic:
	@lsof -i tcp:5000
