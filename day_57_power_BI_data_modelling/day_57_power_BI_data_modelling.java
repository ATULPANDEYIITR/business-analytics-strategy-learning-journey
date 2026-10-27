import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Collectors;

public class PowerBIDataModelDemo {

    enum RelationshipType {
        MANY_TO_ONE
    }

    enum FilterDirection {
        SINGLE
    }

    enum ModelState {
        DRAFT,
        VALIDATED
    }

    record DateDimension(
            int dateKey,
            String calendarDate,
            int year,
            int quarter,
            int month
    ) {
        DateDimension {
            if (dateKey <= 0 || calendarDate == null || calendarDate.isBlank()) {
                throw new IllegalArgumentException("Invalid date dimension.");
            }
        }
    }

    record CustomerDimension(
            int customerKey,
            String customerId,
            String customerName,
            String segment,
            String region
    ) {
        CustomerDimension {
            if (customerKey <= 0 ||
                customerId == null ||
                customerName == null ||
                segment == null ||
                region == null) {
                throw new IllegalArgumentException(
                        "Invalid customer dimension."
                );
            }
        }
    }

    record ProductDimension(
            int productKey,
            String productId,
            String productName,
            String category,
            String subcategory
    ) {
        ProductDimension {
            if (productKey <= 0 ||
                productId == null ||
                productName == null ||
                category == null ||
                subcategory == null) {
                throw new IllegalArgumentException(
                        "Invalid product dimension."
                );
            }
        }
    }

    record Relationship(
            String factColumn,
            String dimensionColumn,
            RelationshipType type,
            FilterDirection direction
    ) {}

    record SalesFact(
            int salesKey,
            int dateKey,
            int customerKey,
            int productKey,
            String orderId,
            int quantity,
            BigDecimal unitPrice,
            BigDecimal discountRate
    ) {
        SalesFact {
            Objects.requireNonNull(orderId, "Order ID is required.");
            Objects.requireNonNull(unitPrice, "Unit price is required.");
            Objects.requireNonNull(discountRate, "Discount rate is required.");

            if (salesKey <= 0) {
                throw new IllegalArgumentException("Sales key must be positive.");
            }
            if (quantity <= 0) {
                throw new IllegalArgumentException("Quantity must be positive.");
            }
            if (unitPrice.signum() < 0) {
                throw new IllegalArgumentException(
                        "Unit price cannot be negative."
                );
            }
            if (discountRate.signum() < 0 ||
                discountRate.compareTo(BigDecimal.ONE) > 0) {
                throw new IllegalArgumentException(
                        "Discount rate must be between zero and one."
                );
            }
        }

        BigDecimal netSales() {
            BigDecimal gross = unitPrice.multiply(
                    BigDecimal.valueOf(quantity)
            );

            return gross.multiply(
                    BigDecimal.ONE.subtract(discountRate)
            );
        }
    }

    static final class ModelValidationException extends RuntimeException {
        ModelValidationException(String message) {
            super(message);
        }
    }

    static final class DataModel {
        private final Map<Integer, DateDimension> dates = new LinkedHashMap<>();
        private final Map<Integer, CustomerDimension> customers =
                new LinkedHashMap<>();
        private final Map<Integer, ProductDimension> products =
                new LinkedHashMap<>();
        private final List<SalesFact> facts = new ArrayList<>();
        private final Set<RelationshipType> supportedRelationshipTypes =
                EnumSet.of(RelationshipType.MANY_TO_ONE);

        private final List<Relationship> relationships = List.of(
                new Relationship(
                        "dateKey",
                        "dateKey",
                        RelationshipType.MANY_TO_ONE,
                        FilterDirection.SINGLE
                ),
                new Relationship(
                        "customerKey",
                        "customerKey",
                        RelationshipType.MANY_TO_ONE,
                        FilterDirection.SINGLE
                ),
                new Relationship(
                        "productKey",
                        "productKey",
                        RelationshipType.MANY_TO_ONE,
                        FilterDirection.SINGLE
                )
        );

        private ModelState state = ModelState.DRAFT;

        void addDate(DateDimension row) {
            if (dates.putIfAbsent(row.dateKey(), row) != null) {
                throw new ModelValidationException(
                        "Duplicate date key: " + row.dateKey()
                );
            }
        }

        void addCustomer(CustomerDimension row) {
            if (customers.putIfAbsent(row.customerKey(), row) != null) {
                throw new ModelValidationException(
                        "Duplicate customer key: " + row.customerKey()
                );
            }
        }

        void addProduct(ProductDimension row) {
            if (products.putIfAbsent(row.productKey(), row) != null) {
                throw new ModelValidationException(
                        "Duplicate product key: " + row.productKey()
                );
            }
        }

        void addFact(SalesFact fact) {
            if (facts.stream().anyMatch(
                    existing -> existing.salesKey() == fact.salesKey())) {
                throw new ModelValidationException(
                        "Duplicate sales key: " + fact.salesKey()
                );
            }

            validateForeignKeys(fact);
            facts.add(fact);
            state = ModelState.DRAFT;
        }

        private void validateForeignKeys(SalesFact fact) {
            if (!dates.containsKey(fact.dateKey())) {
                throw new ModelValidationException(
                        "Missing date dimension key: " + fact.dateKey()
                );
            }

            if (!customers.containsKey(fact.customerKey())) {
                throw new ModelValidationException(
                        "Missing customer dimension key: "
                                + fact.customerKey()
                );
            }

            if (!products.containsKey(fact.productKey())) {
                throw new ModelValidationException(
                        "Missing product dimension key: "
                                + fact.productKey()
                );
            }
        }

        void validate() {
            if (dates.isEmpty() ||
                customers.isEmpty() ||
                products.isEmpty() ||
                facts.isEmpty()) {
                throw new ModelValidationException(
                        "All dimensions and the fact table must contain data."
                );
            }

            for (Relationship relationship : relationships) {
                if (!supportedRelationshipTypes.contains(
                        relationship.type())) {
                    throw new ModelValidationException(
                            "Unsupported relationship type."
                    );
                }

                if (relationship.direction() != FilterDirection.SINGLE) {
                    throw new ModelValidationException(
                            "Only single-direction filtering is allowed."
                    );
                }
            }

            facts.forEach(this::validateForeignKeys);
            state = ModelState.VALIDATED;
        }

        List<SalesFact> query(Predicate<SalesFact> factPredicate) {
            if (state != ModelState.VALIDATED) {
                throw new ModelValidationException(
                        "The model must be validated before querying."
                );
            }

            return facts.stream()
                    .filter(factPredicate)
                    .toList();
        }

        BigDecimal totalNetSales(List<SalesFact> selectedFacts) {
            return selectedFacts.stream()
                    .map(SalesFact::netSales)
                    .reduce(BigDecimal.ZERO, BigDecimal::add)
                    .setScale(2, RoundingMode.HALF_UP);
        }

        int totalQuantity(List<SalesFact> selectedFacts) {
            return selectedFacts.stream()
                    .mapToInt(SalesFact::quantity)
                    .sum();
        }

        Map<String, BigDecimal> salesByCategory(
                List<SalesFact> selectedFacts
        ) {
            return selectedFacts.stream().collect(
                    Collectors.groupingBy(
                            fact -> products.get(
                                    fact.productKey()
                            ).category(),
                            LinkedHashMap::new,
                            Collectors.reducing(
                                    BigDecimal.ZERO,
                                    SalesFact::netSales,
                                    BigDecimal::add
                            )
                    )
            );
        }

        Map<String, BigDecimal> salesByRegion(
                List<SalesFact> selectedFacts
        ) {
            return selectedFacts.stream().collect(
                    Collectors.groupingBy(
                            fact -> customers.get(
                                    fact.customerKey()
                            ).region(),
                            LinkedHashMap::new,
                            Collectors.reducing(
                                    BigDecimal.ZERO,
                                    SalesFact::netSales,
                                    BigDecimal::add
                            )
                    )
            );
        }

        ModelState state() {
            return state;
        }
    }

    static void loadSampleData(DataModel model) {
        model.addDate(
                new DateDimension(
                        20260105, "2026-01-05", 2026, 1, 1
                )
        );
        model.addDate(
                new DateDimension(
                        20260207, "2026-02-07", 2026, 1, 2
                )
        );
        model.addDate(
                new DateDimension(
                        20260312, "2026-03-12", 2026, 1, 3
                )
        );
        model.addDate(
                new DateDimension(
                        20260425, "2026-04-25", 2026, 2, 4
                )
        );

        model.addCustomer(
                new CustomerDimension(
                        1, "C001", "Apex Systems", "Enterprise", "North"
                )
        );
        model.addCustomer(
                new CustomerDimension(
                        2, "C002", "Blue Retail", "SMB", "West"
                )
        );
        model.addCustomer(
                new CustomerDimension(
                        3, "C003", "Cedar Health", "Enterprise", "South"
                )
        );
        model.addCustomer(
                new CustomerDimension(
                        4, "C004", "Delta Labs", "Mid-Market", "East"
                )
        );

        model.addProduct(
                new ProductDimension(
                        1, "P001", "Analytics Platform",
                        "Software", "Analytics"
                )
        );
        model.addProduct(
                new ProductDimension(
                        2, "P002", "Security Suite",
                        "Software", "Security"
                )
        );
        model.addProduct(
                new ProductDimension(
                        3, "P003", "Cloud Appliance",
                        "Hardware", "Infrastructure"
                )
        );
        model.addProduct(
                new ProductDimension(
                        4, "P004", "Support Contract",
                        "Services", "Support"
                )
        );

        model.addFact(
                new SalesFact(
                        1, 20260105, 1, 1, "SO1001",
                        3, new BigDecimal("1200.00"),
                        new BigDecimal("0.05")
                )
        );

        model.addFact(
                new SalesFact(
                        2, 20260207, 2, 2, "SO1002",
                        2, new BigDecimal("800.00"),
                        new BigDecimal("0.00")
                )
        );

        model.addFact(
                new SalesFact(
                        3, 20260312, 3, 3, "SO1003",
                        1, new BigDecimal("4500.00"),
                        new BigDecimal("0.10")
                )
        );

        model.addFact(
                new SalesFact(
                        4, 20260425, 4, 4, "SO1004",
                        5, new BigDecimal("300.00"),
                        new BigDecimal("0.05")
                )
        );
    }

    public static void main(String[] args) {
        DataModel model = new DataModel();
        loadSampleData(model);
        model.validate();

        List<SalesFact> all = model.query(fact -> true);

        List<SalesFact> enterprise = model.query(
                fact -> {
                    CustomerDimension customer = findCustomer(
                            model, fact.customerKey()
                    );
                    return customer.segment().equals("Enterprise");
                }
        );

        List<SalesFact> software = model.query(
                fact -> {
                    ProductDimension product = findProduct(
                            model, fact.productKey()
                    );
                    return product.category().equals("Software");
                }
        );

        System.out.println("POWER BI-STYLE ENTERPRISE DATA MODEL");
        System.out.println("====================================");
        System.out.println("Model state: " + model.state());
        System.out.println(
                "Total net sales: $" + model.totalNetSales(all)
        );
        System.out.println(
                "Total quantity: " + model.totalQuantity(all)
        );
        System.out.println(
                "Enterprise sales: $" + model.totalNetSales(enterprise)
        );
        System.out.println(
                "Software sales: $" + model.totalNetSales(software)
        );

        System.out.println("\nSales by category");
        model.salesByCategory(all).forEach(
                (category, value) ->
                        System.out.println(
                                category + ": $" +
                                value.setScale(2, RoundingMode.HALF_UP)
                        )
        );

        System.out.println("\nSales by region");
        model.salesByRegion(all).forEach(
                (region, value) ->
                        System.out.println(
                                region + ": $" +
                                value.setScale(2, RoundingMode.HALF_UP)
                        )
        );

        System.out.println("\nFailure-state demonstration");

        try {
            model.addFact(
                    new SalesFact(
                            99, 99999999, 1, 1, "BAD-FK",
                            1, new BigDecimal("100"),
                            BigDecimal.ZERO
                    )
            );
        } catch (ModelValidationException error) {
            System.out.println(
                    "Rejected invalid fact: " + error.getMessage()
            );
        }

        try {
            model.query(fact -> true);
            System.out.println("Validated query executed successfully.");
        } catch (ModelValidationException error) {
            System.out.println(
                    "Query rejected: " + error.getMessage()
            );
        }

        System.out.println("\nEnterprise design decisions");
        System.out.println(
                "- Records provide immutable dimension and fact values."
        );
        System.out.println(
                "- DataModel controls state transitions from DRAFT to VALIDATED."
        );
        System.out.println(
                "- BigDecimal prevents binary floating-point currency errors."
        );
        System.out.println(
                "- Predicate-based queries separate filtering from storage."
        );
        System.out.println(
                "- Stream grouping provides report-oriented aggregations."
        );
        System.out.println(
                "- Foreign-key validation prevents orphan fact records."
        );
    }

    private static CustomerDimension findCustomer(
            DataModel model,
            int key
    ) {
        try {
            var field = DataModel.class.getDeclaredField("customers");
            field.setAccessible(true);

            @SuppressWarnings("unchecked")
            Map<Integer, CustomerDimension> customers =
                    (Map<Integer, CustomerDimension>) field.get(model);

            return customers.get(key);
        } catch (ReflectiveOperationException error) {
            throw new IllegalStateException(
                    "Unable to resolve customer dimension.",
                    error
            );
        }
    }

    private static ProductDimension findProduct(
            DataModel model,
            int key
    ) {
        try {
            var field = DataModel.class.getDeclaredField("products");
            field.setAccessible(true);

            @SuppressWarnings("unchecked")
            Map<Integer, ProductDimension> products =
                    (Map<Integer, ProductDimension>) field.get(model);

            return products.get(key);
        } catch (ReflectiveOperationException error) {
            throw new IllegalStateException(
                    "Unable to resolve product dimension.",
                    error
            );
        }
    }
}
