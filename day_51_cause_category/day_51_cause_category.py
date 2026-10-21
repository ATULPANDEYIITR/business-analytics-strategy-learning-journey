from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from collections import Counter, defaultdict
from typing import Iterable


class EvidenceStrength(Enum):
    WEAK = 1
    MODERATE = 2
    STRONG = 3


class CauseCategory(Enum):
    PEOPLE = "People"
    PROCESS = "Process"
    TECHNOLOGY = "Technology"
    DATA = "Data"
    ENVIRONMENT = "Environment"
    MANAGEMENT = "Management"


@dataclass(frozen=True)
class Evidence:
    observation: str
    source: str
    strength: EvidenceStrength


@dataclass
class Cause:
    statement: str
    category: CauseCategory
    evidence: list[Evidence] = field(default_factory=list)
    parent: "Cause | None" = None
    children: list["Cause"] = field(default_factory=list)

    @property
    def evidence_score(self) -> int:
        return sum(item.strength.value for item in self.evidence)

    def add_child(self, child: "Cause") -> None:
        child.parent = self
        self.children.append(child)

    def describe(self, level: int = 0) -> None:
        indent = "  " * level
        print(f"{indent}- [{self.category.value}] {self.statement}")
        for evidence in self.evidence:
            print(
                f"{indent}  Evidence: {evidence.observation} "
                f"({evidence.source}, {evidence.strength.name.lower()})"
            )
        for child in self.children:
            child.describe(level + 1)


@dataclass(frozen=True)
class WhyStep:
    question: str
    answer: str
    evidence: tuple[Evidence, ...]


@dataclass
class FiveWhys:
    problem: str
    steps: list[WhyStep] = field(default_factory=list)

    def add_step(
        self,
        question: str,
        answer: str,
        evidence: Iterable[Evidence],
    ) -> None:
        if not question.strip() or not answer.strip():
            raise ValueError("A Why step requires a non-empty question and answer.")
        self.steps.append(WhyStep(question, answer, tuple(evidence)))

    def validate(self) -> None:
        if not self.steps:
            raise ValueError("At least one Why step is required.")
        if len(self.steps) > 5:
            raise ValueError("Five Whys should contain no more than five causal levels.")

    def root_cause(self) -> str:
        self.validate()
        return self.steps[-1].answer


class RCA:
    def __init__(self, problem: str):
        if not problem.strip():
            raise ValueError("Problem statement cannot be empty.")
        self.problem = problem
        self.whys = FiveWhys(problem)
        self.fishbone: dict[CauseCategory, Cause] = {}
        self.hypotheses: list[Cause] = []

    def add_category(self, category: CauseCategory, cause: Cause) -> None:
        if cause.category != category:
            raise ValueError("Cause category does not match fishbone branch.")
        self.fishbone[category] = cause

    def rank_hypotheses(self) -> list[Cause]:
        return sorted(
            self.hypotheses,
            key=lambda cause: cause.evidence_score,
            reverse=True,
        )

    def diagnostic_report(self) -> None:
        print("\nROOT CAUSE ANALYSIS")
        print("=" * 70)
        print(f"Problem: {self.problem}")

        print("\n5 WHYS")
        print("-" * 70)
        for index, step in enumerate(self.whys.steps, start=1):
            print(f"Why {index}: {step.question}")
            print(f"Answer: {step.answer}")
            for evidence in step.evidence:
                print(f"  - {evidence.observation} [{evidence.source}]")

        print("\nFISHBONE ANALYSIS")
        print("-" * 70)
        for category in CauseCategory:
            branch = self.fishbone.get(category)
            if branch:
                branch.describe()

        print("\nRANKED HYPOTHESES")
        print("-" * 70)
        for position, hypothesis in enumerate(self.rank_hypotheses(), start=1):
            print(
                f"{position}. {hypothesis.statement} "
                f"| {hypothesis.category.value} "
                f"| evidence score={hypothesis.evidence_score}"
            )


def validate_measurements(
    before: list[float],
    after: list[float],
    expected_direction: str,
) -> bool:
    if not before or not after:
        raise ValueError("Both before and after measurements are required.")

    before_avg = sum(before) / len(before)
    after_avg = sum(after) / len(after)

    if expected_direction == "decrease":
        return after_avg < before_avg
    if expected_direction == "increase":
        return after_avg > before_avg
    if expected_direction == "stable":
        return abs(after_avg - before_avg) < 0.01

    raise ValueError("Unknown expected direction.")


def recurring_failure_analysis(events: list[str]) -> dict[str, int]:
    if not events:
        return {}

    normalized = [event.strip().lower() for event in events if event.strip()]
    return dict(Counter(normalized).most_common())


def build_incident_rca() -> RCA:
    incident = (
        "Production payment requests experienced a 17-minute failure window "
        "after a deployment."
    )

    rca = RCA(incident)

    rca.whys.add_step(
        "Why did payment requests fail?",
        "The payment service rejected requests because its database connection pool was exhausted.",
        [
            Evidence(
                "Connection-pool utilization reached 100%",
                "application metrics",
                EvidenceStrength.STRONG,
            )
        ],
    )

    rca.whys.add_step(
        "Why was the connection pool exhausted?",
        "A new endpoint opened database connections without reliably releasing them.",
        [
            Evidence(
                "Connection count increased continuously after deployment",
                "database telemetry",
                EvidenceStrength.STRONG,
            ),
            Evidence(
                "Code review identified missing resource cleanup",
                "source inspection",
                EvidenceStrength.MODERATE,
            ),
        ],
    )

    rca.whys.add_step(
        "Why could the endpoint reach production without reliable cleanup?",
        "The integration tests did not exercise repeated requests under connection-pressure conditions.",
        [
            Evidence(
                "Existing tests covered successful single requests",
                "test suite",
                EvidenceStrength.STRONG,
            )
        ],
    )

    rca.whys.add_step(
        "Why did testing omit connection-pressure behavior?",
        "The test strategy focused on functional responses and did not include resource-lifecycle acceptance criteria.",
        [
            Evidence(
                "No test asserted connection counts before and after repeated calls",
                "test design review",
                EvidenceStrength.STRONG,
            )
        ],
    )

    rca.whys.add_step(
        "Why were resource-lifecycle criteria absent?",
        "The engineering delivery process defined API behavior but did not explicitly require operational-resource checks for database-backed endpoints.",
        [
            Evidence(
                "Endpoint checklist contained functional but not resource-lifecycle controls",
                "engineering checklist",
                EvidenceStrength.MODERATE,
            )
        ],
    )

    people = Cause(
        "Developers understood API behavior but resource-lifecycle ownership was not explicit.",
        CauseCategory.PEOPLE,
        [
            Evidence(
                "No named reviewer criterion for connection lifecycle",
                "review checklist",
                EvidenceStrength.MODERATE,
            )
        ],
    )

    process = Cause(
        "Release acceptance did not require resource-lifecycle tests.",
        CauseCategory.PROCESS,
        [
            Evidence(
                "Deployment checklist omitted connection-pressure verification",
                "release checklist",
                EvidenceStrength.STRONG,
            )
        ],
    )

    technology = Cause(
        "The database client permitted connections to remain open until pool exhaustion.",
        CauseCategory.TECHNOLOGY,
        [
            Evidence(
                "Pool reached configured maximum",
                "database metrics",
                EvidenceStrength.STRONG,
            )
        ],
    )

    data = Cause(
        "Monitoring captured pool utilization but no automated release-rate anomaly.",
        CauseCategory.DATA,
        [
            Evidence(
                "Utilization alert triggered only after saturation",
                "monitoring configuration",
                EvidenceStrength.MODERATE,
            )
        ],
    )

    management = Cause(
        "Delivery objectives prioritized endpoint completion over operational resilience.",
        CauseCategory.MANAGEMENT,
        [
            Evidence(
                "Resource-lifecycle acceptance criterion was absent",
                "delivery specification",
                EvidenceStrength.MODERATE,
            )
        ],
    )

    rca.add_category(CauseCategory.PEOPLE, people)
    rca.add_category(CauseCategory.PROCESS, process)
    rca.add_category(CauseCategory.TECHNOLOGY, technology)
    rca.add_category(CauseCategory.DATA, data)
    rca.add_category(CauseCategory.MANAGEMENT, management)

    hypotheses = [
        process,
        technology,
        data,
        people,
        management,
    ]
    rca.hypotheses.extend(hypotheses)

    return rca


def demonstrate_causal_validation() -> None:
    before = [99, 103, 101, 100]
    after = [71, 69, 73, 70]

    reduced = validate_measurements(before, after, "decrease")
    print("\nCAUSAL VALIDATION")
    print("-" * 70)
    print(f"Average before: {sum(before) / len(before):.2f}")
    print(f"Average after : {sum(after) / len(after):.2f}")
    print(f"Observed reduction: {reduced}")

    events = [
        "connection leak",
        "timeout",
        "connection leak",
        "connection leak",
        "timeout",
        "slow query",
    ]

    print("\nRECURRING FAILURE SIGNALS")
    print("-" * 70)
    for event, count in recurring_failure_analysis(events).items():
        print(f"{event}: {count}")


def main() -> None:
    rca = build_incident_rca()
    rca.diagnostic_report()

    print("\nROOT CAUSE")
    print("-" * 70)
    print(rca.whys.root_cause())

    demonstrate_causal_validation()


if __name__ == "__main__":
    main()
