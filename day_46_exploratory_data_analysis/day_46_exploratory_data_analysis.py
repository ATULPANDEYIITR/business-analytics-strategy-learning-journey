from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, median, stdev
from collections import Counter
import csv
import math
import random
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Observation:
    timestamp: datetime
    value: float
    region: str
    category: str


def mean_ignore_nan(values: Iterable[float]) -> float:
    clean = [float(v) for v in values if not math.isnan(float(v))]
    if not clean:
        raise ValueError("Cannot calculate a mean from empty or all-missing data.")
    return mean(clean)


def median_ignore_nan(values: Iterable[float]) -> float:
    clean = sorted(float(v) for v in values if not math.isnan(float(v)))
    if not clean:
        raise ValueError("Cannot calculate a median from empty or all-missing data.")
    return median(clean)


def sample_standard_deviation(values: Iterable[float]) -> float:
    clean = [float(v) for v in values if not math.isnan(float(v))]
    if len(clean) < 2:
        return 0.0
    return stdev(clean)


def percentile(values: Sequence[float], p: float) -> float:
    clean = sorted(float(v) for v in values if not math.isnan(float(v)))
    if not clean:
        raise ValueError("Cannot calculate a percentile from empty data.")
    if not 0 <= p <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    position = (len(clean) - 1) * p / 100
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return clean[lower]

    fraction = position - lower
    return clean[lower] + (clean[upper] - clean[lower]) * fraction


def quartiles(values: Sequence[float]) -> tuple[float, float, float]:
    return (
        percentile(values, 25),
        percentile(values, 50),
        percentile(values, 75),
    )


def z_scores(values: Sequence[float]) -> list[float]:
    clean = [float(v) for v in values]
    average = mean_ignore_nan(clean)
    standard_deviation = sample_standard_deviation(clean)

    if standard_deviation == 0:
        return [0.0 for _ in clean]

    return [(value - average) / standard_deviation for value in clean]


def iqr_outliers(values: Sequence[float]) -> list[tuple[int, float]]:
    q1, _, q3 = quartiles(values)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    return [
        (index, float(value))
        for index, value in enumerate(values)
        if value < lower or value > upper
    ]


def moving_average(values: Sequence[float], window: int) -> list[float]:
    if window <= 0:
        raise ValueError("Window must be positive.")
    if window > len(values):
        return []

    return [
        mean(values[index - window + 1:index + 1])
        for index in range(window - 1, len(values))
    ]


def linear_trend(values: Sequence[float]) -> tuple[float, float]:
    if len(values) < 2:
        raise ValueError("At least two observations are required.")

    x = list(range(len(values)))
    x_mean = mean(x)
    y_mean = mean(values)

    numerator = sum(
        (x_value - x_mean) * (y_value - y_mean)
        for x_value, y_value in zip(x, values)
    )
    denominator = sum((x_value - x_mean) ** 2 for x_value in x)

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    return slope, intercept


def correlation(first: Sequence[float], second: Sequence[float]) -> float:
    if len(first) != len(second) or len(first) < 2:
        raise ValueError("Correlation requires equally sized sequences with at least two values.")

    first_mean = mean(first)
    second_mean = mean(second)

    numerator = sum(
        (a - first_mean) * (b - second_mean)
        for a, b in zip(first, second)
    )
    first_ss = sum((a - first_mean) ** 2 for a in first)
    second_ss = sum((b - second_mean) ** 2 for b in second)

    denominator = math.sqrt(first_ss * second_ss)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def detect_local_anomalies(values: Sequence[float], window: int = 3) -> list[tuple[int, float, float]]:
    if window < 2:
        raise ValueError("Local anomaly window must contain at least two values.")

    anomalies = []

    for index, value in enumerate(values):
        start = max(0, index - window)
        end = min(len(values), index + window + 1)
        neighborhood = [
            values[i]
            for i in range(start, end)
            if i != index
        ]

        if len(neighborhood) < 2:
            continue

        local_mean = mean(neighborhood)
        local_std = sample_standard_deviation(neighborhood)

        if local_std > 0:
            local_z = abs(value - local_mean) / local_std
            if local_z >= 2.5:
                anomalies.append((index, value, local_z))

    return anomalies


def describe_dataset(values: Sequence[float]) -> dict[str, float]:
    q1, q2, q3 = quartiles(values)

    return {
        "count": len(values),
        "mean": mean(values),
        "median": q2,
        "minimum": min(values),
        "maximum": max(values),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "standard_deviation": sample_standard_deviation(values),
    }


def frequency_table(values: Sequence[str]) -> dict[str, int]:
    return dict(Counter(values))


def print_descriptive_statistics(values: Sequence[float]) -> None:
    statistics = describe_dataset(values)

    print("\nDescriptive statistics")
    for key, value in statistics.items():
        if isinstance(value, float):
            print(f"{key:20}: {value:.3f}")
        else:
            print(f"{key:20}: {value}")


def load_csv(path: str | Path) -> list[Observation]:
    observations = []

    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        required_columns = {"timestamp", "value", "region", "category"}
        if not required_columns.issubset(reader.fieldnames or set()):
            missing = required_columns - set(reader.fieldnames or set())
            raise ValueError(f"Missing required CSV columns: {sorted(missing)}")

        for row_number, row in enumerate(reader, start=2):
            try:
                timestamp = datetime.fromisoformat(row["timestamp"])
                value = float(row["value"])

                if not math.isfinite(value):
                    raise ValueError("Value must be finite.")

                observations.append(
                    Observation(
                        timestamp=timestamp,
                        value=value,
                        region=row["region"].strip(),
                        category=row["category"].strip(),
                    )
                )
            except (ValueError, TypeError) as error:
                raise ValueError(
                    f"Invalid observation on CSV row {row_number}: {error}"
                ) from error

    return observations


def create_realistic_sales_data(seed: int = 42) -> list[Observation]:
    random.seed(seed)

    regions = ["North", "South", "West"]
    categories = ["Enterprise", "SMB"]

    start = datetime(2026, 1, 1)
    observations: list[Observation] = []

    for day in range(90):
        timestamp = start + timedelta(days=day)

        seasonal_effect = 12 * math.sin(2 * math.pi * day / 30)
        growth_effect = day * 0.18

        for region_index, region in enumerate(regions):
            for category_index, category in enumerate(categories):
                base = 100 + region_index * 12 + category_index * 20
                noise = random.gauss(0, 5)

                value = base + seasonal_effect + growth_effect + noise

                if day == 53 and region == "West" and category == "Enterprise":
                    value += 65

                if day == 71 and region == "South" and category == "SMB":
                    value -= 55

                observations.append(
                    Observation(
                        timestamp=timestamp,
                        value=round(value, 2),
                        region=region,
                        category=category,
                    )
                )

    return observations


def aggregate_daily(observations: Sequence[Observation]) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}

    for observation in observations:
        key = observation.timestamp.date().isoformat()
        grouped.setdefault(key, []).append(observation.value)

    return {
        date: mean(values)
        for date, values in sorted(grouped.items())
    }


def aggregate_by_category(observations: Sequence[Observation]) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}

    for observation in observations:
        grouped.setdefault(observation.category, []).append(observation.value)

    return {
        category: mean(values)
        for category, values in sorted(grouped.items())
    }


def aggregate_by_region(observations: Sequence[Observation]) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}

    for observation in observations:
        grouped.setdefault(observation.region, []).append(observation.value)

    return {
        region: mean(values)
        for region, values in sorted(grouped.items())
    }


def compare_periods(values: Sequence[float], split: int) -> dict[str, float]:
    if not 0 < split < len(values):
        raise ValueError("Split must create two non-empty periods.")

    first = values[:split]
    second = values[split:]

    first_mean = mean(first)
    second_mean = mean(second)
    absolute_change = second_mean - first_mean
    percentage_change = (
        absolute_change / first_mean * 100
        if first_mean != 0
        else float("inf")
    )

    return {
        "first_mean": first_mean,
        "second_mean": second_mean,
        "absolute_change": absolute_change,
        "percentage_change": percentage_change,
    }


def create_analysis_report(observations: Sequence[Observation]) -> dict:
    values = [observation.value for observation in observations]
    daily = aggregate_daily(observations)
    daily_values = list(daily.values())

    slope, intercept = linear_trend(daily_values)
    global_outliers = iqr_outliers(values)
    local_outliers = detect_local_anomalies(daily_values)

    category_means = aggregate_by_category(observations)
    region_means = aggregate_by_region(observations)

    return {
        "records": len(observations),
        "statistics": describe_dataset(values),
        "daily_trend_slope": slope,
        "daily_trend_intercept": intercept,
        "moving_average_7": moving_average(daily_values, 7),
        "global_outlier_count": len(global_outliers),
        "local_anomaly_count": len(local_outliers),
        "category_means": category_means,
        "region_means": region_means,
        "period_comparison": compare_periods(
            daily_values,
            len(daily_values) // 2,
        ),
    }


def write_cleaned_csv(observations: Sequence[Observation], path: str | Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "value", "region", "category"])

        for observation in observations:
            writer.writerow([
                observation.timestamp.isoformat(),
                f"{observation.value:.2f}",
                observation.region,
                observation.category,
            ])


def main() -> None:
    print("Exploratory Data Analysis: patterns, trends, and anomalies")

    observations = create_realistic_sales_data()
    values = [observation.value for observation in observations]

    print(f"\nRecords analysed: {len(observations)}")
    print_descriptive_statistics(values)

    daily = aggregate_daily(observations)
    daily_values = list(daily.values())

    slope, intercept = linear_trend(daily_values)
    print(f"\nDaily trend slope: {slope:.4f}")
    print(f"Trend intercept:    {intercept:.4f}")

    moving = moving_average(daily_values, 7)
    print(f"7-day moving average points: {len(moving)}")
    print(f"Latest 7-day average: {moving[-1]:.3f}")

    global_outliers = iqr_outliers(values)
    print(f"\nGlobal IQR outliers: {len(global_outliers)}")

    local_anomalies = detect_local_anomalies(daily_values)
    print(f"Local time-series anomalies: {len(local_anomalies)}")

    if local_anomalies:
        print("\nStrong local anomalies")
        for index, value, score in local_anomalies:
            date = list(daily.keys())[index]
            print(f"{date}: value={value:.2f}, local deviation={score:.2f}σ")

    print("\nCategory patterns")
    for category, average in aggregate_by_category(observations).items():
        print(f"{category:12}: mean={average:.2f}")

    print("\nRegional patterns")
    for region, average in aggregate_by_region(observations).items():
        print(f"{region:12}: mean={average:.2f}")

    first_half = daily_values[:45]
    second_half = daily_values[45:]
    trend_change = mean(second_half) - mean(first_half)

    print("\nPeriod comparison")
    print(f"First period mean : {mean(first_half):.2f}")
    print(f"Second period mean: {mean(second_half):.2f}")
    print(f"Change            : {trend_change:+.2f}")

    z = z_scores(daily_values)
    extreme_daily_points = [
        (index, value, score)
        for index, (value, score) in enumerate(zip(daily_values, z))
        if abs(score) >= 2.5
    ]

    print("\nGlobal standardized anomalies")
    for index, value, score in extreme_daily_points:
        date = list(daily.keys())[index]
        print(f"{date}: value={value:.2f}, z={score:.2f}")

    print("\nFrequency structure")
    regions = [observation.region for observation in observations]
    categories = [observation.category for observation in observations]
    print("Regions:", frequency_table(regions))
    print("Categories:", frequency_table(categories))

    report = create_analysis_report(observations)

    output_path = Path("eda_sales_observations.csv")
    write_cleaned_csv(observations, output_path)

    print("\nReusable report fields")
    print(f"records             : {report['records']}")
    print(f"global outliers     : {report['global_outlier_count']}")
    print(f"local anomalies     : {report['local_anomaly_count']}")
    print(f"category means      : {report['category_means']}")
    print(f"region means        : {report['region_means']}")
    print(f"CSV written to      : {output_path.resolve()}")

    # Correlation is useful only when the paired observations have a meaningful
    # analytical relationship. Here, regional daily means are compared with
    # enterprise daily means after aligning them by date.
    enterprise_daily: dict[str, list[float]] = {}
    west_daily: dict[str, list[float]] = {}

    for observation in observations:
        date = observation.timestamp.date().isoformat()

        if observation.category == "Enterprise":
            enterprise_daily.setdefault(date, []).append(observation.value)

        if observation.region == "West":
            west_daily.setdefault(date, []).append(observation.value)

    paired_dates = sorted(set(enterprise_daily) & set(west_daily))
    enterprise_values = [mean(enterprise_daily[d]) for d in paired_dates]
    west_values = [mean(west_daily[d]) for d in paired_dates]

    print(
        f"\nEnterprise/West aligned correlation: "
        f"{correlation(enterprise_values, west_values):.3f}"
    )


if __name__ == "__main__":
    main()
