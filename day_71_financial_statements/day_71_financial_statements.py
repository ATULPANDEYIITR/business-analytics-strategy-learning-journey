"""
FINANCIAL STATEMENTS: INCOME STATEMENT, BALANCE SHEET AND CASH FLOW

A self-contained financial reporting and accounting simulation.

Features:
- Double-entry bookkeeping
- Chart of accounts
- Journal entries and ledger validation
- Income statement
- Balance sheet
- Cash flow statement using the indirect method
- Retained earnings reconciliation
- Financial ratios
- Accounting equation validation
- JSON report export
- Error handling and automated assertions

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

ZERO = Decimal("0.00")


def money(value: str | int | float | Decimal) -> Decimal:
    """Convert monetary values into exact two-decimal amounts."""
    result = Decimal(str(value)).quantize(Decimal("0.01"))
    return result


class AccountType(Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"
    CONTRA_ASSET = "contra_asset"


class StatementType(Enum):
    INCOME = "income_statement"
    BALANCE = "balance_sheet"
    CASH_FLOW = "cash_flow_statement"


@dataclass(frozen=True)
class Account:
    code: str
    name: str
    account_type: AccountType
    cash_flow_category: Optional[str] = None


@dataclass(frozen=True)
class JournalLine:
    account_code: str
    debit: Decimal = ZERO
    credit: Decimal = ZERO

    def __post_init__(self):
        if self.debit < ZERO or self.credit < ZERO:
            raise ValueError("Debit and credit cannot be negative.")

        if (self.debit > ZERO) == (self.credit > ZERO):
            raise ValueError(
                "Each journal line must contain exactly one positive debit or credit."
            )


@dataclass
class JournalEntry:
    entry_id: str
    description: str
    lines: list[JournalLine]

    def validate(self, accounts: dict[str, Account]) -> None:
        if not self.lines:
            raise ValueError("Journal entry cannot be empty.")

        if sum((line.debit for line in self.lines), ZERO) != sum(
            (line.credit for line in self.lines), ZERO
        ):
            raise ValueError(f"Unbalanced journal entry: {self.entry_id}")

        for line in self.lines:
            if line.account_code not in accounts:
                raise ValueError(
                    f"Unknown account: {line.account_code}"
                )


@dataclass
class FinancialStatements:
    income_statement: dict = field(default_factory=dict)
    balance_sheet: dict = field(default_factory=dict)
    cash_flow_statement: dict = field(default_factory=dict)
    ratios: dict = field(default_factory=dict)


class AccountingSystem:
    def __init__(self, company_name: str):
        if not company_name.strip():
            raise ValueError("Company name is required.")

        self.company_name = company_name
        self.accounts: dict[str, Account] = {}
        self.entries: list[JournalEntry] = []
        self.entry_ids: set[str] = set()

    def add_account(
        self,
        code: str,
        name: str,
        account_type: AccountType,
        cash_flow_category: Optional[str] = None
    ) -> None:
        if code in self.accounts:
            raise ValueError(f"Duplicate account code: {code}")

        if not code.strip() or not name.strip():
            raise ValueError("Account code and name are required.")

        self.accounts[code] = Account(
            code, name, account_type, cash_flow_category
        )

    def post(self, entry: JournalEntry) -> None:
        if entry.entry_id in self.entry_ids:
            raise ValueError("Duplicate journal entry ID.")

        entry.validate(self.accounts)

        # Entries are stored only after complete validation.
        self.entries.append(entry)
        self.entry_ids.add(entry.entry_id)

    def ledger(self) -> dict[str, Decimal]:
        balances = {
            code: ZERO for code in self.accounts
        }

        for entry in self.entries:
            for line in entry.lines:
                account = self.accounts[line.account_code]

                if account.account_type in (
                    AccountType.ASSET,
                    AccountType.EXPENSE,
                    AccountType.CONTRA_ASSET
                ):
                    balances[line.account_code] += (
                        line.debit - line.credit
                    )
                else:
                    balances[line.account_code] += (
                        line.credit - line.debit
                    )

        return balances

    def account_balance(
        self,
        balances: dict[str, Decimal],
        code: str
    ) -> Decimal:
        return balances.get(code, ZERO)

    def total(
        self,
        balances: dict[str, Decimal],
        account_type: AccountType
    ) -> Decimal:
        return sum(
            (
                balances[code]
                for code, account in self.accounts.items()
                if account.account_type == account_type
            ),
            ZERO
        )

    def build_statements(self) -> FinancialStatements:
        balances = self.ledger()

        def get(code: str) -> Decimal:
            return self.account_balance(balances, code)

        # Income statement.
        revenue = get("4000")
        cogs = get("5000")
        operating_expense = get("5100")
        depreciation = get("5200")
        interest = get("5300")
        tax = get("5400")

        gross_profit = revenue - cogs
        operating_income = gross_profit - operating_expense - depreciation
        pretax_income = operating_income - interest
        net_income = pretax_income - tax

        # Balance sheet.
        cash = get("1000")
        receivables = get("1100")
        inventory = get("1200")
        equipment = get("1500")
        accumulated_depreciation = get("1590")

        current_assets = cash + receivables + inventory
        fixed_assets = equipment - accumulated_depreciation
        total_assets = current_assets + fixed_assets

        accounts_payable = get("2000")
        tax_payable = get("2100")
        loan = get("2500")

        total_liabilities = accounts_payable + tax_payable + loan

        contributed_capital = get("3000")
        dividends = get("3100")

        # Retained earnings are derived from current-period activity.
        retained_earnings = net_income - dividends
        total_equity = contributed_capital + retained_earnings

        # Indirect cash flow statement.
        # All changes are measured against a zero opening balance.
        operating_cash_flow = (
            net_income
            + depreciation
            - receivables
            - inventory
            + accounts_payable
            + tax_payable
        )

        investing_cash_flow = -equipment

        financing_cash_flow = (
            contributed_capital + loan - dividends
        )

        net_change_cash = (
            operating_cash_flow
            + investing_cash_flow
            + financing_cash_flow
        )

        if total_assets != total_liabilities + total_equity:
            raise ArithmeticError("Balance sheet does not balance.")

        if net_change_cash != cash:
            raise ArithmeticError(
                "Cash flow statement does not reconcile with cash."
            )

        income_statement = {
            "revenue": revenue,
            "cost_of_goods_sold": cogs,
            "gross_profit": gross_profit,
            "operating_expenses": operating_expense,
            "depreciation": depreciation,
            "operating_income": operating_income,
            "interest_expense": interest,
            "pretax_income": pretax_income,
            "tax_expense": tax,
            "net_income": net_income
        }

        balance_sheet = {
            "cash": cash,
            "accounts_receivable": receivables,
            "inventory": inventory,
            "current_assets": current_assets,
            "equipment": equipment,
            "accumulated_depreciation": accumulated_depreciation,
            "net_fixed_assets": fixed_assets,
            "total_assets": total_assets,
            "accounts_payable": accounts_payable,
            "tax_payable": tax_payable,
            "long_term_debt": loan,
            "total_liabilities": total_liabilities,
            "contributed_capital": contributed_capital,
            "retained_earnings": retained_earnings,
            "total_equity": total_equity,
            "total_liabilities_and_equity": (
                total_liabilities + total_equity
            )
        }

        cash_flow_statement = {
            "net_income": net_income,
            "depreciation_adjustment": depreciation,
            "increase_in_receivables": -receivables,
            "increase_in_inventory": -inventory,
            "increase_in_payables": accounts_payable,
            "increase_in_tax_payable": tax_payable,
            "operating_cash_flow": operating_cash_flow,
            "investing_cash_flow": investing_cash_flow,
            "financing_cash_flow": financing_cash_flow,
            "net_change_in_cash": net_change_cash,
            "opening_cash": ZERO,
            "closing_cash": cash
        }

        ratios = {
            "current_ratio": (
                current_assets / (accounts_payable + tax_payable)
                if accounts_payable + tax_payable else None
            ),
            "debt_to_equity": (
                total_liabilities / total_equity
                if total_equity else None
            ),
            "gross_profit_margin": (
                gross_profit / revenue * 100 if revenue else ZERO
            ),
            "net_profit_margin": (
                net_income / revenue * 100 if revenue else ZERO
            ),
            "return_on_assets": (
                net_income / total_assets * 100
                if total_assets else ZERO
            )
        }

        return FinancialStatements(
            income_statement,
            balance_sheet,
            cash_flow_statement,
            ratios
        )

    def export_json(
        self,
        statements: FinancialStatements,
        filename: str = "financial_statements.json"
    ) -> None:
        def serialize(value):
            if isinstance(value, Decimal):
                return str(value)
            return value

        payload = {
            "company": self.company_name,
            "income_statement": {
                k: serialize(v)
                for k, v in statements.income_statement.items()
            },
            "balance_sheet": {
                k: serialize(v)
                for k, v in statements.balance_sheet.items()
            },
            "cash_flow_statement": {
                k: serialize(v)
                for k, v in statements.cash_flow_statement.items()
            },
            "ratios": {
                k: serialize(v)
                for k, v in statements.ratios.items()
            }
        }

        Path(filename).write_text(
            json.dumps(payload, indent=4),
            encoding="utf-8"
        )


def create_entry(entry_id, description, *lines):
    return JournalEntry(entry_id, description, list(lines))


def sample_system() -> AccountingSystem:
    system = AccountingSystem("Apex Manufacturing Private Limited")

    accounts = [
        ("1000", "Cash and Bank", AccountType.ASSET),
        ("1100", "Accounts Receivable", AccountType.ASSET),
        ("1200", "Inventory", AccountType.ASSET),
        ("1500", "Equipment", AccountType.ASSET),
        ("1590", "Accumulated Depreciation", AccountType.CONTRA_ASSET),
        ("2000", "Accounts Payable", AccountType.LIABILITY),
        ("2100", "Tax Payable", AccountType.LIABILITY),
        ("2500", "Long-Term Loan", AccountType.LIABILITY),
        ("3000", "Share Capital", AccountType.EQUITY),
        ("3100", "Dividends", AccountType.EQUITY),
        ("4000", "Sales Revenue", AccountType.REVENUE),
        ("5000", "Cost of Goods Sold", AccountType.EXPENSE),
        ("5100", "Operating Expenses", AccountType.EXPENSE),
        ("5200", "Depreciation Expense", AccountType.EXPENSE),
        ("5300", "Interest Expense", AccountType.EXPENSE),
        ("5400", "Income Tax Expense", AccountType.EXPENSE)
    ]

    for code, name, account_type in accounts:
        system.add_account(code, name, account_type)

    entries = [
        create_entry(
            "JE001", "Issue of share capital",
            JournalLine("1000", debit=money(100000)),
            JournalLine("3000", credit=money(100000))
        ),
        create_entry(
            "JE002", "Cash sales",
            JournalLine("1000", debit=money(120000)),
            JournalLine("4000", credit=money(120000))
        ),
        create_entry(
            "JE003", "Credit sales",
            JournalLine("1100", debit=money(30000)),
            JournalLine("4000", credit=money(30000))
        ),
        create_entry(
            "JE004", "Purchase inventory on credit",
            JournalLine("1200", debit=money(40000)),
            JournalLine("2000", credit=money(40000))
        ),
        create_entry(
            "JE005", "Cash inventory purchase",
            JournalLine("1200", debit=money(25000)),
            JournalLine("1000", credit=money(25000))
        ),
        create_entry(
            "JE006", "Record cost of goods sold",
            JournalLine("5000", debit=money(60000)),
            JournalLine("1200", credit=money(60000))
        ),
        create_entry(
            "JE007", "Operating expenses paid",
            JournalLine("5100", debit=money(25000)),
            JournalLine("1000", credit=money(25000))
        ),
        create_entry(
            "JE008", "Equipment acquisition",
            JournalLine("1500", debit=money(50000)),
            JournalLine("1000", credit=money(50000))
        ),
        create_entry(
            "JE009", "Depreciation adjustment",
            JournalLine("5200", debit=money(5000)),
            JournalLine("1590", credit=money(5000))
        ),
        create_entry(
            "JE010", "Interest payment",
            JournalLine("5300", debit=money(2000)),
            JournalLine("1000", credit=money(2000))
        ),
        create_entry(
            "JE011", "Income tax provision",
            JournalLine("5400", debit=money(8000)),
            JournalLine("2100", credit=money(8000))
        ),
        create_entry(
            "JE012", "Collection from customers",
            JournalLine("1000", debit=money(20000)),
            JournalLine("1100", credit=money(20000))
        ),
        create_entry(
            "JE013", "Payment to suppliers",
            JournalLine("2000", debit=money(15000)),
            JournalLine("1000", credit=money(15000))
        ),
        create_entry(
            "JE014", "Bank loan received",
            JournalLine("1000", debit=money(30000)),
            JournalLine("2500", credit=money(30000))
        ),
        create_entry(
            "JE015", "Dividend distribution",
            JournalLine("3100", debit=money(5000)),
            JournalLine("1000", credit=money(5000))
        )
    ]

    for entry in entries:
        system.post(entry)

    return system


def display_statement(title: str, data: dict) -> None:
    print(f"\n{'=' * 65}")
    print(title)
    print("=" * 65)

    for name, value in data.items():
        if isinstance(value, Decimal):
            formatted = f"{value:,.2f}"
        elif isinstance(value, float):
            formatted = f"{value:,.2f}"
        elif value is None:
            formatted = "Not meaningful"
        else:
            formatted = str(value)

        print(f"{name.replace('_', ' ').title():40} {formatted:>20}")


def run_tests(system: AccountingSystem) -> None:
    statements = system.build_statements()

    assert statements.income_statement["revenue"] == money(150000)
    assert statements.income_statement["net_income"] == money(50000)
    assert statements.balance_sheet["total_assets"] == money(208000)
    assert statements.balance_sheet["total_liabilities"] == money(63000)
    assert statements.balance_sheet["total_equity"] == money(145000)
    assert statements.cash_flow_statement["operating_cash_flow"] == money(73000)
    assert statements.cash_flow_statement["net_change_in_cash"] == money(148000)

    try:
        system.post(
            JournalEntry(
                "INVALID",
                "Unbalanced transaction",
                [
                    JournalLine("1000", debit=money(100)),
                    JournalLine("4000", credit=money(50))
                ]
            )
        )
        raise AssertionError("Unbalanced entry was accepted.")
    except ValueError:
        pass

    try:
        system.post(
            JournalEntry(
                "INVALID2",
                "Unknown account",
                [
                    JournalLine("9999", debit=money(100)),
                    JournalLine("4000", credit=money(100))
                ]
            )
        )
        raise AssertionError("Unknown account was accepted.")
    except ValueError:
        pass

    print("\nAll accounting validation tests passed.")


def main():
    system = sample_system()
    statements = system.build_statements()

    print(f"\nCOMPANY: {system.company_name}")
    print(f"POSTED JOURNAL ENTRIES: {len(system.entries)}")

    display_statement("INCOME STATEMENT", statements.income_statement)
    display_statement("BALANCE SHEET", statements.balance_sheet)
    display_statement("CASH FLOW STATEMENT", statements.cash_flow_statement)
    display_statement("FINANCIAL RATIOS", statements.ratios)

    run_tests(system)

    system.export_json(statements)
    logging.info("Financial statements exported successfully.")


if __name__ == "__main__":
    main()
