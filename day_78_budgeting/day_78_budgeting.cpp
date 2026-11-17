#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * BUDGET PREPARATION AND VARIANCE ANALYSIS
 *
 * C++17 standalone budgeting and governance engine.
 *
 * Implements:
 * - Department budget allocation
 * - Static and flexible budgeting
 * - Revenue and expense planning
 * - Actual transaction registration
 * - Variance classification
 * - Budget utilization
 * - Forecasting
 * - Approval state management
 * - Financial validation
 */

namespace budgeting {

constexpr long long SCALE = 100;

long long toMinorUnits(double value) {
    if (!std::isfinite(value) || value < 0) {
        throw std::invalid_argument("Invalid financial amount.");
    }

    return static_cast<long long>(
        std::round(value * SCALE)
    );
}

double toMajorUnits(long long value) {
    return static_cast<double>(value) / SCALE;
}

std::string requireText(const std::string& value) {
    if (value.empty() ||
        value.find_first_not_of(" \t\n\r") == std::string::npos) {
        throw std::invalid_argument("Required text is empty.");
    }
    return value;
}

enum class AccountType {
    Revenue,
    Expense
};

enum class CostBehavior {
    Fixed,
    Variable,
    Mixed
};

enum class BudgetStatus {
    Draft,
    Submitted,
    Approved,
    Rejected,
    Closed
};

enum class VarianceStatus {
    Favorable,
    Unfavorable,
    OnTarget
};

std::string toString(VarianceStatus status) {
    switch (status) {
        case VarianceStatus::Favorable:
            return "FAVORABLE";
        case VarianceStatus::Unfavorable:
            return "UNFAVORABLE";
        case VarianceStatus::OnTarget:
            return "ON TARGET";
    }

    throw std::logic_error("Unknown variance status.");
}

struct Department {
    std::string id;
    std::string name;
    long long spendingLimit;

    Department(
        std::string departmentId,
        std::string departmentName,
        long long limit
    ) :
        id(requireText(departmentId)),
        name(requireText(departmentName)),
        spendingLimit(limit) {

        if (limit < 0) {
            throw std::invalid_argument("Negative department limit.");
        }
    }
};

struct BudgetLine {
    std::string code;
    std::string description;
    std::string departmentId;

    AccountType accountType;
    CostBehavior behavior;

    long long fixedAmount;
    long long variableRate;
    long long plannedActivity;

    long long plannedAmount() const {
        if (accountType == AccountType::Revenue) {
            return fixedAmount;
        }

        if (behavior == CostBehavior::Fixed) {
            return fixedAmount;
        }

        if (behavior == CostBehavior::Variable) {
            return fixedAmount +
                (variableRate * plannedActivity) / SCALE;
        }

        return fixedAmount +
            (variableRate * plannedActivity) / SCALE;
    }

    long long flexibleAmount(long long actualActivity) const {
        if (accountType != AccountType::Expense) {
            throw std::invalid_argument(
                "Flexible expense calculation requires an expense."
            );
        }

        if (actualActivity < 0) {
            throw std::invalid_argument("Negative activity.");
        }

        if (behavior == CostBehavior::Fixed) {
            return fixedAmount;
        }

        const long long variable =
            (variableRate * actualActivity) / SCALE;

        if (behavior == CostBehavior::Variable) {
            return variable;
        }

        return fixedAmount + variable;
    }
};

struct ActualTransaction {
    std::string id;
    std::string budgetId;
    std::string accountCode;
    std::string departmentId;
    int period;
    long long amount;
    AccountType accountType;
    long long activity;
};

struct VarianceResult {
    std::string accountCode;
    std::string departmentId;
    AccountType accountType;
    long long budget;
    long long actual;
    long long variance;
    double percentage;
    VarianceStatus status;
};

// ---------------------------------------------------------
// Budget model
// ---------------------------------------------------------

class Budget {
private:
    std::string id_;
    int fiscalYear_;
    BudgetStatus status_;
    std::vector<BudgetLine> lines_;
    std::set<std::string> uniqueAccounts_;

public:
    Budget(const std::string& id, int fiscalYear) :
        id_(requireText(id)),
        fiscalYear_(fiscalYear),
        status_(BudgetStatus::Draft) {

        if (fiscalYear < 2000 || fiscalYear > 2200) {
            throw std::invalid_argument("Invalid fiscal year.");
        }
    }

    const std::string& id() const {
        return id_;
    }

    BudgetStatus status() const {
        return status_;
    }

    const std::vector<BudgetLine>& lines() const {
        return lines_;
    }

    void addLine(const BudgetLine& line) {
        if (status_ != BudgetStatus::Draft) {
            throw std::logic_error("Budget is not editable.");
        }

        requireText(line.code);
        requireText(line.departmentId);
        requireText(line.description);

        if (line.fixedAmount < 0 ||
            line.variableRate < 0 ||
            line.plannedActivity < 0) {
            throw std::invalid_argument("Negative budget input.");
        }

        if (line.accountType == AccountType::Revenue &&
            line.behavior != CostBehavior::Fixed) {
            throw std::invalid_argument(
                "Revenue cannot use expense cost behavior."
            );
        }

        const std::string key =
            line.departmentId + ":" + line.code;

        if (!uniqueAccounts_.insert(key).second) {
            throw std::invalid_argument("Duplicate budget line.");
        }

        lines_.push_back(line);
    }

    long long total(AccountType type) const {
        long long result = 0;

        for (const auto& line : lines_) {
            if (line.accountType == type) {
                result += line.plannedAmount();
            }
        }

        return result;
    }

    long long plannedProfit() const {
        return total(AccountType::Revenue) -
            total(AccountType::Expense);
    }

    void transition(
        BudgetStatus expected,
        BudgetStatus next
    ) {
        if (status_ != expected) {
            throw std::logic_error("Invalid budget state transition.");
        }

        status_ = next;
    }
};

// ---------------------------------------------------------
// Preparation and approval
// ---------------------------------------------------------

class BudgetPreparation {
private:
    std::map<std::string, Department> departments_;

public:
    explicit BudgetPreparation(
        std::map<std::string, Department> departments
    ) : departments_(std::move(departments)) {}

    void validate(const Budget& budget) const {
        if (budget.lines().empty()) {
            throw std::invalid_argument("Empty budget.");
        }

        std::map<std::string, long long> totals;

        for (const auto& line : budget.lines()) {
            auto it = departments_.find(line.departmentId);

            if (it == departments_.end()) {
                throw std::invalid_argument(
                    "Unknown department: " + line.departmentId
                );
            }

            if (line.accountType == AccountType::Expense) {
                totals[line.departmentId] += line.plannedAmount();
            }
        }

        for (const auto& [id, total] : totals) {
            if (total > departments_.at(id).spendingLimit) {
                throw std::invalid_argument(
                    "Department spending limit exceeded: " + id
                );
            }
        }
    }

    void submit(Budget& budget) const {
        validate(budget);

        budget.transition(
            BudgetStatus::Draft,
            BudgetStatus::Submitted
        );
    }

    void approve(Budget& budget, const std::string& approver) const {
        requireText(approver);

        budget.transition(
            BudgetStatus::Submitted,
            BudgetStatus::Approved
        );

        std::cout << "Approved by " << approver << '\n';
    }

    void reject(Budget& budget, const std::string& reason) const {
        requireText(reason);

        budget.transition(
            BudgetStatus::Submitted,
            BudgetStatus::Rejected
        );
    }
};

// ---------------------------------------------------------
// Actual ledger
// ---------------------------------------------------------

class ActualLedger {
private:
    std::map<std::string, ActualTransaction> transactions_;

public:
    void record(
        const ActualTransaction& transaction,
        const Budget& budget
    ) {
        if (budget.status() != BudgetStatus::Approved) {
            throw std::logic_error(
                "Transactions require an approved budget."
            );
        }

        requireText(transaction.id);

        if (transaction.budgetId != budget.id()) {
            throw std::invalid_argument("Budget ID mismatch.");
        }

        if (transaction.period < 1 ||
            transaction.period > 12) {
            throw std::invalid_argument("Invalid accounting period.");
        }

        if (transaction.amount < 0 || transaction.activity < 0) {
            throw std::invalid_argument("Negative actual value.");
        }

        if (transactions_.count(transaction.id)) {
            throw std::invalid_argument("Duplicate transaction.");
        }

        const auto match = std::find_if(
            budget.lines().begin(),
            budget.lines().end(),
            [&](const BudgetLine& line) {
                return line.code == transaction.accountCode &&
                    line.departmentId == transaction.departmentId &&
                    line.accountType == transaction.accountType;
            }
        );

        if (match == budget.lines().end()) {
            throw std::invalid_argument(
                "Actual transaction has no budget account."
            );
        }

        transactions_.emplace(
            transaction.id,
            transaction
        );
    }

    long long aggregate(
        const std::string& budgetId,
        const BudgetLine& line,
        std::optional<int> period = std::nullopt
    ) const {
        long long total = 0;

        for (const auto& [id, transaction] : transactions_) {
            if (transaction.budgetId == budgetId &&
                transaction.accountCode == line.code &&
                transaction.departmentId == line.departmentId &&
                transaction.accountType == line.accountType &&
                (!period || transaction.period == *period)) {
                total += transaction.amount;
            }
        }

        return total;
    }
};

// ---------------------------------------------------------
// Variance engine
// ---------------------------------------------------------

class VarianceEngine {
public:
    static VarianceStatus classify(
        AccountType type,
        long long variance
    ) {
        if (variance == 0) {
            return VarianceStatus::OnTarget;
        }

        const bool favorable =
            type == AccountType::Revenue
                ? variance > 0
                : variance < 0;

        return favorable
            ? VarianceStatus::Favorable
            : VarianceStatus::Unfavorable;
    }

    std::vector<VarianceResult> analyze(
        const Budget& budget,
        const ActualLedger& ledger,
        std::optional<int> period = std::nullopt
    ) const {
        if (budget.status() != BudgetStatus::Approved) {
            throw std::logic_error(
                "Budget must be approved before analysis."
            );
        }

        if (period && (*period < 1 || *period > 12)) {
            throw std::invalid_argument("Invalid period.");
        }

        std::vector<VarianceResult> results;

        for (const auto& line : budget.lines()) {
            long long planned = line.plannedAmount();

            if (period) {
                planned = (planned + 6) / 12;
            }

            const long long actual = ledger.aggregate(
                budget.id(),
                line,
                period
            );

            const long long variance = actual - planned;

            const double ratio = planned == 0
                ? 0.0
                : static_cast<double>(variance) /
                    static_cast<double>(planned) * 100.0;

            results.push_back({
                line.code,
                line.departmentId,
                line.accountType,
                planned,
                actual,
                variance,
                ratio,
                classify(line.accountType, variance)
            });
        }

        return results;
    }

    std::vector<VarianceResult> analyzeFlexible(
        const Budget& budget,
        const ActualLedger& ledger,
        int period,
        const std::map<std::string, long long>& activities
    ) const {
        if (period < 1 || period > 12) {
            throw std::invalid_argument("Invalid period.");
        }

        std::vector<VarianceResult> results;

        for (const auto& line : budget.lines()) {
            if (line.accountType != AccountType::Expense) {
                continue;
            }

            auto activity = activities.find(line.departmentId);

            const long long actualActivity =
                activity == activities.end() ? 0 : activity->second;

            const long long planned =
                line.flexibleAmount(actualActivity);

            const long long actual = ledger.aggregate(
                budget.id(),
                line,
                period
            );

            const long long variance = actual - planned;

            results.push_back({
                line.code,
                line.departmentId,
                AccountType::Expense,
                planned,
                actual,
                variance,
                planned == 0 ? 0.0 :
                    static_cast<double>(variance) /
                    static_cast<double>(planned) * 100.0,
                classify(AccountType::Expense, variance)
            });
        }

        return results;
    }
};

// ---------------------------------------------------------
// Reporting
// ---------------------------------------------------------

void printReport(const std::vector<VarianceResult>& results) {
    std::cout << "\nBUDGET VARIANCE REPORT\n";

    std::cout
        << std::left << std::setw(12) << "ACCOUNT"
        << std::setw(14) << "DEPARTMENT"
        << std::right << std::setw(14) << "BUDGET"
        << std::setw(14) << "ACTUAL"
        << std::setw(14) << "VARIANCE"
        << std::setw(13) << "VARIANCE %"
        << "  STATUS\n";

    for (const auto& row : results) {
        std::cout
            << std::left << std::setw(12) << row.accountCode
            << std::setw(14) << row.departmentId
            << std::right << std::fixed << std::setprecision(2)
            << std::setw(14) << toMajorUnits(row.budget)
            << std::setw(14) << toMajorUnits(row.actual)
            << std::setw(14) << toMajorUnits(row.variance)
            << std::setw(13) << row.percentage
            << "  " << toString(row.status) << '\n';
    }
}

double utilization(long long actual, long long budget) {
    if (budget <= 0) {
        throw std::invalid_argument("Budget must be positive.");
    }

    return static_cast<double>(actual) /
        static_cast<double>(budget) * 100.0;
}

long long forecastAnnual(
    long long yearToDate,
    int elapsedMonths
) {
    if (elapsedMonths < 1 || elapsedMonths > 12) {
        throw std::invalid_argument("Invalid elapsed months.");
    }

    return yearToDate * 12 / elapsedMonths;
}

// ---------------------------------------------------------
// Application
// ---------------------------------------------------------

int main() {
    try {
        using namespace budgeting;

        std::map<std::string, Department> departments;

        departments.emplace(
            "FIN",
            Department("FIN", "Finance", toMinorUnits(500000))
        );

        departments.emplace(
            "OPS",
            Department("OPS", "Operations", toMinorUnits(900000))
        );

        departments.emplace(
            "IT",
            Department("IT", "Technology", toMinorUnits(600000))
        );

        Budget budget("BUDGET-2027", 2027);

        budget.addLine({
            "REV001", "Service revenue", "FIN",
            AccountType::Revenue, CostBehavior::Fixed,
            toMinorUnits(3000000), 0, 0
        });

        budget.addLine({
            "EXP001", "Salaries", "FIN",
            AccountType::Expense, CostBehavior::Fixed,
            toMinorUnits(360000), 0, 0
        });

        budget.addLine({
            "EXP002", "Production materials", "OPS",
            AccountType::Expense, CostBehavior::Variable,
            0, toMinorUnits(120), 5000
        });

        budget.addLine({
            "EXP003", "IT infrastructure", "IT",
            AccountType::Expense, CostBehavior::Mixed,
            toMinorUnits(180000), toMinorUnits(20), 5000
        });

        BudgetPreparation preparation(departments);

        preparation.submit(budget);
        preparation.approve(budget, "Finance Controller");

        std::cout << "\nBUDGET PREPARATION\n";
        std::cout << "Budget: " << budget.id() << '\n';
        std::cout << "Revenue: "
            << toMajorUnits(budget.total(AccountType::Revenue)) << '\n';
        std::cout << "Expenses: "
            << toMajorUnits(budget.total(AccountType::Expense)) << '\n';
        std::cout << "Planned profit: "
            << toMajorUnits(budget.plannedProfit()) << '\n';

        ActualLedger ledger;

        ledger.record({
            "TX001", budget.id(), "REV001", "FIN",
            1, toMinorUnits(280000), AccountType::Revenue, 0
        }, budget);

        ledger.record({
            "TX002", budget.id(), "EXP001", "FIN",
            1, toMinorUnits(30000), AccountType::Expense, 0
        }, budget);

        ledger.record({
            "TX003", budget.id(), "EXP002", "OPS",
            1, toMinorUnits(55000), AccountType::Expense, 450
        }, budget);

        ledger.record({
            "TX004", budget.id(), "EXP003", "IT",
            1, toMinorUnits(19000), AccountType::Expense, 500
        }, budget);

        VarianceEngine engine;

        const auto annual = engine.analyze(
            budget,
            ledger
        );

        printReport(annual);

        std::cout << "\nMONTHLY VARIANCE\n";

        const auto monthly = engine.analyze(
            budget,
            ledger,
            1
        );

        printReport(monthly);

        std::cout << "\nFLEXIBLE BUDGET ANALYSIS\n";

        const auto flexible = engine.analyzeFlexible(
            budget,
            ledger,
            1,
            {
                {"OPS", 450},
                {"IT", 500}
            }
        );

        printReport(flexible);

        std::cout << "\nFORECASTING\n";

        std::cout << "Annualized operations expense: "
            << toMajorUnits(
                forecastAnnual(toMinorUnits(55000), 1)
            ) << '\n';

        std::cout << "\nUTILIZATION\n";

        std::cout << "Operations: "
            << utilization(
                toMinorUnits(55000),
                toMinorUnits(600000)
            ) << "%\n";

        std::cout << "\nVALIDATION\n";

        if (classify(AccountType::Revenue, 100) !=
            VarianceStatus::Favorable) {
            throw std::logic_error("Revenue classification failed.");
        }

        if (classify(AccountType::Expense, 100) !=
            VarianceStatus::Unfavorable) {
            throw std::logic_error("Expense classification failed.");
        }

        if (classify(AccountType::Expense, 0) !=
            VarianceStatus::OnTarget) {
            throw std::logic_error("Zero variance classification failed.");
        }

        try {
            ledger.record({
                "TX001", budget.id(), "REV001", "FIN",
                1, toMinorUnits(100), AccountType::Revenue, 0
            }, budget);
        } catch (const std::invalid_argument& error) {
            std::cout << "Duplicate transaction rejected: "
                << error.what() << '\n';
        }

        try {
            utilization(100, 0);
        } catch (const std::invalid_argument& error) {
            std::cout << "Invalid utilization rejected: "
                << error.what() << '\n';
        }

        std::cout << "All budgeting checks completed.\n";

    } catch (const std::exception& error) {
        std::cerr << "Budgeting error: "
            << error.what() << '\n';

        return 1;
    }

    return 0;
}
