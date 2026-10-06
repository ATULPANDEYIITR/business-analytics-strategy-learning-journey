#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * Repository-independent technical case study:
 *
 * A subscription business needs a deterministic order decision engine.
 * The engine mirrors SQL CASE rules for customer segmentation, payment
 * classification, shipment priority, and discounts.
 *
 * The important SQL distinction is that CASE is an expression. It produces
 * a value from conditions; it does not replace constraints, transactions,
 * or relational integrity.
 */

enum class AccountStatus {
    Active,
    Suspended
};

enum class PaymentStatus {
    Paid,
    Pending,
    Failed,
    Refunded
};

enum class OrderStatus {
    Confirmed,
    Cancelled
};

struct Customer {
    int id;
    string name;
    string country;
    double lifetimeValue;
    AccountStatus status;
};

struct Order {
    int id;
    int customerId;
    double subtotal;
    double shipping;
    PaymentStatus payment;
    OrderStatus status;
};

string accountStatusText(AccountStatus status) {
    switch (status) {
        case AccountStatus::Active: return "active";
        case AccountStatus::Suspended: return "suspended";
    }
    return "unknown";
}

string paymentText(PaymentStatus status) {
    switch (status) {
        case PaymentStatus::Paid: return "SETTLED";
        case PaymentStatus::Pending: return "AWAITING PAYMENT";
        case PaymentStatus::Failed: return "PAYMENT FAILED";
        case PaymentStatus::Refunded: return "REFUNDED";
    }
    return "UNKNOWN";
}

string orderStatusText(OrderStatus status) {
    switch (status) {
        case OrderStatus::Confirmed: return "confirmed";
        case OrderStatus::Cancelled: return "cancelled";
    }
    return "unknown";
}

/*
 * This is a searched CASE equivalent:
 *
 * CASE
 *   WHEN status = 'suspended' THEN 'RESTRICTED'
 *   WHEN lifetime_value >= 100000 THEN 'PLATINUM'
 *   ...
 * END
 *
 * Ordering matters because SQL CASE stops at the first true WHEN.
 */
string customerSegment(const Customer& customer) {
    if (customer.status == AccountStatus::Suspended) {
        return "RESTRICTED";
    }
    if (customer.lifetimeValue >= 100000.0) {
        return "PLATINUM";
    }
    if (customer.lifetimeValue >= 50000.0) {
        return "GOLD";
    }
    if (customer.lifetimeValue >= 10000.0) {
        return "SILVER";
    }
    return "STANDARD";
}

string shippingPriority(const Order& order) {
    if (order.status == OrderStatus::Cancelled) {
        return "DO NOT SHIP";
    }

    if (order.payment != PaymentStatus::Paid) {
        return "HOLD";
    }

    const double total = order.subtotal + order.shipping;

    if (total >= 10000.0) {
        return "URGENT";
    }
    if (total >= 5000.0) {
        return "HIGH";
    }
    return "NORMAL";
}

double discountRate(const Customer& customer, const Order& order) {
    if (order.payment != PaymentStatus::Paid) {
        return 0.0;
    }

    if (customer.status == AccountStatus::Suspended) {
        return 0.0;
    }

    const double total = order.subtotal + order.shipping;

    if (customer.lifetimeValue >= 100000.0 && total >= 5000.0) {
        return 0.15;
    }
    if (customer.lifetimeValue >= 50000.0) {
        return 0.10;
    }
    if (total >= 10000.0) {
        return 0.08;
    }
    if (total >= 5000.0) {
        return 0.05;
    }
    return 0.0;
}

struct OrderDecision {
    string segment;
    string payment;
    string shipment;
    double gross;
    double discount;
    double net;
};

class GovernanceEngine {
public:
    explicit GovernanceEngine(vector<Customer> customers)
        : customers_(std::move(customers)) {}

    OrderDecision evaluate(const Order& order) const {
        const Customer* customer = findCustomer(order.customerId);

        if (customer == nullptr) {
            throw invalid_argument(
                "Order " + to_string(order.id) +
                " references an unknown customer"
            );
        }

        if (order.subtotal < 0.0 || order.shipping < 0.0) {
            throw invalid_argument(
                "Order " + to_string(order.id) +
                " contains a negative monetary value"
            );
        }

        const double gross = order.subtotal + order.shipping;
        const double rate = discountRate(*customer, order);
        const double discount = gross * rate;

        return {
            customerSegment(*customer),
            paymentText(order.payment),
            shippingPriority(order),
            gross,
            discount,
            gross - discount
        };
    }

private:
    const Customer* findCustomer(int id) const {
        auto iterator = find_if(
            customers_.begin(),
            customers_.end(),
            [id](const Customer& customer) {
                return customer.id == id;
            }
        );

        return iterator == customers_.end() ? nullptr : &(*iterator);
    }

    vector<Customer> customers_;
};

void printCaseDesign() {
    cout << "\nCASE design used by the SQL implementation\n";
    cout << "-------------------------------------------\n";
    cout << "Simple CASE compares one expression with multiple values.\n";
    cout << "Searched CASE evaluates independent Boolean conditions.\n";
    cout << "The first matching WHEN wins.\n";
    cout << "ELSE prevents unexpected NULL results when no branch matches.\n";
}

int main() {
    try {
        vector<Customer> customers{
            {1, "Aarav Labs", "IN", 125000.0, AccountStatus::Active},
            {2, "Northwind", "US", 62000.0, AccountStatus::Active},
            {3, "BerlinWorks", "DE", 18000.0, AccountStatus::Active},
            {4, "RiskAccount", "US", 200000.0, AccountStatus::Suspended}
        };

        vector<Order> orders{
            {501, 1, 12000.0, 250.0, PaymentStatus::Paid,
             OrderStatus::Confirmed},
            {502, 2, 7000.0, 200.0, PaymentStatus::Pending,
             OrderStatus::Confirmed},
            {503, 4, 15000.0, 250.0, PaymentStatus::Paid,
             OrderStatus::Confirmed},
            {504, 3, 4000.0, 100.0, PaymentStatus::Failed,
             OrderStatus::Cancelled}
        };

        GovernanceEngine engine(customers);

        cout << fixed << setprecision(2);
        cout << "SQL CASE business-rule case study\n\n";

        for (const auto& order : orders) {
            const OrderDecision decision = engine.evaluate(order);

            cout << "Order " << order.id << '\n'
                 << "  Segment:   " << decision.segment << '\n'
                 << "  Payment:   " << decision.payment << '\n'
                 << "  Shipment:  " << decision.shipment << '\n'
                 << "  Gross:     " << decision.gross << '\n'
                 << "  Discount:  " << decision.discount << '\n'
                 << "  Net:       " << decision.net << "\n\n";
        }

        printCaseDesign();

        cout << "\nRelational design implication\n";
        cout << "-----------------------------\n";
        cout << "A CASE expression can derive a category from stored data, but it "
                "does not enforce uniqueness or referential integrity.\n";
        cout << "Those guarantees belong to PRIMARY KEY, UNIQUE, FOREIGN KEY, "
                "CHECK, and related database mechanisms.\n";

    } catch (const exception& error) {
        cerr << "Business-rule evaluation failed: "
             << error.what() << '\n';
        return 1;
    }

    return 0;
}
