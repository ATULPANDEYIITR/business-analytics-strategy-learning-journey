"""
MARKETING ANALYTICS
Marketing data collection, campaign performance measurement,
customer acquisition, conversion funnels, attribution, and ROI analysis.

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import csv
import json
import logging
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("marketing_analytics")


class MarketingError(Exception):
    """Base exception for marketing analytics."""


class ValidationError(MarketingError):
    """Invalid marketing data."""


class AttributionModel(Enum):
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"


@dataclass
class Campaign:
    campaign_id: str
    name: str
    channel: str
    budget: float
    start_date: date
    end_date: date
    objective: str

    def __post_init__(self):
        if not self.campaign_id.strip():
            raise ValidationError("Campaign ID cannot be empty.")
        if self.budget < 0:
            raise ValidationError("Budget cannot be negative.")
        if self.end_date < self.start_date:
            raise ValidationError("Invalid campaign date range.")


@dataclass
class CampaignMetrics:
    campaign_id: str
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    spend: float

    def validate(self):
        values = (
            self.impressions,
            self.clicks,
            self.conversions,
            self.revenue,
            self.spend
        )

        if any(value < 0 for value in values):
            raise ValidationError("Metrics cannot be negative.")

        if self.clicks > self.impressions:
            raise ValidationError("Clicks cannot exceed impressions.")

        if self.conversions > self.clicks:
            raise ValidationError("Conversions cannot exceed clicks.")


@dataclass
class Customer:
    customer_id: str
    acquisition_date: date
    acquisition_cost: float
    lifetime_revenue: float

    def validate(self):
        if self.acquisition_cost < 0 or self.lifetime_revenue < 0:
            raise ValidationError("Customer financial values cannot be negative.")


@dataclass
class Touchpoint:
    customer_id: str
    campaign_id: str
    channel: str
    timestamp: datetime


@dataclass
class CampaignReport:
    campaign_id: str
    ctr: float
    conversion_rate: float
    cpc: float
    cpa: float
    roas: float
    roi: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    spend: float


class MarketingAnalytics:

    def __init__(self):
        self.campaigns: dict[str, Campaign] = {}
        self.metrics: dict[str, CampaignMetrics] = {}
        self.customers: dict[str, Customer] = {}
        self.touchpoints: list[Touchpoint] = []

    def add_campaign(self, campaign: Campaign):
        if campaign.campaign_id in self.campaigns:
            raise ValidationError("Duplicate campaign ID.")

        self.campaigns[campaign.campaign_id] = campaign

    def add_metrics(self, metrics: CampaignMetrics):
        metrics.validate()

        if metrics.campaign_id not in self.campaigns:
            raise ValidationError("Campaign does not exist.")

        campaign = self.campaigns[metrics.campaign_id]

        if metrics.spend > campaign.budget:
            raise ValidationError("Campaign spend exceeds approved budget.")

        self.metrics[metrics.campaign_id] = metrics

    def add_customer(self, customer: Customer):
        customer.validate()

        if customer.customer_id in self.customers:
            raise ValidationError("Duplicate customer ID.")

        self.customers[customer.customer_id] = customer

    def add_touchpoint(self, touchpoint: Touchpoint):
        if touchpoint.customer_id not in self.customers:
            raise ValidationError("Unknown customer.")

        if touchpoint.campaign_id not in self.campaigns:
            raise ValidationError("Unknown campaign.")

        self.touchpoints.append(touchpoint)

    @staticmethod
    def safe_divide(numerator: float, denominator: float) -> float:
        return numerator / denominator if denominator else 0.0

    def calculate_campaign_report(
        self,
        campaign_id: str
    ) -> CampaignReport:

        if campaign_id not in self.metrics:
            raise ValidationError("Campaign metrics are unavailable.")

        m = self.metrics[campaign_id]

        ctr = self.safe_divide(m.clicks, m.impressions) * 100
        conversion_rate = self.safe_divide(
            m.conversions, m.clicks
        ) * 100

        cpc = self.safe_divide(m.spend, m.clicks)
        cpa = self.safe_divide(m.spend, m.conversions)
        roas = self.safe_divide(m.revenue, m.spend)
        roi = self.safe_divide(
            m.revenue - m.spend, m.spend
        ) * 100

        return CampaignReport(
            campaign_id=campaign_id,
            ctr=round(ctr, 2),
            conversion_rate=round(conversion_rate, 2),
            cpc=round(cpc, 2),
            cpa=round(cpa, 2),
            roas=round(roas, 2),
            roi=round(roi, 2),
            impressions=m.impressions,
            clicks=m.clicks,
            conversions=m.conversions,
            revenue=m.revenue,
            spend=m.spend
        )

    def calculate_funnel(self):
        impressions = sum(m.impressions for m in self.metrics.values())
        clicks = sum(m.clicks for m in self.metrics.values())
        conversions = sum(m.conversions for m in self.metrics.values())

        return {
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "impression_to_click_rate": round(
                self.safe_divide(clicks, impressions) * 100, 2
            ),
            "click_to_conversion_rate": round(
                self.safe_divide(conversions, clicks) * 100, 2
            ),
            "impression_to_conversion_rate": round(
                self.safe_divide(conversions, impressions) * 100, 2
            )
        }

    def attribute_revenue(
        self,
        customer_id: str,
        model: AttributionModel
    ) -> dict[str, float]:

        if customer_id not in self.customers:
            raise ValidationError("Unknown customer.")

        customer = self.customers[customer_id]

        events = sorted(
            [
                event for event in self.touchpoints
                if event.customer_id == customer_id
            ],
            key=lambda event: event.timestamp
        )

        if not events:
            return {}

        allocations = defaultdict(float)

        if model == AttributionModel.FIRST_TOUCH:
            allocations[events[0].campaign_id] = customer.lifetime_revenue

        elif model == AttributionModel.LAST_TOUCH:
            allocations[events[-1].campaign_id] = customer.lifetime_revenue

        elif model == AttributionModel.LINEAR:
            share = customer.lifetime_revenue / len(events)

            for event in events:
                allocations[event.campaign_id] += share

        return dict(allocations)

    def campaign_ranking(self):
        reports = [
            self.calculate_campaign_report(campaign_id)
            for campaign_id in self.metrics
        ]

        return sorted(
            reports,
            key=lambda report: (
                report.roas,
                report.conversions
            ),
            reverse=True
        )

    def channel_performance(self):
        channels = defaultdict(
            lambda: {
                "spend": 0.0,
                "revenue": 0.0,
                "clicks": 0,
                "conversions": 0
            }
        )

        for campaign_id, metrics in self.metrics.items():
            channel = self.campaigns[campaign_id].channel

            channels[channel]["spend"] += metrics.spend
            channels[channel]["revenue"] += metrics.revenue
            channels[channel]["clicks"] += metrics.clicks
            channels[channel]["conversions"] += metrics.conversions

        results = {}

        for channel, values in channels.items():
            results[channel] = {
                **values,
                "roas": round(
                    self.safe_divide(
                        values["revenue"], values["spend"]
                    ), 2
                ),
                "cpa": round(
                    self.safe_divide(
                        values["spend"], values["conversions"]
                    ), 2
                )
            }

        return results

    def detect_underperforming_campaigns(
        self,
        minimum_roas: float = 2.0,
        minimum_conversions: int = 1
    ):
        if minimum_roas < 0 or minimum_conversions < 0:
            raise ValidationError("Thresholds cannot be negative.")

        return [
            report
            for report in self.campaign_ranking()
            if report.roas < minimum_roas
            or report.conversions < minimum_conversions
        ]

    def customer_acquisition_metrics(self):
        if not self.customers:
            return {
                "customers": 0,
                "cac": 0.0,
                "average_lifetime_revenue": 0.0,
                "average_ltv_to_cac": 0.0
            }

        acquisition_cost = sum(
            customer.acquisition_cost
            for customer in self.customers.values()
        )

        lifetime_revenue = sum(
            customer.lifetime_revenue
            for customer in self.customers.values()
        )

        cac = self.safe_divide(
            acquisition_cost, len(self.customers)
        )

        average_ltv = self.safe_divide(
            lifetime_revenue, len(self.customers)
        )

        return {
            "customers": len(self.customers),
            "cac": round(cac, 2),
            "average_lifetime_revenue": round(average_ltv, 2),
            "average_ltv_to_cac": round(
                self.safe_divide(average_ltv, cac), 2
            )
        }

    def export_reports(self, output_file: str):
        reports = [
            asdict(self.calculate_campaign_report(campaign_id))
            for campaign_id in self.metrics
        ]

        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as file:
            if not reports:
                return

            writer = csv.DictWriter(
                file,
                fieldnames=reports[0].keys()
            )
            writer.writeheader()
            writer.writerows(reports)

    def export_json(self, output_file: str):
        data = {
            "funnel": self.calculate_funnel(),
            "channels": self.channel_performance(),
            "customers": self.customer_acquisition_metrics(),
            "campaigns": [
                asdict(self.calculate_campaign_report(campaign_id))
                for campaign_id in self.metrics
            ]
        }

        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=4),
            encoding="utf-8"
        )


def build_demo():
    analytics = MarketingAnalytics()

    campaigns = [
        Campaign(
            "C001", "Search Acquisition", "Search",
            50000, date(2026, 1, 1), date(2026, 12, 31),
            "Customer Acquisition"
        ),
        Campaign(
            "C002", "Social Awareness", "Social",
            40000, date(2026, 1, 1), date(2026, 12, 31),
            "Brand Awareness"
        ),
        Campaign(
            "C003", "Email Retention", "Email",
            20000, date(2026, 1, 1), date(2026, 12, 31),
            "Customer Retention"
        )
    ]

    for campaign in campaigns:
        analytics.add_campaign(campaign)

    sample_metrics = [
        CampaignMetrics("C001", 100000, 8000, 640, 240000, 40000),
        CampaignMetrics("C002", 150000, 6000, 240, 90000, 30000),
        CampaignMetrics("C003", 50000, 10000, 1200, 180000, 15000)
    ]

    for metrics in sample_metrics:
        analytics.add_metrics(metrics)

    customers = [
        Customer("U001", date(2026, 2, 10), 500, 3000),
        Customer("U002", date(2026, 3, 15), 400, 2500),
        Customer("U003", date(2026, 4, 20), 600, 4200)
    ]

    for customer in customers:
        analytics.add_customer(customer)

    analytics.add_touchpoint(
        Touchpoint(
            "U001", "C002", "Social",
            datetime(2026, 2, 1, 10, 0)
        )
    )

    analytics.add_touchpoint(
        Touchpoint(
            "U001", "C001", "Search",
            datetime(2026, 2, 5, 12, 0)
        )
    )

    analytics.add_touchpoint(
        Touchpoint(
            "U002", "C001", "Search",
            datetime(2026, 3, 10, 9, 0)
        )
    )

    analytics.add_touchpoint(
        Touchpoint(
            "U002", "C003", "Email",
            datetime(2026, 3, 14, 15, 0)
        )
    )

    return analytics


def run_tests(analytics: MarketingAnalytics):
    report = analytics.calculate_campaign_report("C001")

    assert report.ctr == 8.0
    assert report.conversion_rate == 8.0
    assert report.cpc == 5.0
    assert report.cpa == 62.5
    assert report.roas == 6.0

    funnel = analytics.calculate_funnel()
    assert funnel["impressions"] == 300000
    assert funnel["clicks"] == 24000

    first_touch = analytics.attribute_revenue(
        "U001", AttributionModel.FIRST_TOUCH
    )

    last_touch = analytics.attribute_revenue(
        "U001", AttributionModel.LAST_TOUCH
    )

    assert first_touch == {"C002": 3000}
    assert last_touch == {"C001": 3000}

    try:
        CampaignMetrics("INVALID", 10, 20, 1, 100, 50).validate()
        raise AssertionError("Invalid click count was accepted.")
    except ValidationError:
        pass

    logger.info("All validation tests passed.")


def main():
    analytics = build_demo()

    run_tests(analytics)

    print("\nMARKETING ANALYTICS REPORT")
    print("=" * 65)

    for report in analytics.campaign_ranking():
        print(
            f"{report.campaign_id}: "
            f"CTR={report.ctr}% | "
            f"Conversion={report.conversion_rate}% | "
            f"CPC={report.cpc} | "
            f"CPA={report.cpa} | "
            f"ROAS={report.roas} | "
            f"ROI={report.roi}%"
        )

    print("\nCONVERSION FUNNEL")
    print(json.dumps(analytics.calculate_funnel(), indent=4))

    print("\nCHANNEL PERFORMANCE")
    print(json.dumps(analytics.channel_performance(), indent=4))

    print("\nCUSTOMER ACQUISITION")
    print(json.dumps(
        analytics.customer_acquisition_metrics(),
        indent=4
    ))

    print("\nLINEAR ATTRIBUTION FOR U001")
    print(analytics.attribute_revenue(
        "U001", AttributionModel.LINEAR
    ))

    analytics.export_reports("output/campaign_reports.csv")
    analytics.export_json("output/marketing_dashboard.json")

    print("\nReports exported successfully.")


if __name__ == "__main__":
    main()
