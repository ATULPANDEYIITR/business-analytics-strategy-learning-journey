import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class DaxFundamentalsEnterprise {

    enum Category {
        TECHNOLOGY,
        FURNITURE
    }

    enum SalesBand {
        LOW,
        MEDIUM,
        HIGH
    }

    interface Measure {
        double evaluate(List<SalesRow> context);
    }

    record SalesRow(
        int orderId,
        String region,
        String product,
        Category category,
        int quantity,
        double unitPrice,
        double unitCost
    ) {
        SalesRow {
            if (orderId <= 0) {
                throw new ValidationException("Order ID must be positive");
            }

            if (region == null || region.isBlank()) {
                throw new ValidationException("Region is required");
            }

            if (product == null || product.isBlank()) {
                throw new ValidationException("Product is required");
            }

            if (quantity <= 0) {
                throw new ValidationException("Quantity must be positive");
            }

            if (unitPrice < 0 || unitCost < 0) {
                throw new ValidationException(
                    "Prices cannot be negative"
                );
            }

            if (unitCost > unitPrice) {
                throw new ValidationException(
                    "Unit cost cannot exceed unit price"
                );
            }
        }
    }

    record MeasureResult(
        double sales,
        double cost,
        double profit,
        double margin,
        int orders
    ) {}

    record Policy(
        double highSalesThreshold,
        double mediumSalesThreshold,
        Set<Category> includedCategories
    ) {
        Policy {
            if (highSalesThreshold <= mediumSalesThreshold) {
                throw new ValidationException(
                    "High threshold must exceed medium threshold"
                );
            }

            if (includedCategories == null) {
                throw new ValidationException(
                    "Category policy cannot be null"
                );
            }

            includedCategories =
                Set.copyOf(includedCategories);
        }
    }

    static class ValidationException extends RuntimeException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class SalesService {
        private final List<SalesRow> rows;
        private final Policy policy;

        SalesService(List<SalesRow> rows, Policy policy) {
            if (rows == null || rows.isEmpty()) {
                throw new ValidationException(
                    "At least one sales row is required"
                );
            }

            this.policy = policy;
            this.rows = List.copyOf(rows);
            validateUniqueOrders();
        }

        private void validateUniqueOrders() {
            Set<Integer> ids = new HashSet<>();

            for (SalesRow row : rows) {
                if (!ids.add(row.orderId())) {
                    throw new ValidationException(
                        "Duplicate order ID: " + row.orderId()
                    );
                }
            }
        }

        double salesAmount(SalesRow row) {
            return row.quantity() * row.unitPrice();
        }

        double costAmount(SalesRow row) {
            return row.quantity() * row.unitCost();
        }

        double profitAmount(SalesRow row) {
            return salesAmount(row) - costAmount(row);
        }

        double profitMargin(SalesRow row) {
            double sales = salesAmount(row);
            return sales == 0 ? 0 : profitAmount(row) / sales;
        }

        SalesBand classify(SalesRow row) {
            double sales = salesAmount(row);

            if (sales >= policy.highSalesThreshold()) {
                return SalesBand.HIGH;
            }

            if (sales >= policy.mediumSalesThreshold()) {
                return SalesBand.MEDIUM;
            }

            return SalesBand.LOW;
        }

        List<SalesRow> filter(
            String region,
            Category category,
            String product
        ) {
            return rows.stream()
                .filter(row ->
                    region == null ||
                    row.region().equals(region)
                )
                .filter(row ->
                    category == null ||
                    row.category() == category
                )
                .filter(row ->
                    product == null ||
                    row.product().equals(product)
                )
                .toList();
        }

        Measure totalSales() {
            return context ->
                context.stream()
                    .mapToDouble(this::salesAmount)
                    .sum();
        }

        Measure totalProfit() {
            return context ->
                context.stream()
                    .mapToDouble(this::profitAmount)
                    .sum();
        }

        Measure profitMargin() {
            return context -> {
                double sales = totalSales().evaluate(context);
                if (sales == 0) {
                    return 0;
                }

                return totalProfit().evaluate(context) / sales;
            };
        }

        MeasureResult evaluate(List<SalesRow> context) {
            double sales = totalSales().evaluate(context);
            double cost = context.stream()
                .mapToDouble(this::costAmount)
                .sum();
            double profit = totalProfit().evaluate(context);
            double margin = sales == 0 ? 0 : profit / sales;

            return new MeasureResult(
                sales,
                cost,
                profit,
                margin,
                context.size()
            );
        }

        /*
         * This method represents a context-changing analytical operation:
         * first create a filtered context, then evaluate a measure inside it.
         */
        double calculate(
            Measure measure,
            String region,
            Category category
        ) {
            List<SalesRow> context =
                filter(region, category, null);

            return measure.evaluate(context);
        }

        Map<String, MeasureResult> summarizeByRegion() {
            Map<String, List<SalesRow>> groups = new HashMap<>();

            for (SalesRow row : rows) {
                groups.computeIfAbsent(
                    row.region(),
                    ignored -> new ArrayList<>()
                ).add(row);
            }

            Map<String, MeasureResult> result = new HashMap<>();

            for (var entry : groups.entrySet()) {
                result.put(
                    entry.getKey(),
                    evaluate(entry.getValue())
                );
            }

            return result;
        }

        Map<Category, MeasureResult> summarizeByCategory() {
            Map<Category, List<SalesRow>> groups = new HashMap<>();

            for (SalesRow row : rows) {
                groups.computeIfAbsent(
                    row.category(),
                    ignored -> new ArrayList<>()
                ).add(row);
            }

            Map<Category, MeasureResult> result = new HashMap<>();

            for (var entry : groups.entrySet()) {
                result.put(
                    entry.getKey(),
                    evaluate(entry.getValue())
                );
            }

            return result;
        }

        List<Map.Entry<String, Double>> topProducts(int limit) {
            if (limit <= 0) {
                throw new ValidationException(
                    "Limit must be positive"
                );
            }

            Map<String, Double> totals = new HashMap<>();

            for (SalesRow row : rows) {
                totals.merge(
                    row.product(),
                    salesAmount(row),
                    Double::sum
                );
            }

            return totals.entrySet()
                .stream()
                .sorted(
                    Comparator
                        .<Map.Entry<String, Double>>comparingDouble(
                            Map.Entry::getValue
                        )
                        .reversed()
                        .thenComparing(Map.Entry::getKey)
                )
                .limit(limit)
                .toList();
        }

        List<SalesRow> rows() {
            return rows;
        }
    }

    static void money(double value) {
        System.out.printf("$%,.2f", value);
    }

    static void printResult(
        String name,
        MeasureResult result
    ) {
        System.out.print(name + ": sales=");
        money(result.sales());

        System.out.print(", cost=");
        money(result.cost());

        System.out.print(", profit=");
        money(result.profit());

        System.out.printf(
            ", margin=%.2f%%, orders=%d%n",
            result.margin() * 100,
            result.orders()
        );
    }

    public static void main(String[] args) {
        Policy policy = new Policy(
            5000,
            2000,
            EnumSet.allOf(Category.class)
        );

        List<SalesRow> rows = List.of(
            new SalesRow(
                1001, "North", "Laptop",
                Category.TECHNOLOGY, 2, 1200, 850
            ),
            new SalesRow(
                1002, "South", "Monitor",
                Category.TECHNOLOGY, 4, 350, 220
            ),
            new SalesRow(
                1003, "North", "Desk",
                Category.FURNITURE, 3, 500, 310
            ),
            new SalesRow(
                1004, "West", "Laptop",
                Category.TECHNOLOGY, 1, 1500, 980
            ),
            new SalesRow(
                1005, "South", "Chair",
                Category.FURNITURE, 8, 180, 110
            ),
            new SalesRow(
                1006, "West", "Desk",
                Category.FURNITURE, 2, 550, 320
            ),
            new SalesRow(
                1007, "North", "Monitor",
                Category.TECHNOLOGY, 5, 325, 200
            ),
            new SalesRow(
                1008, "South", "Laptop",
                Category.TECHNOLOGY, 3, 1100, 790
            )
        );

        SalesService service =
            new SalesService(rows, policy);

        MeasureResult all =
            service.evaluate(service.rows());

        List<SalesRow> north =
            service.filter("North", null, null);

        List<SalesRow> northTechnology =
            service.filter(
                "North",
                Category.TECHNOLOGY,
                null
            );

        System.out.println(
            "=== DAX FUNDAMENTALS ENTERPRISE MODEL ==="
        );

        printResult("All data", all);
        printResult(
            "North context",
            service.evaluate(north)
        );
        printResult(
            "North Technology context",
            service.evaluate(northTechnology)
        );

        double southTechnologyProfit =
            service.calculate(
                service.totalProfit(),
                "South",
                Category.TECHNOLOGY
            );

        System.out.print(
            "South Technology Profit: "
        );
        money(southTechnologyProfit);
        System.out.println();

        System.out.println(
            "\n=== CALCULATED-COLUMN STYLE DOMAIN LOGIC ==="
        );

        for (SalesRow row : service.rows()) {
            System.out.printf(
                "Order %d: sales=",
                row.orderId()
            );

            money(service.salesAmount(row));

            System.out.print(", profit=");
            money(service.profitAmount(row));

            System.out.printf(
                ", margin=%.2f%%, band=%s%n",
                service.profitMargin(row) * 100,
                service.classify(row)
            );
        }

        System.out.println("\n=== REGION MEASURES ===");

        service.summarizeByRegion()
            .entrySet()
            .stream()
            .sorted(Map.Entry.comparingByKey())
            .forEach(entry ->
                printResult(
                    entry.getKey(),
                    entry.getValue()
                )
            );

        System.out.println("\n=== CATEGORY MEASURES ===");

        service.summarizeByCategory()
            .forEach((category, result) ->
                printResult(
                    category.toString(),
                    result
                )
            );

        System.out.println("\n=== TOP PRODUCTS ===");

        for (var entry : service.topProducts(3)) {
            System.out.print(entry.getKey() + ": ");
            money(entry.getValue());
            System.out.println();
        }

        if (Math.abs(all.sales() - 10555.0) > 0.000001) {
            throw new AssertionError(
                "Unexpected total sales"
            );
        }

        if (Math.abs(all.profit() - 3405.0) > 0.000001) {
            throw new AssertionError(
                "Unexpected total profit"
            );
        }

        if (north.size() != 3) {
            throw new AssertionError(
                "Unexpected North row count"
            );
        }

        if (service.profitMargin().evaluate(List.of()) != 0) {
            throw new AssertionError(
                "Empty-context division handling failed"
            );
        }

        System.out.println("\nValidation checks: PASSED");
    }
}
