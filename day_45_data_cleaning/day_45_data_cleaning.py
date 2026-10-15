"""
Data Cleaning: Missing Values, Duplicates, and Inconsistent Data

A self-contained practical data-cleaning pipeline using only the Python
standard library. The example models customer transaction records and
demonstrates detection, normalization, repair, rejection, auditing, and
quality measurement for three distinct data-quality problems:
missing values, duplicate records, and inconsistent representations.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from collections import Counter, defaultdict
from copy import deepcopy
import csv
import io
import json
import re
from typing import Any, Iterable


RAW_CSV = """customer_id,name,email,phone,city,amount,currency,status,signup_date
C001,Asha Sharma,ASHA@EXAMPLE.COM,+91 98765 43210,Lucknow,1250,INR,active,2026-01-05
C002,Rahul Verma,rahul@example.com,9876543211,Lucknow,850,inr,Active,05/01/2026
C003,Meera Singh,,+91-91234-56789,Kanpur,,INR,ACTIVE,2026-01-08
C004,Arun Kumar,arun@example.com,,Kanpur,450,INR,active,2026-01-09
C005,Neha Gupta,neha@example.com,+91 90000 11111,Lucknow,1250,INR,Active,2026-01-10
C005,Neha Gupta,neha@example.com,+91 90000 11111,Lucknow,1250,INR,Active,2026-01-10
C006,Ravi Patel,ravi@example.com,+91-98888-22222,lucknow,850,INR,active,2026-01-11
C007,Sonia Rao,sonia@example.com,+91 97777 33333,Kanpur,N/A,INR,pending,2026-01-12
C008,Vikram Das,vIKRAM@EXAMPLE.COM,+91 96666 44444,Kanpur,1,250,INR,active,2026-01-13
C009,Pooja Nair,pooja@example.com,+91 95555 55555,Lucknow,1250,Rs.,active,2026-01-14
C010,Dev Shah,dev@example.com,+91 94444 66666,Lucknow,900,INR,ACTIVE,
"""


MISSING_TOKENS = {
    "",
    "na",
    "n/a",
    "null",
    "none",
    "unknown",
    "-",
    "--",
}


@dataclass
class CleaningIssue:
    row_number: int
    field: str
    issue_type: str
    original_value: Any
    cleaned_value: Any
    action: str
    reason: str


@dataclass
class QualityReport:
    total_rows: int
    complete_rows: int
    missing_cells: int
    duplicate_rows: int
    inconsistent_cells: int
    rejected_rows: int

    @property
    def completeness_rate(self) -> float:
        if self.total_rows == 0:
            return 100.0
        return self.complete_rows / self.total_rows * 100


def parse_csv(text: str) -> list[dict[str, str]]:
    """Read source records without silently changing their raw values."""
    return list(csv.DictReader(io.StringIO(text)))


def normalize_missing(value: Any) -> Any:
    """Convert recognized textual missing-value markers to None."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return None
    return text


def normalize_name(value: Any) -> Any:
    if value is None:
        return None
    return " ".join(str(value).strip().split()).title()


def normalize_email(value: Any) -> Any:
    if value is None:
        return None
    value = str(value).strip().lower()
    if not value:
        return None
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        return value
    return value


def normalize_phone(value: Any) -> Any:
    if value is None:
        return None

    digits = re.sub(r"\D", "", str(value))
    if not digits:
        return None

    if digits.startswith("91") and len(digits) == 12:
        return "+91 " + digits[2:7] + " " + digits[7:]

    if len(digits) == 10:
        return "+91 " + digits[:5] + " " + digits[5:]

    return "+" + digits


def normalize_city(value: Any) -> Any:
    if value is None:
        return None
    value = " ".join(str(value).strip().split()).lower()
    city_map = {
        "lucknow": "Lucknow",
        "lko": "Lucknow",
        "kanpur": "Kanpur",
        "knp": "Kanpur",
    }
    return city_map.get(value, value.title())


def parse_amount(value: Any) -> Decimal | None:
    if value is None:
        return None

    text = str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return None

    text = text.replace(",", "")
    text = re.sub(r"^(rs\.?|inr)\s*", "", text, flags=re.IGNORECASE)

    try:
        amount = Decimal(text)
    except InvalidOperation:
        return None

    if amount < 0:
        raise ValueError("Transaction amount cannot be negative")

    return amount


def normalize_currency(value: Any) -> str | None:
    if value is None:
        return None

    token = str(value).strip().upper()
    aliases = {
        "RS": "INR",
        "RS.": "INR",
        "₹": "INR",
        "RUPEE": "INR",
        "RUPEES": "INR",
    }
    return aliases.get(token, token)


def normalize_status(value: Any) -> str | None:
    if value is None:
        return None

    token = str(value).strip().lower()
    aliases = {
        "active": "active",
        "act": "active",
        "pending": "pending",
        "pend": "pending",
        "inactive": "inactive",
        "in-active": "inactive",
    }
    return aliases.get(token, token)


def normalize_date(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return None

    formats = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d")

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass

    return text


def record_signature(record: dict[str, Any]) -> tuple[Any, ...]:
    """
    Use normalized business attributes for duplicate detection.
    Customer ID is included because it identifies the customer in this model.
    """
    fields = (
        "customer_id",
        "name",
        "email",
        "phone",
        "city",
        "amount",
        "currency",
        "status",
        "signup_date",
    )
    return tuple(record.get(field) for field in fields)


def detect_duplicates(records: list[dict[str, Any]]) -> tuple[set[int], dict[tuple[Any, ...], list[int]]]:
    groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)

    for index, record in enumerate(records):
        groups[record_signature(record)].append(index)

    duplicate_indexes: set[int] = set()

    for indexes in groups.values():
        if len(indexes) > 1:
            duplicate_indexes.update(indexes[1:])

    return duplicate_indexes, groups


def clean_records(
    raw_records: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[CleaningIssue]]:
    cleaned: list[dict[str, Any]] = []
    issues: list[CleaningIssue] = []

    for row_number, raw in enumerate(raw_records, start=2):
        row: dict[str, Any] = {}

        for field, raw_value in raw.items():
            normalized = normalize_missing(raw_value)

            if normalized is None:
                row[field] = None
                if str(raw_value).strip() != "":
                    issues.append(
                        CleaningIssue(
                            row_number,
                            field,
                            "missing_value",
                            raw_value,
                            None,
                            "standardized",
                            "Recognized missing-value token was converted to None.",
                        )
                    )
                continue

            row[field] = normalized

        original = deepcopy(row)

        row["name"] = normalize_name(row["name"])
        row["email"] = normalize_email(row["email"])
        row["phone"] = normalize_phone(row["phone"])
        row["city"] = normalize_city(row["city"])

        try:
            row["amount"] = parse_amount(row["amount"])
        except ValueError as exc:
            issues.append(
                CleaningIssue(
                    row_number,
                    "amount",
                    "invalid_value",
                    original["amount"],
                    None,
                    "rejected",
                    str(exc),
                )
            )
            row["amount"] = None

        row["currency"] = normalize_currency(row["currency"])
        row["status"] = normalize_status(row["status"])
        row["signup_date"] = normalize_date(row["signup_date"])

        for field, before in original.items():
            after = row.get(field)
            if before != after and before is not None:
                issues.append(
                    CleaningIssue(
                        row_number,
                        field,
                        "inconsistent_representation",
                        before,
                        after,
                        "normalized",
                        "Equivalent values were converted to the canonical representation.",
                    )
                )

        cleaned.append(row)

    duplicate_indexes, _ = detect_duplicates(cleaned)

    for index in sorted(duplicate_indexes):
        row_number = index + 2
        issues.append(
            CleaningIssue(
                row_number,
                "__row__",
                "duplicate",
                cleaned[index],
                None,
                "removed",
                "A normalized duplicate of an earlier record was detected.",
            )
        )

    deduplicated = [
        record for index, record in enumerate(cleaned)
        if index not in duplicate_indexes
    ]

    return deduplicated, issues


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if not record.get("customer_id"):
        errors.append("customer_id is required")

    if not record.get("name"):
        errors.append("name is required")

    email = record.get("email")
    if email is not None and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors.append("email has invalid structure")

    amount = record.get("amount")
    if amount is not None and amount < 0:
        errors.append("amount cannot be negative")

    if record.get("currency") not in {None, "INR", "USD", "EUR", "GBP"}:
        errors.append("unsupported currency")

    if record.get("status") not in {"active", "pending", "inactive"}:
        errors.append("unsupported status")

    signup_date = record.get("signup_date")
    if signup_date is not None:
        try:
            datetime.fromisoformat(signup_date)
        except ValueError:
            errors.append("signup_date is not ISO formatted")

    return errors


def impute_missing_amounts(
    records: list[dict[str, Any]],
    issues: list[CleaningIssue],
) -> None:
    """
    Amount is a numeric measure. For this demonstration, missing amounts are
    imputed using the median amount within the same city. This is preferable
    to a global value when city-level transaction behavior is materially
    different.
    """
    city_values: dict[str, list[Decimal]] = defaultdict(list)

    for record in records:
        if record["amount"] is not None:
            city_values[record["city"]].append(record["amount"])

    medians: dict[str, Decimal] = {}

    for city, values in city_values.items():
        ordered = sorted(values)
        middle = len(ordered) // 2

        if len(ordered) % 2:
            medians[city] = ordered[middle]
        else:
            medians[city] = (ordered[middle - 1] + ordered[middle]) / 2

    for row_index, record in enumerate(records, start=2):
        if record["amount"] is None and record["city"] in medians:
            replacement = medians[record["city"]]
            record["amount"] = replacement
            issues.append(
                CleaningIssue(
                    row_index,
                    "amount",
                    "missing_value",
                    None,
                    replacement,
                    "imputed",
                    "Missing transaction amount was replaced by the city-level median.",
                )
            )


def validate_dataset(records: list[dict[str, Any]]) -> dict[int, list[str]]:
    failures: dict[int, list[str]] = {}

    for index, record in enumerate(records, start=2):
        errors = validate_record(record)
        if errors:
            failures[index] = errors

    return failures


def calculate_quality_report(
    original: list[dict[str, Any]],
    cleaned: list[dict[str, Any]],
    issues: list[CleaningIssue],
) -> QualityReport:
    missing_cells = sum(
        value is None
        for record in original
        for value in record.values()
    )

    duplicate_rows = sum(issue.issue_type == "duplicate" for issue in issues)
    inconsistent_cells = sum(
        issue.issue_type == "inconsistent_representation"
        for issue in issues
    )
    rejected_rows = len(
        {
            issue.row_number
            for issue in issues
            if issue.action == "rejected"
        }
    )

    complete_rows = sum(
        all(value is not None for value in record.values())
        for record in cleaned
    )

    return QualityReport(
        total_rows=len(original),
        complete_rows=complete_rows,
        missing_cells=missing_cells,
        duplicate_rows=duplicate_rows,
        inconsistent_cells=inconsistent_cells,
        rejected_rows=rejected_rows,
    )


def export_clean_csv(records: list[dict[str, Any]]) -> str:
    fields = [
        "customer_id",
        "name",
        "email",
        "phone",
        "city",
        "amount",
        "currency",
        "status",
        "signup_date",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()

    for record in records:
        serialized = dict(record)
        if serialized["amount"] is not None:
            serialized["amount"] = format(serialized["amount"], "f")
        writer.writerow(serialized)

    return output.getvalue()


def print_issue_audit(issues: Iterable[CleaningIssue]) -> None:
    print("\nCLEANING AUDIT")
    print("=" * 80)

    for issue in issues:
        print(
            f"row={issue.row_number} "
            f"field={issue.field} "
            f"type={issue.issue_type} "
            f"action={issue.action} "
            f"original={issue.original_value!r} "
            f"cleaned={issue.cleaned_value!r}"
        )


def print_quality_report(report: QualityReport) -> None:
    print("\nDATA QUALITY REPORT")
    print("=" * 80)
    print(f"Rows received:              {report.total_rows}")
    print(f"Complete cleaned rows:      {report.complete_rows}")
    print(f"Missing source cells:       {report.missing_cells}")
    print(f"Duplicate rows removed:     {report.duplicate_rows}")
    print(f"Inconsistent values fixed: {report.inconsistent_cells}")
    print(f"Rejected rows:              {report.rejected_rows}")
    print(f"Completeness after cleaning:{report.completeness_rate:7.2f}%")


def demonstrate_deduplication() -> None:
    print("\nDUPLICATE DETECTION")
    print("=" * 80)

    examples = [
        {"id": "A", "email": "USER@example.com", "city": "Lucknow"},
        {"id": "A", "email": "user@example.com", "city": "lucknow"},
        {"id": "B", "email": "other@example.com", "city": "Kanpur"},
    ]

    normalized = []

    for record in examples:
        normalized.append(
            {
                "id": record["id"],
                "email": normalize_email(record["email"]),
                "city": normalize_city(record["city"]),
            }
        )

    groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)

    for index, record in enumerate(normalized):
        key = tuple(record.values())
        groups[key].append(index)

    for key, indexes in groups.items():
        print(f"{key}: rows {indexes}")


def demonstrate_missing_value_strategies(records: list[dict[str, Any]]) -> None:
    print("\nMISSING-VALUE STRATEGY")
    print("=" * 80)

    for field in ("email", "phone", "amount", "signup_date"):
        missing = sum(record.get(field) is None for record in records)
        print(f"{field:12} missing={missing}")

    print(
        "\nThe pipeline deliberately does not replace every missing field with "
        "a default. Identifier and contact fields can require preservation of "
        "unknown state, while the transaction amount has a documented "
        "city-level median imputation rule."
    )


def demonstrate_json_serialization(records: list[dict[str, Any]]) -> None:
    print("\nSTRUCTURED OUTPUT")
    print("=" * 80)

    serializable = []

    for record in records:
        item = dict(record)
        if isinstance(item["amount"], Decimal):
            item["amount"] = str(item["amount"])
        serializable.append(item)

    print(json.dumps(serializable[:2], indent=2))


def main() -> None:
    print("DATA CLEANING PIPELINE")
    print("=" * 80)
    print("Domain: customer transaction records")
    print("Focus: missing values, duplicates, and inconsistent representations")

    raw_records = parse_csv(RAW_CSV)

    print(f"\nSource rows loaded: {len(raw_records)}")

    cleaned_records, issues = clean_records(raw_records)

    impute_missing_amounts(cleaned_records, issues)

    validation_failures = validate_dataset(cleaned_records)

    for row_number, errors in validation_failures.items():
        print(f"\nValidation failure at row {row_number}:")
        for error in errors:
            print(f"  {error}")

    report = calculate_quality_report(raw_records, cleaned_records, issues)

    print_quality_report(report)
    print_issue_audit(issues)
    demonstrate_deduplication()
    demonstrate_missing_value_strategies(cleaned_records)
    demonstrate_json_serialization(cleaned_records)

    print("\nCLEANED RECORDS")
    print("=" * 80)

    for record in cleaned_records:
        print(record)

    print("\nCLEANED CSV")
    print("=" * 80)
    print(export_clean_csv(cleaned_records))


if __name__ == "__main__":
    main()
