"""Helpers for analysing prompt_optimisation.ipynb experiment results."""

import pandas as pd


def compute_binary_metrics(
    df: pd.DataFrame,
    true_col: str = "label",
    pred_col: str = "verdict",
    positive_class: str = "tampered",
    negative_class: str = "authentic",
) -> pd.Series:
    """Compute binary classification metrics for one DataFrame.

    `positive_class` (default "tampered") is treated as positive and
    `negative_class` (default "authentic") as negative.

    Pass any subset of a `load_results()` DataFrame, or use with
    `df.groupby(...).apply(compute_binary_metrics)` to get metrics per group.

    Rows with no ground-truth label, or whose `pred_col` is neither
    `positive_class` nor `negative_class` (e.g. "inconclusive"), are
    excluded — `excluded_count` reports how many were dropped this way.
    """
    labeled = df[df[true_col].notna()]
    binary = labeled[labeled[pred_col].isin([positive_class, negative_class])]

    true_positive = (
        (binary[pred_col] == positive_class) & (binary[true_col] == positive_class)
    ).sum()
    false_positive = (
        (binary[pred_col] == positive_class) & (binary[true_col] == negative_class)
    ).sum()
    false_negative = (
        (binary[pred_col] == negative_class) & (binary[true_col] == positive_class)
    ).sum()
    true_negative = (
        (binary[pred_col] == negative_class) & (binary[true_col] == negative_class)
    ).sum()

    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else float("nan")
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if (true_positive + false_negative) > 0
        else float("nan")
    )
    specificity = (
        true_negative / (true_negative + false_positive)
        if (true_negative + false_positive) > 0
        else float("nan")
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else float("nan")
    )
    accuracy = (
        (true_positive + true_negative) / len(binary)
        if len(binary) > 0
        else float("nan")
    )

    return pd.Series(
        {
            "precision": precision,
            "recall": recall,
            "specificity": specificity,
            "f1": f1,
            "accuracy": accuracy,
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "true_negative": true_negative,
            "excluded_count": len(labeled) - len(binary),
        }
    )
