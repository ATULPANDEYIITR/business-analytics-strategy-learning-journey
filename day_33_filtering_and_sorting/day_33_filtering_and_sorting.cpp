#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

/*
    Business Data Governance and Query Engine
    -----------------------------------------

    Technical case study:

    A regional sales organization maintains an order table and needs a
    deterministic reporting engine. Analysts must be able to:

    - filter orders by business conditions
    - combine predicates
    - handle missing values explicitly
    - sort by multiple business fields
    - paginate deterministic results
    - calculate regional totals
    - validate records before reporting

    The implementation deliberately separates:
    - filtering: deciding which records qualify
    - sorting: deciding how qualifying records are ordered
    - pagination: selecting a window from the ordered result
    - aggregation: calculating business metrics from the selected dataset

    Compile:
        g++ -std=c++17 -O2 business_filter_sort.cpp -o business_filter_sort
*/

using namespace std;


// -----------------------------------------------------------------------------
// Domain model
// -----------------------------------------------------------------------------

enum class OrderStatus {
    Pending,
    Processing,
    Shipped,
    Cancelled
};

enum class Priority {
    Low,
    Medium,
    High
};

struct Order {
    int orderId;
    int customerId;
    string salesRep;
    string region;
    string category;
    double orderValue;
    OrderStatus status;
    string orderDate;
    Priority priority;
    double discountRate;
    optional<double> customerCreditLimit;
};


// -----------------------------------------------------------------------------
// Conversion helpers
// -----------------------------------------------------------------------------

string statusToString(OrderStatus status) {
    switch (status) {
        case OrderStatus::Pending:
            return "Pending";
        case OrderStatus::Processing:
            return "Processing";
        case OrderStatus::Shipped:
            return "Shipped";
        case OrderStatus::Cancelled:
            return "Cancelled";
    }

    return "Unknown";
}

string priorityToString(Priority priority) {
    switch (priority) {
        case Priority::Low:
            return "Low";
        case Priority::Medium:
            return "Medium";
        case Priority::High:
            return "High";
    }

    return "Unknown";
}

int priorityRank(Priority priority) {
    switch (priority) {
        case Priority::Low:
            return 1;
        case Priority::Medium:
            return 2;
        case Priority::High:
            return 3;
    }

    return 0;
}


// -----------------------------------------------------------------------------
// Sample operational dataset
// -----------------------------------------------------------------------------

vector<Order> loadOrders() {
    return {
        {5001, 101, "Anita", "North", "Cloud", 245000,
         OrderStatus::Shipped, "2026-09-03", Priority::High, 0.05, 2000000},

        {5002, 102, "Rahul", "West", "Security", 185000,
         OrderStatus::Pending, "2026-09-04", Priority::Medium, 0.02, 750000},

        {5003, 103, "Meera", "South", "Analytics", 72000,
         OrderStatus::Shipped, "2026-09-05", Priority::Low, 0.00, 200000},

        {5004, 104, "Vikram", "East", "Cloud", 310000,
         OrderStatus::Cancelled, "2026-09-06", Priority::High, 0.10, 1500000},

        {5005, 105, "Anita", "North", "Security", 126000,
         OrderStatus::Processing, "2026-09-08", Priority::High, 0.03, 600000},

        {5006, 106, "Rahul", "West", "Cloud", 455000,
         OrderStatus::Shipped, "2026-09-09", Priority::High, 0.07, 2500000},

        {5007, 107, "Vikram", "East", "Analytics", 64000,
         OrderStatus::Pending, "2026-09-10", Priority::Low, 0.00, nullopt},

        {5008, 108, "Meera", "South", "Security", 198000,
         OrderStatus::Shipped, "2026-09-11", Priority::Medium, 0.04, 500000},

        {5009, 101, "Anita", "North", "Analytics", 175000,
         OrderStatus::Processing, "2026-09-12", Priority::Medium, 0.02, 2000000},

        {5010, 102, "Rahul", "West", "Cloud", 225000,
         OrderStatus::Shipped, "2026-09-13", Priority::High, 0.05, 750000},

        {5011, 103, "Meera", "South", "Security", 91000,
         OrderStatus::Pending, "2026-09-15", Priority::Low, 0.01, 200000},

        {5012, 106, "Rahul", "West", "Security", 275000,
         OrderStatus::Processing, "2026-09-16", Priority::High, 0.06, 2500000}
    };
}


// -----------------------------------------------------------------------------
// Predicate model
// -----------------------------------------------------------------------------

using Predicate = function<bool(const Order&)>;

Predicate hasStatus(OrderStatus expected) {
    return [expected](const Order& order) {
        return order.status == expected;
    };
}

Predicate hasRegion(const string& expected) {
    return [expected](const Order& order) {
        return order.region == expected;
    };
}

Predicate hasCategory(const string& expected) {
    return [expected](const Order& order) {
        return order.category == expected;
    };
}

Predicate valueAbove(double threshold) {
    return [threshold](const Order& order) {
        return order.orderValue > threshold;
    };
}

Predicate valueAtLeast(double threshold) {
    return [threshold](const Order& order) {
        return order.orderValue >= threshold;
    };
}

Predicate priorityAtLeast(Priority minimum) {
    return [minimum](const Order& order) {
        return priorityRank(order.priority) >= priorityRank(minimum);
    };
}

Predicate creditLimitKnown() {
    return [](const Order& order) {
        return order.customerCreditLimit.has_value();
    };
}

Predicate creditLimitAbove(double threshold) {
    return [threshold](const Order& order) {
        return order.customerCreditLimit.has_value() &&
               *order.customerCreditLimit > threshold;
    };
}

Predicate allOf(initializer_list<Predicate> predicates) {
    return [predicates](const Order& order) {
        for (const auto& predicate : predicates) {
            if (!predicate(order)) {
                return false;
            }
        }

        return true;
    };
}

Predicate anyOf(initializer_list<Predicate> predicates) {
    return [predicates](const Order& order) {
        for (const auto& predicate : predicates) {
            if (predicate(order)) {
                return true;
            }
        }

        return false;
    };
}

Predicate negate(Predicate predicate) {
    return [predicate](const Order& order) {
        return !predicate(order);
    };
}


// -----------------------------------------------------------------------------
// Filtering engine
// -----------------------------------------------------------------------------

vector<Order> filterOrders(
    const vector<Order>& orders,
    const Predicate& predicate
) {
    vector<Order> result;
    result.reserve(orders.size());

    for (const auto& order : orders) {
        if (predicate(order)) {
            result.push_back(order);
        }
    }

    return result;
}


// -----------------------------------------------------------------------------
// ORDER BY model
// -----------------------------------------------------------------------------

enum class SortDirection {
    Ascending,
    Descending
};

struct SortRule {
    function<int(const Order&, const Order&)> compare;
};

int compareString(
    const string& left,
    const string& right,
    SortDirection direction
) {
    if (left == right) {
        return 0;
    }

    int result = left < right ? -1 : 1;

    return direction == SortDirection::Descending ? -result : result;
}

int compareDouble(
    double left,
    double right,
    SortDirection direction
) {
    if (fabs(left - right) < 1e-9) {
        return 0;
    }

    int result = left < right ? -1 : 1;

    return direction == SortDirection::Descending ? -result : result;
}

SortRule sortByRegion(SortDirection direction) {
    return {
        [direction](const Order& left, const Order& right) {
            return compareString(left.region, right.region, direction);
        }
    };
}

SortRule sortByValue(SortDirection direction) {
    return {
        [direction](const Order& left, const Order& right) {
            return compareDouble(
                left.orderValue,
                right.orderValue,
                direction
            );
        }
    };
}

SortRule sortByDate(SortDirection direction) {
    return {
        [direction](const Order& left, const Order& right) {
            // ISO-8601 dates in YYYY-MM-DD format sort lexicographically
            // in chronological order, so no date library is required here.
            return compareString(
                left.orderDate,
                right.orderDate,
                direction
            );
        }
    };
}

SortRule sortByPriority(SortDirection direction) {
    return {
        [direction](const Order& left, const Order& right) {
            return compareDouble(
                static_cast<double>(priorityRank(left.priority)),
                static_cast<double>(priorityRank(right.priority)),
                direction
            );
        }
    };
}

SortRule sortByOrderId(SortDirection direction) {
    return {
        [direction](const Order& left, const Order& right) {
            return compareDouble(
                static_cast<double>(left.orderId),
                static_cast<double>(right.orderId),
                direction
            );
        }
    };
}


// -----------------------------------------------------------------------------
// Query engine
// -----------------------------------------------------------------------------

class QueryEngine {
private:
    vector<Order> source;
    vector<Predicate> predicates;
    vector<SortRule> sortRules;

public:
    explicit QueryEngine(vector<Order> orders)
        : source(move(orders)) {}

    QueryEngine& where(Predicate predicate) {
        predicates.push_back(move(predicate));
        return *this;
    }

    QueryEngine& orderBy(SortRule rule) {
        sortRules.push_back(move(rule));
        return *this;
    }

    vector<Order> execute() const {
        vector<Order> result = source;

        // WHERE conditions are evaluated before ORDER BY. This mirrors the
        // logical purpose of a database query and reduces sorting work when
        // the predicate is selective.
        for (const auto& predicate : predicates) {
            result = filterOrders(result, predicate);
        }

        if (!sortRules.empty()) {
            stable_sort(
                result.begin(),
                result.end(),
                [this](const Order& left, const Order& right) {
                    for (const auto& rule : sortRules) {
                        int comparison = rule.compare(left, right);

                        if (comparison < 0) {
                            return true;
                        }

                        if (comparison > 0) {
                            return false;
                        }
                    }

                    return false;
                }
            );
        }

        return result;
    }

    vector<Order> executePage(
        size_t offset,
        size_t limit
    ) const {
        vector<Order> ordered = execute();

        if (offset >= ordered.size()) {
            return {};
        }

        size_t end = min(offset + limit, ordered.size());

        return vector<Order>(
            ordered.begin() + static_cast<long>(offset),
            ordered.begin() + static_cast<long>(end)
        );
    }
};


// -----------------------------------------------------------------------------
// Validation
// -----------------------------------------------------------------------------

vector<string> validateOrders(const vector<Order>& orders) {
    vector<string> errors;

    for (const auto& order : orders) {
        if (order.orderValue < 0) {
            errors.push_back(
                "Order " + to_string(order.orderId) +
                " has a negative order value."
            );
        }

        if (order.discountRate < 0.0 || order.discountRate > 1.0) {
            errors.push_back(
                "Order " + to_string(order.orderId) +
                " has an invalid discount rate."
            );
        }
    }

    return errors;
}


// -----------------------------------------------------------------------------
// Business reporting
// -----------------------------------------------------------------------------

map<string, double> totalByRegion(
    const vector<Order>& orders
) {
    map<string, double> totals;

    for (const auto& order : orders) {
        totals[order.region] += order.orderValue;
    }

    return totals;
}

double totalOrderValue(const vector<Order>& orders) {
    double total = 0.0;

    for (const auto& order : orders) {
        total += order.orderValue;
    }

    return total;
}

double averageOrderValue(const vector<Order>& orders) {
    if (orders.empty()) {
        return 0.0;
    }

    return totalOrderValue(orders) /
           static_cast<double>(orders.size());
}


// -----------------------------------------------------------------------------
// Presentation
// -----------------------------------------------------------------------------

void printTitle(const string& title) {
    cout << "\n"
         << string(78, '=')
         << "\n"
         << title
         << "\n"
         << string(78, '=')
         << "\n";
}

void printOrders(const vector<Order>& orders) {
    if (orders.empty()) {
        cout << "(no rows)\n";
        return;
    }

    cout << left
         << setw(8) << "ID"
         << setw(10) << "Region"
         << setw(12) << "Category"
         << setw(14) << "Value"
         << setw(14) << "Status"
         << setw(10) << "Priority"
         << setw(13) << "Date"
         << "\n";

    cout << string(81, '-') << "\n";

    cout << fixed << setprecision(2);

    for (const auto& order : orders) {
        cout << left
             << setw(8) << order.orderId
             << setw(10) << order.region
             << setw(12) << order.category
             << setw(14) << order.orderValue
             << setw(14) << statusToString(order.status)
             << setw(10) << priorityToString(order.priority)
             << setw(13) << order.orderDate
             << "\n";
    }
}


// -----------------------------------------------------------------------------
// Case study workflows
// -----------------------------------------------------------------------------

void highValueWestRegionReport(
    const vector<Order>& orders
) {
    printTitle("Case Study: High-value West-region pipeline");

    QueryEngine engine(orders);

    vector<Order> result = engine
        .where(hasRegion("West"))
        .where(valueAtLeast(200000))
        .where(negate(hasStatus(OrderStatus::Cancelled)))
        .orderBy(sortByValue(SortDirection::Descending))
        .orderBy(sortByDate(SortDirection::Ascending))
        .orderBy(sortByOrderId(SortDirection::Ascending))
        .execute();

    cout << "\nBusiness rule:\n"
         << "West region AND value >= 200K AND not cancelled.\n"
         << "Sort by value descending, date ascending, then order ID.\n\n";

    printOrders(result);

    cout << "\nQualified order count: "
         << result.size()
         << "\n";

    cout << "Qualified order value: "
         << totalOrderValue(result)
         << "\n";
}

void operationalPriorityQueue(
    const vector<Order>& orders
) {
    printTitle("Case Study: Operations queue");

    QueryEngine engine(orders);

    vector<Order> result = engine
        .where(
            allOf({
                anyOf({
                    hasStatus(OrderStatus::Pending),
                    hasStatus(OrderStatus::Processing)
                }),
                priorityAtLeast(Priority::Medium)
            })
        )
        .orderBy(sortByPriority(SortDirection::Descending))
        .orderBy(sortByDate(SortDirection::Ascending))
        .orderBy(sortByOrderId(SortDirection::Ascending))
        .execute();

    cout << "\nPending or processing orders requiring at least medium priority:\n\n";

    printOrders(result);
}

void creditRiskReport(
    const vector<Order>& orders
) {
    printTitle("Case Study: Credit-risk filtering");

    QueryEngine engine(orders);

    vector<Order> result = engine
        .where(creditLimitKnown())
        .where(creditLimitAbove(1000000))
        .where(valueAtLeast(250000))
        .where(negate(hasStatus(OrderStatus::Cancelled)))
        .orderBy(sortByValue(SortDirection::Descending))
        .orderBy(sortByOrderId(SortDirection::Ascending))
        .execute();

    cout << "\nOrders from customers with known credit limit > 1M "
         << "and order value >= 250K:\n\n";

    printOrders(result);
}

void regionalReport(
    const vector<Order>& orders
) {
    printTitle("Case Study: Regional sales report");

    QueryEngine engine(orders);

    vector<Order> result = engine
        .where(negate(hasStatus(OrderStatus::Cancelled)))
        .where(valueAtLeast(100000))
        .execute();

    map<string, double> totals = totalByRegion(result);

    cout << "\nNon-cancelled orders of at least 100K:\n\n";

    for (const auto& [region, value] : totals) {
        cout << left
             << setw(10) << region
             << fixed << setprecision(2)
             << value
             << "\n";
    }

    cout << "\nAverage qualifying order: "
         << averageOrderValue(result)
         << "\n";
}

void paginatedReport(
    const vector<Order>& orders
) {
    printTitle("Case Study: Deterministic pagination");

    QueryEngine engine(orders);

    engine
        .where(negate(hasStatus(OrderStatus::Cancelled)))
        .orderBy(sortByValue(SortDirection::Descending))
        .orderBy(sortByOrderId(SortDirection::Ascending));

    vector<Order> firstPage = engine.executePage(0, 4);
    vector<Order> secondPage = engine.executePage(4, 4);

    cout << "\nFirst page:\n";
    printOrders(firstPage);

    cout << "\nSecond page:\n";
    printOrders(secondPage);

    cout << "\nThe order ID is a final tie-breaker so equal-value rows "
         << "have deterministic positions across repeated report runs.\n";
}


// -----------------------------------------------------------------------------
// Performance discussion represented as executable metadata
// -----------------------------------------------------------------------------

void printPerformanceCharacteristics() {
    printTitle("Performance characteristics");

    cout << "Filtering a vector requires O(n) predicate evaluations.\n";
    cout << "Sorting m retained rows costs approximately O(m log m).\n";
    cout << "Filtering before sorting can reduce m when the predicate is selective.\n";
    cout << "stable_sort preserves relative order when all explicit sort rules tie.\n";
    cout << "A production database can avoid full scans through indexes and "
            "query-planning strategies.\n";
}


// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

int main() {
    try {
        vector<Order> orders = loadOrders();

        vector<string> validationErrors = validateOrders(orders);

        printTitle("Data validation");

        if (validationErrors.empty()) {
            cout << "All sample orders passed validation.\n";
        } else {
            for (const auto& error : validationErrors) {
                cout << error << "\n";
            }

            return 1;
        }

        highValueWestRegionReport(orders);
        operationalPriorityQueue(orders);
        creditRiskReport(orders);
        regionalReport(orders);
        paginatedReport(orders);
        printPerformanceCharacteristics();

        printTitle("Business filtering and sorting case study complete");

        return 0;
    }
    catch (const exception& error) {
        cerr << "Execution failed: " << error.what() << "\n";
        return 1;
    }
}
