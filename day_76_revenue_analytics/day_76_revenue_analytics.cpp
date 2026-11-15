#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * Revenue Analytics and Governance Engine
 *
 * C++17 implementation.
 *
 * Responsibilities:
 * - Revenue observation validation
 * - Period aggregation
 * - Revenue growth analysis
 * - Volume, mix and price decomposition
 * - Product and regional contribution
 * - Gross-margin evaluation
 * - Customer concentration
 * - Forecasting
 * - Reconciliation and failure handling
 */

namespace Revenue {

constexpr double EPSILON = 1e-8;

enum class Dimension {
    Product,
    Region,
    Customer
};

struct RevenueRecord {
    string period;
    string product;
    string region;
    string customer;

    long long units;
    double listPrice;
    double discountRate;
    double unitCost;

    double netPrice() const {
        return listPrice * (1.0 - discountRate);
    }

    double revenue() const {
        return static_cast<double>(units) * netPrice();
    }

    double cost() const {
        return static_cast<double>(units) * unitCost;
    }

    double grossProfit() const {
        return revenue() - cost();
    }
};

struct Metrics {
    long long units = 0;
    double revenue = 0.0;
    double cost = 0.0;
    double grossProfit = 0.0;
    double averagePrice = 0.0;
    double grossMargin = 0.0;
};

struct GrowthResult {
    double previousRevenue;
    double currentRevenue;
    double revenueChange;
    double growthRate;
    long long unitChange;
    double averagePriceChange;
};

struct DecompositionResult {
    double previousRevenue;
    double currentRevenue;
    double revenueChange;
    double volumeEffect;
    double mixEffect;
    double priceEffect;
    double reconciliationDifference;
};

struct ProductMetrics {
    long long units = 0;
    double revenue = 0.0;
    double averagePrice = 0.0;
    double grossProfit = 0.0;
    double margin = 0.0;
    double revenueShare = 0.0;
};

class AnalyticsException : public runtime_error {
public:
    explicit AnalyticsException(const string& message)
        : runtime_error(message) {}
};

class RevenueEngine {
private:
    vector<RevenueRecord> records;
    set<string> uniqueKeys;

    static void validate(const RevenueRecord& r) {
        if (r.period.size() != 7 ||
            r.period[4] != '-' ||
            !all_of(r.period.begin(), r.period.end(),
                [](char c) {
                    return c == '-' || (c >= '0' && c <= '9');
                })) {
            throw AnalyticsException("Invalid period format.");
        }

        int month = stoi(r.period.substr(5, 2));

        if (month < 1 || month > 12) {
            throw AnalyticsException("Invalid calendar month.");
        }

        if (r.product.empty() ||
            r.region.empty() ||
            r.customer.empty()) {
            throw AnalyticsException("Empty business dimension.");
        }

        if (r.units < 0) {
            throw AnalyticsException("Negative units are invalid.");
        }

        if (!isfinite(r.listPrice) ||
            !isfinite(r.discountRate) ||
            !isfinite(r.unitCost)) {
            throw AnalyticsException("Non-finite financial value.");
        }

        if (r.listPrice < 0.0 ||
            r.unitCost < 0.0 ||
            r.discountRate < 0.0 ||
            r.discountRate > 1.0) {
            throw AnalyticsException("Invalid financial parameters.");
        }
    }

    static string makeKey(const RevenueRecord& r) {
        return r.period + "|" + r.product + "|" +
            r.region + "|" + r.customer;
    }

    vector<RevenueRecord> getPeriod(const string& period) const {
        vector<RevenueRecord> result;

        copy_if(
            records.begin(),
            records.end(),
            back_inserter(result),
            [&](const RevenueRecord& r) {
                return r.period == period;
            }
        );

        if (result.empty()) {
            throw AnalyticsException(
                "No observations for period " + period
            );
        }

        return result;
    }

public:
    void addRecord(const RevenueRecord& record) {
        validate(record);

        string key = makeKey(record);

        if (uniqueKeys.count(key)) {
            throw AnalyticsException("Duplicate observation: " + key);
        }

        uniqueKeys.insert(key);
        records.push_back(record);
    }

    Metrics aggregate(
        const vector<RevenueRecord>& observations
    ) const {
        Metrics result;

        for (const auto& r : observations) {
            result.units += r.units;
            result.revenue += r.revenue();
            result.cost += r.cost();
        }

        result.grossProfit = result.revenue - result.cost;

        if (result.units > 0) {
            result.averagePrice =
                result.revenue / result.units;
        }

        if (result.revenue > 0.0) {
            result.grossMargin =
                result.grossProfit / result.revenue;
        }

        return result;
    }

    GrowthResult growth(
        const string& previous,
        const string& current
    ) const {
        if (previous >= current) {
            throw AnalyticsException(
                "Current period must follow previous period."
            );
        }

        Metrics old = aggregate(getPeriod(previous));
        Metrics latest = aggregate(getPeriod(current));

        double change = latest.revenue - old.revenue;

        return {
            old.revenue,
            latest.revenue,
            change,
            old.revenue != 0.0 ? change / old.revenue : 0.0,
            latest.units - old.units,
            latest.averagePrice - old.averagePrice
        };
    }

    map<string, ProductMetrics> productMetrics(
        const string& period
    ) const {
        map<string, ProductMetrics> result;
        auto observations = getPeriod(period);

        double totalRevenue = 0.0;

        for (const auto& r : observations) {
            auto& p = result[r.product];

            p.units += r.units;
            p.revenue += r.revenue();
            p.grossProfit += r.grossProfit();

            totalRevenue += r.revenue();
        }

        for (auto& [name, p] : result) {
            if (p.units > 0) {
                p.averagePrice = p.revenue / p.units;
            }

            if (p.revenue > 0.0) {
                p.margin = p.grossProfit / p.revenue;
            }

            if (totalRevenue > 0.0) {
                p.revenueShare = p.revenue / totalRevenue;
            }
        }

        return result;
    }

    DecompositionResult decompose(
        const string& previous,
        const string& current
    ) const {
        auto oldRecords = getPeriod(previous);
        auto newRecords = getPeriod(current);

        auto oldProducts = productMetrics(previous);
        auto newProducts = productMetrics(current);

        Metrics oldMetrics = aggregate(oldRecords);
        Metrics newMetrics = aggregate(newRecords);

        double q0 = static_cast<double>(oldMetrics.units);
        double q1 = static_cast<double>(newMetrics.units);

        if (q0 <= 0.0 || q1 <= 0.0) {
            throw AnalyticsException(
                "Decomposition requires positive volume."
            );
        }

        set<string> products;

        for (const auto& [name, p] : oldProducts) {
            products.insert(name);
        }

        for (const auto& [name, p] : newProducts) {
            products.insert(name);
        }

        double baselinePrice = 0.0;
        double mixEffect = 0.0;
        double priceEffect = 0.0;

        for (const string& product : products) {
            ProductMetrics old{};
            ProductMetrics latest{};

            if (oldProducts.count(product)) {
                old = oldProducts.at(product);
            }

            if (newProducts.count(product)) {
                latest = newProducts.at(product);
            }

            double oldShare = old.units / q0;
            double newShare = latest.units / q1;

            baselinePrice += oldShare * old.averagePrice;

            mixEffect += q1 *
                (newShare - oldShare) *
                old.averagePrice;

            priceEffect += q1 *
                newShare *
                (latest.averagePrice - old.averagePrice);
        }

        double volumeEffect = (q1 - q0) * baselinePrice;
        double change = newMetrics.revenue - oldMetrics.revenue;

        double reconciled =
            volumeEffect + mixEffect + priceEffect;

        double difference = change - reconciled;

        if (abs(difference) > 0.000001) {
            throw AnalyticsException(
                "Revenue decomposition did not reconcile."
            );
        }

        return {
            oldMetrics.revenue,
            newMetrics.revenue,
            change,
            volumeEffect,
            mixEffect,
            priceEffect,
            difference
        };
    }

    map<string, Metrics> dimensionAnalysis(
        const string& period,
        Dimension dimension
    ) const {
        map<string, vector<RevenueRecord>> groups;

        for (const auto& r : getPeriod(period)) {
            string key;

            switch (dimension) {
                case Dimension::Product:
                    key = r.product;
                    break;

                case Dimension::Region:
                    key = r.region;
                    break;

                case Dimension::Customer:
                    key = r.customer;
                    break;
            }

            groups[key].push_back(r);
        }

        map<string, Metrics> result;

        for (const auto& [name, observations] : groups) {
            result[name] = aggregate(observations);
        }

        return result;
    }

    double customerHHI(const string& period) const {
        auto groups = dimensionAnalysis(
            period,
            Dimension::Customer
        );

        double total = aggregate(getPeriod(period)).revenue;

        if (total <= 0.0) {
            throw AnalyticsException(
                "HHI requires positive revenue."
            );
        }

        double hhi = 0.0;

        for (const auto& [name, metrics] : groups) {
            double share = metrics.revenue / total;
            hhi += share * share;
        }

        return hhi;
    }

    vector<double> forecast(int horizon) const {
        if (horizon < 1 || horizon > 36) {
            throw AnalyticsException(
                "Forecast horizon must be between 1 and 36."
            );
        }

        set<string> periods;

        for (const auto& r : records) {
            periods.insert(r.period);
        }

        if (periods.size() < 2) {
            throw AnalyticsException(
                "Two periods are required for forecasting."
            );
        }

        vector<double> values;

        for (const string& period : periods) {
            values.push_back(
                aggregate(getPeriod(period)).revenue
            );
        }

        double totalGrowth = 0.0;

        for (size_t i = 1; i < values.size(); ++i) {
            if (values[i - 1] <= 0.0) {
                throw AnalyticsException(
                    "Forecast requires positive base revenue."
                );
            }

            totalGrowth += values[i] / values[i - 1] - 1.0;
        }

        double averageGrowth =
            totalGrowth / static_cast<double>(values.size() - 1);

        vector<double> predictions;
        double value = values.back();

        for (int i = 0; i < horizon; ++i) {
            value = max(0.0, value * (1.0 + averageGrowth));
            predictions.push_back(value);
        }

        return predictions;
    }

    void printProductReport(const string& period) const {
        auto products = productMetrics(period);

        cout << "\nPRODUCT REVENUE REPORT: " << period << "\n";

        cout << left << setw(15) << "Product"
             << right << setw(12) << "Units"
             << setw(16) << "Revenue"
             << setw(12) << "Margin"
             << setw(12) << "Share" << "\n";

        for (const auto& [name, p] : products) {
            cout << left << setw(15) << name
                 << right << setw(12) << p.units
                 << setw(16) << fixed << setprecision(2)
                 << p.revenue
                 << setw(11) << setprecision(2)
                 << p.margin * 100.0 << "%"
                 << setw(11) << p.revenueShare * 100.0
                 << "%\n";
        }
    }
};

RevenueEngine createSampleEngine() {
    RevenueEngine engine;

    vector<RevenueRecord> data = {
        {"2026-01","Cloud","North","Customer A",100,1200,.05,600},
        {"2026-01","Software","South","Customer B",180,500,.10,180},
        {"2026-01","Hardware","East","Customer C",250,300,.08,190},
        {"2026-01","Services","West","Customer D",90,900,.05,400},

        {"2026-02","Cloud","North","Customer A",115,1250,.04,600},
        {"2026-02","Software","South","Customer B",200,520,.08,180},
        {"2026-02","Hardware","East","Customer C",230,310,.05,190},
        {"2026-02","Services","West","Customer D",105,920,.04,400},

        {"2026-03","Cloud","North","Customer A",130,1300,.03,600},
        {"2026-03","Software","South","Customer B",220,540,.07,180},
        {"2026-03","Hardware","East","Customer C",245,320,.05,190},
        {"2026-03","Services","West","Customer D",115,950,.03,400},

        {"2026-04","Cloud","North","Customer A",145,1350,.03,600},
        {"2026-04","Software","South","Customer B",240,550,.06,180},
        {"2026-04","Hardware","East","Customer C",260,330,.06,190},
        {"2026-04","Services","West","Customer D",130,970,.04,400}
    };

    for (const auto& record : data) {
        engine.addRecord(record);
    }

    return engine;
}

void runTests(const RevenueEngine& engine) {
    auto decomposition = engine.decompose(
        "2026-03",
        "2026-04"
    );

    if (abs(decomposition.reconciliationDifference) > EPSILON) {
        throw AnalyticsException("Test failed: reconciliation.");
    }

    auto growth = engine.growth("2026-03", "2026-04");

    if (growth.currentRevenue <= growth.previousRevenue) {
        throw AnalyticsException("Test failed: expected growth.");
    }

    if (engine.customerHHI("2026-04") <= 0.0) {
        throw AnalyticsException("Test failed: customer HHI.");
    }

    cout << "All analytical validation tests passed.\n";
}

} // namespace Revenue

int main() {
    using namespace Revenue;

    try {
        RevenueEngine engine = createSampleEngine();

        runTests(engine);

        cout << fixed << setprecision(2);

        auto growth = engine.growth(
            "2026-03",
            "2026-04"
        );

        cout << "\nREVENUE GROWTH ANALYSIS\n";
        cout << "Previous revenue: " << growth.previousRevenue << "\n";
        cout << "Current revenue:  " << growth.currentRevenue << "\n";
        cout << "Revenue change:   " << growth.revenueChange << "\n";
        cout << "Growth rate:      "
             << growth.growthRate * 100.0 << "%\n";
        cout << "Unit change:      " << growth.unitChange << "\n";

        auto decomposition = engine.decompose(
            "2026-03",
            "2026-04"
        );

        cout << "\nREVENUE DECOMPOSITION\n";
        cout << "Volume effect: " << decomposition.volumeEffect << "\n";
        cout << "Mix effect:    " << decomposition.mixEffect << "\n";
        cout << "Price effect:  " << decomposition.priceEffect << "\n";
        cout << "Reconciliation difference: "
             << decomposition.reconciliationDifference << "\n";

        engine.printProductReport("2026-04");

        cout << "\nREGIONAL ANALYSIS\n";

        auto regions = engine.dimensionAnalysis(
            "2026-04",
            Dimension::Region
        );

        for (const auto& [name, metrics] : regions) {
            cout << name
                 << " | Revenue: " << metrics.revenue
                 << " | Margin: " << metrics.grossMargin * 100.0
                 << "%\n";
        }

        cout << "\nCUSTOMER CONCENTRATION\n";
        cout << "HHI: " << engine.customerHHI("2026-04") << "\n";

        cout << "\nTHREE-PERIOD REVENUE FORECAST\n";

        auto predictions = engine.forecast(3);

        for (size_t i = 0; i < predictions.size(); ++i) {
            cout << "Period +" << i + 1
                 << ": " << predictions[i] << "\n";
        }

        // Demonstrate rejection of invalid input.
        try {
            RevenueRecord invalid{
                "2026-05", "Invalid", "North", "Customer X",
                -10, 100, .05, 50
            };

            engine.addRecord(invalid);
        } catch (const AnalyticsException& error) {
            cout << "\nExpected validation error: "
                 << error.what() << "\n";
        }

    } catch (const exception& error) {
        cerr << "Fatal analytics error: "
             << error.what() << "\n";

        return 1;
    }

    return 0;
}
