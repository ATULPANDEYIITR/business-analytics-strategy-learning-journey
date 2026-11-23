import java.util.*;
import java.util.stream.Collectors;

/**
 * Customer Lifetime Value enterprise management system.
 *
 * Java 17
 *
 * Includes customer accounting, predictive CLV, acquisition economics,
 * customer segmentation, retention decisions, channel analytics,
 * policy validation and portfolio reporting.
 */

public class CustomerLifetimeValue {

    enum CustomerStatus {
        ACTIVE,
        AT_RISK,
        CHURNED
    }

    enum CustomerSegment {
        HIGH_VALUE,
        GROWING,
        STANDARD,
        LOW_VALUE,
        UNPROFITABLE
    }

    enum Confidence {
        LOW,
        MEDIUM,
        HIGH
    }

    enum DecisionType {
        PREMIUM_RETENTION,
        CROSS_SELL,
        ENGAGEMENT,
        ACQUISITION_REVIEW,
        CHURN_INTERVENTION,
        DATA_COLLECTION
    }

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static class Validation {

        static double nonNegative(double value, String field) {
            if (!Double.isFinite(value) || value < 0) {
                throw new DomainException(
                    field + " must be finite and non-negative."
                );
            }

            return value;
        }

        static void probability(double value, String field) {
            if (
                !Double.isFinite(value) ||
                value < 0 ||
                value > 1
            ) {
                throw new DomainException(
                    field + " must be between zero and one."
                );
            }
        }
    }

    record Transaction(
        String id,
        double revenue,
        double variableCost,
        double acquisitionCost
    ) {
        Transaction {
            if (id == null || id.isBlank()) {
                throw new DomainException(
                    "Transaction ID is required."
                );
            }

            Validation.nonNegative(revenue, "Revenue");
            Validation.nonNegative(variableCost, "Variable cost");
            Validation.nonNegative(
                acquisitionCost,
                "Acquisition cost"
            );

            if (variableCost > revenue) {
                throw new DomainException(
                    "Variable cost exceeds revenue."
                );
            }
        }

        double contribution() {
            return revenue - variableCost;
        }
    }

    static final class Customer {

        private final String id;
        private final String acquisitionChannel;
        private final List<Transaction> transactions =
            new ArrayList<>();

        private final Set<String> transactionIds =
            new HashSet<>();

        private CustomerStatus status = CustomerStatus.ACTIVE;

        Customer(String id, String acquisitionChannel) {
            if (
                id == null || id.isBlank() ||
                acquisitionChannel == null ||
                acquisitionChannel.isBlank()
            ) {
                throw new DomainException(
                    "Customer identity and channel are required."
                );
            }

            this.id = id;
            this.acquisitionChannel = acquisitionChannel;
        }

        synchronized void addTransaction(Transaction transaction) {
            if (!transactionIds.add(transaction.id())) {
                throw new DomainException(
                    "Duplicate transaction."
                );
            }

            transactions.add(transaction);
        }

        String id() {
            return id;
        }

        String channel() {
            return acquisitionChannel;
        }

        synchronized List<Transaction> transactions() {
            return List.copyOf(transactions);
        }

        synchronized double revenue() {
            return transactions.stream()
                .mapToDouble(Transaction::revenue)
                .sum();
        }

        synchronized double contribution() {
            return transactions.stream()
                .mapToDouble(Transaction::contribution)
                .sum();
        }

        synchronized double acquisitionCost() {
            return transactions.stream()
                .mapToDouble(Transaction::acquisitionCost)
                .sum();
        }

        synchronized int orderCount() {
            return transactions.size();
        }

        synchronized double averageOrderValue() {
            return transactions.isEmpty()
                ? 0
                : revenue() / transactions.size();
        }

        synchronized double annualPurchaseFrequency() {
            if (transactions.size() < 2) {
                return 0;
            }

            // The demo uses a one-year observation period.
            return transactions.size();
        }

        synchronized CustomerStatus status() {
            return status;
        }

        synchronized void updateStatus(CustomerStatus newStatus) {
            Objects.requireNonNull(newStatus);
            status = newStatus;
        }
    }

    record CLVPolicy(
        double annualChurnRate,
        double annualDiscountRate,
        double defaultGrossMargin,
        double maximumLifetime
    ) {
        CLVPolicy {
            Validation.probability(
                annualChurnRate,
                "Annual churn rate"
            );

            if (annualChurnRate == 0) {
                throw new DomainException(
                    "Churn rate must be greater than zero."
                );
            }

            if (
                !Double.isFinite(annualDiscountRate) ||
                annualDiscountRate < 0 ||
                annualDiscountRate >= 1
            ) {
                throw new DomainException(
                    "Invalid discount rate."
                );
            }

            Validation.probability(
                defaultGrossMargin,
                "Gross margin"
            );

            if (
                !Double.isFinite(maximumLifetime) ||
                maximumLifetime <= 0
            ) {
                throw new DomainException(
                    "Maximum lifetime must be positive."
                );
            }
        }
    }

    record Valuation(
        String customerId,
        double historicalRevenue,
        double historicalContribution,
        double acquisitionCost,
        double grossMargin,
        double projectedCLV,
        double netCLV,
        double expectedLifetime,
        CustomerSegment segment,
        Confidence confidence
    ) {}

    static final class CLVService {

        private final CLVPolicy policy;

        CLVService(CLVPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        private CustomerSegment classify(double netCLV) {
            if (netCLV < 0) {
                return CustomerSegment.UNPROFITABLE;
            }

            if (netCLV >= 10000) {
                return CustomerSegment.HIGH_VALUE;
            }

            if (netCLV >= 5000) {
                return CustomerSegment.GROWING;
            }

            if (netCLV >= 1000) {
                return CustomerSegment.STANDARD;
            }

            return CustomerSegment.LOW_VALUE;
        }

        Valuation calculate(Customer customer) {
            Objects.requireNonNull(customer);

            double revenue = customer.revenue();
            double contribution = customer.contribution();
            double acquisition = customer.acquisitionCost();

            double margin = revenue > 0
                ? contribution / revenue
                : policy.defaultGrossMargin();

            double annualRevenue =
                customer.averageOrderValue() *
                customer.annualPurchaseFrequency();

            double annualContribution =
                annualRevenue * margin;

            double lifetime = Math.min(
                policy.maximumLifetime(),
                1.0 / policy.annualChurnRate()
            );

            double projected;

            if (policy.annualDiscountRate() == 0) {
                projected = annualContribution * lifetime;
            } else {
                projected =
                    annualContribution *
                    (
                        1 - Math.pow(
                            1 + policy.annualDiscountRate(),
                            -lifetime
                        )
                    ) /
                    policy.annualDiscountRate();
            }

            double netCLV = projected - acquisition;

            Confidence confidence =
                customer.orderCount() >= 5
                    ? Confidence.HIGH
                    : customer.orderCount() >= 2
                        ? Confidence.MEDIUM
                        : Confidence.LOW;

            return new Valuation(
                customer.id(),
                revenue,
                contribution,
                acquisition,
                margin,
                projected,
                netCLV,
                lifetime,
                classify(netCLV),
                confidence
            );
        }
    }

    record AcquisitionMetrics(
        double marketingSpend,
        int acquiredCustomers,
        double averageCLV
    ) {
        AcquisitionMetrics {
            Validation.nonNegative(marketingSpend, "Marketing spend");
            Validation.nonNegative(averageCLV, "Average CLV");

            if (acquiredCustomers <= 0) {
                throw new DomainException(
                    "Acquired customers must be positive."
                );
            }
        }

        double customerAcquisitionCost() {
            return marketingSpend / acquiredCustomers;
        }

        double clvToCacRatio() {
            double cac = customerAcquisitionCost();

            return cac == 0
                ? Double.POSITIVE_INFINITY
                : averageCLV / cac;
        }

        String assessment() {
            double ratio = clvToCacRatio();

            if (ratio >= 3) return "HEALTHY";
            if (ratio >= 1) return "REVIEW";
            return "UNSUSTAINABLE";
        }
    }

    record StrategicDecision(
        String customerId,
        List<DecisionType> decisions
    ) {
        StrategicDecision {
            decisions = List.copyOf(decisions);
        }
    }

    static final class StrategyService {

        StrategicDecision evaluate(
            Valuation valuation,
            double churnRisk
        ) {
            Validation.probability(churnRisk, "Churn risk");

            List<DecisionType> decisions = new ArrayList<>();

            switch (valuation.segment()) {
                case HIGH_VALUE ->
                    decisions.add(
                        DecisionType.PREMIUM_RETENTION
                    );

                case GROWING ->
                    decisions.add(
                        DecisionType.CROSS_SELL
                    );

                case STANDARD, LOW_VALUE ->
                    decisions.add(
                        DecisionType.ENGAGEMENT
                    );

                case UNPROFITABLE ->
                    decisions.add(
                        DecisionType.ACQUISITION_REVIEW
                    );
            }

            if (churnRisk >= 0.70) {
                decisions.add(
                    DecisionType.CHURN_INTERVENTION
                );
            }

            if (valuation.confidence() == Confidence.LOW) {
                decisions.add(
                    DecisionType.DATA_COLLECTION
                );
            }

            return new StrategicDecision(
                valuation.customerId(),
                decisions
            );
        }
    }

    static final class CustomerRepository {

        private final Map<String, Customer> customers =
            new LinkedHashMap<>();

        synchronized void add(Customer customer) {
            if (customers.putIfAbsent(
                customer.id(),
                customer
            ) != null) {
                throw new DomainException(
                    "Customer already exists."
                );
            }
        }

        synchronized Customer find(String id) {
            Customer customer = customers.get(id);

            if (customer == null) {
                throw new DomainException(
                    "Customer not found."
                );
            }

            return customer;
        }

        synchronized List<Customer> all() {
            return List.copyOf(customers.values());
        }

        synchronized int size() {
            return customers.size();
        }
    }

    static final class PortfolioService {

        private final CustomerRepository repository;
        private final CLVService clvService;

        PortfolioService(
            CustomerRepository repository,
            CLVService clvService
        ) {
            this.repository = repository;
            this.clvService = clvService;
        }

        List<Valuation> evaluatePortfolio() {
            return repository.all()
                .stream()
                .map(clvService::calculate)
                .toList();
        }

        Map<String, Double> averageCLVByChannel() {
            return evaluatePortfolio()
                .stream()
                .collect(
                    Collectors.groupingBy(
                        valuation -> repository
                            .find(valuation.customerId())
                            .channel(),
                        Collectors.averagingDouble(
                            Valuation::netCLV
                        )
                    )
                );
        }

        double portfolioValue() {
            return evaluatePortfolio()
                .stream()
                .mapToDouble(Valuation::netCLV)
                .sum();
        }
    }

    static void runTests() {
        CLVService service = new CLVService(
            new CLVPolicy(0.20, 0.10, 0.60, 10)
        );

        Customer customer = new Customer(
            "TEST",
            "organic"
        );

        customer.addTransaction(
            new Transaction("T1", 1000, 400, 200)
        );

        customer.addTransaction(
            new Transaction("T2", 2000, 800, 0)
        );

        Valuation result = service.calculate(customer);

        if (result.historicalRevenue() != 3000) {
            throw new AssertionError("Revenue calculation failed.");
        }

        if (result.historicalContribution() != 1800) {
            throw new AssertionError("Contribution calculation failed.");
        }

        if (result.netCLV() <= 0) {
            throw new AssertionError("Net CLV calculation failed.");
        }

        boolean duplicateRejected = false;

        try {
            customer.addTransaction(
                new Transaction("T1", 100, 20, 0)
            );
        } catch (DomainException exception) {
            duplicateRejected = true;
        }

        if (!duplicateRejected) {
            throw new AssertionError("Duplicate transaction accepted.");
        }

        System.out.println("All Java tests passed.");
    }

    private static Customer createCustomer(
        String id,
        String channel,
        Transaction... transactions
    ) {
        Customer customer = new Customer(id, channel);

        for (Transaction transaction : transactions) {
            customer.addTransaction(transaction);
        }

        return customer;
    }

    public static void main(String[] args) {

        runTests();

        CLVPolicy policy = new CLVPolicy(
            0.20,
            0.10,
            0.60,
            10
        );

        CLVService clvService = new CLVService(policy);

        CustomerRepository repository =
            new CustomerRepository();

        repository.add(createCustomer(
            "C001",
            "organic",
            new Transaction("T001", 5000, 1800, 500),
            new Transaction("T002", 6500, 2200, 0),
            new Transaction("T003", 7000, 2500, 0),
            new Transaction("T004", 8000, 2800, 0)
        ));

        repository.add(createCustomer(
            "C002",
            "paid_search",
            new Transaction("T005", 1500, 900, 2000),
            new Transaction("T006", 1800, 1000, 0),
            new Transaction("T007", 2000, 1100, 0)
        ));

        repository.add(createCustomer(
            "C003",
            "referral",
            new Transaction("T008", 3000, 1200, 300),
            new Transaction("T009", 4000, 1500, 0),
            new Transaction("T010", 5000, 1800, 0)
        ));

        repository.add(createCustomer(
            "C004",
            "paid_social",
            new Transaction("T011", 700, 500, 2500),
            new Transaction("T012", 800, 600, 0)
        ));

        PortfolioService portfolio = new PortfolioService(
            repository,
            clvService
        );

        StrategyService strategy = new StrategyService();

        System.out.println("\nCUSTOMER LIFETIME VALUE");

        for (Valuation valuation : portfolio.evaluatePortfolio()) {
            System.out.printf(
                Locale.US,
                "%s | Revenue: %.2f | Contribution: %.2f | " +
                "Projected CLV: %.2f | Net CLV: %.2f | Segment: %s%n",
                valuation.customerId(),
                valuation.historicalRevenue(),
                valuation.historicalContribution(),
                valuation.projectedCLV(),
                valuation.netCLV(),
                valuation.segment()
            );

            StrategicDecision decision = strategy.evaluate(
                valuation,
                0.65
            );

            System.out.println(
                "  Decisions: " + decision.decisions()
            );
        }

        System.out.println("\nCHANNEL PERFORMANCE");

        portfolio.averageCLVByChannel().forEach(
            (channel, average) ->
                System.out.printf(
                    "%s: %.2f%n",
                    channel,
                    average
                )
        );

        System.out.printf(
            Locale.US,
            "%nPortfolio net CLV: %.2f%n",
            portfolio.portfolioValue()
        );

        AcquisitionMetrics acquisition =
            new AcquisitionMetrics(
                50000,
                100,
                6000
            );

        System.out.println("\nACQUISITION ECONOMICS");

        System.out.printf(
            "CAC: %.2f%n",
            acquisition.customerAcquisitionCost()
        );

        System.out.printf(
            "CLV/CAC ratio: %.2f%n",
            acquisition.clvToCacRatio()
        );

        System.out.println(
            "Assessment: " + acquisition.assessment()
        );
    }
}
