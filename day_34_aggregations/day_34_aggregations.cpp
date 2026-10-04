/*
 * Aggregation Governance Engine
 * ==============================
 *
 * C++17 technical case study:
 *
 * A regional operations platform receives sales events and must produce
 * reliable aggregate metrics for completed orders. The engine calculates
 * COUNT, SUM, AVG, MIN, and MAX while enforcing data-quality rules.
 *
 * The implementation demonstrates:
 *   - strongly typed records
 *   - aggregation state
 *   - GROUP BY-style partitioning
 *   - post-aggregation threshold filtering
 *   - validation and failure handling
 *   - exact monetary arithmetic using integer cents
 *   - single-pass aggregation
 *   - mergeable aggregate state for distributed processing
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic aggregations.cpp -o aggregations
 */

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

// -----------------------------------------------------------------------------
// Monetary representation
// -----------------------------------------------------------------------------

class Money {
public:
    explicit Money(std::int64_t cents = 0) : cents_(cents) {}

    std::int64_t cents() const {
        return cents_;
    }

    double asDecimal() const {
        return static_cast<double>(cents_) / 100.0;
    }

    Money operator+(const Money& other) const {
        return Money(cents_ + other.cents_);
    }

    Money& operator+=(const Money& other) {
        cents_ += other.cents_;
        return *this;
    }

    Money operator*(std::int64_t quantity) const {
        return Money(cents_ * quantity);
    }

    bool operator<(const Money& other) const {
        return cents_ < other.cents_;
    }

    bool operator>(const Money& other) const {
        return cents_ > other.cents_;
    }

    bool operator==(const Money& other) const {
        return cents_ == other.cents_;
    }

private:
    std::int64_t cents_;
};

std::ostream& operator<<(std::ostream& output, const Money& money) {
    output << std::fixed << std::setprecision(2) << money.asDecimal();
    return output;
}

// -----------------------------------------------------------------------------
// Order domain model
// -----------------------------------------------------------------------------

enum class OrderStatus {
    Completed,
    Pending,
    Cancelled
};

struct Order {
    std::int64_t id;
    std::string region;
    std::string category;
    std::int64_t quantity;
    Money unitPrice;
    OrderStatus status;

    Money revenue() const {
        return unitPrice * quantity;
    }
};

// -----------------------------------------------------------------------------
// Validation
// -----------------------------------------------------------------------------

void validateOrder(const Order& order) {
    if (order.id <= 0) {
        throw std::invalid_argument("order id must be positive");
    }

    if (order.quantity <= 0) {
        throw std::invalid_argument(
            "quantity must be positive for order " +
            std::to_string(order.id)
        );
    }

    if (order.unitPrice.cents() < 0) {
        throw std::invalid_argument(
            "unit price cannot be negative for order " +
            std::to_string(order.id)
        );
    }

    if (order.region.empty()) {
        throw std::invalid_argument(
            "region cannot be empty for order " +
            std::to_string(order.id)
        );
    }
}

// -----------------------------------------------------------------------------
// Aggregation state
// -----------------------------------------------------------------------------

struct AggregateState {
    std::uint64_t count = 0;
    std::uint64_t nonNullCount = 0;
    Money sum;
    std::optional<Money> minimum;
    std::optional<Money> maximum;

    void add(const std::optional<Money>& value) {
        ++count;

        if (!value.has_value()) {
            return;
        }

        ++nonNullCount;
        sum += value.value();

        if (!minimum.has_value() || value.value() < minimum.value()) {
            minimum = value.value();
        }

        if (!maximum.has_value() || value.value() > maximum.value()) {
            maximum = value.value();
        }
    }

    std::optional<double> average() const {
        if (nonNullCount == 0) {
            return std::nullopt;
        }

        return sum.asDecimal() /
               static_cast<double>(nonNullCount);
    }
};

// -----------------------------------------------------------------------------
// Mergeable aggregate state
// -----------------------------------------------------------------------------

AggregateState mergeAggregates(
    const AggregateState& left,
    const AggregateState& right
) {
    AggregateState result;

    result.count = left.count + right.count;
    result.nonNullCount =
        left.nonNullCount + right.nonNullCount;
    result.sum = left.sum + right.sum;

    if (left.minimum.has_value() && right.minimum.has_value()) {
        result.minimum = std::min(
            left.minimum.value(),
            right.minimum.value()
        );
    } else if (left.minimum.has_value()) {
        result.minimum = left.minimum;
    } else {
        result.minimum = right.minimum;
    }

    if (left.maximum.has_value() && right.maximum.has_value()) {
        result.maximum = std::max(
            left.maximum.value(),
            right.maximum.value()
        );
    } else if (left.maximum.has_value()) {
        result.maximum = left.maximum;
    } else {
        result.maximum = right.maximum;
    }

    return result;
}

// -----------------------------------------------------------------------------
// Repository-level aggregation engine
// -----------------------------------------------------------------------------

class SalesAggregationEngine {
public:
    void ingest(const Order& order) {
        validateOrder(order);

        ++allOrders_;

        // The business report is explicitly about completed orders. Pending
        // and cancelled records remain counted in the raw ingestion metric but
        // do not contaminate completed-sales aggregates.
        if (order.status != OrderStatus::Completed) {
            return;
        }

        aggregateAll_.add(order.revenue());

        regionAggregates_[order.region].add(order.revenue());
        categoryAggregates_[order.category].add(order.revenue());
    }

    std::uint64_t allOrderCount() const {
        return allOrders_;
    }

    const AggregateState& overall() const {
        return aggregateAll_;
    }

    const std::map<std::string, AggregateState>& byRegion() const {
        return regionAggregates_;
    }

    const std::map<std::string, AggregateState>& byCategory() const {
        return categoryAggregates_;
    }

private:
    std::uint64_t allOrders_ = 0;
    AggregateState aggregateAll_;
    std::map<std::string, AggregateState> regionAggregates_;
    std::map<std::string, AggregateState> categoryAggregates_;
};

// -----------------------------------------------------------------------------
// Reporting
// -----------------------------------------------------------------------------

void printAggregate(
    const std::string& label,
    const AggregateState& aggregate
) {
    std::cout << std::left << std::setw(12) << label
              << " COUNT=" << aggregate.count
              << " SUM=" << aggregate.sum;

    if (aggregate.average().has_value()) {
        std::cout << " AVG="
                  << std::fixed
                  << std::setprecision(2)
                  << aggregate.average().value();
    } else {
        std::cout << " AVG=NULL";
    }

    std::cout << " MIN=";

    if (aggregate.minimum.has_value()) {
        std::cout << aggregate.minimum.value();
    } else {
        std::cout << "NULL";
    }

    std::cout << " MAX=";

    if (aggregate.maximum.has_value()) {
        std::cout << aggregate.maximum.value();
    } else {
        std::cout << "NULL";
    }

    std::cout << '\n';
}

void printReport(const SalesAggregationEngine& engine) {
    std::cout << "\n=== Sales Aggregation Report ===\n";
    std::cout << "Raw orders received: "
              << engine.allOrderCount() << '\n';

    std::cout << "\nCompleted-order aggregates\n";
    printAggregate("ALL", engine.overall());

    std::cout << "\nRegion aggregates\n";
    for (const auto& [region, aggregate] : engine.byRegion()) {
        printAggregate(region, aggregate);
    }

    std::cout << "\nCategory aggregates\n";
    for (const auto& [category, aggregate] : engine.byCategory()) {
        printAggregate(category, aggregate);
    }
}

// -----------------------------------------------------------------------------
// HAVING-style filtering
// -----------------------------------------------------------------------------

void printHighRevenueRegions(
    const SalesAggregationEngine& engine,
    Money threshold
) {
    std::cout << "\n=== Regions Above Revenue Threshold ===\n";

    for (const auto& [region, aggregate] : engine.byRegion()) {
        // This condition is deliberately evaluated after aggregation. It is
        // equivalent in intent to HAVING SUM(revenue) >= threshold.
        if (aggregate.sum.cents() >= threshold.cents()) {
            std::cout << region
                      << " revenue=" << aggregate.sum
                      << '\n';
        }
    }
}

// -----------------------------------------------------------------------------
// Distributed aggregation simulation
// -----------------------------------------------------------------------------

AggregateState aggregatePartition(
    const std::vector<Order>& partition
) {
    AggregateState result;

    for (const Order& order : partition) {
        validateOrder(order);

        if (order.status == OrderStatus::Completed) {
            result.add(order.revenue());
        }
    }

    return result;
}

void demonstrateDistributedMerge(
    const std::vector<Order>& orders
) {
    std::cout << "\n=== Partition and Merge ===\n";

    if (orders.empty()) {
        std::cout << "No records to partition.\n";
        return;
    }

    const std::size_t midpoint = orders.size() / 2;

    std::vector<Order> first(
        orders.begin(),
        orders.begin() + static_cast<std::ptrdiff_t>(midpoint)
    );

    std::vector<Order> second(
        orders.begin() + static_cast<std::ptrdiff_t>(midpoint),
        orders.end()
    );

    AggregateState left = aggregatePartition(first);
    AggregateState right = aggregatePartition(second);
    AggregateState merged = mergeAggregates(left, right);

    printAggregate("PARTITION-A", left);
    printAggregate("PARTITION-B", right);
    printAggregate("MERGED", merged);
}

// -----------------------------------------------------------------------------
// Edge-case demonstrations
// -----------------------------------------------------------------------------

void demonstrateEmptyAggregate() {
    std::cout << "\n=== Empty Aggregate ===\n";

    AggregateState empty;

    printAggregate("EMPTY", empty);

    assert(empty.count == 0);
    assert(empty.nonNullCount == 0);
    assert(!empty.average().has_value());
    assert(!empty.minimum.has_value());
    assert(!empty.maximum.has_value());
}

void demonstrateValidationFailure() {
    std::cout << "\n=== Validation Failure ===\n";

    Order invalid{
        9999,
        "North",
        "Laptop",
        -3,
        Money(10000),
        OrderStatus::Completed
    };

    try {
        validateOrder(invalid);
        std::cout << "Unexpectedly accepted invalid order.\n";
    } catch (const std::exception& error) {
        std::cout << "Rejected invalid order: "
                  << error.what() << '\n';
    }
}

// -----------------------------------------------------------------------------
// Dataset
// -----------------------------------------------------------------------------

std::vector<Order> buildOrders() {
    return {
        {1001, "North", "Laptop", 2, Money(85000), OrderStatus::Completed},
        {1002, "North", "Phone", 3, Money(50000), OrderStatus::Completed},
        {1003, "West", "Monitor", 1, Money(30000), OrderStatus::Completed},
        {1004, "South", "Laptop", 1, Money(92000), OrderStatus::Cancelled},
        {1005, "North", "Keyboard", 4, Money(7500), OrderStatus::Completed},
        {1006, "East", "Phone", 2, Money(65000), OrderStatus::Completed},
        {1007, "West", "Laptop", 1, Money(110000), OrderStatus::Completed},
        {1008, "South", "Monitor", 2, Money(28000), OrderStatus::Completed},
        {1009, "East", "Keyboard", 5, Money(6000), OrderStatus::Pending},
        {1010, "North", "Monitor", 2, Money(32500), OrderStatus::Completed}
    };
}

// -----------------------------------------------------------------------------
// Correctness checks
// -----------------------------------------------------------------------------

void runChecks(const SalesAggregationEngine& engine) {
    const AggregateState& overall = engine.overall();

    assert(engine.allOrderCount() == 10);
    assert(overall.count == 8);
    assert(overall.sum == Money(690500));
    assert(overall.minimum == Money(30000));
    assert(overall.maximum == Money(170000));
    assert(overall.average().has_value());

    const double expectedAverage =
        6905.0 / 8.0;

    assert(
        std::abs(
            overall.average().value() - expectedAverage
        ) < 0.000001
    );

    std::cout << "\nAll C++ aggregation checks passed.\n";
}

// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

int main() {
    try {
        const std::vector<Order> orders = buildOrders();

        SalesAggregationEngine engine;

        // Every record enters the engine. Only completed records contribute
        // to the business-sales aggregates, making the filtering rule explicit.
        for (const Order& order : orders) {
            engine.ingest(order);
        }

        printReport(engine);

        printHighRevenueRegions(
            engine,
            Money(200000)
        );

        demonstrateDistributedMerge(orders);
        demonstrateEmptyAggregate();
        demonstrateValidationFailure();
        runChecks(engine);

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Aggregation engine failed: "
                  << error.what() << '\n';
        return 1;
    }
}
