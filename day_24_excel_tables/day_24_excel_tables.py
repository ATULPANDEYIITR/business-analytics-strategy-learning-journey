"""
Excel Tables: Structured Data and Dynamic Calculations

A standalone study script demonstrating the concepts behind Excel Tables,
structured data, calculated columns, dynamic references, filtering,
aggregation, validation, and production-oriented table design.

The script uses only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable, Iterable, Iterator, Sequence
import csv
import io
import statistics
import time


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL CONCEPTS
# ---------------------------------------------------------------------------
# An Excel Table is a structured range of related records with:
# - a header row,
# - records (data rows),
# - named columns,
# - automatic expansion,
# - formulas that can propagate through calculated columns,
# - filtering and sorting,
# - structured references such as Table1[Amount].
#
# Python does not implement Excel's UI or formula engine here. Instead,
# ordinary Python data structures model the same underlying ideas:
# structured records, named fields, dynamic calculations, filtering,
# aggregation, and automatic propagation of derived values.


@dataclass
class SalesRecord:
    order_id: int
    customer: str
    region: str
    product: str
    quantity: int
    unit_price: Decimal
    discount_rate: Decimal
    order_date: date

    @property
    def gross_amount(self) -> Decimal:
        return self.unit_price * self.quantity

    @property
    def discount_amount(self) -> Decimal:
        return self.gross_amount * self.discount_rate

    @property
    def net_amount(self) -> Decimal:
        return self.gross_amount - self.discount_amount


def money(value: Decimal) -> Decimal:
    """Round currency consistently to two decimal places."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def demonstrate_basic_table():
    print("\n=== 1. BASIC STRUCTURED DATA ===")

    rows = [
        SalesRecord(
            1001, "Asha", "North", "Laptop", 2,
            Decimal("75000"), Decimal("0.05"), date(2026, 9, 1)
        ),
        SalesRecord(
            1002, "Ravi", "South", "Monitor", 3,
            Decimal("18000"), Decimal("0.10"), date(2026, 9, 2)
        ),
        SalesRecord(
            1003, "Meera", "North", "Keyboard", 5,
            Decimal("2500"), Decimal("0.00"), date(2026, 9, 3)
        ),
    ]

    for row in rows:
        print(
            row.order_id,
            row.customer,
            row.product,
            f"net={money(row.net_amount)}"
        )


# ---------------------------------------------------------------------------
# 2. A TABLE ABSTRACTION
# ---------------------------------------------------------------------------

class StructuredTable:
    """
    A small table abstraction.

    It models important Excel Table concepts:
    - stable column names,
    - rows represented as dictionaries,
    - dynamic row insertion,
    - calculated columns,
    - filtering,
    - sorting,
    - aggregation,
    - selection of named columns.
    """

    def __init__(self, columns: Sequence[str], rows: Iterable[dict] = ()):
        self.columns = list(columns)
        self.rows: list[dict] = []

        if len(set(self.columns)) != len(self.columns):
            raise ValueError("Column names must be unique.")

        for row in rows:
            self.add_row(row)

    def add_row(self, row: dict) -> None:
        missing = set(self.columns) - set(row)
        extra = set(row) - set(self.columns)

        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        if extra:
            raise ValueError(f"Unknown columns: {sorted(extra)}")

        self.rows.append({column: row[column] for column in self.columns})

    def add_rows(self, rows: Iterable[dict]) -> None:
        for row in rows:
            self.add_row(row)

    def calculated_column(
        self,
        column_name: str,
        calculation: Callable[[dict], object],
    ) -> None:
        """Equivalent to an Excel calculated column."""
        if column_name not in self.columns:
            self.columns.append(column_name)

        for row in self.rows:
            row[column_name] = calculation(row)

    def select(self, *column_names: str) -> list[dict]:
        for name in column_names:
            if name not in self.columns:
                raise KeyError(f"Unknown column: {name}")

        return [
            {name: row[name] for name in column_names}
            for row in self.rows
        ]

    def filter(self, predicate: Callable[[dict], bool]) -> "StructuredTable":
        return StructuredTable(
            self.columns,
            (row for row in self.rows if predicate(row)),
        )

    def sort(
        self,
        column_name: str,
        reverse: bool = False,
    ) -> "StructuredTable":
        if column_name not in self.columns:
            raise KeyError(f"Unknown column: {column_name}")

        return StructuredTable(
            self.columns,
            sorted(
                self.rows,
                key=lambda row: row[column_name],
                reverse=reverse,
            ),
        )

    def sum(self, column_name: str) -> Decimal:
        values = [row[column_name] for row in self.rows]
        return sum(values, Decimal("0"))

    def average(self, column_name: str) -> Decimal:
        values = [row[column_name] for row in self.rows]
        if not values:
            raise ValueError("Cannot average an empty table.")
        return sum(values, Decimal("0")) / len(values)

    def count(self) -> int:
        return len(self.rows)

    def unique(self, column_name: str) -> list:
        if column_name not in self.columns:
            raise KeyError(column_name)

        seen = []
        for row in self.rows:
            value = row[column_name]
            if value not in seen:
                seen.append(value)
        return seen

    def group_sum(
        self,
        group_column: str,
        value_column: str,
    ) -> dict:
        result = {}
        for row in self.rows:
            key = row[group_column]
            result[key] = result.get(key, Decimal("0")) + row[value_column]
        return result

    def to_csv(self) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.columns)
        writer.writeheader()
        writer.writerows(self.rows)
        return output.getvalue()

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[dict]:
        return iter(self.rows)


# ---------------------------------------------------------------------------
# 3. SAMPLE SALES TABLE
# ---------------------------------------------------------------------------

def build_sales_table() -> StructuredTable:
    columns = [
        "Order ID",
        "Customer",
        "Region",
        "Product",
        "Category",
        "Quantity",
        "Unit Price",
        "Discount Rate",
        "Order Date",
    ]

    rows = [
        {
            "Order ID": 1001,
            "Customer": "Asha",
            "Region": "North",
            "Product": "Laptop",
            "Category": "Computers",
            "Quantity": 2,
            "Unit Price": Decimal("75000"),
            "Discount Rate": Decimal("0.05"),
            "Order Date": date(2026, 9, 1),
        },
        {
            "Order ID": 1002,
            "Customer": "Ravi",
            "Region": "South",
            "Product": "Monitor",
            "Category": "Displays",
            "Quantity": 3,
            "Unit Price": Decimal("18000"),
            "Discount Rate": Decimal("0.10"),
            "Order Date": date(2026, 9, 2),
        },
        {
            "Order ID": 1003,
            "Customer": "Meera",
            "Region": "North",
            "Product": "Keyboard",
            "Category": "Accessories",
            "Quantity": 5,
            "Unit Price": Decimal("2500"),
            "Discount Rate": Decimal("0"),
            "Order Date": date(2026, 9, 3),
        },
        {
            "Order ID": 1004,
            "Customer": "Kabir",
            "Region": "West",
            "Product": "Laptop",
            "Category": "Computers",
            "Quantity": 1,
            "Unit Price": Decimal("82000"),
            "Discount Rate": Decimal("0.08"),
            "Order Date": date(2026, 9, 4),
        },
        {
            "Order ID": 1005,
            "Customer": "Neha",
            "Region": "East",
            "Product": "Mouse",
            "Category": "Accessories",
            "Quantity": 10,
            "Unit Price": Decimal("1200"),
            "Discount Rate": Decimal("0.02"),
            "Order Date": date(2026, 9, 5),
        },
    ]

    return StructuredTable(columns, rows)


def add_sales_calculated_columns(table: StructuredTable) -> None:
    # Excel equivalent:
    # =[@Quantity]*[@[Unit Price]]
    table.calculated_column(
        "Gross Amount",
        lambda row: money(
            row["Quantity"] * row["Unit Price"]
        ),
    )

    # Excel equivalent:
    # =[@[Gross Amount]]*[@[Discount Rate]]
    table.calculated_column(
        "Discount Amount",
        lambda row: money(
            row["Gross Amount"] * row["Discount Rate"]
        ),
    )

    # Excel equivalent:
    # =[@[Gross Amount]]-[@[Discount Amount]]
    table.calculated_column(
        "Net Amount",
        lambda row: money(
            row["Gross Amount"] - row["Discount Amount"]
        ),
    )

    # Example of a conditional calculated column:
    # =IF([@[Net Amount]]>=100000,"Large","Standard")
    table.calculated_column(
        "Order Size",
        lambda row: (
            "Large"
            if row["Net Amount"] >= Decimal("100000")
            else "Standard"
        ),
    )


# ---------------------------------------------------------------------------
# 4. DYNAMIC TABLE BEHAVIOR
# ---------------------------------------------------------------------------

def demonstrate_dynamic_expansion():
    print("\n=== 2. DYNAMIC ROW EXPANSION AND CALCULATED COLUMNS ===")

    table = build_sales_table()
    add_sales_calculated_columns(table)

    print(f"Initial row count: {len(table)}")

    # Adding a record changes the table's data set.
    # A calculated-column definition can then be reapplied to new rows.
    table.add_row({
        "Order ID": 1006,
        "Customer": "Arjun",
        "Region": "South",
        "Product": "Tablet",
        "Category": "Computers",
        "Quantity": 4,
        "Unit Price": Decimal("30000"),
        "Discount Rate": Decimal("0.05"),
        "Order Date": date(2026, 9, 6),
        "Gross Amount": Decimal("0"),
        "Discount Amount": Decimal("0"),
        "Net Amount": Decimal("0"),
        "Order Size": "Pending",
    })

    # Recalculate all derived values after expansion.
    add_sales_calculated_columns(table)

    print(f"Expanded row count: {len(table)}")

    for row in table:
        print(
            row["Order ID"],
            row["Product"],
            money(row["Net Amount"]),
            row["Order Size"],
        )


# ---------------------------------------------------------------------------
# 5. STRUCTURED REFERENCE IDEAS
# ---------------------------------------------------------------------------

def demonstrate_structured_reference_equivalents():
    print("\n=== 3. STRUCTURED REFERENCE EQUIVALENTS ===")

    table = build_sales_table()
    add_sales_calculated_columns(table)

    # Excel-style references conceptually map as follows:
    #
    # Table1[Net Amount]
    # -> every value in the "Net Amount" column
    #
    # Table1[[#Headers],[Net Amount]]
    # -> the column header
    #
    # Table1[@[Net Amount]]
    # -> the current row's Net Amount
    #
    # Table1[[#Data],[Net Amount]]
    # -> data cells in the Net Amount column
    #
    # Table1[#All]
    # -> headers + data + totals, if present

    net_amounts = [row["Net Amount"] for row in table]
    print("Table-like column reference:", net_amounts)
    print("Total:", money(sum(net_amounts, Decimal("0"))))


# ---------------------------------------------------------------------------
# 6. FILTERING AND MULTI-CONDITION LOGIC
# ---------------------------------------------------------------------------

def demonstrate_filtering():
    print("\n=== 4. FILTERING ===")

    table = build_sales_table()
    add_sales_calculated_columns(table)

    north_orders = table.filter(
        lambda row: row["Region"] == "North"
    )

    high_value = table.filter(
        lambda row: row["Net Amount"] >= Decimal("50000")
    )

    north_high_value = table.filter(
        lambda row:
        row["Region"] == "North"
        and row["Net Amount"] >= Decimal("50000")
    )

    print("North:", [r["Order ID"] for r in north_orders])
    print("High value:", [r["Order ID"] for r in high_value])
    print(
        "North + high value:",
        [r["Order ID"] for r in north_high_value],
    )


# ---------------------------------------------------------------------------
# 7. SORTING AND DYNAMIC ORDERING
# ---------------------------------------------------------------------------

def demonstrate_sorting():
    print("\n=== 5. SORTING ===")

    table = build_sales_table()
    add_sales_calculated_columns(table)

    descending = table.sort("Net Amount", reverse=True)

    for row in descending:
        print(row["Order ID"], money(row["Net Amount"]))


# ---------------------------------------------------------------------------
# 8. AGGREGATION
# ---------------------------------------------------------------------------

def demonstrate_aggregation():
    print("\n=== 6. AGGREGATION ===")

    table = build_sales_table()
    add_sales_calculated_columns(table)

    total_sales = table.sum("Net Amount")
    average_order = table.average("Net Amount")

    by_region = table.group_sum("Region", "Net Amount")
    by_category = table.group_sum("Category", "Net Amount")

    print("Rows:", table.count())
    print("Total sales:", money(total_sales))
    print("Average order:", money(average_order))

    print("\nSales by region:")
    for region, value in by_region.items():
        print(region, money(value))

    print("\nSales by category:")
    for category, value in by_category.items():
        print(category, money(value))


# ---------------------------------------------------------------------------
# 9. TOTALS-ROW THINKING
# ---------------------------------------------------------------------------

def calculate_totals_row(table: StructuredTable) -> dict:
    """
    Models an Excel Table Totals Row.

    Only meaningful numeric measures are aggregated.
    """
    if not table.rows:
        return {
            "Quantity": 0,
            "Gross Amount": Decimal("0"),
            "Discount Amount": Decimal("0"),
            "Net Amount": Decimal("0"),
        }

    return {
        "Quantity": sum(row["Quantity"] for row in table),
        "Gross Amount": money(table.sum("Gross Amount")),
        "Discount Amount": money(table.sum("Discount Amount")),
        "Net Amount": money(table.sum("Net Amount")),
    }


def demonstrate_totals():
    print("\n=== 7. TOTALS ROW ===")

    table = build_sales_table()
    add_sales_calculated_columns(table)

    totals = calculate_totals_row(table)

    for key, value in totals.items():
        print(f"{key}: {value}")


# ---------------------------------------------------------------------------
# 10. DATA VALIDATION
# ---------------------------------------------------------------------------

ALLOWED_REGIONS = {"North", "South", "East", "West"}
ALLOWED_CATEGORIES = {"Computers", "Displays", "Accessories"}


def validate_sales_row(row: dict) -> list[str]:
    errors = []

    if not isinstance(row.get("Order ID"), int):
        errors.append("Order ID must be an integer.")

    if not row.get("Customer"):
        errors.append("Customer is required.")

    if row.get("Region") not in ALLOWED_REGIONS:
        errors.append("Region is invalid.")

    if row.get("Category") not in ALLOWED_CATEGORIES:
        errors.append("Category is invalid.")

    if not isinstance(row.get("Quantity"), int) or row["Quantity"] <= 0:
        errors.append("Quantity must be a positive integer.")

    if not isinstance(row.get("Unit Price"), Decimal):
        errors.append("Unit Price must use Decimal.")

    elif row["Unit Price"] < 0:
        errors.append("Unit Price cannot be negative.")

    if not isinstance(row.get("Discount Rate"), Decimal):
        errors.append("Discount Rate must use Decimal.")

    elif not Decimal("0") <= row["Discount Rate"] <= Decimal("1"):
        errors.append("Discount Rate must be between 0 and 1.")

    if not isinstance(row.get("Order Date"), date):
        errors.append("Order Date must be a date.")

    return errors


def demonstrate_validation():
    print("\n=== 8. VALIDATION AND EDGE CASES ===")

    invalid_row = {
        "Order ID": "BAD-ID",
        "Customer": "",
        "Region": "Unknown",
        "Product": "Laptop",
        "Category": "Computers",
        "Quantity": 0,
        "Unit Price": Decimal("-100"),
        "Discount Rate": Decimal("1.5"),
        "Order Date": "not-a-date",
    }

    errors = validate_sales_row(invalid_row)

    for error in errors:
        print("Validation error:", error)


# ---------------------------------------------------------------------------
# 11. LOOKUP-LIKE OPERATIONS
# ---------------------------------------------------------------------------

def lookup_by_key(
    table: StructuredTable,
    key_column: str,
    key_value: object,
) -> dict | None:
    """
    Models the basic idea behind lookup functions such as XLOOKUP.

    A dictionary index is preferable when many lookups are required.
    """
    for row in table:
        if row[key_column] == key_value:
            return row
    return None


def build_index(
    table: StructuredTable,
    key_column: str,
) -> dict:
    index = {}

    for row in table:
        key = row[key_column]

        if key in index:
            raise ValueError(
                f"Duplicate key detected: {key}"
            )

        index[key] = row

    return index


def demonstrate_lookups():
    print("\n=== 9. LOOKUP CONCEPTS ===")

    table = build_sales_table()
    add_sales_calculated_columns(table)

    row = lookup_by_key(table, "Order ID", 1003)
    print("Linear lookup:", row["Customer"] if row else None)

    index = build_index(table, "Order ID")
    indexed_row = index.get(1003)
    print(
        "Indexed lookup:",
        indexed_row["Customer"] if indexed_row else None,
    )


# ---------------------------------------------------------------------------
# 12. MISSING VALUES AND ERROR HANDLING
# ---------------------------------------------------------------------------

def safe_net_amount(row: dict) -> Decimal | None:
    """
    Demonstrates explicit handling of incomplete data.

    Returning None is different from treating missing data as zero.
    """
    try:
        quantity = row["Quantity"]
        price = row["Unit Price"]
        discount = row.get("Discount Rate", Decimal("0"))

        if quantity is None or price is None:
            return None

        return money(
            quantity * price * (Decimal("1") - discount)
        )
    except (TypeError, KeyError):
        return None


def demonstrate_missing_values():
    print("\n=== 10. MISSING VALUES ===")

    examples = [
        {
            "Quantity": 2,
            "Unit Price": Decimal("100"),
            "Discount Rate": Decimal("0.10"),
        },
        {
            "Quantity": None,
            "Unit Price": Decimal("100"),
            "Discount Rate": Decimal("0.10"),
        },
        {
            "Quantity": 2,
            "Unit Price": None,
            "Discount Rate": Decimal("0.10"),
        },
    ]

    for row in examples:
        print("Net amount:", safe_net_amount(row))


# ---------------------------------------------------------------------------
# 13. RELATIVE VS ABSOLUTE LOGIC
# ---------------------------------------------------------------------------

def demonstrate_reference_semantics():
    print("\n=== 11. REFERENCE SEMANTICS ===")

    tax_rate = Decimal("0.18")

    amounts = [
        Decimal("1000"),
        Decimal("2500"),
        Decimal("5000"),
    ]

    # Conceptually:
    # =[@Amount]*(1+$B$1)
    #
    # The row-specific amount changes for every record.
    # The tax rate is an absolute/shared parameter.
    for amount in amounts:
        final_amount = money(amount * (Decimal("1") + tax_rate))
        print(amount, "->", final_amount)


# ---------------------------------------------------------------------------
# 14. DYNAMIC ARRAYS AND TABLE-LIKE RESULTS
# ---------------------------------------------------------------------------

def unique_sorted(values: Iterable[object]) -> list[object]:
    return sorted(set(values))


def demonstrate_dynamic_results():
    print("\n=== 12. DYNAMIC RESULTS ===")

    table = build_sales_table()
    regions = unique_sorted(row["Region"] for row in table)
    products = unique_sorted(row["Product"] for row in table)

    print("Unique regions:", regions)
    print("Unique products:", products)

    # A dynamic result can be consumed by another calculation.
    north_products = unique_sorted(
        row["Product"]
        for row in table
        if row["Region"] == "North"
    )

    print("North products:", north_products)


# ---------------------------------------------------------------------------
# 15. PERFORMANCE: SCAN VS INDEX
# ---------------------------------------------------------------------------

def benchmark_lookup_strategies():
    print("\n=== 13. PERFORMANCE: LINEAR SEARCH VS INDEX ===")

    rows = [
        {
            "ID": number,
            "Value": number * 10,
        }
        for number in range(1, 10001)
    ]

    table = StructuredTable(["ID", "Value"], rows)
    target = 9999

    start = time.perf_counter()
    for _ in range(1000):
        lookup_by_key(table, "ID", target)
    linear_time = time.perf_counter() - start

    index = build_index(table, "ID")

    start = time.perf_counter()
    for _ in range(1000):
        index.get(target)
    indexed_time = time.perf_counter() - start

    print(f"Linear repeated lookup: {linear_time:.6f}s")
    print(f"Indexed repeated lookup: {indexed_time:.6f}s")
    print(
        "The index requires additional memory but avoids repeatedly "
        "scanning the complete table."
    )


# ---------------------------------------------------------------------------
# 16. GROUPED BUSINESS ANALYSIS
# ---------------------------------------------------------------------------

def regional_report(table: StructuredTable) -> None:
    print("\n=== 14. REGIONAL BUSINESS REPORT ===")

    by_region = {}

    for row in table:
        region = row["Region"]

        if region not in by_region:
            by_region[region] = {
                "orders": 0,
                "units": 0,
                "sales": Decimal("0"),
            }

        by_region[region]["orders"] += 1
        by_region[region]["units"] += row["Quantity"]
        by_region[region]["sales"] += row["Net Amount"]

    for region, metrics in sorted(by_region.items()):
        print(
            f"{region}: "
            f"orders={metrics['orders']}, "
            f"units={metrics['units']}, "
            f"sales={money(metrics['sales'])}"
        )


# ---------------------------------------------------------------------------
# 17. EXPORT
# ---------------------------------------------------------------------------

def demonstrate_export():
    print("\n=== 15. CSV EXPORT ===")

    table = build_sales_table()
    add_sales_calculated_columns(table)

    # CSV has no native Excel Table semantics. It stores records only.
    csv_text = table.to_csv()

    print(csv_text)


# ---------------------------------------------------------------------------
# 18. TESTING CALCULATED COLUMNS
# ---------------------------------------------------------------------------

def test_calculations() -> None:
    table = build_sales_table()
    add_sales_calculated_columns(table)

    first = table.rows[0]

    assert first["Gross Amount"] == Decimal("150000.00")
    assert first["Discount Amount"] == Decimal("7500.00")
    assert first["Net Amount"] == Decimal("142500.00")

    assert len(table) == 5
    assert table.sum("Net Amount") > Decimal("0")

    empty = StructuredTable(["A"])
    try:
        empty.average("A")
    except ValueError:
        pass
    else:
        raise AssertionError("Empty average should fail.")

    print("\n=== 16. TESTS ===")
    print("All tests passed.")


# ---------------------------------------------------------------------------
# 19. ADVANCED: FORMULA DEPENDENCY ORDER
# ---------------------------------------------------------------------------

def calculate_financial_columns(table: StructuredTable) -> None:
    """
    Derived columns should be calculated in dependency order.

    Net Revenue depends on Gross Revenue and Discount.
    Profit depends on Net Revenue and Cost.
    Margin depends on Profit and Net Revenue.
    """

    table.calculated_column(
        "Gross Revenue",
        lambda row: money(
            row["Quantity"] * row["Unit Price"]
        ),
    )

    table.calculated_column(
        "Discount",
        lambda row: money(
            row["Gross Revenue"] * row["Discount Rate"]
        ),
    )

    table.calculated_column(
        "Net Revenue",
        lambda row: money(
            row["Gross Revenue"] - row["Discount"]
        ),
    )

    # Cost is intentionally modeled from a fixed percentage here.
    table.calculated_column(
        "Cost",
        lambda row: money(
            row["Net Revenue"] * Decimal("0.70")
        ),
    )

    table.calculated_column(
        "Profit",
        lambda row: money(
            row["Net Revenue"] - row["Cost"]
        ),
    )

    table.calculated_column(
        "Margin",
        lambda row: (
            row["Profit"] / row["Net Revenue"]
            if row["Net Revenue"] != 0
            else Decimal("0")
        ),
    )


def demonstrate_dependency_chain():
    print("\n=== 17. CALCULATION DEPENDENCY CHAIN ===")

    table = build_sales_table()
    calculate_financial_columns(table)

    for row in table:
        print(
            row["Order ID"],
            "Revenue=", row["Net Revenue"],
            "Profit=", row["Profit"],
            "Margin=", f"{row['Margin']:.2%}",
        )


# ---------------------------------------------------------------------------
# 20. DESIGN PRINCIPLES
# ---------------------------------------------------------------------------

def demonstrate_design_principles():
    print("\n=== 18. DESIGN PRINCIPLES ===")

    principles = [
        "Keep one logical record per row.",
        "Use one field per column.",
        "Use descriptive, stable column names.",
        "Avoid merged cells inside structured data.",
        "Keep raw inputs separate from calculated outputs.",
        "Use validation to protect data quality.",
        "Avoid duplicated calculations when one calculated column can serve the table.",
        "Use consistent data types.",
        "Use explicit handling for blanks and errors.",
        "Use indexes or lookup structures when repeated searches become expensive.",
        "Treat imported external data as untrusted input.",
        "Keep business rules documented and testable.",
    ]

    for number, principle in enumerate(principles, start=1):
        print(f"{number}. {principle}")


# ---------------------------------------------------------------------------
# 21. PRACTICAL APPLICATIONS
# ---------------------------------------------------------------------------

def demonstrate_real_world_models():
    print("\n=== 19. REAL-WORLD TABLE MODELS ===")

    examples = {
        "Sales": ["Order ID", "Customer", "Product", "Quantity", "Revenue"],
        "Inventory": ["SKU", "Product", "Stock", "Reorder Level"],
        "Employees": ["Employee ID", "Department", "Salary", "Status"],
        "Projects": ["Project ID", "Owner", "Budget", "Actual Cost", "Status"],
        "Transactions": ["Transaction ID", "Date", "Account", "Amount"],
    }

    for name, columns in examples.items():
        print(f"{name}: {', '.join(columns)}")


# ---------------------------------------------------------------------------
# 22. SECURITY AND PRODUCTION CONSIDERATIONS
# ---------------------------------------------------------------------------

def demonstrate_security_rules():
    print("\n=== 20. SECURITY AND PRODUCTION RULES ===")

    rules = [
        "Validate imported records before calculations.",
        "Do not trust externally supplied formulas or executable expressions.",
        "Use parameterized database queries when moving table data to SQL.",
        "Protect confidential spreadsheets with appropriate access controls.",
        "Avoid exposing personally identifiable information unnecessarily.",
        "Keep source data and calculated outputs distinguishable.",
        "Test financial calculations against known expected values.",
        "Use Decimal for currency calculations when binary floating-point error matters.",
        "Version important calculation logic.",
        "Monitor data imports for unexpected schema changes.",
    ]

    for rule in rules:
        print("-", rule)


# ---------------------------------------------------------------------------
# 23. MAIN STUDY PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    demonstrate_basic_table()
    demonstrate_dynamic_expansion()
    demonstrate_structured_reference_equivalents()
    demonstrate_filtering()
    demonstrate_sorting()
    demonstrate_aggregation()
    demonstrate_totals()
    demonstrate_validation()
    demonstrate_lookups()
    demonstrate_missing_values()
    demonstrate_reference_semantics()
    demonstrate_dynamic_results()
    benchmark_lookup_strategies()

    table = build_sales_table()
    add_sales_calculated_columns(table)
    regional_report(table)

    demonstrate_export()
    test_calculations()
    demonstrate_dependency_chain()
    demonstrate_design_principles()
    demonstrate_real_world_models()
    demonstrate_security_rules()

    print("\n=== STUDY COMPLETE ===")
    print(
        "The examples modeled structured rows, named columns, "
        "calculated columns, dynamic expansion, filtering, sorting, "
        "aggregation, lookups, validation, dependencies, and "
        "production-oriented design."
    )


if __name__ == "__main__":
    main()
