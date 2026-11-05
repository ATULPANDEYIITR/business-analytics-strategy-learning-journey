#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

enum class Metric {
    Revenue,
    Expenses,
    Profit,
    Orders,
    Customers
};

struct BusinessRecord {
    std::string month;
    double revenue;
    double expenses;
    int orders;
    int customers;
    double target;

    double profit() const {
        return revenue - expenses;
    }

    double margin() const {
        return revenue > 0 ? profit() / revenue * 100.0 : 0.0;
    }

    double targetAchievement() const {
        return revenue / target * 100.0;
    }
};

class BusinessDataset {
private:
    std::vector<BusinessRecord> records;

public:
    explicit BusinessDataset(std::vector<BusinessRecord> input)
        : records(std::move(input)) {
        validate();
    }

    void validate() const {
        if (records.empty()) {
            throw std::invalid_argument("Dataset cannot be empty.");
        }

        std::map<std::string, bool> seen;

        for (const auto& record : records) {
            if (record.month.empty()) {
                throw std::invalid_argument("Month cannot be empty.");
            }

            if (seen[record.month]) {
                throw std::invalid_argument("Duplicate month.");
            }

            seen[record.month] = true;

            if (!std::isfinite(record.revenue) ||
                !std::isfinite(record.expenses) ||
                !std::isfinite(record.target)) {
                throw std::invalid_argument("Non-finite financial value.");
            }

            if (record.revenue < 0 ||
                record.expenses < 0 ||
                record.target <= 0 ||
                record.orders < 0 ||
                record.customers < 0) {
                throw std::invalid_argument("Invalid business record.");
            }

            if (record.orders > 0 &&
                record.customers > record.orders) {
                throw std::invalid_argument("Invalid customer count.");
            }
        }
    }

    const std::vector<BusinessRecord>& getRecords() const {
        return records;
    }
};

class BusinessAnalytics {
private:
    const BusinessDataset& dataset;

public:
    explicit BusinessAnalytics(const BusinessDataset& source)
        : dataset(source) {}

    double totalRevenue() const {
        double total = 0;

        for (const auto& record : dataset.getRecords()) {
            total += record.revenue;
        }

        return total;
    }

    double totalExpenses() const {
        double total = 0;

        for (const auto& record : dataset.getRecords()) {
            total += record.expenses;
        }

        return total;
    }

    double totalProfit() const {
        return totalRevenue() - totalExpenses();
    }

    double overallMargin() const {
        const double revenue = totalRevenue();

        return revenue > 0
            ? totalProfit() / revenue * 100.0
            : 0.0;
    }

    const BusinessRecord& bestProfitMonth() const {
        const auto& records = dataset.getRecords();

        return *std::max_element(
            records.begin(),
            records.end(),
            [](const auto& a, const auto& b) {
                return a.profit() < b.profit();
            }
        );
    }

    std::vector<double> movingAverage(std::size_t window) const {
        const auto& records = dataset.getRecords();

        if (window == 0 || window > records.size()) {
            throw std::invalid_argument("Invalid moving-average window.");
        }

        std::vector<double> result;

        // Sliding sum avoids recalculating every window.
        double currentSum = 0;

        for (std::size_t i = 0; i < records.size(); ++i) {
            currentSum += records[i].revenue;

            if (i >= window) {
                currentSum -= records[i - window].revenue;
            }

            if (i + 1 >= window) {
                result.push_back(currentSum / window);
            }
        }

        return result;
    }

    std::vector<std::pair<std::string, double>>
    targetFailures() const {
        std::vector<std::pair<std::string, double>> failures;

        for (const auto& record : dataset.getRecords()) {
            if (record.revenue < record.target) {
                failures.emplace_back(
                    record.month,
                    record.targetAchievement()
                );
            }
        }

        return failures;
    }

    double pearsonCorrelation(Metric first, Metric second) const {
        const auto& records = dataset.getRecords();

        if (records.size() < 2) {
            throw std::invalid_argument(
                "At least two records are required."
            );
        }

        auto extract = [](const BusinessRecord& record, Metric metric) {
            switch (metric) {
                case Metric::Revenue: return record.revenue;
                case Metric::Expenses: return record.expenses;
                case Metric::Profit: return record.profit();
                case Metric::Orders: return static_cast<double>(record.orders);
                case Metric::Customers: return static_cast<double>(record.customers);
            }

            return 0.0;
        };

        double meanX = 0;
        double meanY = 0;

        for (const auto& record : records) {
            meanX += extract(record, first);
            meanY += extract(record, second);
        }

        meanX /= records.size();
        meanY /= records.size();

        double numerator = 0;
        double sumX = 0;
        double sumY = 0;

        for (const auto& record : records) {
            const double x = extract(record, first) - meanX;
            const double y = extract(record, second) - meanY;

            numerator += x * y;
            sumX += x * x;
            sumY += y * y;
        }

        const double denominator = std::sqrt(sumX * sumY);

        // Constant variables have undefined correlation.
        if (denominator == 0) {
            return 0;
        }

        return numerator / denominator;
    }

    void exportCsv(const std::string& filename) const {
        std::ofstream file(filename);

        if (!file.is_open()) {
            throw std::runtime_error("Unable to create CSV file.");
        }

        file << "month,revenue,expenses,profit,orders,customers,"
                "margin,target,target_achievement\n";

        file << std::fixed << std::setprecision(2);

        for (const auto& record : dataset.getRecords()) {
            file << record.month << ','
                 << record.revenue << ','
                 << record.expenses << ','
                 << record.profit() << ','
                 << record.orders << ','
                 << record.customers << ','
                 << record.margin() << ','
                 << record.target << ','
                 << record.targetAchievement() << '\n';
        }

        if (!file.good()) {
            throw std::runtime_error("CSV write failed.");
        }
    }

    void printTextChart() const {
        const auto& records = dataset.getRecords();

        double maximum = 0;

        for (const auto& record : records) {
            maximum = std::max(maximum, record.revenue);
        }

        std::cout << "\nREVENUE BAR CHART\n";
        std::cout << std::string(65, '-') << '\n';

        for (const auto& record : records) {
            const int width = maximum > 0
                ? static_cast<int>(record.revenue / maximum * 40)
                : 0;

            std::cout << std::left << std::setw(12)
                      << record.month << " | "
                      << std::string(width, '#')
                      << " "
                      << std::fixed << std::setprecision(0)
                      << record.revenue << '\n';
        }
    }

    void printExecutiveReport() const {
        std::cout << "\nEXECUTIVE BUSINESS REPORT\n";
        std::cout << std::string(45, '=') << '\n';

        std::cout << std::fixed << std::setprecision(2);

        std::cout << "Revenue: INR " << totalRevenue() << '\n';
        std::cout << "Expenses: INR " << totalExpenses() << '\n';
        std::cout << "Profit: INR " << totalProfit() << '\n';
        std::cout << "Profit margin: "
                  << overallMargin() << "%\n";

        const auto& best = bestProfitMonth();

        std::cout << "Best profit month: "
                  << best.month << '\n';

        std::cout << "\nTARGET FAILURES\n";

        for (const auto& [month, achievement] : targetFailures()) {
            std::cout << month << ": "
                      << achievement << "%\n";
        }

        std::cout << "\nREVENUE-EXPENSE CORRELATION: "
                  << pearsonCorrelation(
                      Metric::Revenue,
                      Metric::Expenses
                  )
                  << '\n';
    }
};

int main() {
    try {
        std::vector<BusinessRecord> records = {
            {"January", 450000, 310000, 420, 350, 430000},
            {"February", 480000, 325000, 450, 370, 450000},
            {"March", 520000, 340000, 490, 395, 500000},
            {"April", 495000, 350000, 465, 380, 510000},
            {"May", 560000, 365000, 530, 425, 530000},
            {"June", 590000, 375000, 560, 445, 550000},
            {"July", 610000, 390000, 580, 460, 580000},
            {"August", 575000, 385000, 550, 440, 590000},
            {"September", 650000, 405000, 610, 490, 620000},
            {"October", 680000, 420000, 640, 510, 650000},
            {"November", 710000, 440000, 670, 535, 680000},
            {"December", 780000, 465000, 740, 590, 720000}
        };

        BusinessDataset dataset(std::move(records));
        BusinessAnalytics analytics(dataset);

        analytics.printExecutiveReport();
        analytics.printTextChart();

        const auto averages = analytics.movingAverage(3);

        std::cout << "\nTHREE-MONTH MOVING AVERAGE\n";

        for (double value : averages) {
            std::cout << std::fixed << std::setprecision(2)
                      << value << '\n';
        }

        analytics.exportCsv("business_performance_cpp.csv");

        std::cout << "\nCSV export completed.\n";
    } catch (const std::exception& error) {
        std::cerr << "Business analytics error: "
                  << error.what() << '\n';

        return 1;
    }

    return 0;
}
