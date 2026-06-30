PYTHON ?= /usr/bin/python3
PIP ?= pip3
PROJECT_PYTHONPATH := src$(if $(PYTHONPATH),:$(PYTHONPATH))
RUN_PYTHON = PYTHONPATH=$(PROJECT_PYTHONPATH) $(PYTHON)

.PHONY: setup data features train evaluate active-learning report reproduce-small test clean

setup:
	@if /usr/bin/python3 -m venv .venv >/dev/null 2>&1 && [ -x .venv/bin/python ]; then \
		.venv/bin/pip install --upgrade pip; \
		.venv/bin/pip install -e .; \
	else \
		rm -rf .venv; \
		$(PIP) install --user --break-system-packages -e .; \
	fi

data:
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.select_dataset
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.audit_dataset
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.clean_reactions

features:
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.build_features
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.make_splits

train:
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.train_and_evaluate

evaluate:
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.uncertainty_calibration

active-learning:
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.active_learning_simulation

report:
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.rank_existing_records
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.interpret_models
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.build_final_report
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.final_quality_gate

reproduce-small:
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.select_dataset --fixture
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.audit_dataset --fixture
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.clean_reactions --fixture
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.build_features
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.make_splits
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.train_and_evaluate
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.uncertainty_calibration
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.active_learning_simulation
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.rank_existing_records
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.interpret_models
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.build_final_report
	$(RUN_PYTHON) -m reaction_yield_ml.workflows.final_quality_gate

test:
	$(RUN_PYTHON) -m pytest
	$(RUN_PYTHON) -c "import json, pathlib; p=pathlib.Path('reports/metrics/pytest_status.json'); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps({'status':'PASS'}, indent=2) + '\n')"

clean:
	rm -rf data/processed reports/metrics/*.json reports/figures/*.png reports/*.md .pytest_cache
