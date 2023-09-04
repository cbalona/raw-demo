.PHONY: venv setup

SHELL := /bin/bash

PROJECT_NAME := auto_reserving
PROJECT_DIR := ${CURDIR}
SETUP_DIR := ${PROJECT_DIR}/0-setup

VENV := source .venv/bin/activate
PROJECT_CONFIG := requirements.in

venv: .venv/touchfile

.venv/touchfile: requirements.txt
	$(VENV); pip-sync
	touch .venv/touchfile

requirements.txt: $(PROJECT_CONFIG)
	$(VENV); pip-compile --output-file=requirements.txt --resolver=backtracking $(PROJECT_CONFIG)

setup:
	virtualenv .venv
	$(VENV); pip install pip-tools
	$(VENV); pip install --upgrade pip setuptools wheel

claims:
	mkdir -p $(SETUP_DIR)/data

	mkdir -p $(PROJECT_DIR)/1-automation/data
	mkdir -p $(PROJECT_DIR)/2-data-manipulation/data
	mkdir -p $(PROJECT_DIR)/3-databases/data
	mkdir -p $(PROJECT_DIR)/4-reporting/data
	mkdir -p $(PROJECT_DIR)/5-ml/data

	# docker build -t synthetic-claims $(SETUP_DIR)
	# docker run -v $(SETUP_DIR):/output synthetic-claims

	$(VENV); python $(SETUP_DIR)/simulate.py
	cp $(PROJECT_DIR)/1-automation/data/* $(PROJECT_DIR)/2-data-manipulation/data
	cp $(PROJECT_DIR)/3-databases/data/* $(PROJECT_DIR)/4-reporting/data
	cp $(PROJECT_DIR)/4-reporting/data/* $(PROJECT_DIR)/5-ml/data