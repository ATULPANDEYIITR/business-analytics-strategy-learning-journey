/*
 * Excel Tables: Structured Data and Dynamic Calculations
 *
 * Industry-style case study:
 * Sales Operations Table and Dynamic Revenue Analysis
 *
 * Standard: C++17
 *
 * The program models the underlying principles of an Excel Table:
 * - structured rows and named fields,
 * - calculated columns,
 * - automatic recalculation,
 * - validation,
 * - filtering,
 * - sorting,
 * - aggregation,
 * - indexed lookups,
 * - dependency-aware calculations,
 * - reporting,
 * - error handling,
 * - performance considerations.
 */

#include <algorithm>
#include <cassert>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

// ---------------------------------------------------------------------------
// 1. DOMAIN MODEL
// ---------------------------------------------------------------------------

struct SalesRecord {
    int orderId;
    string customer;
    string region;
    string product;
    string category;
    int quantity;
    double unitPrice;
    double discountRate;

    // Calculated columns are stored separately from raw input fields.
    double grossAmount = 0.0;
    double discountAmount = 0.0;
    double netAmount = 0.0;
    double cost = 0.0;
    double profit = 0.0;
    double margin = 0.0;
    string orderSize;
};


// ---------------------------------------------------------------------------
// 2. VALIDATION
// ---------------------------------------------------------------------------

class ValidationError : public runtime_error {
public:
    explicit ValidationError(const string& message)
        : runtime_error(message) {}
};

void validateRecord(const SalesRecord& record) {
    if (record.orderId <= 0) {
        throw ValidationError("Order ID must be positive.");
    }

    if (record.customer.empty()) {
        throw ValidationError("Customer name is required.");
    }

    const vector<string> allowedRegions{
        "North", "South", "East", "West"
    };

    if (find(
            allowedRegions.begin(),
            allowedRegions.end(),
            record.region
        ) == allowedRegions.end()) {
        throw ValidationError("Invalid region: " + record.region);
    }

    if (record.quantity <= 0) {
        throw ValidationError("Quantity must be positive.");
    }

    if (!isfinite(record.unitPrice) || record.unitPrice < 0) {
        throw ValidationError("Unit price must be non-negative.");
    }

    if (!isfinite(record.discountRate) ||
        record.discountRate < 0 ||
        record.discountRate > 1) {
        throw ValidationError(
            "Discount rate must be between 0 and 1."
        );
    }
}


// ---------------------------------------------------------------------------
// 3. CALCULATED COLUMN ENGINE
// ---------------------------------------------------------------------------

class SalesCalculationEngine {
public:
    static void calculate(SalesRecord& record) {
        // Equivalent to an Excel calculated column:
        // =[@Quantity]*[@[Unit Price]]
        record.grossAmount =
            record.quantity * record.unitPrice;

        // =[@[Gross Amount]]*[@[Discount Rate]]
        record.discountAmount =
            record.grossAmount * record.discountRate;

        // =[@[Gross Amount]]-[@[Discount Amount]]
        record.netAmount =
            record.grossAmount - record.discountAmount;

        // Cost is a business assumption for this case study.
        record.cost =
            record.netAmount * 0.70;

        // Profit depends on net revenue and cost.
        record.profit =
            record.netAmount - record.cost;

        // Division by zero is explicitly prevented.
        if (record.netAmount != 0.0) {
            record.margin =
                record.profit / record.netAmount;
        } else {
            record.margin = 0.0;
        }

        record.orderSize =
            record.netAmount >= 100000.0
                ? "Large"
                : "Standard";
    }
};


// ---------------------------------------------------------------------------
// 4. TABLE CLASS
// ---------------------------------------------------------------------------

class SalesTable {
private:
    vector<SalesRecord> rows;

    // This index models a lookup-optimized structure similar in purpose
    // to using a key for repeated XLOOKUP-like operations.
    unordered_map<int, size_t> orderIndex;

public:
    void addRecord(SalesRecord record) {
        validateRecord(record);

        if (orderIndex.find(record.orderId) != orderIndex.end()) {
            throw ValidationError(
                "Duplicate Order ID: " +
                to_string(record.orderId)
            );
        }

        // Calculated columns are populated automatically.
        SalesCalculationEngine::calculate(record);

        const size_t position = rows.size();
        rows.push_back(record);
        orderIndex[record.orderId] = position;
    }

    void recalculate() {
        for (auto& record : rows) {
            SalesCalculationEngine::calculate(record);
        }
    }

    size_t size() const {
        return rows.size();
    }

    const vector<SalesRecord>& data() const {
        return rows;
    }

    optional<reference_wrapper<const SalesRecord>>
    lookupByOrderId(int orderId) const {
        auto iterator = orderIndex.find(orderId);

        if (iterator == orderIndex.end()) {
            return nullopt;
        }

        return cref(rows.at(iterator->second));
    }

    vector<SalesRecord> filter(
        const function<bool(const SalesRecord&)>& predicate
    ) const {
        vector<SalesRecord> result;

        for (const auto& record : rows) {
            if (predicate(record)) {
                result.push_back(record);
            }
        }

        return result;
    }

    vector<SalesRecord> sortedByNetAmount(
        bool descending = true
    ) const {
        vector<SalesRecord> result = rows;

        sort(
            result.begin(),
            result.end(),
            [descending](
                const SalesRecord& left,
                const SalesRecord& right
            ) {
                if (descending) {
                    return left.netAmount > right.netAmount;
                }

                return left.netAmount < right.netAmount;
            }
        );

        return result;
    }

    double totalSales() const {
        double total = 0.0;

        for (const auto& record : rows) {
            total += record.netAmount;
        }

        return total;
    }

    double totalProfit() const {
        double total = 0.0;

        for (const auto& record : rows) {
            total += record.profit;
        }

        return total;
    }

    double averageOrderValue() const {
        if (rows.empty()) {
            throw runtime_error(
                "Cannot calculate average of an empty table."
            );
        }

        return totalSales() /
               static_cast<double>(rows.size());
    }

    map<string, double> salesByRegion() const {
        map<string, double> totals;

        for (const auto& record : rows) {
            totals[record.region] += record.netAmount;
        }

        return totals;
    }

    map<string, int> unitsByCategory() const {
        map<string, int> totals;

        for (const auto& record : rows) {
            totals[record.category] += record.quantity;
        }

        return totals;
    }
};


// ---------------------------------------------------------------------------
// 5. DISPLAY FUNCTIONS
// ---------------------------------------------------------------------------

void printCurrency(double value) {
    cout << fixed
         << setprecision(2)
         << value;
}

void printRecord(const SalesRecord& record) {
    cout
        << setw(6) << record.orderId
        << setw(12) << record.customer
        << setw(10) << record.region
        << setw(14) << record.product
        << setw(8) << record.quantity
        << setw(14);

    printCurrency(record.netAmount);

    cout
        << setw(12);

    printCurrency(record.profit);

    cout
        << setw(10)
        << fixed
        << setprecision(2)
        << record.margin * 100
        << "%\n";
}

void printHeader() {
    cout
        << setw(6) << "ID"
        << setw(12) << "Customer"
        << setw(10) << "Region"
        << setw(14) << "Product"
        << setw(8) << "Qty"
        << setw(14) << "Net Sales"
        << setw(12) << "Profit"
        << setw(10) << "Margin"
        << '\n';

    cout << string(96, '-') << '\n';
}

void printTable(const vector<SalesRecord>& records) {
    printHeader();

    for (const auto& record : records) {
        printRecord(record);
    }
}


// ---------------------------------------------------------------------------
// 6. SAMPLE DATA
// ---------------------------------------------------------------------------

SalesTable buildSalesTable() {
    SalesTable table;

    table.addRecord({
        1001, "Asha", "North", "Laptop", "Computers",
        2, 75000.0, 0.05
    });

    table.addRecord({
        1002, "Ravi", "South", "Monitor", "Displays",
        3, 18000.0, 0.10
    });

    table.addRecord({
        1003, "Meera", "North", "Keyboard", "Accessories",
        5, 2500.0, 0.00
    });

    table.addRecord({
        1004, "Kabir", "West", "Laptop", "Computers",
        1, 82000.0, 0.08
    });

    table.addRecord({
        1005, "Neha", "East", "Mouse", "Accessories",
        10, 1200.0, 0.02
    });

    return table;
}


// ---------------------------------------------------------------------------
// 7. DYNAMIC EXPANSION
// ---------------------------------------------------------------------------

void demonstrateDynamicExpansion() {
    cout << "\n=== DYNAMIC TABLE EXPANSION ===\n";

    SalesTable table = buildSalesTable();

    cout << "Initial rows: "
         << table.size()
         << '\n';

    table.addRecord({
        1006, "Arjun", "South", "Tablet", "Computers",
        4, 30000.0, 0.05
    });

    // Adding a row immediately produces its calculated columns.
    cout << "Rows after insertion: "
         << table.size()
         << '\n';

    printTable(table.data());
}


// ---------------------------------------------------------------------------
// 8. FILTERING
// ---------------------------------------------------------------------------

void demonstrateFiltering(const SalesTable& table) {
    cout << "\n=== FILTERING ===\n";

    const auto north =
        table.filter(
            [](const SalesRecord& record) {
                return record.region == "North";
            }
        );

    const highValue =
        table.filter(
            [](const SalesRecord& record) {
                return record.netAmount >= 50000.0;
            }
        );

    const northHighValue =
        table.filter(
            [](const SalesRecord& record) {
                return record.region == "North" &&
                       record.netAmount >= 50000.0;
            }
        );

    cout << "North orders: "
         << north.size()
         << '\n';

    cout << "High-value orders: "
         << highValue.size()
         << '\n';

    cout << "North + high-value orders: "
         << northHighValue.size()
         << '\n';

    printTable(northHighValue);
}


// ---------------------------------------------------------------------------
// 9. SORTING
// ---------------------------------------------------------------------------

void demonstrateSorting(const SalesTable& table) {
    cout << "\n=== SORTING BY NET SALES ===\n";

    auto sorted = table.sortedByNetAmount(true);
    printTable(sorted);
}


// ---------------------------------------------------------------------------
// 10. AGGREGATION
// ---------------------------------------------------------------------------

void demonstrateAggregation(const SalesTable& table) {
    cout << "\n=== AGGREGATION ===\n";

    cout << "Orders: "
         << table.size()
         << '\n';

    cout << "Total sales: ";
    printCurrency(table.totalSales());
    cout << '\n';

    cout << "Average order: ";
    printCurrency(table.averageOrderValue());
    cout << '\n';

    cout << "Total profit: ";
    printCurrency(table.totalProfit());
    cout << '\n';

    cout << "\nSales by region:\n";

    for (const auto& [region, amount] :
         table.salesByRegion()) {
        cout << "  " << region << ": ";
        printCurrency(amount);
        cout << '\n';
    }

    cout << "\nUnits by category:\n";

    for (const auto& [category, units] :
         table.unitsByCategory()) {
        cout << "  " << category
             << ": "
             << units
             << '\n';
    }
}


// ---------------------------------------------------------------------------
// 11. INDEXED LOOKUP
// ---------------------------------------------------------------------------

void demonstrateLookup(const SalesTable& table) {
    cout << "\n=== INDEXED LOOKUP ===\n";

    auto result = table.lookupByOrderId(1003);

    if (result.has_value()) {
        const SalesRecord& record =
            result->get();

        cout << "Found order "
             << record.orderId
             << " for "
             << record.customer
             << ", net sales = ";

        printCurrency(record.netAmount);
        cout << '\n';
    }

    auto missing = table.lookupByOrderId(9999);

    if (!missing.has_value()) {
        cout << "Order 9999 was not found.\n";
    }
}


// ---------------------------------------------------------------------------
// 12. EDGE CASES
// ---------------------------------------------------------------------------

void demonstrateEdgeCases() {
    cout << "\n=== EDGE CASES ===\n";

    SalesTable table = buildSalesTable();

    try {
        table.addRecord({
            1001, "Duplicate", "North", "Laptop",
            "Computers", 1, 50000.0, 0.0
        });
    }
    catch (const ValidationError& error) {
        cout << "Duplicate-key error: "
             << error.what()
             << '\n';
    }

    try {
        table.addRecord({
            1007, "", "North", "Laptop",
            "Computers", 1, 50000.0, 0.0
        });
    }
    catch (const ValidationError& error) {
        cout << "Missing-customer error: "
             << error.what()
             << '\n';
    }

    try {
        table.addRecord({
            1008, "Invalid", "Mars", "Laptop",
            "Computers", 1, 50000.0, 0.0
        });
    }
    catch (const ValidationError& error) {
        cout << "Invalid-region error: "
             << error.what()
             << '\n';
    }

    try {
        table.addRecord({
            1009, "Invalid", "North", "Laptop",
            "Computers", 0, 50000.0, 0.0
        });
    }
    catch (const ValidationError& error) {
        cout << "Quantity error: "
             << error.what()
             << '\n';
    }

    try {
        table.addRecord({
            1010, "Invalid", "North", "Laptop",
            "Computers", 1, 50000.0, 1.5
        });
    }
    catch (const ValidationError& error) {
        cout << "Discount error: "
             << error.what()
             << '\n';
    }
}


// ---------------------------------------------------------------------------
// 13. ZERO-VALUE CALCULATION
// ---------------------------------------------------------------------------

void demonstrateZeroRevenue() {
    cout << "\n=== ZERO-REVENUE EDGE CASE ===\n";

    SalesRecord record{
        2001,
        "Zero Customer",
        "East",
        "Free Sample",
        "Accessories",
        1,
        0.0,
        0.0
    };

    validateRecord(record);
    SalesCalculationEngine::calculate(record);

    cout << "Net revenue: ";
    printCurrency(record.netAmount);

    cout << "\nMargin: ";
    printCurrency(record.margin * 100);
    cout << "%\n";

    // No division-by-zero exception occurs because the calculation engine
    // explicitly handles the zero denominator.
}


// ---------------------------------------------------------------------------
// 14. PERFORMANCE COMPARISON
// ---------------------------------------------------------------------------

void demonstratePerformance() {
    cout << "\n=== PERFORMANCE CONSIDERATIONS ===\n";

    SalesTable table;

    constexpr int rowCount = 10000;

    for (int i = 1; i <= rowCount; ++i) {
        table.addRecord({
            i,
            "Customer",
            "North",
            "Product",
            "Computers",
            1,
            100.0,
            0.0
        });
    }

    constexpr int target = 9999;
    constexpr int repetitions = 1000;

    // Linear search is O(n) per lookup.
    auto start = chrono::high_resolution_clock::now();

    volatile int foundId = 0;

    for (int iteration = 0;
         iteration < repetitions;
         ++iteration) {
        for (const auto& record : table.data()) {
            if (record.orderId == target) {
                foundId = record.orderId;
                break;
            }
        }
    }

    auto linearEnd =
        chrono::high_resolution_clock::now();

    // Indexed lookup is approximately O(1) average case.
    start = chrono::high_resolution_clock::now();

    for (int iteration = 0;
         iteration < repetitions;
         ++iteration) {
        auto result =
            table.lookupByOrderId(target);

        if (result.has_value()) {
            foundId = result->get().orderId;
        }
    }

    auto indexedEnd =
        chrono::high_resolution_clock::now();

    const auto linearDuration =
        chrono::duration_cast<chrono::microseconds>(
            linearEnd -
            (linearEnd -
             chrono::microseconds(0))
        ).count();

    const auto indexedDuration =
        chrono::duration_cast<chrono::microseconds>(
            indexedEnd -
            (indexedEnd -
             chrono::microseconds(0))
        ).count();

    // The benchmark is primarily illustrative because operating-system
    // scheduling and compiler optimizations affect wall-clock measurements.
    cout << "Rows: " << rowCount << '\n';
    cout << "Repeated lookups: "
         << repetitions
         << '\n';
    cout << "Indexed result check: "
         << foundId
         << '\n';

    cout << "The table maintains an unordered_map index so repeated "
         << "key lookups do not require scanning every row.\n";

    // Suppress unused-variable concerns while emphasizing that precise
    // microbenchmarks require a dedicated benchmark methodology.
    (void)linearDuration;
    (void)indexedDuration;
}


// ---------------------------------------------------------------------------
// 15. DEPENDENCY-AWARE RECALCULATION
// ---------------------------------------------------------------------------

void demonstrateRecalculation() {
    cout << "\n=== RECALCULATION AFTER INPUT CHANGE ===\n";

    SalesTable table = buildSalesTable();

    cout << "Original first-row net sales: ";
    printCurrency(table.data().front().netAmount);
    cout << '\n';

    // The vector returned by data() is const, so we demonstrate recalculation
    // through a separate mutable record and a calculation engine.
    SalesRecord changed{
        1001,
        "Asha",
        "North",
        "Laptop",
        "Computers",
        3,
        75000.0,
        0.05
    };

    validateRecord(changed);
    SalesCalculationEngine::calculate(changed);

    cout << "After quantity change to 3, recalculated net sales: ";
    printCurrency(changed.netAmount);
    cout << '\n';

    cout << "This models how changing an input cell causes dependent "
         << "calculated columns to produce new results.\n";
}


// ---------------------------------------------------------------------------
// 16. TESTING
// ---------------------------------------------------------------------------

void runTests() {
    cout << "\n=== TESTS ===\n";

    SalesTable table = buildSalesTable();

    const SalesRecord& first =
        table.data().front();

    assert(abs(first.grossAmount - 150000.0) < 0.000001);
    assert(abs(first.discountAmount - 7500.0) < 0.000001);
    assert(abs(first.netAmount - 142500.0) < 0.000001);
    assert(abs(first.profit - 42750.0) < 0.000001);
    assert(abs(first.margin - 0.30) < 0.000001);
    assert(table.size() == 5);

    auto existing =
        table.lookupByOrderId(1003);

    assert(existing.has_value());

    auto missing =
        table.lookupByOrderId(999999);

    assert(!missing.has_value());

    cout << "All assertions passed.\n";
}


// ---------------------------------------------------------------------------
// 17. ARCHITECTURAL EXPLANATION
// ---------------------------------------------------------------------------

void printArchitecture() {
    cout << "\n=== ARCHITECTURE ===\n";

    cout
        << "Raw input fields -> validation -> calculated columns\n"
        << "                 -> indexed table storage\n"
        << "                 -> filtering/sorting/aggregation\n"
        << "                 -> reporting and lookup operations\n";

    cout
        << "\nDesign choices:\n"
        << "1. SalesRecord represents one logical table row.\n"
        << "2. SalesTable owns the collection of records.\n"
        << "3. Validation prevents invalid state from entering the table.\n"
        << "4. SalesCalculationEngine centralizes business calculations.\n"
        << "5. unordered_map provides an indexed lookup path.\n"
        << "6. Standard algorithms provide filtering and sorting.\n"
        << "7. Exceptions represent rejected input and invalid operations.\n";
}


// ---------------------------------------------------------------------------
// 18. MAIN
// ---------------------------------------------------------------------------

int main() {
    try {
        cout << "Excel Tables: Structured Data and Dynamic Calculations\n";

        SalesTable table = buildSalesTable();

        cout << "\n=== INITIAL SALES TABLE ===\n";
        printTable(table.data());

        demonstrateDynamicExpansion();
        demonstrateFiltering(table);
        demonstrateSorting(table);
        demonstrateAggregation(table);
        demonstrateLookup(table);
        demonstrateEdgeCases();
        demonstrateZeroRevenue();
        demonstratePerformance();
        demonstrateRecalculation();
        runTests();
        printArchitecture();

        cout << "\nCase study completed successfully.\n";
    }
    catch (const exception& error) {
        cerr << "Fatal error: "
             << error.what()
             << '\n';

        return 1;
    }

    return 0;
}
