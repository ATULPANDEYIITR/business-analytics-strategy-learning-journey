/*
 * Pivot Charts | Visualizing Business Performance
 *
 * C++17 case study:
 * A business-performance analytics engine that transforms transaction-level
 * records into pivot-style summaries used by an executive dashboard.
 *
 * The implementation demonstrates:
 * - structured business records
 * - classes and encapsulation
 * - dimensions and measures
 * - validation
 * - aggregation
 * - two-dimensional pivot tables
 * - filtering
 * - KPI calculations
 * - ranking
 * - Pareto analysis
 * - month grouping
 * - growth analysis
 * - rolling averages
 * - textual pivot charts
 * - exception handling
 * - complexity considerations
 * - modular design
 *
 * Compile:
 *   g++ -std=c++17 -O2 pivot_charts.cpp -o pivot_charts
 *
 * Run:
 *   ./pivot_charts
 */

#include <algorithm>
#include <chrono>
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
#include <tuple>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;


// ============================================================================
// 1. DATA MODEL
// ============================================================================

struct Transaction {
    string transactionId;
    string date;
    string region;
    string segment;
    string category;
    string product;
    string channel;
    string salesperson;

    int quantity{};
    double sales{};
    double cost{};

    double profit() const {
        return sales - cost;
    }

    optional<double> margin() const {
        if (sales == 0.0) {
            return nullopt;
        }

        return profit() / sales;
    }
};


struct Metrics {
    double sales = 0.0;
    double cost = 0.0;
    double profit = 0.0;
    long long quantity = 0;

    double margin() const {
        if (sales == 0.0) {
            return 0.0;
        }

        return profit / sales;
    }
};


// ============================================================================
// 2. FORMATTING HELPERS
// ============================================================================

string currency(double value) {
    ostringstream stream;

    stream << fixed << setprecision(2)
           << "$" << value;

    return stream.str();
}


string percentage(double value) {
    ostringstream stream;

    stream << fixed << setprecision(2)
           << value * 100.0 << "%";

    return stream.str();
}


void section(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}


// ============================================================================
// 3. SAMPLE DATA
// ============================================================================

vector<Transaction> buildTransactions() {
    return {
        {"T001", "2026-01-05", "North", "Enterprise", "Technology", "Laptop", "Online", "Asha", 4, 4800, 3400},
        {"T002", "2026-01-08", "South", "Consumer", "Technology", "Phone", "Retail", "Ravi", 8, 6400, 5000},
        {"T003", "2026-01-12", "West", "SMB", "Office", "Chair", "Partner", "Neha", 12, 3600, 2280},
        {"T004", "2026-01-19", "East", "Enterprise", "Software", "Analytics", "Online", "Arjun", 3, 7500, 3300},
        {"T005", "2026-02-03", "North", "Consumer", "Technology", "Phone", "Retail", "Asha", 10, 8000, 6200},
        {"T006", "2026-02-10", "South", "SMB", "Office", "Desk", "Partner", "Ravi", 7, 3500, 2380},
        {"T007", "2026-02-15", "West", "Enterprise", "Software", "Analytics", "Online", "Neha", 4, 10000, 4400},
        {"T008", "2026-02-21", "East", "Consumer", "Technology", "Laptop", "Retail", "Arjun", 3, 3600, 2550},
        {"T009", "2026-03-04", "North", "SMB", "Office", "Chair", "Partner", "Asha", 15, 4500, 2850},
        {"T010", "2026-03-09", "South", "Enterprise", "Technology", "Laptop", "Online", "Ravi", 5, 6000, 4250},
        {"T011", "2026-03-16", "West", "Consumer", "Technology", "Phone", "Retail", "Neha", 14, 11200, 8680},
        {"T012", "2026-03-22", "East", "SMB", "Software", "Analytics", "Partner", "Arjun", 2, 5000, 2200},
        {"T013", "2026-04-02", "North", "Enterprise", "Software", "Analytics", "Online", "Asha", 5, 12500, 5500},
        {"T014", "2026-04-11", "South", "Consumer", "Office", "Desk", "Retail", "Ravi", 9, 4500, 3060},
        {"T015", "2026-04-17", "West", "SMB", "Technology", "Laptop", "Partner", "Neha", 6, 7200, 5100},
        {"T016", "2026-04-26", "East", "Enterprise", "Technology", "Phone", "Online", "Arjun", 7, 5600, 4340},
        {"T017", "2026-05-03", "North", "Consumer", "Technology", "Phone", "Retail", "Asha", 18, 14400, 11160},
        {"T018", "2026-05-08", "South", "SMB", "Office", "Chair", "Partner", "Ravi", 20, 6000, 3800},
        {"T019", "2026-05-15", "West", "Enterprise", "Software", "Analytics", "Online", "Neha", 6, 15000, 6600},
        {"T020", "2026-05-23", "East", "Consumer", "Technology", "Laptop", "Retail", "Arjun", 5, 6000, 4250},
        {"T021", "2026-06-04", "North", "SMB", "Office", "Desk", "Partner", "Asha", 11, 5500, 3740},
        {"T022", "2026-06-10", "South", "Enterprise", "Technology", "Laptop", "Online", "Ravi", 8, 9600, 6800},
        {"T023", "2026-06-16", "West", "Consumer", "Technology", "Phone", "Retail", "Neha", 20, 16000, 12400},
        {"T024", "2026-06-24", "East", "SMB", "Software", "Analytics", "Partner", "Arjun", 4, 10000, 4400},
        {"T025", "2026-07-03", "North", "Enterprise", "Technology", "Laptop", "Online", "Asha", 9, 10800, 7650},
        {"T026", "2026-07-09", "South", "Consumer", "Office", "Desk", "Retail", "Ravi", 13, 6500, 4420},
        {"T027", "2026-07-15", "West", "SMB", "Software", "Analytics", "Partner", "Neha", 5, 12500, 5500},
        {"T028", "2026-07-23", "East", "Enterprise", "Technology", "Phone", "Online", "Arjun", 10, 8000, 6200},
        {"T029", "2026-08-04", "North", "Consumer", "Technology", "Phone", "Retail", "Asha", 22, 17600, 13640},
        {"T030", "2026-08-12", "South", "SMB", "Office", "Chair", "Partner", "Ravi", 18, 5400, 3420},
        {"T031", "2026-08-18", "West", "Enterprise", "Software", "Analytics", "Online", "Neha", 8, 20000, 8800},
        {"T032", "2026-08-25", "East", "Consumer", "Technology", "Laptop", "Retail", "Arjun", 7, 8400, 5950},
        {"T033", "2026-09-02", "North", "SMB", "Office", "Desk", "Partner", "Asha", 14, 7000, 4760},
        {"T034", "2026-09-08", "South", "Enterprise", "Technology", "Laptop", "Online", "Ravi", 10, 12000, 8500},
        {"T035", "2026-09-16", "West", "Consumer", "Technology", "Phone", "Retail", "Neha", 25, 20000, 15500},
        {"T036", "2026-09-24", "East", "SMB", "Software", "Analytics", "Partner", "Arjun", 6, 15000, 6600},
        {"T037", "2026-09-27", "North", "Consumer", "Office", "Chair", "Retail", "Asha", 0, 0, 0}
    };
}


// ============================================================================
// 4. VALIDATION
// ============================================================================

vector<string> validateTransactions(
    const vector<Transaction>& transactions
) {
    vector<string> errors;
    unordered_set<string> ids;

    for (const auto& transaction : transactions) {
        if (!ids.insert(transaction.transactionId).second) {
            errors.push_back(
                "Duplicate transaction ID: " + transaction.transactionId
            );
        }

        if (transaction.quantity < 0) {
            errors.push_back(
                "Negative quantity: " + transaction.transactionId
            );
        }

        if (transaction.sales < 0.0) {
            errors.push_back(
                "Negative sales: " + transaction.transactionId
            );
        }

        if (transaction.cost < 0.0) {
            errors.push_back(
                "Negative cost: " + transaction.transactionId
            );
        }

        if (transaction.region.empty()) {
            errors.push_back(
                "Missing region: " + transaction.transactionId
            );
        }

        if (transaction.product.empty()) {
            errors.push_back(
                "Missing product: " + transaction.transactionId
            );
        }
    }

    return errors;
}


// ============================================================================
// 5. BUSINESS METRICS
// ============================================================================

Metrics calculateMetrics(
    const vector<Transaction>& transactions
) {
    Metrics result;

    for (const auto& transaction : transactions) {
        result.sales += transaction.sales;
        result.cost += transaction.cost;
        result.profit += transaction.profit();
        result.quantity += transaction.quantity;
    }

    return result;
}


// ============================================================================
// 6. GENERIC DIMENSION AGGREGATION
// ============================================================================

using DimensionExtractor = function<string(const Transaction&)>;

map<string, Metrics> aggregateBy(
    const vector<Transaction>& transactions,
    const DimensionExtractor& extractor
) {
    map<string, Metrics> result;

    for (const auto& transaction : transactions) {
        const string key = extractor(transaction);

        Metrics& bucket = result[key];

        bucket.sales += transaction.sales;
        bucket.cost += transaction.cost;
        bucket.profit += transaction.profit();
        bucket.quantity += transaction.quantity;
    }

    return result;
}


// ============================================================================
// 7. PIVOT TABLE DISPLAY
// ============================================================================

void printMetricTable(
    const string& title,
    const map<string, Metrics>& data
) {
    section(title);

    cout << left
         << setw(15) << "Dimension"
         << right
         << setw(15) << "Sales"
         << setw(15) << "Profit"
         << setw(12) << "Margin"
         << setw(10) << "Units"
         << "\n";

    cout << string(67, '-') << "\n";

    for (const auto& [key, metrics] : data) {
        cout << left
             << setw(15) << key
             << right
             << setw(15) << currency(metrics.sales)
             << setw(15) << currency(metrics.profit)
             << setw(12) << percentage(metrics.margin())
             << setw(10) << metrics.quantity
             << "\n";
    }
}


// ============================================================================
// 8. TWO-DIMENSIONAL PIVOT
// ============================================================================

map<string, map<string, double>> pivot2D(
    const vector<Transaction>& transactions,
    const DimensionExtractor& rowExtractor,
    const DimensionExtractor& columnExtractor
) {
    map<string, map<string, double>> result;

    for (const auto& transaction : transactions) {
        const string row = rowExtractor(transaction);
        const string column = columnExtractor(transaction);

        result[row][column] += transaction.sales;
    }

    return result;
}


void printPivotMatrix(
    const map<string, map<string, double>>& matrix
) {
    set<string> columns;

    for (const auto& [row, values] : matrix) {
        for (const auto& [column, value] : values) {
            columns.insert(column);
        }
    }

    cout << left << setw(15) << "Region";

    for (const auto& column : columns) {
        cout << right << setw(16) << column;
    }

    cout << "\n";

    for (const auto& [row, values] : matrix) {
        cout << left << setw(15) << row;

        for (const auto& column : columns) {
            const auto iterator = values.find(column);

            double value = iterator == values.end()
                ? 0.0
                : iterator->second;

            cout << right << setw(16) << currency(value);
        }

        cout << "\n";
    }
}


// ============================================================================
// 9. FILTERING
// ============================================================================

vector<Transaction> filterTransactions(
    const vector<Transaction>& transactions,
    const function<bool(const Transaction&)>& predicate
) {
    vector<Transaction> filtered;

    for (const auto& transaction : transactions) {
        if (predicate(transaction)) {
            filtered.push_back(transaction);
        }
    }

    return filtered;
}


// ============================================================================
// 10. MONTH GROUPING
// ============================================================================

string monthKey(const Transaction& transaction) {
    return transaction.date.substr(0, 7);
}


map<string, Metrics> aggregateByMonth(
    const vector<Transaction>& transactions
) {
    return aggregateBy(
        transactions,
        [](const Transaction& transaction) {
            return monthKey(transaction);
        }
    );
}


// ============================================================================
// 11. TEXTUAL BAR CHART
// ============================================================================

string makeBar(
    double value,
    double maximum,
    size_t width = 42
) {
    if (maximum <= 0.0) {
        return "";
    }

    const size_t count = static_cast<size_t>(
        round((value / maximum) * static_cast<double>(width))
    );

    return string(count, '#');
}


void printBarChart(
    const string& title,
    const map<string, double>& data
) {
    section(title);

    if (data.empty()) {
        cout << "No data.\n";
        return;
    }

    double maximum = 0.0;

    for (const auto& [label, value] : data) {
        maximum = max(maximum, value);
    }

    vector<pair<string, double>> sortedData(
        data.begin(),
        data.end()
    );

    sort(
        sortedData.begin(),
        sortedData.end(),
        [](const auto& first, const auto& second) {
            return first.second > second.second;
        }
    );

    for (const auto& [label, value] : sortedData) {
        cout << left
             << setw(15) << label
             << " | "
             << setw(42) << makeBar(value, maximum)
             << " "
             << currency(value)
             << "\n";
    }
}


// ============================================================================
// 12. RANKING
// ============================================================================

vector<pair<string, Metrics>> sortBySales(
    const map<string, Metrics>& data
) {
    vector<pair<string, Metrics>> result(
        data.begin(),
        data.end()
    );

    sort(
        result.begin(),
        result.end(),
        [](const auto& first, const auto& second) {
            return first.second.sales > second.second.sales;
        }
    );

    return result;
}


// ============================================================================
// 13. PARETO ANALYSIS
// ============================================================================

struct ParetoItem {
    string key;
    double value{};
    double share{};
    double cumulativeShare{};
};


vector<ParetoItem> calculatePareto(
    const map<string, Metrics>& data
) {
    const auto sorted = sortBySales(data);

    double total = 0.0;

    for (const auto& [key, metrics] : sorted) {
        total += metrics.sales;
    }

    vector<ParetoItem> result;

    double cumulative = 0.0;

    for (const auto& [key, metrics] : sorted) {
        cumulative += metrics.sales;

        const double share =
            total == 0.0 ? 0.0 : metrics.sales / total;

        const double cumulativeShare =
            total == 0.0 ? 0.0 : cumulative / total;

        result.push_back({
            key,
            metrics.sales,
            share,
            cumulativeShare
        });
    }

    return result;
}


// ============================================================================
// 14. GROWTH ANALYSIS
// ============================================================================

optional<double> growthRate(
    double current,
    double previous
) {
    if (previous == 0.0) {
        return nullopt;
    }

    return (current - previous) / previous;
}


vector<optional<double>> sequentialGrowth(
    const vector<double>& values
) {
    vector<optional<double>> result;

    if (values.empty()) {
        return result;
    }

    result.push_back(nullopt);

    for (size_t index = 1; index < values.size(); ++index) {
        result.push_back(
            growthRate(values[index], values[index - 1])
        );
    }

    return result;
}


// ============================================================================
// 15. ROLLING AVERAGE
// ============================================================================

vector<double> rollingAverage(
    const vector<double>& values,
    size_t window
) {
    if (window == 0) {
        throw invalid_argument(
            "Rolling-average window must be greater than zero."
        );
    }

    vector<double> result;

    for (size_t index = 0; index < values.size(); ++index) {
        const size_t start =
            index >= window - 1
                ? index - window + 1
                : 0;

        double sum = 0.0;
        size_t count = 0;

        for (size_t position = start;
             position <= index;
             ++position) {
            sum += values[position];
            ++count;
        }

        result.push_back(sum / static_cast<double>(count));
    }

    return result;
}


// ============================================================================
// 16. EXECUTIVE DASHBOARD MODEL
// ============================================================================

struct Dashboard {
    Metrics overall;
    map<string, Metrics> byRegion;
    map<string, Metrics> byProduct;
    map<string, Metrics> byChannel;
    map<string, Metrics> byMonth;
};


// ============================================================================
// 17. DASHBOARD CONSTRUCTION
// ============================================================================

Dashboard buildDashboard(
    const vector<Transaction>& transactions
) {
    Dashboard dashboard;

    dashboard.overall = calculateMetrics(transactions);

    dashboard.byRegion = aggregateBy(
        transactions,
        [](const Transaction& transaction) {
            return transaction.region;
        }
    );

    dashboard.byProduct = aggregateBy(
        transactions,
        [](const Transaction& transaction) {
            return transaction.product;
        }
    );

    dashboard.byChannel = aggregateBy(
        transactions,
        [](const Transaction& transaction) {
            return transaction.channel;
        }
    );

    dashboard.byMonth = aggregateByMonth(transactions);

    return dashboard;
}


// ============================================================================
// 18. MAIN APPLICATION
// ============================================================================

int main() {
    try {
        const vector<Transaction> transactions =
            buildTransactions();

        // --------------------------------------------------------------------
        // Validation happens before analytical processing.
        // --------------------------------------------------------------------

        section("DATA VALIDATION");

        const vector<string> validationErrors =
            validateTransactions(transactions);

        if (validationErrors.empty()) {
            cout << "All records passed validation.\n";
        } else {
            for (const string& error : validationErrors) {
                cout << "ERROR: " << error << "\n";
            }
        }

        // --------------------------------------------------------------------
        // Overall KPIs.
        // --------------------------------------------------------------------

        const Metrics overall =
            calculateMetrics(transactions);

        section("EXECUTIVE KPIs");

        cout << "Revenue:       "
             << currency(overall.sales)
             << "\n";

        cout << "Cost:          "
             << currency(overall.cost)
             << "\n";

        cout << "Profit:        "
             << currency(overall.profit)
             << "\n";

        cout << "Profit margin: "
             << percentage(overall.margin())
             << "\n";

        cout << "Units sold:    "
             << overall.quantity
             << "\n";

        // --------------------------------------------------------------------
        // Region pivot.
        // --------------------------------------------------------------------

        const auto regionMetrics =
            aggregateBy(
                transactions,
                [](const Transaction& transaction) {
                    return transaction.region;
                }
            );

        printMetricTable(
            "REGION PIVOT TABLE",
            regionMetrics
        );

        // --------------------------------------------------------------------
        // Product pivot.
        // --------------------------------------------------------------------

        const auto productMetrics =
            aggregateBy(
                transactions,
                [](const Transaction& transaction) {
                    return transaction.product;
                }
            );

        printMetricTable(
            "PRODUCT PIVOT TABLE",
            productMetrics
        );

        // --------------------------------------------------------------------
        // Channel pivot.
        // --------------------------------------------------------------------

        const auto channelMetrics =
            aggregateBy(
                transactions,
                [](const Transaction& transaction) {
                    return transaction.channel;
                }
            );

        printMetricTable(
            "CHANNEL PIVOT TABLE",
            channelMetrics
        );

        // --------------------------------------------------------------------
        // Region x segment matrix.
        // --------------------------------------------------------------------

        section("REGION × CUSTOMER SEGMENT PIVOT");

        const auto regionSegment =
            pivot2D(
                transactions,
                [](const Transaction& transaction) {
                    return transaction.region;
                },
                [](const Transaction& transaction) {
                    return transaction.segment;
                }
            );

        printPivotMatrix(regionSegment);

        // --------------------------------------------------------------------
        // Regional chart.
        // --------------------------------------------------------------------

        map<string, double> regionalSales;

        for (const auto& [region, metrics] : regionMetrics) {
            regionalSales[region] = metrics.sales;
        }

        printBarChart(
            "PIVOT CHART: SALES BY REGION",
            regionalSales
        );

        // --------------------------------------------------------------------
        // Monthly chart.
        // --------------------------------------------------------------------

        const auto monthly =
            aggregateByMonth(transactions);

        map<string, double> monthlySales;

        for (const auto& [month, metrics] : monthly) {
            monthlySales[month] = metrics.sales;
        }

        printBarChart(
            "PIVOT CHART: MONTHLY SALES",
            monthlySales
        );

        // --------------------------------------------------------------------
        // Enterprise filtering.
        // --------------------------------------------------------------------

        const auto enterpriseRows =
            filterTransactions(
                transactions,
                [](const Transaction& transaction) {
                    return transaction.segment == "Enterprise";
                }
            );

        const auto enterpriseRegionMetrics =
            aggregateBy(
                enterpriseRows,
                [](const Transaction& transaction) {
                    return transaction.region;
                }
            );

        map<string, double> enterpriseRegionalSales;

        for (const auto& [region, metrics] :
             enterpriseRegionMetrics) {
            enterpriseRegionalSales[region] =
                metrics.sales;
        }

        printBarChart(
            "ENTERPRISE SALES BY REGION",
            enterpriseRegionalSales
        );

        // --------------------------------------------------------------------
        // Ranking.
        // --------------------------------------------------------------------

        section("TOP PRODUCTS");

        const auto rankedProducts =
            sortBySales(productMetrics);

        const size_t topCount =
            min<size_t>(3, rankedProducts.size());

        for (size_t index = 0; index < topCount; ++index) {
            cout << index + 1
                 << ". "
                 << rankedProducts[index].first
                 << " - "
                 << currency(
                        rankedProducts[index].second.sales
                    )
                 << "\n";
        }

        // --------------------------------------------------------------------
        // Pareto.
        // --------------------------------------------------------------------

        section("PRODUCT PARETO ANALYSIS");

        for (const auto& item :
             calculatePareto(productMetrics)) {
            cout << left
                 << setw(12) << item.key
                 << " Share=" << setw(9)
                 << percentage(item.share)
                 << " Cumulative="
                 << percentage(item.cumulativeShare)
                 << "\n";
        }

        // --------------------------------------------------------------------
        // Monthly growth.
        // --------------------------------------------------------------------

        vector<double> monthlyValues;

        for (const auto& [month, metrics] : monthly) {
            monthlyValues.push_back(metrics.sales);
        }

        const auto growth =
            sequentialGrowth(monthlyValues);

        section("MONTH-OVER-MONTH SALES GROWTH");

        size_t growthIndex = 0;

        for (const auto& [month, metrics] : monthly) {
            cout << month << ": ";

            if (!growth[growthIndex].has_value()) {
                cout << "N/A";
            } else {
                cout << percentage(
                    growth[growthIndex].value()
                );
            }

            cout << "\n";

            ++growthIndex;
        }

        // --------------------------------------------------------------------
        // Rolling average.
        // --------------------------------------------------------------------

        const auto rolling =
            rollingAverage(monthlyValues, 3);

        section("THREE-MONTH ROLLING SALES AVERAGE");

        size_t rollingIndex = 0;

        for (const auto& [month, metrics] : monthly) {
            cout << month
                 << ": "
                 << currency(rolling[rollingIndex])
                 << "\n";

            ++rollingIndex;
        }

        // --------------------------------------------------------------------
        // Margin analysis.
        // --------------------------------------------------------------------

        section("PRODUCT MARGIN ANALYSIS");

        vector<pair<string, double>> marginRanking;

        for (const auto& [product, metrics] :
             productMetrics) {
            marginRanking.emplace_back(
                product,
                metrics.margin()
            );
        }

        sort(
            marginRanking.begin(),
            marginRanking.end(),
            [](const auto& first, const auto& second) {
                return first.second > second.second;
            }
        );

        for (const auto& [product, margin] :
             marginRanking) {
            cout << left
                 << setw(12)
                 << product
                 << percentage(margin)
                 << "\n";
        }

        // --------------------------------------------------------------------
        // Edge-case demonstration.
        // --------------------------------------------------------------------

        section("EDGE CASE: ZERO SALES");

        const Transaction zeroSales =
            transactions.back();

        const optional<double> zeroMargin =
            zeroSales.margin();

        cout << "Transaction: "
             << zeroSales.transactionId
             << "\n";

        cout << "Margin: ";

        if (zeroMargin.has_value()) {
            cout << percentage(zeroMargin.value());
        } else {
            cout << "Undefined because sales are zero.";
        }

        cout << "\n";

        // --------------------------------------------------------------------
        // Dashboard object.
        // --------------------------------------------------------------------

        const Dashboard dashboard =
            buildDashboard(transactions);

        section("DASHBOARD MODEL");

        cout << "Regions:  "
             << dashboard.byRegion.size()
             << "\n";

        cout << "Products: "
             << dashboard.byProduct.size()
             << "\n";

        cout << "Channels: "
             << dashboard.byChannel.size()
             << "\n";

        cout << "Months:   "
             << dashboard.byMonth.size()
             << "\n";

        // --------------------------------------------------------------------
        // Performance measurement.
        // --------------------------------------------------------------------

        section("PERFORMANCE MEASUREMENT");

        const auto start =
            chrono::high_resolution_clock::now();

        volatile double performanceSink = 0.0;

        for (const auto& transaction : transactions) {
            performanceSink += transaction.sales;
        }

        const auto end =
            chrono::high_resolution_clock::now();

        const chrono::duration<double, milli> elapsed =
            end - start;

        cout << "Aggregation scan time: "
             << fixed
             << setprecision(6)
             << elapsed.count()
             << " ms\n";

        cout << "Performance sink: "
             << performanceSink
             << "\n";

        // --------------------------------------------------------------------
        // Complexity discussion.
        // --------------------------------------------------------------------

        section("ALGORITHM COMPLEXITY");

        cout << "Single-pass aggregation: approximately O(n).\n";
        cout << "Two-dimensional pivot construction: O(n).\n";
        cout << "Sorting k grouped categories: O(k log k).\n";
        cout << "Filtering: O(n).\n";
        cout << "Rolling average in this educational implementation: O(n*w), "
                "where w is the window size.\n";
        cout << "A production implementation can use prefix sums for "
                "O(n) rolling-average computation.\n";

        // --------------------------------------------------------------------
        // Internal assertions.
        // --------------------------------------------------------------------

        section("INTERNAL TESTS");

        if (transactions.empty()) {
            throw runtime_error(
                "The transaction dataset must not be empty."
            );
        }

        if (overall.sales < 0.0) {
            throw runtime_error(
                "Revenue cannot be negative."
            );
        }

        double regionalTotal = 0.0;

        for (const auto& [region, metrics] :
             regionMetrics) {
            regionalTotal += metrics.sales;
        }

        if (fabs(regionalTotal - overall.sales) > 1e-9) {
            throw runtime_error(
                "Regional totals do not reconcile with revenue."
            );
        }

        cout << "All internal tests passed.\n";

        // --------------------------------------------------------------------
        // Final executive report.
        // --------------------------------------------------------------------

        section("EXECUTIVE BUSINESS PERFORMANCE REPORT");

        const auto bestRegion =
            *max_element(
                regionMetrics.begin(),
                regionMetrics.end(),
                [](const auto& first, const auto& second) {
                    return first.second.sales <
                           second.second.sales;
                }
            );

        const auto bestProduct =
            *max_element(
                productMetrics.begin(),
                productMetrics.end(),
                [](const auto& first, const auto& second) {
                    return first.second.sales <
                           second.second.sales;
                }
            );

        cout << "Revenue: "
             << currency(overall.sales)
             << "\n";

        cout << "Profit:  "
             << currency(overall.profit)
             << "\n";

        cout << "Margin:  "
             << percentage(overall.margin())
             << "\n";

        cout << "Highest-sales region: "
             << bestRegion.first
             << " ("
             << currency(bestRegion.second.sales)
             << ")\n";

        cout << "Highest-sales product: "
             << bestProduct.first
             << " ("
             << currency(bestProduct.second.sales)
             << ")\n";

        cout << "\nCase study completed successfully.\n";
    }
    catch (const exception& error) {
        cerr << "Application error: "
             << error.what()
             << "\n";

        return 1;
    }

    return 0;
}
