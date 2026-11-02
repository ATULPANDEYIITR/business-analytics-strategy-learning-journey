from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable
import json
import tempfile

import pandas as pd


class DataQuality(Enum):
    VALID = "valid"
    INVALID = "invalid"


@dataclass(frozen=True)
class SalesRecord:
    order_id: int
    order_date: str
    region: str
    product: str
    category: str
    units: int
    unit_price: float
    discount: float
    customer: str


RECORDS = [
    SalesRecord(1001, "2026-01-03", "North", "Laptop", "Electronics", 2, 75000, 0.05, "Apex Ltd"),
    SalesRecord(1002, "2026-01-05", "South", "Monitor", "Electronics", 4, 18000, 0.10, "Beta Corp"),
    SalesRecord(1003, "2026-01-08", "West", "Desk", "Furniture", 3, 12000, 0.00, "Gamma Pvt"),
    SalesRecord(1004, "2026-01-11", "North", "Chair", "Furniture", 10, 6500, 0.08, "Apex Ltd"),
    SalesRecord(1005, "2026-01-13", "East", "Laptop", "Electronics", 1, 82000, 0.05, "Delta Inc"),
    SalesRecord(1006, "2026-01-18", "South", "Desk", "Furniture", 2, 13500, 0.03, "Beta Corp"),
    SalesRecord(1007, "2026-01-20", "West", "Keyboard", "Accessories", 15, 2200, 0.00, "Gamma Pvt"),
    SalesRecord(1008, "2026-01-23", "East", "Monitor", "Electronics", 5, 19500, 0.12, "Delta Inc"),
    SalesRecord(1009, "2026-02-02", "North", "Laptop", "Electronics", 3, 76000, 0.04, "Apex Ltd"),
    SalesRecord(1010, "2026-02-04", "South", "Chair", "Furniture", 8, 6200, 0.06, "Beta Corp"),
    SalesRecord(1011, "2026-02-09", "West", "Monitor", "Electronics", 2, 18500, 0.02, "Gamma Pvt"),
    SalesRecord(1012, "2026-02-15", "East", "Keyboard", "Accessories", 20, 2100, 0.05, "Delta Inc"),
]


def records_to_dataframe(records: Iterable[SalesRecord]) -> pd.DataFrame:
    """Build a typed DataFrame from domain records."""
    frame = pd.DataFrame([record.__dict__ for record in records])

    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="raise")
    frame["units"] = pd.to_numeric(frame["units"], errors="raise").astype("int64")
    frame["unit_price"] = pd.to_numeric(frame["unit_price"], errors="raise")
    frame["discount"] = pd.to_numeric(frame["discount"], errors="raise")

    if frame["order_id"].duplicated().any():
        raise ValueError("order_id must be unique")

    if (frame["units"] <= 0).any():
        raise ValueError("units must be positive")

    if ((frame["discount"] < 0) | (frame["discount"] >= 1)).any():
        raise ValueError("discount must be in [0, 1)")

    return frame


def enrich_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Create derived columns without mutating the input."""
    result = frame.copy()

    result["gross_sales"] = result["units"] * result["unit_price"]
    result["discount_amount"] = result["gross_sales"] * result["discount"]
    result["net_sales"] = result["gross_sales"] - result["discount_amount"]
    result["month"] = result["order_date"].dt.to_period("M").astype(str)
    result["quarter"] = result["order_date"].dt.quarter
    result["high_value"] = result["net_sales"] >= 100000

    return result


def inspect_series_and_dataframe(frame: pd.DataFrame) -> dict:
    """Exercise Series operations and structural inspection."""
    return {
        "shape": frame.shape,
        "columns": frame.columns.tolist(),
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "regions": sorted(frame["region"].unique().tolist()),
        "region_counts": frame["region"].value_counts().to_dict(),
        "net_sales_mean": round(float(frame["net_sales"].mean()), 2),
        "net_sales_median": round(float(frame["net_sales"].median()), 2),
    }


def filter_and_transform(frame: pd.DataFrame) -> pd.DataFrame:
    """Demonstrate boolean filtering, loc, assign, sorting and ranking."""
    selected = frame.loc[
        (frame["category"] == "Electronics")
        & (frame["net_sales"] >= 50000)
    ].copy()

    selected["sales_rank"] = selected["net_sales"].rank(
        ascending=False,
        method="dense"
    ).astype(int)

    return selected.sort_values(
        ["net_sales", "order_id"],
        ascending=[False, True]
    )


def aggregate_sales(frame: pd.DataFrame) -> pd.DataFrame:
    """Produce multi-dimensional business aggregates."""
    summary = (
        frame.groupby(["region", "category"], as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            units=("units", "sum"),
            gross_sales=("gross_sales", "sum"),
            net_sales=("net_sales", "sum"),
            average_order_value=("net_sales", "mean"),
        )
        .sort_values(["region", "net_sales"], ascending=[True, False])
    )

    summary["net_sales"] = summary["net_sales"].round(2)
    summary["average_order_value"] = summary["average_order_value"].round(2)
    return summary


def monthly_pivot(frame: pd.DataFrame) -> pd.DataFrame:
    """Create a pivot table with region as rows and months as columns."""
    return pd.pivot_table(
        frame,
        index="region",
        columns="month",
        values="net_sales",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="Total",
    ).round(2)


def demonstrate_merge(frame: pd.DataFrame) -> pd.DataFrame:
    """Join order data to a customer dimension."""
    customer_dimension = pd.DataFrame(
        {
            "customer": ["Apex Ltd", "Beta Corp", "Gamma Pvt", "Delta Inc"],
            "segment": ["Enterprise", "Enterprise", "Mid-Market", "Enterprise"],
            "account_manager": ["Neha", "Ravi", "Meera", "Arjun"],
        }
    )

    return frame.merge(
        customer_dimension,
        on="customer",
        how="left",
        validate="many_to_one",
    )


def demonstrate_missing_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Show detection and controlled filling of missing values."""
    frame = pd.DataFrame(
        {
            "region": ["North", "South", "East", None],
            "sales": [100000.0, None, 85000.0, 70000.0],
        }
    )

    missing_report = frame.isna().sum().rename("missing").to_frame()
    cleaned = frame.copy()
    cleaned["region"] = cleaned["region"].fillna("Unknown")
    cleaned["sales"] = cleaned["sales"].fillna(cleaned["sales"].median())

    return missing_report, cleaned


def demonstrate_concat_and_duplicates(frame: pd.DataFrame) -> pd.DataFrame:
    """Concatenate a new batch and remove duplicate order identifiers."""
    first_batch = frame.iloc[:6]
    second_batch = frame.iloc[6:]
    duplicate = frame.iloc[[0]].copy()

    combined = pd.concat(
        [first_batch, second_batch, duplicate],
        ignore_index=True
    )

    return combined.drop_duplicates(
        subset=["order_id"],
        keep="last"
    ).sort_values("order_id").reset_index(drop=True)


def rolling_sales(frame: pd.DataFrame) -> pd.DataFrame:
    """Calculate a time-indexed rolling three-order sales average."""
    ordered = frame.sort_values("order_date").copy()
    ordered["rolling_3_order_average"] = (
        ordered["net_sales"].rolling(window=3, min_periods=1).mean().round(2)
    )
    return ordered[["order_date", "order_id", "net_sales", "rolling_3_order_average"]]


def validate_quality(frame: pd.DataFrame) -> DataQuality:
    """Apply explicit data-quality assertions before analytical use."""
    required = {
        "order_id",
        "order_date",
        "region",
        "product",
        "category",
        "units",
        "unit_price",
        "discount",
        "customer",
        "gross_sales",
        "discount_amount",
        "net_sales",
        "month",
        "quarter",
        "high_value",
    }

    if not required.issubset(frame.columns):
        raise ValueError("Required columns are missing")

    if frame.empty:
        raise ValueError("DataFrame must not be empty")

    if frame[["order_id", "units", "unit_price", "discount"]].isna().any().any():
        raise ValueError("Critical numeric fields contain missing values")

    if frame["order_id"].duplicated().any():
        raise ValueError("Duplicate order IDs detected")

    if (frame["net_sales"] < 0).any():
        raise ValueError("Negative net sales detected")

    return DataQuality.VALID


def export_and_reload(frame: pd.DataFrame) -> pd.DataFrame:
    """Use a temporary CSV to exercise serialization and type restoration."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sales.csv"
        frame.to_csv(path, index=False)

        reloaded = pd.read_csv(
            path,
            parse_dates=["order_date"],
        )

        if len(reloaded) != len(frame):
            raise IOError("Round-trip row count changed")

        return reloaded


def demonstrate_json(frame: pd.DataFrame) -> list[dict]:
    """Serialize selected records into JSON-compatible Python structures."""
    selected = frame[
        ["order_id", "region", "category", "net_sales"]
    ].head(3)

    payload = selected.to_json(orient="records", date_format="iso")
    return json.loads(payload)


def run_edge_case_checks() -> None:
    """Exercise failure paths rather than silently accepting invalid data."""
    invalid = pd.DataFrame(
        {
            "order_id": [1, 1],
            "units": [1, 0],
            "unit_price": [100.0, 100.0],
            "discount": [0.0, 1.0],
        }
    )

    assert invalid["order_id"].duplicated().any()
    assert (invalid["units"] <= 0).any()
    assert (invalid["discount"] >= 1).any()

    empty = pd.DataFrame(columns=["order_id"])
    try:
        validate_quality(empty)
    except ValueError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("Empty DataFrame should fail validation")


def main() -> None:
    pd.set_option("display.width", 140)
    pd.set_option("display.max_columns", 20)

    sales = records_to_dataframe(RECORDS)
    sales = enrich_dataframe(sales)

    quality = validate_quality(sales)
    assert quality is DataQuality.VALID
    assert round(float(sales["net_sales"].sum()), 2) > 0

    inspection = inspect_series_and_dataframe(sales)
    print("\nDATAFRAME INSPECTION")
    print(inspection)

    print("\nFILTERED ELECTRONICS ORDERS")
    print(filter_and_transform(sales).to_string(index=False))

    print("\nREGION/CATEGORY AGGREGATION")
    print(aggregate_sales(sales).to_string(index=False))

    print("\nMONTHLY PIVOT")
    print(monthly_pivot(sales))

    print("\nMERGED CUSTOMER DIMENSION")
    merged = demonstrate_merge(sales)
    print(
        merged[
            ["order_id", "customer", "segment", "account_manager", "net_sales"]
        ].head(8).to_string(index=False)
    )

    print("\nMISSING-DATA REPORT")
    missing_report, cleaned = demonstrate_missing_data()
    print(missing_report.to_string())
    print("\nCLEANED DATA")
    print(cleaned.to_string(index=False))

    print("\nCONCATENATION AND DUPLICATE CONTROL")
    combined = demonstrate_concat_and_duplicates(sales)
    print(f"rows after duplicate control: {len(combined)}")

    print("\nROLLING SALES")
    print(rolling_sales(sales).to_string(index=False))

    print("\nCSV ROUND TRIP")
    reloaded = export_and_reload(sales)
    print(f"rows written and reloaded: {len(reloaded)}")

    print("\nJSON SAMPLE")
    print(json.dumps(demonstrate_json(sales), indent=2))

    run_edge_case_checks()

    assert sales["net_sales"].ge(0).all()
    assert sales["order_id"].is_unique
    print("\nDATA QUALITY: VALID")
    print("All assertions passed.")


if __name__ == "__main__":
    main()
