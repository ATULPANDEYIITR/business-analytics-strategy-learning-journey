#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

enum class ColumnType {
    Numeric,
    Categorical,
    Empty
};

struct Record {
    string employeeId;
    string department;
    string salary;
    string experience;
    string rating;
};

struct NumericSummary {
    size_t count = 0;
    double mean = 0;
    double median = 0;
    double minimum = 0;
    double maximum = 0;
    double standardDeviation = 0;
    double q1 = 0;
    double q3 = 0;
    double iqr = 0;
    vector<double> outliers;
};

class Statistics {
public:
    static double mean(const vector<double>& values) {
        if (values.empty()) {
            throw invalid_argument("Cannot calculate mean of empty data.");
        }

        return accumulate(values.begin(), values.end(), 0.0)
            / values.size();
    }

    static double quantile(vector<double> values, double fraction) {
        if (values.empty() || fraction < 0 || fraction > 1) {
            throw invalid_argument("Invalid quantile input.");
        }

        sort(values.begin(), values.end());

        double position = (values.size() - 1) * fraction;

        size_t lower = static_cast<size_t>(floor(position));
        size_t upper = static_cast<size_t>(ceil(position));

        return values[lower]
            + (values[upper] - values[lower])
            * (position - lower);
    }

    static double median(vector<double> values) {
        return quantile(values, 0.5);
    }

    static double sampleStandardDeviation(
        const vector<double>& values
    ) {
        if (values.size() < 2) return 0;

        double average = mean(values);
        double sum = 0;

        for (double value : values) {
            sum += pow(value - average, 2);
        }

        return sqrt(sum / (values.size() - 1));
    }

    static double correlation(
        const vector<double>& first,
        const vector<double>& second
    ) {
        if (
            first.size() != second.size() ||
            first.size() < 2
        ) {
            throw invalid_argument(
                "Correlation requires at least two aligned observations."
            );
        }

        double meanX = mean(first);
        double meanY = mean(second);

        double numerator = 0;
        double sumX = 0;
        double sumY = 0;

        for (size_t i = 0; i < first.size(); i++) {
            double dx = first[i] - meanX;
            double dy = second[i] - meanY;

            numerator += dx * dy;
            sumX += dx * dx;
            sumY += dy * dy;
        }

        double denominator = sqrt(sumX * sumY);

        if (denominator == 0) {
            throw invalid_argument(
                "Correlation is undefined for constant columns."
            );
        }

        return numerator / denominator;
    }
};

class Dataset {
private:
    vector<Record> records;

public:
    explicit Dataset(vector<Record> input)
        : records(move(input)) {}

    const vector<Record>& getRecords() const {
        return records;
    }

    size_t size() const {
        return records.size();
    }

    static Dataset sample() {
        return Dataset({
            {"E001", "Engineering", "85000", "5", "4.5"},
            {"E002", "Analytics", "72000", "3", "4.2"},
            {"E003", "Engineering", "95000", "8", "4.8"},
            {"E004", "Operations", "61000", "2", "3.9"},
            {"E005", "Analytics", "78000", "4", "4.4"},
            {"E006", "Engineering", "110000", "12", "4.9"},
            {"E007", "Operations", "", "3", "3.7"},
            {"E008", "Analytics", "75000", "4", ""},
            {"E009", "Engineering", "85000", "5", "4.5"},
            {"E010", "Operations", "58000", "1", "3.5"},
            {"E010", "Operations", "58000", "1", "3.5"}
        });
    }
};

class EDAEngine {
private:
    Dataset dataset;

    static bool isMissing(const string& value) {
        static const set<string> missing = {
            "", "NA", "N/A", "NULL", "null",
            "none", "None", "NaN", "nan", "missing"
        };

        return missing.count(value) > 0;
    }

    static double parseNumber(const string& value) {
        if (isMissing(value)) {
            throw invalid_argument("Missing numeric value.");
        }

        size_t position = 0;
        double number = stod(value, &position);

        if (position != value.size() || !isfinite(number)) {
            throw invalid_argument("Invalid finite numeric value.");
        }

        return number;
    }

    vector<double> extractNumeric(
        const string& column
    ) const {
        vector<double> values;

        for (const auto& record : dataset.getRecords()) {
            string value;

            if (column == "salary") {
                value = record.salary;
            } else if (column == "experience") {
                value = record.experience;
            } else if (column == "rating") {
                value = record.rating;
            } else {
                throw invalid_argument("Unknown numeric column.");
            }

            if (!isMissing(value)) {
                values.push_back(parseNumber(value));
            }
        }

        return values;
    }

    static NumericSummary summarize(
        const vector<double>& values
    ) {
        NumericSummary summary;

        if (values.empty()) return summary;

        summary.count = values.size();
        summary.mean = Statistics::mean(values);
        summary.median = Statistics::median(values);
        summary.minimum = *min_element(values.begin(), values.end());
        summary.maximum = *max_element(values.begin(), values.end());

        summary.standardDeviation =
            Statistics::sampleStandardDeviation(values);

        summary.q1 = Statistics::quantile(values, 0.25);
        summary.q3 = Statistics::quantile(values, 0.75);
        summary.iqr = summary.q3 - summary.q1;

        double lower = summary.q1 - 1.5 * summary.iqr;
        double upper = summary.q3 + 1.5 * summary.iqr;

        copy_if(
            values.begin(),
            values.end(),
            back_inserter(summary.outliers),
            [lower, upper](double value) {
                return value < lower || value > upper;
            }
        );

        return summary;
    }

    static void printSummary(
        const string& column,
        const NumericSummary& summary
    ) {
        cout << "\n" << column << "\n";

        if (summary.count == 0) {
            cout << "No valid observations.\n";
            return;
        }

        cout << "Count: " << summary.count << "\n";
        cout << "Mean: " << summary.mean << "\n";
        cout << "Median: " << summary.median << "\n";
        cout << "Minimum: " << summary.minimum << "\n";
        cout << "Maximum: " << summary.maximum << "\n";
        cout << "Standard deviation: "
             << summary.standardDeviation << "\n";
        cout << "Q1: " << summary.q1 << "\n";
        cout << "Q3: " << summary.q3 << "\n";
        cout << "IQR: " << summary.iqr << "\n";

        cout << "Outliers: ";

        if (summary.outliers.empty()) {
            cout << "None";
        } else {
            for (double value : summary.outliers) {
                cout << value << " ";
            }
        }

        cout << "\n";
    }

public:
    explicit EDAEngine(Dataset input)
        : dataset(move(input)) {}

    size_t duplicateCount() const {
        set<string> seen;
        size_t duplicates = 0;

        for (const auto& r : dataset.getRecords()) {
            string key = r.employeeId + "\x1f"
                + r.department + "\x1f"
                + r.salary + "\x1f"
                + r.experience + "\x1f"
                + r.rating;

            if (!seen.insert(key).second) {
                duplicates++;
            }
        }

        return duplicates;
    }

    map<string, size_t> missingCounts() const {
        map<string, size_t> result = {
            {"employee_id", 0},
            {"department", 0},
            {"salary", 0},
            {"experience", 0},
            {"rating", 0}
        };

        for (const auto& record : dataset.getRecords()) {
            if (isMissing(record.employeeId)) result["employee_id"]++;
            if (isMissing(record.department)) result["department"]++;
            if (isMissing(record.salary)) result["salary"]++;
            if (isMissing(record.experience)) result["experience"]++;
            if (isMissing(record.rating)) result["rating"]++;
        }

        return result;
    }

    map<string, size_t> departmentCounts() const {
        map<string, size_t> result;

        for (const auto& record : dataset.getRecords()) {
            if (!isMissing(record.department)) {
                result[record.department]++;
            }
        }

        return result;
    }

    map<string, NumericSummary> numericProfiles() const {
        map<string, NumericSummary> result;

        for (const string& column : {
            "salary", "experience", "rating"
        }) {
            result[column] = summarize(extractNumeric(column));
        }

        return result;
    }

    map<string, double> groupedSalaryMeans() const {
        map<string, vector<double>> groups;

        for (const auto& record : dataset.getRecords()) {
            if (
                isMissing(record.department) ||
                isMissing(record.salary)
            ) {
                continue;
            }

            groups[record.department].push_back(
                parseNumber(record.salary)
            );
        }

        map<string, double> result;

        for (const auto& [department, salaries] : groups) {
            result[department] = Statistics::mean(salaries);
        }

        return result;
    }

    void analyze() const {
        cout << fixed << setprecision(3);

        cout << "EXPLORATORY DATA ANALYSIS\n";
        cout << "=========================\n";

        cout << "Records: " << dataset.size() << "\n";
        cout << "Duplicate rows: " << duplicateCount() << "\n";

        cout << "\nMISSING VALUE COUNTS\n";

        for (const auto& [column, count] : missingCounts()) {
            cout << column << ": " << count << "\n";
        }

        cout << "\nCOLUMN STATISTICS\n";

        for (const auto& [column, summary] : numericProfiles()) {
            printSummary(column, summary);
        }

        cout << "\nDEPARTMENT FREQUENCIES\n";

        for (const auto& [department, count] : departmentCounts()) {
            cout << department << ": " << count << "\n";
        }

        cout << "\nAVERAGE SALARY BY DEPARTMENT\n";

        for (const auto& [department, average] : groupedSalaryMeans()) {
            cout << department << ": " << average << "\n";
        }

        vector<double> salaries;
        vector<double> experiences;

        for (const auto& record : dataset.getRecords()) {
            if (
                !isMissing(record.salary) &&
                !isMissing(record.experience)
            ) {
                salaries.push_back(parseNumber(record.salary));
                experiences.push_back(parseNumber(record.experience));
            }
        }

        cout << "\nSALARY-EXPERIENCE CORRELATION\n";

        try {
            cout << Statistics::correlation(
                salaries,
                experiences
            ) << "\n";
        } catch (const invalid_argument& error) {
            cout << "Unavailable: " << error.what() << "\n";
        }

        cout << "\nDATA QUALITY FINDINGS\n";

        if (duplicateCount() > 0) {
            cout << "- Duplicate records detected.\n";
        }

        for (const auto& [column, count] : missingCounts()) {
            if (count > 0) {
                cout << "- " << column
                     << " has " << count << " missing values.\n";
            }
        }
    }
};

int main() {
    try {
        Dataset dataset = Dataset::sample();
        EDAEngine analyzer(move(dataset));

        analyzer.analyze();

        return 0;
    } catch (const exception& error) {
        cerr << "EDA ERROR: " << error.what() << "\n";
        return 1;
    }
}
