"""
Data Cleaning in Excel
=======================

A comprehensive standalone study script for understanding, simulating, and
automating common Excel data-cleaning concepts with Python.

The examples use standard Python libraries so the file can be executed without
third-party dependencies.

The central workflow demonstrated throughout this file is:

    Inspect -> Profile -> Clean -> Standardize -> Validate -> Transform
    -> Detect anomalies -> Report -> Export

The examples model spreadsheet-style datasets such as customer records,
transactions, contact lists, and operational records.

Important Excel concepts demonstrated in Python include:

- Missing values
- Blank cells
- Whitespace and invisible characters
- Text normalization
- Case standardization
- Duplicate detection
- Data type conversion
- Date normalization
- Number normalization
- Currency cleaning
- Phone number standardization
- Email validation
- Category standardization
- Validation rules
- Outlier detection
- Referential consistency
- Business-rule validation
- Data-quality scoring
- Audit trails
- Idempotent cleaning
- Safe transformation
- Before/after comparison
- Exporting cleaned data
- Reproducible cleaning pipelines

This is an educational implementation of spreadsheet data-cleaning logic.
Excel provides equivalent operations through functions, Find & Replace,
Power Query, conditional formatting, data validation, tables, filters,
sorting, and formulas.
"""

from __future__ import annotations

import csv
import io
import math
import re
import statistics
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable


# ============================================================================
# SECTION 1: BASIC DATA STRUCTURES
# ============================================================================

print("=" * 78)
print("DATA CLEANING IN EXCEL - PYTHON STUDY SCRIPT")
print("=" * 78)


Dataset = list[dict[str, Any]]


def print_table(rows: Dataset, columns: list[str] | None = None, limit: int = 20) -> None:
    """Print dictionaries in a compact spreadsheet-like form."""
    if not rows:
        print("(empty dataset)")
        return

    if columns is None:
        columns = list(rows[0].keys())

    displayed_rows = rows[:limit]

    widths = {}
    for column in columns:
        values = [str(row.get(column, "")) for row in displayed_rows]
        widths[column] = max(len(column), *(len(value) for value in values))

    header = " | ".join(column.ljust(widths[column]) for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(separator)

    for row in displayed_rows:
        print(
            " | ".join(
                str(row.get(column, "")).ljust(widths[column])
                for column in columns
            )
        )

    if len(rows) > limit:
        print(f"... {len(rows) - limit} additional rows not displayed")


# ============================================================================
# SECTION 2: A SMALL DIRTY DATASET
# ============================================================================

raw_data: Dataset = [
    {
        "Customer ID": " C001 ",
        "Name": "  Rahul Sharma ",
        "Email": "RAHUL.SHARMA@EXAMPLE.COM ",
        "Phone": "98765 43210",
        "City": " lucknow",
        "State": "UP",
        "Amount": "₹ 12,500",
        "Order Date": "15/09/2026",
        "Category": " electronics ",
        "Age": "29",
    },
    {
        "Customer ID": "C002",
        "Name": "PRIYA SINGH",
        "Email": "priya.singh@example.com",
        "Phone": "+91-9876543211",
        "City": "Lucknow ",
        "State": "Uttar Pradesh",
        "Amount": "15000",
        "Order Date": "2026-09-16",
        "Category": "Electronics",
        "Age": "31",
    },
    {
        "Customer ID": "C003",
        "Name": " Amit Kumar ",
        "Email": " amit.kumar@example.com",
        "Phone": "98765-43212",
        "City": "KANPUR",
        "State": "UP",
        "Amount": "₹8,750.50",
        "Order Date": "16-09-2026",
        "Category": "electronics",
        "Age": "twenty-eight",
    },
    {
        "Customer ID": "C004",
        "Name": "Neha Verma",
        "Email": "neha.verma@example.com",
        "Phone": "9876543213",
        "City": "Kanpur",
        "State": "U.P.",
        "Amount": "10,000",
        "Order Date": "17/09/2026",
        "Category": " Home Appliances ",
        "Age": "42",
    },
    {
        "Customer ID": "C005",
        "Name": "Suresh Patel",
        "Email": "",
        "Phone": "9876543214",
        "City": "Delhi",
        "State": "Delhi",
        "Amount": "12500",
        "Order Date": "",
        "Category": "home appliance",
        "Age": "37",
    },
    {
        "Customer ID": "C005",
        "Name": " Suresh Patel ",
        "Email": "",
        "Phone": "9876543214",
        "City": "Delhi ",
        "State": "Delhi",
        "Amount": "12500",
        "Order Date": "",
        "Category": "Home Appliances",
        "Age": "37",
    },
    {
        "Customer ID": "C006",
        "Name": "Meera Joshi",
        "Email": "meera.joshi@example.com",
        "Phone": "09876543215",
        "City": "Delhi",
        "State": "DL",
        "Amount": "-500",
        "Order Date": "31/09/2026",
        "Category": "Furniture",
        "Age": "150",
    },
    {
        "Customer ID": "C007",
        "Name": "Arjun Mehta",
        "Email": "arjun.mehta@example",
        "Phone": "9876543216",
        "City": "Lucknow",
        "State": "Uttar Pradesh",
        "Amount": "1O,500",
        "Order Date": "18/09/2026",
        "Category": "Furniture",
        "Age": "34",
    },
]


print("\nRAW DATA")
print_table(raw_data)


# ============================================================================
# SECTION 3: DATA PROFILING
# ============================================================================

def profile_dataset(rows: Dataset) -> dict[str, Any]:
    """Create basic spreadsheet-style data-quality statistics."""
    if not rows:
        return {
            "row_count": 0,
            "column_count": 0,
            "columns": [],
            "missing_values": {},
            "unique_values": {},
        }

    columns = list(rows[0].keys())
    missing_values: dict[str, int] = {}
    unique_values: dict[str, int] = {}

    for column in columns:
        values = [row.get(column) for row in rows]

        missing_values[column] = sum(
            value is None or str(value).strip() == ""
            for value in values
        )

        unique_values[column] = len(
            {
                str(value).strip().lower()
                for value in values
                if value is not None and str(value).strip() != ""
            }
        )

    return {
        "row_count": len(rows),
        "column_count": len(columns),
        "columns": columns,
        "missing_values": missing_values,
        "unique_values": unique_values,
    }


profile = profile_dataset(raw_data)

print("\nDATA PROFILE")
print(f"Rows: {profile['row_count']}")
print(f"Columns: {profile['column_count']}")

for column in profile["columns"]:
    print(
        f"{column:15} "
        f"missing={profile['missing_values'][column]:2} "
        f"unique={profile['unique_values'][column]:2}"
    )


# ============================================================================
# SECTION 4: MISSING VALUES
# ============================================================================

def is_missing(value: Any) -> bool:
    """
    Spreadsheet-style missing-value detection.

    Empty strings, whitespace-only strings, and None are considered missing.
    """
    return value is None or (
        isinstance(value, str) and value.strip() == ""
    )


def count_missing(rows: Dataset, column: str) -> int:
    return sum(is_missing(row.get(column)) for row in rows)


print("\nMISSING VALUE ANALYSIS")

for column in profile["columns"]:
    print(f"{column}: {count_missing(raw_data, column)} missing")


def fill_missing_with_value(
    rows: Dataset,
    column: str,
    replacement: Any,
) -> Dataset:
    """Return a copy with missing cells replaced."""
    result = deepcopy(rows)

    for row in result:
        if is_missing(row.get(column)):
            row[column] = replacement

    return result


# Example:
# filled = fill_missing_with_value(raw_data, "Category", "Unknown")


# ============================================================================
# SECTION 5: WHITESPACE AND INVISIBLE CHARACTER CLEANING
# ============================================================================

def clean_whitespace(value: Any) -> Any:
    """
    Remove leading/trailing whitespace and collapse repeated internal spaces.

    Excel equivalents include:
    - TRIM()
    - CLEAN()
    - Find & Replace
    """
    if not isinstance(value, str):
        return value

    # Replace common non-breaking spaces with normal spaces.
    value = value.replace("\u00A0", " ")

    # Remove non-printing control characters.
    value = "".join(character for character in value if character.isprintable())

    # Collapse repeated whitespace.
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def clean_all_text_whitespace(rows: Dataset) -> Dataset:
    result = deepcopy(rows)

    for row in result:
        for key, value in row.items():
            row[key] = clean_whitespace(value)

    return result


whitespace_cleaned = clean_all_text_whitespace(raw_data)

print("\nWHITESPACE-CLEANED DATA")
print_table(whitespace_cleaned)


# ============================================================================
# SECTION 6: CASE STANDARDIZATION
# ============================================================================

def normalize_name(value: Any) -> Any:
    if is_missing(value):
        return None

    value = clean_whitespace(value)
    return value.title()


def normalize_email(value: Any) -> Any:
    if is_missing(value):
        return None

    return clean_whitespace(value).lower()


def normalize_city(value: Any) -> Any:
    if is_missing(value):
        return None

    return clean_whitespace(value).title()


# Excel equivalents:
#
# =UPPER(A2)
# =LOWER(A2)
# =PROPER(A2)


# ============================================================================
# SECTION 7: CATEGORY STANDARDIZATION
# ============================================================================

CATEGORY_MAP = {
    "electronics": "Electronics",
    "electronic": "Electronics",
    "home appliance": "Home Appliances",
    "home appliances": "Home Appliances",
    "furniture": "Furniture",
}


def normalize_category(value: Any) -> Any:
    if is_missing(value):
        return None

    normalized = clean_whitespace(value).lower()
    return CATEGORY_MAP.get(normalized, normalized.title())


# A controlled vocabulary is preferable to blindly changing text.
# In Excel, this can be implemented using:
# - XLOOKUP
# - VLOOKUP
# - a mapping table
# - Power Query Merge
# - Data Validation lists


# ============================================================================
# SECTION 8: STATE STANDARDIZATION
# ============================================================================

STATE_MAP = {
    "up": "Uttar Pradesh",
    "u.p.": "Uttar Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "dl": "Delhi",
    "delhi": "Delhi",
}


def normalize_state(value: Any) -> Any:
    if is_missing(value):
        return None

    normalized = clean_whitespace(value).lower()
    return STATE_MAP.get(normalized, clean_whitespace(value).title())


# ============================================================================
# SECTION 9: PHONE NUMBER STANDARDIZATION
# ============================================================================

def normalize_phone(value: Any) -> Any:
    """
    Keep digits only and normalize common Indian +91 representations.

    This function intentionally does not claim that every ten-digit number
    is a real or currently assigned telephone number. Format validation and
    existence verification are separate concerns.
    """
    if is_missing(value):
        return None

    digits = re.sub(r"\D", "", str(value))

    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]

    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]

    if len(digits) == 10:
        return digits

    return None


# ============================================================================
# SECTION 10: EMAIL VALIDATION
# ============================================================================

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)


def validate_email(value: Any) -> bool:
    if is_missing(value):
        return False

    return bool(EMAIL_PATTERN.fullmatch(str(value).strip()))


# This is deliberately a practical syntax check, not full RFC-level email
# validation. A syntactically valid address can still be nonexistent.


# ============================================================================
# SECTION 11: NUMBER CLEANING
# ============================================================================

def parse_currency(value: Any) -> Decimal | None:
    """
    Convert common currency representations to Decimal.

    Examples:
        '₹ 12,500'  -> Decimal('12500')
        '8,750.50'  -> Decimal('8750.50')
        '1O,500'    -> None

    Decimal is preferred over float for monetary values because it avoids
    many binary floating-point representation problems.
    """
    if is_missing(value):
        return None

    text = str(value).strip()

    # Currency symbols and grouping separators are removed.
    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace(",", "")
    text = text.replace(" ", "")

    # The letter O is not automatically converted to zero.
    # Doing so could silently corrupt legitimate data.
    try:
        amount = Decimal(text)
    except InvalidOperation:
        return None

    return amount


def parse_integer(value: Any) -> int | None:
    if is_missing(value):
        return None

    try:
        return int(str(value).strip())
    except ValueError:
        return None


# ============================================================================
# SECTION 12: DATE STANDARDIZATION
# ============================================================================

DATE_FORMATS = (
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
)


def parse_date(value: Any) -> date | None:
    if is_missing(value):
        return None

    text = clean_whitespace(value)

    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue

    return None


def format_date(value: Any) -> str | None:
    parsed = parse_date(value)

    if parsed is None:
        return None

    return parsed.isoformat()


# Important:
# 31/09/2026 is rejected because September has only 30 days.
# A cleaning process should not "fix" it silently unless there is a reliable
# business rule that identifies the intended date.


# ============================================================================
# SECTION 13: AGE VALIDATION
# ============================================================================

def validate_age(value: Any) -> tuple[bool, int | None]:
    """
    Demonstrate separation of parsing and business validation.

    A value can be numeric but still invalid according to business rules.
    """
    parsed = parse_integer(value)

    if parsed is None:
        return False, None

    if not 0 <= parsed <= 120:
        return False, parsed

    return True, parsed


# ============================================================================
# SECTION 14: APPLYING A COMPLETE CLEANING PIPELINE
# ============================================================================

def clean_customer_dataset(rows: Dataset) -> Dataset:
    """
    Apply deterministic transformations.

    A useful cleaning pipeline should be:
    - explicit
    - repeatable
    - auditable
    - conservative
    - preferably idempotent

    Idempotent means applying the same cleaning function twice should not
    continue changing already-clean values.
    """
    cleaned: Dataset = []

    for original_row in rows:
        row = {}

        row["Customer ID"] = clean_whitespace(original_row.get("Customer ID"))
        row["Name"] = normalize_name(original_row.get("Name"))
        row["Email"] = normalize_email(original_row.get("Email"))
        row["Phone"] = normalize_phone(original_row.get("Phone"))
        row["City"] = normalize_city(original_row.get("City"))
        row["State"] = normalize_state(original_row.get("State"))
        row["Amount"] = parse_currency(original_row.get("Amount"))
        row["Order Date"] = format_date(original_row.get("Order Date"))
        row["Category"] = normalize_category(original_row.get("Category"))

        age_valid, age = validate_age(original_row.get("Age"))
        row["Age"] = age if age_valid else None

        cleaned.append(row)

    return cleaned


cleaned_data = clean_customer_dataset(raw_data)

print("\nCLEANED DATA")
print_table(cleaned_data)


# ============================================================================
# SECTION 15: VALIDATION RULES
# ============================================================================

def validate_required_fields(
    row: dict[str, Any],
    required_columns: Iterable[str],
) -> list[str]:
    errors = []

    for column in required_columns:
        if is_missing(row.get(column)):
            errors.append(f"{column} is required")

    return errors


def validate_customer_id(value: Any) -> bool:
    if is_missing(value):
        return False

    return bool(re.fullmatch(r"C\d{3}", str(value)))


def validate_amount(value: Any) -> bool:
    if value is None:
        return False

    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        return False

    return amount >= Decimal("0")


def validate_order_date(value: Any) -> bool:
    return parse_date(value) is not None


def validate_row(row: dict[str, Any]) -> list[str]:
    errors = []

    errors.extend(
        validate_required_fields(
            row,
            ["Customer ID", "Name", "Phone", "City", "State", "Category"],
        )
    )

    if not validate_customer_id(row.get("Customer ID")):
        errors.append("Customer ID has invalid format")

    if row.get("Email") is not None and not validate_email(row.get("Email")):
        errors.append("Email has invalid format")

    if row.get("Amount") is None:
        errors.append("Amount is invalid or missing")
    elif not validate_amount(row.get("Amount")):
        errors.append("Amount cannot be negative")

    if row.get("Order Date") is not None and not validate_order_date(
        row.get("Order Date")
    ):
        errors.append("Order Date is invalid")

    if row.get("Age") is None:
        errors.append("Age is invalid or missing")

    return errors


validation_results = []

for index, row in enumerate(cleaned_data, start=2):
    errors = validate_row(row)

    validation_results.append(
        {
            "Excel Row": index,
            "Valid": not errors,
            "Errors": errors,
        }
    )

print("\nROW VALIDATION RESULTS")

for result in validation_results:
    print(
        f"Excel row {result['Excel Row']}: "
        f"{'VALID' if result['Valid'] else 'INVALID'}"
    )

    for error in result["Errors"]:
        print(f"  - {error}")


# ============================================================================
# SECTION 16: DUPLICATE DETECTION
# ============================================================================

def find_duplicates(
    rows: Dataset,
    key_columns: list[str],
) -> dict[tuple[Any, ...], list[int]]:
    """
    Detect duplicates using one or more business keys.

    Duplicate definition must be chosen deliberately.
    Two rows with the same customer ID may represent:
    - accidental duplicates
    - multiple transactions
    - multiple versions
    - legitimate repeated activity
    """
    groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)

    for index, row in enumerate(rows, start=2):
        key = tuple(row.get(column) for column in key_columns)
        groups[key].append(index)

    return {
        key: indexes
        for key, indexes in groups.items()
        if len(indexes) > 1
    }


duplicates = find_duplicates(cleaned_data, ["Customer ID"])

print("\nDUPLICATES BY CUSTOMER ID")

for key, indexes in duplicates.items():
    print(f"{key}: rows {indexes}")


# Exact duplicate detection considers every relevant column.


def find_exact_duplicates(rows: Dataset) -> list[list[int]]:
    groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)

    columns = list(rows[0].keys()) if rows else []

    for index, row in enumerate(rows, start=2):
        signature = tuple(str(row.get(column)) for column in columns)
        groups[signature].append(index)

    return [indexes for indexes in groups.values() if len(indexes) > 1]


print("\nEXACT DUPLICATES")
print(find_exact_duplicates(cleaned_data))


# ============================================================================
# SECTION 17: DATA QUALITY DIMENSIONS
# ============================================================================

def completeness_score(
    rows: Dataset,
    required_columns: list[str],
) -> float:
    if not rows or not required_columns:
        return 100.0

    total_cells = len(rows) * len(required_columns)
    populated_cells = sum(
        not is_missing(row.get(column))
        for row in rows
        for column in required_columns
    )

    return populated_cells / total_cells * 100


def uniqueness_score(
    rows: Dataset,
    key_column: str,
) -> float:
    if not rows:
        return 100.0

    values = [
        row.get(key_column)
        for row in rows
        if not is_missing(row.get(key_column))
    ]

    if not values:
        return 0.0

    return len(set(values)) / len(values) * 100


def validity_score(
    rows: Dataset,
    validator: Callable[[dict[str, Any]], list[str]],
) -> float:
    if not rows:
        return 100.0

    valid_rows = sum(not validator(row) for row in rows)
    return valid_rows / len(rows) * 100


print("\nDATA QUALITY SCORES")

required_columns = [
    "Customer ID",
    "Name",
    "Phone",
    "City",
    "State",
    "Category",
]

print(
    f"Completeness: "
    f"{completeness_score(cleaned_data, required_columns):.2f}%"
)

print(
    f"Customer ID uniqueness: "
    f"{uniqueness_score(cleaned_data, 'Customer ID'):.2f}%"
)

print(
    f"Row validity: "
    f"{validity_score(cleaned_data, validate_row):.2f}%"
)


# ============================================================================
# SECTION 18: BEFORE/AFTER AUDIT TRAIL
# ============================================================================

def create_audit_trail(
    before: Dataset,
    after: Dataset,
) -> list[dict[str, Any]]:
    """
    Record changes instead of silently overwriting the original data.

    In production workflows, auditability is important because cleaning is
    itself a transformation that can introduce errors if implemented poorly.
    """
    changes = []

    for row_number, (old_row, new_row) in enumerate(
        zip(before, after),
        start=2,
    ):
        columns = set(old_row) | set(new_row)

        for column in columns:
            old_value = old_row.get(column)
            new_value = new_row.get(column)

            if str(old_value) != str(new_value):
                changes.append(
                    {
                        "Excel Row": row_number,
                        "Column": column,
                        "Before": old_value,
                        "After": new_value,
                    }
                )

    return changes


audit_trail = create_audit_trail(raw_data, cleaned_data)

print("\nAUDIT TRAIL")

for change in audit_trail:
    print(
        f"Row {change['Excel Row']}, "
        f"{change['Column']}: "
        f"{change['Before']!r} -> {change['After']!r}"
    )


# ============================================================================
# SECTION 19: OUTLIER DETECTION
# ============================================================================

def z_scores(values: list[float]) -> list[float]:
    """
    Calculate population-style z-scores.

    A z-score alone does not prove that a value is erroneous.
    An unusual transaction may be completely legitimate.
    """
    if len(values) < 2:
        return [0.0 for _ in values]

    mean = statistics.mean(values)
    standard_deviation = statistics.pstdev(values)

    if standard_deviation == 0:
        return [0.0 for _ in values]

    return [
        (value - mean) / standard_deviation
        for value in values
    ]


amounts = [
    float(row["Amount"])
    for row in cleaned_data
    if row["Amount"] is not None
]

scores = z_scores(amounts)

print("\nAMOUNT Z-SCORES")

for amount, score in zip(amounts, scores):
    print(f"{amount:10.2f} -> z={score:7.3f}")


# ============================================================================
# SECTION 20: IQR OUTLIER DETECTION
# ============================================================================

def iqr_bounds(values: list[float]) -> tuple[float, float] | None:
    if len(values) < 4:
        return None

    sorted_values = sorted(values)

    midpoint = len(sorted_values) // 2

    if len(sorted_values) % 2 == 0:
        lower_half = sorted_values[:midpoint]
        upper_half = sorted_values[midpoint:]
    else:
        lower_half = sorted_values[:midpoint]
        upper_half = sorted_values[midpoint + 1:]

    q1 = statistics.median(lower_half)
    q3 = statistics.median(upper_half)

    iqr = q3 - q1

    return (
        q1 - 1.5 * iqr,
        q3 + 1.5 * iqr,
    )


bounds = iqr_bounds(amounts)

print("\nIQR OUTLIER BOUNDS")
print(bounds)

if bounds:
    lower, upper = bounds

    for amount in amounts:
        if amount < lower or amount > upper:
            print(f"Potential statistical outlier: {amount}")


# ============================================================================
# SECTION 21: VALIDATION AGAINST CONTROLLED CATEGORIES
# ============================================================================

ALLOWED_CATEGORIES = {
    "Electronics",
    "Home Appliances",
    "Furniture",
}


def validate_category(value: Any) -> bool:
    return value in ALLOWED_CATEGORIES


print("\nCATEGORY VALIDATION")

for row in cleaned_data:
    category = row.get("Category")
    print(
        f"{category!r}: "
        f"{'valid' if validate_category(category) else 'invalid'}"
    )


# ============================================================================
# SECTION 22: CROSS-FIELD BUSINESS RULES
# ============================================================================

def cross_field_validation(row: dict[str, Any]) -> list[str]:
    """
    Demonstrate rules that involve multiple columns.

    Examples:
    - A valid row may require both state and city.
    - An amount may be required to be non-negative.
    - A transaction date may not be in the future.
    """
    errors = []

    city = row.get("City")
    state = row.get("State")
    amount = row.get("Amount")

    if city == "Lucknow" and state != "Uttar Pradesh":
        errors.append("Lucknow should belong to Uttar Pradesh")

    if city == "Kanpur" and state != "Uttar Pradesh":
        errors.append("Kanpur should belong to Uttar Pradesh")

    if amount is not None and amount < 0:
        errors.append("Amount cannot be negative")

    return errors


print("\nCROSS-FIELD VALIDATION")

for index, row in enumerate(cleaned_data, start=2):
    errors = cross_field_validation(row)

    if errors:
        print(f"Row {index}:")
        for error in errors:
            print(f"  - {error}")


# ============================================================================
# SECTION 23: STANDARDIZATION VERSUS VALIDATION
# ============================================================================

print("\nSTANDARDIZATION VS VALIDATION")
print("Standardization changes representation.")
print("Validation determines whether a value satisfies a rule.")
print("A cleaned value can still be invalid.")
print("A valid value can still be non-standardized.")


# Example:
#
# "PRiya@example.com" -> standardized to "priya@example.com"
# "priya@example.com" -> valid syntax
#
# But an address may still be unreachable even if its syntax is valid.


# ============================================================================
# SECTION 24: SAFE IMPUTATION
# ============================================================================

def fill_missing_numeric_with_median(
    rows: Dataset,
    column: str,
) -> Dataset:
    """
    Median imputation is shown for educational purposes.

    It should not automatically be used in every dataset because replacing
    missing information changes the statistical distribution and may hide the
    fact that data was originally missing.
    """
    result = deepcopy(rows)

    values = [
        row[column]
        for row in result
        if isinstance(row.get(column), (int, float, Decimal))
    ]

    if not values:
        return result

    numeric_values = [float(value) for value in values]
    median_value = statistics.median(numeric_values)

    for row in result:
        if row.get(column) is None:
            row[column] = median_value

    return result


# Example:
# imputed = fill_missing_numeric_with_median(cleaned_data, "Amount")


# ============================================================================
# SECTION 25: NORMALIZATION AND IDENTITY
# ============================================================================

def make_identity_key(row: dict[str, Any]) -> str:
    """
    Build a normalized matching key.

    Such keys can help identify likely duplicates when identifiers are missing.
    They should not be treated as proof of identity because two different
    people can legitimately share the same normalized attributes.
    """
    name = clean_whitespace(row.get("Name", "")).lower()
    email = clean_whitespace(row.get("Email", "")).lower()

    phone = normalize_phone(row.get("Phone", "")) or ""

    return "|".join([name, email, phone])


identity_groups: dict[str, list[int]] = defaultdict(list)

for index, row in enumerate(cleaned_data, start=2):
    identity_groups[make_identity_key(row)].append(index)

print("\nPOTENTIAL IDENTITY DUPLICATES")

for key, rows_with_key in identity_groups.items():
    if len(rows_with_key) > 1:
        print(f"{rows_with_key}: {key}")


# ============================================================================
# SECTION 26: EXCEL-STYLE TEXT OPERATIONS
# ============================================================================

def excel_trim_simulation(value: str) -> str:
    """Approximate the practical behavior of Excel TRIM for ordinary text."""
    return re.sub(r" +", " ", value.strip())


def excel_clean_simulation(value: str) -> str:
    """Approximate removal of ASCII control characters."""
    return "".join(character for character in value if ord(character) >= 32)


def excel_left(value: str, number_of_characters: int) -> str:
    return value[:number_of_characters]


def excel_right(value: str, number_of_characters: int) -> str:
    if number_of_characters == 0:
        return ""
    return value[-number_of_characters:]


def excel_mid(value: str, start: int, length: int) -> str:
    """
    Excel MID uses a 1-based start position.
    Python uses 0-based indexing, so conversion happens here.
    """
    if start < 1 or length < 0:
        raise ValueError("start must be >= 1 and length must be >= 0")

    return value[start - 1:start - 1 + length]


def excel_substitute(
    value: str,
    old_text: str,
    new_text: str,
) -> str:
    return value.replace(old_text, new_text)


print("\nEXCEL-STYLE TEXT FUNCTION EXAMPLES")

sample_text = "   Excel    Data   Cleaning   "

print("TRIM:", repr(excel_trim_simulation(sample_text)))
print("CLEAN:", repr(excel_clean_simulation(sample_text)))
print("LEFT:", excel_left("CUSTOMER", 4))
print("RIGHT:", excel_right("CUSTOMER", 4))
print("MID:", excel_mid("CUSTOMER", 2, 4))
print(
    "SUBSTITUTE:",
    excel_substitute("UP, U.P., Uttar Pradesh", "U.P.", "UP"),
)


# ============================================================================
# SECTION 27: DATA TYPE CONVERSION
# ============================================================================

def infer_basic_type(value: Any) -> str:
    if value is None:
        return "missing"

    if isinstance(value, bool):
        return "boolean"

    if isinstance(value, int):
        return "integer"

    if isinstance(value, float):
        return "decimal"

    if isinstance(value, Decimal):
        return "decimal"

    if isinstance(value, date):
        return "date"

    if isinstance(value, str):
        if parse_date(value):
            return "date"

        if parse_currency(value) is not None:
            return "numeric-like"

        return "text"

    return type(value).__name__


print("\nTYPE INFERENCE")

for value in [
    "123",
    "₹ 12,500",
    "2026-09-20",
    "hello",
    None,
]:
    print(f"{value!r:20} -> {infer_basic_type(value)}")


# ============================================================================
# SECTION 28: CONSISTENCY CHECKS
# ============================================================================

def consistency_check(rows: Dataset) -> list[str]:
    errors = []

    for index, row in enumerate(rows, start=2):
        if row.get("City") in {"Lucknow", "Kanpur"}:
            if row.get("State") != "Uttar Pradesh":
                errors.append(
                    f"Row {index}: city/state mismatch"
                )

        if row.get("Amount") is not None and row["Amount"] < 0:
            errors.append(
                f"Row {index}: negative amount"
            )

    return errors


print("\nCONSISTENCY CHECKS")

for error in consistency_check(cleaned_data):
    print(error)


# ============================================================================
# SECTION 29: DATA QUALITY REPORT
# ============================================================================

def generate_quality_report(rows: Dataset) -> dict[str, Any]:
    report = {
        "rows": len(rows),
        "columns": len(rows[0]) if rows else 0,
        "missing_by_column": {},
        "duplicate_customer_ids": {},
        "invalid_rows": [],
    }

    if not rows:
        return report

    for column in rows[0]:
        report["missing_by_column"][column] = count_missing(rows, column)

    report["duplicate_customer_ids"] = find_duplicates(
        rows,
        ["Customer ID"],
    )

    for index, row in enumerate(rows, start=2):
        errors = validate_row(row)

        if errors:
            report["invalid_rows"].append(
                {
                    "row": index,
                    "errors": errors,
                }
            )

    return report


quality_report = generate_quality_report(cleaned_data)

print("\nQUALITY REPORT")
print(f"Rows: {quality_report['rows']}")
print(f"Columns: {quality_report['columns']}")
print(f"Duplicate IDs: {quality_report['duplicate_customer_ids']}")
print(f"Invalid rows: {quality_report['invalid_rows']}")


# ============================================================================
# SECTION 30: CSV EXPORT
# ============================================================================

def decimal_serializer(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, date):
        return value.isoformat()

    return value


def dataset_to_csv(rows: Dataset) -> str:
    """Convert cleaned data to CSV text without requiring a physical file."""
    if not rows:
        return ""

    output = io.StringIO()
    columns = list(rows[0].keys())

    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()

    for row in rows:
        writer.writerow(
            {
                column: decimal_serializer(row.get(column))
                for column in columns
            }
        )

    return output.getvalue()


csv_output = dataset_to_csv(cleaned_data)

print("\nCSV EXPORT PREVIEW")
print(csv_output)


# ============================================================================
# SECTION 31: SORTING AND FILTERING
# ============================================================================

def filter_rows(
    rows: Dataset,
    predicate: Callable[[dict[str, Any]], bool],
) -> Dataset:
    return [row for row in rows if predicate(row)]


def sort_rows(
    rows: Dataset,
    column: str,
    reverse: bool = False,
) -> Dataset:
    return sorted(
        rows,
        key=lambda row: (
            row.get(column) is None,
            row.get(column),
        ),
        reverse=reverse,
    )


high_value_orders = filter_rows(
    cleaned_data,
    lambda row: (
        row.get("Amount") is not None
        and row["Amount"] >= Decimal("10000")
    ),
)

print("\nORDERS >= 10000")
print_table(high_value_orders)

print("\nSORTED BY AMOUNT")
print_table(sort_rows(cleaned_data, "Amount", reverse=True))


# ============================================================================
# SECTION 32: AGGREGATION
# ============================================================================

def group_sum(
    rows: Dataset,
    group_column: str,
    value_column: str,
) -> dict[Any, Decimal]:
    totals: dict[Any, Decimal] = defaultdict(lambda: Decimal("0"))

    for row in rows:
        group = row.get(group_column)
        value = row.get(value_column)

        if group is not None and isinstance(value, Decimal):
            totals[group] += value

    return dict(totals)


print("\nAMOUNT BY CATEGORY")

for category, total in group_sum(
    cleaned_data,
    "Category",
    "Amount",
).items():
    print(f"{category}: {total}")


# ============================================================================
# SECTION 33: TESTING THE CLEANING FUNCTIONS
# ============================================================================

def run_assertion_tests() -> None:
    assert clean_whitespace("  hello   world  ") == "hello world"
    assert normalize_email("  USER@EXAMPLE.COM ") == "user@example.com"
    assert normalize_city(" lucknow ") == "Lucknow"
    assert normalize_category(" electronics ") == "Electronics"
    assert normalize_state("U.P.") == "Uttar Pradesh"

    assert normalize_phone("98765 43210") == "9876543210"
    assert normalize_phone("+91-9876543211") == "9876543211"

    assert parse_currency("₹ 12,500") == Decimal("12500")
    assert parse_currency("₹8,750.50") == Decimal("8750.50")
    assert parse_currency("1O,500") is None

    assert parse_date("15/09/2026") == date(2026, 9, 15)
    assert parse_date("2026-09-16") == date(2026, 9, 16)
    assert parse_date("31/09/2026") is None

    valid_age, age = validate_age("29")
    assert valid_age is True
    assert age == 29

    valid_age, age = validate_age("150")
    assert valid_age is False
    assert age == 150

    assert validate_email("person@example.com") is True
    assert validate_email("person@example") is False


run_assertion_tests()

print("\nALL BASIC ASSERTION TESTS PASSED")


# ============================================================================
# SECTION 34: IDEMPOTENCE TEST
# ============================================================================

cleaned_twice = clean_customer_dataset(cleaned_data)

if cleaned_twice == cleaned_data:
    print("Idempotence test: PASSED")
else:
    print("Idempotence test: FAILED")


# ============================================================================
# SECTION 35: CLEANING DECISIONS
# ============================================================================

print("\nCLEANING DECISION PRINCIPLES")

principles = [
    "Never overwrite raw data before preserving the original.",
    "Separate correction from validation.",
    "Prefer explicit mapping rules over uncontrolled replacements.",
    "Do not invent missing values without a documented rule.",
    "Do not silently repair ambiguous dates.",
    "Treat duplicate detection as a business-definition problem.",
    "Validate both individual fields and relationships between fields.",
    "Use controlled vocabularies for categories.",
    "Keep an audit trail for important transformations.",
    "Use appropriate data types before performing calculations.",
    "Use Decimal for monetary calculations when exact decimal arithmetic matters.",
    "Test cleaning functions with valid, invalid, and boundary values.",
    "Make automated transformations deterministic and repeatable.",
]

for number, principle in enumerate(principles, start=1):
    print(f"{number}. {principle}")


# ============================================================================
# SECTION 36: PERFORMANCE CONSIDERATIONS
# ============================================================================

print("\nPERFORMANCE CONSIDERATIONS")

performance_points = {
    "Repeated scans": "Repeatedly scanning large datasets can be expensive.",
    "Lookups": "Dictionary-based mappings are generally efficient for controlled replacements.",
    "Memory": "Loading an entire dataset into memory is simple but may not scale to very large files.",
    "Vectorization": "Column-oriented tools can reduce repeated per-cell operations.",
    "Power Query": "For large Excel workflows, Power Query can move transformations into a repeatable query pipeline.",
    "Formula recalculation": "Large numbers of volatile or complex formulas can increase workbook calculation time.",
}

for topic, explanation in performance_points.items():
    print(f"{topic}: {explanation}")


# ============================================================================
# SECTION 37: SECURITY AND DATA GOVERNANCE
# ============================================================================

print("\nSECURITY AND GOVERNANCE CONSIDERATIONS")

security_points = [
    "Do not expose personally identifiable information unnecessarily.",
    "Avoid storing passwords, API keys, or authentication secrets in spreadsheets.",
    "Treat imported CSV and spreadsheet content as untrusted input.",
    "Be careful with spreadsheet formula injection when exporting user-controlled text.",
    "Restrict access to sensitive workbooks.",
    "Maintain version history for important transformations.",
    "Document who changed important business data and why.",
    "Validate data before loading it into downstream systems.",
]

for point in security_points:
    print("-", point)


# ============================================================================
# SECTION 38: PRODUCTION-STYLE PIPELINE
# ============================================================================

class DataCleaningPipeline:
    """
    A small pipeline abstraction.

    Each transformation receives a dataset and returns a dataset.
    This makes the process composable and testable.
    """

    def __init__(self) -> None:
        self.steps: list[
            tuple[str, Callable[[Dataset], Dataset]]
        ] = []

    def add_step(
        self,
        name: str,
        function: Callable[[Dataset], Dataset],
    ) -> None:
        self.steps.append((name, function))

    def run(self, rows: Dataset) -> Dataset:
        current = deepcopy(rows)

        for name, function in self.steps:
            print(f"Running step: {name}")
            current = function(current)

        return current


pipeline = DataCleaningPipeline()
pipeline.add_step(
    "whitespace normalization",
    clean_all_text_whitespace,
)
pipeline.add_step(
    "customer standardization",
    clean_customer_dataset,
)

pipeline_result = pipeline.run(raw_data)

print("\nPIPELINE RESULT")
print_table(pipeline_result)


# ============================================================================
# SECTION 39: REFERENCE TO COMMON EXCEL OPERATIONS
# ============================================================================

excel_operations = {
    "TRIM": "Remove unnecessary spaces from text.",
    "CLEAN": "Remove many non-printing characters.",
    "UPPER": "Convert text to uppercase.",
    "LOWER": "Convert text to lowercase.",
    "PROPER": "Convert words to title case.",
    "LEFT": "Extract characters from the left.",
    "RIGHT": "Extract characters from the right.",
    "MID": "Extract characters from a specified position.",
    "LEN": "Count characters.",
    "FIND": "Find a case-sensitive position.",
    "SEARCH": "Find a position without case sensitivity.",
    "SUBSTITUTE": "Replace matching text.",
    "TEXTSPLIT": "Split text into multiple cells.",
    "TEXTJOIN": "Join text values.",
    "IF": "Apply conditional logic.",
    "IFERROR": "Handle formula errors.",
    "XLOOKUP": "Retrieve related values using a lookup key.",
    "COUNTIF": "Count values satisfying a criterion.",
    "COUNTIFS": "Count values satisfying multiple criteria.",
    "SUMIF": "Sum values satisfying a criterion.",
    "SUMIFS": "Sum values satisfying multiple criteria.",
    "UNIQUE": "Return unique values.",
    "FILTER": "Return records satisfying conditions.",
    "SORT": "Sort an array.",
    "VALUE": "Convert text representing a number into a numeric value.",
    "DATEVALUE": "Convert recognizable date text into a date value.",
}

print("\nCOMMON EXCEL DATA-CLEANING FUNCTIONS")

for function_name, purpose in excel_operations.items():
    print(f"{function_name:12} - {purpose}")


# ============================================================================
# SECTION 40: FINAL STUDY CHECKLIST
# ============================================================================

checklist = [
    "Profile the dataset before modifying it.",
    "Preserve the raw dataset.",
    "Identify missing values.",
    "Remove unnecessary whitespace.",
    "Remove or investigate invisible characters.",
    "Standardize case.",
    "Standardize categories.",
    "Normalize dates.",
    "Normalize numbers and currency.",
    "Normalize phone numbers where appropriate.",
    "Validate email syntax.",
    "Validate numeric ranges.",
    "Detect duplicates.",
    "Check cross-field consistency.",
    "Investigate outliers rather than automatically deleting them.",
    "Keep an audit trail.",
    "Recalculate data-quality metrics after cleaning.",
    "Test the cleaning logic.",
    "Export a controlled clean dataset.",
    "Document assumptions and business rules.",
]

print("\nFINAL DATA-CLEANING CHECKLIST")

for item in checklist:
    print(f"[ ] {item}")


print("\n" + "=" * 78)
print("END OF DATA CLEANING IN EXCEL STUDY SCRIPT")
print("=" * 78)
