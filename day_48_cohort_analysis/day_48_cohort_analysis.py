from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import mean
from typing import Iterable


@dataclass(frozen=True)
class Customer:
    customer_id: str
    signup_date: date
    acquisition_channel: str
    plan: str


@dataclass(frozen=True)
class Event:
    customer_id: str
    event_date: date
    event_type: str
    revenue: float = 0.0


@dataclass
class CohortMetrics:
    cohort: str
    cohort_size: int
    retention: dict[int, float] = field(default_factory=dict)
    active_customers: dict[int, int] = field(default_factory=dict)
    revenue: dict[int, float] = field(default_factory=dict)


class CohortAnalyzer:
    """
    Cohort analysis groups customers by a shared starting event, usually
    acquisition or signup month, and follows behavior during later periods.

    This implementation uses monthly cohorts and monthly activity periods.
    """

    def __init__(self, customers: Iterable[Customer], events: Iterable[Event]):
        self.customers = list(customers)
        self.events = list(events)
        self.customer_by_id = {customer.customer_id: customer for customer in self.customers}

        if len(self.customer_by_id) != len(self.customers):
            raise ValueError("Customer IDs must be unique.")

        for event in self.events:
            if event.customer_id not in self.customer_by_id:
                raise ValueError(f"Event references unknown customer: {event.customer_id}")
            if event.revenue < 0:
                raise ValueError("Revenue cannot be negative.")

    @staticmethod
    def month_start(value: date) -> date:
        return value.replace(day=1)

    @staticmethod
    def month_label(value: date) -> str:
        return value.strftime("%Y-%m")

    @staticmethod
    def month_offset(start: date, current: date) -> int:
        return (current.year - start.year) * 12 + current.month - start.month

    def cohort_members(self) -> dict[str, set[str]]:
        cohorts: dict[str, set[str]] = defaultdict(set)

        for customer in self.customers:
            cohort = self.month_label(self.month_start(customer.signup_date))
            cohorts[cohort].add(customer.customer_id)

        return dict(sorted(cohorts.items()))

    def monthly_activity(self) -> dict[str, dict[int, set[str]]]:
        """
        Converts raw events into:
            cohort -> period number -> active customer IDs

        A customer counts as active once per period regardless of event count.
        This prevents high-frequency users from artificially inflating retention.
        """
        activity: dict[str, dict[int, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )

        for event in self.events:
            customer = self.customer_by_id[event.customer_id]
            cohort_start = self.month_start(customer.signup_date)
            event_month = self.month_start(event.event_date)

            offset = self.month_offset(cohort_start, event_month)

            if offset < 0:
                raise ValueError(
                    f"Event {event.event_type} occurs before signup for "
                    f"{event.customer_id}."
                )

            cohort = self.month_label(cohort_start)
            activity[cohort][offset].add(event.customer_id)

        return {
            cohort: dict(periods)
            for cohort, periods in activity.items()
        }

    def retention_table(self) -> list[CohortMetrics]:
        cohorts = self.cohort_members()
        activity = self.monthly_activity()
        results: list[CohortMetrics] = []

        for cohort, members in cohorts.items():
            size = len(members)
            metrics = CohortMetrics(cohort=cohort, cohort_size=size)

            for period, active_ids in activity.get(cohort, {}).items():
                active_count = len(active_ids)
                metrics.active_customers[period] = active_count
                metrics.retention[period] = active_count / size if size else 0.0

            results.append(metrics)

        return results

    def revenue_by_cohort(self) -> dict[str, dict[int, float]]:
        revenue: dict[str, dict[int, float]] = defaultdict(
            lambda: defaultdict(float)
        )

        for event in self.events:
            customer = self.customer_by_id[event.customer_id]
            cohort_start = self.month_start(customer.signup_date)
            event_month = self.month_start(event.event_date)
            period = self.month_offset(cohort_start, event_month)
            cohort = self.month_label(cohort_start)
            revenue[cohort][period] += event.revenue

        return {
            cohort: dict(periods)
            for cohort, periods in revenue.items()
        }

    def average_revenue_per_customer(self) -> dict[str, dict[int, float]]:
        revenue = self.revenue_by_cohort()
        cohorts = self.cohort_members()
        result: dict[str, dict[int, float]] = {}

        for cohort, periods in revenue.items():
            size = len(cohorts[cohort])
            result[cohort] = {
                period: amount / size
                for period, amount in periods.items()
            }

        return result

    def channel_cohorts(self) -> dict[str, dict[str, int]]:
        """
        Shows cohort size by acquisition channel. This helps separate
        retention differences caused by customer source from time effects.
        """
        result: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for customer in self.customers:
            cohort = self.month_label(self.month_start(customer.signup_date))
            result[cohort][customer.acquisition_channel] += 1

        return {cohort: dict(channels) for cohort, channels in result.items()}

    def plan_retention(self) -> dict[str, dict[int, float]]:
        """
        Calculates retention by subscription plan within each signup cohort.
        The denominator is the number of customers in that plan's cohort.
        """
        cohort_plan_members: dict[tuple[str, str], set[str]] = defaultdict(set)

        for customer in self.customers:
            cohort = self.month_label(self.month_start(customer.signup_date))
            cohort_plan_members[(cohort, customer.plan)].add(customer.customer_id)

        active: dict[tuple[str, str], dict[int, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )

        for event in self.events:
            customer = self.customer_by_id[event.customer_id]
            cohort = self.month_label(self.month_start(customer.signup_date))
            period = self.month_offset(
                self.month_start(customer.signup_date),
                self.month_start(event.event_date),
            )
            active[(cohort, customer.plan)][period].add(customer.customer_id)

        output: dict[str, dict[int, float]] = defaultdict(dict)

        for (cohort, plan), members in cohort_plan_members.items():
            for period, ids in active[(cohort, plan)].items():
                output[f"{cohort} / {plan}"][period] = len(ids) / len(members)

        return dict(output)

    def churn_after_inactivity(
        self,
        inactivity_months: int = 2,
    ) -> dict[str, float]:
        """
        A customer is considered churned when there is no activity for the
        configured number of consecutive months after the last observed event.

        This is a behavioral definition rather than a billing-system truth.
        """
        if inactivity_months <= 0:
            raise ValueError("inactivity_months must be positive.")

        activity_dates: dict[str, set[date]] = defaultdict(set)

        for event in self.events:
            activity_dates[event.customer_id].add(
                self.month_start(event.event_date)
            )

        churn_rate: dict[str, float] = {}

        for cohort, members in self.cohort_members().items():
            churned = 0

            for customer_id in members:
                customer = self.customer_by_id[customer_id]
                months = sorted(activity_dates.get(customer_id, set()))

                if not months:
                    churned += 1
                    continue

                last_active = months[-1]
                latest_possible = self.month_start(max(
                    event.event_date for event in self.events
                    if event.customer_id == customer_id
                ))

                inactivity = self.month_offset(last_active, latest_possible)

                if inactivity >= inactivity_months:
                    churned += 1

            churn_rate[cohort] = churned / len(members) if members else 0.0

        return churn_rate


def percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def print_retention(metrics: list[CohortMetrics]) -> None:
    print("\nRETENTION COHORT TABLE")
    print("=" * 72)

    periods = sorted({
        period
        for metric in metrics
        for period in metric.retention
    })

    header = ["Cohort", "Size"] + [f"M{period}" for period in periods]
    print(" | ".join(f"{item:>10}" for item in header))
    print("-" * 72)

    for metric in metrics:
        row = [
            metric.cohort,
            str(metric.cohort_size),
        ]

        for period in periods:
            row.append(
                percentage(metric.retention.get(period, 0.0))
            )

        print(" | ".join(f"{item:>10}" for item in row))


def print_revenue(analyzer: CohortAnalyzer) -> None:
    revenue = analyzer.revenue_by_cohort()

    print("\nCOHORT REVENUE")
    print("=" * 72)

    for cohort, periods in revenue.items():
        formatted = ", ".join(
            f"M{period}=${amount:,.2f}"
            for period, amount in sorted(periods.items())
        )
        print(f"{cohort}: {formatted}")


def print_plan_retention(analyzer: CohortAnalyzer) -> None:
    print("\nRETENTION BY PLAN")
    print("=" * 72)

    for group, periods in analyzer.plan_retention().items():
        formatted = ", ".join(
            f"M{period}={percentage(rate)}"
            for period, rate in sorted(periods.items())
        )
        print(f"{group}: {formatted}")


def demonstrate_statistics(metrics: list[CohortMetrics]) -> None:
    month_one_rates = [
        metric.retention[1]
        for metric in metrics
        if 1 in metric.retention
    ]

    if month_one_rates:
        print("\nM1 BENCHMARK")
        print("=" * 72)
        print(f"Average M1 retention: {percentage(mean(month_one_rates))}")
        print(
            f"Best M1 retention: {percentage(max(month_one_rates))}"
        )
        print(
            f"Worst M1 retention: {percentage(min(month_one_rates))}"
        )


def build_sample_data() -> tuple[list[Customer], list[Event]]:
    customers = [
        Customer("C001", date(2026, 1, 5), "organic", "pro"),
        Customer("C002", date(2026, 1, 12), "paid", "basic"),
        Customer("C003", date(2026, 1, 20), "referral", "pro"),
        Customer("C004", date(2026, 2, 3), "organic", "basic"),
        Customer("C005", date(2026, 2, 8), "paid", "pro"),
        Customer("C006", date(2026, 2, 18), "referral", "basic"),
        Customer("C007", date(2026, 3, 2), "organic", "pro"),
        Customer("C008", date(2026, 3, 11), "paid", "basic"),
        Customer("C009", date(2026, 3, 25), "referral", "pro"),
    ]

    events = [
        Event("C001", date(2026, 1, 5), "signup", 0),
        Event("C001", date(2026, 1, 8), "purchase", 49),
        Event("C001", date(2026, 2, 10), "login", 0),
        Event("C001", date(2026, 3, 9), "purchase", 49),
        Event("C002", date(2026, 1, 12), "signup", 0),
        Event("C002", date(2026, 1, 20), "purchase", 19),
        Event("C002", date(2026, 2, 5), "login", 0),
        Event("C003", date(2026, 1, 20), "signup", 0),
        Event("C003", date(2026, 1, 22), "purchase", 49),
        Event("C003", date(2026, 2, 15), "purchase", 49),
        Event("C003", date(2026, 3, 18), "login", 0),
        Event("C004", date(2026, 2, 3), "signup", 0),
        Event("C004", date(2026, 2, 5), "purchase", 19),
        Event("C004", date(2026, 3, 8), "login", 0),
        Event("C005", date(2026, 2, 8), "signup", 0),
        Event("C005", date(2026, 2, 9), "purchase", 49),
        Event("C005", date(2026, 3, 12), "purchase", 49),
        Event("C005", date(2026, 4, 3), "login", 0),
        Event("C006", date(2026, 2, 18), "signup", 0),
        Event("C006", date(2026, 2, 20), "purchase", 19),
        Event("C007", date(2026, 3, 2), "signup", 0),
        Event("C007", date(2026, 3, 4), "purchase", 49),
        Event("C007", date(2026, 4, 7), "login", 0),
        Event("C008", date(2026, 3, 11), "signup", 0),
        Event("C008", date(2026, 3, 13), "purchase", 19),
        Event("C009", date(2026, 3, 25), "signup", 0),
        Event("C009", date(2026, 3, 27), "purchase", 49),
        Event("C009", date(2026, 4, 10), "purchase", 49),
    ]

    return customers, events


def demonstrate_edge_cases() -> None:
    print("\nVALIDATION EXAMPLES")
    print("=" * 72)

    try:
        CohortAnalyzer(
            [Customer("X", date(2026, 5, 1), "organic", "pro")],
            [Event("X", date(2026, 4, 1), "login")],
        ).monthly_activity()
    except ValueError as exc:
        print(f"Pre-signup activity rejected: {exc}")

    try:
        CohortAnalyzer(
            [Customer("X", date(2026, 5, 1), "organic", "pro")],
            [Event("X", date(2026, 5, 2), "purchase", -10)],
        )
    except ValueError as exc:
        print(f"Negative revenue rejected: {exc}")

    try:
        CohortAnalyzer(
            [
                Customer("X", date(2026, 5, 1), "organic", "pro"),
                Customer("X", date(2026, 5, 2), "paid", "basic"),
            ],
            [],
        )
    except ValueError as exc:
        print(f"Duplicate customer rejected: {exc}")


def main() -> None:
    customers, events = build_sample_data()
    analyzer = CohortAnalyzer(customers, events)

    print("COHORT ANALYSIS: RETENTION AND CUSTOMER BEHAVIOR")
    print("=" * 72)
    print(
        "Customers are grouped by signup month. Each later month is evaluated "
        "using unique active customers rather than raw event counts."
    )

    print_retention(analyzer.retention_table())
    print_revenue(analyzer)
    print_plan_retention(analyzer)

    print("\nACQUISITION CHANNEL MIX")
    print("=" * 72)
    for cohort, channels in analyzer.channel_cohorts().items():
        details = ", ".join(
            f"{channel}={count}"
            for channel, count in sorted(channels.items())
        )
        print(f"{cohort}: {details}")

    print("\nINACTIVITY-BASED CHURN")
    print("=" * 72)
    for cohort, rate in analyzer.churn_after_inactivity(2).items():
        print(f"{cohort}: {percentage(rate)}")

    demonstrate_statistics(analyzer.retention_table())
    demonstrate_edge_cases()


if __name__ == "__main__":
    main()
