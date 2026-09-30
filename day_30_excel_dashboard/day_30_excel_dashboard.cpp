/*
    Executive Business Dashboard Governance and Analytics Engine

    This C++17 case study models the calculation layer of an executive
    business dashboard. A management dashboard receives transactional data,
    validates it, aggregates it by business dimensions, evaluates monthly
    targets, detects performance exceptions, and produces a compact executive
    report.

    The design emphasizes:
    - typed business records
    - validation before aggregation
    - aggregation by region and product
    - weighted margin calculation
    - monthly trend construction
    - target and variance evaluation
    - threshold-based executive alerts
    - deterministic behavior
    - explicit complexity and failure handling

    Compile:
        g++ -std=c++17 -O2 dashboard.cpp -o dashboard
*/

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

// -----------------------------------------------------------------------------
// Domain model
// -----------------------------------------------------------------------------

struct SalesRecord {
    string month;
    string region;
    string product;
    string channel;
    int units;
    double revenue;
    double cost;

    double grossProfit() const {
        return revenue - cost;
    }

    double margin() const {
        return revenue == 0.0 ? 0.0 : grossProfit() / revenue;
    }
};

struct Aggregate {
    double revenue = 0.0;
    double cost = 0.0;
    long long units = 0;
    long long transactions = 0;

    double grossProfit() const {
        return revenue - cost;
    }

    double margin() const {
        return revenue == 0.0 ? 0.0 : grossProfit() / revenue;
    }
};

struct MonthlyPerformance {
    string month;
    double revenue = 0.0;
    double cost = 0.0;
    long long units = 0;

    double grossProfit() const {
        return revenue - cost;
    }

    double margin() const {
        return revenue == 0.0 ? 0.0 : grossProfit() / revenue;
    }
};

struct Variance {
    string month;
    double actual = 0.0;
    double target = 0.0;

    double amount() const {
        return actual - target;
    }

    double percentage() const {
        return target == 0.0 ? 0.0 : amount() / target;
    }

    bool aboveTarget() const {
        return amount() >= 0.0;
    }
};

struct Alert {
    string severity;
    string category;
    string message;
};

// -----------------------------------------------------------------------------
// Data validation
// -----------------------------------------------------------------------------

class DashboardValidator {
public:
    static void validate(const SalesRecord& record) {
        if (record.region != "North" &&
            record.region != "South" &&
            record.region != "East" &&
            record.region != "West") {
            throw invalid_argument(
                "Unknown region: " + record.region
            );
        }

        if (record.product != "Cloud Suite" &&
            record.product != "Analytics Pro" &&
            record.product != "Security Platform" &&
            record.product != "Data Hub") {
            throw invalid_argument(
                "Unknown product: " + record.product
            );
        }

        if (record.channel != "Direct" &&
            record.channel != "Online" &&
            record.channel != "Partner") {
            throw invalid_argument(
                "Unknown channel: " + record.channel
            );
        }

        if (record.units <= 0) {
            throw invalid_argument(
                "Units must be greater than zero."
            );
        }

        if (!isfinite(record.revenue) || record.revenue < 0.0) {
            throw invalid_argument(
                "Revenue must be a finite non-negative value."
            );
        }

        if (!isfinite(record.cost) || record.cost < 0.0) {
            throw invalid_argument(
                "Cost must be a finite non-negative value."
            );
        }

        if (record.cost > record.revenue) {
            throw invalid_argument(
                "Cost cannot exceed revenue."
            );
        }
    }

    static void validateDataset(
        const vector<SalesRecord>& records
    ) {
        if (records.empty()) {
            throw invalid_argument(
                "An executive dashboard requires source records."
            );
        }

        for (const auto& record : records) {
            validate(record);
        }
    }
};

// -----------------------------------------------------------------------------
// Repository data generator
// -----------------------------------------------------------------------------

class SalesRepository {
public:
    static vector<SalesRecord> createDataset() {
        mt19937 generator(42);

        vector<string> regions = {
            "North", "South", "East", "West"
        };

        vector<string> products = {
            "Cloud Suite",
            "Analytics Pro",
            "Security Platform",
            "Data Hub"
        };

        vector<string> channels = {
            "Direct", "Online", "Partner"
        };

        unordered_map<string, double> regionFactor = {
            {"North", 1.10},
            {"South", 0.94},
            {"East", 1.04},
            {"West", 1.18}
        };

        unordered_map<string, double> productPrice = {
            {"Cloud Suite", 4200.0},
            {"Analytics Pro", 3600.0},
            {"Security Platform", 5100.0},
            {"Data Hub", 2900.0}
        };

        unordered_map<string, double> productMargin = {
            {"Cloud Suite", 0.61},
            {"Analytics Pro", 0.56},
            {"Security Platform", 0.64},
            {"Data Hub", 0.49}
        };

        unordered_map<string, double> channelFactor = {
            {"Direct", 1.00},
            {"Online", 0.91},
            {"Partner", 0.96}
        };

        uniform_int_distribution<int> dailyTransactions(3, 6);
        uniform_int_distribution<int> unitsDistribution(2, 14);
        uniform_int_distribution<int> regionDistribution(
            0,
            static_cast<int>(regions.size()) - 1
        );
        uniform_int_distribution<int> productDistribution(
            0,
            static_cast<int>(products.size()) - 1
        );
        uniform_int_distribution<int> channelDistribution(
            0,
            static_cast<int>(channels.size()) - 1
        );
        uniform_real_distribution<double> variation(0.90, 1.12);
        uniform_real_distribution<double> marginVariation(0.94, 1.05);

        vector<SalesRecord> records;

        // A six-month dataset gives the dashboard enough time-series depth
        // for trend, target, and variance analysis.
        for (int month = 1; month <= 6; ++month) {
            string monthName =
                "2026-" + (month < 10 ? "0" : "") +
                to_string(month);

            for (int day = 1; day <= 30; ++day) {
                int transactions = dailyTransactions(generator);

                for (int i = 0; i < transactions; ++i) {
                    const string& region =
                        regions[regionDistribution(generator)];

                    const string& product =
                        products[productDistribution(generator)];

                    const string& channel =
                        channels[channelDistribution(generator)];

                    int units = unitsDistribution(generator);

                    // Month-end demand is stronger, producing a realistic
                    // pattern that can be displayed as a line chart.
                    double monthEndBoost =
                        day >= 25 ? 1.18 : 1.0;

                    double revenue =
                        productPrice[product] *
                        units *
                        regionFactor[region] *
                        channelFactor[channel] *
                        monthEndBoost *
                        variation(generator);

                    double margin =
                        productMargin[product] *
                        marginVariation(generator);

                    double cost = revenue * (1.0 - margin);

                    records.push_back({
                        monthName,
                        region,
                        product,
                        channel,
                        units,
                        revenue,
                        cost
                    });
                }
            }
        }

        DashboardValidator::validateDataset(records);

        return records;
    }
};

// -----------------------------------------------------------------------------
// Analytical engine
// -----------------------------------------------------------------------------

class DashboardEngine {
private:
    vector<SalesRecord> records;

public:
    explicit DashboardEngine(vector<SalesRecord> input)
        : records(std::move(input)) {
        DashboardValidator::validateDataset(records);
    }

    Aggregate overall() const {
        Aggregate result;

        for (const auto& record : records) {
            result.revenue += record.revenue;
            result.cost += record.cost;
            result.units += record.units;
            result.transactions++;
        }

        return result;
    }

    map<string, Aggregate> byRegion() const {
        return aggregateBy(
            [](const SalesRecord& record) {
                return record.region;
            }
        );
    }

    map<string, Aggregate> byProduct() const {
        return aggregateBy(
            [](const SalesRecord& record) {
                return record.product;
            }
        );
    }

    map<string, Aggregate> byChannel() const {
        return aggregateBy(
            [](const SalesRecord& record) {
                return record.channel;
            }
        );
    }

    vector<MonthlyPerformance> monthlyTrend() const {
        map<string, MonthlyPerformance> grouped;

        for (const auto& record : records) {
            auto& month = grouped[record.month];

            month.month = record.month;
            month.revenue += record.revenue;
            month.cost += record.cost;
            month.units += record.units;
        }

        vector<MonthlyPerformance> result;

        for (const auto& [month, performance] : grouped) {
            result.push_back(performance);
        }

        return result;
    }

    vector<Variance> targetVariance(
        const vector<MonthlyPerformance>& trend
    ) const {
        vector<Variance> result;

        optional<double> previousTarget;

        for (size_t i = 0; i < trend.size(); ++i) {
            double target;

            if (!previousTarget.has_value()) {
                target = trend[i].revenue * 0.97;
            } else {
                target =
                    previousTarget.value() *
                    (1.0 + 0.08 / 12.0);
            }

            if (i % 3 == 2) {
                target *= 1.03;
            }

            previousTarget = target;

            result.push_back({
                trend[i].month,
                trend[i].revenue,
                target
            });
        }

        return result;
    }

    vector<Alert> buildAlerts(
        const vector<Variance>& variance,
        const map<string, Aggregate>& regions
    ) const {
        vector<Alert> alerts;

        // Executive dashboards should not display every possible anomaly.
        // Thresholds reduce visual noise and focus attention on material
        // deviations that may warrant management investigation.
        for (const auto& item : variance) {
            if (item.percentage() <= -0.08) {
                alerts.push_back({
                    "HIGH",
                    "Revenue",
                    item.month +
                    " is more than 8% below its revenue target."
                });
            } else if (item.percentage() < 0.0) {
                alerts.push_back({
                    "MEDIUM",
                    "Revenue",
                    item.month +
                    " is below its revenue target."
                });
            }
        }

        double totalRevenue = overall().revenue;

        if (totalRevenue > 0.0 && !regions.empty()) {
            auto largest = max_element(
                regions.begin(),
                regions.end(),
                [](const auto& left, const auto& right) {
                    return left.second.revenue <
                           right.second.revenue;
                }
            );

            double concentration =
                largest->second.revenue / totalRevenue;

            if (concentration > 0.35) {
                alerts.push_back({
                    "MEDIUM",
                    "Concentration",
                    "The largest region contributes more than "
                    "35% of total revenue."
                });
            }
        }

        return alerts;
    }

private:
    template <typename KeyFunction>
    map<string, Aggregate> aggregateBy(
        KeyFunction keyFunction
    ) const {
        map<string, Aggregate> result;

        for (const auto& record : records) {
            string key = keyFunction(record);
            Aggregate& aggregate = result[key];

            aggregate.revenue += record.revenue;
            aggregate.cost += record.cost;
            aggregate.units += record.units;
            aggregate.transactions++;
        }

        return result;
    }
};

// -----------------------------------------------------------------------------
// Presentation helpers
// -----------------------------------------------------------------------------

void printCurrency(double value) {
    cout << "$"
         << fixed
         << setprecision(0)
         << value;
}

void printAggregateTable(
    const string& title,
    const map<string, Aggregate>& values
) {
    cout << "\n" << title << "\n";
    cout << string(76, '-') << "\n";

    for (const auto& [key, aggregate] : values) {
        cout << left
             << setw(23)
             << key
             << " Revenue ";

        printCurrency(aggregate.revenue);

        cout << "  Margin "
             << fixed
             << setprecision(1)
             << aggregate.margin() * 100
             << "%\n";
    }
}

void printExecutiveDashboard(
    const DashboardEngine& engine
) {
    Aggregate total = engine.overall();

    cout << "\nEXECUTIVE BUSINESS DASHBOARD\n";
    cout << string(76, '=') << "\n";

    cout << "Revenue              ";
    printCurrency(total.revenue);
    cout << "\n";

    cout << "Gross Profit         ";
    printCurrency(total.grossProfit());
    cout << "\n";

    cout << "Gross Margin         "
         << fixed
         << setprecision(1)
         << total.margin() * 100
         << "%\n";

    cout << "Units                "
         << total.units
         << "\n";

    cout << "Transactions         "
         << total.transactions
         << "\n";

    printAggregateTable(
        "REGIONAL PERFORMANCE",
        engine.byRegion()
    );

    printAggregateTable(
        "PRODUCT PERFORMANCE",
        engine.byProduct()
    );

    printAggregateTable(
        "CHANNEL PERFORMANCE",
        engine.byChannel()
    );

    cout << "\nMONTHLY TARGET VARIANCE\n";
    cout << string(76, '-') << "\n";

    const auto trend = engine.monthlyTrend();
    const auto variance = engine.targetVariance(trend);

    for (const auto& item : variance) {
        cout << item.month
             << " Actual ";
        printCurrency(item.actual);

        cout << " Target ";
        printCurrency(item.target);

        cout << " Variance ";
        printCurrency(item.amount());

        cout << " "
             << (item.aboveTarget()
                     ? "ABOVE"
                     : "BELOW")
             << "\n";
    }

    cout << "\nEXECUTIVE ALERTS\n";
    cout << string(76, '-') << "\n";

    const auto alerts =
        engine.buildAlerts(variance, engine.byRegion());

    if (alerts.empty()) {
        cout << "No material dashboard exceptions detected.\n";
    } else {
        for (const auto& alert : alerts) {
            cout << "["
                 << alert.severity
                 << "] "
                 << alert.category
                 << ": "
                 << alert.message
                 << "\n";
        }
    }
}

// -----------------------------------------------------------------------------
// Main case study
// -----------------------------------------------------------------------------

int main() {
    try {
        const vector<SalesRecord> records =
            SalesRepository::createDataset();

        DashboardEngine engine(records);

        printExecutiveDashboard(engine);

        // A deliberately invalid row demonstrates that source-quality
        // controls must run before management metrics are trusted.
        cout << "\nVALIDATION TEST\n";
        cout << string(76, '-') << "\n";

        try {
            SalesRecord invalid{
                "2026-06",
                "Central",
                "Cloud Suite",
                "Direct",
                4,
                12000.0,
                4000.0
            };

            DashboardValidator::validate(invalid);
        } catch (const exception& error) {
            cout << "Invalid row rejected: "
                 << error.what()
                 << "\n";
        }

        // Complexity:
        // - Source validation is O(n).
        // - Each aggregation is O(n) expected work.
        // - Ordered map output adds O(k log k), where k is the number of
        //   dashboard categories.
        // - Monthly aggregation uses O(m) memory for m distinct months.
        cout << "\nENGINE STATUS\n";
        cout << string(76, '-') << "\n";
        cout << "Validated source records: "
             << records.size()
             << "\n";
        cout << "Dashboard calculation completed successfully.\n";

        return 0;
    } catch (const exception& error) {
        cerr << "Dashboard processing failed: "
             << error.what()
             << "\n";

        return 1;
    }
}
