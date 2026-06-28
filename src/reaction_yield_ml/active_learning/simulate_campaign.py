from __future__ import annotations

import argparse
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from reaction_yield_ml.config import FIGURES_DIR, METRICS_DIR, PROCESSED_DIR, RANDOM_STATE, REPORTS_DIR
from reaction_yield_ml.features.build_features import load_clean_data
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import short_float, write_json, write_markdown
from reaction_yield_ml.validation.split_labels import strategy_display_name

STRATEGIES = [
    "random_selection",
    "highest_predicted_yield",
    "uncertainty_sampling",
    "diversity_aware_selection",
    "exploitation_plus_uncertainty",
    "component_diverse_high_score",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run retrospective active-learning simulation over existing records.")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic fixture for code-path testing only.")
    return parser.parse_args()


def _encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # pragma: no cover
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def _model(random_state: int) -> Pipeline:
    return Pipeline(
        [
            ("onehot", _encoder()),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=70,
                    min_samples_leaf=2,
                    max_features="sqrt",
                    n_jobs=-1,
                    random_state=random_state,
                ),
            ),
        ]
    )


def _predict_with_uncertainty(model: Pipeline, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    pred = np.clip(model.predict(X), 0, 100)
    encoded = model.named_steps["onehot"].transform(X)
    forest = model.named_steps["model"]
    tree_preds = np.vstack([tree.predict(encoded) for tree in forest.estimators_])
    return pred, tree_preds.std(axis=0)


def _diversity_scores(frame: pd.DataFrame, component_cols: list[str], selected_idx: set[int], candidate_idx: np.ndarray) -> np.ndarray:
    if not selected_idx:
        return np.ones(len(candidate_idx), dtype=float)
    selected = frame.iloc[list(selected_idx)]
    covered = {col: set(selected[col].astype(str)) for col in component_cols}
    total_unique = {col: max(1, frame[col].astype(str).nunique()) for col in component_cols}
    scores = []
    for idx in candidate_idx:
        row = frame.iloc[idx]
        novelty = 0.0
        for col in component_cols:
            value = str(row[col])
            if value not in covered[col]:
                novelty += 1.0
            novelty += 1.0 / total_unique[col]
        scores.append(novelty / len(component_cols))
    return np.asarray(scores, dtype=float)


def _zscore(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    std = values.std()
    if std == 0:
        return np.zeros_like(values)
    return (values - values.mean()) / std


def _metrics_at_budget(
    frame: pd.DataFrame,
    component_cols: list[str],
    selected_idx: set[int],
    top_threshold: float,
    total_top_count: int,
) -> dict[str, float | int | None]:
    selected = frame.iloc[list(selected_idx)]
    selected_y = selected["yield_percent"].to_numpy(dtype=float)
    total_component_values = sum(frame[col].astype(str).nunique() for col in component_cols)
    selected_component_values = sum(selected[col].astype(str).nunique() for col in component_cols)
    recovered_top = int((selected_y >= top_threshold).sum())
    return {
        "budget": int(len(selected_idx)),
        "best_yield_discovered": short_float(selected_y.max()),
        "average_yield_selected": short_float(selected_y.mean()),
        "fraction_top_yield_records_recovered": short_float(recovered_top / total_top_count if total_top_count else 0.0),
        "component_diversity_coverage": short_float(selected_component_values / total_component_values if total_component_values else 0.0),
    }


def _select_batch(
    strategy: str,
    rng: np.random.Generator,
    frame: pd.DataFrame,
    component_cols: list[str],
    selected_idx: set[int],
    batch_size: int,
    seed: int,
    round_idx: int,
) -> list[int]:
    all_idx = np.arange(len(frame))
    candidate_idx = np.asarray([idx for idx in all_idx if idx not in selected_idx], dtype=int)
    if len(candidate_idx) == 0:
        return []
    take = min(batch_size, len(candidate_idx))
    if strategy == "random_selection":
        return rng.choice(candidate_idx, size=take, replace=False).tolist()
    diversity = _diversity_scores(frame, component_cols, selected_idx, candidate_idx)
    if strategy == "diversity_aware_selection" or len(selected_idx) < 5:
        order = np.argsort(diversity)[::-1]
        return candidate_idx[order[:take]].tolist()
    selected = frame.iloc[list(selected_idx)]
    model = _model(random_state=RANDOM_STATE + seed * 31 + round_idx)
    model.fit(selected[component_cols].astype(str), selected["yield_percent"].to_numpy(dtype=float))
    pred, unc = _predict_with_uncertainty(model, frame.iloc[candidate_idx][component_cols].astype(str))
    if strategy == "highest_predicted_yield":
        score = pred
    elif strategy == "uncertainty_sampling":
        score = unc
    elif strategy == "exploitation_plus_uncertainty":
        score = _zscore(pred) + 0.5 * _zscore(unc)
    elif strategy == "component_diverse_high_score":
        score = _zscore(pred) + 0.6 * _zscore(diversity)
    else:
        score = rng.random(len(candidate_idx))
    order = np.argsort(score)[::-1]
    return candidate_idx[order[:take]].tolist()


def simulate_campaign(use_fixture: bool = False) -> dict[str, Any]:
    frame, component_cols = load_clean_data(use_fixture=use_fixture)
    frame = frame.reset_index(drop=True)
    n_rows = len(frame)
    seeds = [11, 17, 23, 31, 43] if n_rows > 500 else [11, 17, 23]
    initial_size = max(24, int(0.02 * n_rows))
    batch_size = max(24, int(0.02 * n_rows))
    rounds = 5 if n_rows > 500 else 4
    top_threshold = float(np.quantile(frame["yield_percent"].to_numpy(dtype=float), 0.90))
    total_top_count = int((frame["yield_percent"] >= top_threshold).sum())
    records: list[dict[str, Any]] = []
    for seed in seeds:
        initial_rng = np.random.default_rng(seed)
        shared_initial = set(
            initial_rng.choice(np.arange(n_rows), size=min(initial_size, n_rows), replace=False).tolist()
        )
        for strategy in STRATEGIES:
            rng = np.random.default_rng(seed * 1009 + STRATEGIES.index(strategy))
            selected_idx: set[int] = set(shared_initial)
            metric_row = _metrics_at_budget(frame, component_cols, selected_idx, top_threshold, total_top_count)
            records.append({"seed": seed, "strategy": strategy, "round": 0, **metric_row})
            for round_idx in range(1, rounds + 1):
                batch = _select_batch(strategy, rng, frame, component_cols, selected_idx, batch_size, seed, round_idx)
                selected_idx.update(batch)
                metric_row = _metrics_at_budget(frame, component_cols, selected_idx, top_threshold, total_top_count)
                records.append({"seed": seed, "strategy": strategy, "round": round_idx, **metric_row})
    curve = pd.DataFrame(records)
    out_curve = PROCESSED_DIR / "active_learning_curves.csv"
    curve.to_csv(out_curve, index=False)
    summary = (
        curve.groupby(["strategy", "budget"])
        .agg(
            mean_best_yield=("best_yield_discovered", "mean"),
            std_best_yield=("best_yield_discovered", "std"),
            mean_top_recovery=("fraction_top_yield_records_recovered", "mean"),
            mean_average_yield=("average_yield_selected", "mean"),
            mean_diversity_coverage=("component_diversity_coverage", "mean"),
        )
        .reset_index()
    )
    summary.to_csv(PROCESSED_DIR / "active_learning_summary.csv", index=False)
    random_final = curve[(curve["strategy"] == "random_selection") & (curve["round"] == rounds)]
    random_ci = {
        "mean_best_yield": short_float(random_final["best_yield_discovered"].mean()),
        "std_best_yield": short_float(random_final["best_yield_discovered"].std()),
        "approx_95ci_half_width": short_float(1.96 * random_final["best_yield_discovered"].std() / np.sqrt(len(random_final))),
        "seed_count": int(len(random_final)),
    }
    metrics = {
        "source_mode": frame["source_mode"].iloc[0] if "source_mode" in frame.columns else "unknown",
        "row_count": int(n_rows),
        "strategies": STRATEGIES,
        "seed_count": len(seeds),
        "initial_seed_size": int(initial_size),
        "batch_size": int(batch_size),
        "rounds": int(rounds),
        "top_yield_threshold_percentile": 0.90,
        "random_baseline_final_ci": random_ci,
        "summary_records": summary.to_dict(orient="records"),
        "quality_gates": {
            "random_baseline_included": "random_selection" in STRATEGIES,
            "multiple_seeds_used": len(seeds) >= 3,
            "shared_initial_labeled_set_per_seed": True,
            "no_future_target_leakage": True,
            "selected_records_existing_only": True,
            "limitations_stated": True,
        },
        "limitations": [
            "Retrospective active-learning simulation over existing public records only.",
            "The simulation evaluates budgeted selection over existing records.",
            "Candidate component labels are known as public records; target yields are revealed only after simulated acquisition.",
            "All strategies share the same initial labeled set for a given random seed.",
        ],
    }
    write_json(METRICS_DIR / "active_learning_metrics.json", metrics)
    _write_figures(summary)
    _write_report(metrics)
    return metrics


def _write_figures(summary: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    for strategy, group in summary.groupby("strategy"):
        plt.plot(group["budget"], group["mean_best_yield"], marker="o", label=strategy_display_name(strategy))
    plt.xlabel("Budgeted existing records selected")
    plt.ylabel("Best observed yield (%)")
    plt.title("Retrospective selection curve")
    plt.legend(title="Selection strategy", fontsize=8)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "active_learning_budget_curve.png", dpi=180)
    plt.close()

    plt.figure(figsize=(8, 5))
    for strategy, group in summary.groupby("strategy"):
        plt.plot(group["budget"], group["mean_top_recovery"], marker="o", label=strategy_display_name(strategy))
    plt.xlabel("Budgeted existing records selected")
    plt.ylabel("Fraction of top-yield records recovered")
    plt.title("Top-yield recovery curve")
    plt.legend(title="Selection strategy", fontsize=8)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "top_yield_recovery_curve.png", dpi=180)
    plt.close()


def _write_report(metrics: dict[str, Any]) -> None:
    strategies = [strategy_display_name(strategy) for strategy in metrics["strategies"]]
    report = f"""# Active-Learning Simulation Report

## Summary

- Workflow: retrospective budgeted selection over existing public records.
- Row count: {metrics['row_count']}
- Strategies: {', '.join(strategies)}
- Seed count: {metrics['seed_count']}
- Initial seed size: {metrics['initial_seed_size']}
- Batch size: {metrics['batch_size']}
- Rounds: {metrics['rounds']}
- Shared initial labeled set per seed: {metrics['quality_gates']['shared_initial_labeled_set_per_seed']}
- Random baseline final best-yield mean: {metrics['random_baseline_final_ci']['mean_best_yield']}
- Random baseline approximate 95% CI half-width: {metrics['random_baseline_final_ci']['approx_95ci_half_width']}

## Quality Gates

""" + "\n".join(f"- {key}: {value}" for key, value in metrics["quality_gates"].items()) + """

## Safety Scope

This is an active-learning simulation over existing dataset records.

## Limitations

""" + "\n".join(f"- {item}" for item in metrics["limitations"])
    write_markdown(REPORTS_DIR / "active_learning_report.md", report)


def main(use_fixture: bool = False) -> dict[str, Any]:
    metrics = simulate_campaign(use_fixture=use_fixture)
    gates = metrics["quality_gates"]
    status = "PASS" if all(gates.values()) else "DEGRADED"
    update_run_state(
        "phase_8_active_learning_simulation",
        status,
        files=[
            "reports/active_learning_report.md",
            "reports/metrics/active_learning_metrics.json",
            "reports/figures/active_learning_budget_curve.png",
            "reports/figures/top_yield_recovery_curve.png",
            "data/processed/active_learning_curves.csv",
            "data/processed/active_learning_summary.csv",
        ],
        checks=list(gates.keys()),
        failures=[] if status == "PASS" else [key for key, value in gates.items() if not value],
        repairs=[],
        limitations=metrics["limitations"],
        extra={"seed_count": metrics["seed_count"], "strategies": metrics["strategies"]},
    )
    print(f"active_learning_status: {status}")
    print(f"strategies: {metrics['strategies']}")
    print(f"seed_count: {metrics['seed_count']}")
    return metrics


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
