#!/usr/bin/env python3
"""
Campaign Analytics: ROI, ROAS and Campaign Performance

A self-contained campaign analytics engine covering:
- Campaign and channel modeling
- Marketing spend and revenue tracking
- ROI and ROAS calculations
- Conversion funnel analysis
- Attribution and performance evaluation
- Budget utilization and profitability
- Campaign ranking and optimization
- CSV/JSON reporting
- Validation and error handling

Run:
    python campaign_analytics.py

Optional:
    python campaign_analytics.py --output campaign_report.json
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import statistics
from dataclasses import asdict, dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("campaign_analytics")


class Channel(str, Enum):
    SEARCH = "Search"
    SOCIAL = "Social"
    EMAIL = "Email"
    DISPLAY = "Display"
    AFFILIATE = "Affiliate"
    VIDEO = "Video"


class CampaignStatus(str, Enum):
    ACTIVE = "Active"
    PAUSED = "Paused"
    COMPLETED = "Completed"


@dataclass
class Campaign:
    campaign_id: str
    name: str
    channel: Channel
    budget: float
    spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    status: CampaignStatus = CampaignStatus.ACTIVE
    start_date: date = field(default_factory=date.today)

    def __post_init__(self):
        if not self.campaign_id.strip():
            raise ValueError("Campaign ID cannot be empty.")

        if not self.name.strip():
            raise ValueError("Campaign name cannot be empty.")

        if self.budget <= 0:
            raise ValueError("Budget must be greater than zero.")

        if self.spend < 0 or self.revenue < 0:
            raise ValueError("Spend and revenue cannot be negative.")

        if self.spend > 1_000_000_000:
            raise ValueError("Spend exceeds the supported limit.")

        if min(self.impressions, self.clicks, self.conversions) < 0:
            raise ValueError("Marketing metrics cannot be negative.")

        if self.clicks > self.impressions:
            raise ValueError("Clicks cannot exceed impressions.")

        if self.conversions > self.clicks:
            raise ValueError("Conversions cannot exceed clicks.")


@dataclass
class CampaignMetrics:
    campaign_id: str
    name: str
    channel: str
    spend: float
    revenue: float
    profit: float
    roi: float
    roas: float
    ctr: float
    conversion_rate: float
    cpc: float
    cpa: float
    cpm: float
    budget_utilization: float
    status: str

    def to_dict(self):
        return asdict(self)


class CampaignAnalytics:
    """Calculates and evaluates campaign performance."""

    @staticmethod
    def percentage(numerator: float, denominator: float) -> float:
        if denominator == 0:
            return 0.0
        return numerator / denominator * 100

    @staticmethod
    def calculate(campaign: Campaign) -> CampaignMetrics:
        spend = campaign.spend
        revenue = campaign.revenue

        profit = revenue - spend

        # ROI measures net return relative to investment.
        roi = CampaignAnalytics.percentage(profit, spend)

        # ROAS measures gross attributed revenue per advertising unit.
        roas = revenue / spend if spend > 0 else 0.0

        ctr = CampaignAnalytics.percentage(
            campaign.clicks,
            campaign.impressions
        )

        conversion_rate = CampaignAnalytics.percentage(
            campaign.conversions,
            campaign.clicks
        )

        cpc = spend / campaign.clicks if campaign.clicks else 0.0

        cpa = (
            spend / campaign.conversions
            if campaign.conversions
            else 0.0
        )

        cpm = (
            spend / campaign.impressions * 1000
            if campaign.impressions
            else 0.0
        )

        budget_utilization = CampaignAnalytics.percentage(
            spend,
            campaign.budget
        )

        return CampaignMetrics(
            campaign_id=campaign.campaign_id,
            name=campaign.name,
            channel=campaign.channel.value,
            spend=round(spend, 2),
            revenue=round(revenue, 2),
            profit=round(profit, 2),
            roi=round(roi, 2),
            roas=round(roas, 4),
            ctr=round(ctr, 2),
            conversion_rate=round(conversion_rate, 2),
            cpc=round(cpc, 2),
            cpa=round(cpa, 2),
            cpm=round(cpm, 2),
            budget_utilization=round(budget_utilization, 2),
            status=campaign.status.value
        )

    @staticmethod
    def classify(metrics: CampaignMetrics) -> str:
        if metrics.spend == 0:
            return "No Investment"

        if metrics.roi > 100 and metrics.roas >= 3:
            return "Excellent"

        if metrics.roi > 0 and metrics.roas > 1:
            return "Profitable"

        if metrics.roi == 0:
            return "Break Even"

        return "Loss Making"

    @staticmethod
    def calculate_cac(spend: float, new_customers: int) -> float:
        if spend < 0 or new_customers < 0:
            raise ValueError("Invalid CAC inputs.")

        return (
            round(spend / new_customers, 2)
            if new_customers
            else 0.0
        )


class CampaignManager:
    def __init__(self):
        self.campaigns: dict[str, Campaign] = {}

    def add(self, campaign: Campaign):
        if campaign.campaign_id in self.campaigns:
            raise ValueError("Duplicate campaign ID.")

        self.campaigns[campaign.campaign_id] = campaign

    def get(self, campaign_id: str) -> Campaign:
        try:
            return self.campaigns[campaign_id]
        except KeyError:
            raise KeyError(f"Campaign not found: {campaign_id}")

    def update_spend(self, campaign_id: str, amount: float):
        campaign = self.get(campaign_id)

        if amount < 0:
            raise ValueError("Spend increment cannot be negative.")

        campaign.spend += amount

        if campaign.spend > campaign.budget:
            logger.warning(
                "Campaign %s has exceeded its budget.",
                campaign_id
            )

    def update_performance(
        self,
        campaign_id: str,
        impressions: int,
        clicks: int,
        conversions: int,
        revenue: float
    ):
        campaign = self.get(campaign_id)

        updated = Campaign(
            campaign_id=campaign.campaign_id,
            name=campaign.name,
            channel=campaign.channel,
            budget=campaign.budget,
            spend=campaign.spend,
            impressions=campaign.impressions + impressions,
            clicks=campaign.clicks + clicks,
            conversions=campaign.conversions + conversions,
            revenue=campaign.revenue + revenue,
            status=campaign.status,
            start_date=campaign.start_date
        )

        self.campaigns[campaign_id] = updated

    def all_metrics(self) -> list[CampaignMetrics]:
        return [
            CampaignAnalytics.calculate(campaign)
            for campaign in self.campaigns.values()
        ]


class PerformanceAnalyzer:

    @staticmethod
    def portfolio_summary(
        metrics: list[CampaignMetrics]
    ) -> dict:

        total_spend = sum(m.spend for m in metrics)
        total_revenue = sum(m.revenue for m in metrics)
        total_profit = total_revenue - total_spend

        # Portfolio ROAS and ROI must use aggregate totals,
        # not arithmetic averages of campaign-level ratios.
        return {
            "campaign_count": len(metrics),
            "total_spend": round(total_spend, 2),
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "portfolio_roi": round(
                total_profit / total_spend * 100,
                2
            ) if total_spend else 0.0,
            "portfolio_roas": round(
                total_revenue / total_spend,
                4
            ) if total_spend else 0.0
        }

    @staticmethod
    def channel_analysis(
        metrics: list[CampaignMetrics]
    ) -> dict:

        grouped = {}

        for metric in metrics:
            grouped.setdefault(
                metric.channel,
                {"spend": 0.0, "revenue": 0.0, "campaigns": 0}
            )

            grouped[metric.channel]["spend"] += metric.spend
            grouped[metric.channel]["revenue"] += metric.revenue
            grouped[metric.channel]["campaigns"] += 1

        result = {}

        for channel, data in grouped.items():
            spend = data["spend"]
            revenue = data["revenue"]

            result[channel] = {
                **data,
                "profit": round(revenue - spend, 2),
                "roi": round(
                    (revenue - spend) / spend * 100,
                    2
                ) if spend else 0.0,
                "roas": round(revenue / spend, 4) if spend else 0.0
            }

        return result

    @staticmethod
    def rank_campaigns(
        metrics: list[CampaignMetrics]
    ) -> list[CampaignMetrics]:

        return sorted(
            metrics,
            key=lambda m: (
                m.profit,
                m.roi,
                m.roas
            ),
            reverse=True
        )

    @staticmethod
    def detect_outliers(
        metrics: list[CampaignMetrics]
    ) -> list[str]:

        rois = [m.roi for m in metrics]

        if len(rois) < 3:
            return []

        median = statistics.median(rois)
        deviations = [
            abs(value - median)
            for value in rois
        ]
        mad = statistics.median(deviations)

        if mad == 0:
            return []

        threshold = 3.5 * 1.4826 * mad

        return [
            m.campaign_id
            for m in metrics
            if abs(m.roi - median) > threshold
        ]


class BudgetOptimizer:

    @staticmethod
    def recommend(
        metrics: list[CampaignMetrics],
        maximum_budget: float
    ) -> dict:

        if maximum_budget < 0:
            raise ValueError("Budget cannot be negative.")

        recommendations = {}

        eligible = [
            m for m in metrics
            if m.roas > 1 and m.status == CampaignStatus.ACTIVE.value
        ]

        total_spend = sum(m.spend for m in eligible)

        if not eligible or total_spend == 0:
            return {
                "available_budget": maximum_budget,
                "allocations": recommendations
            }

        # Allocation is proportional to existing spend among
        # profitable active campaigns, subject to available budget.
        for metric in eligible:
            allocation = (
                maximum_budget * metric.spend / total_spend
            )
            recommendations[metric.campaign_id] = round(
                allocation,
                2
            )

        return {
            "available_budget": maximum_budget,
            "allocations": recommendations
        }


def export_json(data: dict, output: Path):
    output = output.resolve()

    with output.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    logger.info("JSON report saved to %s", output)


def export_csv(
    metrics: list[CampaignMetrics],
    output: Path
):
    if not metrics:
        logger.warning("No metrics available for CSV export.")
        return

    with output.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(metrics[0].to_dict().keys())
        )
        writer.writeheader()

        for metric in metrics:
            writer.writerow(metric.to_dict())

    logger.info("CSV report saved to %s", output.resolve())


def build_demo() -> CampaignManager:
    manager = CampaignManager()

    samples = [
        Campaign(
            "C001", "Search Conversion Campaign",
            Channel.SEARCH, 50000, 35000,
            500000, 25000, 1500, 140000
        ),
        Campaign(
            "C002", "Social Awareness Campaign",
            Channel.SOCIAL, 40000, 30000,
            800000, 16000, 400, 45000
        ),
        Campaign(
            "C003", "Email Retention Campaign",
            Channel.EMAIL, 20000, 12000,
            200000, 30000, 2400, 96000
        ),
        Campaign(
            "C004", "Display Remarketing Campaign",
            Channel.DISPLAY, 30000, 25000,
            1000000, 10000, 250, 18000
        ),
        Campaign(
            "C005", "Affiliate Acquisition Campaign",
            Channel.AFFILIATE, 25000, 15000,
            300000, 12000, 900, 75000
        ),
        Campaign(
            "C006", "Video Awareness Campaign",
            Channel.VIDEO, 35000, 0,
            0, 0, 0, 0,
            CampaignStatus.PAUSED
        )
    ]

    for campaign in samples:
        manager.add(campaign)

    return manager


def run_tests():
    assert CampaignAnalytics.percentage(50, 100) == 50
    assert CampaignAnalytics.percentage(50, 0) == 0
    assert CampaignAnalytics.calculate_cac(1000, 10) == 100

    campaign = Campaign(
        "TEST", "Validation Test",
        Channel.SEARCH, 1000, 500,
        10000, 1000, 100, 1500
    )

    metrics = CampaignAnalytics.calculate(campaign)

    assert metrics.profit == 1000
    assert metrics.roas == 3.0
    assert metrics.roi == 200.0

    try:
        Campaign(
            "INVALID", "Invalid Campaign",
            Channel.SEARCH, 100, 200,
            100, 200, 10, 100
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid campaign was accepted.")

    logger.info("All validation tests passed.")


def main():
    parser = argparse.ArgumentParser(
        description="Campaign performance analytics"
    )

    parser.add_argument(
        "--output",
        default="campaign_report.json"
    )

    parser.add_argument(
        "--csv",
        default="campaign_metrics.csv"
    )

    args = parser.parse_args()

    run_tests()

    manager = build_demo()
    metrics = manager.all_metrics()

    summary = PerformanceAnalyzer.portfolio_summary(metrics)
    channels = PerformanceAnalyzer.channel_analysis(metrics)
    ranking = PerformanceAnalyzer.rank_campaigns(metrics)

    budget = BudgetOptimizer.recommend(
        metrics,
        maximum_budget=100000
    )

    report = {
        "report_date": date.today().isoformat(),
        "portfolio": summary,
        "channels": channels,
        "ranking": [
            {
                **m.to_dict(),
                "classification": CampaignAnalytics.classify(m)
            }
            for m in ranking
        ],
        "outlier_campaigns": (
            PerformanceAnalyzer.detect_outliers(metrics)
        ),
        "budget_recommendations": budget
    }

    print("\nCAMPAIGN PORTFOLIO PERFORMANCE")
    print("=" * 65)

    for key, value in summary.items():
        print(f"{key:25}: {value}")

    print("\nCAMPAIGN RANKING")
    print("-" * 65)

    for position, metric in enumerate(ranking, start=1):
        print(
            f"{position}. {metric.name:35} "
            f"ROI={metric.roi:8.2f}% "
            f"ROAS={metric.roas:7.2f}"
        )

    print("\nCHANNEL PERFORMANCE")

    for channel, data in channels.items():
        print(
            f"{channel:12} "
            f"Spend={data['spend']:10.2f} "
            f"Revenue={data['revenue']:10.2f} "
            f"ROAS={data['roas']:7.2f}"
        )

    export_json(report, Path(args.output))
    export_csv(metrics, Path(args.csv))


if __name__ == "__main__":
    main()
