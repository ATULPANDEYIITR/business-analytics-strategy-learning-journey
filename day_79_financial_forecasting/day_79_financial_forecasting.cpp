#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class Scenario {
    BASE,
    OPTIMISTIC,
    PESSIMISTIC
};

enum class CashStatus {
    HEALTHY,
    LOW_CASH,
    NEGATIVE_CASH
};

enum class PullForwardStatus {
    NOT_APPLICABLE
};

struct FinancialPeriod {
    string period;
    double revenue;
    double operatingExpenses;
    double investingExpenses;
    double financingCashFlow;
    double openingCash;

    double operatingProfit() const {
        return revenue - operatingExpenses;
    }

    double netCashFlow() const {
        return operatingProfit()
            - investingExpenses
            + financingCashFlow;
    }

    double closingCash() const {
        return openingCash + netCashFlow();
    }
};

struct ForecastPolicy {
    int horizon = 6;
    int movingAverageWindow = 3;
    double optimisticAdjustment = 0.05;
    double pessimisticAdjustment = -0.05;
    double expenseAdjustment = 0.02;

    void validate() const {
        if (horizon < 1 || horizon > 120) {
            throw invalid_argument("Invalid forecast horizon.");
        }

        if (movingAverageWindow < 1) {
            throw invalid_argument("Invalid moving-average window.");
        }

        if (
            !isfinite(optimisticAdjustment) ||
            !isfinite(pessimisticAdjustment) ||
            !isfinite(expenseAdjustment)
        ) {
            throw invalid_argument("Invalid scenario adjustment.");
        }
    }
};

struct Forecast {
    string period;
    Scenario scenario;
    double revenue;
    double expenses;
    double investment;
    double operatingProfit;
    double netCashFlow;
    double openingCash;
    double closingCash;
    double profitMargin;
    CashStatus cashStatus;
};

struct GovernancePolicy {
    int requiredApprovals = 2;
    bool requirePassingChecks = true;
    bool requireResolvedConversations = true;

    void validate() const {
        if (requiredApprovals < 0) {
            throw invalid_argument("Approval count cannot be negative.");
        }
    }
};

class FinancialRepository {
private:
    map<string, FinancialPeriod> records;

    static bool validPeriod(const string& period) {
        if (period.size() != 7 || period[4] != '-') {
            return false;
        }

        for (int i = 0; i < 7; ++i) {
            if (i == 4) continue;

            if (!isdigit(static_cast<unsigned char>(period[i]))) {
                return false;
            }
        }

        int month = stoi(period.substr(5, 2));
        return month >= 1 && month <= 12;
    }

public:
    void add(const FinancialPeriod& record) {
        if (!validPeriod(record.period)) {
            throw invalid_argument("Invalid financial period.");
        }

        vector<double> values = {
            record.revenue,
            record.operatingExpenses,
            record.investingExpenses,
            record.financingCashFlow,
            record.openingCash
        };

        for (double value : values) {
            if (!isfinite(value)) {
                throw invalid_argument("Financial values must be finite.");
            }
        }

        if (
            record.revenue < 0 ||
            record.operatingExpenses < 0 ||
            record.investingExpenses < 0 ||
            record.openingCash < 0
        ) {
            throw invalid_argument("Invalid negative financial value.");
        }

        if (records.count(record.period)) {
            throw invalid_argument("Duplicate financial period.");
        }

        records.emplace(record.period, record);
    }

    vector<FinancialPeriod> getRecords() const {
        vector<FinancialPeriod> result;

        for (const auto& entry : records) {
            result.push_back(entry.second);
        }

        return result;
    }

    size_t size() const {
        return records.size();
    }

    FinancialPeriod latest() const {
        if (records.empty()) {
            throw runtime_error("No financial records available.");
        }

        return records.rbegin()->second;
    }
};

class GrowthCalculator {
public:
    static double compoundGrowth(const vector<double>& values) {
        if (values.size() < 2) {
            return 0.0;
        }

        for (double value : values) {
            if (!isfinite(value) || value < 0) {
                throw invalid_argument("Invalid growth observation.");
            }
        }

        double first = values.front();
        double last = values.back();

        if (first > 0) {
            return pow(
                last / first,
                1.0 / static_cast<double>(values.size() - 1)
            ) - 1.0;
        }

        double total = 0.0;

        for (size_t i = 1; i < values.size(); ++i) {
            total += (
                values[i] - values[i - 1]
            ) / max(abs(values[i - 1]), 1.0);
        }

        return total / static_cast<double>(values.size() - 1);
    }

    static double movingAverage(
        const vector<double>& values,
        int window
    ) {
        if (values.empty() || window < 1) {
            throw invalid_argument("Invalid moving average input.");
        }

        size_t count = min(
            values.size(),
            static_cast<size_t>(window)
        );

        double sum = accumulate(
            values.end() - count,
            values.end(),
            0.0
        );

        return sum / static_cast<double>(count);
    }
};

class FinancialForecastEngine {
private:
    const FinancialRepository& repository;
    ForecastPolicy policy;

    static string nextPeriod(const string& period) {
        int year = stoi(period.substr(0, 4));
        int month = stoi(period.substr(5, 2));

        if (month == 12) {
            ++year;
            month = 1;
        } else {
            ++month;
        }

        string result = to_string(year) + "-";

        if (month < 10) {
            result += "0";
        }

        result += to_string(month);
        return result;
    }

    static string scenarioName(Scenario scenario) {
        switch (scenario) {
            case Scenario::BASE:
                return "BASE";
            case Scenario::OPTIMISTIC:
                return "OPTIMISTIC";
            case Scenario::PESSIMISTIC:
                return "PESSIMISTIC";
        }

        throw invalid_argument("Unknown scenario.");
    }

public:
    FinancialForecastEngine(
        const FinancialRepository& repository,
        ForecastPolicy policy
    ) : repository(repository), policy(policy) {
        policy.validate();
    }

    vector<Forecast> generate(Scenario scenario) const {
        vector<FinancialPeriod> records = repository.getRecords();

        if (
            records.size() <
            static_cast<size_t>(policy.movingAverageWindow)
        ) {
            throw runtime_error("Insufficient historical data.");
        }

        vector<double> revenues;
        vector<double> expenses;
        vector<double> investments;

        for (const auto& record : records) {
            revenues.push_back(record.revenue);
            expenses.push_back(record.operatingExpenses);
            investments.push_back(record.investingExpenses);
        }

        double revenueGrowth =
            GrowthCalculator::compoundGrowth(revenues);

        double expenseGrowth =
            GrowthCalculator::compoundGrowth(expenses);

        if (scenario == Scenario::OPTIMISTIC) {
            revenueGrowth += policy.optimisticAdjustment;
        } else if (scenario == Scenario::PESSIMISTIC) {
            revenueGrowth += policy.pessimisticAdjustment;
            expenseGrowth += policy.expenseAdjustment;
        }

        revenueGrowth = clamp(revenueGrowth, -0.95, 1.0);
        expenseGrowth = clamp(expenseGrowth, -0.95, 1.0);

        double revenue = GrowthCalculator::movingAverage(
            revenues,
            policy.movingAverageWindow
        );

        double expense = GrowthCalculator::movingAverage(
            expenses,
            policy.movingAverageWindow
        );

        double investment = GrowthCalculator::movingAverage(
            investments,
            policy.movingAverageWindow
        );

        double cash = records.back().closingCash();
        string period = nextPeriod(records.back().period);

        vector<Forecast> results;

        for (int i = 0; i < policy.horizon; ++i) {
            revenue *= 1.0 + revenueGrowth;
            expense *= 1.0 + expenseGrowth;

            double profit = revenue - expense;
            double cashFlow = profit - investment;

            double openingCash = cash;
            double closingCash = openingCash + cashFlow;

            double margin = revenue > 0
                ? profit / revenue
                : 0.0;

            CashStatus status;

            if (closingCash < 0) {
                status = CashStatus::NEGATIVE_CASH;
            } else if (closingCash < expense) {
                status = CashStatus::LOW_CASH;
            } else {
                status = CashStatus::HEALTHY;
            }

            results.push_back({
                period,
                scenario,
                revenue,
                expense,
                investment,
                profit,
                cashFlow,
                openingCash,
                closingCash,
                margin,
                status
            });

            cash = closingCash;
            period = nextPeriod(period);
        }

        return results;
    }
};

class MergeEligibilityEngine {
    /*
     * Repository governance is separate from financial forecasting.
     * This class illustrates the same independent-policy design:
     * approval, automated validation, and enforcement are separate inputs.
     */
public:
    struct Review {
        bool eligibleReviewer;
        bool approved;
        bool stale;
        bool dismissed;
    };

    struct PullRequest {
        bool open;
        bool draft;
        bool mergeConflict;
        bool conversationsResolved;
        bool checksPassing;
        bool protectedBranch;
        bool directPush;
        bool forcePush;
        vector<Review> reviews;
    };

    struct Decision {
        bool eligible;
        vector<string> blockers;
    };

    static Decision evaluate(
        const PullRequest& pr,
        const GovernancePolicy& policy
    ) {
        policy.validate();

        vector<string> blockers;

        if (!pr.open) blockers.push_back("Pull request is closed.");
        if (pr.draft) blockers.push_back("Draft cannot be merged.");
        if (pr.mergeConflict) blockers.push_back("Merge conflict exists.");

        if (
            policy.requireResolvedConversations &&
            !pr.conversationsResolved
        ) {
            blockers.push_back("Unresolved review conversations.");
        }

        if (
            policy.requirePassingChecks &&
            !pr.checksPassing
        ) {
            blockers.push_back("Required checks are not passing.");
        }

        if (pr.directPush && pr.protectedBranch) {
            blockers.push_back("Direct push is prohibited.");
        }

        if (pr.forcePush && pr.protectedBranch) {
            blockers.push_back("Force push is prohibited.");
        }

        int approvals = 0;

        for (const auto& review : pr.reviews) {
            if (
                review.eligibleReviewer &&
                review.approved &&
                !review.stale &&
                !review.dismissed
            ) {
                ++approvals;
            }
        }

        if (pr.protectedBranch &&
            approvals < policy.requiredApprovals) {
            blockers.push_back("Required approvals are missing.");
        }

        return {
            blockers.empty(),
            blockers
        };
    }
};

class FinancialAnalytics {
public:
    static double total(
        const vector<Forecast>& forecasts,
        double Forecast::*field
    ) {
        double result = 0;

        for (const auto& forecast : forecasts) {
            result += forecast.*field;
        }

        return result;
    }

    static optional<double> cashRunway(
        double cash,
        double monthlyBurn
    ) {
        if (
            !isfinite(cash) ||
            !isfinite(monthlyBurn) ||
            cash < 0 ||
            monthlyBurn < 0
        ) {
            throw invalid_argument("Invalid runway inputs.");
        }

        if (monthlyBurn == 0) {
            return nullopt;
        }

        return cash / monthlyBurn;
    }

    static double budgetVariance(
        double actual,
        double budget
    ) {
        if (!isfinite(actual) || !isfinite(budget)) {
            throw invalid_argument("Invalid budget inputs.");
        }

        return actual - budget;
    }
};

string cashStatusName(CashStatus status) {
    switch (status) {
        case CashStatus::HEALTHY:
            return "HEALTHY";
        case CashStatus::LOW_CASH:
            return "LOW_CASH";
        case CashStatus::NEGATIVE_CASH:
            return "NEGATIVE_CASH";
    }

    return "UNKNOWN";
}

void runTests(
    const FinancialForecastEngine& engine
) {
    auto base = engine.generate(Scenario::BASE);
    auto optimistic = engine.generate(Scenario::OPTIMISTIC);
    auto pessimistic = engine.generate(Scenario::PESSIMISTIC);

    if (base.size() != 6) {
        throw runtime_error("Forecast horizon test failed.");
    }

    if (optimistic.front().revenue <= base.front().revenue) {
        throw runtime_error("Optimistic scenario test failed.");
    }

    if (pessimistic.front().revenue >= base.front().revenue) {
        throw runtime_error("Pessimistic scenario test failed.");
    }

    if (
        abs(
            base.front().closingCash -
            (
                base.front().openingCash +
                base.front().netCashFlow
            )
        ) > 0.01
    ) {
        throw runtime_error("Cash reconciliation failed.");
    }

    if (
        abs(
            FinancialAnalytics::budgetVariance(950, 1000) + 50
        ) > 0.001
    ) {
        throw runtime_error("Budget variance test failed.");
    }

    auto runway = FinancialAnalytics::cashRunway(10000, 2000);

    if (!runway || abs(*runway - 5.0) > 0.001) {
        throw runtime_error("Cash runway test failed.");
    }
}

int main() {
    try {
        FinancialRepository repository;

        vector<FinancialPeriod> sample = {
            {"2026-01", 850000, 520000, 65000, 20000, 300000},
            {"2026-02", 875000, 530000, 70000, 0, 595000},
            {"2026-03", 900000, 540000, 60000, -10000, 870000},
            {"2026-04", 925000, 555000, 75000, 15000, 1155000},
            {"2026-05", 960000, 565000, 80000, 0, 1465000},
            {"2026-06", 990000, 580000, 70000, 10000, 1780000}
        };

        for (const auto& record : sample) {
            repository.add(record);
        }

        ForecastPolicy policy;
        policy.horizon = 6;
        policy.movingAverageWindow = 3;

        FinancialForecastEngine engine(repository, policy);

        runTests(engine);

        cout << fixed << setprecision(2);

        cout << "FINANCIAL FORECASTING ENGINE\n";
        cout << string(110, '=') << "\n";

        for (Scenario scenario : {
            Scenario::BASE,
            Scenario::OPTIMISTIC,
            Scenario::PESSIMISTIC
        }) {
            auto forecasts = engine.generate(scenario);

            cout << "\nSCENARIO: ";

            switch (scenario) {
                case Scenario::BASE:
                    cout << "BASE";
                    break;
                case Scenario::OPTIMISTIC:
                    cout << "OPTIMISTIC";
                    break;
                case Scenario::PESSIMISTIC:
                    cout << "PESSIMISTIC";
                    break;
            }

            cout << "\n";

            for (const auto& forecast : forecasts) {
                cout
                    << forecast.period
                    << " | Revenue: " << forecast.revenue
                    << " | Expenses: " << forecast.expenses
                    << " | Profit: " << forecast.operatingProfit
                    << " | Closing cash: " << forecast.closingCash
                    << " | " << cashStatusName(forecast.cashStatus)
                    << "\n";
            }

            cout << "Total forecast revenue: "
                 << FinancialAnalytics::total(
                     forecasts,
                     &Forecast::revenue
                 )
                 << "\n";

            cout << "Total operating profit: "
                 << FinancialAnalytics::total(
                     forecasts,
                     &Forecast::operatingProfit
                 )
                 << "\n";

            cout << "Ending cash: "
                 << forecasts.back().closingCash
                 << "\n";
        }

        cout << "\nBUDGET VARIANCE\n";

        cout << FinancialAnalytics::budgetVariance(
            950000,
            1000000
        ) << "\n";

        auto runway = FinancialAnalytics::cashRunway(
            1000000,
            200000
        );

        cout << "Cash runway: ";

        if (runway) {
            cout << *runway << " months\n";
        } else {
            cout << "Not limited by operating burn\n";
        }

        cout << "\nREPOSITORY GOVERNANCE POLICY TEST\n";

        GovernancePolicy governance;
        governance.requiredApprovals = 2;

        MergeEligibilityEngine::PullRequest pr{
            true,
            false,
            false,
            true,
            true,
            true,
            false,
            false,
            {
                {true, true, false, false},
                {true, true, false, false}
            }
        };

        auto decision = MergeEligibilityEngine::evaluate(
            pr,
            governance
        );

        cout << "Merge eligible: "
             << (decision.eligible ? "YES" : "NO")
             << "\n";

        if (!decision.eligible) {
            for (const auto& blocker : decision.blockers) {
                cout << "- " << blocker << "\n";
            }
        }

        cout << "\nAll tests passed.\n";

    } catch (const exception& error) {
        cerr << "ERROR: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
