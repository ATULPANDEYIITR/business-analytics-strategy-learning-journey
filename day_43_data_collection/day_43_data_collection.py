"""
Data Collection: Internal, External, Transactional, and Behavioral Data

A self-contained implementation of a data collection pipeline for an
online retail business. It demonstrates source-specific collection,
validation, normalization, provenance, deduplication, consent handling,
data quality checks, aggregation, JSON/CSV export, and audit logging.

Run:
    python data_collection.py

Only the Python standard library is required.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
import statistics
import tempfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
LOGGER = logging.getLogger("data_collection")


class DataCategory(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    TRANSACTIONAL = "transactional"
    BEHAVIORAL = "behavioral"


class CollectionError(ValueError):
    """Raised when a collected record violates a source-specific rule."""


@dataclass(frozen=True)
class CollectionContext:
    source: str
    category: DataCategory
    collected_at: datetime
    lawful_basis: str
    purpose: str
    schema_version: str = "1.0"


@dataclass
class DataRecord:
    record_id: str
    category: DataCategory
    source: str
    collected_at: datetime
    observed_at: datetime
    payload: dict[str, Any]
    purpose: str
    lawful_basis: str
    schema_version: str
    quality_issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category.value
        result["collected_at"] = self.collected_at.isoformat()
        result["observed_at"] = self.observed_at.isoformat()
        return result


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: str | datetime) -> datetime:
    """Normalize timestamps to UTC and reject ambiguous or invalid values."""
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise CollectionError(f"Invalid timestamp: {value}") from exc
    else:
        raise CollectionError("Timestamp must be a datetime or ISO-8601 string.")

    if parsed.tzinfo is None:
        raise CollectionError("Timestamp must include a timezone.")

    return parsed.astimezone(timezone.utc)


def normalize_email(value: str) -> str:
    """Normalize an email address without claiming that it is deliverable."""
    if not isinstance(value, str):
        raise CollectionError("Email must be a string.")

    email = value.strip().lower()

    if len(email) > 254 or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+", email
    ):
        raise CollectionError("Invalid email format.")

    return email


def parse_amount(value: Any) -> Decimal:
    """Use Decimal to avoid binary floating-point errors in money values."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CollectionError(f"Invalid monetary amount: {value}") from exc

    if not amount.is_finite() or amount < 0:
        raise CollectionError("Amount must be finite and non-negative.")

    if amount.as_tuple().exponent < -2:
        raise CollectionError("Amount cannot contain fractions of a cent.")

    return amount.quantize(Decimal("0.01"))


def stable_fingerprint(source: str, external_id: str) -> str:
    """Create a deterministic key without exposing the raw external ID."""
    if not source.strip() or not external_id.strip():
        raise CollectionError("Source and external ID are required.")

    material = f"{source.strip().lower()}:{external_id.strip()}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class ConsentRegistry:
    """
    Track purpose-specific collection permission.

    A production registry would also need a reliable identity resolution
    mechanism, consent evidence, retention rules, and withdrawal timestamps.
    """

    def __init__(self) -> None:
        self._permissions: dict[tuple[str, str], bool] = {}

    def set_permission(
        self, subject_id: str, purpose: str, allowed: bool
    ) -> None:
        if not subject_id.strip() or not purpose.strip():
            raise CollectionError("Subject and purpose are required.")

        self._permissions[(subject_id, purpose)] = allowed

    def allows(self, subject_id: str, purpose: str) -> bool:
        return self._permissions.get((subject_id, purpose), False)


class DataCollector:
    """Collect heterogeneous records into a consistent, auditable format."""

    ALLOWED_CATEGORIES = set(DataCategory)

    def __init__(self, consent_registry: ConsentRegistry) -> None:
        self.consent_registry = consent_registry
        self.records: dict[str, DataRecord] = {}
        self.rejected_records: list[dict[str, str]] = []

    def collect(
        self,
        context: CollectionContext,
        external_id: str,
        observed_at: str | datetime,
        payload: dict[str, Any],
        subject_id: str | None = None,
        requires_consent: bool = False,
    ) -> DataRecord:
        if context.category not in self.ALLOWED_CATEGORIES:
            raise CollectionError("Unsupported data category.")

        if not context.source.strip() or not context.purpose.strip():
            raise CollectionError("Source and purpose are required.")

        if not context.lawful_basis.strip():
            raise CollectionError("A documented collection basis is required.")

        if not isinstance(payload, dict) or not payload:
            raise CollectionError("Payload must be a non-empty dictionary.")

        if requires_consent:
            if not subject_id or not self.consent_registry.allows(
                subject_id, context.purpose
            ):
                raise CollectionError(
                    "Collection rejected: purpose-specific consent is absent."
                )

        fingerprint = stable_fingerprint(context.source, external_id)

        if fingerprint in self.records:
            existing = self.records[fingerprint]
            if existing.payload == payload:
                LOGGER.info("Duplicate record ignored: %s", fingerprint[:12])
                return existing

            raise CollectionError(
                "Conflicting duplicate detected; investigate source revision."
            )

        record = DataRecord(
            record_id=fingerprint,
            category=context.category,
            source=context.source.strip(),
            collected_at=parse_timestamp(context.collected_at),
            observed_at=parse_timestamp(observed_at),
            payload=payload.copy(),
            purpose=context.purpose.strip(),
            lawful_basis=context.lawful_basis.strip(),
            schema_version=context.schema_version,
        )

        if record.observed_at > record.collected_at:
            record.quality_issues.append("Observation occurs after collection.")

        self.records[fingerprint] = record
        LOGGER.info(
            "Collected %s record from %s",
            record.category.value,
            record.source,
        )
        return record

    def collect_safely(self, *args: Any, **kwargs: Any) -> DataRecord | None:
        """Reject malformed input without stopping the entire ingestion batch."""
        try:
            return self.collect(*args, **kwargs)
        except (CollectionError, TypeError, AttributeError) as exc:
            self.rejected_records.append(
                {
                    "reason": str(exc),
                    "source": str(
                        args[0].source if args and isinstance(
                            args[0], CollectionContext
                        ) else kwargs.get("context", "unknown")
                    ),
                }
            )
            LOGGER.warning("Record rejected: %s", exc)
            return None


def collect_internal_metrics(collector: DataCollector) -> None:
    """Internal data originates in systems owned or operated by the business."""
    now = utc_now()
    context = CollectionContext(
        source="erp_inventory",
        category=DataCategory.INTERNAL,
        collected_at=now,
        lawful_basis="documented_business_purpose",
        purpose="inventory_reconciliation",
    )

    collector.collect(
        context,
        "inventory-snapshot-2026-10-13",
        now,
        {
            "warehouse": "DEL-01",
            "sku": "LAPTOP-14",
            "available_units": 184,
            "reserved_units": 16,
        },
    )


def collect_external_market_data(collector: DataCollector) -> None:
    """External data arrives from a supplier or a licensed data provider."""
    now = utc_now()
    context = CollectionContext(
        source="supplier_catalog_api",
        category=DataCategory.EXTERNAL,
        collected_at=now,
        lawful_basis="contract_and_documented_purpose",
        purpose="supplier_price_comparison",
    )

    collector.collect(
        context,
        "supplier-feed-8842",
        now,
        {
            "supplier": "Northstar Components",
            "sku": "LAPTOP-14",
            "unit_price": "64500.00",
            "currency": "INR",
            "feed_revision": "r18",
        },
    )


def collect_transaction(
    collector: DataCollector,
    order_id: str,
    customer_id: str,
    amount: str,
    currency: str = "INR",
) -> DataRecord:
    """
    Transactional data represents a business event with monetary and
    operational consequences, not merely an observed click or page view.
    """
    now = utc_now()
    context = CollectionContext(
        source="order_management",
        category=DataCategory.TRANSACTIONAL,
        collected_at=now,
        lawful_basis="contract_performance",
        purpose="order_fulfillment_and_reconciliation",
    )

    normalized_amount = parse_amount(amount)

    return collector.collect(
        context,
        order_id,
        now,
        {
            "order_id": order_id,
            "customer_id": customer_id,
            "amount": str(normalized_amount),
            "currency": currency.upper(),
            "status": "paid",
            "items": [
                {"sku": "LAPTOP-14", "quantity": 1},
                {"sku": "USB-C-DOCK", "quantity": 1},
            ],
        },
    )


def collect_behavioral_event(
    collector: DataCollector,
    consent: ConsentRegistry,
    visitor_id: str,
    event_id: str,
    event_type: str,
    page_path: str,
    occurred_at: datetime,
) -> DataRecord | None:
    """
    Behavioral data records interactions. It is collected only when the
    registry authorizes the declared purpose in this example.
    """
    permitted_event_types = {
        "page_view",
        "product_view",
        "add_to_cart",
        "search",
        "checkout_started",
    }

    if event_type not in permitted_event_types:
        raise CollectionError(f"Unsupported behavioral event: {event_type}")

    if not page_path.startswith("/") or page_path.startswith("//"):
        raise CollectionError("Page path must be a relative application path.")

    context = CollectionContext(
        source="web_analytics",
        category=DataCategory.BEHAVIORAL,
        collected_at=utc_now(),
        lawful_basis="consent",
        purpose="product_experience_analytics",
    )

    return collector.collect_safely(
        context,
        event_id,
        occurred_at,
        {
            "visitor_id": visitor_id,
            "event_type": event_type,
            "page_path": page_path,
        },
        subject_id=visitor_id,
        requires_consent=True,
    )


def assess_record_quality(record: DataRecord) -> list[str]:
    """Apply category-specific rules without mixing different data meanings."""
    issues = list(record.quality_issues)
    payload = record.payload

    if record.category == DataCategory.INTERNAL:
        for field_name in ("available_units", "reserved_units"):
            value = payload.get(field_name)
            if not isinstance(value, int) or value < 0:
                issues.append(f"{field_name} must be a non-negative integer.")

        if (
            isinstance(payload.get("available_units"), int)
            and isinstance(payload.get("reserved_units"), int)
            and payload["reserved_units"] > payload["available_units"]
        ):
            issues.append("Reserved units exceed available units.")

    elif record.category == DataCategory.EXTERNAL:
        if not payload.get("supplier"):
            issues.append("Supplier identity is missing.")
        if "unit_price" in payload:
            try:
                parse_amount(payload["unit_price"])
            except CollectionError as exc:
                issues.append(str(exc))
        if payload.get("currency") not in {"INR", "USD", "EUR", "GBP"}:
            issues.append("Unsupported or missing currency.")

    elif record.category == DataCategory.TRANSACTIONAL:
        try:
            parse_amount(payload.get("amount"))
        except CollectionError as exc:
            issues.append(str(exc))

        if payload.get("status") not in {
            "pending",
            "paid",
            "refunded",
            "cancelled",
        }:
            issues.append("Invalid transaction status.")

        if not payload.get("order_id") or not payload.get("customer_id"):
            issues.append("Order and customer identifiers are required.")

    elif record.category == DataCategory.BEHAVIORAL:
        if payload.get("event_type") not in {
            "page_view",
            "product_view",
            "add_to_cart",
            "search",
            "checkout_started",
        }:
            issues.append("Unknown behavioral event type.")

        if not str(payload.get("page_path", "")).startswith("/"):
            issues.append("Behavioral page path must be relative.")

    return sorted(set(issues))


def profile_collection(records: Iterable[DataRecord]) -> dict[str, Any]:
    """Produce a compact quality and provenance profile for a batch."""
    records = list(records)
    by_category = Counter(record.category.value for record in records)
    by_source = Counter(record.source for record in records)
    quality_counts = Counter()

    for record in records:
        quality_counts.update(assess_record_quality(record))

    return {
        "record_count": len(records),
        "records_by_category": dict(sorted(by_category.items())),
        "records_by_source": dict(sorted(by_source.items())),
        "quality_issues": dict(sorted(quality_counts.items())),
        "collection_window": {
            "start": min(
                (record.collected_at for record in records),
                default=None,
            ).isoformat()
            if records
            else None,
            "end": max(
                (record.collected_at for record in records),
                default=None,
            ).isoformat()
            if records
            else None,
        },
    }


def summarize_transactions(records: Iterable[DataRecord]) -> dict[str, Any]:
    """
    Aggregate business transactions separately from behavioral events.
    Only paid INR orders are included in the example revenue measure.
    """
    amounts: list[Decimal] = []

    for record in records:
        if record.category != DataCategory.TRANSACTIONAL:
            continue
        if record.payload.get("status") != "paid":
            continue
        if record.payload.get("currency") != "INR":
            continue

        try:
            amounts.append(parse_amount(record.payload["amount"]))
        except (KeyError, CollectionError):
            LOGGER.warning("Invalid transaction excluded from revenue.")

    total = sum(amounts, Decimal("0.00"))
    average = (
        total / Decimal(len(amounts))
        if amounts
        else Decimal("0.00")
    )

    return {
        "paid_order_count": len(amounts),
        "revenue_inr": str(total.quantize(Decimal("0.01"))),
        "average_order_value_inr": str(
            average.quantize(Decimal("0.01"))
        ),
        "median_order_value_inr": str(
            Decimal(str(statistics.median(amounts))).quantize(
                Decimal("0.01")
            )
        ) if amounts else "0.00",
    }


def summarize_behavior(records: Iterable[DataRecord]) -> dict[str, Any]:
    """Count approved behavioral events by event type and page."""
    event_counts: Counter[str] = Counter()
    page_counts: Counter[str] = Counter()
    visitor_events: dict[str, set[str]] = defaultdict(set)

    for record in records:
        if record.category != DataCategory.BEHAVIORAL:
            continue

        event_counts[str(record.payload["event_type"])] += 1
        page_counts[str(record.payload["page_path"])] += 1
        visitor_events[str(record.payload["visitor_id"])].add(
            str(record.payload["event_type"])
        )

    return {
        "events_by_type": dict(sorted(event_counts.items())),
        "events_by_page": dict(sorted(page_counts.items())),
        "unique_visitors": len(visitor_events),
        "visitors_with_checkout_activity": sum(
            "checkout_started" in events
            for events in visitor_events.values()
        ),
    }


def export_json(records: Iterable[DataRecord], path: Path) -> None:
    """Write normalized records as UTF-8 JSON with explicit timestamps."""
    rows = [record.to_dict() for record in records]
    path.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def export_csv(records: Iterable[DataRecord], path: Path) -> None:
    """
    Keep payload as JSON text in CSV because the four categories have
    different fields. A production warehouse would generally use typed
    columns or normalized tables for important business attributes.
    """
    fieldnames = [
        "record_id",
        "category",
        "source",
        "collected_at",
        "observed_at",
        "purpose",
        "lawful_basis",
        "schema_version",
        "payload",
        "quality_issues",
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            row = record.to_dict()
            row["payload"] = json.dumps(
                row["payload"],
                ensure_ascii=False,
                sort_keys=True,
            )
            row["quality_issues"] = json.dumps(
                assess_record_quality(record)
            )
            writer.writerow(row)


def demo() -> None:
    consent = ConsentRegistry()
    consent.set_permission(
        "visitor-201",
        "product_experience_analytics",
        True,
    )
    consent.set_permission(
        "visitor-202",
        "product_experience_analytics",
        False,
    )

    collector = DataCollector(consent)

    collect_internal_metrics(collector)
    collect_external_market_data(collector)

    collect_transaction(
        collector,
        "ORD-2026-1001",
        "CUS-0081",
        "72999.90",
    )
    collect_transaction(
        collector,
        "ORD-2026-1002",
        "CUS-0097",
        "64999.00",
    )

    event_time = utc_now()
    collect_behavioral_event(
        collector,
        consent,
        "visitor-201",
        "evt-5001",
        "product_view",
        "/products/laptop-14",
        event_time,
    )
    collect_behavioral_event(
        collector,
        consent,
        "visitor-201",
        "evt-5002",
        "add_to_cart",
        "/products/laptop-14",
        event_time,
    )
    collect_behavioral_event(
        collector,
        consent,
        "visitor-201",
        "evt-5003",
        "checkout_started",
        "/checkout",
        event_time,
    )

    # This event is rejected because its collection purpose is not authorized.
    collect_behavioral_event(
        collector,
        consent,
        "visitor-202",
        "evt-5004",
        "page_view",
        "/home",
        event_time,
    )

    # Exact duplicate ingestion is idempotent; a conflicting duplicate fails.
    original = next(
        record for record in collector.records.values()
        if record.category == DataCategory.INTERNAL
    )
    duplicate_context = CollectionContext(
        source=original.source,
        category=original.category,
        collected_at=utc_now(),
        lawful_basis=original.lawful_basis,
        purpose=original.purpose,
    )
    collector.collect(
        duplicate_context,
        "inventory-snapshot-2026-10-13",
        original.observed_at,
        original.payload,
    )

    records = list(collector.records.values())

    print("\nCollection profile")
    print(json.dumps(profile_collection(records), indent=2))

    print("\nTransactional analysis")
    print(json.dumps(summarize_transactions(records), indent=2))

    print("\nBehavioral analysis")
    print(json.dumps(summarize_behavior(records), indent=2))

    print("\nRejected records")
    print(json.dumps(collector.rejected_records, indent=2))

    with tempfile.TemporaryDirectory(prefix="data_collection_") as directory:
        output_directory = Path(directory)
        export_json(records, output_directory / "records.json")
        export_csv(records, output_directory / "records.csv")
        print(f"\nJSON export: {output_directory / 'records.json'}")
        print(f"CSV export:  {output_directory / 'records.csv'}")
        print("Export files are available while this demonstration runs.")


if __name__ == "__main__":
    demo()
