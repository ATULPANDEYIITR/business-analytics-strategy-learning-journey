import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
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
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/*
 * RETENTION ANALYTICS
 *
 * Enterprise customer retention and loyalty management system.
 *
 * Java version: 17
 * Dependencies: Java standard library
 *
 * Enterprise capabilities:
 * - Immutable customer events
 * - Explicit customer state transitions
 * - Repository and service separation
 * - Configurable churn policies
 * - RFM segmentation
 * - Cohort analysis
 * - Loyalty rules
 * - Campaign eligibility and budgeting
 * - CLV estimation
 * - Retention performance reporting
 *
 * Compile:
 * javac RetentionAnalytics.java
 *
 * Run:
 * java RetentionAnalytics
 */

public class RetentionAnalytics {

    // ========================================================
    // 1. DOMAIN ENUMERATIONS
    // ========================================================

    enum CustomerStatus {
        ACTIVE,
        AT_RISK,
        CHURNED,
        REACTIVATED
    }

    enum EventType {
        PURCHASE,
        LOGIN,
        SUPPORT,
        EMAIL_OPEN,
        EMAIL_CLICK,
        SUBSCRIPTION,
        REFUND
    }

    enum LoyaltyTier {
        BRONZE,
        SILVER,
        GOLD,
        PLATINUM
    }

    enum RiskLevel {
        LOW,
        MEDIUM,
        HIGH
    }

    enum CampaignState {
        DRAFT,
        ACTIVE,
        PAUSED,
        COMPLETED
    }


    // ========================================================
    // 2. CUSTOM EXCEPTIONS
    // ========================================================

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static class NotFoundException extends DomainException {
        NotFoundException(String message) {
            super(message);
        }
    }

    static class ConflictException extends DomainException {
        ConflictException(String message) {
            super(message);
        }
    }

    static class ValidationException extends DomainException {
        ValidationException(String message) {
            super(message);
        }
    }


    // ========================================================
    // 3. DOMAIN VALIDATION
    // ========================================================

    static void requireNonBlank(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new ValidationException(field + " is required.");
        }
    }

    static void requireNonNegative(double value, String field) {
        if (!Double.isFinite(value) || value < 0) {
            throw new ValidationException("Invalid " + field);
        }
    }


    // ========================================================
    // 4. CUSTOMER DOMAIN
    // ========================================================

    static class Customer {

        private final String id;
        private final String name;
        private final String email;
        private final LocalDate acquisitionDate;
        private final String region;
        private final double monthlyRevenue;

        private CustomerStatus status;
        private LoyaltyTier tier;
        private int loyaltyPoints;

        Customer(
            String id,
            String name,
            String email,
            LocalDate acquisitionDate,
            String region,
            double monthlyRevenue
        ) {

            requireNonBlank(id, "Customer ID");
            requireNonBlank(name, "Customer name");
            requireNonBlank(email, "Email");
            requireNonBlank(region, "Region");
            requireNonNegative(monthlyRevenue, "Monthly revenue");

            if (!email.matches("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
                throw new ValidationException("Invalid email.");
            }

            this.id = id;
            this.name = name;
            this.email = email.toLowerCase();
            this.acquisitionDate = Objects.requireNonNull(
                acquisitionDate
            );

            this.region = region;
            this.monthlyRevenue = monthlyRevenue;

            this.status = CustomerStatus.ACTIVE;
            this.tier = LoyaltyTier.BRONZE;
            this.loyaltyPoints = 0;
        }

        String id() {
            return id;
        }

        String email() {
            return email;
        }

        CustomerStatus status() {
            return status;
        }

        LoyaltyTier tier() {
            return tier;
        }

        void updateTier(LoyaltyTier tier) {
            this.tier = Objects.requireNonNull(tier);
        }

        void awardPoints(int points) {
            if (points < 0) {
                throw new ValidationException("Negative points.");
            }

            this.loyaltyPoints = Math.addExact(
                loyaltyPoints,
                points
            );
        }

        int loyaltyPoints() {
            return loyaltyPoints;
        }

        void transition(CustomerStatus next) {

            Map<CustomerStatus, Set<CustomerStatus>> allowed =
                Map.of(
                    CustomerStatus.ACTIVE,
                    Set.of(
                        CustomerStatus.AT_RISK,
                        CustomerStatus.CHURNED
                    ),

                    CustomerStatus.AT_RISK,
                    Set.of(
                        CustomerStatus.ACTIVE,
                        CustomerStatus.CHURNED
                    ),

                    CustomerStatus.CHURNED,
                    Set.of(CustomerStatus.REACTIVATED),

                    CustomerStatus.REACTIVATED,
                    Set.of(
                        CustomerStatus.ACTIVE,
                        CustomerStatus.AT_RISK
                    )
                );

            if (!allowed.get(status).contains(next)) {
                throw new ConflictException(
                    "Invalid transition: " + status + " -> " + next
                );
            }

            status = next;
        }
    }


    // ========================================================
    // 5. IMMUTABLE CUSTOMER EVENTS
    // ========================================================

    record CustomerEvent(
        String id,
        String customerId,
        EventType type,
        LocalDateTime occurredAt,
        double amount,
        Map<String, String> metadata
    ) {

        CustomerEvent {

            requireNonBlank(id, "Event ID");
            requireNonBlank(customerId, "Customer ID");

            Objects.requireNonNull(type);
            Objects.requireNonNull(occurredAt);

            requireNonNegative(amount, "Amount");

            if (type != EventType.PURCHASE &&
                type != EventType.SUBSCRIPTION &&
                amount != 0) {

                throw new ValidationException(
                    "Monetary amount not supported by event type."
                );
            }

            metadata = metadata == null
                ? Map.of()
                : Collections.unmodifiableMap(
                    new HashMap<>(metadata)
                );
        }
    }


    // ========================================================
    // 6. CUSTOMER REPOSITORY
    // ========================================================

    static class CustomerRepository {

        private final Map<String, Customer> customers =
            new ConcurrentHashMap<>();

        private final Map<String, String> emailIndex =
            new ConcurrentHashMap<>();

        synchronized void add(Customer customer) {

            Objects.requireNonNull(customer);

            if (customers.containsKey(customer.id())) {
                throw new ConflictException("Duplicate customer ID.");
            }

            if (emailIndex.containsKey(customer.email())) {
                throw new ConflictException("Duplicate email.");
            }

            customers.put(customer.id(), customer);
            emailIndex.put(customer.email(), customer.id());
        }

        Customer get(String id) {

            Customer customer = customers.get(id);

            if (customer == null) {
                throw new NotFoundException(
                    "Customer not found: " + id
                );
            }

            return customer;
        }

        List<Customer> all() {
            return List.copyOf(customers.values());
        }
    }


    // ========================================================
    // 7. EVENT REPOSITORY
    // ========================================================

    static class EventRepository {

        private final CustomerRepository customerRepository;

        private final Map<String, CustomerEvent> events =
            new ConcurrentHashMap<>();

        private final Map<String, List<CustomerEvent>> byCustomer =
            new ConcurrentHashMap<>();

        EventRepository(CustomerRepository customerRepository) {
            this.customerRepository = customerRepository;
        }

        synchronized void record(CustomerEvent event) {

            customerRepository.get(event.customerId());

            if (events.containsKey(event.id())) {
                throw new ConflictException("Duplicate event ID.");
            }

            events.put(event.id(), event);

            byCustomer.computeIfAbsent(
                event.customerId(),
                key -> new ArrayList<>()
            ).add(event);
        }

        List<CustomerEvent> forCustomer(String customerId) {

            customerRepository.get(customerId);

            return byCustomer.getOrDefault(
                customerId,
                List.of()
            ).stream()
                .sorted((a, b) ->
                    a.occurredAt().compareTo(b.occurredAt())
                )
                .toList();
        }

        List<CustomerEvent> all() {
            return List.copyOf(events.values());
        }
    }


    // ========================================================
    // 8. RFM DOMAIN
    // ========================================================

    record RFMResult(
        int recencyDays,
        int frequency,
        double monetary,
        double score,
        String segment
    ) {}

    static class RFMService {

        RFMResult evaluate(
            Customer customer,
            List<CustomerEvent> events,
            LocalDate referenceDate
        ) {

            List<CustomerEvent> purchases = events.stream()
                .filter(event ->
                    event.type() == EventType.PURCHASE
                )
                .filter(event ->
                    !event.occurredAt().toLocalDate()
                        .isAfter(referenceDate)
                )
                .toList();

            LocalDate lastPurchase = purchases.stream()
                .map(event -> event.occurredAt().toLocalDate())
                .max(LocalDate::compareTo)
                .orElse(customer.acquisitionDate);

            int recency = (int) ChronoUnit.DAYS.between(
                lastPurchase,
                referenceDate
            );

            int frequency = purchases.size();

            double monetary = purchases.stream()
                .mapToDouble(CustomerEvent::amount)
                .sum();

            double recencyScore = Math.max(
                0,
                1 - Math.min(recency, 180) / 180.0
            );

            double frequencyScore = Math.min(
                frequency / 12.0,
                1
            );

            double monetaryScore = Math.min(
                monetary / 12000.0,
                1
            );

            double score = (
                recencyScore * 0.40 +
                frequencyScore * 0.30 +
                monetaryScore * 0.30
            ) * 100;

            String segment;

            if (frequency == 0) {
                segment = "NON_PURCHASING";
            } else if (recency <= 30 && score >= 65) {
                segment = "CHAMPIONS";
            } else if (recency <= 60) {
                segment = "LOYAL";
            } else if (recency <= 90) {
                segment = "AT_RISK";
            } else {
                segment = "HIBERNATING";
            }

            return new RFMResult(
                recency,
                frequency,
                monetary,
                score,
                segment
            );
        }
    }


    // ========================================================
    // 9. CHURN POLICY OBJECT
    // ========================================================

    record ChurnPolicy(
        double mediumThreshold,
        double highThreshold,
        int purchaseInactivityThreshold,
        int engagementInactivityThreshold
    ) {

        ChurnPolicy {

            if (
                mediumThreshold < 0 ||
                highThreshold > 1 ||
                mediumThreshold >= highThreshold ||
                purchaseInactivityThreshold <= 0 ||
                engagementInactivityThreshold <= 0
            ) {
                throw new ValidationException(
                    "Invalid churn policy."
                );
            }
        }

        static ChurnPolicy standard() {
            return new ChurnPolicy(0.35, 0.60, 30, 45);
        }
    }


    // ========================================================
    // 10. CHURN ASSESSMENT
    // ========================================================

    record ChurnAssessment(
        String customerId,
        double probability,
        RiskLevel riskLevel,
        List<String> factors,
        LocalDateTime assessedAt
    ) {

        ChurnAssessment {
            factors = List.copyOf(factors);
        }
    }

    static class ChurnService {

        private final ChurnPolicy policy;

        ChurnService(ChurnPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        ChurnAssessment evaluate(
            Customer customer,
            List<CustomerEvent> events,
            LocalDate referenceDate
        ) {

            List<CustomerEvent> purchases = events.stream()
                .filter(event ->
                    event.type() == EventType.PURCHASE
                )
                .filter(event ->
                    !event.occurredAt().toLocalDate()
                        .isAfter(referenceDate)
                )
                .toList();

            LocalDate lastPurchase = purchases.stream()
                .map(event -> event.occurredAt().toLocalDate())
                .max(LocalDate::compareTo)
                .orElse(customer.acquisitionDate);

            LocalDate lastActivity = events.stream()
                .filter(event ->
                    !event.occurredAt().toLocalDate()
                        .isAfter(referenceDate)
                )
                .map(event -> event.occurredAt().toLocalDate())
                .max(LocalDate::compareTo)
                .orElse(customer.acquisitionDate);

            long purchaseInactivity = ChronoUnit.DAYS.between(
                lastPurchase,
                referenceDate
            );

            long generalInactivity = ChronoUnit.DAYS.between(
                lastActivity,
                referenceDate
            );

            double risk = 0.05;

            List<String> factors = new ArrayList<>();

            if (purchaseInactivity > 30) {
                risk += 0.20;
                factors.add("Purchase inactivity above 30 days");
            }

            if (purchaseInactivity > 60) {
                risk += 0.20;
                factors.add("Purchase inactivity above 60 days");
            }

            if (purchaseInactivity > 90) {
                risk += 0.20;
                factors.add("Purchase inactivity above 90 days");
            }

            if (
                generalInactivity >
                policy.engagementInactivityThreshold()
            ) {
                risk += 0.15;
                factors.add("Low engagement");
            }

            if (purchases.isEmpty()) {
                risk += 0.15;
                factors.add("No purchase history");
            }

            long supportCount = events.stream()
                .filter(event ->
                    event.type() == EventType.SUPPORT
                )
                .filter(event ->
                    ChronoUnit.DAYS.between(
                        event.occurredAt().toLocalDate(),
                        referenceDate
                    ) <= 30
                )
                .count();

            if (supportCount >= 3) {
                risk += 0.10;
                factors.add("Repeated support interactions");
            }

            risk = Math.min(0.99, risk);

            RiskLevel level =
                risk >= policy.highThreshold()
                    ? RiskLevel.HIGH
                    : risk >= policy.mediumThreshold()
                        ? RiskLevel.MEDIUM
                        : RiskLevel.LOW;

            return new ChurnAssessment(
                customer.id(),
                risk,
                level,
                factors,
                LocalDateTime.now()
            );
        }
    }


    // ========================================================
    // 11. LOYALTY POLICY
    // ========================================================

    static class LoyaltyPolicy {

        private final Map<LoyaltyTier, Double> thresholds;
        private final Map<LoyaltyTier, Double> multipliers;

        LoyaltyPolicy() {

            thresholds = new EnumMap<>(LoyaltyTier.class);
            multipliers = new EnumMap<>(LoyaltyTier.class);

            thresholds.put(LoyaltyTier.BRONZE, 0.0);
            thresholds.put(LoyaltyTier.SILVER, 2000.0);
            thresholds.put(LoyaltyTier.GOLD, 5000.0);
            thresholds.put(LoyaltyTier.PLATINUM, 10000.0);

            multipliers.put(LoyaltyTier.BRONZE, 1.0);
            multipliers.put(LoyaltyTier.SILVER, 1.25);
            multipliers.put(LoyaltyTier.GOLD, 1.5);
            multipliers.put(LoyaltyTier.PLATINUM, 2.0);
        }

        LoyaltyTier determine(double spend) {

            requireNonNegative(spend, "Lifetime spend");

            if (spend >= thresholds.get(LoyaltyTier.PLATINUM)) {
                return LoyaltyTier.PLATINUM;
            }

            if (spend >= thresholds.get(LoyaltyTier.GOLD)) {
                return LoyaltyTier.GOLD;
            }

            if (spend >= thresholds.get(LoyaltyTier.SILVER)) {
                return LoyaltyTier.SILVER;
            }

            return LoyaltyTier.BRONZE;
        }

        double multiplier(LoyaltyTier tier) {
            return multipliers.get(tier);
        }
    }


    // ========================================================
    // 12. LOYALTY SERVICE
    // ========================================================

    static class LoyaltyService {

        private final LoyaltyPolicy policy;

        LoyaltyService(LoyaltyPolicy policy) {
            this.policy = policy;
        }

        double lifetimeSpend(List<CustomerEvent> events) {
            return events.stream()
                .filter(event ->
                    event.type() == EventType.PURCHASE
                )
                .mapToDouble(CustomerEvent::amount)
                .sum();
        }

        LoyaltyTier update(
            Customer customer,
            List<CustomerEvent> events
        ) {

            LoyaltyTier tier = policy.determine(
                lifetimeSpend(events)
            );

            customer.updateTier(tier);

            return tier;
        }

        int award(
            Customer customer,
            double purchaseAmount,
            List<CustomerEvent> previousEvents
        ) {

            requireNonNegative(purchaseAmount, "Purchase amount");

            LoyaltyTier tier = policy.determine(
                lifetimeSpend(previousEvents)
            );

            int points = (int) Math.floor(
                purchaseAmount * policy.multiplier(tier)
            );

            customer.awardPoints(points);

            return points;
        }
    }


    // ========================================================
    // 13. COHORT ANALYTICS
    // ========================================================

    static class CohortService {

        Map<String, Map<Integer, Double>> calculate(
            List<Customer> customers,
            List<CustomerEvent> events
        ) {

            Map<String, Set<String>> cohorts = new HashMap<>();

            Map<String, Set<String>> active = new HashMap<>();

            Map<String, Customer> index = customers.stream()
                .collect(Collectors.toMap(
                    Customer::id,
                    customer -> customer
                ));

            for (Customer customer : customers) {

                String cohort = String.format(
                    "%04d-%02d",
                    customer.acquisitionDate.getYear(),
                    customer.acquisitionDate.getMonthValue()
                );

                cohorts.computeIfAbsent(
                    cohort,
                    key -> new HashSet<>()
                ).add(customer.id());
            }

            for (CustomerEvent event : events) {

                if (
                    event.type() != EventType.PURCHASE &&
                    event.type() != EventType.LOGIN
                ) {
                    continue;
                }

                Customer customer = index.get(event.customerId());

                if (customer == null) continue;

                LocalDate acquisition = customer.acquisitionDate;
                LocalDate activity = event.occurredAt().toLocalDate();

                if (activity.isBefore(acquisition)) continue;

                long period = ChronoUnit.MONTHS.between(
                    acquisition.withDayOfMonth(1),
                    activity.withDayOfMonth(1)
                );

                String cohort = String.format(
                    "%04d-%02d",
                    acquisition.getYear(),
                    acquisition.getMonthValue()
                );

                String key = cohort + ":" + period;

                active.computeIfAbsent(
                    key,
                    ignored -> new HashSet<>()
                ).add(customer.id());
            }

            Map<String, Map<Integer, Double>> output =
                new HashMap<>();

            for (var cohort : cohorts.entrySet()) {

                Map<Integer, Double> periods = new HashMap<>();

                for (var entry : active.entrySet()) {

                    String prefix = cohort.getKey() + ":";

                    if (!entry.getKey().startsWith(prefix)) {
                        continue;
                    }

                    int period = Integer.parseInt(
                        entry.getKey().substring(prefix.length())
                    );

                    double retention =
                        entry.getValue().size()
                        * 100.0 / cohort.getValue().size();

                    periods.put(period, retention);
                }

                output.put(cohort.getKey(), periods);
            }

            return output;
        }
    }


    // ========================================================
    // 14. CAMPAIGN POLICY AND STATE MANAGEMENT
    // ========================================================

    static class Campaign {

        private final String id;
        private final String name;
        private final double budget;
        private final double contactCost;
        private final CustomerStatus targetStatus;

        private CampaignState state = CampaignState.DRAFT;

        private final Set<String> assigned = new HashSet<>();
        private final Set<String> conversions = new HashSet<>();

        Campaign(
            String id,
            String name,
            double budget,
            double contactCost,
            CustomerStatus targetStatus
        ) {

            requireNonBlank(id, "Campaign ID");
            requireNonBlank(name, "Campaign name");

            requireNonNegative(budget, "Budget");
            requireNonNegative(contactCost, "Contact cost");

            this.id = id;
            this.name = name;
            this.budget = budget;
            this.contactCost = contactCost;
            this.targetStatus = targetStatus;
        }

        void activate() {

            if (state != CampaignState.DRAFT) {
                throw new ConflictException(
                    "Campaign cannot be activated."
                );
            }

            state = CampaignState.ACTIVE;
        }

        void pause() {

            if (state != CampaignState.ACTIVE) {
                throw new ConflictException(
                    "Campaign is not active."
                );
            }

            state = CampaignState.PAUSED;
        }

        void assign(Customer customer) {

            if (state != CampaignState.ACTIVE) {
                throw new ConflictException(
                    "Campaign is not active."
                );
            }

            if (customer.status() != targetStatus) {
                throw new ConflictException(
                    "Customer is not eligible."
                );
            }

            if (assigned.contains(customer.id())) {
                throw new ConflictException(
                    "Duplicate campaign assignment."
                );
            }

            double projectedCost =
                (assigned.size() + 1) * contactCost;

            if (projectedCost > budget) {
                throw new ConflictException(
                    "Campaign budget exceeded."
                );
            }

            assigned.add(customer.id());
        }

        void convert(String customerId) {

            if (!assigned.contains(customerId)) {
                throw new ConflictException(
                    "Customer was not assigned."
                );
            }

            conversions.add(customerId);
        }

        Map<String, Double> report(double revenuePerConversion) {

            requireNonNegative(
                revenuePerConversion,
                "Revenue per conversion"
            );

            double cost = assigned.size() * contactCost;
            double revenue = conversions.size()
                * revenuePerConversion;

            double rate = assigned.isEmpty()
                ? 0
                : conversions.size() * 100.0 / assigned.size();

            double roi = cost == 0
                ? 0
                : (revenue - cost) / cost * 100;

            Map<String, Double> result = new HashMap<>();

            result.put("contacted", (double) assigned.size());
            result.put("converted", (double) conversions.size());
            result.put("conversion_rate", rate);
            result.put("cost", cost);
            result.put("revenue", revenue);
            result.put("roi", roi);

            return Map.copyOf(result);
        }
    }


    // ========================================================
    // 15. ENTERPRISE RETENTION SERVICE
    // ========================================================

    static class RetentionService {

        private final CustomerRepository customers =
            new CustomerRepository();

        private final EventRepository events =
            new EventRepository(customers);

        private final RFMService rfm = new RFMService();

        private final ChurnService churn =
            new ChurnService(ChurnPolicy.standard());

        private final LoyaltyService loyalty =
            new LoyaltyService(new LoyaltyPolicy());

        private final CohortService cohorts =
            new CohortService();

        void addCustomer(Customer customer) {
            customers.add(customer);
        }

        void recordEvent(CustomerEvent event) {
            events.record(event);
        }

        record CustomerAnalysis(
            String customerId,
            CustomerStatus status,
            RFMResult rfm,
            ChurnAssessment churn,
            LoyaltyTier loyaltyTier
        ) {}

        CustomerAnalysis analyze(
            String customerId,
            LocalDate referenceDate
        ) {

            Customer customer = customers.get(customerId);

            List<CustomerEvent> history =
                events.forCustomer(customerId);

            RFMResult rfmResult = rfm.evaluate(
                customer,
                history,
                referenceDate
            );

            ChurnAssessment churnResult = churn.evaluate(
                customer,
                history,
                referenceDate
            );

            LoyaltyTier tier = loyalty.update(
                customer,
                history
            );

            if (churnResult.riskLevel() == RiskLevel.HIGH) {

                if (customer.status() == CustomerStatus.ACTIVE) {
                    customer.transition(CustomerStatus.AT_RISK);
                }

            } else if (
                churnResult.riskLevel() == RiskLevel.LOW &&
                customer.status() == CustomerStatus.AT_RISK
            ) {
                customer.transition(CustomerStatus.ACTIVE);
            }

            return new CustomerAnalysis(
                customerId,
                customer.status(),
                rfmResult,
                churnResult,
                tier
            );
        }

        List<CustomerAnalysis> analyzeAll(
            LocalDate referenceDate
        ) {

            return customers.all().stream()
                .map(customer ->
                    analyze(customer.id(), referenceDate)
                )
                .toList();
        }

        Map<String, Map<Integer, Double>> cohortReport() {
            return cohorts.calculate(
                customers.all(),
                events.all()
            );
        }

        CustomerRepository customerRepository() {
            return customers;
        }
    }


    // ========================================================
    // 16. CLV SERVICE
    // ========================================================

    static double calculateCLV(
        double monthlyRevenue,
        double grossMargin,
        double monthlyChurn
    ) {

        requireNonNegative(monthlyRevenue, "Revenue");

        if (grossMargin < 0 || grossMargin > 1) {
            throw new ValidationException("Invalid gross margin.");
        }

        if (monthlyChurn <= 0 || monthlyChurn > 1) {
            throw new ValidationException("Invalid churn rate.");
        }

        return monthlyRevenue * grossMargin / monthlyChurn;
    }


    // ========================================================
    // 17. SAMPLE EVENT FACTORY
    // ========================================================

    static CustomerEvent event(
        String id,
        String customerId,
        EventType type,
        int daysAgo,
        double amount,
        LocalDate referenceDate
    ) {

        LocalDateTime occurredAt = referenceDate
            .minusDays(daysAgo)
            .atStartOfDay();

        return new CustomerEvent(
            id,
            customerId,
            type,
            occurredAt,
            amount,
            Map.of()
        );
    }


    // ========================================================
    // 18. VALIDATION TESTS
    // ========================================================

    static void runTests() {

        if (Math.abs(
            calculateCLV(1000, 0.70, 0.05) - 14000
        ) > 0.001) {
            throw new AssertionError("CLV test failed.");
        }

        LoyaltyPolicy loyalty = new LoyaltyPolicy();

        if (
            loyalty.determine(12000) !=
            LoyaltyTier.PLATINUM
        ) {
            throw new AssertionError("Loyalty test failed.");
        }

        if (
            loyalty.determine(3000) !=
            LoyaltyTier.SILVER
        ) {
            throw new AssertionError("Tier test failed.");
        }

        try {
            calculateCLV(1000, 0.70, 0);
            throw new AssertionError(
                "Invalid churn rate was accepted."
            );
        } catch (ValidationException expected) {
            // Expected validation behavior.
        }

        System.out.println("All tests passed.");
    }


    // ========================================================
    // 19. MAIN ENTERPRISE WORKFLOW
    // ========================================================

    public static void main(String[] args) {

        runTests();

        LocalDate referenceDate = LocalDate.of(
            2026, 11, 27
        );

        RetentionService service = new RetentionService();

        List<Customer> sampleCustomers = List.of(
            new Customer(
                "C001", "Aarav Sharma", "aarav@example.com",
                LocalDate.of(2026, 1, 10), "North", 999
            ),
            new Customer(
                "C002", "Priya Verma", "priya@example.com",
                LocalDate.of(2026, 2, 15), "South", 1499
            ),
            new Customer(
                "C003", "Rahul Singh", "rahul@example.com",
                LocalDate.of(2026, 3, 20), "West", 799
            ),
            new Customer(
                "C004", "Ananya Gupta", "ananya@example.com",
                LocalDate.of(2026, 4, 5), "East", 1999
            )
        );

        sampleCustomers.forEach(service::addCustomer);

        List<CustomerEvent> sampleEvents = List.of(
            event("E001", "C001", EventType.PURCHASE, 5, 3000, referenceDate),
            event("E002", "C001", EventType.PURCHASE, 35, 2500, referenceDate),
            event("E003", "C001", EventType.LOGIN, 1, 0, referenceDate),
            event("E004", "C002", EventType.PURCHASE, 15, 1500, referenceDate),
            event("E005", "C002", EventType.LOGIN, 2, 0, referenceDate),
            event("E006", "C003", EventType.PURCHASE, 110, 700, referenceDate),
            event("E007", "C004", EventType.PURCHASE, 80, 8000, referenceDate),
            event("E008", "C004", EventType.SUPPORT, 10, 0, referenceDate),
            event("E009", "C004", EventType.SUPPORT, 8, 0, referenceDate),
            event("E010", "C004", EventType.SUPPORT, 5, 0, referenceDate)
        );

        sampleEvents.forEach(service::recordEvent);

        List<RetentionService.CustomerAnalysis> analyses =
            service.analyzeAll(referenceDate);

        System.out.println("\nCUSTOMER RETENTION REPORT");
        System.out.println("================================");

        analyses.forEach(analysis -> {

            System.out.println("\nCustomer: " + analysis.customerId());
            System.out.println("Status: " + analysis.status());

            System.out.println(
                "Churn probability: " +
                analysis.churn().probability()
            );

            System.out.println(
                "Risk level: " +
                analysis.churn().riskLevel()
            );

            System.out.println(
                "RFM segment: " +
                analysis.rfm().segment()
            );

            System.out.println(
                "RFM score: " +
                analysis.rfm().score()
            );

            System.out.println(
                "Loyalty tier: " +
                analysis.loyaltyTier()
            );
        });

        System.out.println("\nCOHORT RETENTION");

        service.cohortReport().forEach((cohort, periods) -> {
            System.out.println(cohort + " -> " + periods);
        });

        Campaign campaign = new Campaign(
            "CMP001",
            "November Reactivation",
            1000,
            50,
            CustomerStatus.AT_RISK
        );

        campaign.activate();

        for (Customer customer :
            service.customerRepository().all()) {

            if (customer.status() == CustomerStatus.AT_RISK) {
                campaign.assign(customer);
            }
        }

        campaign.assignments.stream().findFirst().ifPresent(
            campaign::convert
        );

        System.out.println("\nCAMPAIGN PERFORMANCE");
        System.out.println(campaign.report(1500));

        System.out.println("\nCUSTOMER LIFETIME VALUE");
        System.out.println(
            calculateCLV(1500, 0.65, 0.04)
        );
    }
}
