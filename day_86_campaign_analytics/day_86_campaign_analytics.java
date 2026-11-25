import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * Enterprise Campaign Analytics and Performance Management.
 *
 * Java 17 implementation featuring:
 * - Immutable domain records
 * - Campaign lifecycle management
 * - Financial performance metrics
 * - Channel aggregation
 * - Attribution records
 * - Budget governance
 * - Performance policies
 * - Validation and domain exceptions
 * - Merge-free, atomic state transitions
 */

public class CampaignAnalytics {

    enum Channel {
        SEARCH,
        SOCIAL,
        EMAIL,
        DISPLAY,
        AFFILIATE,
        VIDEO
    }

    enum CampaignStatus {
        ACTIVE,
        PAUSED,
        COMPLETED
    }

    enum PerformanceCategory {
        EXCELLENT,
        PROFITABLE,
        BREAK_EVEN,
        LOSS_MAKING,
        NO_INVESTMENT
    }

    enum AttributionModel {
        FIRST_TOUCH,
        LAST_TOUCH,
        LINEAR
    }

    static class CampaignException extends RuntimeException {
        CampaignException(String message) {
            super(message);
        }
    }

    static class CampaignNotFoundException
            extends CampaignException {
        CampaignNotFoundException(String id) {
            super("Campaign not found: " + id);
        }
    }

    record Campaign(
            String id,
            String name,
            Channel channel,
            CampaignStatus status,
            double budget,
            double spend,
            double revenue,
            long impressions,
            long clicks,
            long conversions,
            Instant createdAt
    ) {
        Campaign {
            id = Objects.requireNonNull(id).trim();
            name = Objects.requireNonNull(name).trim();
            Objects.requireNonNull(channel);
            Objects.requireNonNull(status);
            Objects.requireNonNull(createdAt);

            if (id.isEmpty() || name.isEmpty()) {
                throw new CampaignException(
                    "Campaign ID and name are required."
                );
            }

            if (
                !Double.isFinite(budget) ||
                !Double.isFinite(spend) ||
                !Double.isFinite(revenue) ||
                budget <= 0 ||
                spend < 0 ||
                revenue < 0
            ) {
                throw new CampaignException(
                    "Invalid financial values."
                );
            }

            if (
                impressions < 0 ||
                clicks < 0 ||
                conversions < 0
            ) {
                throw new CampaignException(
                    "Funnel values cannot be negative."
                );
            }

            if (
                clicks > impressions ||
                conversions > clicks
            ) {
                throw new CampaignException(
                    "Invalid conversion funnel."
                );
            }
        }

        Campaign withActivity(Activity activity) {
            return new Campaign(
                id,
                name,
                channel,
                status,
                budget,
                spend + activity.spend(),
                revenue + activity.revenue(),
                impressions + activity.impressions(),
                clicks + activity.clicks(),
                conversions + activity.conversions(),
                createdAt
            );
        }

        Campaign withStatus(CampaignStatus newStatus) {
            return new Campaign(
                id,
                name,
                channel,
                newStatus,
                budget,
                spend,
                revenue,
                impressions,
                clicks,
                conversions,
                createdAt
            );
        }
    }

    record Activity(
            double spend,
            double revenue,
            long impressions,
            long clicks,
            long conversions
    ) {
        Activity {
            if (
                !Double.isFinite(spend) ||
                !Double.isFinite(revenue) ||
                spend < 0 ||
                revenue < 0 ||
                impressions < 0 ||
                clicks < 0 ||
                conversions < 0
            ) {
                throw new CampaignException(
                    "Invalid activity record."
                );
            }
        }
    }

    record Metrics(
            String campaignId,
            String name,
            Channel channel,
            CampaignStatus status,
            double spend,
            double revenue,
            double profit,
            double roi,
            double roas,
            double ctr,
            double conversionRate,
            double cpc,
            double cpa,
            double cpm,
            double budgetUtilization
    ) {}

    record AttributionTouch(
            String campaignId,
            double revenue,
            int position
    ) {
        AttributionTouch {
            if (
                campaignId == null ||
                campaignId.isBlank() ||
                !Double.isFinite(revenue) ||
                revenue < 0 ||
                position < 0
            ) {
                throw new CampaignException(
                    "Invalid attribution touch."
                );
            }
        }
    }

    record ChannelReport(
            Channel channel,
            long campaignCount,
            double spend,
            double revenue,
            double profit,
            double roi,
            double roas
    ) {}

    record BudgetRule(
            double minimumRoas,
            double maximumUtilization,
            double reservePercentage
    ) {
        BudgetRule {
            if (
                minimumRoas < 0 ||
                maximumUtilization <= 0 ||
                reservePercentage < 0 ||
                reservePercentage >= 100
            ) {
                throw new CampaignException(
                    "Invalid budget policy."
                );
            }
        }
    }

    record PortfolioReport(
            int campaignCount,
            double totalSpend,
            double totalRevenue,
            double totalProfit,
            double roi,
            double roas
    ) {}

    static class MetricService {

        private static double divide(double a, double b) {
            return b == 0 ? 0 : a / b;
        }

        Metrics calculate(Campaign campaign) {
            double profit = campaign.revenue() - campaign.spend();

            return new Metrics(
                campaign.id(),
                campaign.name(),
                campaign.channel(),
                campaign.status(),
                campaign.spend(),
                campaign.revenue(),
                profit,
                divide(profit * 100, campaign.spend()),
                divide(campaign.revenue(), campaign.spend()),
                divide(
                    campaign.clicks() * 100.0,
                    campaign.impressions()
                ),
                divide(
                    campaign.conversions() * 100.0,
                    campaign.clicks()
                ),
                divide(
                    campaign.spend(),
                    campaign.clicks()
                ),
                divide(
                    campaign.spend(),
                    campaign.conversions()
                ),
                divide(
                    campaign.spend() * 1000,
                    campaign.impressions()
                ),
                divide(
                    campaign.spend() * 100,
                    campaign.budget()
                )
            );
        }

        PerformanceCategory classify(Metrics metric) {
            if (metric.spend() == 0) {
                return PerformanceCategory.NO_INVESTMENT;
            }

            if (
                metric.roi() > 100 &&
                metric.roas() >= 3
            ) {
                return PerformanceCategory.EXCELLENT;
            }

            if (metric.roi() > 0 && metric.roas() > 1) {
                return PerformanceCategory.PROFITABLE;
            }

            if (metric.roi() == 0) {
                return PerformanceCategory.BREAK_EVEN;
            }

            return PerformanceCategory.LOSS_MAKING;
        }
    }

    static class CampaignRepository {

        private final Map<String, Campaign> campaigns =
            new HashMap<>();

        synchronized void save(Campaign campaign) {
            Objects.requireNonNull(campaign);

            if (campaigns.containsKey(campaign.id())) {
                throw new CampaignException(
                    "Duplicate campaign ID: " + campaign.id()
                );
            }

            campaigns.put(campaign.id(), campaign);
        }

        synchronized Campaign find(String id) {
            Campaign campaign = campaigns.get(id);

            if (campaign == null) {
                throw new CampaignNotFoundException(id);
            }

            return campaign;
        }

        synchronized List<Campaign> findAll() {
            return List.copyOf(campaigns.values());
        }

        synchronized Campaign updateActivity(
                String id,
                Activity activity
        ) {
            Campaign current = find(id);

            Campaign updated = current.withActivity(activity);

            // Update occurs only after the complete new state validates.
            campaigns.put(id, updated);

            return updated;
        }

        synchronized Campaign updateStatus(
                String id,
                CampaignStatus status
        ) {
            Campaign current = find(id);

            if (current.status() == CampaignStatus.COMPLETED) {
                throw new CampaignException(
                    "Completed campaigns cannot be modified."
                );
            }

            Campaign updated = current.withStatus(status);
            campaigns.put(id, updated);

            return updated;
        }
    }

    static class PortfolioService {

        private final CampaignRepository repository;
        private final MetricService metrics;

        PortfolioService(
                CampaignRepository repository,
                MetricService metrics
        ) {
            this.repository = repository;
            this.metrics = metrics;
        }

        List<Metrics> evaluate() {
            return repository.findAll()
                .stream()
                .map(metrics::calculate)
                .toList();
        }

        PortfolioReport portfolio() {
            List<Metrics> results = evaluate();

            double spend = results.stream()
                .mapToDouble(Metrics::spend)
                .sum();

            double revenue = results.stream()
                .mapToDouble(Metrics::revenue)
                .sum();

            double profit = revenue - spend;

            return new PortfolioReport(
                results.size(),
                spend,
                revenue,
                profit,
                spend == 0 ? 0 : profit / spend * 100,
                spend == 0 ? 0 : revenue / spend
            );
        }

        List<Metrics> ranking() {
            return evaluate()
                .stream()
                .sorted(
                    Comparator
                        .comparingDouble(Metrics::profit)
                        .thenComparingDouble(Metrics::roi)
                        .thenComparingDouble(Metrics::roas)
                        .reversed()
                )
                .toList();
        }

        List<ChannelReport> channelReports() {
            Map<Channel, List<Metrics>> grouped =
                evaluate()
                    .stream()
                    .collect(
                        Collectors.groupingBy(
                            Metrics::channel,
                            () -> new EnumMap<>(Channel.class),
                            Collectors.toList()
                        )
                    );

            return grouped.entrySet()
                .stream()
                .map(entry -> {
                    List<Metrics> group = entry.getValue();

                    double spend = group.stream()
                        .mapToDouble(Metrics::spend)
                        .sum();

                    double revenue = group.stream()
                        .mapToDouble(Metrics::revenue)
                        .sum();

                    double profit = revenue - spend;

                    return new ChannelReport(
                        entry.getKey(),
                        group.size(),
                        spend,
                        revenue,
                        profit,
                        spend == 0 ? 0 : profit / spend * 100,
                        spend == 0 ? 0 : revenue / spend
                    );
                })
                .sorted(
                    Comparator.comparingDouble(
                        ChannelReport::profit
                    ).reversed()
                )
                .toList();
        }
    }

    static class BudgetGovernanceService {

        private final BudgetRule rule;

        BudgetGovernanceService(BudgetRule rule) {
            this.rule = rule;
        }

        Map<String, Double> allocate(
                List<Metrics> metrics,
                double additionalBudget
        ) {
            if (
                !Double.isFinite(additionalBudget) ||
                additionalBudget < 0
            ) {
                throw new CampaignException(
                    "Invalid additional budget."
                );
            }

            List<Metrics> eligible = metrics.stream()
                .filter(m ->
                    m.status() == CampaignStatus.ACTIVE
                )
                .filter(m ->
                    m.roas() >= rule.minimumRoas()
                )
                .filter(m ->
                    m.budgetUtilization() <
                        rule.maximumUtilization()
                )
                .filter(m -> m.spend() > 0)
                .toList();

            double available =
                additionalBudget *
                (1 - rule.reservePercentage() / 100);

            double totalSpend = eligible.stream()
                .mapToDouble(Metrics::spend)
                .sum();

            if (eligible.isEmpty() || totalSpend == 0) {
                return Map.of();
            }

            Map<String, Double> allocation = new HashMap<>();

            for (Metrics metric : eligible) {
                allocation.put(
                    metric.campaignId(),
                    available * metric.spend() / totalSpend
                );
            }

            return Map.copyOf(allocation);
        }
    }

    static class AttributionService {

        Map<String, Double> attribute(
                List<AttributionTouch> touches,
                AttributionModel model
        ) {
            Objects.requireNonNull(model);

            if (touches.isEmpty()) {
                return Map.of();
            }

            List<AttributionTouch> ordered = touches.stream()
                .sorted(
                    Comparator.comparingInt(
                        AttributionTouch::position
                    )
                )
                .toList();

            Map<String, Double> result = new HashMap<>();

            switch (model) {
                case FIRST_TOUCH -> {
                    AttributionTouch first = ordered.get(0);

                    result.merge(
                        first.campaignId(),
                        ordered.stream()
                            .mapToDouble(AttributionTouch::revenue)
                            .sum(),
                        Double::sum
                    );
                }

                case LAST_TOUCH -> {
                    AttributionTouch last =
                        ordered.get(ordered.size() - 1);

                    result.merge(
                        last.campaignId(),
                        ordered.stream()
                            .mapToDouble(AttributionTouch::revenue)
                            .sum(),
                        Double::sum
                    );
                }

                case LINEAR -> {
                    double totalRevenue = ordered.stream()
                        .mapToDouble(AttributionTouch::revenue)
                        .sum();

                    double share = totalRevenue / ordered.size();

                    for (AttributionTouch touch : ordered) {
                        result.merge(
                            touch.campaignId(),
                            share,
                            Double::sum
                        );
                    }
                }
            }

            return Map.copyOf(result);
        }
    }

    private static Campaign create(
            String id,
            String name,
            Channel channel,
            double budget,
            double spend,
            long impressions,
            long clicks,
            long conversions,
            double revenue,
            CampaignStatus status
    ) {
        return new Campaign(
            id,
            name,
            channel,
            status,
            budget,
            spend,
            revenue,
            impressions,
            clicks,
            conversions,
            Instant.now()
        );
    }

    private static void runTests() {
        Campaign campaign = create(
            "TEST",
            "Validation Campaign",
            Channel.SEARCH,
            1000,
            500,
            10000,
            1000,
            100,
            1500,
            CampaignStatus.ACTIVE
        );

        Metrics metrics = new MetricService().calculate(campaign);

        if (
            metrics.roas() != 3 ||
            metrics.roi() != 200 ||
            metrics.ctr() != 10
        ) {
            throw new AssertionError("Metric test failed.");
        }

        boolean rejected = false;

        try {
            create(
                "BAD",
                "Invalid Campaign",
                Channel.SEARCH,
                1000,
                500,
                100,
                200,
                10,
                1500,
                CampaignStatus.ACTIVE
            );
        } catch (CampaignException exception) {
            rejected = true;
        }

        if (!rejected) {
            throw new AssertionError(
                "Invalid funnel was accepted."
            );
        }

        System.out.println("All Java 17 tests passed.");
    }

    public static void main(String[] args) {
        runTests();

        CampaignRepository repository =
            new CampaignRepository();

        MetricService metricService = new MetricService();

        repository.save(create(
            "C001", "Search Conversion",
            Channel.SEARCH, 50000, 35000,
            500000, 25000, 1500, 140000,
            CampaignStatus.ACTIVE
        ));

        repository.save(create(
            "C002", "Social Awareness",
            Channel.SOCIAL, 40000, 30000,
            800000, 16000, 400, 45000,
            CampaignStatus.ACTIVE
        ));

        repository.save(create(
            "C003", "Email Retention",
            Channel.EMAIL, 20000, 12000,
            200000, 30000, 2400, 96000,
            CampaignStatus.ACTIVE
        ));

        repository.save(create(
            "C004", "Display Remarketing",
            Channel.DISPLAY, 30000, 25000,
            1000000, 10000, 250, 18000,
            CampaignStatus.ACTIVE
        ));

        repository.save(create(
            "C005", "Affiliate Acquisition",
            Channel.AFFILIATE, 25000, 15000,
            300000, 12000, 900, 75000,
            CampaignStatus.ACTIVE
        ));

        repository.save(create(
            "C006", "Video Awareness",
            Channel.VIDEO, 35000, 0,
            0, 0, 0, 0,
            CampaignStatus.PAUSED
        ));

        PortfolioService service =
            new PortfolioService(repository, metricService);

        PortfolioReport report = service.portfolio();

        System.out.println("\nPORTFOLIO PERFORMANCE");
        System.out.println("-----------------------------");
        System.out.println("Campaigns: " + report.campaignCount());
        System.out.println("Spend: " + report.totalSpend());
        System.out.println("Revenue: " + report.totalRevenue());
        System.out.println("Profit: " + report.totalProfit());
        System.out.println("ROI: " + report.roi() + "%");
        System.out.println("ROAS: " + report.roas());

        System.out.println("\nCAMPAIGN RANKING");

        service.ranking().forEach(metric ->
            System.out.printf(
                "%-25s ROI: %8.2f%% ROAS: %6.2f Profit: %10.2f%n",
                metric.name(),
                metric.roi(),
                metric.roas(),
                metric.profit()
            )
        );

        System.out.println("\nCHANNEL PERFORMANCE");

        service.channelReports().forEach(channel ->
            System.out.printf(
                "%-12s Spend: %10.2f Revenue: %10.2f ROAS: %.2f%n",
                channel.channel(),
                channel.spend(),
                channel.revenue(),
                channel.roas()
            )
        );

        BudgetGovernanceService governance =
            new BudgetGovernanceService(
                new BudgetRule(1.5, 120, 10)
            );

        Map<String, Double> allocations =
            governance.allocate(
                service.evaluate(),
                100000
            );

        System.out.println("\nBUDGET ALLOCATION");

        allocations.forEach((id, amount) ->
            System.out.printf(
                "%s: %.2f%n",
                id,
                amount
            )
        );

        AttributionService attribution =
            new AttributionService();

        Map<String, Double> attributed =
            attribution.attribute(
                List.of(
                    new AttributionTouch("C001", 10000, 1),
                    new AttributionTouch("C003", 10000, 2),
                    new AttributionTouch("C001", 10000, 3)
                ),
                AttributionModel.LINEAR
            );

        System.out.println("\nLINEAR ATTRIBUTION");
        attributed.forEach((id, revenue) ->
            System.out.printf("%s: %.2f%n", id, revenue)
        );
    }
}
