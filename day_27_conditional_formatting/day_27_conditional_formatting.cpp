/*
 * Conditional Formatting Case Study
 * ----------------------------------
 *
 * Scenario:
 *   A retail analytics system receives monthly branch-performance data.
 *   Analysts need a machine-readable decision layer that identifies:
 *
 *     - values below target
 *     - values above expected limits
 *     - missing values
 *     - duplicate measurements
 *     - statistical anomalies
 *     - IQR outliers
 *     - high return rates
 *     - negative growth
 *     - trend direction
 *
 * The program then maps those analytical findings to conditional-formatting
 * decisions that could be consumed by a spreadsheet, dashboard, reporting
 * system, or web application.
 *
 * Standard:
 *   C++17 or later
 *
 * No external libraries are required.
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;


// ============================================================================
// 1. BASIC TYPES
// ============================================================================

enum class Severity {
    Normal = 0,
    Information = 1,
    Warning = 2,
    Critical = 3
};


struct FormatStyle {
    string background;
    string foreground;
    bool bold = false;
    string marker = "NORMAL";
};


struct SalesRecord {
    string month;
    optional<double> sales;
    double target;
    optional<double> growth;
    double returns;
};


// ============================================================================
// 2. FORMATTING HELPERS
// ============================================================================

string formatNumber(double value, int decimals = 0) {
    ostringstream output;

    output << fixed << setprecision(decimals) << value;

    return output.str();
}


string formatOptional(const optional<double>& value, int decimals = 0) {
    if (!value.has_value()) {
        return "MISSING";
    }

    return formatNumber(*value, decimals);
}


string formatPercent(const optional<double>& value) {
    if (!value.has_value()) {
        return "MISSING";
    }

    ostringstream output;
    output << fixed << setprecision(1) << (*value * 100.0) << "%";

    return output.str();
}


// ============================================================================
// 3. STATISTICAL FUNCTIONS
// ============================================================================

double mean(const vector<double>& values) {
    if (values.empty()) {
        throw invalid_argument("Mean requires at least one value.");
    }

    const double total =
        accumulate(values.begin(), values.end(), 0.0);

    return total / static_cast<double>(values.size());
}


double populationStandardDeviation(const vector<double>& values) {
    if (values.empty()) {
        throw invalid_argument(
            "Standard deviation requires at least one value."
        );
    }

    const double average = mean(values);

    double squaredDistance = 0.0;

    for (double value : values) {
        squaredDistance += pow(value - average, 2.0);
    }

    return sqrt(
        squaredDistance / static_cast<double>(values.size())
    );
}


optional<double> zScore(
    double value,
    const vector<double>& population
) {
    if (population.empty()) {
        return nullopt;
    }

    const double deviation =
        populationStandardDeviation(population);

    if (deviation == 0.0) {
        return nullopt;
    }

    return (value - mean(population)) / deviation;
}


// ============================================================================
// 4. PERCENTILE AND IQR
// ============================================================================

double percentile(
    vector<double> values,
    double fraction
) {
    if (values.empty()) {
        throw invalid_argument(
            "Percentile requires at least one value."
        );
    }

    if (fraction < 0.0 || fraction > 1.0) {
        throw invalid_argument(
            "Percentile fraction must be between 0 and 1."
        );
    }

    sort(values.begin(), values.end());

    const double position =
        (static_cast<double>(values.size()) - 1.0) * fraction;

    const size_t lower =
        static_cast<size_t>(floor(position));

    const size_t upper =
        static_cast<size_t>(ceil(position));

    if (lower == upper) {
        return values[lower];
    }

    const double weight =
        position - static_cast<double>(lower);

    return values[lower] +
           (values[upper] - values[lower]) * weight;
}


struct IQRBounds {
    double lower;
    double upper;
};


optional<IQRBounds> calculateIQRBounds(
    const vector<double>& values
) {
    if (values.size() < 4) {
        return nullopt;
    }

    const double q1 = percentile(values, 0.25);
    const double q3 = percentile(values, 0.75);
    const double iqr = q3 - q1;

    return IQRBounds{
        q1 - 1.5 * iqr,
        q3 + 1.5 * iqr
    };
}


// ============================================================================
// 5. TREND ANALYSIS
// ============================================================================

optional<double> linearSlope(
    const vector<optional<double>>& values
) {
    vector<pair<double, double>> points;

    for (size_t index = 0; index < values.size(); ++index) {
        if (values[index].has_value()) {
            points.emplace_back(
                static_cast<double>(index),
                *values[index]
            );
        }
    }

    if (points.size() < 2) {
        return nullopt;
    }

    double xMean = 0.0;
    double yMean = 0.0;

    for (const auto& point : points) {
        xMean += point.first;
        yMean += point.second;
    }

    xMean /= static_cast<double>(points.size());
    yMean /= static_cast<double>(points.size());

    double numerator = 0.0;
    double denominator = 0.0;

    for (const auto& point : points) {
        numerator +=
            (point.first - xMean) *
            (point.second - yMean);

        denominator +=
            pow(point.first - xMean, 2.0);
    }

    if (denominator == 0.0) {
        return nullopt;
    }

    return numerator / denominator;
}


string classifyTrend(
    const vector<optional<double>>& values
) {
    vector<double> valid;

    for (const auto& value : values) {
        if (value.has_value()) {
            valid.push_back(*value);
        }
    }

    const auto slope = linearSlope(values);

    if (!slope.has_value() || valid.empty()) {
        return "INSUFFICIENT DATA";
    }

    const double average = mean(valid);

    if (average == 0.0) {
        if (abs(*slope) < 1e-12) {
            return "FLAT";
        }

        return *slope > 0.0 ? "UP" : "DOWN";
    }

    const double relativeSlope =
        *slope / abs(average);

    if (relativeSlope > 0.01) {
        return "UP";
    }

    if (relativeSlope < -0.01) {
        return "DOWN";
    }

    return "FLAT";
}


// ============================================================================
// 6. MOVING AVERAGE
// ============================================================================

vector<optional<double>> movingAverage(
    const vector<optional<double>>& values,
    size_t window
) {
    if (window == 0) {
        throw invalid_argument(
            "Moving-average window must be greater than zero."
        );
    }

    vector<optional<double>> result(values.size());

    for (size_t index = 0; index < values.size(); ++index) {
        if (index + 1 < window) {
            result[index] = nullopt;
            continue;
        }

        vector<double> valid;

        const size_t start =
            index + 1 - window;

        for (size_t position = start;
             position <= index;
             ++position) {
            if (values[position].has_value()) {
                valid.push_back(*values[position]);
            }
        }

        if (valid.size() < window) {
            result[index] = nullopt;
        } else {
            result[index] = mean(valid);
        }
    }

    return result;
}


// ============================================================================
// 7. CONDITIONAL-FORMATTING RULES
// ============================================================================

using Condition =
    bool (*)(const optional<double>& value);


bool isMissing(
    const optional<double>& value
) {
    return !value.has_value();
}


bool isBelow70K(
    const optional<double>& value
) {
    return value.has_value() && *value < 70000.0;
}


bool isAbove100K(
    const optional<double>& value
) {
    return value.has_value() && *value > 100000.0;
}


struct Rule {
    string name;
    Condition condition;
    FormatStyle style;
    int priority;
    Severity severity;
    bool stopIfTrue;
};


struct CellDecision {
    optional<double> value;
    FormatStyle style;
    vector<string> reasons;
};


// ============================================================================
// 8. RULE ENGINE
// ============================================================================

vector<CellDecision> applyRules(
    const vector<optional<double>>& values,
    vector<Rule> rules
) {
    sort(
        rules.begin(),
        rules.end(),
        [](const Rule& first, const Rule& second) {
            return first.priority < second.priority;
        }
    );

    vector<CellDecision> decisions;

    for (const auto& value : values) {
        CellDecision decision{
            value,
            FormatStyle{},
            {}
        };

        bool styleSelected = false;

        for (const auto& rule : rules) {
            bool matched = false;

            try {
                matched = rule.condition(value);
            } catch (...) {
                matched = false;
            }

            if (!matched) {
                continue;
            }

            decision.reasons.push_back(rule.name);

            if (!styleSelected) {
                decision.style = rule.style;
                styleSelected = true;
            }

            if (rule.stopIfTrue) {
                break;
            }
        }

        decisions.push_back(decision);
    }

    return decisions;
}


// ============================================================================
// 9. BUSINESS EXCEPTIONS
// ============================================================================

string targetException(
    const SalesRecord& record
) {
    if (!record.sales.has_value()) {
        return "Missing sales value";
    }

    if (record.target == 0.0) {
        return "Target is zero";
    }

    const double ratio =
        *record.sales / record.target;

    if (ratio < 0.80) {
        return "Severely below target";
    }

    if (ratio < 1.00) {
        return "Below target";
    }

    if (ratio > 1.50) {
        return "Unusually high sales";
    }

    return "";
}


string returnException(
    const SalesRecord& record
) {
    if (!record.sales.has_value()) {
        return "";
    }

    if (*record.sales == 0.0) {
        return "";
    }

    const double returnRate =
        record.returns / *record.sales;

    if (returnRate >= 0.05) {
        ostringstream output;

        output << "High return rate: "
               << fixed
               << setprecision(1)
               << returnRate * 100.0
               << "%";

        return output.str();
    }

    return "";
}


// ============================================================================
// 10. COLOR SCALE
// ============================================================================

int interpolate(
    int start,
    int end,
    double ratio
) {
    ratio = max(0.0, min(1.0, ratio));

    return static_cast<int>(
        round(
            start +
            (end - start) * ratio
        )
    );
}


string rgbHex(
    int red,
    int green,
    int blue
) {
    ostringstream output;

    output << "#"
           << hex
           << uppercase
           << setw(2)
           << setfill('0')
           << red
           << setw(2)
           << green
           << setw(2)
           << blue;

    return output.str();
}


string colorScale(
    double value,
    double minimum,
    double maximum
) {
    if (minimum == maximum) {
        return "#D9EAD3";
    }

    const double ratio =
        (value - minimum) /
        (maximum - minimum);

    const int red =
        interpolate(255, 190, ratio);

    const int green =
        interpolate(220, 255, ratio);

    const int blue =
        interpolate(220, 200, ratio);

    return rgbHex(red, green, blue);
}


// ============================================================================
// 11. DATA BAR
// ============================================================================

size_t dataBarLength(
    double value,
    double minimum,
    double maximum,
    size_t width = 30
) {
    if (maximum == minimum) {
        return width;
    }

    const double ratio =
        max(
            0.0,
            min(
                1.0,
                (value - minimum) /
                (maximum - minimum)
            )
        );

    return static_cast<size_t>(
        round(ratio * static_cast<double>(width))
    );
}


string dataBar(
    double value,
    double minimum,
    double maximum,
    size_t width = 30
) {
    const size_t length =
        dataBarLength(value, minimum, maximum, width);

    return string(length, '#') +
           string(width - length, ' ');
}


// ============================================================================
// 12. SAMPLE DATA
// ============================================================================

vector<SalesRecord> createDataset() {
    return {
        {"Jan", 82000, 80000, 0.04, 1200},
        {"Feb", 84500, 81000, 0.03, 1300},
        {"Mar", 87000, 83000, 0.03, 1400},
        {"Apr", 61000, 84000, -0.30, 3100},
        {"May", 89000, 85000, 0.46, 1500},
        {"Jun", 91000, 87000, 0.02, 1600},
        {"Jul", 91000, 88000, 0.00, 1700},
        {"Aug", nullopt, 90000, nullopt, 1800},
        {"Sep", 93000, 92000, 0.02, 1900},
        {"Oct", 210000, 94000, 1.26, 2200},
        {"Nov", 95000, 96000, -0.55, 7000},
        {"Dec", 99000, 98000, 0.04, 2000}
    };
}


// ============================================================================
// 13. DATA VALIDATION
// ============================================================================

void validateDataset(
    const vector<SalesRecord>& records
) {
    if (records.empty()) {
        throw invalid_argument(
            "Dataset cannot be empty."
        );
    }

    for (const auto& record : records) {
        if (record.month.empty()) {
            throw invalid_argument(
                "Every record must have a month."
            );
        }

        if (!isfinite(record.target) ||
            !isfinite(record.returns)) {
            throw invalid_argument(
                "Target and returns must be finite."
            );
        }

        if (record.sales.has_value() &&
            !isfinite(*record.sales)) {
            throw invalid_argument(
                "Sales values must be finite."
            );
        }

        if (record.growth.has_value() &&
            !isfinite(*record.growth)) {
            throw invalid_argument(
                "Growth values must be finite."
            );
        }
    }
}


// ============================================================================
// 14. SALES VALUE EXTRACTION
// ============================================================================

vector<optional<double>> extractSales(
    const vector<SalesRecord>& records
) {
    vector<optional<double>> values;

    for (const auto& record : records) {
        values.push_back(record.sales);
    }

    return values;
}


vector<double> validSales(
    const vector<SalesRecord>& records
) {
    vector<double> values;

    for (const auto& record : records) {
        if (record.sales.has_value()) {
            values.push_back(*record.sales);
        }
    }

    return values;
}


// ============================================================================
// 15. DUPLICATE DETECTION
// ============================================================================

map<double, size_t> frequencyTable(
    const vector<double>& values
) {
    map<double, size_t> frequency;

    for (double value : values) {
        ++frequency[value];
    }

    return frequency;
}


// ============================================================================
// 16. COMPLETE REPORT
// ============================================================================

void printReport(
    const vector<SalesRecord>& records
) {
    const vector<double> sales =
        validSales(records);

    const double minimum =
        *min_element(sales.begin(), sales.end());

    const double maximum =
        *max_element(sales.begin(), sales.end());

    const auto iqr =
        calculateIQRBounds(sales);

    const auto frequencies =
        frequencyTable(sales);

    cout << "\n"
         << string(110, '=')
         << "\n";

    cout << "RETAIL SALES CONDITIONAL-FORMATTING ANALYSIS\n";

    cout << string(110, '=')
         << "\n";

    cout << left
         << setw(6) << "Month"
         << right
         << setw(12) << "Sales"
         << setw(12) << "Target"
         << setw(10) << "Growth"
         << setw(10) << "Z-Score"
         << setw(10) << "IQR"
         << setw(12) << "Duplicate"
         << "  Exception"
         << "\n";

    cout << string(110, '-')
         << "\n";

    for (const auto& record : records) {
        cout << left
             << setw(6)
             << record.month
             << right
             << setw(12)
             << formatOptional(record.sales)
             << setw(12)
             << formatNumber(record.target)
             << setw(10)
             << formatPercent(record.growth);

        if (record.sales.has_value()) {
            const auto score =
                zScore(*record.sales, sales);

            if (score.has_value()) {
                cout << setw(10)
                     << fixed
                     << setprecision(2)
                     << *score;
            } else {
                cout << setw(10)
                     << "N/A";
            }

            bool outlier = false;

            if (iqr.has_value()) {
                outlier =
                    *record.sales < iqr->lower ||
                    *record.sales > iqr->upper;
            }

            cout << setw(10)
                 << (outlier ? "YES" : "NO");

            const auto frequency =
                frequencies.find(*record.sales);

            const bool duplicate =
                frequency != frequencies.end() &&
                frequency->second > 1;

            cout << setw(12)
                 << (duplicate ? "YES" : "NO");
        } else {
            cout << setw(10) << "N/A"
                 << setw(10) << "N/A"
                 << setw(12) << "NO";
        }

        vector<string> exceptions;

        const string targetProblem =
            targetException(record);

        const string returnProblem =
            returnException(record);

        if (!targetProblem.empty()) {
            exceptions.push_back(targetProblem);
        }

        if (!returnProblem.empty()) {
            exceptions.push_back(returnProblem);
        }

        if (record.growth.has_value() &&
            *record.growth < 0.0) {
            exceptions.push_back("Negative growth");
        }

        cout << "  ";

        if (exceptions.empty()) {
            cout << "None";
        } else {
            for (size_t index = 0;
                 index < exceptions.size();
                 ++index) {
                if (index > 0) {
                    cout << " | ";
                }

                cout << exceptions[index];
            }
        }

        cout << "\n";
    }
}


// ============================================================================
// 17. COLOR SCALE AND DATA BAR REPORT
// ============================================================================

void printVisualAnalysis(
    const vector<SalesRecord>& records
) {
    const vector<double> sales =
        validSales(records);

    const double minimum =
        *min_element(sales.begin(), sales.end());

    const double maximum =
        *max_element(sales.begin(), sales.end());

    cout << "\n"
         << string(90, '=')
         << "\n";

    cout << "VISUAL MAGNITUDE ANALYSIS\n";

    cout << string(90, '=')
         << "\n";

    for (const auto& record : records) {
        cout << setw(3)
             << record.month
             << " | ";

        if (!record.sales.has_value()) {
            cout << "MISSING\n";
            continue;
        }

        cout << dataBar(
                    *record.sales,
                    minimum,
                    maximum
                )
             << " | "
             << formatNumber(*record.sales)
             << " | "
             << colorScale(
                    *record.sales,
                    minimum,
                    maximum
                )
             << "\n";
    }
}


// ============================================================================
// 18. TREND REPORT
// ============================================================================

void printTrendReport(
    const vector<SalesRecord>& records
) {
    const auto sales =
        extractSales(records);

    const auto averages =
        movingAverage(sales, 3);

    const auto slope =
        linearSlope(sales);

    cout << "\n"
         << string(90, '=')
         << "\n";

    cout << "TREND ANALYSIS\n";

    cout << string(90, '=')
         << "\n";

    cout << "Trend direction: "
         << classifyTrend(sales)
         << "\n";

    if (slope.has_value()) {
        cout << "Regression slope: "
             << fixed
             << setprecision(2)
             << *slope
             << "\n";
    } else {
        cout << "Regression slope: unavailable\n";
    }

    cout << "\n3-period moving average:\n";

    for (size_t index = 0;
         index < records.size();
         ++index) {
        cout << setw(3)
             << records[index].month
             << " | ";

        if (averages[index].has_value()) {
            cout << fixed
                 << setprecision(2)
                 << *averages[index];
        } else {
            cout << "insufficient data";
        }

        cout << "\n";
    }
}


// ============================================================================
// 19. RULE PRECEDENCE
// ============================================================================

void demonstrateRulePrecedence() {
    vector<optional<double>> values = {
        nullopt,
        50000.0,
        150000.0
    };

    const FormatStyle critical{
        "#8B0000",
        "#FFFFFF",
        true,
        "CRITICAL"
    };

    const FormatStyle warning{
        "#FFD966",
        "#000000",
        true,
        "WARNING"
    };

    const FormatStyle information{
        "#D9EAF7",
        "#000000",
        false,
        "INFO"
    };

    vector<Rule> rules = {
        {
            "Missing value",
            isMissing,
            critical,
            1,
            Severity::Critical,
            true
        },
        {
            "Below 70K",
            isBelow70K,
            warning,
            2,
            Severity::Warning,
            false
        },
        {
            "Above 100K",
            isAbove100K,
            information,
            3,
            Severity::Information,
            false
        }
    };

    const auto decisions =
        applyRules(values, rules);

    cout << "\n"
         << string(90, '=')
         << "\n";

    cout << "RULE PRECEDENCE\n";

    cout << string(90, '=')
         << "\n";

    for (const auto& decision : decisions) {
        cout << "Value: "
             << formatOptional(decision.value)
             << " | Style: "
             << decision.style.marker
             << " | Rules: ";

        if (decision.reasons.empty()) {
            cout << "None";
        } else {
            for (size_t index = 0;
                 index < decision.reasons.size();
                 ++index) {
                if (index > 0) {
                    cout << ", ";
                }

                cout << decision.reasons[index];
            }
        }

        cout << "\n";
    }
}


// ============================================================================
// 20. TESTS
// ============================================================================

void assertCondition(
    bool condition,
    const string& message
) {
    if (!condition) {
        throw runtime_error(
            "Test failed: " + message
        );
    }
}


void runTests() {
    assertCondition(
        abs(mean({10.0, 20.0, 30.0}) - 20.0) < 1e-9,
        "mean should equal 20"
    );

    assertCondition(
        isMissing(nullopt),
        "nullopt should be treated as missing"
    );

    assertCondition(
        isBelow70K(50000.0),
        "50000 should be below 70000"
    );

    assertCondition(
        !isAbove100K(50000.0),
        "50000 should not exceed 100000"
    );

    const auto average =
        movingAverage(
            vector<optional<double>>{
                10.0,
                20.0,
                30.0
            },
            2
        );

    assertCondition(
        average[1].has_value() &&
        abs(*average[1] - 15.0) < 1e-9,
        "two-period moving average should equal 15"
    );

    assertCondition(
        targetException(
            SalesRecord{
                "Test",
                50000.0,
                100000.0,
                0.0,
                1000.0
            }
        ) == "Severely below target",
        "target exception should detect severe underperformance"
    );

    assertCondition(
        !calculateIQRBounds(
            vector<double>{10.0, 10.0, 10.0}
        ).has_value(),
        "IQR should require sufficient data"
    );

    cout << "\nAll C++ tests passed.\n";
}


// ============================================================================
// 21. MAIN CASE STUDY
// ============================================================================

int main() {
    try {
        const auto records =
            createDataset();

        validateDataset(records);

        printReport(records);

        printVisualAnalysis(records);

        printTrendReport(records);

        demonstrateRulePrecedence();

        runTests();

        cout << "\n"
             << string(90, '=')
             << "\n";

        cout << "CASE STUDY COMPLETED SUCCESSFULLY\n";

        cout << string(90, '=')
             << "\n";

        /*
         * Architectural interpretation:
         *
         * 1. SalesRecord represents source data.
         * 2. Statistical functions derive analytical measures.
         * 3. Exception functions represent business rules.
         * 4. Rule represents a conditional-formatting decision.
         * 5. applyRules() resolves priority and precedence.
         * 6. Reporting functions transform decisions into presentation.
         *
         * This separation is important in production systems because
         * changing a visual style should not require rewriting the
         * underlying business logic.
         */
    }
    catch (const exception& error) {
        cerr << "Application error: "
             << error.what()
             << "\n";

        return 1;
    }

    return 0;
}
