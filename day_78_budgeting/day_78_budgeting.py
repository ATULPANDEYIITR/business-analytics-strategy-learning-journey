#!/usr/bin/env python3
"""
BUDGET PREPARATION AND VARIANCE ANALYSIS

A self-contained budgeting and financial performance management system.

Features:
- Budget preparation and approval
- Revenue and expense forecasting
- Department-level budget allocation
- Fixed and variable cost modeling
- Monthly budget execution
- Actual-versus-budget variance analysis
- Favorable and unfavorable variance classification
- Flexible and static budget comparison
- Forecast revisions
- Budget utilization monitoring
- Financial controls and validation
- CSV reporting and JSON persistence
- Unit-style assertions and error handling

Compatible with Python 3.10+.
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Optional


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

LOGGER = logging.getLogger("budget_management")

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value: Decimal | int | float | str) -> Decimal:
    """Convert financial values into consistently rounded decimals."""
    try:
        result = Decimal(str(value)).quantize(
            CENT,
            rounding=ROUND_HALF_UP
        )
    except Exception as exc:
        raise ValueError(f"Invalid financial amount: {value}") from exc

    if not result.is_finite():
        raise ValueError("Financial amounts must be finite.")

    return result


def percentage(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator * Decimal("100")).quantize(
        CENT,
        rounding=ROUND_HALF_UP
    )


# ------------------------------------------------------------
# Domain definitions
# ------------------------------------------------------------

class BudgetType(Enum):
    STATIC = "STATIC"
    FLEXIBLE = "FLEXIBLE"
    ROLLING = "ROLLING"


class BudgetStatus(Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class CostBehavior(Enum):
    FIXED = "FIXED"
    VARIABLE = "VARIABLE"
    MIXED = "MIXED"


class VarianceStatus(Enum):
    FAVORABLE = "FAVORABLE"
    UNFAVORABLE = "UNFAVORABLE"
    ON_TARGET = "ON_TARGET"


class AccountType(Enum):
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


@dataclass(frozen=True)
class Department:
    department_id: str
    name: str
    annual_limit: Decimal

    def __post_init__(self):
        if not self.department_id.strip() or not self.name.strip():
            raise ValueError("Department identifiers and names are required.")
        if self.annual_limit < ZERO:
            raise ValueError("Department limit cannot be negative.")


@dataclass(frozen=True)
class BudgetLine:
    account_code: str
    description: str
    department_id: str
    account_type: AccountType
    cost_behavior: CostBehavior
    fixed_amount: Decimal = ZERO
    variable_rate: Decimal = ZERO
    expected_activity: Decimal = ZERO

    def __post_init__(self):
        if not self.account_code.strip():
            raise ValueError("Account code is required.")
        if not self.description.strip():
            raise ValueError("Account description is required.")
        if self.fixed_amount < ZERO:
            raise ValueError("Fixed amount cannot be negative.")
        if self.variable_rate < ZERO:
            raise ValueError("Variable rate cannot be negative.")
        if self.expected_activity < ZERO:
            raise ValueError("Expected activity cannot be negative.")

        if self.account_type == AccountType.REVENUE:
            if self.cost_behavior != CostBehavior.FIXED:
                raise ValueError(
                    "This model treats revenue separately from cost behavior."
                )


@dataclass
class Budget:
    budget_id: str
    fiscal_year: int
    budget_type: BudgetType
    currency: str = "INR"
    status: BudgetStatus = BudgetStatus.DRAFT
    lines: list[BudgetLine] = field(default_factory=list)
    revision: int = 1
    created_on: date = field(default_factory=date.today)

    def __post_init__(self):
        if not self.budget_id.strip():
            raise ValueError("Budget identifier is required.")
        if not 2000 <= self.fiscal_year <= 2200:
            raise ValueError("Invalid fiscal year.")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("Currency must be a three-letter code.")

    def add_line(self, line: BudgetLine) -> None:
        if self.status != BudgetStatus.DRAFT:
            raise ValueError("Only draft budgets can be modified.")

        if any(existing.account_code == line.account_code
               and existing.department_id == line.department_id
               for existing in self.lines):
            raise ValueError("Duplicate budget account and department.")

        self.lines.append(line)

    def total(self, account_type: AccountType) -> Decimal:
        return sum(
            (self.planned_amount(line)
             for line in self.lines
             if line.account_type == account_type),
            ZERO
        )

    def planned_amount(self, line: BudgetLine) -> Decimal:
        if line.account_type == AccountType.REVENUE:
            return line.fixed_amount

        if line.cost_behavior == CostBehavior.FIXED:
            return line.fixed_amount

        if line.cost_behavior == CostBehavior.VARIABLE:
            return money(line.variable_rate * line.expected_activity)

        return money(
            line.fixed_amount +
            line.variable_rate * line.expected_activity
        )

    @property
    def planned_profit(self) -> Decimal:
        return self.total(AccountType.REVENUE) - self.total(
            AccountType.EXPENSE
        )


@dataclass(frozen=True)
class ActualTransaction:
    transaction_id: str
    budget_id: str
    account_code: str
    department_id: str
    period: int
    amount: Decimal
    account_type: AccountType
    activity_units: Decimal = ZERO

    def __post_init__(self):
        if not all((
            self.transaction_id.strip(),
            self.budget_id.strip(),
            self.account_code.strip(),
            self.department_id.strip()
        )):
            raise ValueError("Transaction identifiers are required.")

        if not 1 <= self.period <= 12:
            raise ValueError("Period must be between 1 and 12.")

        if self.amount < ZERO or self.activity_units < ZERO:
            raise ValueError("Actual amounts and activity cannot be negative.")


@dataclass(frozen=True)
class VarianceResult:
    account_code: str
    department_id: str
    account_type: AccountType
    budget_amount: Decimal
    actual_amount: Decimal
    variance_amount: Decimal
    variance_percentage: Decimal
    status: VarianceStatus


# ------------------------------------------------------------
# Budget preparation
# ------------------------------------------------------------

class BudgetPreparationService:

    def __init__(self, departments: dict[str, Department]):
        self.departments = departments

    def validate_budget(self, budget: Budget) -> list[str]:
        errors = []

        if not budget.lines:
            errors.append("Budget contains no line items.")

        for line in budget.lines:
            department = self.departments.get(line.department_id)

            if department is None:
                errors.append(
                    f"Unknown department: {line.department_id}"
                )

        if errors:
            return errors

        department_totals: dict[str, Decimal] = {}

        for line in budget.lines:
            department_totals[line.department_id] = (
                department_totals.get(line.department_id, ZERO)
                + budget.planned_amount(line)
                if line.account_type == AccountType.EXPENSE
                else department_totals.get(line.department_id, ZERO)
            )

        for department_id, amount in department_totals.items():
            limit = self.departments[department_id].annual_limit

            if amount > limit:
                errors.append(
                    f"{department_id} exceeds its annual expense limit: "
                    f"{amount} > {limit}"
                )

        return errors

    def submit(self, budget: Budget) -> None:
        if budget.status != BudgetStatus.DRAFT:
            raise ValueError("Only draft budgets can be submitted.")

        errors = self.validate_budget(budget)

        if errors:
            raise ValueError("; ".join(errors))

        budget.status = BudgetStatus.SUBMITTED

    def approve(self, budget: Budget, approver: str) -> None:
        if budget.status != BudgetStatus.SUBMITTED:
            raise ValueError("Budget must be submitted before approval.")

        if not approver.strip():
            raise ValueError("An approver is required.")

        budget.status = BudgetStatus.APPROVED
        LOGGER.info("Budget %s approved by %s", budget.budget_id, approver)

    def reject(self, budget: Budget, reason: str) -> None:
        if budget.status != BudgetStatus.SUBMITTED:
            raise ValueError("Only submitted budgets can be rejected.")

        if not reason.strip():
            raise ValueError("A rejection reason is required.")

        budget.status = BudgetStatus.REJECTED

    def revise(
        self,
        budget: Budget,
        revised_lines: list[BudgetLine]
    ) -> Budget:
        if budget.status not in (
            BudgetStatus.APPROVED,
            BudgetStatus.REJECTED
        ):
            raise ValueError("Only approved or rejected budgets can be revised.")

        revised = Budget(
            budget_id=budget.budget_id,
            fiscal_year=budget.fiscal_year,
            budget_type=budget.budget_type,
            currency=budget.currency,
            revision=budget.revision + 1
        )

        for line in revised_lines:
            revised.add_line(line)

        errors = self.validate_budget(revised)

        if errors:
            raise ValueError("; ".join(errors))

        return revised


# ------------------------------------------------------------
# Actual transaction management
# ------------------------------------------------------------

class ActualLedger:

    def __init__(self):
        self.transactions: dict[str, ActualTransaction] = {}

    def record(
        self,
        transaction: ActualTransaction,
        budget: Budget
    ) -> None:
        if budget.status != BudgetStatus.APPROVED:
            raise ValueError("Transactions require an approved budget.")

        if transaction.budget_id != budget.budget_id:
            raise ValueError("Transaction references another budget.")

        if transaction.transaction_id in self.transactions:
            raise ValueError("Duplicate transaction identifier.")

        matching = [
            line for line in budget.lines
            if line.account_code == transaction.account_code
            and line.department_id == transaction.department_id
            and line.account_type == transaction.account_type
        ]

        if not matching:
            raise ValueError("Transaction does not match a budget line.")

        self.transactions[transaction.transaction_id] = transaction

    def aggregate(
        self,
        budget_id: str,
        account_code: str,
        department_id: str,
        account_type: AccountType,
        period: Optional[int] = None
    ) -> Decimal:

        return sum(
            (
                transaction.amount
                for transaction in self.transactions.values()
                if transaction.budget_id == budget_id
                and transaction.account_code == account_code
                and transaction.department_id == department_id
                and transaction.account_type == account_type
                and (period is None or transaction.period == period)
            ),
            ZERO
        )


# ------------------------------------------------------------
# Variance analysis
# ------------------------------------------------------------

class VarianceAnalyzer:

    @staticmethod
    def classify(
        account_type: AccountType,
        variance: Decimal
    ) -> VarianceStatus:

        if variance == ZERO:
            return VarianceStatus.ON_TARGET

        if account_type == AccountType.REVENUE:
            return (
                VarianceStatus.FAVORABLE
                if variance > ZERO
                else VarianceStatus.UNFAVORABLE
            )

        return (
            VarianceStatus.FAVORABLE
            if variance < ZERO
            else VarianceStatus.UNFAVORABLE
        )

    def analyze(
        self,
        budget: Budget,
        ledger: ActualLedger,
        period: Optional[int] = None
    ) -> list[VarianceResult]:

        if budget.status != BudgetStatus.APPROVED:
            raise ValueError("Variance analysis requires an approved budget.")

        results = []

        for line in budget.lines:
            if period is None:
                planned = budget.planned_amount(line)
            else:
                planned = money(
                    budget.planned_amount(line) / Decimal("12")
                )

            actual = ledger.aggregate(
                budget.budget_id,
                line.account_code,
                line.department_id,
                line.account_type,
                period
            )

            variance = money(actual - planned)

            results.append(
                VarianceResult(
                    account_code=line.account_code,
                    department_id=line.department_id,
                    account_type=line.account_type,
                    budget_amount=planned,
                    actual_amount=actual,
                    variance_amount=variance,
                    variance_percentage=percentage(
                        variance,
                        planned
                    ),
                    status=self.classify(
                        line.account_type,
                        variance
                    )
                )
            )

        return results

    @staticmethod
    def flexible_budget(
        line: BudgetLine,
        actual_activity: Decimal
    ) -> Decimal:
        if actual_activity < ZERO:
            raise ValueError("Activity cannot be negative.")

        if line.account_type == AccountType.REVENUE:
            raise ValueError(
                "Flexible expense budget is not applicable to revenue."
            )

        if line.cost_behavior == CostBehavior.FIXED:
            return line.fixed_amount

        if line.cost_behavior == CostBehavior.VARIABLE:
            return money(line.variable_rate * actual_activity)

        return money(
            line.fixed_amount +
            line.variable_rate * actual_activity
        )

    def analyze_flexible(
        self,
        budget: Budget,
        ledger: ActualLedger,
        period: int,
        activity_by_department: dict[str, Decimal]
    ) -> list[VarianceResult]:

        if not 1 <= period <= 12:
            raise ValueError("Period must be between 1 and 12.")

        results = []

        for line in budget.lines:
            if line.account_type == AccountType.REVENUE:
                continue

            activity = activity_by_department.get(
                line.department_id,
                ZERO
            )

            planned = self.flexible_budget(line, activity)

            actual = ledger.aggregate(
                budget.budget_id,
                line.account_code,
                line.department_id,
                AccountType.EXPENSE,
                period
            )

            variance = money(actual - planned)

            results.append(
                VarianceResult(
                    account_code=line.account_code,
                    department_id=line.department_id,
                    account_type=AccountType.EXPENSE,
                    budget_amount=planned,
                    actual_amount=actual,
                    variance_amount=variance,
                    variance_percentage=percentage(variance, planned),
                    status=self.classify(
                        AccountType.EXPENSE,
                        variance
                    )
                )
            )

        return results


# ------------------------------------------------------------
# Reporting
# ------------------------------------------------------------

class BudgetReporter:

    @staticmethod
    def print_variances(results: list[VarianceResult]) -> None:
        print("\nBUDGET VARIANCE REPORT")
        print("-" * 105)

        print(
            f"{'Account':<12}"
            f"{'Department':<14}"
            f"{'Budget':>15}"
            f"{'Actual':>15}"
            f"{'Variance':>15}"
            f"{'Variance %':>12}"
            f"  Status"
        )

        print("-" * 105)

        for result in results:
            print(
                f"{result.account_code:<12}"
                f"{result.department_id:<14}"
                f"{result.budget_amount:>15,.2f}"
                f"{result.actual_amount:>15,.2f}"
                f"{result.variance_amount:>15,.2f}"
                f"{result.variance_percentage:>12,.2f}"
                f"  {result.status.value}"
            )

    @staticmethod
    def department_summary(
        results: list[VarianceResult]
    ) -> dict[str, dict[str, Decimal]]:

        summary = {}

        for result in results:
            department = result.department_id

            if department not in summary:
                summary[department] = {
                    "budget": ZERO,
                    "actual": ZERO,
                    "variance": ZERO
                }

            summary[department]["budget"] += result.budget_amount
            summary[department]["actual"] += result.actual_amount
            summary[department]["variance"] += result.variance_amount

        return summary

    @staticmethod
    def export_csv(
        results: list[VarianceResult],
        filename: str
    ) -> None:

        path = Path(filename)

        if path.suffix.lower() != ".csv":
            raise ValueError("Report filename must end with .csv")

        fields = [
            "account_code",
            "department_id",
            "account_type",
            "budget_amount",
            "actual_amount",
            "variance_amount",
            "variance_percentage",
            "status"
        ]

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()

            for result in results:
                row = asdict(result)
                row["account_type"] = result.account_type.value
                row["status"] = result.status.value
                writer.writerow(row)

        LOGGER.info("CSV report exported to %s", path)


# ------------------------------------------------------------
# Budget utilization and forecasting
# ------------------------------------------------------------

def utilization_percentage(
    actual: Decimal,
    approved_budget: Decimal
) -> Decimal:

    if approved_budget <= ZERO:
        raise ValueError("Approved budget must be positive.")

    return percentage(actual, approved_budget)


def forecast_annual_expense(
    year_to_date_actual: Decimal,
    elapsed_months: int
) -> Decimal:

    if not 1 <= elapsed_months <= 12:
        raise ValueError("Elapsed months must be between 1 and 12.")

    if year_to_date_actual < ZERO:
        raise ValueError("Actual expenses cannot be negative.")

    return money(
        year_to_date_actual *
        Decimal("12") /
        Decimal(elapsed_months)
    )


# ------------------------------------------------------------
# JSON persistence
# ------------------------------------------------------------

def save_budget(budget: Budget, filename: str) -> None:
    """Persist budget data without losing decimal precision."""

    data = {
        "budget_id": budget.budget_id,
        "fiscal_year": budget.fiscal_year,
        "budget_type": budget.budget_type.value,
        "currency": budget.currency,
        "status": budget.status.value,
        "revision": budget.revision,
        "created_on": budget.created_on.isoformat(),
        "lines": [
            {
                **asdict(line),
                "account_type": line.account_type.value,
                "cost_behavior": line.cost_behavior.value,
                "fixed_amount": str(line.fixed_amount),
                "variable_rate": str(line.variable_rate),
                "expected_activity": str(line.expected_activity)
            }
            for line in budget.lines
        ]
    }

    path = Path(filename)
    temporary = path.with_suffix(path.suffix + ".tmp")

    try:
        temporary.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )
        temporary.replace(path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def load_budget(filename: str) -> Budget:
    data = json.loads(
        Path(filename).read_text(encoding="utf-8")
    )

    budget = Budget(
        budget_id=data["budget_id"],
        fiscal_year=int(data["fiscal_year"]),
        budget_type=BudgetType(data["budget_type"]),
        currency=data["currency"],
        status=BudgetStatus(data["status"]),
        revision=int(data["revision"]),
        created_on=date.fromisoformat(data["created_on"])
    )

    for item in data["lines"]:
        budget.lines.append(
            BudgetLine(
                account_code=item["account_code"],
                description=item["description"],
                department_id=item["department_id"],
                account_type=AccountType(item["account_type"]),
                cost_behavior=CostBehavior(item["cost_behavior"]),
                fixed_amount=money(item["fixed_amount"]),
                variable_rate=money(item["variable_rate"]),
                expected_activity=money(item["expected_activity"])
            )
        )

    return budget


# ------------------------------------------------------------
# Integrated demonstration
# ------------------------------------------------------------

def run_demo() -> None:

    departments = {
        "FIN": Department("FIN", "Finance", money(500000)),
        "OPS": Department("OPS", "Operations", money(900000)),
        "IT": Department("IT", "Information Technology", money(600000))
    }

    preparation = BudgetPreparationService(departments)

    budget = Budget(
        budget_id="BUDGET-2027",
        fiscal_year=2027,
        budget_type=BudgetType.FLEXIBLE
    )

    budget.add_line(
        BudgetLine(
            account_code="REV001",
            description="Service Revenue",
            department_id="FIN",
            account_type=AccountType.REVENUE,
            cost_behavior=CostBehavior.FIXED,
            fixed_amount=money(3000000)
        )
    )

    budget.add_line(
        BudgetLine(
            account_code="EXP001",
            description="Employee Salaries",
            department_id="FIN",
            account_type=AccountType.EXPENSE,
            cost_behavior=CostBehavior.FIXED,
            fixed_amount=money(360000)
        )
    )

    budget.add_line(
        BudgetLine(
            account_code="EXP002",
            description="Production Materials",
            department_id="OPS",
            account_type=AccountType.EXPENSE,
            cost_behavior=CostBehavior.VARIABLE,
            variable_rate=money(120),
            expected_activity=money(5000)
        )
    )

    budget.add_line(
        BudgetLine(
            account_code="EXP003",
            description="IT Infrastructure",
            department_id="IT",
            account_type=AccountType.EXPENSE,
            cost_behavior=CostBehavior.MIXED,
            fixed_amount=money(180000),
            variable_rate=money(20),
            expected_activity=money(5000)
        )
    )

    preparation.submit(budget)
    preparation.approve(budget, "Finance Controller")

    print("BUDGET PREPARATION")
    print("-" * 45)
    print("Budget:", budget.budget_id)
    print("Fiscal year:", budget.fiscal_year)
    print("Status:", budget.status.value)
    print("Revenue:", budget.total(AccountType.REVENUE))
    print("Expenses:", budget.total(AccountType.EXPENSE))
    print("Planned profit:", budget.planned_profit)

    ledger = ActualLedger()

    transactions = [
        ActualTransaction(
            "TX001", budget.budget_id, "REV001", "FIN",
            1, money(280000), AccountType.REVENUE
        ),
        ActualTransaction(
            "TX002", budget.budget_id, "EXP001", "FIN",
            1, money(30000), AccountType.EXPENSE
        ),
        ActualTransaction(
            "TX003", budget.budget_id, "EXP002", "OPS",
            1, money(55000), AccountType.EXPENSE,
            money(450)
        ),
        ActualTransaction(
            "TX004", budget.budget_id, "EXP003", "IT",
            1, money(19000), AccountType.EXPENSE,
            money(500)
        )
    ]

    for transaction in transactions:
        ledger.record(transaction, budget)

    analyzer = VarianceAnalyzer()

    annual_results = analyzer.analyze(budget, ledger)
    BudgetReporter.print_variances(annual_results)

    monthly_results = analyzer.analyze(
        budget,
        ledger,
        period=1
    )

    BudgetReporter.print_variances(monthly_results)

    flexible_results = analyzer.analyze_flexible(
        budget,
        ledger,
        period=1,
        activity_by_department={
            "OPS": money(450),
            "IT": money(500)
        }
    )

    print("\nFLEXIBLE BUDGET VARIANCE")
    BudgetReporter.print_variances(flexible_results)

    print("\nDEPARTMENT SUMMARY")

    for department, values in BudgetReporter.department_summary(
        annual_results
    ).items():
        print(
            department,
            {
                key: str(value)
                for key, value in values.items()
            }
        )

    print("\nBUDGET UTILIZATION")
    ops_budget = budget.planned_amount(
        next(line for line in budget.lines if line.account_code == "EXP002")
    )

    ops_utilization = utilization_percentage(
        money(55000),
        ops_budget
    )

    print("Operations utilization:", f"{ops_utilization}%")

    print("\nANNUAL FORECAST")
    print(
        "Projected annual operations expense:",
        forecast_annual_expense(money(55000), 1)
    )

    save_budget(budget, "budget_2027.json")
    restored = load_budget("budget_2027.json")

    assert restored.budget_id == budget.budget_id
    assert restored.planned_profit == budget.planned_profit

    BudgetReporter.export_csv(
        monthly_results,
        "budget_variance_report.csv"
    )

    print("\nVALIDATION TESTS")

    assert money("100.125") == money("100.13")
    assert percentage(money(25), money(100)) == money(25)

    assert analyzer.classify(
        AccountType.REVENUE,
        money(100)
    ) == VarianceStatus.FAVORABLE

    assert analyzer.classify(
        AccountType.EXPENSE,
        money(100)
    ) == VarianceStatus.UNFAVORABLE

    try:
        ledger.record(transactions[0], budget)
    except ValueError:
        print("Duplicate transaction correctly rejected.")

    try:
        utilization_percentage(money(100), ZERO)
    except ValueError:
        print("Zero-budget utilization correctly rejected.")

    print("All validation assertions passed.")
    print("Budgeting demonstration completed.")


if __name__ == "__main__":
    try:
        run_demo()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        LOGGER.error("Budget management failure: %s", exc)
        raise SystemExit(1)
