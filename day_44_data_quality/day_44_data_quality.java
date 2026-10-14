import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.*;

/*
 * Enterprise Data Quality Governance Model
 *
 * The program separates:
 * Accuracy      -> agreement with trusted reference information
 * Completeness  -> presence of required information
 * Consistency   -> agreement among related values and records
 * Validity      -> compliance with formal data rules
 *
 * Java 17 standard library only.
 */

public class DataQualityEnterprise {

    enum QualityDimension {
        ACCURACY,
        COMPLETENESS,
        CONSISTENCY,
        VALIDITY
    }

    enum CustomerStatus {
        ACTIVE,
        INACTIVE,
        PENDING
    }

    record Customer(
        String id,
        String name,
        String email,
        String country,
        String currency,
        CustomerStatus status,
        LocalDate signupDate,
        double creditLimit
    ) {}

    record VerifiedCustomer(
        String email,
        String country,
        String currency
    ) {}

    record QualityIssue(
        QualityDimension dimension,
        String field,
        String customerId,
        String message,
        Object value
    ) {}

    record QualityReport(
        List<QualityIssue> issues,
        Map<QualityDimension, Double> scores
    ) {
        boolean passesOverallGate(double threshold) {
            return scores.values()
                    .stream()
                    .mapToDouble(Double::doubleValue)
                    .average()
                    .orElse(100.0) >= threshold;
        }
    }

    interface QualityRule {
        List<QualityIssue> evaluate(
            Customer customer,
            QualityContext context
        );
    }

    record QualityContext(
        Map<String, VerifiedCustomer> verifiedCustomers,
        Map<String, String> currencyByCountry
    ) {}

    static final class CompletenessRule implements QualityRule {
        @Override
        public List<QualityIssue> evaluate(
            Customer customer,
            QualityContext context
        ) {
            List<QualityIssue> issues = new ArrayList<>();

            check("name", customer.name(), customer, issues);
            check("email", customer.email(), customer, issues);
            check("country", customer.country(), customer, issues);
            check("currency", customer.currency(), customer, issues);
            check("status", customer.status(), customer, issues);
            check("signupDate", customer.signupDate(), customer, issues);

            return issues;
        }

        private void check(
            String field,
            Object value,
            Customer customer,
            List<QualityIssue> issues
        ) {
            if (value == null || value.toString().isBlank()) {
                issues.add(
                    new QualityIssue(
                        QualityDimension.COMPLETENESS,
                        field,
                        customer.id(),
                        "Required value is missing.",
                        value
                    )
                );
            }
        }
    }

    static final class ValidityRule implements QualityRule {
        private static final Set<String> COUNTRIES =
            Set.of("IN", "US", "GB", "DE", "FR", "JP", "SG", "AU");

        @Override
        public List<QualityIssue> evaluate(
            Customer customer,
            QualityContext context
        ) {
            List<QualityIssue> issues = new ArrayList<>();

            if (!COUNTRIES.contains(customer.country())) {
                issues.add(
                    issue(
                        "country",
                        customer,
                        "Country is outside the accepted domain.",
                        customer.country()
                    )
                );
            }

            if (customer.status() == null) {
                issues.add(
                    issue(
                        "status",
                        customer,
                        "Customer status is missing.",
                        null
                    )
                );
            }

            if (customer.email() != null &&
                !customer.email().isBlank() &&
                !customer.email().matches(
                    "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$"
                )) {
                issues.add(
                    issue(
                        "email",
                        customer,
                        "Email format is invalid.",
                        customer.email()
                    )
                );
            }

            if (customer.signupDate() != null &&
                customer.signupDate().isAfter(LocalDate.now())) {
                issues.add(
                    issue(
                        "signupDate",
                        customer,
                        "Signup date cannot be in the future.",
                        customer.signupDate()
                    )
                );
            }

            if (customer.creditLimit() < 0) {
                issues.add(
                    issue(
                        "creditLimit",
                        customer,
                        "Credit limit cannot be negative.",
                        customer.creditLimit()
                    )
                );
            }

            return issues;
        }

        private QualityIssue issue(
            String field,
            Customer customer,
            String message,
            Object value
        ) {
            return new QualityIssue(
                QualityDimension.VALIDITY,
                field,
                customer.id(),
                message,
                value
            );
        }
    }

    static final class ConsistencyRule implements QualityRule {
        @Override
        public List<QualityIssue> evaluate(
            Customer customer,
            QualityContext context
        ) {
            List<QualityIssue> issues = new ArrayList<>();

            String expectedCurrency =
                context.currencyByCountry().get(customer.country());

            if (expectedCurrency != null &&
                !expectedCurrency.equals(customer.currency())) {
                issues.add(
                    new QualityIssue(
                        QualityDimension.CONSISTENCY,
                        "currency",
                        customer.id(),
                        "Country and currency are inconsistent.",
                        customer.currency()
                    )
                );
            }

            if (customer.status() == CustomerStatus.INACTIVE &&
                customer.creditLimit() > 0) {
                issues.add(
                    new QualityIssue(
                        QualityDimension.CONSISTENCY,
                        "creditLimit",
                        customer.id(),
                        "Inactive customer has a positive credit limit.",
                        customer.creditLimit()
                    )
                );
            }

            if (customer.name() != null &&
                customer.name().chars().anyMatch(Character::isDigit)) {
                issues.add(
                    new QualityIssue(
                        QualityDimension.CONSISTENCY,
                        "name",
                        customer.id(),
                        "Customer name contains numeric characters.",
                        customer.name()
                    )
                );
            }

            return issues;
        }
    }

    static final class AccuracyRule implements QualityRule {
        @Override
        public List<QualityIssue> evaluate(
            Customer customer,
            QualityContext context
        ) {
            VerifiedCustomer reference =
                context.verifiedCustomers().get(customer.id());

            if (reference == null) {
                return List.of();
            }

            List<QualityIssue> issues = new ArrayList<>();

            compare(
                "email",
                customer.email(),
                reference.email(),
                customer,
                issues
            );

            compare(
                "country",
                customer.country(),
                reference.country(),
                customer,
                issues
            );

            compare(
                "currency",
                customer.currency(),
                reference.currency(),
                customer,
                issues
            );

            return issues;
        }

        private void compare(
            String field,
            Object actual,
            Object expected,
            Customer customer,
            List<QualityIssue> issues
        ) {
            if (!Objects.equals(actual, expected)) {
                issues.add(
                    new QualityIssue(
                        QualityDimension.ACCURACY,
                        field,
                        customer.id(),
                        "Value differs from trusted reference data.",
                        actual
                    )
                );
            }
        }
    }

    static final class DatasetConsistencyRule {
        List<QualityIssue> evaluate(List<Customer> customers) {
            List<QualityIssue> issues = new ArrayList<>();

            Map<String, Long> idCounts =
                customers.stream()
                    .collect(
                        java.util.stream.Collectors.groupingBy(
                            Customer::id,
                            java.util.stream.Collectors.counting()
                        )
                    );

            for (Map.Entry<String, Long> entry : idCounts.entrySet()) {
                if (entry.getValue() > 1) {
                    issues.add(
                        new QualityIssue(
                            QualityDimension.CONSISTENCY,
                            "id",
                            entry.getKey(),
                            "Customer identifier is duplicated.",
                            entry.getKey()
                        )
                    );
                }
            }

            Map<String, List<Customer>> emailGroups =
                customers.stream()
                    .filter(c -> c.email() != null && !c.email().isBlank())
                    .collect(
                        java.util.stream.Collectors.groupingBy(
                            Customer::email
                        )
                    );

            emailGroups.forEach((email, owners) -> {
                if (owners.size() > 1) {
                    owners.forEach(customer ->
                        issues.add(
                            new QualityIssue(
                                QualityDimension.CONSISTENCY,
                                "email",
                                customer.id(),
                                "Email belongs to multiple customer records.",
                                email
                            )
                        )
                    );
                }
            });

            return issues;
        }
    }

    static final class QualityService {
        private final List<QualityRule> rules;
        private final DatasetConsistencyRule datasetRule =
            new DatasetConsistencyRule();

        QualityService(List<QualityRule> rules) {
            this.rules = List.copyOf(rules);
        }

        QualityReport assess(
            List<Customer> customers,
            QualityContext context
        ) {
            List<QualityIssue> issues = new ArrayList<>();

            for (Customer customer : customers) {
                for (QualityRule rule : rules) {
                    issues.addAll(rule.evaluate(customer, context));
                }
            }

            issues.addAll(datasetRule.evaluate(customers));

            Map<QualityDimension, Double> scores =
                calculateScores(customers, issues);

            return new QualityReport(
                List.copyOf(issues),
                Map.copyOf(scores)
            );
        }

        private Map<QualityDimension, Double> calculateScores(
            List<Customer> customers,
            List<QualityIssue> issues
        ) {
            EnumMap<QualityDimension, Set<String>> affected =
                new EnumMap<>(QualityDimension.class);

            for (QualityDimension dimension : QualityDimension.values()) {
                affected.put(dimension, new HashSet<>());
            }

            for (QualityIssue issue : issues) {
                affected
                    .get(issue.dimension())
                    .add(issue.customerId());
            }

            EnumMap<QualityDimension, Double> scores =
                new EnumMap<>(QualityDimension.class);

            for (QualityDimension dimension : QualityDimension.values()) {
                double score;

                if (customers.isEmpty()) {
                    score = 100.0;
                } else {
                    score =
                        100.0 *
                        (customers.size() -
                         affected.get(dimension).size()) /
                        customers.size();
                }

                scores.put(dimension, score);
            }

            return scores;
        }
    }

    private static Customer customer(
        String id,
        String name,
        String email,
        String country,
        String currency,
        String status,
        String signupDate,
        double creditLimit
    ) {
        LocalDate parsedDate;

        try {
            parsedDate = LocalDate.parse(signupDate);
        } catch (DateTimeParseException exception) {
            parsedDate = null;
        }

        CustomerStatus parsedStatus;

        try {
            parsedStatus = CustomerStatus.valueOf(status.toUpperCase());
        } catch (IllegalArgumentException | NullPointerException exception) {
            parsedStatus = null;
        }

        return new Customer(
            id,
            name,
            email,
            country,
            currency,
            parsedStatus,
            parsedDate,
            creditLimit
        );
    }

    public static void main(String[] args) {
        Map<String, VerifiedCustomer> verified =
            Map.of(
                "C1001",
                new VerifiedCustomer(
                    "atul@example.com",
                    "IN",
                    "INR"
                ),
                "C1002",
                new VerifiedCustomer(
                    "maria@example.com",
                    "DE",
                    "EUR"
                )
            );

        Map<String, String> currencyByCountry =
            Map.of(
                "IN", "INR",
                "US", "USD",
                "GB", "GBP",
                "DE", "EUR",
                "FR", "EUR",
                "JP", "JPY",
                "SG", "SGD",
                "AU", "AUD"
            );

        QualityContext context =
            new QualityContext(
                verified,
                currencyByCountry
            );

        List<Customer> customers =
            List.of(
                customer(
                    "C1001",
                    "Atul Pandey",
                    "atul@example.com",
                    "IN",
                    "INR",
                    "active",
                    "2026-01-15",
                    500000
                ),
                customer(
                    "C1002",
                    "Maria Silva",
                    "maria.changed@example.com",
                    "DE",
                    "EUR",
                    "active",
                    "2026-02-12",
                    75000
                ),
                customer(
                    "C1003",
                    "Ravi Kumar",
                    "",
                    "IN",
                    "INR",
                    "pending",
                    "2026-03-10",
                    25000
                ),
                customer(
                    "C1004",
                    "Elena7",
                    "elena@example",
                    "XX",
                    "USD",
                    "unknown",
                    "2027-04-01",
                    -500
                ),
                customer(
                    "C1005",
                    "John Smith",
                    "john@example.com",
                    "US",
                    "EUR",
                    "inactive",
                    "2026-02-01",
                    1000
                ),
                customer(
                    "C1006",
                    "Duplicate User",
                    "atul@example.com",
                    "IN",
                    "INR",
                    "active",
                    "2026-04-01",
                    30000
                )
            );

        QualityService service =
            new QualityService(
                List.of(
                    new CompletenessRule(),
                    new ValidityRule(),
                    new ConsistencyRule(),
                    new AccuracyRule()
                )
            );

        QualityReport report =
            service.assess(customers, context);

        System.out.println("DATA QUALITY SCORECARD");
        System.out.println("=====================");

        report.scores().forEach(
            (dimension, score) ->
                System.out.printf(
                    Locale.US,
                    "%-15s %.2f%%%n",
                    dimension,
                    score
                )
        );

        System.out.println("\nQUALITY ISSUES");
        System.out.println("==============");

        report.issues().forEach(
            issue ->
                System.out.printf(
                    "[%s] %s.%s: %s%n",
                    issue.dimension(),
                    issue.customerId(),
                    issue.field(),
                    issue.message()
                )
        );

        double average =
            report.scores()
                .values()
                .stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(100.0);

        System.out.printf(
            Locale.US,
            "%nOverall score: %.2f%%%n",
            average
        );

        if (report.passesOverallGate(90.0)) {
            System.out.println("Quality gate: PASSED");
        } else {
            System.out.println("Quality gate: FAILED");
        }
    }
}
