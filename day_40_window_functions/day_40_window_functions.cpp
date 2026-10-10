#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

using namespace std;

struct Transaction {
    int id;
    string branch;
    string month;
    string service;
    long long revenue_cents;
};

struct Analysis {
    Transaction transaction;
    size_t row_number = 0;
    size_t rank = 0;
    size_t dense_rank = 0;
    long long running_total_cents = 0;
    optional<double> moving_average_cents;
    optional<long long> previous_revenue_cents;
    optional<double> percent_change;
    size_t revenue_bucket = 0;
};

class RevenueGovernanceEngine {
private:
    vector<Transaction> transactions;

    static bool valid_month(const string& month) {
        if (month.size() != 7 || month[4] != '-') return false;
        for (size_t i = 0; i < month.size(); ++i) {
            if (i == 4) continue;
            if (month[i] < '0' || month[i] > '9') return false;
        }
        int month_number = stoi(month.substr(5, 2));
        return month_number >= 1 && month_number <= 12;
    }

    static void validate(const vector<Transaction>& rows) {
        unordered_set<int> identifiers;

        for (const auto& row : rows) {
            if (row.id <= 0 || !identifiers.insert(row.id).second) {
                throw invalid_argument("Transaction IDs must be unique and positive");
            }
            if (row.branch.empty() || row.service.empty()) {
                throw invalid_argument("Branch and service are required");
            }
            if (!valid_month(row.month)) {
                throw invalid_argument("Month must be a valid YYYY-MM value");
            }
            if (row.revenue_cents < 0) {
                throw invalid_argument("Revenue cannot be negative");
            }
        }
    }

    static string money(long long cents) {
        ostringstream output;
        output << '$' << cents / 100 << '.'
               << setw(2) << setfill('0') << cents % 100;
        return output.str();
    }

public:
    explicit RevenueGovernanceEngine(vector<Transaction> input)
        : transactions(move(input)) {
        validate(transactions);
    }

    vector<Analysis> analyze_branch(const string& branch) const {
        vector<Transaction> rows;

        for (const auto& transaction : transactions) {
            if (transaction.branch == branch) rows.push_back(transaction);
        }

        // The ID tie-breaker makes output reproducible when month values tie.
        sort(rows.begin(), rows.end(), [](const auto& left, const auto& right) {
            if (left.month != right.month) return left.month < right.month;
            return left.id < right.id;
        });

        vector<Transaction> by_revenue = rows;
        sort(by_revenue.begin(), by_revenue.end(),
             [](const auto& left, const auto& right) {
                 if (left.revenue_cents != right.revenue_cents) {
                     return left.revenue_cents > right.revenue_cents;
                 }
                 return left.id < right.id;
             });

        map<int, size_t> row_number;
        map<int, size_t> rank;
        map<int, size_t> dense_rank;

        size_t current_rank = 0;
        size_t current_dense_rank = 0;
        optional<long long> previous_ranked_revenue;

        for (size_t index = 0; index < by_revenue.size(); ++index) {
            const auto& row = by_revenue[index];
            row_number[row.id] = index + 1;

            if (!previous_ranked_revenue ||
                *previous_ranked_revenue != row.revenue_cents) {
                current_rank = index + 1;
                ++current_dense_rank;
            }

            rank[row.id] = current_rank;
            dense_rank[row.id] = current_dense_rank;
            previous_ranked_revenue = row.revenue_cents;
        }

        vector<Analysis> result;
        long long running = 0;

        for (size_t index = 0; index < rows.size(); ++index) {
            const auto& row = rows[index];
            running += row.revenue_cents;

            Analysis item;
            item.transaction = row;
            item.row_number = row_number[row.id];
            item.rank = rank[row.id];
            item.dense_rank = dense_rank[row.id];
            item.running_total_cents = running;

            // A trailing two-row frame contains the current and previous
            // transaction in chronological order, not the highest revenues.
            const size_t start = index == 0 ? 0 : index - 1;
            long long frame_total = 0;
            size_t frame_count = 0;
            for (size_t position = start; position <= index; ++position) {
                frame_total += rows[position].revenue_cents;
                ++frame_count;
            }
            item.moving_average_cents =
                static_cast<double>(frame_total) / frame_count;

            if (index > 0) {
                const long long previous = rows[index - 1].revenue_cents;
                item.previous_revenue_cents = previous;
                if (previous != 0) {
                    item.percent_change =
                        100.0 * (row.revenue_cents - previous) / previous;
                }
            }

            result.push_back(item);
        }

        return result;
    }

    void print_report() const {
        set<string> branches;
        for (const auto& transaction : transactions) {
            branches.insert(transaction.branch);
        }

        for (const auto& branch : branches) {
            cout << "\nBranch: " << branch << '\n';
            cout << left << setw(8) << "Month"
                 << setw(12) << "Revenue"
                 << setw(9) << "Rank"
                 << setw(10) << "Dense"
                 << setw(15) << "Running total"
                 << setw(14) << "2-row average"
                 << "Change\n";

            for (const auto& row : analyze_branch(branch)) {
                cout << left << setw(8) << row.transaction.month
                     << setw(12) << money(row.transaction.revenue_cents)
                     << setw(9) << row.rank
                     << setw(10) << row.dense_rank
                     << setw(15) << money(row.running_total_cents);

                if (row.moving_average_cents) {
                    cout << '$' << fixed << setprecision(2)
                         << *row.moving_average_cents / 100.0;
                }
                cout << string(4, ' ');

                if (row.percent_change) {
                    cout << fixed << setprecision(2)
                         << *row.percent_change << '%';
                } else {
                    cout << "N/A";
                }
                cout << '\n';
            }
        }
    }
};

int main() {
    try {
        // Integer cents avoid binary floating-point rounding for currency
        // totals. Convert to decimal display only at the reporting boundary.
        vector<Transaction> data = {
            {1, "North", "2026-01", "Cloud", 1200000},
            {2, "North", "2026-01", "Security", 1200000},
            {3, "North", "2026-02", "Cloud", 1500000},
            {4, "North", "2026-02", "Security", 1100000},
            {5, "North", "2026-03", "Cloud", 1400000},
            {6, "North", "2026-03", "Security", 1600000},
            {7, "South", "2026-01", "Cloud", 800000},
            {8, "South", "2026-02", "Cloud", 1200000},
            {9, "South", "2026-03", "Security", 1400000}
        };

        RevenueGovernanceEngine engine(move(data));
        engine.print_report();

        cout << "\nValidation case\n";
        try {
            vector<Transaction> invalid = {
                {1, "North", "2026-01", "Cloud", 1000},
                {1, "North", "2026-02", "Cloud", 2000}
            };
            RevenueGovernanceEngine rejected(move(invalid));
            rejected.print_report();
        } catch (const invalid_argument& error) {
            cout << "Rejected invalid dataset: " << error.what() << '\n';
        }
    } catch (const exception& error) {
        cerr << "Analytics engine failed: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
