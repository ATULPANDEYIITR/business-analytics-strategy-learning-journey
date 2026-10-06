import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/*
 * CASE Statements: Creating Business Logic Using SQL
 *
 * This Java program models an enterprise order-pricing service. Its domain
 * rules correspond to SQL CASE expressions but are represented with explicit
 * Java types so that validation, state, and policy boundaries remain visible.
 *
 * The Java implementation complements SQL rather than replacing it:
 * SQL CASE is particularly valuable when the classification must be derived
 * for many rows during a query, aggregation, reporting operation, or view.
 */
public class CaseBusinessLogicDemo {

    enum AccountStatus {
        ACTIVE, SUSPENDED
    }

    enum PaymentStatus {
        PAID, PENDING, FAILED, REFUNDED
    }

    enum OrderStatus {
        CONFIRMED, CANCELLED
    }

    record Customer(
            long id,
            String name,
            String country,
            BigDecimal lifetimeValue,
            AccountStatus accountStatus
    ) {
        Customer {
            Objects.requireNonNull(name);
            Objects.requireNonNull(country);
            Objects.requireNonNull(lifetimeValue);
            Objects.requireNonNull(accountStatus);

            if (id <= 0) {
                throw new IllegalArgumentException("Customer ID must be positive");
            }

            if (lifetimeValue.signum() < 0) {
                throw new IllegalArgumentException(
                        "Lifetime value cannot be negative"
                );
            }
        }
    }

    record Order(
            long id,
            long customerId,
            BigDecimal subtotal,
            BigDecimal shipping,
            PaymentStatus paymentStatus,
            OrderStatus orderStatus
    ) {
        Order {
            Objects.requireNonNull(subtotal);
            Objects.requireNonNull(shipping);
            Objects.requireNonNull(paymentStatus);
            Objects.requireNonNull(orderStatus);

            if (id <= 0 || customerId <= 0) {
                throw new IllegalArgumentException(
                        "Order and customer IDs must be positive"
                );
            }

            if (subtotal.signum() < 0 || shipping.signum() < 0) {
                throw new IllegalArgumentException(
                        "Order monetary values cannot be negative"
                );
            }
        }

        BigDecimal gross() {
            return subtotal.add(shipping);
        }
    }

    record Decision(
            String customerSegment,
            String paymentLabel,
            String shipmentPriority,
            BigDecimal discountRate,
            BigDecimal gross,
            BigDecimal discount,
            BigDecimal net
    ) {}

    static final class BusinessRuleService {

        /*
         * This method is structurally equivalent to a searched SQL CASE.
         * The order of conditions is part of the business rule: a suspended
         * customer must be restricted even if the monetary threshold would
         * otherwise classify the customer as platinum.
         */
        String classifyCustomer(Customer customer) {
            if (customer.accountStatus() == AccountStatus.SUSPENDED) {
                return "RESTRICTED";
            }

            if (customer.lifetimeValue().compareTo(
                    new BigDecimal("100000")) >= 0) {
                return "PLATINUM";
            }

            if (customer.lifetimeValue().compareTo(
                    new BigDecimal("50000")) >= 0) {
                return "GOLD";
            }

            if (customer.lifetimeValue().compareTo(
                    new BigDecimal("10000")) >= 0) {
                return "SILVER";
            }

            return "STANDARD";
        }

        /*
         * A Java switch is useful for an exact status-to-label mapping.
         * This corresponds conceptually to SQL's simple CASE:
         *
         * CASE payment_status
         *   WHEN 'PAID' THEN 'SETTLED'
         *   ...
         * END
         */
        String paymentLabel(PaymentStatus status) {
            return switch (status) {
                case PAID -> "SETTLED";
                case PENDING -> "AWAITING PAYMENT";
                case FAILED -> "PAYMENT FAILED";
                case REFUNDED -> "REFUNDED";
            };
        }

        String shipmentPriority(Order order) {
            if (order.orderStatus() == OrderStatus.CANCELLED) {
                return "DO NOT SHIP";
            }

            if (order.paymentStatus() != PaymentStatus.PAID) {
                return "HOLD";
            }

            BigDecimal gross = order.gross();

            if (gross.compareTo(new BigDecimal("10000")) >= 0) {
                return "URGENT";
            }

            if (gross.compareTo(new BigDecimal("5000")) >= 0) {
                return "HIGH";
            }

            return "NORMAL";
        }

        BigDecimal discountRate(Customer customer, Order order) {
            if (order.paymentStatus() != PaymentStatus.PAID) {
                return BigDecimal.ZERO;
            }

            if (customer.accountStatus() == AccountStatus.SUSPENDED) {
                return BigDecimal.ZERO;
            }

            BigDecimal gross = order.gross();

            if (customer.lifetimeValue().compareTo(
                    new BigDecimal("100000")) >= 0
                    && gross.compareTo(new BigDecimal("5000")) >= 0) {
                return new BigDecimal("0.15");
            }

            if (customer.lifetimeValue().compareTo(
                    new BigDecimal("50000")) >= 0) {
                return new BigDecimal("0.10");
            }

            if (gross.compareTo(new BigDecimal("10000")) >= 0) {
                return new BigDecimal("0.08");
            }

            if (gross.compareTo(new BigDecimal("5000")) >= 0) {
                return new BigDecimal("0.05");
            }

            return BigDecimal.ZERO;
        }

        Decision evaluate(Customer customer, Order order) {
            if (customer == null) {
                throw new IllegalArgumentException(
                        "Order references an unknown customer"
                );
            }

            BigDecimal gross = order.gross();
            BigDecimal rate = discountRate(customer, order);

            BigDecimal discount = gross
                    .multiply(rate)
                    .setScale(2, RoundingMode.HALF_UP);

            BigDecimal net = gross
                    .subtract(discount)
                    .setScale(2, RoundingMode.HALF_UP);

            return new Decision(
                    classifyCustomer(customer),
                    paymentLabel(order.paymentStatus()),
                    shipmentPriority(order),
                    rate,
                    gross,
                    discount,
                    net
            );
        }
    }

    public static void main(String[] args) {
        List<Customer> customers = List.of(
                new Customer(
                        1,
                        "Aarav Labs",
                        "IN",
                        new BigDecimal("125000"),
                        AccountStatus.ACTIVE
                ),
                new Customer(
                        2,
                        "Northwind",
                        "US",
                        new BigDecimal("62000"),
                        AccountStatus.ACTIVE
                ),
                new Customer(
                        3,
                        "BerlinWorks",
                        "DE",
                        new BigDecimal("18000"),
                        AccountStatus.ACTIVE
                ),
                new Customer(
                        4,
                        "RiskAccount",
                        "US",
                        new BigDecimal("200000"),
                        AccountStatus.SUSPENDED
                )
        );

        List<Order> orders = List.of(
                new Order(
                        501, 1,
                        new BigDecimal("12000"),
                        new BigDecimal("250"),
                        PaymentStatus.PAID,
                        OrderStatus.CONFIRMED
                ),
                new Order(
                        502, 2,
                        new BigDecimal("7000"),
                        new BigDecimal("200"),
                        PaymentStatus.PENDING,
                        OrderStatus.CONFIRMED
                ),
                new Order(
                        503, 4,
                        new BigDecimal("15000"),
                        new BigDecimal("250"),
                        PaymentStatus.PAID,
                        OrderStatus.CONFIRMED
                )
        );

        Map<Long, Customer> customerIndex = customers.stream()
                .collect(java.util.stream.Collectors.toUnmodifiableMap(
                        Customer::id,
                        customer -> customer
                ));

        BusinessRuleService service = new BusinessRuleService();

        System.out.println("CASE business-logic enterprise model\n");

        for (Order order : orders) {
            Customer customer = customerIndex.get(order.customerId());
            Decision decision = service.evaluate(customer, order);

            System.out.println(
                    "Order " + order.id()
                            + " | Segment=" + decision.customerSegment()
                            + " | Payment=" + decision.paymentLabel()
                            + " | Shipment=" + decision.shipmentPriority()
                            + " | Gross=" + decision.gross()
                            + " | Discount=" + decision.discount()
                            + " | Net=" + decision.net()
            );
        }

        System.out.println("\nCASE implementation distinctions");
        System.out.println(
                "Searched CASE is appropriate when each WHEN contains a "
                        + "Boolean business condition."
        );
        System.out.println(
                "Simple CASE is appropriate when one expression is matched "
                        + "against known values."
        );
        System.out.println(
                "CASE returns a value. Database constraints remain responsible "
                        + "for structural integrity."
        );
        System.out.println(
                "For financial rules, DECIMAL/NUMERIC semantics are preferred "
                        + "over binary floating-point arithmetic."
        );
    }
}
