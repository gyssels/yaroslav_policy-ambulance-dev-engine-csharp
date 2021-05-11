SHELL := /bin/bash

CURDIR = $(shell pwd)

VENV = $(CURDIR)/.venv

json-schema-to-class-bin = $(VENV)/bin/json-schema-to-class
pytest-bin = $(VENV)/bin/pytest

.DEFAULT_GOAL := test

.ONESHELL:

.PHONY: clean python-requirements update-schema-pythonBeans

clean:
	@rm -Rf output

$(VENV):
	python3 -m venv $(VENV)

$(json-schema-to-class-bin): $(VENV)
	source $(VENV)/bin/activate
	pip install json-schema-to-class

$(pytest-bin): $(VENV)
	source $(VENV)/bin/activate
	pip install pytest

python-requirements: $(VENV)
	source $(VENV)/bin/activate
	pip install -r requirements.txt
	pip install -r test-requirements.txt

pytest-mypy = $(VENV)/lib/python3.8/site-packages/pytest_mypy.py

${pytest-mypy}: $(VENV)
	source $(VENV)/bin/activate
	pip install -r requirements.txt
	pip install -r test-requirements.txt

test: ${pytest-mypy}
	source $(VENV)/bin/activate
	py.test --mypy engine
