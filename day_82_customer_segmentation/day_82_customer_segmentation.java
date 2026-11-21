import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Collectors;

public class CustomerSegmentationEnterprise {

    enum CustomerStatus {
        ACTIVE,
        INACTIVE,
        SUSPENDED
    }

    enum ValueTier {
        HIGH_VALUE,
        MEDIUM_VALUE,
        LOW_VALUE
    }

    enum BehavioralSegment {
        LOYAL_ACTIVE,
        RECENT_CUSTOMER,
        DIGITALLY_ENGAGED,
        REPEAT_CUSTOMER,
        OCCASIONAL_CUSTOMER,
        DORMANT
    }

    enum CampaignType {
        PREMIUM_RETENTION,
        DIGITAL_ENGAGEMENT,
        STANDARD_ENGAGEMENT,
        REACTIVATION
    }

    static class SegmentationException extends RuntimeException {
        public SegmentationException(String message) {
            super(message);
        }
    }

    static class PolicyViolationException extends RuntimeException {
        public PolicyViolationException(String message) {
            super(message);
        }
    }

    record Customer(
        long id,
        String name,
        int age,
        String region,
        String occupation,
        double annualIncome,
        int purchaseFrequency,
        double totalSpend,
        LocalDate lastPurchase,
        int sessions,
        int emailInteractions,
        int productViews,
        CustomerStatus status
    ) {
        public Customer {
            if (id <= 0) {
                throw new SegmentationException(
                    "Customer ID must be positive."
                );
            }

            if (name == null || name.isBlank()) {
                throw new SegmentationException(
                    "Customer name is required."
                );
            }

            if (age < 18 || age > 120) {
                throw new SegmentationException(
                    "Customer age is outside the permitted range."
                );
            }

            if (
                !Double.isFinite(annualIncome) ||
                !Double.isFinite(totalSpend) ||
                annualIncome < 0 ||
                totalSpend < 0
            ) {
                throw new SegmentationException(
                    "Financial values must be finite and non-negative."
                );
            }

            if (
                purchaseFrequency < 0 ||
                sessions < 0 ||
                emailInteractions < 0 ||
                productViews < 0
            ) {
                throw new SegmentationException(
                    "Behavioral measurements cannot be negative."
                );
            }

            if (purchaseFrequency == 0 && totalSpend > 0) {
                throw new SegmentationException(
                    "Spending requires recorded purchases."
                );
            }

            Objects.requireNonNull(lastPurchase);
            Objects.requireNonNull(status);
        }
    }

    record SegmentationPolicy(
        double highValueThreshold,
        double mediumValueThreshold,
        double highIncomeThreshold,
        int recentDays,
        int dormantDays,
        int frequentPurchaseThreshold,
        int engagedSessionThreshold,
        int engagedEmailThreshold
    ) {
        public SegmentationPolicy {
            if (
                highValueThreshold <= mediumValueThreshold ||
                mediumValueThreshold < 0
            ) {
                throw new IllegalArgumentException(
                    "Invalid value thresholds."
                );
            }

            if (
                highIncomeThreshold <= 0 ||
                recentDays <= 0 ||
                dormantDays <= recentDays ||
                frequentPurchaseThreshold <= 0 ||
                engagedSessionThreshold <= 0 ||
                engagedEmailThreshold <= 0
            ) {
                throw new IllegalArgumentException(
                    "Invalid segmentation configuration."
                );
            }
        }

        public static SegmentationPolicy standard() {
            return new SegmentationPolicy(
                100000,
                30000,
                1200000,
                30,
                180,
                10,
                20,
                10
            );
        }
    }

    record DemographicProfile(
        String ageGroup,
        String incomeGroup,
        String region
    ) {
        public String segmentName() {
            return ageGroup + "_" + incomeGroup;
        }
    }

    record SegmentationResult(
        long customerId,
        DemographicProfile demographic,
        BehavioralSegment behavioral,
        ValueTier valueTier,
        int recencyDays,
        int frequency,
        double monetaryValue,
        double averageOrderValue,
        LocalDate evaluatedDate
    ) {}

    record CampaignDecision(
        long customerId,
        boolean eligible,
        CampaignType campaign,
        String reason
    ) {}

    record SegmentReport(
        long customerCount,
        double totalRevenue,
        double averageRevenue,
        Map<String, Long> demographicDistribution,
        Map<BehavioralSegment, Long> behavioralDistribution,
        Map<ValueTier, Long> valueDistribution
    ) {}

    interface SegmentationRule {
        boolean applies(
            Customer customer,
            SegmentationResult result
        );

        CampaignType campaign();

        String explanation();
    }

    static class CustomerRepository {
        private final Map<Long, Customer> customers =
            new HashMap<>();

        public synchronized void add(Customer customer) {
            Objects.requireNonNull(customer);

            if (customers.containsKey(customer.id())) {
                throw new SegmentationException(
                    "Duplicate customer ID: " + customer.id()
                );
            }

            customers.put(customer.id(), customer);
        }

        public synchronized Customer find(long id) {
            Customer customer = customers.get(id);

            if (customer == null) {
                throw new SegmentationException(
                    "Customer not found: " + id
                );
            }

            return customer;
        }

        public synchronized List<Customer> findAll() {
            return customers.values()
                .stream()
                .sorted(
                    java.util.Comparator.comparingLong(Customer::id)
                )
                .toList();
        }
    }

    static class SegmentationService {
        private final SegmentationPolicy policy;

        public SegmentationService(SegmentationPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        private DemographicProfile classifyDemographics(
            Customer customer
        ) {
            String ageGroup;

            if (customer.age() < 30) {
                ageGroup = "YOUNG_ADULT";
            } else if (customer.age() < 45) {
                ageGroup = "ADULT";
            } else if (customer.age() < 60) {
                ageGroup = "MIDDLE_AGED";
            } else {
                ageGroup = "SENIOR";
            }

            String incomeGroup;

            if (
                customer.annualIncome() >=
                policy.highIncomeThreshold()
            ) {
                incomeGroup = "HIGH_INCOME";
            } else if (
                customer.annualIncome() >=
                policy.highIncomeThreshold() / 3
            ) {
                incomeGroup = "MIDDLE_INCOME";
            } else {
                incomeGroup = "LOWER_INCOME";
            }

            return new DemographicProfile(
                ageGroup,
                incomeGroup,
                customer.region()
            );
        }

        private BehavioralSegment classifyBehavior(
            Customer customer,
            int recency
        ) {
            if (recency > policy.dormantDays()) {
                return BehavioralSegment.DORMANT;
            }

            if (
                recency <= policy.recentDays() &&
                customer.purchaseFrequency() >=
                    policy.frequentPurchaseThreshold()
            ) {
                return BehavioralSegment.LOYAL_ACTIVE;
            }

            if (recency <= policy.recentDays()) {
                return BehavioralSegment.RECENT_CUSTOMER;
            }

            if (
                customer.sessions() >=
                    policy.engagedSessionThreshold() ||
                customer.emailInteractions() >=
                    policy.engagedEmailThreshold()
            ) {
                return BehavioralSegment.DIGITALLY_ENGAGED;
            }

            if (
                customer.purchaseFrequency() >=
                policy.frequentPurchaseThreshold()
            ) {
                return BehavioralSegment.REPEAT_CUSTOMER;
            }

            return BehavioralSegment.OCCASIONAL_CUSTOMER;
        }

        private ValueTier classifyValue(Customer customer) {
            if (
                customer.totalSpend() >=
                policy.highValueThreshold()
            ) {
                return ValueTier.HIGH_VALUE;
            }

            if (
                customer.totalSpend() >=
                policy.mediumValueThreshold()
            ) {
                return ValueTier.MEDIUM_VALUE;
            }

            return ValueTier.LOW_VALUE;
        }

        public SegmentationResult evaluate(
            Customer customer,
            LocalDate evaluationDate
        ) {
            Objects.requireNonNull(customer);
            Objects.requireNonNull(evaluationDate);

            if (customer.lastPurchase().isAfter(evaluationDate)) {
                throw new SegmentationException(
                    "Purchase date cannot be in the future."
                );
            }

            int recency = Math.toIntExact(
                ChronoUnit.DAYS.between(
                    customer.lastPurchase(),
                    evaluationDate
                )
            );

            double averageOrderValue =
                customer.purchaseFrequency() == 0
                ? 0
                : customer.totalSpend() /
                    customer.purchaseFrequency();

            return new SegmentationResult(
                customer.id(),
                classifyDemographics(customer),
                classifyBehavior(customer, recency),
                classifyValue(customer),
                recency,
                customer.purchaseFrequency(),
                customer.totalSpend(),
                averageOrderValue,
                evaluationDate
            );
        }

        public List<SegmentationResult> evaluateBatch(
            List<Customer> customers,
            LocalDate evaluationDate
        ) {
            return customers.stream()
                .map(customer -> evaluate(customer, evaluationDate))
                .toList();
        }
    }

    static class CampaignRuleEngine {
        private final List<SegmentationRule> rules;

        public CampaignRuleEngine() {
            this.rules = List.of(
                new SegmentationRule() {
                    @Override
                    public boolean applies(
                        Customer customer,
                        SegmentationResult result
                    ) {
                        return customer.status() ==
                                CustomerStatus.ACTIVE &&
                            result.valueTier() == ValueTier.HIGH_VALUE;
                    }

                    @Override
                    public CampaignType campaign() {
                        return CampaignType.PREMIUM_RETENTION;
                    }

                    @Override
                    public String explanation() {
                        return "High monetary customer value.";
                    }
                },
                new SegmentationRule() {
                    @Override
                    public boolean applies(
                        Customer customer,
                        SegmentationResult result
                    ) {
                        return customer.status() ==
                                CustomerStatus.ACTIVE &&
                            result.behavioral() ==
                                BehavioralSegment.DIGITALLY_ENGAGED;
                    }

                    @Override
                    public CampaignType campaign() {
                        return CampaignType.DIGITAL_ENGAGEMENT;
                    }

                    @Override
                    public String explanation() {
                        return "High digital engagement.";
                    }
                },
                new SegmentationRule() {
                    @Override
                    public boolean applies(
                        Customer customer,
                        SegmentationResult result
                    ) {
                        return customer.status() ==
                                CustomerStatus.ACTIVE &&
                            result.behavioral() !=
                                BehavioralSegment.DORMANT;
                    }

                    @Override
                    public CampaignType campaign() {
                        return CampaignType.STANDARD_ENGAGEMENT;
                    }

                    @Override
                    public String explanation() {
                        return "Standard engagement eligibility.";
                    }
                }
            );
        }

        public CampaignDecision decide(
            Customer customer,
            SegmentationResult result
        ) {
            if (customer.status() != CustomerStatus.ACTIVE) {
                return new CampaignDecision(
                    customer.id(),
                    false,
                    null,
                    "Account is not active."
                );
            }

            if (
                result.behavioral() ==
                BehavioralSegment.DORMANT
            ) {
                return new CampaignDecision(
                    customer.id(),
                    false,
                    CampaignType.REACTIVATION,
                    "Separate reactivation policy required."
                );
            }

            for (SegmentationRule rule : rules) {
                if (rule.applies(customer, result)) {
                    return new CampaignDecision(
                        customer.id(),
                        true,
                        rule.campaign(),
                        rule.explanation()
                    );
                }
            }

            throw new PolicyViolationException(
                "No campaign policy matched the customer."
            );
        }
    }

    static class AnalyticsService {
        public SegmentReport generate(
            List<SegmentationResult> results
        ) {
            Map<String, Long> demographic = results.stream()
                .collect(
                    Collectors.groupingBy(
                        result -> result.demographic().segmentName(),
                        TreeMap::new,
                        Collectors.counting()
                    )
                );

            Map<BehavioralSegment, Long> behavioral =
                results.stream().collect(
                    Collectors.groupingBy(
                        SegmentationResult::behavioral,
                        () -> new EnumMap<>(BehavioralSegment.class),
                        Collectors.counting()
                    )
                );

            Map<ValueTier, Long> value =
                results.stream().collect(
                    Collectors.groupingBy(
                        SegmentationResult::valueTier,
                        () -> new EnumMap<>(ValueTier.class),
                        Collectors.counting()
                    )
                );

            double revenue = results.stream()
                .mapToDouble(SegmentationResult::monetaryValue)
                .sum();

            double average = results.isEmpty()
                ? 0
                : revenue / results.size();

            return new SegmentReport(
                results.size(),
                revenue,
                average,
                Collections.unmodifiableMap(demographic),
                Collections.unmodifiableMap(behavioral),
                Collections.unmodifiableMap(value)
            );
        }

        public Map<BehavioralSegment, Map<ValueTier, Long>>
        crossTabulate(List<SegmentationResult> results) {
            Map<BehavioralSegment, Map<ValueTier, Long>> matrix =
                new EnumMap<>(BehavioralSegment.class);

            for (SegmentationResult result : results) {
                matrix.computeIfAbsent(
                    result.behavioral(),
                    ignored -> new EnumMap<>(ValueTier.class)
                ).merge(result.valueTier(), 1L, Long::sum);
            }

            return matrix;
        }
    }

    static List<Customer> sampleCustomers(LocalDate today) {
        return List.of(
            new Customer(
                4001, "Customer A", 27, "Delhi",
                "Engineer", 1800000, 20, 165000,
                today.minusDays(5), 50, 20, 90,
                CustomerStatus.ACTIVE
            ),
            new Customer(
                4002, "Customer B", 39, "Mumbai",
                "Manager", 850000, 8, 65000,
                today.minusDays(25), 28, 12, 45,
                CustomerStatus.ACTIVE
            ),
            new Customer(
                4003, "Customer C", 55, "Lucknow",
                "Teacher", 450000, 3, 18000,
                today.minusDays(95), 8, 2, 12,
                CustomerStatus.ACTIVE
            ),
            new Customer(
                4004, "Customer D", 65, "Pune",
                "Consultant", 2200000, 22, 245000,
                today.minusDays(12), 75, 35, 120,
                CustomerStatus.ACTIVE
            ),
            new Customer(
                4005, "Customer E", 32, "Jaipur",
                "Analyst", 700000, 1, 2500,
                today.minusDays(250), 3, 0, 4,
                CustomerStatus.INACTIVE
            )
        );
    }

    static void runTests(
        SegmentationService service,
        LocalDate today
    ) {
        Customer customer = new Customer(
            4999, "Test Customer", 29, "Delhi",
            "Engineer", 1500000, 15, 125000,
            today.minusDays(10), 40, 15, 60,
            CustomerStatus.ACTIVE
        );

        SegmentationResult result =
            service.evaluate(customer, today);

        if (result.valueTier() != ValueTier.HIGH_VALUE) {
            throw new AssertionError("Value classification failed.");
        }

        if (
            result.behavioral() != BehavioralSegment.LOYAL_ACTIVE
        ) {
            throw new AssertionError("Behavioral classification failed.");
        }

        Customer zeroPurchase = new Customer(
            4998, "No Purchase", 30, "Pune",
            "Analyst", 400000, 0, 0,
            today.minusDays(5), 2, 0, 4,
            CustomerStatus.ACTIVE
        );

        if (
            service.evaluate(zeroPurchase, today)
                .averageOrderValue() != 0
        ) {
            throw new AssertionError("Zero purchase handling failed.");
        }

        System.out.println("All Java 17 tests passed.");
    }

    public static void main(String[] args) {
        LocalDate today = LocalDate.now();

        SegmentationPolicy policy =
            SegmentationPolicy.standard();

        CustomerRepository repository =
            new CustomerRepository();

        for (Customer customer : sampleCustomers(today)) {
            repository.add(customer);
        }

        SegmentationService service =
            new SegmentationService(policy);

        CampaignRuleEngine campaignEngine =
            new CampaignRuleEngine();

        AnalyticsService analytics =
            new AnalyticsService();

        runTests(service, today);

        List<Customer> customers = repository.findAll();

        List<SegmentationResult> results =
            service.evaluateBatch(customers, today);

        System.out.println("\nCUSTOMER SEGMENTATION REPORT");

        for (SegmentationResult result : results) {
            Customer customer = repository.find(result.customerId());

            CampaignDecision decision =
                campaignEngine.decide(customer, result);

            System.out.println("\nCustomer: " + customer.id());
            System.out.println(
                "Demographic: " +
                result.demographic().segmentName()
            );
            System.out.println(
                "Behavioral: " + result.behavioral()
            );
            System.out.println(
                "Value: " + result.valueTier()
            );
            System.out.println(
                "Recency: " + result.recencyDays()
            );
            System.out.println(
                "Frequency: " + result.frequency()
            );
            System.out.println(
                "Monetary value: Rs. " +
                result.monetaryValue()
            );
            System.out.println(
                "Average order value: Rs. " +
                result.averageOrderValue()
            );
            System.out.println(
                "Campaign eligible: " + decision.eligible()
            );
            System.out.println(
                "Campaign: " + decision.campaign()
            );
            System.out.println(
                "Decision reason: " + decision.reason()
            );
        }

        SegmentReport report = analytics.generate(results);

        System.out.println("\nENTERPRISE ANALYTICS");
        System.out.println("Customer count: " + report.customerCount());
        System.out.println("Revenue: Rs. " + report.totalRevenue());
        System.out.println("Average value: Rs. " + report.averageRevenue());

        System.out.println(
            "Demographic distribution: " +
            report.demographicDistribution()
        );

        System.out.println(
            "Behavioral distribution: " +
            report.behavioralDistribution()
        );

        System.out.println(
            "Value distribution: " +
            report.valueDistribution()
        );

        System.out.println("\nBEHAVIORAL-VALUE MATRIX");

        System.out.println(
            analytics.crossTabulate(results)
        );
    }
}
