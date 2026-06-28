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
	$(RUN_PYTHON) scripts/00_select_dataset.py
	$(RUN_PYTHON) scripts/01_audit_dataset.py
	$(RUN_PYTHON) scripts/02_clean_reactions.py

features:
	$(RUN_PYTHON) scripts/03_build_features.py
	$(RUN_PYTHON) scripts/04_make_splits.py

train:
	$(RUN_PYTHON) scripts/05_train_and_evaluate.py

evaluate:
	$(RUN_PYTHON) scripts/06_uncertainty_calibration.py

active-learning:
	$(RUN_PYTHON) scripts/07_active_learning_simulation.py

report:
	$(RUN_PYTHON) scripts/08_rank_existing_records.py
	$(RUN_PYTHON) scripts/09_interpret_models.py
	$(RUN_PYTHON) scripts/10_build_final_report.py
	$(RUN_PYTHON) scripts/11_final_quality_gate.py

reproduce-small:
	$(RUN_PYTHON) scripts/00_select_dataset.py --fixture
	$(RUN_PYTHON) scripts/01_audit_dataset.py --fixture
	$(RUN_PYTHON) scripts/02_clean_reactions.py --fixture
	$(RUN_PYTHON) scripts/03_build_features.py
	$(RUN_PYTHON) scripts/04_make_splits.py
	$(RUN_PYTHON) scripts/05_train_and_evaluate.py
	$(RUN_PYTHON) scripts/06_uncertainty_calibration.py
	$(RUN_PYTHON) scripts/07_active_learning_simulation.py
	$(RUN_PYTHON) scripts/08_rank_existing_records.py
	$(RUN_PYTHON) scripts/09_interpret_models.py
	$(RUN_PYTHON) scripts/10_build_final_report.py
	$(RUN_PYTHON) scripts/11_final_quality_gate.py

test:
	$(RUN_PYTHON) -m pytest
	$(RUN_PYTHON) -c "import json, pathlib; p=pathlib.Path('reports/metrics/pytest_status.json'); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps({'status':'PASS'}, indent=2) + '\n')"

clean:
	rm -rf data/processed reports/metrics/*.json reports/figures/*.png reports/*.md .pytest_cache
