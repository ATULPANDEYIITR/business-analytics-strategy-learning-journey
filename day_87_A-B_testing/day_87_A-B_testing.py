from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from statistics import NormalDist
from typing import Optional


# ============================================================
# A/B TESTING: EXPERIMENT DESIGN AND STATISTICAL COMPARISON
# ============================================================

class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"


class Variant(Enum):
    CONTROL = "control"
    TREATMENT = "treatment"


class OutcomeType(Enum):
    BINARY = "binary"
    CONTINUOUS = "continuous"


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_id: str
    name: str
    control_name: str
    treatment_name: str
    allocation_ratio: float = 0.5
    significance_level: float = 0.05
    statistical_power: float = 0.80
    minimum_detectable_effect: float = 0.05
    baseline_conversion_rate: float = 0.10

    def __post_init__(self):
        if not self.experiment_id.strip():
            raise ValueError("Experiment ID cannot be empty.")
        if not 0 < self.allocation_ratio < 1:
            raise ValueError("Allocation ratio must be between 0 and 1.")
        if not 0 < self.significance_level < 1:
            raise ValueError("Invalid significance level.")
        if not 0 < self.statistical_power < 1:
            raise ValueError("Statistical power must be between 0 and 1.")
        if not 0 < self.minimum_detectable_effect < 1:
            raise ValueError("Invalid minimum detectable effect.")
        if not 0 < self.baseline_conversion_rate < 1:
            raise ValueError("Baseline conversion rate must be between 0 and 1.")


@dataclass
class Participant:
    participant_id: str
    variant: Variant
    assigned_at: datetime
    converted: Optional[bool] = None
    revenue: Optional[float] = None


@dataclass
class VariantMetrics:
    variant: Variant
    participants: int
    conversions: int
    conversion_rate: float
    total_revenue: float
    average_revenue: float


@dataclass
class ExperimentResult:
    control: VariantMetrics
    treatment: VariantMetrics
    absolute_lift: float
    relative_lift: float
    standard_error: float
    z_score: float
    p_value: float
    confidence_interval: tuple[float, float]
    statistically_significant: bool
    practical_significance: bool
    interpretation: str


@dataclass
class Experiment:
    config: ExperimentConfig
    status: ExperimentStatus = ExperimentStatus.DRAFT
    participants: dict[str, Participant] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def start(self):
        if self.status != ExperimentStatus.DRAFT:
            raise ValueError("Only draft experiments can be started.")
        self.status = ExperimentStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def assign_variant(self, participant_id: str) -> Variant:
        if self.status != ExperimentStatus.RUNNING:
            raise ValueError("Experiment is not running.")

        if not participant_id or not participant_id.strip():
            raise ValueError("Participant ID cannot be empty.")

        if participant_id in self.participants:
            return self.participants[participant_id].variant

        # Stable hash-based assignment prevents reassignment across sessions.
        key = f"{self.config.experiment_id}:{participant_id}".encode()
        digest = hashlib.sha256(key).digest()
        bucket = int.from_bytes(digest[:8], "big") / (2**64)

        variant = (
            Variant.CONTROL
            if bucket < self.config.allocation_ratio
            else Variant.TREATMENT
        )

        self.participants[participant_id] = Participant(
            participant_id=participant_id,
            variant=variant,
            assigned_at=datetime.now(timezone.utc),
        )
        return variant

    def record_outcome(
        self,
        participant_id: str,
        converted: bool,
        revenue: float = 0.0,
    ):
        if self.status != ExperimentStatus.RUNNING:
            raise ValueError("Outcomes can only be recorded while running.")

        if participant_id not in self.participants:
            raise ValueError("Participant has not been assigned.")

        if not isinstance(converted, bool):
            raise ValueError("Conversion must be boolean.")

        if not math.isfinite(revenue) or revenue < 0:
            raise ValueError("Revenue must be finite and non-negative.")

        participant = self.participants[participant_id]

        if participant.converted is not None:
            raise ValueError("Outcome has already been recorded.")

        participant.converted = converted
        participant.revenue = revenue

    def stop(self):
        if self.status != ExperimentStatus.RUNNING:
            raise ValueError("Only running experiments can be stopped.")
        self.status = ExperimentStatus.STOPPED
        self.completed_at = datetime.now(timezone.utc)

    def complete(self):
        if self.status != ExperimentStatus.RUNNING:
            raise ValueError("Only running experiments can be completed.")
        self.status = ExperimentStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)


class ExperimentAnalyzer:

    @staticmethod
    def metrics(experiment: Experiment, variant: Variant) -> VariantMetrics:
        members = [
            p for p in experiment.participants.values()
            if p.variant == variant and p.converted is not None
        ]

        total = len(members)
        conversions = sum(p.converted for p in members)
        revenue = sum(p.revenue for p in members)

        return VariantMetrics(
            variant=variant,
            participants=total,
            conversions=conversions,
            conversion_rate=conversions / total if total else 0.0,
            total_revenue=revenue,
            average_revenue=revenue / total if total else 0.0,
        )

    @staticmethod
    def analyze(experiment: Experiment) -> ExperimentResult:
        if experiment.status not in (
            ExperimentStatus.COMPLETED,
            ExperimentStatus.STOPPED,
        ):
            raise ValueError("Complete or stop the experiment before analysis.")

        control = ExperimentAnalyzer.metrics(experiment, Variant.CONTROL)
        treatment = ExperimentAnalyzer.metrics(experiment, Variant.TREATMENT)

        n1 = control.participants
        n2 = treatment.participants

        if n1 == 0 or n2 == 0:
            raise ValueError("Both variants require observed participants.")

        p1 = control.conversion_rate
        p2 = treatment.conversion_rate

        absolute_lift = p2 - p1
        relative_lift = absolute_lift / p1 if p1 > 0 else 0.0

        # Two-proportion pooled z-test.
        pooled = (control.conversions + treatment.conversions) / (n1 + n2)

        standard_error = math.sqrt(
            pooled * (1 - pooled) * (1 / n1 + 1 / n2)
        )

        if standard_error == 0:
            z_score = 0.0
            p_value = 1.0
        else:
            z_score = absolute_lift / standard_error
            p_value = 2 * NormalDist().cdf(-abs(z_score))

        # Unpooled standard error is used for the confidence interval.
        ci_se = math.sqrt(
            p1 * (1 - p1) / n1 +
            p2 * (1 - p2) / n2
        )

        critical = NormalDist().inv_cdf(
            1 - experiment.config.significance_level / 2
        )

        confidence_interval = (
            absolute_lift - critical * ci_se,
            absolute_lift + critical * ci_se,
        )

        significant = p_value < experiment.config.significance_level

        practical = (
            absolute_lift >=
            experiment.config.minimum_detectable_effect
        )

        if significant and practical:
            interpretation = "Treatment demonstrates statistically significant and practically meaningful improvement."
        elif significant:
            interpretation = "Treatment demonstrates statistical significance but does not meet the practical effect threshold."
        elif absolute_lift > 0:
            interpretation = "Treatment performs better numerically, but evidence is insufficient for statistical significance."
        elif absolute_lift < 0:
            interpretation = "Treatment performs worse numerically, but the difference is not statistically significant."
        else:
            interpretation = "No observed difference between variants."

        return ExperimentResult(
            control=control,
            treatment=treatment,
            absolute_lift=absolute_lift,
            relative_lift=relative_lift,
            standard_error=standard_error,
            z_score=z_score,
            p_value=p_value,
            confidence_interval=confidence_interval,
            statistically_significant=significant,
            practical_significance=practical,
            interpretation=interpretation,
        )


class ExperimentDesigner:

    @staticmethod
    def required_sample_size(
        baseline_rate: float,
        minimum_detectable_effect: float,
        significance_level: float = 0.05,
        power: float = 0.80,
    ) -> int:

        if not 0 < baseline_rate < 1:
            raise ValueError("Baseline rate must be between 0 and 1.")

        if not 0 < minimum_detectable_effect:
            raise ValueError("Effect size must be positive.")

        treatment_rate = baseline_rate + minimum_detectable_effect

        if treatment_rate >= 1:
            raise ValueError("Treatment rate must be below 1.")

        if not 0 < significance_level < 1:
            raise ValueError("Invalid significance level.")

        if not 0 < power < 1:
            raise ValueError("Invalid power.")

        normal = NormalDist()
        z_alpha = normal.inv_cdf(1 - significance_level / 2)
        z_beta = normal.inv_cdf(power)

        pooled = (baseline_rate + treatment_rate) / 2

        numerator = (
            z_alpha * math.sqrt(2 * pooled * (1 - pooled)) +
            z_beta * math.sqrt(
                baseline_rate * (1 - baseline_rate) +
                treatment_rate * (1 - treatment_rate)
            )
        ) ** 2

        return math.ceil(
            numerator / minimum_detectable_effect**2
        )


class SampleRatioMismatch:

    @staticmethod
    def check(
        control_count: int,
        treatment_count: int,
        expected_control_ratio: float = 0.5,
        alpha: float = 0.001,
    ) -> dict:

        if control_count < 0 or treatment_count < 0:
            raise ValueError("Counts cannot be negative.")

        if control_count + treatment_count == 0:
            raise ValueError("At least one participant is required.")

        if not 0 < expected_control_ratio < 1:
            raise ValueError("Invalid expected ratio.")

        total = control_count + treatment_count
        observed = control_count / total

        expected_control = total * expected_control_ratio
        expected_treatment = total * (1 - expected_control_ratio)

        chi_square = (
            (control_count - expected_control) ** 2 / expected_control +
            (treatment_count - expected_treatment) ** 2 / expected_treatment
        )

        # One degree of freedom chi-square survival probability.
        p_value = math.erfc(math.sqrt(chi_square / 2))

        return {
            "expected_control_ratio": expected_control_ratio,
            "observed_control_ratio": observed,
            "chi_square": chi_square,
            "p_value": p_value,
            "sample_ratio_mismatch": p_value < alpha,
        }


def simulate_experiment(
    control_rate: float,
    treatment_rate: float,
    sample_size: int,
    seed: int = 42,
) -> Experiment:

    random.seed(seed)

    config = ExperimentConfig(
        experiment_id="checkout-button-2026",
        name="Checkout Button Experiment",
        control_name="Original Button",
        treatment_name="Redesigned Button",
        baseline_conversion_rate=control_rate,
        minimum_detectable_effect=0.03,
    )

    experiment = Experiment(config)
    experiment.start()

    for i in range(sample_size):
        participant_id = f"user-{i:06d}"
        variant = experiment.assign_variant(participant_id)

        conversion_probability = (
            control_rate
            if variant == Variant.CONTROL
            else treatment_rate
        )

        converted = random.random() < conversion_probability

        revenue = (
            round(random.uniform(20, 150), 2)
            if converted
            else 0.0
        )

        experiment.record_outcome(
            participant_id,
            converted,
            revenue,
        )

    experiment.complete()
    return experiment


def print_report(experiment: Experiment):
    result = ExperimentAnalyzer.analyze(experiment)

    print("\n========== A/B TEST REPORT ==========")
    print(f"Experiment: {experiment.config.name}")
    print(f"Status: {experiment.status.value}")

    for metrics in (result.control, result.treatment):
        print(f"\nVariant: {metrics.variant.value}")
        print(f"Participants: {metrics.participants}")
        print(f"Conversions: {metrics.conversions}")
        print(f"Conversion rate: {metrics.conversion_rate:.4%}")
        print(f"Revenue: {metrics.total_revenue:.2f}")
        print(f"Average revenue per participant: {metrics.average_revenue:.2f}")

    print("\n========== STATISTICAL ANALYSIS ==========")
    print(f"Absolute lift: {result.absolute_lift:.4%}")
    print(f"Relative lift: {result.relative_lift:.4%}")
    print(f"Z-score: {result.z_score:.4f}")
    print(f"P-value: {result.p_value:.6f}")
    print(
        "95% confidence interval: "
        f"[{result.confidence_interval[0]:.4%}, "
        f"{result.confidence_interval[1]:.4%}]"
    )
    print(f"Statistically significant: {result.statistically_significant}")
    print(f"Practically significant: {result.practical_significance}")
    print(f"Interpretation: {result.interpretation}")


def main():
    print("A/B TESTING AND EXPERIMENT DESIGN")

    config = ExperimentConfig(
        experiment_id="checkout-button-2026",
        name="Checkout Button Conversion Test",
        control_name="Original Checkout",
        treatment_name="Redesigned Checkout",
        baseline_conversion_rate=0.10,
        minimum_detectable_effect=0.02,
    )

    required = ExperimentDesigner.required_sample_size(
        baseline_rate=config.baseline_conversion_rate,
        minimum_detectable_effect=config.minimum_detectable_effect,
        significance_level=config.significance_level,
        power=config.statistical_power,
    )

    print(f"\nRequired approximate sample size per group: {required:,}")

    experiment = simulate_experiment(
        control_rate=0.10,
        treatment_rate=0.12,
        sample_size=20000,
    )

    print_report(experiment)

    print("\n========== SAMPLE RATIO MISMATCH ==========")

    control = sum(
        p.variant == Variant.CONTROL
        for p in experiment.participants.values()
    )

    treatment = sum(
        p.variant == Variant.TREATMENT
        for p in experiment.participants.values()
    )

    print(
        SampleRatioMismatch.check(
            control,
            treatment,
            expected_control_ratio=0.5,
        )
    )

    print("\n========== EDGE CASE VALIDATION ==========")

    try:
        ExperimentConfig(
            experiment_id="invalid",
            name="Invalid",
            control_name="A",
            treatment_name="B",
            allocation_ratio=1.5,
        )
    except ValueError as error:
        print(f"Validation correctly rejected invalid allocation: {error}")

    try:
        ExperimentDesigner.required_sample_size(
            baseline_rate=0.10,
            minimum_detectable_effect=0.95,
        )
    except ValueError as error:
        print(f"Sample size validation: {error}")


if __name__ == "__main__":
    main()
