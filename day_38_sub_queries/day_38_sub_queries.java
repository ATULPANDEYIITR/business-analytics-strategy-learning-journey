import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/*
 * Enterprise-oriented nested-query case study.
 *
 * The domain is a retail analytics service. Java records provide immutable
 * domain values, while service methods model different forms of SQL nested
 * analytical reasoning:
 *
 * scalar benchmark, membership filtering, correlated analysis, existence
 * predicates, derived datasets, and multi-stage aggregation.
 */
public class NestedQueryAnalytics {

    enum OrderStatus {
        COMPLETED,
        CANCELLED,
        PENDING
    }

    record Customer(
        int id,
        String name,
        String region,
        String tier
    ) {}

    record Product(
        int id,
        String name,
        String category,
        double price
    ) {}

    record Order(
        int id,
        int customerId,
        OrderStatus status
    ) {}

    record OrderItem(
        int orderId,
        int productId,
        int quantity
    ) {}

    record OrderTotal(
        int orderId,
        int customerId,
        double total
    ) {}

    record CustomerRevenue(
        Customer customer,
        double revenue
    ) {}

    private final List<Customer> customers;
    private final List<Product> products;
    private final List<Order> orders;
    private final List<OrderItem> orderItems;

    public NestedQueryAnalytics() {
        customers = List.of(
            new Customer(1, "Aarav Mehta", "North", "Gold"),
            new Customer(2, "Diya Sharma", "North", "Silver"),
            new Customer(3, "Kabir Singh", "West", "Gold"),
            new Customer(4, "Meera Iyer", "South", "Standard"),
            new Customer(5, "Rohan Gupta", "West", "Silver"),
            new Customer(6, "Ananya Rao", "South", "Gold"),
            new Customer(7, "Vikram Joshi", "East", "Standard"),
            new Customer(8, "Sara Khan", "East", "Silver")
        );

        products = List.of(
            new Product(1, "Laptop Pro", "Electronics", 1200),
            new Product(2, "Mechanical Keyboard", "Electronics", 140),
            new Product(3, "Office Chair", "Furniture", 350),
            new Product(4, "Monitor 27", "Electronics", 420),
            new Product(5, "Standing Desk", "Furniture", 650),
            new Product(6, "USB-C Hub", "Accessories", 80),
            new Product(7, "Webcam", "Accessories", 110)
        );

        orders = List.of(
            new Order(101, 1, OrderStatus.COMPLETED),
            new Order(102, 1, OrderStatus.COMPLETED),
            new Order(103, 2, OrderStatus.COMPLETED),
            new Order(104, 2, OrderStatus.COMPLETED),
            new Order(105, 3, OrderStatus.COMPLETED),
            new Order(106, 3, OrderStatus.COMPLETED),
            new Order(107, 3, OrderStatus.COMPLETED),
            new Order(108, 4, OrderStatus.COMPLETED),
            new Order(109, 4, OrderStatus.CANCELLED),
            new Order(110, 5, OrderStatus.COMPLETED),
            new Order(111, 5, OrderStatus.COMPLETED),
            new Order(112, 6, OrderStatus.COMPLETED),
            new Order(113, 6, OrderStatus.COMPLETED),
            new Order(114, 7, OrderStatus.COMPLETED),
            new Order(115, 8, OrderStatus.PENDING)
        );

        orderItems = List.of(
            new OrderItem(101, 1, 1),
            new OrderItem(101, 2, 1),
            new OrderItem(102, 4, 1),
            new OrderItem(102, 6, 2),
            new OrderItem(103, 3, 1),
            new OrderItem(103, 7, 1),
            new OrderItem(104, 2, 2),
            new OrderItem(104, 6, 1),
            new OrderItem(105, 1, 1),
            new OrderItem(105, 6, 1),
            new OrderItem(106, 5, 1),
            new OrderItem(106, 4, 1),
            new OrderItem(107, 1, 1),
            new OrderItem(107, 7, 2),
            new OrderItem(108, 3, 1),
            new OrderItem(108, 6, 2),
            new OrderItem(109, 4, 1),
            new OrderItem(110, 5, 1),
            new OrderItem(110, 2, 1),
            new OrderItem(111, 3, 2),
            new OrderItem(111, 7, 1),
            new OrderItem(112, 1, 1),
            new OrderItem(112, 4, 1),
            new OrderItem(113, 5, 1),
            new OrderItem(113, 6, 2),
            new OrderItem(114, 2, 1),
            new OrderItem(114, 7, 1),
            new OrderItem(115, 4, 1)
        );
    }

    private Product productById(int productId) {
        return products.stream()
            .filter(product -> product.id() == productId)
            .findFirst()
            .orElseThrow(() ->
                new IllegalArgumentException(
                    "Unknown product: " + productId
                )
            );
    }

    private Customer customerById(int customerId) {
        return customers.stream()
            .filter(customer -> customer.id() == customerId)
            .findFirst()
            .orElseThrow(() ->
                new IllegalArgumentException(
                    "Unknown customer: " + customerId
                )
            );
    }

    private double orderTotal(int orderId) {
        return orderItems.stream()
            .filter(item -> item.orderId() == orderId)
            .mapToDouble(item -> {
                Product product = productById(item.productId());
                return product.price() * item.quantity();
            })
            .sum();
    }

    /*
     * This intermediate relation is equivalent to a derived table in SQL.
     * Keeping it as an immutable list makes the later analytical stages
     * explicit and prevents repeated item-level calculations.
     */
    private List<OrderTotal> completedOrderTotals() {
        return orders.stream()
            .filter(order -> order.status() == OrderStatus.COMPLETED)
            .map(order -> new OrderTotal(
                order.id(),
                order.customerId(),
                orderTotal(order.id())
            ))
            .toList();
    }

    private static double average(List<Double> values) {
        if (values.isEmpty()) {
            throw new IllegalArgumentException(
                "Average requires at least one value."
            );
        }

        return values.stream()
            .mapToDouble(Double::doubleValue)
            .average()
            .orElseThrow();
    }

    /*
     * Scalar-subquery semantics:
     * the inner analytical operation produces one global benchmark.
     */
    public List<Product> productsAboveOverallAverage() {
        double benchmark = average(
            products.stream()
                .map(Product::price)
                .toList()
        );

        return products.stream()
            .filter(product -> product.price() > benchmark)
            .sorted(Comparator.comparingDouble(Product::price).reversed())
            .toList();
    }

    /*
     * IN-subquery semantics:
     * build a set of qualifying customer IDs first, then perform membership
     * filtering against that set.
     */
    public List<Customer> customersWithCompletedOrders() {
        Set<Integer> completedCustomerIds = orders.stream()
            .filter(order -> order.status() == OrderStatus.COMPLETED)
            .map(Order::customerId)
            .collect(Collectors.toCollection(HashSet::new));

        return customers.stream()
            .filter(customer -> completedCustomerIds.contains(customer.id()))
            .toList();
    }

    /*
     * EXISTS semantics:
     * the customer is retained as soon as one matching furniture purchase
     * exists. Multiple matching items do not duplicate the customer.
     */
    public List<Customer> customersWhoBoughtFurniture() {
        return customers.stream()
            .filter(customer -> orders.stream()
                .filter(order ->
                    order.customerId() == customer.id() &&
                    order.status() == OrderStatus.COMPLETED
                )
                .anyMatch(order -> orderItems.stream()
                    .filter(item -> item.orderId() == order.id())
                    .map(item -> productById(item.productId()))
                    .anyMatch(product ->
                        product.category().equals("Furniture")
                    )
                )
            )
            .toList();
    }

    /*
     * Correlated-subquery semantics:
     * the inner stream uses the current customer ID from the outer stream.
     */
    public Map<String, Double> averageOrderValuePerCustomer() {
        Map<String, Double> result = new HashMap<>();

        for (Customer customer : customers) {
            List<Double> totals = completedOrderTotals().stream()
                .filter(order ->
                    order.customerId() == customer.id()
                )
                .map(OrderTotal::total)
                .toList();

            if (!totals.isEmpty()) {
                result.put(customer.name(), average(totals));
            }
        }

        return result.entrySet().stream()
            .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
            .collect(Collectors.toMap(
                Map.Entry::getKey,
                Map.Entry::getValue,
                (left, right) -> left,
                java.util.LinkedHashMap::new
            ));
    }

    /*
     * Nested aggregation:
     * order totals become customer revenue, then customer revenue becomes
     * the input to a second average benchmark.
     */
    public List<CustomerRevenue> customersAboveAverageRevenue() {
        List<OrderTotal> orderTotals = completedOrderTotals();

        List<CustomerRevenue> revenue = customers.stream()
            .map(customer -> {
                double total = orderTotals.stream()
                    .filter(order ->
                        order.customerId() == customer.id()
                    )
                    .mapToDouble(OrderTotal::total)
                    .sum();

                return new CustomerRevenue(customer, total);
            })
            .filter(row -> row.revenue() > 0)
            .toList();

        double benchmark = average(
            revenue.stream()
                .map(CustomerRevenue::revenue)
                .toList()
        );

        return revenue.stream()
            .filter(row -> row.revenue() > benchmark)
            .sorted(
                Comparator.comparingDouble(CustomerRevenue::revenue)
                    .reversed()
            )
            .toList();
    }

    /*
     * NOT EXISTS semantics:
     * a product is a category leader when no sibling product has a higher
     * price.
     */
    public List<Product> categoryPriceLeaders() {
        return products.stream()
            .filter(candidate -> products.stream()
                .noneMatch(other ->
                    other.category().equals(candidate.category()) &&
                    other.price() > candidate.price()
                )
            )
            .sorted(Comparator.comparing(Product::category))
            .toList();
    }

    /*
     * A grouped intermediate map represents the result of a nested aggregate.
     * The outer stage computes the benchmark across category totals.
     */
    public List<Map.Entry<String, Double>> categoriesAboveAverageRevenue() {
        Map<String, Double> categoryRevenue = new HashMap<>();

        for (Order order : orders) {
            if (order.status() != OrderStatus.COMPLETED) {
                continue;
            }

            for (OrderItem item : orderItems) {
                if (item.orderId() != order.id()) {
                    continue;
                }

                Product product = productById(item.productId());

                categoryRevenue.merge(
                    product.category(),
                    product.price() * item.quantity(),
                    Double::sum
                );
            }
        }

        double benchmark = average(
            new ArrayList<>(categoryRevenue.values())
        );

        return categoryRevenue.entrySet().stream()
            .filter(entry -> entry.getValue() > benchmark)
            .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
            .toList();
    }

    /*
     * Combining EXISTS and NOT EXISTS produces a precise business condition:
     * the customer must have completed activity and must have no cancellation.
     */
    public List<Customer> completedWithoutCancellation() {
        return customers.stream()
            .filter(customer -> orders.stream().anyMatch(order ->
                order.customerId() == customer.id() &&
                order.status() == OrderStatus.COMPLETED
            ))
            .filter(customer -> orders.stream().noneMatch(order ->
                order.customerId() == customer.id() &&
                order.status() == OrderStatus.CANCELLED
            ))
            .toList();
    }

    public void printReport() {
        System.out.println("\nProducts above overall average price");
        productsAboveOverallAverage().forEach(product ->
            System.out.printf(
                "  %s | %s | $%.2f%n",
                product.name(),
                product.category(),
                product.price()
            )
        );

        System.out.println("\nCustomers with completed orders");
        customersWithCompletedOrders().forEach(customer ->
            System.out.println("  " + customer.name())
        );

        System.out.println("\nCustomers who bought furniture");
        customersWhoBoughtFurniture().forEach(customer ->
            System.out.println("  " + customer.name())
        );

        System.out.println("\nAverage order value by customer");
        averageOrderValuePerCustomer().forEach((name, value) ->
            System.out.printf("  %s | $%.2f%n", name, value)
        );

        System.out.println("\nCustomers above average revenue");
        customersAboveAverageRevenue().forEach(row ->
            System.out.printf(
                "  %s | $%.2f%n",
                row.customer().name(),
                row.revenue()
            )
        );

        System.out.println("\nCategory price leaders");
        categoryPriceLeaders().forEach(product ->
            System.out.printf(
                "  %s | %s | $%.2f%n",
                product.category(),
                product.name(),
                product.price()
            )
        );

        System.out.println("\nCategories above average revenue");
        categoriesAboveAverageRevenue().forEach(entry ->
            System.out.printf(
                "  %s | $%.2f%n",
                entry.getKey(),
                entry.getValue()
            )
        );

        System.out.println("\nCompleted activity without cancellation");
        completedWithoutCancellation().forEach(customer ->
            System.out.println("  " + customer.name())
        );
    }

    public static void main(String[] args) {
        try {
            new NestedQueryAnalytics().printReport();
        } catch (IllegalArgumentException exception) {
            System.err.println(
                "Analytical validation failed: " +
                exception.getMessage()
            );
        }
    }
}
