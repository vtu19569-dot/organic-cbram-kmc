.PHONY: test validate run

test:
	. .venv/bin/activate && pytest -q

validate:
	. .venv/bin/activate && python analysis/validate_cbram.py

run:
	. .venv/bin/activate && python main.py
