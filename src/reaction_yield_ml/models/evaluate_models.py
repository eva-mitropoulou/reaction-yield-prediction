from __future__ import annotations

import math
import warnings
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from reaction_yield_ml.reporting.io import short_float


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float | None]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    if y_true.size == 0:
        return {"mae": None, "rmse": None, "r2": None, "spearman": None, "top_10pct_enrichment": None}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        spearman_value = stats.spearmanr(y_true, y_pred).statistic
    if np.isnan(spearman_value):
        spearman_value = None
    return {
        "mae": short_float(mean_absolute_error(y_true, y_pred)),
        "rmse": short_float(math.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": short_float(r2_score(y_true, y_pred)),
        "spearman": short_float(spearman_value) if spearman_value is not None else None,
        "top_10pct_enrichment": short_float(top_fraction_enrichment(y_true, y_pred, fraction=0.10)),
    }


def top_fraction_enrichment(y_true: np.ndarray, y_pred: np.ndarray, fraction: float = 0.10) -> float | None:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    if y_true.size < 10:
        return None
    n_select = max(1, int(math.ceil(fraction * y_true.size)))
    threshold = np.quantile(y_true, 1 - fraction)
    high_yield = y_true >= threshold
    base_rate = high_yield.mean()
    if base_rate == 0:
        return None
    selected = np.argsort(y_pred)[-n_select:]
    selected_rate = high_yield[selected].mean()
    return float(selected_rate / base_rate)


def yield_bin_errors(y_true: np.ndarray, y_pred: np.ndarray, bins: int = 5) -> list[dict[str, Any]]:
    frame = pd.DataFrame({"y_true": y_true, "abs_error": np.abs(np.asarray(y_true) - np.asarray(y_pred))})
    frame["yield_bin"] = pd.cut(frame["y_true"], bins=np.linspace(0, 100, bins + 1), include_lowest=True)
    grouped = frame.groupby("yield_bin", observed=False)["abs_error"].agg(["count", "mean"]).reset_index()
    return [
        {
            "yield_bin": str(row["yield_bin"]),
            "count": int(row["count"]),
            "mae": short_float(row["mean"]),
        }
        for _, row in grouped.iterrows()
    ]
