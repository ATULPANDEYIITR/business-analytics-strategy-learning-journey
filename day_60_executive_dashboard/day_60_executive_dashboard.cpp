#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <regex>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <utility>
#include <vector>

/*
 * C++17 executive dashboard aggregation engine.
 *
 * Monetary amounts are stored as integer cents. This avoids binary
 * floating-point arithmetic for financial aggregation. Floating-point
 * arithmetic is limited to ratios and customer satisfaction averages.
 */

using Money = std::int64_t;

struct MonthlyRecord {
    std::string period;
    std::string businessUnit;
    std::string region;

    Money revenueCents;
    Money revenueTargetCents;
    Money cogsCents;
    Money operatingExpenseCents;

    std::int64_t orders;
    std::int64_t deliveredOrders;
    std::int64_t onTimeOrders;

    double csatScoreSum;
    std::int64_t csatResponses;
};

struct Filter {
    std::optional<std::string> fromMonth;
    std::optional<std::string> toMonth;
    std::optional<std::string> businessUnit;
    std::optional<std::string> region;
};

struct Metrics {
    std::size_t recordCount = 0;

    Money revenueCents = 0;
    Money revenueTargetCents = 0;
    Money cogsCents = 0;
    Money operatingExpenseCents = 0;

    std::int64_t orders = 0;
    std::int64_t deliveredOrders = 0;
    std::int64_t onTimeOrders = 0;

    double csatScoreSum = 0.0;
    std::int64_t csatResponses = 0;

    void add(const MonthlyRecord& record) {
        revenueCents = checkedAdd(revenueCents, record.revenueCents);
        revenueTargetCents = checkedAdd(
            revenueTargetCents, record.revenueTargetCents
        );
        cogsCents = checkedAdd(cogsCents, record.cogsCents);
        operatingExpenseCents = checkedAdd(
            operatingExpenseCents, record.operatingExpenseCents
        );

        orders = checkedAdd(orders, record.orders);
        deliveredOrders = checkedAdd(deliveredOrders, record.deliveredOrders);
        onTimeOrders = checkedAdd(onTimeOrders, record.onTimeOrders);

        csatScoreSum += record.csatScoreSum;
        csatResponses = checkedAdd(csatResponses, record.csatResponses);
        ++recordCount;
    }

    static std::int64_t checkedAdd(std::int64_t left, std::int64_t right) {
        if (right > 0 &&
            left > std::numeric_limits<std::int64_t>::max() - right) {
            throw std::overflow_error("Dashboard aggregation overflow");
        }

        if (right < 0 &&
            left < std::numeric_limits<std::int64_t>::min() - right) {
            throw std::overflow_error("Dashboard aggregation underflow");
        }

        return left + right;
    }

    Money grossProfitCents() const {
        return revenueCents - cogsCents;
    }

    Money operatingProfitCents() const {
        return grossProfitCents() - operatingExpenseCents;
    }

    static std::optional<double> percentage(
        long double numerator,
        long double denominator
    ) {
        if (denominator == 0.0L) {
            return std::nullopt;
        }

        return static_cast<double>(
            (numerator / denominator) * 100.0L
        );
    }

    std::optional<double> revenueAttainmentPct() const {
        return percentage(revenueCents, revenueTargetCents);
    }

    std::optional<double> grossMarginPct() const {
        return percentage(grossProfitCents(), revenueCents);
    }

    std::optional<double> operatingMarginPct() const {
        return percentage(operatingProfitCents(), revenueCents);
    }

    std::optional<double> fulfillmentPct() const {
        return percentage(deliveredOrders, orders);
    }

    std::optional<double> onTimeDeliveryPct() const {
        return percentage(onTimeOrders, deliveredOrders);
    }

    std::optional<double> averageCsat() const {
        if (csatResponses == 0) {
            return std::nullopt;
        }

        return csatScoreSum / static_cast<double>(csatResponses);
    }
};

struct DashboardResult {
    Metrics executive;
    std::map<std::pair<std::string, std::string>, Metrics> segments;
    std::vector<std::string> alerts;
};

class ExecutiveDashboardEngine {
public:
    explicit ExecutiveDashboardEngine(std::vector<MonthlyRecord> records)
        : records_(std::move(records)) {
        validateDataset(records_);
    }

    DashboardResult build(const Filter& filter = {}) const {
        validateFilter(filter);

        DashboardResult result;

        for (const auto& record : records_) {
            if (!matches(record, filter)) {
                continue;
            }

            result.executive.add(record);

            const auto key = std::make_pair(
                record.businessUnit,
                record.region
            );
            result.segments[key].add(record);
        }

        result.alerts = evaluateAlerts(result.executive);
        return result;
    }

    std::size_t sourceRecordCount() const {
        return records_.size();
    }

private:
    std::vector<MonthlyRecord> records_;

    static void validateRecord(const MonthlyRecord& record) {
        static const std::regex monthPattern(
            R"(^[0-9]{4}-(0[1-9]|1[0-2])$)"
        );

        if (!std::regex_match(record.period, monthPattern)) {
            throw std::invalid_argument(
                "Period must use the YYYY-MM format"
            );
        }

        if (record.businessUnit.empty() || record.region.empty()) {
            throw std::invalid_argument(
                "Business unit and region are required"
            );
        }

        if (record.revenueCents < 0 ||
            record.revenueTargetCents <= 0 ||
            record.cogsCents < 0 ||
            record.operatingExpenseCents < 0) {
            throw std::invalid_argument(
                "Financial values violate non-negative constraints"
            );
        }

        if (record.orders < 0 ||
            record.deliveredOrders < 0 ||
            record.onTimeOrders < 0 ||
            record.csatResponses < 0) {
            throw std::invalid_argument(
                "Counts cannot be negative"
            );
        }

        if (record.deliveredOrders > record.orders ||
            record.onTimeOrders > record.deliveredOrders) {
            throw std::invalid_argument(
                "Delivery counts are inconsistent"
            );
        }

        if (!std::isfinite(record.csatScoreSum) ||
            record.csatScoreSum < 0.0) {
            throw std::invalid_argument(
                "CSAT score total must be finite and non-negative"
            );
        }

        if (record.csatResponses == 0) {
            if (record.csatScoreSum != 0.0) {
                throw std::invalid_argument(
                    "CSAT total must be zero without survey responses"
                );
            }
        } else {
            const double minimum =
                static_cast<double>(record.csatResponses);
            const double maximum =
                static_cast<double>(record.csatResponses) * 5.0;

            if (record.csatScoreSum < minimum ||
                record.csatScoreSum > maximum) {
                throw std::invalid_argument(
                    "CSAT total violates the 1-to-5 response scale"
                );
            }
        }
    }

    static std::string keyOf(const MonthlyRecord& record) {
        return record.period + "|" + record.businessUnit + "|" + record.region;
    }

    static void validateDataset(
        const std::vector<MonthlyRecord>& records
    ) {
        if (records.empty()) {
            throw std::invalid_argument("Dataset cannot be empty");
        }

        std::unordered_set<std::string> keys;
        keys.reserve(records.size());

        for (const auto& record : records) {
            validateRecord(record);

            if (!keys.insert(keyOf(record)).second) {
                throw std::invalid_argument(
                    "Duplicate monthly business-unit and region record"
                );
            }
        }
    }

    static void validateFilter(const Filter& filter) {
        const auto validMonth = [](const std::string& value) {
            static const std::regex pattern(
                R"(^[0-9]{4}-(0[1-9]|1[0-2])$)"
            );
            return std::regex_match(value, pattern);
        };

        if (filter.fromMonth && !validMonth(*filter.fromMonth)) {
            throw std::invalid_argument("Invalid filter start month");
        }

        if (filter.toMonth && !validMonth(*filter.toMonth)) {
            throw std::invalid_argument("Invalid filter end month");
        }

        if (filter.fromMonth && filter.toMonth &&
            *filter.fromMonth > *filter.toMonth) {
            throw std::invalid_argument(
                "Filter start month cannot exceed end month"
            );
        }
    }

    static bool matches(
        const MonthlyRecord& record,
        const Filter& filter
    ) {
        if (filter.fromMonth && record.period < *filter.fromMonth) {
            return false;
        }

        if (filter.toMonth && record.period > *filter.toMonth) {
            return false;
        }

        if (filter.businessUnit &&
            record.businessUnit != *filter.businessUnit) {
            return false;
        }

        if (filter.region && record.region != *filter.region) {
            return false;
        }

        return true;
    }

    static std::vector<std::string> evaluateAlerts(
        const Metrics& metrics
    ) {
        if (metrics.recordCount == 0) {
            return {"NO_DATA: no records match the selected filters"};
        }

        std::vector<std::string> alerts;

        const auto attainment = metrics.revenueAttainmentPct();
        if (attainment && *attainment < 95.0) {
            alerts.push_back(
                "CRITICAL: revenue attainment is below 95%"
            );
        } else if (attainment && *attainment < 100.0) {
            alerts.push_back(
                "WARNING: revenue is below plan"
            );
        }

        const auto margin = metrics.grossMarginPct();
        if (margin && *margin < 35.0) {
            alerts.push_back(
                "CRITICAL: gross margin is below 35%"
            );
        }

        const auto delivery = metrics.onTimeDeliveryPct();
        if (delivery && *delivery < 90.0) {
            alerts.push_back(
                "CRITICAL: on-time delivery is below 90%"
            );
        }

        const auto csat = metrics.averageCsat();
        if (csat && *csat < 4.0) {
            alerts.push_back(
                "WARNING: average customer satisfaction is below 4.0"
            );
        }

        return alerts;
    }
};

static void printOptional(
    const std::string& label,
    const std::optional<double>& value,
    const std::string& suffix = "%"
) {
    std::cout << std::left << std::setw(29) << label;

    if (value) {
        std::cout << std::fixed << std::setprecision(2)
                  << *value << suffix;
    } else {
        std::cout << "Not available";
    }

    std::cout << '\n';
}

static void printMoney(
    const std::string& label,
    Money cents
) {
    std::cout << std::left << std::setw(29) << label
              << std::fixed << std::setprecision(2)
              << static_cast<long double>(cents) / 100.0L
              << '\n';
}

static void printMetrics(
    const std::string& heading,
    const Metrics& metrics
) {
    std::cout << "\n" << heading << '\n';
    std::cout << std::string(45, '-') << '\n';

    std::cout << "Records                      "
              << metrics.recordCount << '\n';

    printMoney("Revenue", metrics.revenueCents);
    printMoney("Revenue target", metrics.revenueTargetCents);
    printOptional(
        "Revenue attainment",
        metrics.revenueAttainmentPct()
    );
    printMoney("Gross profit", metrics.grossProfitCents());
    printOptional("Gross margin", metrics.grossMarginPct());
    printMoney("Operating profit", metrics.operatingProfitCents());
    printOptional("Operating margin", metrics.operatingMarginPct());
    printOptional("Order fulfillment", metrics.fulfillmentPct());
    printOptional("On-time delivery", metrics.onTimeDeliveryPct());

    printOptional(
        "Average customer satisfaction",
        metrics.averageCsat(),
        "/5"
    );
}

static std::vector<MonthlyRecord> sampleData() {
    return {
        {"2026-01", "Consumer", "North", 42000000, 40000000, 25200000, 9600000, 1200, 1160, 1080, 792.0, 180},
        {"2026-01", "Consumer", "South", 36000000, 38000000, 22320000, 8000000, 1050, 1000, 910, 615.0, 150},
        {"2026-01", "Enterprise", "North", 61000000, 60000000, 33550000, 16000000, 640, 620, 595, 414.0, 90},
        {"2026-01", "Enterprise", "South", 49000000, 51000000, 27440000, 12800000, 520, 500, 465, 344.0, 80},

        {"2026-02", "Consumer", "North", 44000000, 42000000, 26400000, 9900000, 1240, 1205, 1130, 810.0, 185},
        {"2026-02", "Consumer", "South", 37000000, 38500000, 22940000, 8300000, 1080, 1035, 950, 640.0, 155},
        {"2026-02", "Enterprise", "North", 63500000, 62000000, 34925000, 16500000, 660, 642, 615, 423.0, 92},
        {"2026-02", "Enterprise", "South", 50500000, 52000000, 28280000, 13100000, 535, 516, 480, 356.0, 82},

        {"2026-03", "Consumer", "North", 45500000, 44000000, 27072500, 10100000, 1280, 1250, 1180, 840.0, 190},
        {"2026-03", "Consumer", "South", 39000000, 40000000, 24180000, 8600000, 1120, 1080, 1000, 660.0, 160},
        {"2026-03", "Enterprise", "North", 66000000, 65000000, 36300000, 17000000, 680, 665, 640, 437.0, 95},
        {"2026-03", "Enterprise", "South", 53000000, 53500000, 29680000, 13500000, 550, 535, 500, 374.0, 85},
    };
}

int main() {
    try {
        ExecutiveDashboardEngine engine(sampleData());

        Filter allMonths;
        allMonths.fromMonth = "2026-01";
        allMonths.toMonth = "2026-03";

        const DashboardResult executive = engine.build(allMonths);

        assert(executive.executive.recordCount == 12);
        assert(executive.segments.size() == 4);

        printMetrics("EXECUTIVE PERFORMANCE", executive.executive);

        std::cout << "\nREGIONAL AND BUSINESS-UNIT PERFORMANCE\n";
        std::cout << std::string(45, '-') << '\n';

        for (const auto& [key, metrics] : executive.segments) {
            std::cout << "\n" << key.first << " / " << key.second << '\n';
            printMoney("Revenue", metrics.revenueCents);
            printOptional(
                "Revenue attainment",
                metrics.revenueAttainmentPct()
            );
            printOptional("Gross margin", metrics.grossMarginPct());
            printOptional(
                "On-time delivery",
                metrics.onTimeDeliveryPct()
            );
        }

        std::cout << "\nMANAGEMENT ALERTS\n";
        std::cout << std::string(45, '-') << '\n';

        if (executive.alerts.empty()) {
            std::cout << "No threshold breaches detected.\n";
        } else {
            for (const auto& alert : executive.alerts) {
                std::cout << "- " << alert << '\n';
            }
        }

        Filter northRegion = allMonths;
        northRegion.region = "North";

        const DashboardResult north = engine.build(northRegion);
        assert(north.executive.recordCount == 6);
        printMetrics("NORTH REGION FILTER", north.executive);

        Filter noMatches = allMonths;
        noMatches.region = "West";

        const DashboardResult empty = engine.build(noMatches);
        assert(empty.executive.recordCount == 0);
        assert(!empty.alerts.empty());

        std::cout << "\nNo-data filter check: " << empty.alerts.front()
                  << '\n';

        std::cout << "\nProcessing completed successfully.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Dashboard engine failed: "
                  << error.what() << '\n';
        return 1;
    }
}
