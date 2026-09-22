/*
 * Excel Functions: C++ Case Study
 *
 * Scenario:
 * A company receives sales records from several regions and needs a small
 * spreadsheet-like calculation engine for revenue analysis.
 *
 * The program progressively develops:
 * 1. Spreadsheet-style aggregation functions.
 * 2. Conditional functions.
 * 3. Lookup operations.
 * 4. Formula/error handling.
 * 5. A structured sales-analysis engine.
 * 6. Indexed lookup for repeated queries.
 * 7. Performance and edge-case demonstrations.
 *
 * Standard: C++17
 */

#include <algorithm>
#include <cmath>
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

using namespace std;

// ============================================================================
// 1. BASIC TYPES AND ERROR MODEL
// ============================================================================

class ExcelError : public runtime_error {
public:
    explicit ExcelError(const string& code)
        : runtime_error(code), code_(code) {}

    const string& code() const {
        return code_;
    }

private:
    string code_;
};

void section(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}

template <typename T>
void demo(const string& label, const T& value) {
    cout << left << setw(38) << label << value << "\n";
}

// ============================================================================
// 2. EXCEL-STYLE AGGREGATION
// ============================================================================

double excelSUM(const vector<double>& values) {
    return accumulate(values.begin(), values.end(), 0.0);
}

double excelAVERAGE(const vector<double>& values) {
    if (values.empty()) {
        throw ExcelError("#DIV/0!");
    }

    return excelSUM(values) / static_cast<double>(values.size());
}

double excelMIN(const vector<double>& values) {
    if (values.empty()) {
        throw ExcelError("#MIN!");
    }

    return *min_element(values.begin(), values.end());
}

double excelMAX(const vector<double>& values) {
    if (values.empty()) {
        throw ExcelError("#MAX!");
    }

    return *max_element(values.begin(), values.end());
}

double excelPRODUCT(const vector<double>& values) {
    return accumulate(
        values.begin(),
        values.end(),
        1.0,
        multiplies<double>()
    );
}

// ============================================================================
// 3. MATHEMATICAL FUNCTIONS
// ============================================================================

double excelROUND(double number, int digits = 0) {
    const double factor = pow(10.0, digits);
    return round(number * factor) / factor;
}

double excelABS(double number) {
    return fabs(number);
}

double excelPOWER(double number, double power) {
    return pow(number, power);
}

double excelSQRT(double number) {
    if (number < 0) {
        throw ExcelError("#NUM!");
    }

    return sqrt(number);
}

double excelMOD(double number, double divisor) {
    if (divisor == 0) {
        throw ExcelError("#DIV/0!");
    }

    return fmod(number, divisor);
}

double excelQUOTIENT(double numerator, double denominator) {
    if (denominator == 0) {
        throw ExcelError("#DIV/0!");
    }

    return trunc(numerator / denominator);
}

// ============================================================================
// 4. LOGICAL FUNCTIONS
// ============================================================================

bool excelIF(bool condition, bool trueValue, bool falseValue) {
    return condition ? trueValue : falseValue;
}

bool excelAND(const vector<bool>& conditions) {
    return all_of(
        conditions.begin(),
        conditions.end(),
        [](bool condition) { return condition; }
    );
}

bool excelOR(const vector<bool>& conditions) {
    return any_of(
        conditions.begin(),
        conditions.end(),
        [](bool condition) { return condition; }
    );
}

bool excelNOT(bool condition) {
    return !condition;
}

// ============================================================================
// 5. CONDITIONAL AGGREGATION
// ============================================================================

bool matchesCriteria(double value, const string& criteria) {
    if (criteria.size() >= 2 && criteria.substr(0, 2) == ">=") {
        return value >= stod(criteria.substr(2));
    }

    if (criteria.size() >= 2 && criteria.substr(0, 2) == "<=") {
        return value <= stod(criteria.substr(2));
    }

    if (criteria.size() >= 2 && criteria.substr(0, 2) == "<>") {
        return value != stod(criteria.substr(2));
    }

    if (!criteria.empty() && criteria[0] == '>') {
        return value > stod(criteria.substr(1));
    }

    if (!criteria.empty() && criteria[0] == '<') {
        return value < stod(criteria.substr(1));
    }

    if (!criteria.empty() && criteria[0] == '=') {
        return value == stod(criteria.substr(1));
    }

    return false;
}

int excelCOUNTIF(
    const vector<string>& values,
    const string& target
) {
    return count(values.begin(), values.end(), target);
}

double excelSUMIF(
    const vector<string>& criteriaRange,
    const string& target,
    const vector<double>& sumRange
) {
    if (criteriaRange.size() != sumRange.size()) {
        throw ExcelError("#VALUE!");
    }

    double total = 0;

    for (size_t index = 0; index < criteriaRange.size(); ++index) {
        if (criteriaRange[index] == target) {
            total += sumRange[index];
        }
    }

    return total;
}

double excelSUMIFS(
    const vector<double>& sumRange,
    const vector<string>& regions,
    const string& regionCriteria,
    const vector<double>& revenue,
    const string& revenueCriteria
) {
    if (
        sumRange.size() != regions.size() ||
        sumRange.size() != revenue.size()
    ) {
        throw ExcelError("#VALUE!");
    }

    double total = 0;

    for (size_t index = 0; index < sumRange.size(); ++index) {
        if (
            regions[index] == regionCriteria &&
            matchesCriteria(revenue[index], revenueCriteria)
        ) {
            total += sumRange[index];
        }
    }

    return total;
}

// ============================================================================
// 6. LOOKUP FUNCTIONS
// ============================================================================

struct Product {
    string code;
    string name;
    double price;
};

optional<Product> findProductLinear(
    const vector<Product>& products,
    const string& code
) {
    for (const auto& product : products) {
        if (product.code == code) {
            return product;
        }
    }

    return nullopt;
}

class ProductIndex {
public:
    explicit ProductIndex(const vector<Product>& products) {
        for (const auto& product : products) {
            index_[product.code] = product;
        }
    }

    optional<Product> find(const string& code) const {
        auto iterator = index_.find(code);

        if (iterator == index_.end()) {
            return nullopt;
        }

        return iterator->second;
    }

private:
    unordered_map<string, Product> index_;
};

// ============================================================================
// 7. SALES DOMAIN MODEL
// ============================================================================

struct SalesRecord {
    string orderId;
    string date;
    string region;
    string salesperson;
    string product;
    int units;
    double revenue;
    double cost;

    double profit() const {
        return revenue - cost;
    }

    double margin() const {
        if (revenue == 0) {
            return 0;
        }

        return profit() / revenue;
    }
};

class SalesAnalyzer {
public:
    explicit SalesAnalyzer(vector<SalesRecord> records)
        : records_(move(records)) {}

    double totalRevenue() const {
        double total = 0;

        for (const auto& record : records_) {
            total += record.revenue;
        }

        return total;
    }

    double totalCost() const {
        double total = 0;

        for (const auto& record : records_) {
            total += record.cost;
        }

        return total;
    }

    double totalProfit() const {
        return totalRevenue() - totalCost();
    }

    map<string, double> revenueByRegion() const {
        map<string, double> result;

        for (const auto& record : records_) {
            result[record.region] += record.revenue;
        }

        return result;
    }

    map<string, double> revenueBySalesperson() const {
        map<string, double> result;

        for (const auto& record : records_) {
            result[record.salesperson] += record.revenue;
        }

        return result;
    }

    vector<SalesRecord> highValueOrders(double threshold) const {
        vector<SalesRecord> result;

        copy_if(
            records_.begin(),
            records_.end(),
            back_inserter(result),
            [threshold](const SalesRecord& record) {
                return record.revenue >= threshold;
            }
        );

        return result;
    }

    vector<SalesRecord> productSales(const string& product) const {
        vector<SalesRecord> result;

        copy_if(
            records_.begin(),
            records_.end(),
            back_inserter(result),
            [&product](const SalesRecord& record) {
                return record.product == product;
            }
        );

        return result;
    }

    const vector<SalesRecord>& records() const {
        return records_;
    }

private:
    vector<SalesRecord> records_;
};

// ============================================================================
// 8. FORMULA ENGINE
// ============================================================================

class FormulaEngine {
public:
    static double calculateProfit(
        double revenue,
        double cost
    ) {
        // Equivalent spreadsheet expression:
        // =IF(Revenue > Cost, Revenue - Cost, 0)
        return excelIF(
            revenue > cost,
            true,
            false
        )
            ? revenue - cost
            : 0.0;
    }

    static double safeDivide(
        double numerator,
        double denominator
    ) {
        if (denominator == 0) {
            throw ExcelError("#DIV/0!");
        }

        return numerator / denominator;
    }

    static string performanceCategory(double margin) {
        if (margin >= 0.30) {
            return "High";
        }

        if (margin >= 0.20) {
            return "Medium";
        }

        return "Low";
    }
};

// ============================================================================
// 9. VALIDATION
// ============================================================================

class SalesValidator {
public:
    static void validate(const SalesRecord& record) {
        if (record.orderId.empty()) {
            throw invalid_argument("Order ID cannot be empty.");
        }

        if (record.units <= 0) {
            throw invalid_argument(
                "Units must be greater than zero for " + record.orderId
            );
        }

        if (record.revenue < 0 || record.cost < 0) {
            throw invalid_argument(
                "Revenue and cost cannot be negative for " + record.orderId
            );
        }

        if (record.cost > record.revenue) {
            // This is not necessarily mathematically invalid in a real
            // business. It can represent a loss. Therefore the condition
            // is reported, not rejected.
            cerr << "Warning: " << record.orderId
                 << " has a negative profit.\n";
        }
    }
};

// ============================================================================
// 10. DATASET
// ============================================================================

vector<SalesRecord> buildSalesData() {
    return {
        {"ORD001", "2026-01-05", "North", "Asha", "Laptop", 4, 240000, 190000},
        {"ORD002", "2026-01-08", "South", "Rahul", "Monitor", 8, 144000, 112000},
        {"ORD003", "2026-01-12", "West", "Neha", "Laptop", 3, 180000, 141000},
        {"ORD004", "2026-01-15", "East", "Vikram", "Keyboard", 20, 60000, 38000},
        {"ORD005", "2026-02-02", "North", "Asha", "Monitor", 10, 180000, 140000},
        {"ORD006", "2026-02-09", "South", "Rahul", "Laptop", 5, 300000, 235000},
        {"ORD007", "2026-02-17", "West", "Neha", "Keyboard", 30, 90000, 57000},
        {"ORD008", "2026-03-04", "East", "Vikram", "Laptop", 2, 120000, 94000},
        {"ORD009", "2026-03-11", "North", "Asha", "Keyboard", 25, 75000, 47500},
        {"ORD010", "2026-03-20", "South", "Rahul", "Monitor", 12, 216000, 168000}
    };
}

// ============================================================================
// 11. REPORTING
// ============================================================================

void printCurrency(const string& label, double value) {
    cout << left << setw(38) << label
         << fixed << setprecision(2)
         << value << "\n";
}

void printSalesReport(const SalesAnalyzer& analyzer) {
    section("Sales Analysis Report");

    const double revenue = analyzer.totalRevenue();
    const double cost = analyzer.totalCost();
    const double profit = analyzer.totalProfit();

    printCurrency("Total revenue", revenue);
    printCurrency("Total cost", cost);
    printCurrency("Total profit", profit);

    double margin = revenue == 0 ? 0 : profit / revenue;

    cout << left << setw(38) << "Profit margin"
         << fixed << setprecision(2)
         << margin * 100 << "%\n";

    cout << "\nRevenue by region:\n";

    for (const auto& [region, amount] : analyzer.revenueByRegion()) {
        cout << "  "
             << left << setw(12) << region
             << fixed << setprecision(2)
             << amount << "\n";
    }

    cout << "\nRevenue by salesperson:\n";

    for (const auto& [salesperson, amount] :
         analyzer.revenueBySalesperson()) {
        cout << "  "
             << left << setw(12) << salesperson
             << fixed << setprecision(2)
             << amount << "\n";
    }
}

// ============================================================================
// 12. FILTERING AND SORTING
// ============================================================================

void demonstrateFilteringAndSorting(
    const SalesAnalyzer& analyzer
) {
    section("Filtering and sorting");

    auto highValue = analyzer.highValueOrders(180000);

    cout << "Orders with revenue >= 180000:\n";

    for (const auto& record : highValue) {
        cout << "  "
             << record.orderId << " | "
             << record.product << " | "
             << fixed << setprecision(2)
             << record.revenue << "\n";
    }

    vector<SalesRecord> sorted = analyzer.records();

    sort(
        sorted.begin(),
        sorted.end(),
        [](const SalesRecord& first, const SalesRecord& second) {
            return first.revenue > second.revenue;
        }
    );

    cout << "\nTop revenue records:\n";

    const size_t count = min<size_t>(3, sorted.size());

    for (size_t index = 0; index < count; ++index) {
        cout << "  "
             << sorted[index].orderId << " | "
             << sorted[index].revenue << "\n";
    }
}

// ============================================================================
// 13. FUNCTION CONCEPTS
// ============================================================================

void demonstrateFunctions() {
    section("Excel-style function concepts");

    vector<double> values = {10, 20, 30, 40, 50};

    demo("SUM", excelSUM(values));
    demo("AVERAGE", excelAVERAGE(values));
    demo("MIN", excelMIN(values));
    demo("MAX", excelMAX(values));
    demo("PRODUCT", excelPRODUCT({2, 3, 4}));
    demo("ROUND", excelROUND(123.4567, 2));
    demo("ABS", excelABS(-42));
    demo("POWER", excelPOWER(2, 8));
    demo("SQRT", excelSQRT(144));
    demo("MOD", excelMOD(17, 5));
    demo("QUOTIENT", excelQUOTIENT(17, 5));

    demo(
        "AND",
        excelAND({true, true, true})
    );

    demo(
        "OR",
        excelOR({false, true, false})
    );

    demo(
        "NOT",
        excelNOT(false)
    );
}

// ============================================================================
// 14. CONDITIONAL SALES FUNCTIONS
// ============================================================================

void demonstrateConditionalSales(
    const SalesAnalyzer& analyzer
) {
    section("Conditional sales analysis");

    vector<string> regions;
    vector<double> revenues;

    for (const auto& record : analyzer.records()) {
        regions.push_back(record.region);
        revenues.push_back(record.revenue);
    }

    demo(
        "COUNTIF North",
        excelCOUNTIF(regions, "North")
    );

    demo(
        "SUMIF North",
        excelSUMIF(regions, "North", revenues)
    );

    demo(
        "SUMIFS South and revenue >= 200000",
        excelSUMIFS(
            revenues,
            regions,
            "South",
            revenues,
            ">=200000"
        )
    );
}

// ============================================================================
// 15. LOOKUP CASE STUDY
// ============================================================================

void demonstrateLookupCaseStudy() {
    section("Product lookup case study");

    vector<Product> products = {
        {"P100", "Laptop", 60000},
        {"P200", "Monitor", 18000},
        {"P300", "Keyboard", 3000},
        {"P400", "Mouse", 1500}
    };

    auto product = findProductLinear(products, "P200");

    if (product) {
        demo("Linear lookup product", product->name);
        printCurrency("Linear lookup price", product->price);
    }

    auto missing = findProductLinear(products, "P999");

    demo("Missing product found", missing.has_value());

    ProductIndex index(products);

    auto indexed = index.find("P400");

    if (indexed) {
        demo("Indexed lookup product", indexed->name);
        printCurrency("Indexed lookup price", indexed->price);
    }
}

// ============================================================================
// 16. FORMULA APPLICATION
// ============================================================================

void demonstrateFormulaEngine(
    const SalesAnalyzer& analyzer
) {
    section("Formula engine");

    for (const auto& record : analyzer.records()) {
        const double calculatedProfit =
            FormulaEngine::calculateProfit(
                record.revenue,
                record.cost
            );

        const double margin = record.revenue == 0
            ? 0
            : calculatedProfit / record.revenue;

        cout << record.orderId
             << " | profit = "
             << fixed << setprecision(2)
             << calculatedProfit
             << " | category = "
             << FormulaEngine::performanceCategory(margin)
             << "\n";
    }
}

// ============================================================================
// 17. VALIDATION AND ERROR HANDLING
// ============================================================================

void demonstrateValidation(
    const vector<SalesRecord>& records
) {
    section("Validation and error handling");

    for (const auto& record : records) {
        try {
            SalesValidator::validate(record);
        }
        catch (const exception& error) {
            cerr << "Validation failure: "
                 << error.what() << "\n";
        }
    }

    try {
        FormulaEngine::safeDivide(100, 0);
    }
    catch (const ExcelError& error) {
        demo("Safe divide error", error.code());
    }

    try {
        excelSQRT(-1);
    }
    catch (const ExcelError& error) {
        demo("SQRT negative error", error.code());
    }
}

// ============================================================================
// 18. PERFORMANCE CONSIDERATIONS
// ============================================================================

void demonstrateComplexity() {
    section("Performance considerations");

    cout << "Vector linear search: O(n)\n";
    cout << "unordered_map average lookup: O(1)\n";
    cout << "unordered_map construction: O(n) average\n";
    cout << "Sorting records: O(n log n)\n";
    cout << "SUM over n values: O(n)\n";
    cout << "Memory for a vector of n records: O(n)\n";

    cout << "\nTrade-off:\n";
    cout << "An index improves repeated lookup speed but requires additional memory\n";
    cout << "and an initial construction cost.\n";
}

// ============================================================================
// 19. EDGE CASES
// ============================================================================

void demonstrateEdgeCases() {
    section("Edge cases");

    try {
        excelAVERAGE({});
    }
    catch (const ExcelError& error) {
        demo("AVERAGE empty range", error.code());
    }

    try {
        excelMIN({});
    }
    catch (const ExcelError& error) {
        demo("MIN empty range", error.code());
    }

    try {
        excelMOD(10, 0);
    }
    catch (const ExcelError& error) {
        demo("MOD by zero", error.code());
    }

    try {
        excelQUOTIENT(10, 0);
    }
    catch (const ExcelError& error) {
        demo("QUOTIENT by zero", error.code());
    }
}

// ============================================================================
// 20. MAIN
// ============================================================================

int main() {
    cout << "EXCEL FUNCTIONS: C++ TECHNICAL CASE STUDY\n";

    try {
        vector<SalesRecord> sales = buildSalesData();

        demonstrateFunctions();

        SalesAnalyzer analyzer(sales);

        printSalesReport(analyzer);
        demonstrateFilteringAndSorting(analyzer);
        demonstrateConditionalSales(analyzer);
        demonstrateLookupCaseStudy();
        demonstrateFormulaEngine(analyzer);
        demonstrateValidation(sales);
        demonstrateComplexity();
        demonstrateEdgeCases();

        section("Case study completed");
        cout << "The spreadsheet-style sales calculation system completed successfully.\n";
    }
    catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
