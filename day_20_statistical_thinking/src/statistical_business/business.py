# File: src/statistical_business/business.py

from __future__ import annotations

"""Business metrics built on top of the statistical core."""

from dataclasses import dataclass
from statistics import mean
from typing import Sequence

from .core import (
    StatisticalError,
    linear_regression,
    proportion_confidence_interval,
    two_proportion_z_test,
)


@dataclass(frozen=True)
class ExperimentResult:
    """Business interpretation of an A/B conversion experiment."""

    control_rate: float
    treatment_rate: float
    absolute_lift: float
    relative_lift: float
    p_value: float
    statistically_significant: bool
    confidence_interval: tuple[float, float]


def analyze_ab_test(
    control_conversions: int,
    control_visitors: int,
    treatment_conversions: int,
    treatment_visitors: int,
    alpha: float = 0.05,
) -> ExperimentResult:
    """Analyze conversion-rate differences without treating significance as ROI."""
    if not 0 < alpha < 1:
        raise StatisticalError("Alpha must be between zero and one.")

    result = two_proportion_z_test(
        control_conversions,
        control_visitors,
        treatment_conversions,
        treatment_visitors,
    )

    low, high = proportion_confidence_interval(
        treatment_conversions,
        treatment_visitors,
        confidence=1 - alpha,
    )

    return ExperimentResult(
        control_rate=result["proportion_a"],
        treatment_rate=result["proportion_b"],
        absolute_lift=result["absolute_difference"],
        relative_lift=result["relative_change"],
        p_value=result["p_value"],
        statistically_significant=result["p_value"] < alpha,
        confidence_interval=(low, high),
    )


def customer_lifetime_value(
    average_order_value: float,
    purchase_frequency: float,
    gross_margin: float,
    annual_retention: float,
    years: int = 5,
    discount_rate: float = 0.10,
) -> float:
    """Estimate discounted customer lifetime value.

    The model is deliberately explicit so that learners can inspect each
    assumption rather than treating CLV as a single opaque metric.
    """
    if min(average_order_value, purchase_frequency, gross_margin) < 0:
        raise StatisticalError("Monetary and frequency inputs cannot be negative.")
    if not 0 <= annual_retention <= 1:
        raise StatisticalError("Retention must be between zero and one.")
    if years <= 0:
        raise StatisticalError("Years must be positive.")
    if discount_rate < 0:
        raise StatisticalError("Discount rate cannot be negative.")

    annual_contribution = average_order_value * purchase_frequency * gross_margin

    return sum(
        annual_contribution * annual_retention ** (year - 1)
        / (1 + discount_rate) ** year
        for year in range(1, years + 1)
    )


def sales_forecast(
    historical_periods: Sequence[float],
    historical_sales: Sequence[float],
    future_period: float,
) -> float:
    """Use a simple linear trend as an educational forecasting baseline."""
    model = linear_regression(historical_periods, historical_sales)
    return model.predict(future_period)


def summarize_segments(
    segments: dict[str, Sequence[float]],
) -> dict[str, dict[str, float]]:
    """Compare segment averages without assuming that differences are causal."""
    result: dict[str, dict[str, float]] = {}

    for name, values in segments.items():
        if not values:
            raise StatisticalError(f"Segment '{name}' contains no observations.")

        average = mean(values)
        result[name] = {
            "count": float(len(values)),
            "mean": average,
            "minimum": min(values),
            "maximum": max(values),
        }

    return result
