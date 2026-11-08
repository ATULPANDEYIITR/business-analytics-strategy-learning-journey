#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Business Analytics Automation
 *
 * C++17 batch-processing engine for:
 * - Sales transaction ingestion
 * - Business data validation
 * - KPI computation
 * - Regional and category analysis
 * - Monthly revenue analysis
 * - Anomaly detection
 * - Automated management reporting
 */

using namespace std;

enum class JobStatus {
    Pending,
    Running,
    Completed,
    Failed
};

struct Transaction {
    string id;
    string date;
    string region;
    string product;
    string category;
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

struct Metrics {
    size_t transactions = 0;
    long long units = 0;
    double revenue = 0;
    double cost = 0;
    double profit = 0;
    double marginPercent = 0;
};

struct QualityReport {
    size_t accepted = 0;
    size_t rejected = 0;
    size_t duplicates = 0;
};

class CSVReader {
public:
    static vector<string> parseLine(const string& line) {
        vector<string> fields;
        string field;
        bool quoted = false;

        for (size_t i = 0; i < line.size(); ++i) {
            char ch = line[i];

            if (quoted) {
                if (ch == '"' && i + 1 < line.size()
                    && line[i + 1] == '"') {
                    field += '"';
                    ++i;
                } else if (ch == '"') {
                    quoted = false;
                } else {
                    field += ch;
                }
            } else if (ch == '"') {
                if (!field.empty()) {
                    throw runtime_error("Invalid CSV quotation.");
                }
                quoted = true;
            } else if (ch == ',') {
                fields.push_back(field);
                field.clear();
            } else {
                field += ch;
            }
        }

        if (quoted) {
            throw runtime_error("Unclosed CSV quotation.");
        }

        fields.push_back(field);
        return fields;
    }

    static string escape(const string& value) {
        if (value.find_first_of(",\"\r\n") == string::npos) {
            return value;
        }

        string result = "\"";

        for (char ch : value) {
            if (ch == '"') {
                result += "\"\"";
            } else {
                result += ch;
            }
        }

        return result + "\"";
    }
};

class BusinessAnalytics {
private:
    vector<Transaction> transactions;
    QualityReport quality;
    JobStatus status = JobStatus::Pending;
    double anomalyThreshold;

    static double roundTwo(double value) {
        return round(value * 100.0) / 100.0;
    }

    static bool validDate(const string& value) {
        if (value.size() != 10 ||
            value[4] != '-' || value[7] != '-') {
            return false;
        }

        try {
            int year = stoi(value.substr(0, 4));
            int month = stoi(value.substr(5, 2));
            int day = stoi(value.substr(8, 2));

            if (year < 1900 || month < 1 || month > 12) {
                return false;
            }

            const int days[] = {
                31, 28, 31, 30, 31, 30,
                31, 31, 30, 31, 30, 31
            };

            int maximum = days[month - 1];

            bool leap = (year % 400 == 0) ||
                        (year % 4 == 0 && year % 100 != 0);

            if (month == 2 && leap) {
                maximum = 29;
            }

            return day >= 1 && day <= maximum;
        } catch (...) {
            return false;
        }
    }

    static double parseNumber(const string& value) {
        size_t position = 0;
        double result = stod(value, &position);

        if (position != value.size() || !isfinite(result)) {
            throw invalid_argument("Invalid numeric value.");
        }

        return result;
    }

    static Transaction parseTransaction(
        const vector<string>& fields
    ) {
        if (fields.size() != 8) {
            throw invalid_argument("Incorrect CSV column count.");
        }

        Transaction item{
            fields[0],
            fields[1],
            fields[2],
            fields[3],
            fields[4],
            0,
            0,
            0
        };

        if (item.id.empty() || item.region.empty() ||
            item.product.empty() || item.category.empty()) {
            throw invalid_argument("Empty required business field.");
        }

        if (!validDate(item.date)) {
            throw invalid_argument("Invalid transaction date.");
        }

        double quantity = parseNumber(fields[5]);

        if (quantity < 0 || floor(quantity) != quantity ||
            quantity > 1000000000) {
            throw invalid_argument("Invalid quantity.");
        }

        item.quantity = static_cast<int>(quantity);
        item.unitPrice = parseNumber(fields[6]);
        item.unitCost = parseNumber(fields[7]);

        if (item.unitPrice < 0 || item.unitCost < 0) {
            throw invalid_argument("Negative financial value.");
        }

        if (item.quantity > 0 && item.unitPrice == 0) {
            throw invalid_argument("Positive quantity requires a price.");
        }

        return item;
    }

    template<typename KeyFunction>
    map<string, Metrics> groupBy(KeyFunction keyFunction) const {
        map<string, vector<Transaction>> groups;

        for (const auto& item : transactions) {
            groups[keyFunction(item)].push_back(item);
        }

        map<string, Metrics> result;

        for (const auto& [key, items] : groups) {
            result[key] = calculate(items);
        }

        return result;
    }

public:
    explicit BusinessAnalytics(double threshold = 2.0)
        : anomalyThreshold(threshold) {
        if (!isfinite(threshold) || threshold <= 0) {
            throw invalid_argument("Invalid anomaly threshold.");
        }
    }

    Metrics calculate() const {
        return calculate(transactions);
    }

    static Metrics calculate(
        const vector<Transaction>& items
    ) {
        Metrics result;
        result.transactions = items.size();

        for (const auto& item : items) {
            result.units += item.quantity;
            result.revenue += item.revenue();
            result.cost += item.cost();
        }

        result.profit = result.revenue - result.cost;

        result.marginPercent = result.revenue == 0
            ? 0
            : result.profit / result.revenue * 100;

        result.revenue = roundTwo(result.revenue);
        result.cost = roundTwo(result.cost);
        result.profit = roundTwo(result.profit);
        result.marginPercent = roundTwo(result.marginPercent);

        return result;
    }

    void load(const string& filename) {
        ifstream input(filename);

        if (!input) {
            throw runtime_error("Unable to open input CSV.");
        }

        string line;

        if (!getline(input, line)) {
            throw runtime_error("Empty input file.");
        }

        vector<string> header = CSVReader::parseLine(line);

        const vector<string> expected = {
            "transaction_id", "transaction_date", "region",
            "product", "category", "quantity",
            "unit_price", "cost_per_unit"
        };

        if (header != expected) {
            throw runtime_error("Unexpected CSV header.");
        }

        set<string> seen;

        while (getline(input, line)) {
            if (line.empty()) {
                continue;
            }

            try {
                Transaction item = parseTransaction(
                    CSVReader::parseLine(line)
                );

                if (!seen.insert(item.id).second) {
                    quality.duplicates++;
                    quality.rejected++;
                    continue;
                }

                transactions.push_back(item);
                quality.accepted++;

            } catch (const exception& error) {
                quality.rejected++;
                cerr << "Rejected record: "
                     << error.what() << '\n';
            }
        }

        if (input.bad()) {
            throw runtime_error("Input file read failure.");
        }

        if (transactions.empty()) {
            throw runtime_error("No valid transaction records.");
        }
    }

    map<string, Metrics> regionalAnalysis() const {
        return groupBy(
            [](const Transaction& item) {
                return item.region;
            }
        );
    }

    map<string, Metrics> productAnalysis() const {
        return groupBy(
            [](const Transaction& item) {
                return item.product;
            }
        );
    }

    map<string, Metrics> monthlyAnalysis() const {
        return groupBy(
            [](const Transaction& item) {
                return item.date.substr(0, 7);
            }
        );
    }

    vector<pair<string, double>> detectAnomalies() const {
        vector<double> values;

        for (const auto& item : transactions) {
            values.push_back(item.revenue());
        }

        if (values.size() < 3) {
            return {};
        }

        double mean = accumulate(
            values.begin(), values.end(), 0.0
        ) / values.size();

        double variance = 0;

        for (double value : values) {
            variance += (value - mean) * (value - mean);
        }

        variance /= values.size();

        double deviation = sqrt(variance);

        if (deviation == 0) {
            return {};
        }

        vector<pair<string, double>> anomalies;

        for (const auto& item : transactions) {
            double score = (item.revenue() - mean) / deviation;

            if (abs(score) >= anomalyThreshold) {
                anomalies.emplace_back(item.id, score);
            }
        }

        return anomalies;
    }

    void printReport(ostream& output) const {
        Metrics total = calculate();

        output << fixed << setprecision(2);

        output << "\nBUSINESS ANALYTICS REPORT\n";
        output << "====================================\n";

        output << "Transactions: " << total.transactions << '\n';
        output << "Units sold: " << total.units << '\n';
        output << "Revenue: " << total.revenue << '\n';
        output << "Cost: " << total.cost << '\n';
        output << "Profit: " << total.profit << '\n';
        output << "Margin: " << total.marginPercent << "%\n";

        output << "\nREGIONAL PERFORMANCE\n";

        for (const auto& [region, metrics] : regionalAnalysis()) {
            output << region
                   << " | Revenue: " << metrics.revenue
                   << " | Profit: " << metrics.profit
                   << " | Margin: " << metrics.marginPercent
                   << "%\n";
        }

        output << "\nPRODUCT PERFORMANCE\n";

        for (const auto& [product, metrics] : productAnalysis()) {
            output << product
                   << " | Revenue: " << metrics.revenue
                   << " | Units: " << metrics.units << '\n';
        }

        output << "\nMONTHLY PERFORMANCE\n";

        for (const auto& [month, metrics] : monthlyAnalysis()) {
            output << month
                   << " | Revenue: " << metrics.revenue
                   << " | Profit: " << metrics.profit << '\n';
        }

        output << "\nANOMALIES\n";

        auto anomalies = detectAnomalies();

        if (anomalies.empty()) {
            output << "No anomalies detected.\n";
        }

        for (const auto& [id, score] : anomalies) {
            output << id << " | Z-score: " << score << '\n';
        }

        output << "\nDATA QUALITY\n";
        output << "Accepted: " << quality.accepted << '\n';
        output << "Rejected: " << quality.rejected << '\n';
        output << "Duplicates: " << quality.duplicates << '\n';
    }

    void saveRegionalCSV(const string& filename) const {
        ofstream output(filename);

        if (!output) {
            throw runtime_error("Unable to create regional report.");
        }

        output << "region,transactions,units,revenue,cost,profit,margin\n";
        output << fixed << setprecision(2);

        for (const auto& [region, metrics] : regionalAnalysis()) {
            output << CSVReader::escape(region) << ','
                   << metrics.transactions << ','
                   << metrics.units << ','
                   << metrics.revenue << ','
                   << metrics.cost << ','
                   << metrics.profit << ','
                   << metrics.marginPercent << '\n';
        }

        if (!output) {
            throw runtime_error("Regional report write failure.");
        }
    }

    void run(
        const string& inputFile,
        const string& outputFile
    ) {
        if (status != JobStatus::Pending) {
            throw logic_error("Analytics job already executed.");
        }

        status = JobStatus::Running;

        try {
            load(inputFile);
            printReport(cout);
            saveRegionalCSV(outputFile);
            status = JobStatus::Completed;

            cout << "\nJob status: COMPLETED\n";
            cout << "Regional report: " << outputFile << '\n';

        } catch (...) {
            status = JobStatus::Failed;
            throw;
        }
    }

    JobStatus getStatus() const {
        return status;
    }
};

void runTests() {
    Transaction item{
        "TEST", "2026-01-01", "North",
        "Laptop", "Electronics", 2, 1000, 700
    };

    if (item.revenue() != 2000 ||
        item.cost() != 1400 ||
        item.profit() != 600) {
        throw runtime_error("Transaction calculation test failed.");
    }

    Metrics metrics = BusinessAnalytics::calculate({item});

    if (metrics.profit != 600 ||
        metrics.marginPercent != 30) {
        throw runtime_error("KPI test failed.");
    }

    if (CSVReader::parseLine("North,\"Electronics, Mobile\"").size() != 2) {
        throw runtime_error("CSV parsing test failed.");
    }

    cout << "All tests passed.\n";
}

int main(int argc, char* argv[]) {
    try {
        if (argc > 1 && string(argv[1]) == "--test") {
            runTests();
            return 0;
        }

        string input = argc > 1 ? argv[1] : "sales_data.csv";
        string output = argc > 2 ? argv[2] : "regional_report.csv";

        BusinessAnalytics analytics(2.0);
        analytics.run(input, output);

        return analytics.getStatus() == JobStatus::Completed
            ? 0
            : 1;

    } catch (const exception& error) {
        cerr << "Analytics failure: " << error.what() << '\n';
        return 1;
    }
}
