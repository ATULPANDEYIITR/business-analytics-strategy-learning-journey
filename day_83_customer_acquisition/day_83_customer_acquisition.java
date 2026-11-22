import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/*
 * Enterprise Customer Acquisition and CAC Management.
 *
 * Java 17
 * Dependencies: Java standard library only.
 *
 * Demonstrates domain modeling, campaign lifecycle management,
 * acquisition attribution, unit economics, policy evaluation,
 * and budget allocation.
 */
public class CustomerAcquisition {

    private static final MathContext MC =
            new MathContext(12, RoundingMode.HALF_UP);

    enum Channel {
        PAID_SEARCH,
        PAID_SOCIAL,
        ORGANIC_SEARCH,
        EMAIL,
        REFERRAL,
        AFFILIATE,
        CONTENT,
        EVENTS,
        DIRECT
    }

    enum CampaignStatus {
        DRAFT,
        ACTIVE,
        PAUSED,
        COMPLETED
    }

    enum Decision {
        SCALE,
        OPTIMIZE,
        REDUCE,
        INSUFFICIENT_DATA
    }

    enum AttributionModel {
        FIRST_TOUCH,
        LAST_TOUCH,
        LINEAR
    }

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static class ValidationException extends DomainException {
        ValidationException(String message) {
            super(message);
        }
    }

    static BigDecimal amount(String value) {
        BigDecimal result = new BigDecimal(value);

        if (result.signum() < 0) {
            throw new ValidationException("Negative financial amount.");
        }

        return result;
    }

    static BigDecimal divide(BigDecimal numerator, BigDecimal denominator) {
        if (denominator.signum() == 0) {
            throw new DomainException("Division by zero.");
        }

        return numerator.divide(denominator, MC);
    }

    record CampaignId(String value) {
        CampaignId {
            if (value == null || value.isBlank()) {
                throw new ValidationException("Campaign ID is required.");
            }
        }
    }

    record CustomerId(String value) {
        CustomerId {
            if (value == null || value.isBlank()) {
                throw new ValidationException("Customer ID is required.");
            }
        }
    }

    record AcquisitionTouchpoint(
            Channel channel,
            LocalDate occurredOn
    ) {
        AcquisitionTouchpoint {
            Objects.requireNonNull(channel);
            Objects.requireNonNull(occurredOn);
        }
    }

    record Customer(
            CustomerId id,
            CampaignId campaignId,
            Channel channel,
            LocalDate acquiredOn,
            BigDecimal firstPurchase,
            BigDecimal monthlyRevenue,
            BigDecimal grossMargin,
            BigDecimal retention
    ) {
        Customer {
            Objects.requireNonNull(id);
            Objects.requireNonNull(campaignId);
            Objects.requireNonNull(channel);
            Objects.requireNonNull(acquiredOn);

            firstPurchase = validateMoney(firstPurchase);
            monthlyRevenue = validateMoney(monthlyRevenue);
            grossMargin = validateRatio(grossMargin, "gross margin");
            retention = validateRatio(retention, "retention");
        }

        private static BigDecimal validateMoney(BigDecimal value) {
            Objects.requireNonNull(value);

            if (value.signum() < 0) {
                throw new ValidationException("Revenue cannot be negative.");
            }

            return value;
        }

        private static BigDecimal validateRatio(
                BigDecimal value,
                String field
        ) {
            Objects.requireNonNull(value);

            if (value.compareTo(BigDecimal.ZERO) < 0 ||
                    value.compareTo(BigDecimal.ONE) > 0) {
                throw new ValidationException(
                        field + " must be between 0 and 1."
                );
            }

            return value;
        }

        BigDecimal lifetimeValue(int months) {
            if (months < 1) {
                throw new ValidationException(
                        "Projection months must be positive."
                );
            }

            BigDecimal initialProfit =
                    firstPurchase.multiply(grossMargin, MC);

            BigDecimal monthlyProfit =
                    monthlyRevenue.multiply(grossMargin, MC);

            BigDecimal retained = BigDecimal.ONE;
            BigDecimal recurringProfit = BigDecimal.ZERO;

            for (int month = 1; month <= months; month++) {
                retained = retained.multiply(retention, MC);

                recurringProfit = recurringProfit.add(
                        monthlyProfit.multiply(retained, MC),
                        MC
                );
            }

            return initialProfit.add(recurringProfit, MC);
        }
    }

    static class Campaign {
        private final CampaignId id;
        private final String name;
        private final Channel channel;
        private final LocalDate startDate;
        private final LocalDate endDate;
        private final BigDecimal budget;

        private BigDecimal spend;
        private BigDecimal revenue;

        private long impressions;
        private long clicks;
        private long leads;
        private long conversions;

        private CampaignStatus status = CampaignStatus.DRAFT;

        Campaign(
                CampaignId id,
                String name,
                Channel channel,
                LocalDate startDate,
                LocalDate endDate,
                BigDecimal budget,
                BigDecimal spend,
                long impressions,
                long clicks,
                long leads,
                long conversions,
                BigDecimal revenue
        ) {
            this.id = Objects.requireNonNull(id);

            if (name == null || name.isBlank()) {
                throw new ValidationException("Campaign name is required.");
            }

            this.name = name;
            this.channel = Objects.requireNonNull(channel);
            this.startDate = Objects.requireNonNull(startDate);
            this.endDate = Objects.requireNonNull(endDate);
            this.budget = validateMoney(budget);
            this.spend = validateMoney(spend);
            this.revenue = validateMoney(revenue);

            this.impressions = validateCount(impressions);
            this.clicks = validateCount(clicks);
            this.leads = validateCount(leads);
            this.conversions = validateCount(conversions);

            validate();
        }

        private static BigDecimal validateMoney(BigDecimal value) {
            Objects.requireNonNull(value);

            if (value.signum() < 0) {
                throw new ValidationException("Negative financial value.");
            }

            return value;
        }

        private static long validateCount(long value) {
            if (value < 0) {
                throw new ValidationException("Negative marketing metric.");
            }

            return value;
        }

        private void validate() {
            if (endDate.isBefore(startDate)) {
                throw new ValidationException("Invalid campaign dates.");
            }

            if (spend.compareTo(budget) > 0) {
                throw new ValidationException("Campaign budget exceeded.");
            }

            if (clicks > impressions || leads > clicks ||
                    conversions > leads) {
                throw new ValidationException(
                        "Campaign funnel metrics are inconsistent."
                );
            }
        }

        void activate() {
            if (status != CampaignStatus.DRAFT &&
                    status != CampaignStatus.PAUSED) {
                throw new DomainException(
                        "Campaign cannot be activated from " + status
                );
            }

            status = CampaignStatus.ACTIVE;
        }

        void pause() {
            requireStatus(CampaignStatus.ACTIVE);
            status = CampaignStatus.PAUSED;
        }

        void complete() {
            if (status == CampaignStatus.COMPLETED) {
                throw new DomainException("Campaign already completed.");
            }

            status = CampaignStatus.COMPLETED;
        }

        private void requireStatus(CampaignStatus expected) {
            if (status != expected) {
                throw new DomainException(
                        "Expected " + expected + ", found " + status
                );
            }
        }

        void recordSpend(BigDecimal additionalSpend) {
            additionalSpend = validateMoney(additionalSpend);
            requireStatus(CampaignStatus.ACTIVE);

            BigDecimal proposed = spend.add(additionalSpend);

            if (proposed.compareTo(budget) > 0) {
                throw new DomainException("Budget limit exceeded.");
            }

            spend = proposed;
        }

        BigDecimal cac() {
            return conversions == 0
                    ? null
                    : divide(spend, BigDecimal.valueOf(conversions));
        }

        BigDecimal roas() {
            return spend.signum() == 0
                    ? null
                    : divide(revenue, spend);
        }

        BigDecimal ctr() {
            return impressions == 0
                    ? BigDecimal.ZERO
                    : divide(
                            BigDecimal.valueOf(clicks),
                            BigDecimal.valueOf(impressions)
                    ).multiply(BigDecimal.valueOf(100), MC);
        }

        CampaignId id() {
            return id;
        }

        String name() {
            return name;
        }

        Channel channel() {
            return channel;
        }

        LocalDate startDate() {
            return startDate;
        }

        LocalDate endDate() {
            return endDate;
        }

        CampaignStatus status() {
            return status;
        }

        BigDecimal spend() {
            return spend;
        }

        long conversions() {
            return conversions;
        }
    }

    static class AcquisitionRepository {
        private final Map<CampaignId, Campaign> campaigns = new HashMap<>();
        private final Map<CustomerId, Customer> customers = new HashMap<>();

        void registerCampaign(Campaign campaign) {
            if (campaigns.putIfAbsent(campaign.id(), campaign) != null) {
                throw new ValidationException("Duplicate campaign.");
            }
        }

        void activateCampaign(CampaignId campaignId) {
            requireCampaign(campaignId).activate();
        }

        Campaign requireCampaign(CampaignId id) {
            Campaign campaign = campaigns.get(id);

            if (campaign == null) {
                throw new DomainException("Campaign does not exist.");
            }

            return campaign;
        }

        void registerCustomer(Customer customer) {
            if (customers.containsKey(customer.id())) {
                throw new ValidationException("Duplicate customer.");
            }

            Campaign campaign = requireCampaign(customer.campaignId());

            if (campaign.status() != CampaignStatus.ACTIVE) {
                throw new DomainException("Campaign is not active.");
            }

            if (campaign.channel() != customer.channel()) {
                throw new ValidationException("Channel mismatch.");
            }

            if (customer.acquiredOn().isBefore(campaign.startDate()) ||
                    customer.acquiredOn().isAfter(campaign.endDate())) {
                throw new ValidationException(
                        "Customer acquisition outside campaign period."
                );
            }

            customers.put(customer.id(), customer);
        }

        Map<CampaignId, Campaign> campaigns() {
            return Collections.unmodifiableMap(campaigns);
        }

        Map<CustomerId, Customer> customers() {
            return Collections.unmodifiableMap(customers);
        }
    }

    static class AttributionService {

        Map<Channel, BigDecimal> calculate(
                List<AcquisitionTouchpoint> touchpoints,
                AttributionModel model
        ) {
            if (touchpoints == null || touchpoints.isEmpty()) {
                throw new ValidationException("Touchpoints are required.");
            }

            List<AcquisitionTouchpoint> ordered = touchpoints.stream()
                    .sorted(
                            java.util.Comparator.comparing(
                                    AcquisitionTouchpoint::occurredOn
                            )
                    )
                    .toList();

            Map<Channel, BigDecimal> result =
                    new EnumMap<>(Channel.class);

            if (model == AttributionModel.FIRST_TOUCH) {
                result.put(ordered.get(0).channel(), BigDecimal.ONE);
                return result;
            }

            if (model == AttributionModel.LAST_TOUCH) {
                result.put(
                        ordered.get(ordered.size() - 1).channel(),
                        BigDecimal.ONE
                );
                return result;
            }

            BigDecimal credit = BigDecimal.ONE.divide(
                    BigDecimal.valueOf(ordered.size()),
                    MC
            );

            for (AcquisitionTouchpoint touchpoint : ordered) {
                result.merge(
                        touchpoint.channel(),
                        credit,
                        (a, b) -> a.add(b, MC)
                );
            }

            return result;
        }
    }

    record ChannelMetrics(
            Channel channel,
            BigDecimal spend,
            BigDecimal customers,
            BigDecimal revenue,
            BigDecimal grossProfit
    ) {
        BigDecimal cac() {
            return customers.signum() == 0
                    ? null
                    : divide(spend, customers);
        }

        BigDecimal ltv() {
            return customers.signum() == 0
                    ? null
                    : divide(grossProfit, customers);
        }

        BigDecimal ltvCacRatio() {
            BigDecimal acquisitionCost = cac();
            BigDecimal lifetimeValue = ltv();

            if (acquisitionCost == null ||
                    acquisitionCost.signum() == 0 ||
                    lifetimeValue == null) {
                return null;
            }

            return divide(lifetimeValue, acquisitionCost);
        }

        BigDecimal roas() {
            return spend.signum() == 0
                    ? null
                    : divide(revenue, spend);
        }
    }

    static class AnalyticsService {
        private final AcquisitionRepository repository;

        AnalyticsService(AcquisitionRepository repository) {
            this.repository = repository;
        }

        List<ChannelMetrics> analyze(int projectionMonths) {
            Map<Channel, BigDecimal[]> totals =
                    new EnumMap<>(Channel.class);

            for (Channel channel : Channel.values()) {
                totals.put(channel, new BigDecimal[]{
                        BigDecimal.ZERO,
                        BigDecimal.ZERO,
                        BigDecimal.ZERO,
                        BigDecimal.ZERO
                });
            }

            for (Campaign campaign : repository.campaigns().values()) {
                totals.get(campaign.channel())[0] =
                        totals.get(campaign.channel())[0]
                                .add(campaign.spend(), MC);
            }

            for (Customer customer : repository.customers().values()) {
                BigDecimal[] values = totals.get(customer.channel());

                values[1] = values[1].add(BigDecimal.ONE, MC);
                values[2] = values[2].add(customer.firstPurchase(), MC);
                values[3] = values[3].add(
                        customer.lifetimeValue(projectionMonths),
                        MC
                );
            }

            return totals.entrySet().stream()
                    .map(entry -> new ChannelMetrics(
                            entry.getKey(),
                            entry.getValue()[0],
                            entry.getValue()[1],
                            entry.getValue()[2],
                            entry.getValue()[3]
                    ))
                    .sorted((a, b) -> {
                        BigDecimal left = a.cac();
                        BigDecimal right = b.cac();

                        if (left == null) return 1;
                        if (right == null) return -1;

                        return left.compareTo(right);
                    })
                    .toList();
        }

        BigDecimal blendedCAC() {
            BigDecimal spend = repository.campaigns().values().stream()
                    .map(Campaign::spend)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);

            long customerCount = repository.customers().size();

            return customerCount == 0
                    ? null
                    : divide(spend, BigDecimal.valueOf(customerCount));
        }
    }

    record AcquisitionPolicy(
            int minimumCustomers,
            BigDecimal minimumLtvCac,
            BigDecimal maximumCAC
    ) {
        AcquisitionPolicy {
            if (minimumCustomers < 1) {
                throw new ValidationException(
                        "Minimum customer count must be positive."
                );
            }

            if (minimumLtvCac.signum() <= 0 ||
                    maximumCAC.signum() <= 0) {
                throw new ValidationException("Invalid policy thresholds.");
            }
        }

        Decision evaluate(ChannelMetrics metrics) {
            if (metrics.customers().compareTo(
                    BigDecimal.valueOf(minimumCustomers)
            ) < 0) {
                return Decision.INSUFFICIENT_DATA;
            }

            BigDecimal cac = metrics.cac();
            BigDecimal ratio = metrics.ltvCacRatio();

            if (cac == null || ratio == null) {
                return Decision.INSUFFICIENT_DATA;
            }

            if (ratio.compareTo(minimumLtvCac) >= 0 &&
                    cac.compareTo(maximumCAC) <= 0) {
                return Decision.SCALE;
            }

            if (ratio.compareTo(BigDecimal.ONE) >= 0) {
                return Decision.OPTIMIZE;
            }

            return Decision.REDUCE;
        }
    }

    record BudgetForecast(
            Channel channel,
            BigDecimal expectedCAC
    ) {
        BudgetForecast {
            Objects.requireNonNull(channel);
            Objects.requireNonNull(expectedCAC);

            if (expectedCAC.signum() <= 0) {
                throw new ValidationException(
                        "Expected CAC must be positive."
                );
            }
        }
    }

    static class BudgetAllocationService {

        Map<Channel, BigDecimal> allocate(
                BigDecimal totalBudget,
                List<BudgetForecast> forecasts,
                BigDecimal minimumAllocation
        ) {
            if (totalBudget.signum() < 0 ||
                    minimumAllocation.signum() < 0) {
                throw new ValidationException("Invalid budget.");
            }

            if (forecasts == null || forecasts.isEmpty()) {
                throw new ValidationException("Forecasts are required.");
            }

            Set<Channel> uniqueChannels = new HashSet<>();

            for (BudgetForecast forecast : forecasts) {
                if (!uniqueChannels.add(forecast.channel())) {
                    throw new ValidationException(
                            "Duplicate forecast channel."
                    );
                }
            }

            BigDecimal minimumTotal = minimumAllocation.multiply(
                    BigDecimal.valueOf(forecasts.size())
            );

            if (minimumTotal.compareTo(totalBudget) > 0) {
                throw new DomainException(
                        "Minimum allocation exceeds available budget."
                );
            }

            BigDecimal totalEfficiency = forecasts.stream()
                    .map(f -> BigDecimal.ONE.divide(f.expectedCAC(), MC))
                    .reduce(BigDecimal.ZERO, (a, b) -> a.add(b, MC));

            BigDecimal remaining = totalBudget.subtract(minimumTotal);
            Map<Channel, BigDecimal> result =
                    new EnumMap<>(Channel.class);

            BigDecimal allocated = BigDecimal.ZERO;
            Channel mostEfficient = forecasts.stream()
                    .min(java.util.Comparator.comparing(
                            BudgetForecast::expectedCAC
                    ))
                    .orElseThrow()
                    .channel();

            for (BudgetForecast forecast : forecasts) {
                BigDecimal efficiency = BigDecimal.ONE.divide(
                        forecast.expectedCAC(),
                        MC
                );

                BigDecimal share = efficiency.divide(
                        totalEfficiency,
                        MC
                );

                BigDecimal amount = minimumAllocation.add(
                        remaining.multiply(share, MC),
                        MC
                );

                result.put(forecast.channel(), amount);
                allocated = allocated.add(amount, MC);
            }

            // Preserve the exact total despite decimal rounding.
            BigDecimal residual = totalBudget.subtract(allocated);
            result.merge(mostEfficient, residual, BigDecimal::add);

            return result;
        }
    }

    static AcquisitionRepository sampleData() {
        AcquisitionRepository repository = new AcquisitionRepository();

        LocalDate start = LocalDate.of(2026, 1, 1);
        LocalDate end = LocalDate.of(2026, 12, 31);

        List<Campaign> campaigns = List.of(
                new Campaign(
                        new CampaignId("C001"), "Search Acquisition",
                        Channel.PAID_SEARCH, start, end,
                        amount("50000"), amount("42000"),
                        500000, 25000, 5000, 1000,
                        amount("180000")
                ),
                new Campaign(
                        new CampaignId("C002"), "Social Acquisition",
                        Channel.PAID_SOCIAL, start, end,
                        amount("40000"), amount("36000"),
                        800000, 40000, 6000, 600,
                        amount("90000")
                ),
                new Campaign(
                        new CampaignId("C003"), "Organic Acquisition",
                        Channel.ORGANIC_SEARCH, start, end,
                        amount("20000"), amount("15000"),
                        600000, 30000, 4500, 900,
                        amount("150000")
                ),
                new Campaign(
                        new CampaignId("C004"), "Referral Acquisition",
                        Channel.REFERRAL, start, end,
                        amount("15000"), amount("12000"),
                        100000, 10000, 3000, 750,
                        amount("140000")
                ),
                new Campaign(
                        new CampaignId("C005"), "Email Acquisition",
                        Channel.EMAIL, start, end,
                        amount("10000"), amount("7000"),
                        200000, 12000, 3600, 720,
                        amount("110000")
                )
        );

        campaigns.forEach(repository::registerCampaign);

        campaigns.forEach(c ->
                repository.activateCampaign(c.id())
        );

        LocalDate acquired = LocalDate.of(2026, 6, 15);

        List<Customer> customers = List.of(
                new Customer(
                        new CustomerId("U001"), new CampaignId("C001"),
                        Channel.PAID_SEARCH, acquired,
                        amount("120"), amount("100"),
                        amount("0.75"), amount("0.92")
                ),
                new Customer(
                        new CustomerId("U002"), new CampaignId("C001"),
                        Channel.PAID_SEARCH, acquired,
                        amount("150"), amount("100"),
                        amount("0.75"), amount("0.92")
                ),
                new Customer(
                        new CustomerId("U003"), new CampaignId("C002"),
                        Channel.PAID_SOCIAL, acquired,
                        amount("90"), amount("100"),
                        amount("0.65"), amount("0.90")
                ),
                new Customer(
                        new CustomerId("U004"), new CampaignId("C002"),
                        Channel.PAID_SOCIAL, acquired,
                        amount("110"), amount("100"),
                        amount("0.65"), amount("0.90")
                ),
                new Customer(
                        new CustomerId("U005"), new CampaignId("C003"),
                        Channel.ORGANIC_SEARCH, acquired,
                        amount("140"), amount("100"),
                        amount("0.80"), amount("0.93")
                ),
                new Customer(
                        new CustomerId("U006"), new CampaignId("C003"),
                        Channel.ORGANIC_SEARCH, acquired,
                        amount("160"), amount("100"),
                        amount("0.80"), amount("0.93")
                ),
                new Customer(
                        new CustomerId("U007"), new CampaignId("C004"),
                        Channel.REFERRAL, acquired,
                        amount("180"), amount("100"),
                        amount("0.82"), amount("0.94")
                ),
                new Customer(
                        new CustomerId("U008"), new CampaignId("C004"),
                        Channel.REFERRAL, acquired,
                        amount("170"), amount("100"),
                        amount("0.82"), amount("0.94")
                ),
                new Customer(
                        new CustomerId("U009"), new CampaignId("C005"),
                        Channel.EMAIL, acquired,
                        amount("130"), amount("100"),
                        amount("0.78"), amount("0.92")
                ),
                new Customer(
                        new CustomerId("U010"), new CampaignId("C005"),
                        Channel.EMAIL, acquired,
                        amount("125"), amount("100"),
                        amount("0.78"), amount("0.92")
                )
        );

        customers.forEach(repository::registerCustomer);

        return repository;
    }

    static void runTests() {
        Campaign campaign = new Campaign(
                new CampaignId("TEST"),
                "Test Campaign",
                Channel.PAID_SEARCH,
                LocalDate.of(2026, 1, 1),
                LocalDate.of(2026, 12, 31),
                amount("1000"),
                amount("800"),
                10000, 500, 100, 20,
                amount("2000")
        );

        if (campaign.cac().compareTo(amount("40")) != 0) {
            throw new AssertionError("CAC test failed.");
        }

        AttributionService attribution = new AttributionService();

        Map<Channel, BigDecimal> credits = attribution.calculate(
                List.of(
                        new AcquisitionTouchpoint(
                                Channel.PAID_SOCIAL,
                                LocalDate.of(2026, 1, 1)
                        ),
                        new AcquisitionTouchpoint(
                                Channel.PAID_SEARCH,
                                LocalDate.of(2026, 1, 5)
                        )
                ),
                AttributionModel.LINEAR
        );

        BigDecimal total = credits.values().stream()
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        if (total.compareTo(BigDecimal.ONE) != 0) {
            throw new AssertionError("Attribution test failed.");
        }

        Map<Channel, BigDecimal> allocation =
                new BudgetAllocationService().allocate(
                        amount("3000"),
                        List.of(
                                new BudgetForecast(
                                        Channel.PAID_SEARCH,
                                        amount("50")
                                ),
                                new BudgetForecast(
                                        Channel.PAID_SOCIAL,
                                        amount("100")
                                )
                        ),
                        amount("0")
                );

        BigDecimal allocated = allocation.values().stream()
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        if (allocated.compareTo(amount("3000")) != 0) {
            throw new AssertionError("Allocation test failed.");
        }

        System.out.println("All enterprise validation tests passed.");
    }

    public static void main(String[] args) {
        try {
            AcquisitionRepository repository = sampleData();

            AnalyticsService analytics =
                    new AnalyticsService(repository);

            AcquisitionPolicy policy = new AcquisitionPolicy(
                    2,
                    amount("3"),
                    amount("1000")
            );

            System.out.println("\nCUSTOMER ACQUISITION REPORT");
            System.out.println("=".repeat(105));

            for (Campaign campaign : repository.campaigns().values()) {
                System.out.printf(
                        "%-25s | %-18s | Spend: %10s | CAC: %10s%n",
                        campaign.name(),
                        campaign.channel(),
                        campaign.spend(),
                        campaign.cac() == null
                                ? "N/A"
                                : campaign.cac().setScale(
                                        2,
                                        RoundingMode.HALF_UP
                                )
                );
            }

            System.out.println("\nCHANNEL UNIT ECONOMICS");

            List<ChannelMetrics> report = analytics.analyze(24);

            for (ChannelMetrics metrics : report) {
                Decision decision = policy.evaluate(metrics);

                System.out.printf(
                        "%-18s | CAC: %10s | LTV: %10s | Ratio: %8s | %s%n",
                        metrics.channel(),
                        metrics.cac() == null
                                ? "N/A"
                                : metrics.cac().setScale(2, RoundingMode.HALF_UP),
                        metrics.ltv() == null
                                ? "N/A"
                                : metrics.ltv().setScale(2, RoundingMode.HALF_UP),
                        metrics.ltvCacRatio() == null
                                ? "N/A"
                                : metrics.ltvCacRatio().setScale(
                                        2,
                                        RoundingMode.HALF_UP
                                ),
                        decision
                );
            }

            System.out.println(
                    "\nBLENDED CAC: " + analytics.blendedCAC()
            );

            System.out.println("\nPROPOSED BUDGET");

            Map<Channel, BigDecimal> allocation =
                    new BudgetAllocationService().allocate(
                            amount("100000"),
                            List.of(
                                    new BudgetForecast(
                                            Channel.PAID_SEARCH,
                                            amount("42")
                                    ),
                                    new BudgetForecast(
                                            Channel.PAID_SOCIAL,
                                            amount("60")
                                    ),
                                    new BudgetForecast(
                                            Channel.ORGANIC_SEARCH,
                                            amount("30")
                                    ),
                                    new BudgetForecast(
                                            Channel.REFERRAL,
                                            amount("25")
                                    ),
                                    new BudgetForecast(
                                            Channel.EMAIL,
                                            amount("20")
                                    )
                            ),
                            amount("0")
                    );

            allocation.forEach((channel, value) ->
                    System.out.println(channel + ": " + value)
            );

            System.out.println("\nVALIDATION");
            runTests();

        } catch (DomainException exception) {
            System.err.println(
                    "Acquisition domain error: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
