#!/usr/bin/env python3
"""
Executive performance dashboard data model.

Calculates management KPIs from monthly business-unit and regional
performance records. Supports CSV input, filtering, validation, alert
evaluation, JSON export, and built-in data-quality tests.

CSV columns:
period,business_unit,region,revenue,revenue_target,cogs,operating_expense,
orders,delivered_orders,on_time_orders,csat_score_sum,csat_responses

Monetary values use the same currency unit throughout the input.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable


TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0")
ONE_HUNDRED = Decimal("100")

CSV_FIELDS = {
    "period",
    "business_unit",
    "region",
    "revenue",
    "revenue_target",
    "cogs",
    "operating_expense",
    "orders",
    "delivered_orders",
    "on_time_orders",
    "csat_score_sum",
    "csat_responses",
}


@dataclass(frozen=True, slots=True)
class PerformanceRecord:
    period: date
    business_unit: str
    region: str
    revenue: Decimal
    revenue_target: Decimal
    cogs: Decimal
    operating_expense: Decimal
    orders: int
    delivered_orders: int
    on_time_orders: int
    csat_score_sum: Decimal
    csat_responses: int


@dataclass(frozen=True, slots=True)
class DashboardFilters:
    from_month: str | None = None
    to_month: str | None = None
    business_unit: str | None = None
    region: str | None = None


def decimal_value(value: Any, field_name: str) -> Decimal:
    """Convert an input value without introducing binary float errors."""
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} must be a valid decimal number") from exc

    if not result.is_finite():
        raise ValueError(f"{field_name} must be finite")

    return result


def integer_value(value: Any, field_name: str) -> int:
    """Reject fractional counts instead of silently rounding them."""
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc

    if not parsed.is_finite() or parsed != parsed.to_integral_value():
        raise ValueError(f"{field_name} must be an integer")

    return int(parsed)


def parse_month(value: str) -> date:
    """Convert YYYY-MM into the first calendar day of that month."""
    try:
        parsed = date.fromisoformat(f"{value.strip()}-01")
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid month '{value}'. Expected YYYY-MM.") from exc

    return parsed


def validate_record(record: PerformanceRecord) -> None:
    """Enforce record-level business rules before aggregation."""
    if record.period.day != 1:
        raise ValueError("period must be the first day of a calendar month")

    if not record.business_unit.strip():
        raise ValueError("business_unit cannot be empty")

    if not record.region.strip():
        raise ValueError("region cannot be empty")

    if record.revenue < ZERO:
        raise ValueError("revenue cannot be negative")

    if record.revenue_target <= ZERO:
        raise ValueError("revenue_target must be greater than zero")

    if record.cogs < ZERO or record.operating_expense < ZERO:
        raise ValueError("cost values cannot be negative")

    counts = (
        record.orders,
        record.delivered_orders,
        record.on_time_orders,
        record.csat_responses,
    )
    if any(value < 0 for value in counts):
        raise ValueError("order and survey counts cannot be negative")

    if record.delivered_orders > record.orders:
        raise ValueError("delivered_orders cannot exceed orders")

    if record.on_time_orders > record.delivered_orders:
        raise ValueError("on_time_orders cannot exceed delivered_orders")

    if record.csat_score_sum < ZERO:
        raise ValueError("csat_score_sum cannot be negative")

    # CSAT is assumed to use a 1-to-5 response scale.
    if record.csat_responses == 0:
        if record.csat_score_sum != ZERO:
            raise ValueError("CSAT score sum must be zero without responses")
    else:
        minimum = Decimal(record.csat_responses)
        maximum = Decimal(record.csat_responses) * Decimal("5")
        if not minimum <= record.csat_score_sum <= maximum:
            raise ValueError(
                "csat_score_sum is inconsistent with the response count "
                "and the 1-to-5 score scale"
            )


def validate_records(records: Iterable[PerformanceRecord]) -> list[PerformanceRecord]:
    """Validate records and reject duplicate monthly reporting keys."""
    validated: list[PerformanceRecord] = []
    seen: set[tuple[date, str, str]] = set()

    for record in records:
        validate_record(record)
        key = (record.period, record.business_unit, record.region)

        if key in seen:
            raise ValueError(
                "Duplicate performance record for "
                f"{record.period:%Y-%m}, {record.business_unit}, {record.region}"
            )

        seen.add(key)
        validated.append(record)

    if not validated:
        raise ValueError("The input dataset contains no performance records")

    return validated


def make_record(
    period: str,
    business_unit: str,
    region: str,
    revenue: str,
    revenue_target: str,
    cogs: str,
    operating_expense: str,
    orders: int,
    delivered_orders: int,
    on_time_orders: int,
    csat_score_sum: str,
    csat_responses: int,
) -> PerformanceRecord:
    return PerformanceRecord(
        period=parse_month(period),
        business_unit=business_unit,
        region=region,
        revenue=Decimal(revenue),
        revenue_target=Decimal(revenue_target),
        cogs=Decimal(cogs),
        operating_expense=Decimal(operating_expense),
        orders=orders,
        delivered_orders=delivered_orders,
        on_time_orders=on_time_orders,
        csat_score_sum=Decimal(csat_score_sum),
        csat_responses=csat_responses,
    )


def sample_records() -> list[PerformanceRecord]:
    """Three months of sample results across two units and two regions."""
    raw_rows = [
        ("2026-01", "Consumer", "North", "420000", "400000", "252000", "96000", 1200, 1160, 1080, "792", 180),
        ("2026-01", "Consumer", "South", "360000", "380000", "223200", "80000", 1050, 1000, 910, "615", 150),
        ("2026-01", "Enterprise", "North", "610000", "600000", "335500", "160000", 640, 620, 595, "414", 90),
        ("2026-01", "Enterprise", "South", "490000", "510000", "274400", "128000", 520, 500, 465, "344", 80),
        ("2026-02", "Consumer", "North", "440000", "420000", "264000", "99000", 1240, 1205, 1130, "810", 185),
        ("2026-02", "Consumer", "South", "370000", "385000", "229400", "83000", 1080, 1035, 950, "640", 155),
        ("2026-02", "Enterprise", "North", "635000", "620000", "349250", "165000", 660, 642, 615, "423", 92),
        ("2026-02", "Enterprise", "South", "505000", "520000", "282800", "131000", 535, 516, 480, "356", 82),
        ("2026-03", "Consumer", "North", "455000", "440000", "270725", "101000", 1280, 1250, 1180, "840", 190),
        ("2026-03", "Consumer", "South", "390000", "400000", "241800", "86000", 1120, 1080, 1000, "660", 160),
        ("2026-03", "Enterprise", "North", "660000", "650000", "363000", "170000", 680, 665, 640, "437", 95),
        ("2026-03", "Enterprise", "South", "530000", "535000", "296800", "135000", 550, 535, 500, "374", 85),
    ]

    return [
        make_record(*row)
        for row in raw_rows
    ]


def load_csv(path: Path) -> list[PerformanceRecord]:
    """Load a validated CSV file using explicit field conversion."""
    records: list[PerformanceRecord] = []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)

        if reader.fieldnames is None:
            raise ValueError("CSV file has no header")

        missing = CSV_FIELDS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        for line_number, row in enumerate(reader, start=2):
            try:
                records.append(
                    PerformanceRecord(
                        period=parse_month(row["period"]),
                        business_unit=row["business_unit"].strip(),
                        region=row["region"].strip(),
                        revenue=decimal_value(row["revenue"], "revenue"),
                        revenue_target=decimal_value(
                            row["revenue_target"], "revenue_target"
                        ),
                        cogs=decimal_value(row["cogs"], "cogs"),
                        operating_expense=decimal_value(
                            row["operating_expense"], "operating_expense"
                        ),
                        orders=integer_value(row["orders"], "orders"),
                        delivered_orders=integer_value(
                            row["delivered_orders"], "delivered_orders"
                        ),
                        on_time_orders=integer_value(
                            row["on_time_orders"], "on_time_orders"
                        ),
                        csat_score_sum=decimal_value(
                            row["csat_score_sum"], "csat_score_sum"
                        ),
                        csat_responses=integer_value(
                            row["csat_responses"], "csat_responses"
                        ),
                    )
                )
            except (KeyError, ValueError) as exc:
                raise ValueError(f"CSV line {line_number}: {exc}") from exc

    return validate_records(records)


def ratio_pct(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    """Return a percentage or None when the denominator is zero."""
    if denominator == ZERO:
        return None

    return (numerator / denominator * ONE_HUNDRED).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP
    )


def average(numerator: Decimal, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None

    return (numerator / Decimal(denominator)).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP
    )


def matches_filters(
    record: PerformanceRecord,
    filters: DashboardFilters,
) -> bool:
    month = record.period.strftime("%Y-%m")

    if filters.from_month and month < filters.from_month:
        return False
    if filters.to_month and month > filters.to_month:
        return False
    if filters.business_unit and record.business_unit != filters.business_unit:
        return False
    if filters.region and record.region != filters.region:
        return False

    return True


def aggregate(records: list[PerformanceRecord]) -> dict[str, Any]:
    """Aggregate additive values first, then calculate weighted KPIs."""
    revenue = sum((r.revenue for r in records), ZERO)
    revenue_target = sum((r.revenue_target for r in records), ZERO)
    cogs = sum((r.cogs for r in records), ZERO)
    operating_expense = sum((r.operating_expense for r in records), ZERO)

    orders = sum(r.orders for r in records)
    delivered_orders = sum(r.delivered_orders for r in records)
    on_time_orders = sum(r.on_time_orders for r in records)

    csat_score_sum = sum((r.csat_score_sum for r in records), ZERO)
    csat_responses = sum(r.csat_responses for r in records)

    gross_profit = revenue - cogs
    operating_profit = gross_profit - operating_expense

    return {
        "record_count": len(records),
        "revenue": revenue,
        "revenue_target": revenue_target,
        "revenue_attainment_pct": ratio_pct(revenue, revenue_target),
        "cogs": cogs,
        "gross_profit": gross_profit,
        "gross_margin_pct": ratio_pct(gross_profit, revenue),
        "operating_expense": operating_expense,
        "operating_profit": operating_profit,
        "operating_margin_pct": ratio_pct(operating_profit, revenue),
        "orders": orders,
        "delivered_orders": delivered_orders,
        "fulfillment_pct": ratio_pct(Decimal(delivered_orders), Decimal(orders)),
        "on_time_orders": on_time_orders,
        "on_time_delivery_pct": ratio_pct(
            Decimal(on_time_orders), Decimal(delivered_orders)
        ),
        "csat_score_sum": csat_score_sum,
        "csat_responses": csat_responses,
        "average_csat": average(csat_score_sum, csat_responses),
    }


def evaluate_alerts(metrics: dict[str, Any]) -> list[dict[str, str]]:
    """Evaluate management thresholds against the aggregated result."""
    alerts: list[dict[str, str]] = []

    if metrics["record_count"] == 0:
        return [{
            "code": "NO_DATA",
            "severity": "WARNING",
            "message": "No records match the selected dashboard filters.",
        }]

    attainment = metrics["revenue_attainment_pct"]
    if attainment is not None and attainment < Decimal("95"):
        alerts.append({
            "code": "REVENUE_BELOW_PLAN",
            "severity": "CRITICAL",
            "message": f"Revenue attainment is {attainment}% of target.",
        })
    elif attainment is not None and attainment < ONE_HUNDRED:
        alerts.append({
            "code": "REVENUE_NEAR_PLAN",
            "severity": "WARNING",
            "message": f"Revenue is below target at {attainment}% attainment.",
        })

    margin = metrics["gross_margin_pct"]
    if margin is not None and margin < Decimal("35"):
        alerts.append({
            "code": "LOW_GROSS_MARGIN",
            "severity": "CRITICAL",
            "message": f"Gross margin is {margin}%, below the 35% threshold.",
        })

    delivery = metrics["on_time_delivery_pct"]
    if delivery is not None and delivery < Decimal("90"):
        alerts.append({
            "code": "DELIVERY_PERFORMANCE",
            "severity": "CRITICAL",
            "message": f"On-time delivery is {delivery}%, below 90%.",
        })

    csat = metrics["average_csat"]
    if csat is not None and csat < Decimal("4.00"):
        alerts.append({
            "code": "CUSTOMER_SATISFACTION",
            "severity": "WARNING",
            "message": f"Average customer satisfaction is {csat}/5.",
        })

    return alerts


def segment_performance(
    records: list[PerformanceRecord],
) -> list[dict[str, Any]]:
    """Return independently aggregated business-unit and region results."""
    groups: dict[tuple[str, str], list[PerformanceRecord]] = {}

    for record in records:
        key = (record.business_unit, record.region)
        groups.setdefault(key, []).append(record)

    result: list[dict[str, Any]] = []

    for (business_unit, region), group_records in sorted(groups.items()):
        result.append({
            "business_unit": business_unit,
            "region": region,
            "metrics": aggregate(group_records),
        })

    return result


def decimal_json(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f")


def metrics_to_json(metrics: dict[str, Any]) -> dict[str, Any]:
    decimal_fields = {
        "revenue",
        "revenue_target",
        "revenue_attainment_pct",
        "cogs",
        "gross_profit",
        "gross_margin_pct",
        "operating_expense",
        "operating_profit",
        "operating_margin_pct",
        "fulfillment_pct",
        "on_time_delivery_pct",
        "csat_score_sum",
        "average_csat",
    }

    return {
        key: decimal_json(value) if key in decimal_fields else value
        for key, value in metrics.items()
    }


def record_to_json(record: PerformanceRecord) -> dict[str, Any]:
    return {
        "period": record.period.strftime("%Y-%m"),
        "business_unit": record.business_unit,
        "region": record.region,
        "revenue": decimal_json(record.revenue),
        "revenue_target": decimal_json(record.revenue_target),
        "cogs": decimal_json(record.cogs),
        "operating_expense": decimal_json(record.operating_expense),
        "orders": record.orders,
        "delivered_orders": record.delivered_orders,
        "on_time_orders": record.on_time_orders,
        "csat_score_sum": decimal_json(record.csat_score_sum),
        "csat_responses": record.csat_responses,
    }


def build_dashboard(
    records: list[PerformanceRecord],
    filters: DashboardFilters,
) -> dict[str, Any]:
    filtered = [
        record for record in records
        if matches_filters(record, filters)
    ]

    metrics = aggregate(filtered)

    return {
        "filters": {
            "from_month": filters.from_month,
            "to_month": filters.to_month,
            "business_unit": filters.business_unit,
            "region": filters.region,
        },
        "metrics": metrics_to_json(metrics),
        "alerts": evaluate_alerts(metrics),
        "segments": segment_performance(filtered),
        "filtered_record_count": len(filtered),
    }


def run_self_tests(records: list[PerformanceRecord]) -> None:
    """Small executable checks for core aggregation and validation rules."""
    validated = validate_records(records)
    full_metrics = aggregate(validated)

    assert full_metrics["record_count"] == 12
    assert full_metrics["revenue"] > ZERO
    assert full_metrics["revenue_attainment_pct"] is not None
    assert full_metrics["average_csat"] is not None

    try:
        validate_records([validated[0], validated[0]])
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate record validation did not fail")

    invalid = replace(
        validated[0],
        delivered_orders=validated[0].orders + 1,
    )

    try:
        validate_record(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid delivery count validation did not fail")

    empty_metrics = aggregate([])
    assert empty_metrics["revenue_attainment_pct"] is None
    assert evaluate_alerts(empty_metrics)[0]["code"] == "NO_DATA"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an executive performance dashboard snapshot."
    )
    parser.add_argument("--input", type=Path, help="Input CSV file.")
    parser.add_argument("--output", type=Path, help="Optional JSON output file.")
    parser.add_argument("--from-month", help="Inclusive start month, YYYY-MM.")
    parser.add_argument("--to-month", help="Inclusive end month, YYYY-MM.")
    parser.add_argument("--business-unit", help="Exact business-unit name.")
    parser.add_argument("--region", help="Exact region name.")
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip built-in validation assertions.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.from_month:
            parse_month(args.from_month)
        if args.to_month:
            parse_month(args.to_month)
        if args.from_month and args.to_month and args.from_month > args.to_month:
            raise ValueError("from-month cannot be later than to-month")

        records = (
            load_csv(args.input)
            if args.input
            else validate_records(sample_records())
        )

        if not args.skip_tests and args.input is None:
            run_self_tests(records)

        filters = DashboardFilters(
            from_month=args.from_month,
            to_month=args.to_month,
            business_unit=args.business_unit,
            region=args.region,
        )

        dashboard = build_dashboard(records, filters)

        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "currency_note": "Monetary values use the input currency unit.",
            "records": [record_to_json(record) for record in records],
            "dashboard": dashboard,
        }

        output = json.dumps(payload, indent=2, ensure_ascii=False)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = args.output.with_name(args.output.name + ".tmp")
            temporary_path.write_text(output + "\n", encoding="utf-8")
            temporary_path.replace(args.output)
            print(f"Dashboard snapshot written to {args.output}")
            print(json.dumps(dashboard["metrics"], indent=2))
        else:
            print(output)

        return 0

    except (OSError, ValueError, AssertionError) as exc:
        print(f"Dashboard processing failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
