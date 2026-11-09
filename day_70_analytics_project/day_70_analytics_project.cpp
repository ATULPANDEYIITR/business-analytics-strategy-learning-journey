/*
 * BUSINESS ANALYTICS AND PERFORMANCE ENGINE
 *
 * Language: C++17
 * Scenario: Enterprise retail business performance analysis.
 *
 * Features:
 * - Transaction validation
 * - Revenue and profitability calculations
 * - Regional and category analysis
 * - Customer segmentation
 * - Monthly performance analysis
 * - Revenue forecasting
 * - Business rule evaluation
 * - Merge-free aggregation using STL containers
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic business_analytics.cpp -o business_analytics
 *
 * Run:
 * ./business_analytics
 */

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

enum class CustomerSegment {
    HIGH_VALUE,
    REGULAR,
    OCCASIONAL,
    AT_RISK
};

enum class FindingSeverity {
    LOW,
    MEDIUM,
    HIGH
};

struct Transaction {
    string id;
    string customerId;
    string productId;
    string category;
    string region;
    int month;
    int quantity;
    double unitPrice;
    double unitCost;

    double revenue() const {
        return quantity * unitPrice;
    }

    double cost() const {
        return quantity * unitCost;
    }

    double profit() const {
        return revenue() - cost();
    }
};

struct Aggregate {
    double revenue = 0;
    double profit = 0;
    int units = 0;
    int transactions = 0;

    void add(const Transaction& transaction) {
        revenue += transaction.revenue();
        profit += transaction.profit();
        units += transaction.quantity;
        transactions++;
    }
};

struct Customer {
    int frequency = 0;
    double monetaryValue = 0;
    int lastPurchaseMonth = 1;
};

struct Finding {
    FindingSeverity severity;
    string code;
    string description;
};

struct AnalyticsPolicy {
    double minimumMarginPercent = 20.0;
    double minimumRepeatRatePercent = 30.0;
};

class BusinessAnalytics {
private:
    vector<Transaction> transactions;

    map<string, Aggregate> categories;
    map<string, Aggregate> regions;
    map<string, Aggregate> products;

    map<string, Customer> customers;
    map<int, Aggregate> monthly;

    set<string> transactionIds;

    double totalRevenue = 0;
    double totalCost = 0;
    int totalUnits = 0;

    void validate(const Transaction& transaction) const {
        if (transaction.id.empty() ||
            transaction.customerId.empty() ||
            transaction.productId.empty()) {
            throw invalid_argument("Missing transaction identifiers.");
        }

        if (transaction.month < 1 || transaction.month > 12) {
            throw invalid_argument("Month must be between 1 and 12.");
        }

        if (transaction.quantity <= 0) {
            throw invalid_argument("Quantity must be positive.");
        }

        if (!isfinite(transaction.unitPrice) ||
            !isfinite(transaction.unitCost) ||
            transaction.unitPrice <= 0 ||
            transaction.unitCost < 0 ||
            transaction.unitCost > transaction.unitPrice) {
            throw invalid_argument("Invalid pricing information.");
        }

        if (transaction.category.empty() ||
            transaction.region.empty()) {
            throw invalid_argument("Missing business dimensions.");
        }
    }

public:
    void addTransaction(const Transaction& transaction) {
        validate(transaction);

        if (transactionIds.count(transaction.id)) {
            throw invalid_argument("Duplicate transaction ID.");
        }

        transactionIds.insert(transaction.id);
        transactions.push_back(transaction);

        totalRevenue += transaction.revenue();
        totalCost += transaction.cost();
        totalUnits += transaction.quantity;

        categories[transaction.category].add(transaction);
        regions[transaction.region].add(transaction);
        products[transaction.productId].add(transaction);
        monthly[transaction.month].add(transaction);

        Customer& customer = customers[transaction.customerId];

        customer.frequency++;
        customer.monetaryValue += transaction.revenue();

        customer.lastPurchaseMonth = max(
            customer.lastPurchaseMonth,
            transaction.month
        );
    }

    double grossProfit() const {
        return totalRevenue - totalCost;
    }

    double grossMarginPercent() const {
        return totalRevenue > 0
            ? grossProfit() / totalRevenue * 100
            : 0;
    }

    double averageOrderValue() const {
        return transactions.empty()
            ? 0
            : totalRevenue / transactions.size();
    }

    double repeatCustomerRate() const {
        if (customers.empty()) {
            return 0;
        }

        int repeat = 0;

        for (const auto& entry : customers) {
            if (entry.second.frequency > 1) {
                repeat++;
            }
        }

        return 100.0 * repeat / customers.size();
    }

    map<CustomerSegment, vector<string>> segmentCustomers() const {
        map<CustomerSegment, vector<string>> result;

        for (const auto& entry : customers) {
            const string& id = entry.first;
            const Customer& customer = entry.second;

            const int recency =
                12 - customer.lastPurchaseMonth;

            CustomerSegment segment;

            if (
                customer.frequency >= 5 &&
                customer.monetaryValue >= 50000 &&
                recency <= 3
            ) {
                segment = CustomerSegment::HIGH_VALUE;
            } else if (
                customer.frequency >= 3 &&
                recency <= 6
            ) {
                segment = CustomerSegment::REGULAR;
            } else if (recency > 6) {
                segment = CustomerSegment::AT_RISK;
            } else {
                segment = CustomerSegment::OCCASIONAL;
            }

            result[segment].push_back(id);
        }

        return result;
    }

    pair<double, double> calculateTrend() const {
        if (monthly.empty()) {
            return {0, 0};
        }

        vector<double> values;

        for (int month = 1; month <= 12; month++) {
            auto it = monthly.find(month);

            values.push_back(
                it == monthly.end() ? 0 : it->second.revenue
            );
        }

        const double n = values.size();

        double xMean = (n - 1) / 2.0;
        double yMean = 0;

        for (double value : values) {
            yMean += value;
        }

        yMean /= n;

        double numerator = 0;
        double denominator = 0;

        for (int i = 0; i < static_cast<int>(values.size()); i++) {
            numerator += (i - xMean) * (values[i] - yMean);
            denominator += pow(i - xMean, 2);
        }

        double slope = denominator > 0
            ? numerator / denominator
            : 0;

        double forecast = max(
            0.0,
            yMean + slope * (n - xMean)
        );

        return {slope, forecast};
    }

    vector<Finding> evaluatePolicy(
        const AnalyticsPolicy& policy
    ) const {
        vector<Finding> findings;

        if (grossMarginPercent() < policy.minimumMarginPercent) {
            findings.push_back({
                FindingSeverity::HIGH,
                "LOW_MARGIN",
                "Gross margin is below the business threshold."
            });
        }

        if (repeatCustomerRate() < policy.minimumRepeatRatePercent) {
            findings.push_back({
                FindingSeverity::MEDIUM,
                "LOW_RETENTION",
                "Repeat customer rate is below the target."
            });
        }

        return findings;
    }

    void printDimension(
        const string& title,
        const map<string, Aggregate>& dimension
    ) const {
        cout << "\n" << title << "\n";
        cout << string(68, '-') << "\n";

        cout << left
             << setw(20) << "Dimension"
             << right
             << setw(15) << "Revenue"
             << setw(15) << "Profit"
             << setw(10) << "Units"
             << setw(10) << "Orders"
             << "\n";

        vector<pair<string, Aggregate>> ranked(
            dimension.begin(),
            dimension.end()
        );

        sort(
            ranked.begin(),
            ranked.end(),
            [](const auto& a, const auto& b) {
                return a.second.revenue > b.second.revenue;
            }
        );

        for (const auto& entry : ranked) {
            cout << left << setw(20) << entry.first
                 << right << fixed << setprecision(2)
                 << setw(15) << entry.second.revenue
                 << setw(15) << entry.second.profit
                 << setw(10) << entry.second.units
                 << setw(10) << entry.second.transactions
                 << "\n";
        }
    }

    void printMonthlyReport() const {
        cout << "\nMONTHLY PERFORMANCE\n";
        cout << string(55, '-') << "\n";

        double previousRevenue = 0;

        for (const auto& entry : monthly) {
            const double revenue = entry.second.revenue;

            cout << "Month " << setw(2) << entry.first
                 << " | Revenue: " << fixed << setprecision(2)
                 << revenue;

            if (previousRevenue > 0) {
                double growth =
                    (revenue - previousRevenue) /
                    previousRevenue * 100;

                cout << " | Growth: " << growth << "%";
            }

            cout << "\n";
            previousRevenue = revenue;
        }
    }

    void printReport() const {
        if (transactions.empty()) {
            throw runtime_error("No business transactions available.");
        }

        cout << "\nENTERPRISE BUSINESS ANALYTICS\n";
        cout << string(55, '=') << "\n";

        cout << fixed << setprecision(2);

        cout << "Transactions: " << transactions.size() << "\n";
        cout << "Unique customers: " << customers.size() << "\n";
        cout << "Revenue: INR " << totalRevenue << "\n";
        cout << "Cost: INR " << totalCost << "\n";
        cout << "Gross profit: INR " << grossProfit() << "\n";
        cout << "Gross margin: " << grossMarginPercent() << "%\n";
        cout << "Average order value: INR "
             << averageOrderValue() << "\n";
        cout << "Units sold: " << totalUnits << "\n";
        cout << "Repeat customer rate: "
             << repeatCustomerRate() << "%\n";

        printDimension("CATEGORY PERFORMANCE", categories);
        printDimension("REGIONAL PERFORMANCE", regions);
        printDimension("PRODUCT PERFORMANCE", products);

        printMonthlyReport();

        auto trend = calculateTrend();

        cout << "\nREVENUE FORECAST\n";
        cout << "Trend slope: INR " << trend.first << "\n";
        cout << "Next-period estimate: INR "
             << trend.second << "\n";

        auto segments = segmentCustomers();

        cout << "\nCUSTOMER SEGMENTATION\n";

        for (const auto& entry : segments) {
            string name;

            switch (entry.first) {
                case CustomerSegment::HIGH_VALUE:
                    name = "High Value";
                    break;
                case CustomerSegment::REGULAR:
                    name = "Regular";
                    break;
                case CustomerSegment::OCCASIONAL:
                    name = "Occasional";
                    break;
                case CustomerSegment::AT_RISK:
                    name = "At Risk";
                    break;
            }

            cout << name << ": "
                 << entry.second.size() << " customers\n";
        }

        AnalyticsPolicy policy;

        cout << "\nBUSINESS POLICY FINDINGS\n";

        auto findings = evaluatePolicy(policy);

        if (findings.empty()) {
            cout << "No policy violations detected.\n";
        }

        for (const Finding& finding : findings) {
            cout << finding.code << ": "
                 << finding.description << "\n";
        }
    }

    void runValidationTests() {
        Transaction test{
            "TEST001", "C001", "P001", "Electronics",
            "North", 1, 2, 1000, 600
        };

        BusinessAnalytics temporary;
        temporary.addTransaction(test);

        if (temporary.totalRevenue != 2000 ||
            temporary.grossProfit() != 800) {
            throw runtime_error("Financial calculation test failed.");
        }

        bool duplicateRejected = false;

        try {
            temporary.addTransaction(test);
        } catch (const invalid_argument&) {
            duplicateRejected = true;
        }

        if (!duplicateRejected) {
            throw runtime_error("Duplicate transaction test failed.");
        }

        cout << "All C++ validation tests passed.\n";
    }
};

vector<Transaction> generateSampleData() {
    vector<Transaction> records;

    const vector<string> regions = {
        "North", "South", "East", "West", "Central"
    };

    struct Product {
        string id;
        string category;
        double price;
        double cost;
    };

    const vector<Product> products = {
        {"P001", "Electronics", 25000, 18000},
        {"P002", "Furniture", 18000, 12000},
        {"P003", "Clothing", 2500, 1200},
        {"P004", "Groceries", 900, 650}
    };

    for (int i = 1; i <= 300; i++) {
        const Product& product = products[i % products.size()];

        records.push_back({
            "TXN" + to_string(i),
            "C" + to_string((i % 80) + 1),
            product.id,
            product.category,
            regions[i % regions.size()],
            ((i - 1) / 25) % 12 + 1,
            (i % 5) + 1,
            product.price,
            product.cost
        });
    }

    return records;
}

int main() {
    try {
        BusinessAnalytics analytics;

        analytics.runValidationTests();

        const auto records = generateSampleData();

        for (const Transaction& transaction : records) {
            analytics.addTransaction(transaction);
        }

        analytics.printReport();

    } catch (const exception& error) {
        cerr << "Business analytics error: "
             << error.what() << "\n";

        return 1;
    }

    return 0;
}
