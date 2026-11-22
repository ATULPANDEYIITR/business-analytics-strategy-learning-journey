from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from collections import defaultdict
from typing import Optional
import json
import logging
import statistics
import unittest


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("customer_acquisition")


class AcquisitionError(Exception):
    """Base exception for acquisition analysis errors."""


class ValidationError(AcquisitionError):
    """Raised when acquisition data violates business rules."""


class ChannelType(Enum):
    PAID_SEARCH = "Paid Search"
    PAID_SOCIAL = "Paid Social"
    ORGANIC_SEARCH = "Organic Search"
    EMAIL = "Email Marketing"
    REFERRAL = "Referral"
    AFFILIATE = "Affiliate"
    CONTENT = "Content Marketing"
    EVENTS = "Events"
    DIRECT = "Direct"


class CampaignStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class Campaign:
    campaign_id: str
    name: str
    channel: ChannelType
    start_date: date
    end_date: date
    budget: Decimal
    spend: Decimal = Decimal("0")
    impressions: int = 0
    clicks: int = 0
    leads: int = 0
    conversions: int = 0
    revenue: Decimal = Decimal("0")
    status: CampaignStatus = CampaignStatus.ACTIVE

    def __post_init__(self):
        if not self.campaign_id.strip():
            raise ValidationError("Campaign ID cannot be empty.")

        if self.end_date < self.start_date:
            raise ValidationError("Campaign end date precedes start date.")

        if self.budget < 0 or self.spend < 0 or self.revenue < 0:
            raise ValidationError("Financial values cannot be negative.")

        if self.spend > self.budget:
            raise ValidationError("Campaign spend exceeds its budget.")

        if min(self.impressions, self.clicks, self.leads, self.conversions) < 0:
            raise ValidationError("Marketing metrics cannot be negative.")

        if self.clicks > self.impressions:
            raise ValidationError("Clicks cannot exceed impressions.")

        if self.leads > self.clicks:
            raise ValidationError("Leads cannot exceed clicks.")

        if self.conversions > self.leads:
            raise ValidationError("Conversions cannot exceed leads.")

    @property
    def ctr(self) -> Decimal:
        return self._rate(self.clicks, self.impressions)

    @property
    def lead_conversion_rate(self) -> Decimal:
        return self._rate(self.leads, self.clicks)

    @property
    def customer_conversion_rate(self) -> Decimal:
        return self._rate(self.conversions, self.leads)

    @property
    def cac(self) -> Optional[Decimal]:
        if self.conversions == 0:
            return None
        return self.spend / Decimal(self.conversions)

    @property
    def cost_per_click(self) -> Optional[Decimal]:
        if self.clicks == 0:
            return None
        return self.spend / Decimal(self.clicks)

    @property
    def cost_per_lead(self) -> Optional[Decimal]:
        if self.leads == 0:
            return None
        return self.spend / Decimal(self.leads)

    @property
    def roas(self) -> Optional[Decimal]:
        if self.spend == 0:
            return None
        return self.revenue / self.spend

    @staticmethod
    def _rate(numerator: int, denominator: int) -> Decimal:
        if denominator == 0:
            return Decimal("0")
        return Decimal(numerator) / Decimal(denominator) * 100


@dataclass
class Customer:
    customer_id: str
    acquisition_date: date
    campaign_id: str
    acquisition_channel: ChannelType
    first_purchase_revenue: Decimal
    gross_margin_rate: Decimal
    monthly_retention_rate: Decimal = Decimal("0.90")
    monthly_revenue: Decimal = Decimal("100")
    attribution_weight: Decimal = Decimal("1")

    def __post_init__(self):
        if not self.customer_id or not self.campaign_id:
            raise ValidationError("Customer and campaign IDs are required.")

        if self.first_purchase_revenue < 0 or self.monthly_revenue < 0:
            raise ValidationError("Revenue cannot be negative.")

        if not Decimal("0") <= self.gross_margin_rate <= Decimal("1"):
            raise ValidationError("Gross margin must be between 0 and 1.")

        if not Decimal("0") <= self.monthly_retention_rate <= Decimal("1"):
            raise ValidationError("Retention must be between 0 and 1.")

        if not Decimal("0") <= self.attribution_weight <= Decimal("1"):
            raise ValidationError("Attribution weight must be between 0 and 1.")

    def projected_lifetime_value(self, months: int = 24) -> Decimal:
        if months < 1:
            raise ValidationError("Projection period must be positive.")

        # Sum expected monthly gross profit using a retention model.
        monthly_profit = self.monthly_revenue * self.gross_margin_rate
        retention = self.monthly_retention_rate

        if retention == 1:
            recurring_value = monthly_profit * months
        else:
            recurring_value = (
                monthly_profit
                * (1 - retention ** months)
                / (1 - retention)
            )

        initial_profit = self.first_purchase_revenue * self.gross_margin_rate
        return initial_profit + recurring_value


@dataclass
class ChannelMetrics:
    channel: ChannelType
    spend: Decimal = Decimal("0")
    customers: Decimal = Decimal("0")
    revenue: Decimal = Decimal("0")
    gross_profit: Decimal = Decimal("0")

    @property
    def cac(self) -> Optional[Decimal]:
        if self.customers == 0:
            return None
        return self.spend / self.customers

    @property
    def roas(self) -> Optional[Decimal]:
        if self.spend == 0:
            return None
        return self.revenue / self.spend

    @property
    def ltv(self) -> Optional[Decimal]:
        if self.customers == 0:
            return None
        return self.gross_profit / self.customers

    @property
    def ltv_cac_ratio(self) -> Optional[Decimal]:
        if not self.cac or self.cac == 0:
            return None
        return self.ltv / self.cac


class AcquisitionRepository:
    """Maintains validated campaigns and acquired customers."""

    def __init__(self):
        self.campaigns: dict[str, Campaign] = {}
        self.customers: dict[str, Customer] = {}

    def add_campaign(self, campaign: Campaign):
        if campaign.campaign_id in self.campaigns:
            raise ValidationError("Duplicate campaign ID.")

        self.campaigns[campaign.campaign_id] = campaign

    def add_customer(self, customer: Customer):
        if customer.customer_id in self.customers:
            raise ValidationError("Duplicate customer ID.")

        if customer.campaign_id not in self.campaigns:
            raise ValidationError("Customer references an unknown campaign.")

        campaign = self.campaigns[customer.campaign_id]

        if campaign.channel != customer.acquisition_channel:
            raise ValidationError("Customer channel does not match campaign.")

        if not campaign.start_date <= customer.acquisition_date <= campaign.end_date:
            raise ValidationError("Customer acquisition date is outside campaign dates.")

        self.customers[customer.customer_id] = customer


class AcquisitionAnalyzer:
    def __init__(self, repository: AcquisitionRepository):
        self.repository = repository

    def campaign_report(self) -> list[dict]:
        reports = []

        for campaign in self.repository.campaigns.values():
            reports.append({
                "campaign_id": campaign.campaign_id,
                "campaign": campaign.name,
                "channel": campaign.channel.value,
                "spend": float(campaign.spend),
                "impressions": campaign.impressions,
                "clicks": campaign.clicks,
                "leads": campaign.leads,
                "conversions": campaign.conversions,
                "ctr_percent": float(campaign.ctr),
                "lead_conversion_percent": float(campaign.lead_conversion_rate),
                "customer_conversion_percent": float(campaign.customer_conversion_rate),
                "cac": float(campaign.cac) if campaign.cac is not None else None,
                "cost_per_lead": (
                    float(campaign.cost_per_lead)
                    if campaign.cost_per_lead is not None else None
                ),
                "roas": float(campaign.roas) if campaign.roas is not None else None
            })

        return reports

    def channel_report(self, projection_months: int = 24) -> list[ChannelMetrics]:
        metrics = {
            channel: ChannelMetrics(channel)
            for channel in ChannelType
        }

        for campaign in self.repository.campaigns.values():
            item = metrics[campaign.channel]
            item.spend += campaign.spend

        for customer in self.repository.customers.values():
            item = metrics[customer.acquisition_channel]
            weight = customer.attribution_weight

            item.customers += weight
            item.revenue += customer.first_purchase_revenue * weight
            item.gross_profit += (
                customer.projected_lifetime_value(projection_months) * weight
            )

        return sorted(
            metrics.values(),
            key=lambda item: (
                item.cac if item.cac is not None else Decimal("Infinity")
            )
        )

    def calculate_blended_cac(self) -> Optional[Decimal]:
        total_spend = sum(
            (campaign.spend for campaign in self.repository.campaigns.values()),
            Decimal("0")
        )

        total_customers = Decimal(len(self.repository.customers))

        if total_customers == 0:
            return None

        return total_spend / total_customers

    def calculate_ltv_cac(self, months: int = 24) -> Optional[Decimal]:
        cac = self.calculate_blended_cac()

        if cac is None or cac == 0:
            return None

        total_ltv = sum(
            (
                customer.projected_lifetime_value(months)
                for customer in self.repository.customers.values()
            ),
            Decimal("0")
        )

        average_ltv = total_ltv / Decimal(len(self.repository.customers))
        return average_ltv / cac

    def calculate_payback_months(self, monthly_gross_margin: Decimal) -> Optional[Decimal]:
        cac = self.calculate_blended_cac()

        if cac is None or monthly_gross_margin <= 0:
            return None

        return cac / monthly_gross_margin

    def channel_recommendations(self, minimum_ltv_cac: Decimal = Decimal("3")) -> list[dict]:
        results = []

        for item in self.channel_report():
            ratio = item.ltv_cac_ratio

            if item.customers == 0:
                decision = "INSUFFICIENT DATA"
            elif ratio is not None and ratio >= minimum_ltv_cac:
                decision = "CONSIDER SCALING"
            elif ratio is not None and ratio >= Decimal("1"):
                decision = "OPTIMIZE"
            else:
                decision = "REVIEW OR REDUCE"

            results.append({
                "channel": item.channel.value,
                "customers": float(item.customers),
                "cac": float(item.cac) if item.cac is not None else None,
                "ltv": float(item.ltv) if item.ltv is not None else None,
                "ltv_cac_ratio": float(ratio) if ratio is not None else None,
                "decision": decision
            })

        return results

    def export_json(self, filename: str):
        # Do not accept untrusted paths in a network-facing application.
        data = {
            "campaigns": self.campaign_report(),
            "channels": self.channel_recommendations(),
            "blended_cac": (
                float(self.calculate_blended_cac())
                if self.calculate_blended_cac() is not None else None
            )
        }

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)


@dataclass
class BudgetAllocation:
    channel: ChannelType
    current_budget: Decimal
    expected_cac: Decimal
    estimated_customers: int = 0


class BudgetOptimizer:
    """Allocates a fixed budget according to expected marginal CAC."""

    @staticmethod
    def allocate(
        total_budget: Decimal,
        channels: list[BudgetAllocation],
        minimum_budget: Decimal = Decimal("0")
    ) -> dict[ChannelType, Decimal]:

        if total_budget < 0 or minimum_budget < 0:
            raise ValidationError("Budget values cannot be negative.")

        if not channels:
            raise ValidationError("At least one channel is required.")

        if len({item.channel for item in channels}) != len(channels):
            raise ValidationError("Duplicate channels are not allowed.")

        if any(item.expected_cac <= 0 for item in channels):
            raise ValidationError("Expected CAC must be positive.")

        required = minimum_budget * len(channels)

        if required > total_budget:
            raise ValidationError("Minimum allocation exceeds total budget.")

        remaining = total_budget - required

        # Lower expected CAC receives more incremental budget.
        efficiency = {
            item.channel: Decimal("1") / item.expected_cac
            for item in channels
        }

        total_efficiency = sum(efficiency.values(), Decimal("0"))

        allocation = {
            item.channel: minimum_budget
            + remaining * efficiency[item.channel] / total_efficiency
            for item in channels
        }

        # Assign rounding residual to the most efficient channel.
        residual = total_budget - sum(allocation.values(), Decimal("0"))

        best_channel = max(efficiency, key=efficiency.get)
        allocation[best_channel] += residual

        return allocation


def build_sample_repository() -> AcquisitionRepository:
    repository = AcquisitionRepository()

    campaigns = [
        Campaign(
            "C001", "Google Search Acquisition",
            ChannelType.PAID_SEARCH,
            date(2026, 1, 1), date(2026, 12, 31),
            Decimal("50000"), Decimal("42000"),
            500000, 25000, 5000, 1000,
            Decimal("180000")
        ),
        Campaign(
            "C002", "Social Media Acquisition",
            ChannelType.PAID_SOCIAL,
            date(2026, 1, 1), date(2026, 12, 31),
            Decimal("40000"), Decimal("36000"),
            800000, 40000, 6000, 600,
            Decimal("90000")
        ),
        Campaign(
            "C003", "Organic Search Program",
            ChannelType.ORGANIC_SEARCH,
            date(2026, 1, 1), date(2026, 12, 31),
            Decimal("20000"), Decimal("15000"),
            600000, 30000, 4500, 900,
            Decimal("150000")
        ),
        Campaign(
            "C004", "Referral Program",
            ChannelType.REFERRAL,
            date(2026, 1, 1), date(2026, 12, 31),
            Decimal("15000"), Decimal("12000"),
            100000, 10000, 3000, 750,
            Decimal("140000")
        ),
        Campaign(
            "C005", "Email Acquisition",
            ChannelType.EMAIL,
            date(2026, 1, 1), date(2026, 12, 31),
            Decimal("10000"), Decimal("7000"),
            200000, 12000, 3600, 720,
            Decimal("110000")
        )
    ]

    for campaign in campaigns:
        repository.add_campaign(campaign)

    sample_customers = [
        ("U001", "C001", ChannelType.PAID_SEARCH, "120", "0.75"),
        ("U002", "C001", ChannelType.PAID_SEARCH, "150", "0.75"),
        ("U003", "C002", ChannelType.PAID_SOCIAL, "90", "0.65"),
        ("U004", "C002", ChannelType.PAID_SOCIAL, "110", "0.65"),
        ("U005", "C003", ChannelType.ORGANIC_SEARCH, "140", "0.80"),
        ("U006", "C003", ChannelType.ORGANIC_SEARCH, "160", "0.80"),
        ("U007", "C004", ChannelType.REFERRAL, "180", "0.82"),
        ("U008", "C004", ChannelType.REFERRAL, "170", "0.82"),
        ("U009", "C005", ChannelType.EMAIL, "130", "0.78"),
        ("U010", "C005", ChannelType.EMAIL, "125", "0.78")
    ]

    for customer_id, campaign_id, channel, revenue, margin in sample_customers:
        repository.add_customer(
            Customer(
                customer_id=customer_id,
                campaign_id=campaign_id,
                acquisition_channel=channel,
                acquisition_date=date(2026, 6, 15),
                first_purchase_revenue=Decimal(revenue),
                gross_margin_rate=Decimal(margin),
                monthly_retention_rate=Decimal("0.92"),
                monthly_revenue=Decimal("100")
            )
        )

    return repository


class AcquisitionTests(unittest.TestCase):

    def test_campaign_cac(self):
        campaign = Campaign(
            "T001", "Test",
            ChannelType.PAID_SEARCH,
            date(2026, 1, 1), date(2026, 12, 31),
            Decimal("1000"), Decimal("800"),
            10000, 500, 100, 20,
            Decimal("2000")
        )
        self.assertEqual(campaign.cac, Decimal("40"))

    def test_zero_conversion_cac(self):
        campaign = Campaign(
            "T002", "No Conversion",
            ChannelType.EMAIL,
            date(2026, 1, 1), date(2026, 12, 31),
            Decimal("1000"), Decimal("500")
        )
        self.assertIsNone(campaign.cac)

    def test_budget_allocation(self):
        allocations = [
            BudgetAllocation(ChannelType.PAID_SEARCH, Decimal("0"), Decimal("50")),
            BudgetAllocation(ChannelType.PAID_SOCIAL, Decimal("0"), Decimal("100"))
        ]

        result = BudgetOptimizer.allocate(Decimal("3000"), allocations)

        self.assertEqual(sum(result.values()), Decimal("3000"))
        self.assertGreater(
            result[ChannelType.PAID_SEARCH],
            result[ChannelType.PAID_SOCIAL]
        )

    def test_duplicate_customer(self):
        repository = build_sample_repository()
        customer = repository.customers["U001"]

        with self.assertRaises(ValidationError):
            repository.add_customer(customer)


def main():
    repository = build_sample_repository()
    analyzer = AcquisitionAnalyzer(repository)

    print("\nCUSTOMER ACQUISITION: CAMPAIGN PERFORMANCE")
    print("=" * 95)

    for report in analyzer.campaign_report():
        print(
            f"{report['campaign']:<30}"
            f" Spend: {report['spend']:>9.2f}"
            f" Customers: {report['conversions']:>5}"
            f" CAC: {str(round(report['cac'], 2) if report['cac'] is not None else 'N/A'):>8}"
            f" ROAS: {str(round(report['roas'], 2) if report['roas'] is not None else 'N/A'):>6}"
        )

    print("\nCHANNEL-LEVEL ANALYSIS")
    print("=" * 95)

    for report in analyzer.channel_recommendations():
        print(
            f"{report['channel']:<22}"
            f" CAC: {str(round(report['cac'], 2) if report['cac'] is not None else 'N/A'):>8}"
            f" LTV: {str(round(report['ltv'], 2) if report['ltv'] is not None else 'N/A'):>9}"
            f" LTV/CAC: {str(round(report['ltv_cac_ratio'], 2) if report['ltv_cac_ratio'] is not None else 'N/A'):>7}"
            f" {report['decision']}"
        )

    blended_cac = analyzer.calculate_blended_cac()
    ratio = analyzer.calculate_ltv_cac()

    print("\nBUSINESS PERFORMANCE")
    print(f"Blended CAC: {blended_cac:.2f}" if blended_cac is not None else "Blended CAC: N/A")
    print(f"Blended LTV/CAC: {ratio:.2f}" if ratio is not None else "Blended LTV/CAC: N/A")

    print("\nBUDGET ALLOCATION")
    allocations = [
        BudgetAllocation(ChannelType.PAID_SEARCH, Decimal("0"), Decimal("42")),
        BudgetAllocation(ChannelType.PAID_SOCIAL, Decimal("0"), Decimal("60")),
        BudgetAllocation(ChannelType.ORGANIC_SEARCH, Decimal("0"), Decimal("30")),
        BudgetAllocation(ChannelType.REFERRAL, Decimal("0"), Decimal("25")),
        BudgetAllocation(ChannelType.EMAIL, Decimal("0"), Decimal("20"))
    ]

    budget = BudgetOptimizer.allocate(Decimal("100000"), allocations)

    for channel, amount in budget.items():
        print(f"{channel.value:<22}: {amount:.2f}")

    print("\nRUNNING VALIDATION TESTS")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AcquisitionTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
