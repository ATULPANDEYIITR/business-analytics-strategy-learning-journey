import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Collectors;

public class SegmentationEnterpriseDemo {

    enum SegmentDimension {
        CUSTOMER,
        PRODUCT,
        GEOGRAPHIC,
        BEHAVIORAL
    }

    enum CustomerTier {
        SILVER,
        GOLD,
        PLATINUM
    }

    record Customer(
        String id,
        int age,
        double income,
        String region,
        String city,
        CustomerTier tier
    ) {
        Customer {
            if (age < 18) {
                throw new IllegalArgumentException("Customer must be an adult.");
            }
            if (income < 0) {
                throw new IllegalArgumentException("Income cannot be negative.");
            }
            Objects.requireNonNull(id);
            Objects.requireNonNull(region);
        }
    }

    record Product(
        String id,
        String category,
        double price,
        double margin
    ) {
        Product {
            if (price < 0) {
                throw new IllegalArgumentException("Price cannot be negative.");
            }
            if (margin < 0 || margin > 1) {
                throw new IllegalArgumentException("Margin must be between 0 and 1.");
            }
        }
    }

    record Purchase(
        String customerId,
        String productId,
        int quantity,
        double unitPrice,
        LocalDate date
    ) {
        Purchase {
            if (quantity <= 0) {
                throw new IllegalArgumentException("Quantity must be positive.");
            }
            if (unitPrice < 0) {
                throw new IllegalArgumentException("Unit price cannot be negative.");
            }
        }

        double value() {
            return quantity * unitPrice;
        }
    }

    record Segment(
        String name,
        SegmentDimension dimension,
        Set<String> members,
        String rule
    ) {}

    interface SegmentRule {
        boolean matches(Customer customer, CustomerContext context);
    }

    record CustomerContext(
        double medianIncome,
        Map<String, List<Purchase>> purchasesByCustomer
    ) {}

    static final class RepositoryGovernanceService {
        private final Map<String, Customer> customers = new LinkedHashMap<>();
        private final Map<String, Product> products = new LinkedHashMap<>();
        private final List<Purchase> purchases = new ArrayList<>();

        void registerCustomer(Customer customer) {
            if (customers.putIfAbsent(customer.id(), customer) != null) {
                throw new IllegalArgumentException(
                    "Duplicate customer: " + customer.id()
                );
            }
        }

        void registerProduct(Product product) {
            if (products.putIfAbsent(product.id(), product) != null) {
                throw new IllegalArgumentException(
                    "Duplicate product: " + product.id()
                );
            }
        }

        void recordPurchase(Purchase purchase) {
            if (!customers.containsKey(purchase.customerId())) {
                throw new IllegalArgumentException(
                    "Unknown customer: " + purchase.customerId()
                );
            }

            if (!products.containsKey(purchase.productId())) {
                throw new IllegalArgumentException(
                    "Unknown product: " + purchase.productId()
                );
            }

            purchases.add(purchase);
        }

        CustomerContext customerContext() {
            double medianIncome = median(
                customers.values().stream()
                    .map(Customer::income)
                    .toList()
            );

            Map<String, List<Purchase>> grouped =
                purchases.stream().collect(
                    Collectors.groupingBy(
                        Purchase::customerId,
                        LinkedHashMap::new,
                        Collectors.toList()
                    )
                );

            return new CustomerContext(medianIncome, grouped);
        }

        List<Segment> customerSegments() {
            CustomerContext context = customerContext();

            SegmentRule youngProfessional =
                (customer, ignored) ->
                    customer.age() <= 34 &&
                    customer.income() >= context.medianIncome();

            SegmentRule establishedHighIncome =
                (customer, ignored) ->
                    customer.age() >= 35 &&
                    customer.income() > context.medianIncome();

            SegmentRule valueConscious =
                (customer, ignored) ->
                    customer.income() < context.medianIncome();

            return List.of(
                buildCustomerSegment(
                    "young_professionals",
                    youngProfessional,
                    context,
                    "Age <= 34 and income >= median income"
                ),
                buildCustomerSegment(
                    "established_high_income",
                    establishedHighIncome,
                    context,
                    "Age >= 35 and income > median income"
                ),
                buildCustomerSegment(
                    "value_conscious",
                    valueConscious,
                    context,
                    "Income below median income"
                )
            );
        }

        private Segment buildCustomerSegment(
            String name,
            SegmentRule rule,
            CustomerContext context,
            String description
        ) {
            Set<String> members = customers.values().stream()
                .filter(customer -> rule.matches(customer, context))
                .map(Customer::id)
                .collect(Collectors.toSet());

            return new Segment(
                name,
                SegmentDimension.CUSTOMER,
                members,
                description
            );
        }

        List<Segment> geographicSegments() {
            Map<String, Set<String>> groups = new LinkedHashMap<>();

            customers.values().forEach(customer ->
                groups.computeIfAbsent(
                    customer.region(),
                    ignored -> new java.util.HashSet<>()
                ).add(customer.id())
            );

            return groups.entrySet().stream()
                .map(entry -> new Segment(
                    "region_" + entry.getKey().toLowerCase(),
                    SegmentDimension.GEOGRAPHIC,
                    Set.copyOf(entry.getValue()),
                    "Customers located in " + entry.getKey()
                ))
                .toList();
        }

        List<Segment> productSegments() {
            double medianPrice = median(
                products.values().stream()
                    .map(Product::price)
                    .toList()
            );

            Set<String> premium = products.values().stream()
                .filter(product -> product.price() > medianPrice)
                .map(Product::id)
                .collect(Collectors.toSet());

            Set<String> highMargin = products.values().stream()
                .filter(product -> product.margin() >= 0.30)
                .map(Product::id)
                .collect(Collectors.toSet());

            return List.of(
                new Segment(
                    "premium",
                    SegmentDimension.PRODUCT,
                    Set.copyOf(premium),
                    "Price above portfolio median"
                ),
                new Segment(
                    "high_margin",
                    SegmentDimension.PRODUCT,
                    Set.copyOf(highMargin),
                    "Margin >= 30%"
                )
            );
        }

        List<Segment> behavioralSegments(LocalDate referenceDate) {
            Map<String, Behavior> behavior = new HashMap<>();

            for (String customerId : customers.keySet()) {
                List<Purchase> customerPurchases =
                    customerContext().purchasesByCustomer()
                        .getOrDefault(customerId, List.of());

                int frequency = customerPurchases.size();
                double monetary = customerPurchases.stream()
                    .mapToDouble(Purchase::value)
                    .sum();

                long recency = customerPurchases.stream()
                    .map(Purchase::date)
                    .mapToLong(date ->
                        ChronoUnit.DAYS.between(date, referenceDate))
                    .min()
                    .orElse(Long.MAX_VALUE);

                behavior.put(
                    customerId,
                    new Behavior(frequency, monetary, recency)
                );
            }

            double frequencyMedian = median(
                behavior.values().stream()
                    .mapToDouble(Behavior::frequency)
                    .boxed()
                    .toList()
            );

            double monetaryMedian = median(
                behavior.values().stream()
                    .mapToDouble(Behavior::monetary)
                    .boxed()
                    .toList()
            );

            Set<String> loyalHighValue = behavior.entrySet().stream()
                .filter(entry ->
                    entry.getValue().frequency() >= frequencyMedian &&
                    entry.getValue().monetary() >= monetaryMedian
                )
                .map(Map.Entry::getKey)
                .collect(Collectors.toSet());

            Set<String> recentLowFrequency = behavior.entrySet().stream()
                .filter(entry ->
                    entry.getValue().recency() <= 30 &&
                    entry.getValue().frequency() < frequencyMedian
                )
                .map(Map.Entry::getKey)
                .collect(Collectors.toSet());

            Set<String> atRisk = behavior.entrySet().stream()
                .filter(entry -> entry.getValue().recency() > 60)
                .map(Map.Entry::getKey)
                .collect(Collectors.toSet());

            return List.of(
                new Segment(
                    "loyal_high_value",
                    SegmentDimension.BEHAVIORAL,
                    Set.copyOf(loyalHighValue),
                    "Frequency and monetary value at or above their medians"
                ),
                new Segment(
                    "recent_low_frequency",
                    SegmentDimension.BEHAVIORAL,
                    Set.copyOf(recentLowFrequency),
                    "Recent purchase with below-median frequency"
                ),
                new Segment(
                    "at_risk",
                    SegmentDimension.BEHAVIORAL,
                    Set.copyOf(atRisk),
                    "No purchase within the recent activity threshold"
                )
            );
        }

        Map<SegmentDimension, List<Segment>> allSegments(
            LocalDate referenceDate
        ) {
            Map<SegmentDimension, List<Segment>> result =
                new EnumMap<>(SegmentDimension.class);

            result.put(SegmentDimension.CUSTOMER, customerSegments());
            result.put(SegmentDimension.PRODUCT, productSegments());
            result.put(SegmentDimension.GEOGRAPHIC, geographicSegments());
            result.put(
                SegmentDimension.BEHAVIORAL,
                behavioralSegments(referenceDate)
            );

            return result;
        }
    }

    record Behavior(
        int frequency,
        double monetary,
        long recency
    ) {}

    static double median(List<Double> values) {
        if (values.isEmpty()) {
            throw new IllegalArgumentException("Median requires data.");
        }

        List<Double> sorted = new ArrayList<>(values);
        sorted.sort(Double::compareTo);

        int middle = sorted.size() / 2;

        if (sorted.size() % 2 == 0) {
            return (sorted.get(middle - 1) + sorted.get(middle)) / 2;
        }

        return sorted.get(middle);
    }

    static void printSegments(
        SegmentDimension dimension,
        List<Segment> segments
    ) {
        System.out.println("\n" + dimension + " segmentation");

        for (Segment segment : segments) {
            System.out.printf(
                "  %s -> %s%n",
                segment.name(),
                segment.members()
            );
            System.out.println("    Rule: " + segment.rule());
        }
    }

    public static void main(String[] args) {
        RepositoryGovernanceService service =
            new RepositoryGovernanceService();

        service.registerCustomer(
            new Customer(
                "C001", 27, 90000, "North", "Delhi", CustomerTier.GOLD
            )
        );
        service.registerCustomer(
            new Customer(
                "C002", 42, 145000, "West", "Mumbai", CustomerTier.PLATINUM
            )
        );
        service.registerCustomer(
            new Customer(
                "C003", 31, 42000, "East", "Kolkata", CustomerTier.SILVER
            )
        );
        service.registerCustomer(
            new Customer(
                "C004", 55, 70000, "South", "Bengaluru", CustomerTier.GOLD
            )
        );
        service.registerCustomer(
            new Customer(
                "C005", 23, 52000, "North", "Lucknow", CustomerTier.SILVER
            )
        );
        service.registerCustomer(
            new Customer(
                "C006", 38, 160000, "West", "Pune", CustomerTier.PLATINUM
            )
        );

        service.registerProduct(
            new Product("P001", "Electronics", 120000, 0.22)
        );
        service.registerProduct(
            new Product("P002", "Home", 18000, 0.35)
        );
        service.registerProduct(
            new Product("P003", "Household", 3500, 0.42)
        );
        service.registerProduct(
            new Product("P004", "Fashion", 6500, 0.48)
        );
        service.registerProduct(
            new Product("P005", "Electronics", 42000, 0.31)
        );

        service.recordPurchase(
            new Purchase("C001", "P005", 1, 42000, LocalDate.of(2026, 10, 5))
        );
        service.recordPurchase(
            new Purchase("C001", "P003", 3, 3500, LocalDate.of(2026, 9, 20))
        );
        service.recordPurchase(
            new Purchase("C002", "P001", 1, 120000, LocalDate.of(2026, 10, 10))
        );
        service.recordPurchase(
            new Purchase("C002", "P002", 3, 18000, LocalDate.of(2026, 9, 11))
        );
        service.recordPurchase(
            new Purchase("C003", "P003", 4, 3500, LocalDate.of(2026, 10, 1))
        );
        service.recordPurchase(
            new Purchase("C004", "P002", 2, 18000, LocalDate.of(2026, 7, 5))
        );
        service.recordPurchase(
            new Purchase("C005", "P004", 1, 6500, LocalDate.of(2026, 10, 3))
        );
        service.recordPurchase(
            new Purchase("C006", "P001", 1, 120000, LocalDate.of(2026, 9, 30))
        );
        service.recordPurchase(
            new Purchase("C006", "P005", 2, 42000, LocalDate.of(2026, 8, 29))
        );

        Map<SegmentDimension, List<Segment>> segments =
            service.allSegments(LocalDate.of(2026, 10, 17));

        segments.forEach(
            (dimension, values) -> printSegments(dimension, values)
        );

        try {
            service.recordPurchase(
                new Purchase(
                    "C999",
                    "P001",
                    1,
                    120000,
                    LocalDate.of(2026, 10, 17)
                )
            );
        } catch (IllegalArgumentException error) {
            System.out.println(
                "\nRejected invalid transaction: " + error.getMessage()
            );
        }
    }
}
