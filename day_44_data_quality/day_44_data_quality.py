"""
Data Quality Engineering
Covers accuracy, completeness, consistency, and validity through
executable validation, profiling, rule evaluation, remediation, and reporting.

The implementation uses only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable
import csv
import io
import json
import re
from collections import Counter, defaultdict


# ---------------------------------------------------------------------------
# Core data-quality model
# ---------------------------------------------------------------------------

class QualityDimension:
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    VALIDITY = "validity"


@dataclass
class Issue:
    dimension: str
    field: str
    record_id: str
    message: str
    value: Any = None
    severity: str = "error"

    def as_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "field": self.field,
            "record_id": self.record_id,
            "message": self.message,
            "value": self.value,
            "severity": self.severity,
        }


@dataclass
class QualityResult:
    passed: bool
    issues: list[Issue] = field(default_factory=list)

    def add(self, issue: Issue) -> None:
        self.issues.append(issue)
        self.passed = False


@dataclass
class QualityReport:
    total_records: int
    valid_records: int
    issues: list[Issue]
    dimension_scores: dict[str, float]

    @property
    def overall_score(self) -> float:
        if not self.dimension_scores:
            return 100.0
        return sum(self.dimension_scores.values()) / len(self.dimension_scores)

    def summary(self) -> dict[str, Any]:
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.total_records - self.valid_records,
            "issue_count": len(self.issues),
            "dimension_scores": self.dimension_scores,
            "overall_score": round(self.overall_score, 2),
        }


# ---------------------------------------------------------------------------
# Validation primitives
# ---------------------------------------------------------------------------

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)

COUNTRY_CODES = {"IN", "US", "GB", "DE", "FR", "JP", "SG", "AU"}

ALLOWED_STATUSES = {"active", "inactive", "pending"}

EXPECTED_CURRENCY_BY_COUNTRY = {
    "IN": "INR",
    "US": "USD",
    "GB": "GBP",
    "DE": "EUR",
    "FR": "EUR",
    "JP": "JPY",
    "SG": "SGD",
    "AU": "AUD",
}


def is_non_empty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def parse_decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def parse_iso_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


def valid_email(value: Any) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(str(value).strip()))


# ---------------------------------------------------------------------------
# Accuracy
#
# Accuracy asks whether a value represents the real-world fact it is
# supposed to represent. A syntactically valid value can still be inaccurate.
# For example, an email can have a valid shape but belong to the wrong person.
# ---------------------------------------------------------------------------

def check_accuracy(record: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    record_id = str(record["customer_id"])

    # The expected values below represent independently verified reference
    # information. This is different from checking whether a value merely has
    # an acceptable format.
    verified = {
        "C1001": {
            "email": "atul@example.com",
            "country": "IN",
            "currency": "INR",
        },
        "C1002": {
            "email": "maria@example.com",
            "country": "DE",
            "currency": "EUR",
        },
    }

    reference = verified.get(record_id)
    if reference:
        for field_name, expected in reference.items():
            actual = record.get(field_name)
            if actual != expected:
                issues.append(
                    Issue(
                        QualityDimension.ACCURACY,
                        field_name,
                        record_id,
                        f"Value differs from the verified reference value {expected!r}.",
                        actual,
                    )
                )

    # Country and currency also provide a cross-source accuracy check when
    # the reference table contains the country-to-currency mapping.
    country = record.get("country")
    currency = record.get("currency")
    expected_currency = EXPECTED_CURRENCY_BY_COUNTRY.get(country)
    if expected_currency and currency != expected_currency:
        issues.append(
            Issue(
                QualityDimension.ACCURACY,
                "currency",
                record_id,
                f"Currency does not match the verified country mapping for {country}.",
                currency,
            )
        )

    return issues


# ---------------------------------------------------------------------------
# Completeness
#
# Completeness checks whether required information exists. Empty strings,
# whitespace, and missing keys are treated as absent.
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {
    "customer_id",
    "name",
    "email",
    "country",
    "currency",
    "status",
    "signup_date",
    "credit_limit",
}


def check_completeness(record: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    record_id = str(record.get("customer_id", "<missing-id>"))

    for field_name in REQUIRED_FIELDS:
        if not is_non_empty(record.get(field_name)):
            issues.append(
                Issue(
                    QualityDimension.COMPLETENESS,
                    field_name,
                    record_id,
                    "Required value is missing or empty.",
                    record.get(field_name),
                )
            )

    return issues


# ---------------------------------------------------------------------------
# Validity
#
# Validity checks whether values conform to formally defined rules such as
# type, range, enumeration, format, and domain constraints.
# ---------------------------------------------------------------------------

def check_validity(record: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    record_id = str(record.get("customer_id", "<missing-id>"))

    country = record.get("country")
    if country not in COUNTRY_CODES:
        issues.append(
            Issue(
                QualityDimension.VALIDITY,
                "country",
                record_id,
                "Country code is outside the accepted ISO-like domain.",
                country,
            )
        )

    status = record.get("status")
    if status not in ALLOWED_STATUSES:
        issues.append(
            Issue(
                QualityDimension.VALIDITY,
                "status",
                record_id,
                "Status is not an accepted domain value.",
                status,
            )
        )

    email = record.get("email")
    if is_non_empty(email) and not valid_email(email):
        issues.append(
            Issue(
                QualityDimension.VALIDITY,
                "email",
                record_id,
                "Email does not conform to the required format.",
                email,
            )
        )

    signup_date = record.get("signup_date")
    if is_non_empty(signup_date):
        parsed_date = parse_iso_date(signup_date)
        if parsed_date is None:
            issues.append(
                Issue(
                    QualityDimension.VALIDITY,
                    "signup_date",
                    record_id,
                    "Date must use YYYY-MM-DD format.",
                    signup_date,
                )
            )
        elif parsed_date > date.today():
            issues.append(
                Issue(
                    QualityDimension.VALIDITY,
                    "signup_date",
                    record_id,
                    "Signup date cannot be in the future.",
                    signup_date,
                )
            )

    credit_limit = parse_decimal(record.get("credit_limit"))
    if credit_limit is None:
        issues.append(
            Issue(
                QualityDimension.VALIDITY,
                "credit_limit",
                record_id,
                "Credit limit must be numeric.",
                record.get("credit_limit"),
            )
        )
    elif credit_limit < 0:
        issues.append(
            Issue(
                QualityDimension.VALIDITY,
                "credit_limit",
                record_id,
                "Credit limit cannot be negative.",
                record.get("credit_limit"),
            )
        )

    return issues


# ---------------------------------------------------------------------------
# Consistency
#
# Consistency checks relationships among values. A record can contain only
# valid values and still be inconsistent if those values contradict one another.
# ---------------------------------------------------------------------------

def check_consistency(record: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    record_id = str(record.get("customer_id", "<missing-id>"))

    status = record.get("status")
    credit_limit = parse_decimal(record.get("credit_limit"))

    if status == "inactive" and credit_limit is not None and credit_limit > 0:
        issues.append(
            Issue(
                QualityDimension.CONSISTENCY,
                "credit_limit",
                record_id,
                "Inactive customers should not retain a positive active credit limit.",
                credit_limit,
            )
        )

    country = record.get("country")
    currency = record.get("currency")
    expected_currency = EXPECTED_CURRENCY_BY_COUNTRY.get(country)

    if expected_currency and currency and currency != expected_currency:
        issues.append(
            Issue(
                QualityDimension.CONSISTENCY,
                "currency",
                record_id,
                "Country and currency contradict each other.",
                currency,
            )
        )

    name = str(record.get("name", "")).strip()
    if name and any(character.isdigit() for character in name):
        issues.append(
            Issue(
                QualityDimension.CONSISTENCY,
                "name",
                record_id,
                "Customer name contains numeric characters.",
                name,
            )
        )

    return issues


# ---------------------------------------------------------------------------
# Dataset-level rules
# ---------------------------------------------------------------------------

def check_duplicate_ids(records: Iterable[dict[str, Any]]) -> list[Issue]:
    issues: list[Issue] = []
    counts = Counter(str(record.get("customer_id")) for record in records)

    for customer_id, count in counts.items():
        if customer_id == "None" or count <= 1:
            continue
        issues.append(
            Issue(
                QualityDimension.CONSISTENCY,
                "customer_id",
                customer_id,
                f"Customer identifier occurs {count} times.",
                customer_id,
            )
        )

    return issues


def check_cross_record_email_uniqueness(
    records: Iterable[dict[str, Any]]
) -> list[Issue]:
    issues: list[Issue] = []
    owners: defaultdict[str, list[str]] = defaultdict(list)

    for record in records:
        email = str(record.get("email", "")).strip().lower()
        if email:
            owners[email].append(str(record.get("customer_id")))

    for email, ids in owners.items():
        if len(ids) > 1:
            for customer_id in ids:
                issues.append(
                    Issue(
                        QualityDimension.CONSISTENCY,
                        "email",
                        customer_id,
                        "Email address is assigned to multiple customer records.",
                        email,
                    )
                )

    return issues


# ---------------------------------------------------------------------------
# Data profiling
# ---------------------------------------------------------------------------

def profile_column(records: list[dict[str, Any]], field_name: str) -> dict[str, Any]:
    values = [record.get(field_name) for record in records]
    non_empty = [value for value in values if is_non_empty(value)]

    return {
        "field": field_name,
        "row_count": len(values),
        "non_null_count": len(non_empty),
        "missing_count": len(values) - len(non_empty),
        "completeness_rate": (
            len(non_empty) / len(values) if values else 1.0
        ),
        "distinct_count": len({str(value) for value in non_empty}),
    }


def profile_dataset(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = sorted({key for record in records for key in record})
    return [profile_column(records, field_name) for field_name in fields]


# ---------------------------------------------------------------------------
# Quality scoring
#
# Each dimension is scored using issue-free record observations. The score is
# deliberately simple: it is useful for operational monitoring but should not
# be confused with a universal statistical measure of data quality.
# ---------------------------------------------------------------------------

def calculate_dimension_scores(
    records: list[dict[str, Any]],
    issues: list[Issue],
) -> dict[str, float]:
    total = len(records)

    if total == 0:
        return {
            QualityDimension.ACCURACY: 100.0,
            QualityDimension.COMPLETENESS: 100.0,
            QualityDimension.CONSISTENCY: 100.0,
            QualityDimension.VALIDITY: 100.0,
        }

    affected: dict[str, set[str]] = defaultdict(set)

    for issue in issues:
        affected[issue.dimension].add(issue.record_id)

    return {
        dimension: round(
            100 * (total - len(affected[dimension])) / total,
            2,
        )
        for dimension in (
            QualityDimension.ACCURACY,
            QualityDimension.COMPLETENESS,
            QualityDimension.CONSISTENCY,
            QualityDimension.VALIDITY,
        )
    }


# ---------------------------------------------------------------------------
# Quality engine
# ---------------------------------------------------------------------------

class DataQualityEngine:
    def validate(self, records: list[dict[str, Any]]) -> QualityReport:
        issues: list[Issue] = []

        for record in records:
            issues.extend(check_completeness(record))
            issues.extend(check_validity(record))
            issues.extend(check_consistency(record))
            issues.extend(check_accuracy(record))

        issues.extend(check_duplicate_ids(records))
        issues.extend(check_cross_record_email_uniqueness(records))

        invalid_ids = {issue.record_id for issue in issues}
        valid_records = sum(
            1 for record in records
            if str(record.get("customer_id")) not in invalid_ids
        )

        scores = calculate_dimension_scores(records, issues)

        return QualityReport(
            total_records=len(records),
            valid_records=valid_records,
            issues=issues,
            dimension_scores=scores,
        )


# ---------------------------------------------------------------------------
# Remediation
#
# Safe remediation is intentionally conservative. Missing values are not
# silently invented because imputation can create false accuracy.
# ---------------------------------------------------------------------------

def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)

    for key, value in normalized.items():
        if isinstance(value, str):
            normalized[key] = value.strip()

    if "email" in normalized and normalized["email"]:
        normalized["email"] = normalized["email"].lower()

    if "country" in normalized and normalized["country"]:
        normalized["country"] = normalized["country"].upper()

    if "currency" in normalized and normalized["currency"]:
        normalized["currency"] = normalized["currency"].upper()

    if "status" in normalized and normalized["status"]:
        normalized["status"] = normalized["status"].lower()

    return normalized


def quarantine_invalid_records(
    records: list[dict[str, Any]],
    report: QualityReport,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    invalid_ids = {issue.record_id for issue in report.issues}

    accepted = [
        record
        for record in records
        if str(record.get("customer_id")) not in invalid_ids
    ]

    quarantined = [
        record
        for record in records
        if str(record.get("customer_id")) in invalid_ids
    ]

    return accepted, quarantined


# ---------------------------------------------------------------------------
# CSV ingestion
# ---------------------------------------------------------------------------

def load_csv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def export_issues_json(report: QualityReport) -> str:
    payload = {
        "summary": report.summary(),
        "issues": [issue.as_dict() for issue in report.issues],
    }
    return json.dumps(payload, indent=2, default=str)


# ---------------------------------------------------------------------------
# Demonstration dataset
#
# The examples deliberately contain different failure types:
# - C1001 contains a verified email and valid INR mapping.
# - C1002 has a syntactically valid email but an inaccurate email value.
# - C1003 is incomplete.
# - C1004 has invalid country/status/date/credit-limit values.
# - C1005 is internally inconsistent.
# - C1006 creates a duplicate email condition.
# ---------------------------------------------------------------------------

RAW_DATA = """
customer_id,name,email,country,currency,status,signup_date,credit_limit
C1001,Atul Pandey,atul@example.com,IN,INR,active,2026-01-15,500000
C1002,Maria Silva,maria.changed@example.com,DE,EUR,active,2026-02-12,75000
C1003,Ravi Kumar,,IN,INR,pending,2026-03-10,25000
C1004,Elena7,elena@example,XX,USD,unknown,2027-04-01,-500
C1005,John Smith,john@example.com,US,EUR,inactive,2026-02-01,1000
C1006,Duplicate User,atul@example.com,IN,INR,active,2026-04-01,30000
"""


def print_report(report: QualityReport) -> None:
    print("\nDATA QUALITY REPORT")
    print("=" * 72)

    for key, value in report.summary().items():
        print(f"{key}: {value}")

    print("\nISSUES")
    print("-" * 72)

    if not report.issues:
        print("No quality issues detected.")
        return

    for issue in report.issues:
        print(
            f"[{issue.dimension.upper()}] "
            f"{issue.record_id}.{issue.field}: {issue.message} "
            f"(value={issue.value!r})"
        )


def demonstrate_profiling(records: list[dict[str, Any]]) -> None:
    print("\nDATA PROFILE")
    print("=" * 72)

    for profile in profile_dataset(records):
        print(
            f"{profile['field']}: "
            f"rows={profile['row_count']}, "
            f"missing={profile['missing_count']}, "
            f"distinct={profile['distinct_count']}, "
            f"completeness={profile['completeness_rate']:.2%}"
        )


def demonstrate_remediation(records: list[dict[str, Any]]) -> None:
    print("\nNORMALIZATION")
    print("=" * 72)

    normalized = [normalize_record(record) for record in records]

    for before, after in zip(records, normalized):
        if before != after:
            print(
                f"{before.get('customer_id')}: "
                f"email={before.get('email')!r} -> {after.get('email')!r}, "
                f"country={before.get('country')!r} -> {after.get('country')!r}"
            )

    engine = DataQualityEngine()
    report = engine.validate(normalized)
    accepted, quarantined = quarantine_invalid_records(normalized, report)

    print(f"\nAccepted records: {len(accepted)}")
    print(f"Quarantined records: {len(quarantined)}")


def demonstrate_edge_cases() -> None:
    print("\nEDGE CASE VALIDATION")
    print("=" * 72)

    cases = [
        {
            "customer_id": "EDGE-1",
            "name": "Valid Customer",
            "email": "valid@example.com",
            "country": "IN",
            "currency": "INR",
            "status": "active",
            "signup_date": date.today().isoformat(),
            "credit_limit": "0",
        },
        {
            "customer_id": "EDGE-2",
            "name": "Whitespace",
            "email": "   ",
            "country": "IN",
            "currency": "INR",
            "status": "pending",
            "signup_date": "not-a-date",
            "credit_limit": "unknown",
        },
    ]

    report = DataQualityEngine().validate(cases)

    for issue in report.issues:
        print(
            f"{issue.record_id}: "
            f"{issue.dimension} -> {issue.field}: {issue.message}"
        )


def main() -> None:
    records = load_csv(RAW_DATA.strip())

    demonstrate_profiling(records)

    engine = DataQualityEngine()
    report = engine.validate(records)

    print_report(report)

    print("\nISSUE EXPORT")
    print("=" * 72)
    print(export_issues_json(report))

    demonstrate_remediation(records)
    demonstrate_edge_cases()


if __name__ == "__main__":
    main()
