# File: tests/test_core.py

import math

import pytest

from statistical_business.business import analyze_ab_test, customer_lifetime_value
from statistical_business.core import (
    StatisticalError,
    correlation,
    describe,
    expected_value,
    linear_regression,
    moving_average,
    proportion_confidence_interval,
)


def test_describe_returns_expected_statistics():
    result = describe([10, 20, 30, 40])

    assert result["count"] == 4
    assert result["mean"] == 25
    assert result["median"] == 25
    assert result["minimum"] == 10
    assert result["maximum"] == 40


def test_correlation_of_perfect_positive_relationship():
    assert math.isclose(correlation([1, 2, 3], [2, 4, 6]), 1.0)


def test_linear_regression():
    model = linear_regression([1, 2, 3, 4], [2, 4, 6, 8])

    assert math.isclose(model.slope, 2.0)
    assert math.isclose(model.intercept, 0.0)
    assert math.isclose(model.r_squared, 1.0)
    assert math.isclose(model.predict(5), 10.0)


def test_moving_average():
    assert moving_average([10, 20, 30, 40], 2) == [15, 25, 35]


def test_expected_value():
    assert expected_value([(100, 0.25), (0, 0.75)]) == 25


def test_confidence_interval_is_bounded():
    low, high = proportion_confidence_interval(50, 100)

    assert 0 <= low < 0.5 < high <= 1


def test_ab_test_detects_conversion_difference():
    result = analyze_ab_test(100, 1000, 130, 1000)

    assert result.treatment_rate > result.control_rate
    assert result.absolute_lift == pytest.approx(0.03)
    assert result.p_value < 0.05


def test_clv_is_positive():
    value = customer_lifetime_value(
        average_order_value=100,
        purchase_frequency=4,
        gross_margin=0.4,
        annual_retention=0.8,
    )

    assert value > 0


@pytest.mark.parametrize(
    "values",
    [
        [],
        [1],
    ],
)
def test_describe_rejects_insufficient_data(values):
    with pytest.raises(StatisticalError):
        describe(values)


def test_correlation_rejects_mismatched_lengths():
    with pytest.raises(StatisticalError):
        correlation([1, 2], [1, 2, 3])


def test_expected_value_requires_probabilities_to_sum_to_one():
    with pytest.raises(StatisticalError):
        expected_value([(10, 0.4), (20, 0.4)])
