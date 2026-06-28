PYTHON ?= /usr/bin/python3
PIP ?= pip3

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
	$(PYTHON) scripts/00_select_dataset.py
	$(PYTHON) scripts/01_audit_dataset.py
	$(PYTHON) scripts/02_clean_reactions.py

features:
	$(PYTHON) scripts/03_build_features.py
	$(PYTHON) scripts/04_make_splits.py

train:
	$(PYTHON) scripts/05_train_and_evaluate.py

evaluate:
	$(PYTHON) scripts/06_uncertainty_calibration.py

active-learning:
	$(PYTHON) scripts/07_active_learning_simulation.py

report:
	$(PYTHON) scripts/08_rank_existing_records.py
	$(PYTHON) scripts/09_interpret_models.py
	$(PYTHON) scripts/10_build_final_report.py
	$(PYTHON) scripts/11_final_quality_gate.py

reproduce-small:
	$(PYTHON) scripts/00_select_dataset.py --fixture
	$(PYTHON) scripts/01_audit_dataset.py --fixture
	$(PYTHON) scripts/02_clean_reactions.py --fixture
	$(PYTHON) scripts/03_build_features.py
	$(PYTHON) scripts/04_make_splits.py
	$(PYTHON) scripts/05_train_and_evaluate.py
	$(PYTHON) scripts/06_uncertainty_calibration.py
	$(PYTHON) scripts/07_active_learning_simulation.py
	$(PYTHON) scripts/08_rank_existing_records.py
	$(PYTHON) scripts/09_interpret_models.py
	$(PYTHON) scripts/10_build_final_report.py
	$(PYTHON) scripts/11_final_quality_gate.py

test:
	$(PYTHON) -m pytest
	$(PYTHON) -c "import json, pathlib; p=pathlib.Path('reports/metrics/pytest_status.json'); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps({'status':'PASS'}, indent=2) + '\n')"

clean:
	rm -rf data/processed reports/metrics/*.json reports/figures/*.png reports/*.md .pytest_cache
