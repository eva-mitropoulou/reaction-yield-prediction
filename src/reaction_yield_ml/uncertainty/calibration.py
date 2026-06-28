from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from reaction_yield_ml.reporting.io import short_float


def empirical_coverage(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float | None:
    if len(y_true) == 0:
        return None
    covered = (np.asarray(y_true) >= np.asarray(lower)) & (np.asarray(y_true) <= np.asarray(upper))
    return short_float(float(np.mean(covered)))


def uncertainty_error_summary(y_true: np.ndarray, y_pred: np.ndarray, uncertainty: np.ndarray, bins: int = 5) -> dict[str, Any]:
    errors = np.abs(np.asarray(y_true) - np.asarray(y_pred))
    uncertainty = np.asarray(uncertainty)
    corr = stats.spearmanr(errors, uncertainty).statistic
    if np.isnan(corr):
        corr = None
    frame = pd.DataFrame({"abs_error": errors, "uncertainty": uncertainty})
    frame["uncertainty_bin"] = pd.qcut(frame["uncertainty"].rank(method="first"), q=min(bins, len(frame)), duplicates="drop")
    grouped = frame.groupby("uncertainty_bin", observed=False).agg(
        count=("abs_error", "size"),
        mean_abs_error=("abs_error", "mean"),
        mean_uncertainty=("uncertainty", "mean"),
    )
    return {
        "spearman_abs_error_vs_uncertainty": short_float(corr) if corr is not None else None,
        "bins": [
            {
                "bin": str(idx),
                "count": int(row["count"]),
                "mean_abs_error": short_float(row["mean_abs_error"]),
                "mean_uncertainty": short_float(row["mean_uncertainty"]),
            }
            for idx, row in grouped.iterrows()
        ],
    }
