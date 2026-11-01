#!/usr/bin/env python3
"""
NumPy numerical computing and array operations.

This script covers:
- Array creation and dtype control
- Indexing, slicing, masking, reshaping, and broadcasting
- Vectorized arithmetic and aggregation
- Linear algebra
- Statistical calculations
- NaN-aware processing
- Random number generation
- Numerical validation
- Performance comparison with Python loops
- A realistic numerical analytics workflow
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class SensorBatch:
    """Validated matrix of sensor measurements."""

    values: np.ndarray
    sensor_names: tuple[str, ...]

    def __post_init__(self) -> None:
        values = np.asarray(self.values, dtype=np.float64)

        if values.ndim != 2:
            raise ValueError("Sensor data must be a two-dimensional array.")

        if values.shape[1] != len(self.sensor_names):
            raise ValueError("Sensor name count must match the number of columns.")

        if not np.isfinite(values).any():
            raise ValueError("Sensor data contains no finite measurements.")

        object.__setattr__(self, "values", values)

    @property
    def rows(self) -> int:
        return self.values.shape[0]

    @property
    def columns(self) -> int:
        return self.values.shape[1]

    def column(self, name: str) -> np.ndarray:
        if name not in self.sensor_names:
            raise KeyError(f"Unknown sensor: {name}")
        index = self.sensor_names.index(name)
        return self.values[:, index]


def create_measurements() -> SensorBatch:
    """Create a deterministic sample sensor matrix."""
    raw = np.array(
        [
            [22.4, 45.0, 1012.3, 0.12],
            [23.1, 46.5, 1011.8, 0.15],
            [24.8, 49.2, 1010.4, 0.18],
            [26.7, 54.0, 1008.9, 0.31],
            [28.4, 58.1, 1007.5, 0.42],
            [29.1, 61.0, 1006.2, 0.55],
            [27.8, 57.3, 1007.1, 0.38],
            [25.6, 51.4, 1009.2, 0.22],
        ],
        dtype=np.float64,
    )
    return SensorBatch(
        raw,
        ("temperature_c", "humidity_pct", "pressure_hpa", "vibration"),
    )


def demonstrate_array_operations(batch: SensorBatch) -> None:
    values = batch.values

    print("=== Array structure ===")
    print("Shape:", values.shape)
    print("Dimensions:", values.ndim)
    print("Dtype:", values.dtype)
    print("First row:", values[0])
    print("Temperature column:", values[:, 0])
    print("First three records:\n", values[:3])
    print("Last two records:\n", values[-2:])

    print("\n=== Boolean masking ===")
    high_temperature = values[values[:, 0] >= 27.0]
    print("Rows with temperature >= 27 C:\n", high_temperature)

    print("\n=== Vectorized transformation ===")
    temperature_f = values[:, 0] * 9.0 / 5.0 + 32.0
    print("Temperature Fahrenheit:", temperature_f)

    print("\n=== Reshaping ===")
    flattened = values.reshape(-1)
    restored = flattened.reshape(values.shape)
    assert np.array_equal(restored, values)
    print("Flattened elements:", flattened.size)
    print("Restored shape:", restored.shape)

    print("\n=== Broadcasting ===")
    offsets = np.array([1.0, -2.0, 0.5, 0.0])
    adjusted = values + offsets
    print("Adjusted first row:", adjusted[0])


def summarize(batch: SensorBatch) -> dict[str, dict[str, float]]:
    values = batch.values
    summary: dict[str, dict[str, float]] = {}

    for index, name in enumerate(batch.sensor_names):
        column = values[:, index]
        summary[name] = {
            "minimum": float(np.min(column)),
            "maximum": float(np.max(column)),
            "mean": float(np.mean(column)),
            "median": float(np.median(column)),
            "std": float(np.std(column)),
        }

    return summary


def robust_z_scores(values: np.ndarray) -> np.ndarray:
    """Calculate column-wise z-scores with zero-variance protection."""
    values = np.asarray(values, dtype=np.float64)

    if values.ndim != 2:
        raise ValueError("Expected a two-dimensional matrix.")

    mean = np.mean(values, axis=0)
    std = np.std(values, axis=0)

    safe_std = np.where(std == 0.0, 1.0, std)
    return (values - mean) / safe_std


def detect_anomalies(batch: SensorBatch, threshold: float = 2.0) -> np.ndarray:
    """Return rows containing at least one large absolute z-score."""
    if threshold <= 0:
        raise ValueError("Anomaly threshold must be positive.")

    scores = robust_z_scores(batch.values)
    return np.any(np.abs(scores) >= threshold, axis=1)


def demonstrate_missing_values() -> None:
    print("\n=== Missing-value handling ===")

    data = np.array(
        [
            [10.0, 20.0, np.nan],
            [11.0, np.nan, 30.0],
            [12.0, 22.0, 31.0],
        ]
    )

    print("NaN locations:\n", np.isnan(data))
    print("NaN-aware column means:", np.nanmean(data, axis=0))

    cleaned = np.nan_to_num(data, nan=0.0)
    print("NaN replaced with zero:\n", cleaned)


def demonstrate_linear_algebra() -> None:
    print("\n=== Linear algebra ===")

    matrix = np.array(
        [
            [4.0, 2.0],
            [1.0, 3.0],
        ]
    )
    vector = np.array([10.0, 20.0])

    product = matrix @ vector
    determinant = np.linalg.det(matrix)
    inverse = np.linalg.inv(matrix)
    solution = np.linalg.solve(matrix, vector)

    print("Matrix-vector product:", product)
    print("Determinant:", determinant)
    print("Inverse:\n", inverse)
    print("Linear-system solution:", solution)

    assert np.allclose(matrix @ solution, vector)


def demonstrate_statistics(batch: SensorBatch) -> None:
    print("\n=== Statistics ===")

    matrix = batch.values

    print("Column means:", np.mean(matrix, axis=0))
    print("Column standard deviations:", np.std(matrix, axis=0))
    print("Correlation matrix:\n", np.corrcoef(matrix, rowvar=False))
    print("Global minimum:", np.min(matrix))
    print("Global maximum:", np.max(matrix))

    weights = np.array([0.4, 0.2, 0.3, 0.1])
    normalized = (matrix - matrix.min(axis=0)) / (
        matrix.max(axis=0) - matrix.min(axis=0)
    )
    score = normalized @ weights

    print("Weighted normalized scores:", score)


def demonstrate_random_generation() -> None:
    print("\n=== Reproducible random generation ===")

    rng = np.random.default_rng(20261101)
    samples = rng.normal(loc=100.0, scale=15.0, size=(5, 3))

    print("Random sample matrix:\n", samples)
    print("Sample means:", samples.mean(axis=0))

    choices = rng.choice(
        np.array(["normal", "warning", "critical"]),
        size=10,
        p=[0.7, 0.25, 0.05],
    )
    print("Generated states:", choices)


def compare_performance() -> None:
    print("\n=== Vectorization performance ===")

    size = 1_000_000
    data = np.arange(size, dtype=np.float64)

    start = perf_counter()
    loop_result = [x * x + 2.0 * x + 1.0 for x in data]
    loop_time = perf_counter() - start

    start = perf_counter()
    vector_result = data * data + 2.0 * data + 1.0
    vector_time = perf_counter() - start

    assert np.allclose(loop_result, vector_result)

    print(f"Python loop: {loop_time:.6f} seconds")
    print(f"NumPy vectorization: {vector_time:.6f} seconds")

    if vector_time > 0:
        print(f"Measured speed ratio: {loop_time / vector_time:.2f}x")


def run_workflow(batch: SensorBatch) -> None:
    print("\n=== Numerical analytics workflow ===")

    values = batch.values

    # Normalize each feature independently. The epsilon prevents division
    # by zero if a future dataset contains a constant feature.
    minimum = values.min(axis=0)
    maximum = values.max(axis=0)
    denominator = np.where((maximum - minimum) == 0.0, 1.0, maximum - minimum)

    normalized = (values - minimum) / denominator

    weights = np.array([0.35, 0.20, 0.25, 0.20])
    risk_score = normalized @ weights

    high_risk = risk_score >= 0.60

    for row_index, score in enumerate(risk_score):
        state = "ALERT" if high_risk[row_index] else "NORMAL"
        print(f"Record {row_index + 1}: score={score:.3f} state={state}")

    print("Highest-risk record:", int(np.argmax(risk_score)) + 1)


def validate_edge_cases() -> None:
    print("\n=== Validation and edge cases ===")

    try:
        SensorBatch(np.array([1.0, 2.0]), ("x",))
    except ValueError as exc:
        print("Rejected invalid dimensionality:", exc)

    try:
        robust_z_scores(np.array([1.0, 2.0, 3.0]))
    except ValueError as exc:
        print("Rejected invalid z-score input:", exc)

    constant = np.full((3, 2), 5.0)
    scores = robust_z_scores(constant)
    assert np.allclose(scores, 0.0)
    print("Handled zero-variance features safely.")

    integer_values = np.arange(12).reshape(3, 4)
    view = integer_values[:, :2]
    view[0, 0] = -100
    assert integer_values[0, 0] == -100
    print("Array slicing produced a view; mutation was visible in the source.")


def main() -> None:
    batch = create_measurements()

    demonstrate_array_operations(batch)

    print("\n=== Descriptive summary ===")
    for name, stats in summarize(batch).items():
        print(name, stats)

    anomaly_mask = detect_anomalies(batch, threshold=2.0)
    print("\nAnomaly rows:", np.flatnonzero(anomaly_mask).tolist())

    demonstrate_missing_values()
    demonstrate_linear_algebra()
    demonstrate_statistics(batch)
    demonstrate_random_generation()
    compare_performance()
    run_workflow(batch)
    validate_edge_cases()

    print("\nNumPy numerical workflow completed successfully.")


if __name__ == "__main__":
    main()
