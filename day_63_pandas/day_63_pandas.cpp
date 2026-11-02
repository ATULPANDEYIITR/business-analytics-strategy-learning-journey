#include <algorithm>
#include <cassert>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

enum class Category {
    Electronics,
    Furniture,
    Accessories
};

struct SalesRecord {
    int orderId;
    std::string orderDate;
    std::string region;
    std::string product;
    Category category;
    int units;
    double unitPrice;
    double discount;
    std::string customer;
};

struct EnrichedRecord {
    SalesRecord source;
    double grossSales{};
    double discountAmount{};
    double netSales{};
    std::string month;
    bool highValue{};
};

struct Aggregate {
    std::string region;
    Category category;
    int orders{};
    int units{};
    double netSales{};
};

std::string categoryName(Category category) {
    switch (category) {
        case Category::Electronics: return "Electronics";
        case Category::Furniture: return "Furniture";
        case Category::Accessories: return "Accessories";
    }
    throw std::logic_error("Unknown category");
}

void validate(const std::vector<SalesRecord>& records) {
    if (records.empty()) {
        throw std::invalid_argument("Sales data cannot be empty");
    }

    std::set<int> orderIds;

    for (const auto& record : records) {
        if (!orderIds.insert(record.orderId).second) {
            throw std::invalid_argument("Duplicate order ID");
        }

        if (record.units <= 0) {
            throw std::invalid_argument("Units must be positive");
        }

        if (!std::isfinite(record.unitPrice) || record.unitPrice <= 0) {
            throw std::invalid_argument("Unit price must be positive");
        }

        if (!std::isfinite(record.discount) ||
            record.discount < 0 ||
            record.discount >= 1) {
            throw std::invalid_argument("Discount must be in [0, 1)");
        }

        if (record.region.empty() || record.customer.empty()) {
            throw std::invalid_argument("Region and customer are required");
        }
    }
}

std::string monthOf(const std::string& date) {
    if (date.size() < 7) {
        throw std::invalid_argument("Date must use YYYY-MM-DD");
    }
    return date.substr(0, 7);
}

std::vector<EnrichedRecord> enrich(
    const std::vector<SalesRecord>& records
) {
    std::vector<EnrichedRecord> result;
    result.reserve(records.size());

    for (const auto& record : records) {
        const double gross = record.units * record.unitPrice;
        const double discountAmount = gross * record.discount;
        const double net = gross - discountAmount;

        result.push_back({
            record,
            gross,
            discountAmount,
            net,
            monthOf(record.orderDate),
            net >= 100000.0
        });
    }

    return result;
}

std::vector<Aggregate> groupByRegionCategory(
    const std::vector<EnrichedRecord>& records
) {
    std::map<std::pair<std::string, Category>, Aggregate> groups;

    for (const auto& record : records) {
        auto key = std::make_pair(
            record.source.region,
            record.source.category
        );

        auto& aggregate = groups[key];
        aggregate.region = record.source.region;
        aggregate.category = record.source.category;
        aggregate.orders++;
        aggregate.units += record.source.units;
        aggregate.netSales += record.netSales;
    }

    std::vector<Aggregate> result;
    result.reserve(groups.size());

    for (const auto& [key, value] : groups) {
        result.push_back(value);
    }

    std::sort(
        result.begin(),
        result.end(),
        [](const Aggregate& left, const Aggregate& right) {
            return left.netSales > right.netSales;
        }
    );

    return result;
}

std::map<std::string, double> monthlyTotals(
    const std::vector<EnrichedRecord>& records
) {
    std::map<std::string, double> result;

    for (const auto& record : records) {
        result[record.month] += record.netSales;
    }

    return result;
}

std::vector<EnrichedRecord> filter(
    const std::vector<EnrichedRecord>& records,
    Category category,
    double minimumSales
) {
    std::vector<EnrichedRecord> result;

    std::copy_if(
        records.begin(),
        records.end(),
        std::back_inserter(result),
        [&](const EnrichedRecord& record) {
            return record.source.category == category &&
                   record.netSales >= minimumSales;
        }
    );

    std::sort(
        result.begin(),
        result.end(),
        [](const EnrichedRecord& left, const EnrichedRecord& right) {
            if (left.netSales != right.netSales) {
                return left.netSales > right.netSales;
            }
            return left.source.orderId < right.source.orderId;
        }
    );

    return result;
}

std::vector<double> rollingMean(
    const std::vector<EnrichedRecord>& records,
    std::size_t window
) {
    if (window == 0) {
        throw std::invalid_argument("Rolling window cannot be zero");
    }

    std::vector<EnrichedRecord> ordered = records;

    std::sort(
        ordered.begin(),
        ordered.end(),
        [](const EnrichedRecord& left, const EnrichedRecord& right) {
            return left.source.orderDate < right.source.orderDate;
        }
    );

    std::vector<double> result;
    result.reserve(ordered.size());

    double runningSum = 0.0;

    for (std::size_t i = 0; i < ordered.size(); ++i) {
        runningSum += ordered[i].netSales;

        if (i >= window) {
            runningSum -= ordered[i - window].netSales;
        }

        const std::size_t count = std::min(i + 1, window);
        result.push_back(runningSum / static_cast<double>(count));
    }

    return result;
}

void printMoney(double value) {
    std::cout << std::fixed << std::setprecision(2) << value;
}

int main() {
    try {
        const std::vector<SalesRecord> sales = {
            {1001, "2026-01-03", "North", "Laptop", Category::Electronics, 2, 75000, 0.05, "Apex Ltd"},
            {1002, "2026-01-05", "South", "Monitor", Category::Electronics, 4, 18000, 0.10, "Beta Corp"},
            {1003, "2026-01-08", "West", "Desk", Category::Furniture, 3, 12000, 0.00, "Gamma Pvt"},
            {1004, "2026-01-11", "North", "Chair", Category::Furniture, 10, 6500, 0.08, "Apex Ltd"},
            {1005, "2026-01-13", "East", "Laptop", Category::Electronics, 1, 82000, 0.05, "Delta Inc"},
            {1006, "2026-01-18", "South", "Desk", Category::Furniture, 2, 13500, 0.03, "Beta Corp"},
            {1007, "2026-01-20", "West", "Keyboard", Category::Accessories, 15, 2200, 0.00, "Gamma Pvt"},
            {1008, "2026-01-23", "East", "Monitor", Category::Electronics, 5, 19500, 0.12, "Delta Inc"},
            {1009, "2026-02-02", "North", "Laptop", Category::Electronics, 3, 76000, 0.04, "Apex Ltd"},
            {1010, "2026-02-04", "South", "Chair", Category::Furniture, 8, 6200, 0.06, "Beta Corp"},
            {1011, "2026-02-09", "West", "Monitor", Category::Electronics, 2, 18500, 0.02, "Gamma Pvt"},
            {1012, "2026-02-15", "East", "Keyboard", Category::Accessories, 20, 2100, 0.05, "Delta Inc"}
        };

        validate(sales);

        const auto enriched = enrich(sales);

        std::cout << "RECORDS: " << enriched.size() << "\n\n";

        std::cout << "ENRICHED SALES\n";
        for (const auto& record : enriched) {
            std::cout
                << record.source.orderId << " "
                << record.source.region << " "
                << record.source.product << " net=";
            printMoney(record.netSales);
            std::cout << "\n";
        }

        std::cout << "\nHIGH-VALUE ELECTRONICS\n";
        const auto selected = filter(
            enriched,
            Category::Electronics,
            50000.0
        );

        for (const auto& record : selected) {
            std::cout
                << record.source.orderId
                << " "
                << record.source.product
                << " ";
            printMoney(record.netSales);
            std::cout << "\n";
        }

        std::cout << "\nREGION/CATEGORY AGGREGATION\n";
        for (const auto& aggregate : groupByRegionCategory(enriched)) {
            std::cout
                << aggregate.region
                << " | "
                << categoryName(aggregate.category)
                << " | orders=" << aggregate.orders
                << " | units=" << aggregate.units
                << " | net=";
            printMoney(aggregate.netSales);
            std::cout << "\n";
        }

        std::cout << "\nMONTHLY TOTALS\n";
        for (const auto& [month, total] : monthlyTotals(enriched)) {
            std::cout << month << " = ";
            printMoney(total);
            std::cout << "\n";
        }

        std::cout << "\nROLLING THREE-ORDER AVERAGES\n";
        const auto rolling = rollingMean(enriched, 3);
        for (std::size_t i = 0; i < rolling.size(); ++i) {
            std::cout << enriched[i].source.orderId << " = ";
            printMoney(rolling[i]);
            std::cout << "\n";
        }

        assert(std::all_of(
            enriched.begin(),
            enriched.end(),
            [](const EnrichedRecord& record) {
                return record.netSales >= 0;
            }
        ));

        std::vector<SalesRecord> invalid = sales;
        invalid.push_back(sales.front());

        try {
            validate(invalid);
            throw std::logic_error("Duplicate test unexpectedly passed");
        } catch (const std::invalid_argument&) {
            std::cout << "\nDuplicate validation: REJECTED\n";
        }

        try {
            rollingMean(enriched, 0);
            throw std::logic_error("Invalid rolling window unexpectedly passed");
        } catch (const std::invalid_argument&) {
            std::cout << "Zero rolling window: REJECTED\n";
        }

        std::cout << "Data quality: VALID\n";
    } catch (const std::exception& error) {
        std::cerr << "Processing failure: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
