#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

/*
 * Data Aggregation Engine for Enterprise Sales Analytics.
 *
 * Implements:
 * - Multi-dimensional grouping.
 * - Count, sum, average, minimum, maximum.
 * - Distinct counting.
 * - Conditional aggregation.
 * - Pivot and unpivot.
 * - Incremental aggregation.
 * - Revenue reconciliation.
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic data_aggregation.cpp -o aggregation
 */

enum class Status {
    Completed,
    Pending,
    Cancelled
};

enum class Operation {
    Count,
    Sum,
    Average,
    Minimum,
    Maximum,
    DistinctCount
};

std::string toString(Status status) {
    switch (status) {
        case Status::Completed: return "completed";
        case Status::Pending: return "pending";
        case Status::Cancelled: return "cancelled";
    }

    throw std::invalid_argument("Unknown status.");
}

struct Transaction {
    std::string id;
    std::string region;
    std::string category;
    std::string product;
    std::string salesperson;
    int quantity;
    long long unitPriceCents;
    Status status;
};

void validate(const Transaction& transaction) {
    if (
        transaction.id.empty() ||
        transaction.region.empty() ||
        transaction.category.empty() ||
        transaction.product.empty() ||
        transaction.salesperson.empty()
    ) {
        throw std::invalid_argument("Required text field is empty.");
    }

    if (transaction.quantity <= 0) {
        throw std::invalid_argument("Quantity must be positive.");
    }

    if (transaction.unitPriceCents < 0) {
        throw std::invalid_argument("Unit price cannot be negative.");
    }

    if (
        transaction.unitPriceCents >
        1000000000000LL / transaction.quantity
    ) {
        throw std::overflow_error("Transaction revenue exceeds limit.");
    }
}

long long revenue(const Transaction& transaction) {
    validate(transaction);
    return transaction.unitPriceCents * transaction.quantity;
}

std::string formatMoney(long long cents) {
    std::ostringstream output;
    output << std::fixed << std::setprecision(2)
           << static_cast<double>(cents) / 100.0;
    return output.str();
}

struct AggregateState {
    long long count = 0;
    long long quantity = 0;
    long long totalRevenue = 0;
    long long minimumRevenue = 0;
    long long maximumRevenue = 0;
    std::set<std::string> products;
    bool initialized = false;

    void add(const Transaction& transaction) {
        const long long amount = revenue(transaction);

        if (
            totalRevenue >
            9000000000000000000LL - amount
        ) {
            throw std::overflow_error("Aggregate revenue overflow.");
        }

        if (quantity >
            9000000000000000000LL - transaction.quantity) {
            throw std::overflow_error("Aggregate quantity overflow.");
        }

        if (!initialized) {
            minimumRevenue = amount;
            maximumRevenue = amount;
            initialized = true;
        } else {
            minimumRevenue = std::min(minimumRevenue, amount);
            maximumRevenue = std::max(maximumRevenue, amount);
        }

        ++count;
        quantity += transaction.quantity;
        totalRevenue += amount;
        products.insert(transaction.product);
    }

    double averageRevenue() const {
        if (count == 0) {
            return 0.0;
        }

        return static_cast<double>(totalRevenue) /
               static_cast<double>(count);
    }
};

using GroupKey = std::pair<std::string, std::string>;

class AggregationEngine {
private:
    std::vector<Transaction> transactions;

    static void validateUniqueIdentifiers(
        const std::vector<Transaction>& records
    ) {
        std::set<std::string> identifiers;

        for (const auto& record : records) {
            validate(record);

            if (!identifiers.insert(record.id).second) {
                throw std::invalid_argument(
                    "Duplicate transaction identifier: " + record.id
                );
            }
        }
    }

public:
    explicit AggregationEngine(
        std::vector<Transaction> records
    ) : transactions(std::move(records)) {
        validateUniqueIdentifiers(transactions);
    }

    std::map<GroupKey, AggregateState> groupByRegionCategory() const {
        std::map<GroupKey, AggregateState> groups;

        for (const auto& transaction : transactions) {
            groups[
                {transaction.region, transaction.category}
            ].add(transaction);
        }

        return groups;
    }

    std::map<std::string, AggregateState> groupByRegion() const {
        std::map<std::string, AggregateState> groups;

        for (const auto& transaction : transactions) {
            groups[transaction.region].add(transaction);
        }

        return groups;
    }

    std::map<std::string, AggregateState> conditionalAggregation(
        Status selectedStatus
    ) const {
        std::map<std::string, AggregateState> result;

        for (const auto& transaction : transactions) {
            if (transaction.status == selectedStatus) {
                result[transaction.region].add(transaction);
            }
        }

        return result;
    }

    std::map<std::string, std::map<std::string, long long>> pivot(
        Operation operation
    ) const {
        std::map<GroupKey, AggregateState> groups =
            groupByRegionCategory();

        std::map<
            std::string,
            std::map<std::string, long long>
        > result;

        for (const auto& [key, state] : groups) {
            long long value = 0;

            switch (operation) {
                case Operation::Count:
                    value = state.count;
                    break;

                case Operation::Sum:
                    value = state.totalRevenue;
                    break;

                case Operation::Average:
                    value = static_cast<long long>(
                        std::llround(state.averageRevenue())
                    );
                    break;

                case Operation::Minimum:
                    value = state.minimumRevenue;
                    break;

                case Operation::Maximum:
                    value = state.maximumRevenue;
                    break;

                case Operation::DistinctCount:
                    value = static_cast<long long>(
                        state.products.size()
                    );
                    break;
            }

            result[key.first][key.second] = value;
        }

        return result;
    }

    std::vector<std::tuple<std::string, std::string, long long>>
    unpivot(
        const std::map<
            std::string,
            std::map<std::string, long long>
        >& table
    ) const {
        std::vector<
            std::tuple<std::string, std::string, long long>
        > result;

        for (const auto& [row, columns] : table) {
            for (const auto& [column, value] : columns) {
                result.emplace_back(row, column, value);
            }
        }

        return result;
    }

    long long totalRevenue() const {
        long long total = 0;

        for (const auto& transaction : transactions) {
            const long long amount = revenue(transaction);

            if (total > 9000000000000000000LL - amount) {
                throw std::overflow_error("Total revenue overflow.");
            }

            total += amount;
        }

        return total;
    }

    std::size_t size() const {
        return transactions.size();
    }
};

class StreamingAggregator {
private:
    std::map<std::string, AggregateState> groups;
    std::set<std::string> processedIdentifiers;

public:
    void process(const Transaction& transaction) {
        validate(transaction);

        if (!processedIdentifiers.insert(transaction.id).second) {
            throw std::invalid_argument("Duplicate streaming event.");
        }

        try {
            groups[transaction.region].add(transaction);
        } catch (...) {
            processedIdentifiers.erase(transaction.id);
            throw;
        }
    }

    const std::map<std::string, AggregateState>& snapshot() const {
        return groups;
    }
};

std::vector<Transaction> sampleData() {
    return {
        {"T001", "North", "Electronics", "Laptop", "Asha", 2, 6500000, Status::Completed},
        {"T002", "North", "Electronics", "Phone", "Asha", 3, 2500000, Status::Completed},
        {"T003", "South", "Furniture", "Chair", "Ravi", 5, 300000, Status::Completed},
        {"T004", "South", "Electronics", "Laptop", "Ravi", 1, 6500000, Status::Pending},
        {"T005", "East", "Furniture", "Table", "Neha", 2, 1200000, Status::Completed},
        {"T006", "East", "Electronics", "Phone", "Neha", 4, 2500000, Status::Cancelled},
        {"T007", "West", "Furniture", "Chair", "Arun", 3, 300000, Status::Completed},
        {"T008", "West", "Electronics", "Laptop", "Arun", 2, 6500000, Status::Completed},
        {"T009", "North", "Furniture", "Table", "Asha", 1, 1200000, Status::Pending},
        {"T010", "South", "Furniture", "Chair", "Ravi", 2, 300000, Status::Completed}
    };
}

void printGroups(
    const std::map<GroupKey, AggregateState>& groups
) {
    for (const auto& [key, state] : groups) {
        std::cout
            << key.first << " / " << key.second
            << " | count=" << state.count
            << " | quantity=" << state.quantity
            << " | revenue=" << formatMoney(state.totalRevenue)
            << " | average=" << formatMoney(
                static_cast<long long>(std::llround(
                    state.averageRevenue()
                ))
            )
            << " | distinct products=" << state.products.size()
            << '\n';
    }
}

int main() {
    try {
        AggregationEngine engine(sampleData());

        std::cout << "1. Grouping by region and category\n";
        auto groups = engine.groupByRegionCategory();
        printGroups(groups);

        std::cout << "\n2. Regional aggregation\n";

        for (const auto& [region, state] : engine.groupByRegion()) {
            std::cout
                << region
                << " | count=" << state.count
                << " | revenue=" << formatMoney(state.totalRevenue)
                << '\n';
        }

        std::cout << "\n3. Conditional aggregation: completed\n";

        for (const auto& [region, state] :
             engine.conditionalAggregation(Status::Completed)) {
            std::cout
                << region
                << " | completed revenue="
                << formatMoney(state.totalRevenue)
                << '\n';
        }

        std::cout << "\n4. Pivot: revenue by region and category\n";

        auto pivot = engine.pivot(Operation::Sum);

        for (const auto& [region, columns] : pivot) {
            std::cout << region << '\n';

            for (const auto& [category, value] : columns) {
                std::cout
                    << "  " << category
                    << " = " << formatMoney(value)
                    << '\n';
            }
        }

        std::cout << "\n5. Unpivot\n";

        for (const auto& [region, category, value] :
             engine.unpivot(pivot)) {
            std::cout
                << region << " | "
                << category << " | "
                << formatMoney(value) << '\n';
        }

        std::cout << "\n6. Streaming aggregation\n";

        StreamingAggregator stream;

        for (const auto& transaction : sampleData()) {
            stream.process(transaction);
        }

        for (const auto& [region, state] : stream.snapshot()) {
            std::cout
                << region << " | "
                << state.count << " transactions | "
                << formatMoney(state.totalRevenue) << '\n';
        }

        std::cout << "\n7. Reconciliation\n";

        long long groupedTotal = 0;

        for (const auto& [key, state] : groups) {
            (void)key;
            groupedTotal += state.totalRevenue;
        }

        assert(groupedTotal == engine.totalRevenue());
        assert(engine.size() == 10);

        std::cout
            << "Original revenue: "
            << formatMoney(engine.totalRevenue())
            << '\n';

        std::cout << "Grouped revenue matches source revenue.\n";

        std::cout << "\n8. Failure handling\n";

        try {
            Transaction invalid = sampleData()[0];
            invalid.quantity = -5;
            validate(invalid);
        } catch (const std::exception& error) {
            std::cout << "Rejected: " << error.what() << '\n';
        }

        try {
            StreamingAggregator duplicateStream;
            duplicateStream.process(sampleData()[0]);
            duplicateStream.process(sampleData()[0]);
        } catch (const std::exception& error) {
            std::cout << "Duplicate rejected: "
                      << error.what() << '\n';
        }

        std::cout << "\nAll aggregation checks completed.\n";

    } catch (const std::exception& error) {
        std::cerr << "Aggregation failure: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
