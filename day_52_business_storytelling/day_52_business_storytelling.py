from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, median
from typing import Iterable
import csv
import json
import math


@dataclass(frozen=True)
class Metric:
    name: str
    current: float
    previous: float
    target: float
    unit: str = ""

    @property
    def change(self) -> float:
        return self.current - self.previous

    @property
    def change_pct(self) -> float:
        if self.previous == 0:
            return math.inf if self.current > 0 else 0.0
        return (self.change / self.previous) * 100

    @property
    def target_gap(self) -> float:
        return self.current - self.target


@dataclass
class Insight:
    observation: str
    implication: str
    action: str
    priority: str
    evidence: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "observation": self.observation,
            "implication": self.implication,
            "action": self.action,
            "priority": self.priority,
            "evidence": self.evidence,
        }


class StorytellingModel:
    """Transforms analytical measurements into decision-oriented business stories."""

    POSITIVE_KEYWORDS = {"growth", "conversion", "retention", "revenue", "margin"}

    def __init__(self, metrics: Iterable[Metric]):
        self.metrics = list(metrics)
        self._validate()

    def _validate(self) -> None:
        if not self.metrics:
            raise ValueError("At least one metric is required.")

        names = [metric.name.strip().lower() for metric in self.metrics]
        if any(not name for name in names):
            raise ValueError("Metric names cannot be empty.")
        if len(names) != len(set(names)):
            raise ValueError("Metric names must be unique.")

        for metric in self.metrics:
            values = (metric.current, metric.previous, metric.target)
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"Non-finite value found for {metric.name}.")

    def identify_signals(self) -> list[dict]:
        signals = []

        for metric in self.metrics:
            if metric.change_pct >= 10:
                signal = "strong positive movement"
            elif metric.change_pct >= 3:
                signal = "moderate positive movement"
            elif metric.change_pct <= -10:
                signal = "material deterioration"
            elif metric.change_pct <= -3:
                signal = "moderate deterioration"
            else:
                signal = "stable movement"

            target_state = (
                "above target"
                if metric.current >= metric.target
                else "below target"
            )

            signals.append(
                {
                    "metric": metric.name,
                    "change_pct": round(metric.change_pct, 2),
                    "signal": signal,
                    "target_state": target_state,
                }
            )

        return signals

    def build_insights(self) -> list[Insight]:
        insights: list[Insight] = []

        for metric in self.metrics:
            pct = metric.change_pct

            if pct <= -10:
                priority = "critical"
                implication = (
                    f"{metric.name} has deteriorated materially, which can "
                    "translate into a measurable business risk."
                )
                action = (
                    f"Investigate the drivers of {metric.name}, segment the decline "
                    "by business dimension, and assign an owner to the largest driver."
                )
            elif pct < -3:
                priority = "high"
                implication = (
                    f"{metric.name} is moving in an unfavorable direction and "
                    "requires targeted investigation."
                )
                action = (
                    f"Analyze {metric.name} by customer, channel, product, and "
                    "time period before selecting a corrective intervention."
                )
            elif pct >= 10:
                priority = "high"
                implication = (
                    f"{metric.name} is showing strong improvement and may indicate "
                    "a repeatable business opportunity."
                )
                action = (
                    f"Identify the operational driver behind {metric.name}'s growth "
                    "and determine whether the successful behavior can be scaled."
                )
            elif pct >= 3:
                priority = "medium"
                implication = (
                    f"{metric.name} is improving, but the magnitude should be "
                    "evaluated against its target and business importance."
                )
                action = (
                    f"Continue monitoring {metric.name} and test whether the "
                    "observed improvement persists across relevant segments."
                )
            else:
                priority = "low"
                implication = (
                    f"{metric.name} is relatively stable and does not currently "
                    "represent a major directional signal."
                )
                action = (
                    f"Maintain monitoring for {metric.name} while prioritizing "
                    "metrics with larger business impact."
                )

            evidence = [
                f"Current: {metric.current:g}{metric.unit}",
                f"Previous: {metric.previous:g}{metric.unit}",
                f"Target: {metric.target:g}{metric.unit}",
                f"Change: {metric.change:+g}{metric.unit}",
                f"Change rate: {pct:+.2f}%",
            ]

            insights.append(
                Insight(
                    observation=(
                        f"{metric.name} changed from "
                        f"{metric.previous:g}{metric.unit} to "
                        f"{metric.current:g}{metric.unit}."
                    ),
                    implication=implication,
                    action=action,
                    priority=priority,
                    evidence=evidence,
                )
            )

        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        insights.sort(key=lambda item: priority_order[item.priority])
        return insights

    def executive_story(self) -> str:
        insights = self.build_insights()
        strongest = insights[0]

        improving = [
            metric for metric in self.metrics if metric.change > 0
        ]
        declining = [
            metric for metric in self.metrics if metric.change < 0
        ]

        return (
            "EXECUTIVE STORY\n"
            "================\n"
            f"Headline: {strongest.observation}\n\n"
            f"What happened: {strongest.observation}\n"
            f"Why it matters: {strongest.implication}\n"
            f"What to do: {strongest.action}\n\n"
            f"Portfolio signal: {len(improving)} metrics improved and "
            f"{len(declining)} metrics declined.\n"
        )

    def decision_table(self) -> list[dict]:
        return [
            {
                "metric": metric.name,
                "current": metric.current,
                "previous": metric.previous,
                "target": metric.target,
                "change_pct": round(metric.change_pct, 2),
                "target_gap": round(metric.target_gap, 2),
            }
            for metric in self.metrics
        ]


def load_metrics_csv(path: str | Path) -> list[Metric]:
    """Load analytical data while validating numeric business measures."""
    metrics: list[Metric] = []

    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        required = {"name", "current", "previous", "target"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV must contain columns: {sorted(required)}")

        for row_number, row in enumerate(reader, start=2):
            try:
                metrics.append(
                    Metric(
                        name=row["name"].strip(),
                        current=float(row["current"]),
                        previous=float(row["previous"]),
                        target=float(row["target"]),
                        unit=row.get("unit", "").strip(),
                    )
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid metric data on CSV row {row_number}."
                ) from exc

    return metrics


def save_story(path: str | Path, model: StorytellingModel) -> None:
    output = {
        "story": model.executive_story(),
        "signals": model.identify_signals(),
        "insights": [item.as_dict() for item in model.build_insights()],
        "decision_table": model.decision_table(),
    }

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)


def main() -> None:
    # The dataset represents a business dashboard converted into a decision story.
    metrics = [
        Metric("Revenue", 12.4, 10.8, 12.0, "M"),
        Metric("Conversion Rate", 4.7, 5.3, 5.0, "%"),
        Metric("Customer Retention", 91.0, 88.0, 90.0, "%"),
        Metric("Support Cost", 1.9, 1.6, 1.7, "M"),
        Metric("Gross Margin", 37.5, 35.8, 36.0, "%"),
    ]

    model = StorytellingModel(metrics)

    print(model.executive_story())

    print("DECISION SIGNALS")
    print("================")
    for signal in model.identify_signals():
        print(
            f"{signal['metric']}: {signal['signal']} | "
            f"{signal['change_pct']:+.2f}% | {signal['target_state']}"
        )

    print("\nACTIONABLE INSIGHTS")
    print("===================")
    for insight in model.build_insights():
        print(f"\n[{insight.priority.upper()}] {insight.observation}")
        print(f"Implication: {insight.implication}")
        print(f"Action: {insight.action}")
        print("Evidence: " + "; ".join(insight.evidence))

    output_path = Path("business_story.json")
    save_story(output_path, model)
    print(f"\nStory artifact written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
