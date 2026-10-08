#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

/*
 * Technical case study:
 *
 * A retail analytics service needs to determine which customers, products,
 * and categories exceed analytical benchmarks. The implementation models
 * nested SQL-style reasoning explicitly:
 *
 *   base records -> intermediate relation -> aggregate benchmark -> filter
 *
 * The program intentionally uses C++ data structures and algorithms rather
 * than translating SQL syntax. This makes the distinction between an outer
 * operation and its inner analytical dependency visible in application code.
 */

struct Customer {
    int id;
    string name;
    string region;
    string tier;
};

struct Product {
    int id;
    string name;
    string category;
    double price;
};

enum class OrderStatus {
    Completed,
    Cancelled,
    Pending
};

struct Order {
    int id;
    int customerId;
    OrderStatus status;
};

struct OrderItem {
    int orderId;
    int productId;
    int quantity;
};

struct OrderTotal {
    int orderId;
    int customerId;
    double total;
};

struct CustomerRevenue {
    int customerId;
    string name;
    double revenue;
};

class RetailAnalytics {
private:
    vector<Customer> customers;
    vector<Product> products;
    vector<Order> orders;
    vector<OrderItem> items;

    const Customer& customerById(int id) const {
        auto it = find_if(
            customers.begin(),
            customers.end(),
            [id](const Customer& customer) {
                return customer.id == id;
            }
        );

        if (it == customers.end()) {
            throw runtime_error("Customer does not exist: " + to_string(id));
        }

        return *it;
    }

    const Product& productById(int id) const {
        auto it = find_if(
            products.begin(),
            products.end(),
            [id](const Product& product) {
                return product.id == id;
            }
        );

        if (it == products.end()) {
            throw runtime_error("Product does not exist: " + to_string(id));
        }

        return *it;
    }

    vector<const Order*> completedOrders() const {
        vector<const Order*> result;

        for (const auto& order : orders) {
            if (order.status == OrderStatus::Completed) {
                result.push_back(&order);
            }
        }

        return result;
    }

public:
    RetailAnalytics() {
        customers = {
            {1, "Aarav Mehta", "North", "Gold"},
            {2, "Diya Sharma", "North", "Silver"},
            {3, "Kabir Singh", "West", "Gold"},
            {4, "Meera Iyer", "South", "Standard"},
            {5, "Rohan Gupta", "West", "Silver"},
            {6, "Ananya Rao", "South", "Gold"},
            {7, "Vikram Joshi", "East", "Standard"},
            {8, "Sara Khan", "East", "Silver"}
        };

        products = {
            {1, "Laptop Pro", "Electronics", 1200.0},
            {2, "Mechanical Keyboard", "Electronics", 140.0},
            {3, "Office Chair", "Furniture", 350.0},
            {4, "Monitor 27", "Electronics", 420.0},
            {5, "Standing Desk", "Furniture", 650.0},
            {6, "USB-C Hub", "Accessories", 80.0},
            {7, "Webcam", "Accessories", 110.0}
        };

        orders = {
            {101, 1, OrderStatus::Completed},
            {102, 1, OrderStatus::Completed},
            {103, 2, OrderStatus::Completed},
            {104, 2, OrderStatus::Completed},
            {105, 3, OrderStatus::Completed},
            {106, 3, OrderStatus::Completed},
            {107, 3, OrderStatus::Completed},
            {108, 4, OrderStatus::Completed},
            {109, 4, OrderStatus::Cancelled},
            {110, 5, OrderStatus::Completed},
            {111, 5, OrderStatus::Completed},
            {112, 6, OrderStatus::Completed},
            {113, 6, OrderStatus::Completed},
            {114, 7, OrderStatus::Completed},
            {115, 8, OrderStatus::Pending}
        };

        items = {
            {101, 1, 1}, {101, 2, 1},
            {102, 4, 1}, {102, 6, 2},
            {103, 3, 1}, {103, 7, 1},
            {104, 2, 2}, {104, 6, 1},
            {105, 1, 1}, {105, 6, 1},
            {106, 5, 1}, {106, 4, 1},
            {107, 1, 1}, {107, 7, 2},
            {108, 3, 1}, {108, 6, 2},
            {109, 4, 1},
            {110, 5, 1}, {110, 2, 1},
            {111, 3, 2}, {111, 7, 1},
            {112, 1, 1}, {112, 4, 1},
            {113, 5, 1}, {113, 6, 2},
            {114, 2, 1}, {114, 7, 1},
            {115, 4, 1}
        };
    }

    /*
     * This function constructs the equivalent of a derived table:
     * every completed order becomes one intermediate analytical row.
     */
    vector<OrderTotal> completedOrderTotals() const {
        vector<OrderTotal> result;

        for (const Order* order : completedOrders()) {
            double total = 0.0;

            for (const auto& item : items) {
                if (item.orderId == order->id) {
                    const Product& product = productById(item.productId);
                    total += product.price * item.quantity;
                }
            }

            result.push_back({order->id, order->customerId, total});
        }

        return result;
    }

    /*
     * Scalar-subquery equivalent:
     * calculate a single global average and use it as the outer predicate.
     */
    vector<Product> productsAboveAveragePrice() const {
        if (products.empty()) {
            return {};
        }

        const double total = accumulate(
            products.begin(),
            products.end(),
            0.0,
            [](double sum, const Product& product) {
                return sum + product.price;
            }
        );

        const double averagePrice = total / products.size();

        vector<Product> result;

        copy_if(
            products.begin(),
            products.end(),
            back_inserter(result),
            [averagePrice](const Product& product) {
                return product.price > averagePrice;
            }
        );

        sort(
            result.begin(),
            result.end(),
            [](const Product& left, const Product& right) {
                return left.price > right.price;
            }
        );

        return result;
    }

    /*
     * Correlated-subquery equivalent:
     * each customer's outer row establishes the customer ID used by the
     * inner search for completed order totals.
     */
    vector<pair<string, double>> averageOrderValuePerCustomer() const {
        const auto orderTotals = completedOrderTotals();
        vector<pair<string, double>> result;

        for (const auto& customer : customers) {
            vector<double> customerTotals;

            for (const auto& orderTotal : orderTotals) {
                if (orderTotal.customerId == customer.id) {
                    customerTotals.push_back(orderTotal.total);
                }
            }

            if (!customerTotals.empty()) {
                const double total = accumulate(
                    customerTotals.begin(),
                    customerTotals.end(),
                    0.0
                );

                result.emplace_back(
                    customer.name,
                    total / customerTotals.size()
                );
            }
        }

        sort(
            result.begin(),
            result.end(),
            [](const auto& left, const auto& right) {
                return left.second > right.second;
            }
        );

        return result;
    }

    /*
     * Multi-level nesting:
     * completed order totals are first grouped into customer revenue.
     * Customer revenue then becomes the input to a second aggregate benchmark.
     */
    vector<CustomerRevenue> customersAboveAverageRevenue() const {
        const auto orderTotals = completedOrderTotals();
        vector<CustomerRevenue> customerRevenue;

        for (const auto& customer : customers) {
            double revenue = 0.0;

            for (const auto& orderTotal : orderTotals) {
                if (orderTotal.customerId == customer.id) {
                    revenue += orderTotal.total;
                }
            }

            if (revenue > 0.0) {
                customerRevenue.push_back({
                    customer.id,
                    customer.name,
                    revenue
                });
            }
        }

        if (customerRevenue.empty()) {
            return {};
        }

        const double totalRevenue = accumulate(
            customerRevenue.begin(),
            customerRevenue.end(),
            0.0,
            [](double sum, const CustomerRevenue& row) {
                return sum + row.revenue;
            }
        );

        const double averageRevenue =
            totalRevenue / customerRevenue.size();

        customerRevenue.erase(
            remove_if(
                customerRevenue.begin(),
                customerRevenue.end(),
                [averageRevenue](const CustomerRevenue& row) {
                    return row.revenue <= averageRevenue;
                }
            ),
            customerRevenue.end()
        );

        sort(
            customerRevenue.begin(),
            customerRevenue.end(),
            [](const CustomerRevenue& left, const CustomerRevenue& right) {
                return left.revenue > right.revenue;
            }
        );

        return customerRevenue;
    }

    /*
     * EXISTS-style analysis:
     * the outer customer is retained if at least one completed order contains
     * a furniture product. The matching item rows do not become duplicate
     * customer results.
     */
    vector<Customer> customersWhoBoughtFurniture() const {
        vector<Customer> result;

        for (const auto& customer : customers) {
            bool exists = false;

            for (const auto& order : orders) {
                if (order.customerId != customer.id ||
                    order.status != OrderStatus::Completed) {
                    continue;
                }

                for (const auto& item : items) {
                    if (item.orderId != order.id) {
                        continue;
                    }

                    if (productById(item.productId).category == "Furniture") {
                        exists = true;
                        break;
                    }
                }

                if (exists) {
                    break;
                }
            }

            if (exists) {
                result.push_back(customer);
            }
        }

        return result;
    }

    /*
     * Correlated top-per-group analysis:
     * a product is a category leader when no product in the same category has
     * a greater price. This directly models a NOT EXISTS-style condition.
     */
    vector<Product> mostExpensiveProductsPerCategory() const {
        vector<Product> result;

        for (const auto& candidate : products) {
            bool greaterProductExists = false;

            for (const auto& other : products) {
                if (other.category == candidate.category &&
                    other.price > candidate.price) {
                    greaterProductExists = true;
                    break;
                }
            }

            if (!greaterProductExists) {
                result.push_back(candidate);
            }
        }

        return result;
    }

    /*
     * Nested aggregation over category revenue.
     * The first layer calculates category totals, while the outer logic
     * computes the benchmark and filters categories above it.
     */
    vector<pair<string, double>> categoriesAboveAverageRevenue() const {
        map<string, double> revenueByCategory;

        for (const auto& order : orders) {
            if (order.status != OrderStatus::Completed) {
                continue;
            }

            for (const auto& item : items) {
                if (item.orderId != order.id) {
                    continue;
                }

                const Product& product = productById(item.productId);

                revenueByCategory[product.category] +=
                    product.price * item.quantity;
            }
        }

        if (revenueByCategory.empty()) {
            return {};
        }

        double total = 0.0;

        for (const auto& [category, revenue] : revenueByCategory) {
            total += revenue;
        }

        const double averageRevenue =
            total / revenueByCategory.size();

        vector<pair<string, double>> result;

        for (const auto& [category, revenue] : revenueByCategory) {
            if (revenue > averageRevenue) {
                result.emplace_back(category, revenue);
            }
        }

        sort(
            result.begin(),
            result.end(),
            [](const auto& left, const auto& right) {
                return left.second > right.second;
            }
        );

        return result;
    }

    /*
     * NOT EXISTS-style exclusion:
     * a customer must have a completed order but must not have any cancelled
     * order. This shows how positive and negative existence predicates combine.
     */
    vector<Customer> completedWithoutCancellation() const {
        vector<Customer> result;

        for (const auto& customer : customers) {
            bool completedExists = false;
            bool cancelledExists = false;

            for (const auto& order : orders) {
                if (order.customerId != customer.id) {
                    continue;
                }

                if (order.status == OrderStatus::Completed) {
                    completedExists = true;
                }

                if (order.status == OrderStatus::Cancelled) {
                    cancelledExists = true;
                }
            }

            if (completedExists && !cancelledExists) {
                result.push_back(customer);
            }
        }

        return result;
    }

    void printReport() const {
        cout << fixed << setprecision(2);

        cout << "\nProducts above overall average price\n";
        for (const auto& product : productsAboveAveragePrice()) {
            cout << "  " << product.name
                 << " | " << product.category
                 << " | $" << product.price << '\n';
        }

        cout << "\nAverage order value by customer\n";
        for (const auto& [name, average] : averageOrderValuePerCustomer()) {
            cout << "  " << name << " | $" << average << '\n';
        }

        cout << "\nCustomers above average revenue\n";
        for (const auto& row : customersAboveAverageRevenue()) {
            cout << "  " << row.name
                 << " | $" << row.revenue << '\n';
        }

        cout << "\nCustomers who bought furniture\n";
        for (const auto& customer : customersWhoBoughtFurniture()) {
            cout << "  " << customer.name << '\n';
        }

        cout << "\nMost expensive product per category\n";
        for (const auto& product : mostExpensiveProductsPerCategory()) {
            cout << "  " << product.category
                 << " | " << product.name
                 << " | $" << product.price << '\n';
        }

        cout << "\nCategories above average revenue\n";
        for (const auto& [category, revenue] : categoriesAboveAverageRevenue()) {
            cout << "  " << category
                 << " | $" << revenue << '\n';
        }

        cout << "\nCompleted orders with no cancellation for the customer\n";
        for (const auto& customer : completedWithoutCancellation()) {
            cout << "  " << customer.name
                 << " | " << customer.region << '\n';
        }
    }
};

int main() {
    try {
        RetailAnalytics analytics;
        analytics.printReport();
    } catch (const exception& error) {
        cerr << "Analytical processing failed: "
             << error.what() << '\n';
        return 1;
    }

    return 0;
}
