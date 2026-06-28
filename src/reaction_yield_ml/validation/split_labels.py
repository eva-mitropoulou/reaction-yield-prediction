from __future__ import annotations

from typing import Any


ROLE_LABELS = {
    "component_additive": "additive",
    "component_aryl_halide": "aryl halide",
    "component_base": "base",
    "component_ligand": "ligand",
    "component_substrate": "substrate",
    "component_electrophile": "electrophile",
}

MODEL_LABELS = {
    "gradient_boosting": "Gradient boosting",
    "mean_baseline": "Mean baseline",
    "onehot_elastic_net": "Elastic net",
    "onehot_ridge": "Ridge regression",
    "ridge": "Ridge regression",
    "random_forest": "Random forest",
}

SPLIT_LABELS = {
    "grouped_high_cardinality_component": "Grouped component split",
    "out_of_additive": "Held-out additive split",
    "out_of_base": "Held-out base split",
    "out_of_ligand": "Held-out ligand split",
    "out_of_substrate": "Held-out aryl halide split",
    "random_split": "Random split",
}

STRATEGY_LABELS = {
    "component_diverse_high_score": "Diverse high-score",
    "diversity_aware_selection": "Diversity-aware",
    "exploitation_plus_uncertainty": "Score plus uncertainty",
    "highest_predicted_yield": "Highest predicted yield",
    "random_selection": "Random selection",
    "uncertainty_sampling": "Uncertainty sampling",
}


def component_role_label(group_column: str | None) -> str | None:
    if not group_column:
        return None
    return ROLE_LABELS.get(group_column, group_column.replace("component_", "").replace("_", " "))


def component_role_display_name(group_column: str | None) -> str:
    role = component_role_label(group_column)
    return role.title() if role else "Component"


def model_display_name(value: str) -> str:
    return MODEL_LABELS.get(value, value.replace("_", " ").title())


def strategy_display_name(value: str) -> str:
    return STRATEGY_LABELS.get(value, value.replace("_", " ").title())


def split_display_name(split_name: str, split_payload: dict[str, Any] | None = None) -> str:
    split_payload = split_payload or {}
    group_column = split_payload.get("group_column")
    role = component_role_label(group_column)
    if split_name == "grouped_high_cardinality_component" and role:
        return f"{role.title()} held-out grouped split"
    if split_name.startswith("out_of_") and role:
        return f"Held-out {role} split"
    return SPLIT_LABELS.get(split_name, split_name.replace("_", " ").title())


def equivalent_grouped_split_note(primary_split: str, splits: dict[str, dict[str, Any]]) -> str | None:
    primary = splits.get(primary_split, {})
    group_column = primary.get("group_column")
    if not group_column:
        return None
    equivalent = [
        name
        for name, payload in splits.items()
        if name != primary_split and payload.get("is_valid") and payload.get("group_column") == group_column
    ]
    if not equivalent:
        return None
    role = component_role_label(group_column) or "component"
    equivalent_labels = [split_display_name(name, splits.get(name, {})) for name in equivalent]
    equivalent_text = ", ".join(equivalent_labels)
    return (
        f"In this dataset, the grouped split holds out {role} values, so it uses the "
        f"same held-out group design as {equivalent_text}."
    )
