#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * Cost Analytics and Governance Engine
 *
 * C++17 implementation of:
 * - Cost classification
 * - Cost centre accounting
 * - Cost allocation
 * - Contribution analysis
 * - Budget control
 * - Optimization evaluation
 * - Merge-independent financial policy decisions
 */

enum class CostType {
    Fixed,
    Variable,
    SemiVariable
};

enum class CostBehavior {
    Direct,
    Indirect
};

enum class Category {
    Labor,
    Materials,
    Technology,
    Facilities,
    Logistics,
    Administration
};

enum class Decision {
    Accepted,
    Rejected
};

string toString(CostType type) {
    switch (type) {
        case CostType::Fixed: return "Fixed";
        case CostType::Variable: return "Variable";
        case CostType::SemiVariable: return "Semi-variable";
    }
    throw invalid_argument("Unknown cost type.");
}

string toString(Category category) {
    switch (category) {
        case Category::Labor: return "Labor";
        case Category::Materials: return "Materials";
        case Category::Technology: return "Technology";
        case Category::Facilities: return "Facilities";
        case Category::Logistics: return "Logistics";
        case Category::Administration: return "Administration";
    }
    throw invalid_argument("Unknown category.");
}

void validateAmount(double amount, const string& field) {
    if (!isfinite(amount) || amount < 0) {
        throw invalid_argument(field + " must be non-negative.");
    }
}

struct CostRecord {
    string id;
    string costCenter;
    string period;
    string description;
    Category category;
    CostType type;
    CostBehavior behavior;
    double amount;
    double activityUnits;

    CostRecord(
        string id_,
        string center_,
        string period_,
        string description_,
        Category category_,
        CostType type_,
        CostBehavior behavior_,
        double amount_,
        double activity_
    )
        : id(move(id_)),
          costCenter(move(center_)),
          period(move(period_)),
          description(move(description_)),
          category(category_),
          type(type_),
          behavior(behavior_),
          amount(amount_),
          activityUnits(activity_) {

        if (id.empty() || costCenter.empty() || period.empty()) {
            throw invalid_argument("Required cost record field is empty.");
        }

        validateAmount(amount, "Cost amount");
        validateAmount(activityUnits, "Activity units");
    }
};

struct Budget {
    string costCenter;
    string period;
    double allocated;

    Budget(string center, string period_, double amount)
        : costCenter(move(center)),
          period(move(period_)),
          allocated(amount) {
        validateAmount(allocated, "Budget");
    }
};

struct OptimizationProposal {
    string name;
    Category category;
    double reductionRate;
    double implementationCost;
    double risk;
};

struct OptimizationResult {
    string name;
    double baseline;
    double grossSavings;
    double implementationCost;
    double netSavings;
    Decision decision;
    string reason;
};

struct Policy {
    double maximumRisk = 5.0;
    double minimumReduction = 0.05;
    double minimumNetSavings = 1000.0;
};

class CostLedger {
private:
    vector<CostRecord> records;
    set<string> identifiers;

public:
    void add(const CostRecord& record) {
        if (!identifiers.insert(record.id).second) {
            throw invalid_argument("Duplicate record ID: " + record.id);
        }

        records.push_back(record);
    }

    vector<CostRecord> find(
        const string& period,
        const string& center = ""
    ) const {
        vector<CostRecord> result;

        copy_if(
            records.begin(),
            records.end(),
            back_inserter(result),
            [&](const CostRecord& record) {
                return record.period == period
                    && (center.empty() || record.costCenter == center);
            }
        );

        return result;
    }

    double total(const string& period) const {
        auto selected = find(period);

        return accumulate(
            selected.begin(),
            selected.end(),
            0.0,
            [](double sum, const CostRecord& record) {
                return sum + record.amount;
            }
        );
    }

    const vector<CostRecord>& all() const {
        return records;
    }
};

class CostAnalyzer {
private:
    const CostLedger& ledger;

public:
    explicit CostAnalyzer(const CostLedger& ledger_)
        : ledger(ledger_) {}

    map<string, double> classify(const string& period) const {
        map<string, double> result;

        for (const auto& record : ledger.find(period)) {
            result[toString(record.type)] += record.amount;
            result[toString(record.category)] += record.amount;

            result[
                record.behavior == CostBehavior::Direct
                    ? "Direct"
                    : "Indirect"
            ] += record.amount;
        }

        return result;
    }

    map<string, double> costCenters(const string& period) const {
        map<string, double> result;

        for (const auto& record : ledger.find(period)) {
            result[record.costCenter] += record.amount;
        }

        return result;
    }

    double unitCost(const string& period) const {
        auto records = ledger.find(period);

        double totalCost = 0;
        double totalActivity = 0;

        for (const auto& record : records) {
            totalCost += record.amount;
            totalActivity += record.activityUnits;
        }

        if (totalActivity <= 0) {
            throw domain_error("Activity volume must be positive.");
        }

        return totalCost / totalActivity;
    }

    map<string, double> breakEven(
        double fixedCost,
        double sellingPrice,
        double variableCost
    ) const {
        validateAmount(fixedCost, "Fixed cost");
        validateAmount(sellingPrice, "Selling price");
        validateAmount(variableCost, "Variable cost");

        double contribution = sellingPrice - variableCost;

        if (contribution <= 0) {
            throw domain_error("Contribution margin must be positive.");
        }

        double units = ceil(fixedCost / contribution);

        return {
            {"contribution_per_unit", contribution},
            {"contribution_margin_percent",
                contribution / sellingPrice * 100},
            {"break_even_units", units},
            {"break_even_revenue", units * sellingPrice}
        };
    }

    map<string, double> variance(
        const Budget& budget,
        double actual
    ) const {
        validateAmount(actual, "Actual expenditure");

        double difference = budget.allocated - actual;

        double percentage = budget.allocated == 0
            ? 0
            : difference / budget.allocated * 100;

        return {
            {"budget", budget.allocated},
            {"actual", actual},
            {"variance", difference},
            {"variance_percent", percentage}
        };
    }

    map<string, map<string, double>> allocateIndirect(
        const string& period
    ) const {
        map<string, double> direct;
        double indirect = 0;

        for (const auto& record : ledger.find(period)) {
            if (record.behavior == CostBehavior::Direct) {
                direct[record.costCenter] += record.amount;
            } else {
                indirect += record.amount;
            }
        }

        double base = 0;

        for (const auto& [center, amount] : direct) {
            base += amount;
        }

        if (base == 0 && indirect > 0) {
            throw domain_error("No valid allocation base exists.");
        }

        map<string, map<string, double>> result;

        for (const auto& [center, amount] : direct) {
            double allocation = base == 0
                ? 0
                : indirect * amount / base;

            result[center] = {
                {"direct", amount},
                {"indirect", allocation},
                {"total", amount + allocation}
            };
        }

        return result;
    }
};

class OptimizationEngine {
private:
    Policy policy;

public:
    explicit OptimizationEngine(Policy policy_)
        : policy(policy_) {

        if (policy.maximumRisk < 0 || policy.maximumRisk > 10) {
            throw invalid_argument("Invalid risk policy.");
        }

        if (
            policy.minimumReduction < 0
            || policy.minimumReduction > 1
        ) {
            throw invalid_argument("Invalid reduction policy.");
        }

        validateAmount(
            policy.minimumNetSavings,
            "Minimum net savings"
        );
    }

    vector<OptimizationResult> evaluate(
        const CostLedger& ledger,
        const string& period,
        const vector<OptimizationProposal>& proposals
    ) const {
        map<Category, double> totals;

        for (const auto& record : ledger.find(period)) {
            totals[record.category] += record.amount;
        }

        vector<OptimizationResult> results;

        for (const auto& proposal : proposals) {
            if (
                !isfinite(proposal.reductionRate)
                || proposal.reductionRate < 0
                || proposal.reductionRate > 1
            ) {
                throw invalid_argument("Invalid reduction rate.");
            }

            validateAmount(
                proposal.implementationCost,
                "Implementation cost"
            );

            if (
                !isfinite(proposal.risk)
                || proposal.risk < 0
                || proposal.risk > 10
            ) {
                throw invalid_argument("Invalid risk score.");
            }

            double baseline = totals[proposal.category];
            double gross = baseline * proposal.reductionRate;
            double net = gross - proposal.implementationCost;

            string reason;
            bool eligible = true;

            if (baseline <= 0) {
                eligible = false;
                reason = "No baseline expenditure.";
            } else if (proposal.risk > policy.maximumRisk) {
                eligible = false;
                reason = "Risk threshold exceeded.";
            } else if (
                proposal.reductionRate < policy.minimumReduction
            ) {
                eligible = false;
                reason = "Reduction below minimum.";
            } else if (net < policy.minimumNetSavings) {
                eligible = false;
                reason = "Insufficient net savings.";
            } else {
                reason = "Eligible.";
            }

            results.push_back({
                proposal.name,
                baseline,
                gross,
                eligible ? proposal.implementationCost : 0,
                eligible ? net : 0,
                eligible ? Decision::Accepted : Decision::Rejected,
                reason
            });
        }

        return results;
    }
};

void printSection(const string& title) {
    cout << "\n" << title << "\n";
    cout << string(55, '-') << "\n";
}

void printMap(const map<string, double>& values) {
    for (const auto& [name, value] : values) {
        cout << left << setw(32) << name
             << right << fixed << setprecision(2)
             << value << "\n";
    }
}

void runTests() {
    CostLedger testLedger;

    testLedger.add(CostRecord(
        "T001", "TEST", "2026-10", "Test record",
        Category::Labor, CostType::Fixed,
        CostBehavior::Direct, 100, 10
    ));

    bool duplicateRejected = false;

    try {
        testLedger.add(CostRecord(
            "T001", "TEST", "2026-10", "Duplicate",
            Category::Labor, CostType::Fixed,
            CostBehavior::Direct, 100, 10
        ));
    } catch (const invalid_argument&) {
        duplicateRejected = true;
    }

    if (!duplicateRejected) {
        throw runtime_error("Duplicate validation failed.");
    }

    CostAnalyzer analyzer(testLedger);

    if (abs(analyzer.unitCost("2026-10") - 10) > 1e-9) {
        throw runtime_error("Unit cost test failed.");
    }

    auto result = analyzer.breakEven(1000, 100, 60);

    if (result.at("break_even_units") != 25) {
        throw runtime_error("Break-even test failed.");
    }

    cout << "All C++ validation tests passed.\n";
}

int main() {
    try {
        runTests();

        CostLedger ledger;

        ledger.add(CostRecord(
            "C001", "PRODUCTION", "2026-10",
            "Production workforce",
            Category::Labor, CostType::Fixed,
            CostBehavior::Direct, 120000, 1000
        ));

        ledger.add(CostRecord(
            "C002", "PRODUCTION", "2026-10",
            "Raw materials",
            Category::Materials, CostType::Variable,
            CostBehavior::Direct, 180000, 1000
        ));

        ledger.add(CostRecord(
            "C003", "PRODUCTION", "2026-10",
            "Factory facilities",
            Category::Facilities, CostType::Fixed,
            CostBehavior::Indirect, 45000, 1000
        ));

        ledger.add(CostRecord(
            "C004", "TECHNOLOGY", "2026-10",
            "Cloud infrastructure",
            Category::Technology, CostType::SemiVariable,
            CostBehavior::Indirect, 60000, 1000
        ));

        ledger.add(CostRecord(
            "C005", "LOGISTICS", "2026-10",
            "Distribution",
            Category::Logistics, CostType::Variable,
            CostBehavior::Direct, 35000, 1000
        ));

        ledger.add(CostRecord(
            "C006", "ADMINISTRATION", "2026-10",
            "Administrative services",
            Category::Administration, CostType::Fixed,
            CostBehavior::Indirect, 25000, 1000
        ));

        CostAnalyzer analyzer(ledger);
        const string period = "2026-10";

        printSection("COST ANALYTICS ENGINE");

        cout << "Period: " << period << "\n";
        cout << "Total expenditure: Rs. "
             << ledger.total(period) << "\n";
        cout << "Unit cost: Rs. "
             << analyzer.unitCost(period) << "\n";

        printSection("COST CLASSIFICATION");
        printMap(analyzer.classify(period));

        printSection("COST CENTRE REPORT");
        printMap(analyzer.costCenters(period));

        printSection("BUDGET VARIANCE");

        Budget budget("PRODUCTION", period, 350000);

        auto productionRecords = ledger.find(
            period,
            "PRODUCTION"
        );

        double actual = 0;

        for (const auto& record : productionRecords) {
            actual += record.amount;
        }

        printMap(analyzer.variance(budget, actual));

        printSection("CONTRIBUTION AND BREAK-EVEN");

        printMap(analyzer.breakEven(
            150000,
            500,
            300
        ));

        printSection("INDIRECT COST ALLOCATION");

        for (const auto& [center, values] :
             analyzer.allocateIndirect(period)) {

            cout << "\n" << center << "\n";
            printMap(values);
        }

        printSection("OPTIMIZATION ENGINE");

        Policy policy;
        policy.maximumRisk = 5;
        policy.minimumReduction = 0.05;
        policy.minimumNetSavings = 1000;

        OptimizationEngine engine(policy);

        vector<OptimizationProposal> proposals = {
            {
                "Cloud capacity rightsizing",
                Category::Technology,
                0.20, 3000, 2
            },
            {
                "Procurement consolidation",
                Category::Materials,
                0.08, 5000, 3
            },
            {
                "Logistics route optimization",
                Category::Logistics,
                0.15, 2000, 4
            },
            {
                "High-risk workforce reduction",
                Category::Labor,
                0.10, 1000, 9
            }
        };

        auto results = engine.evaluate(
            ledger,
            period,
            proposals
        );

        double netSavings = 0;

        for (const auto& result : results) {
            cout << "\nProposal: " << result.name << "\n";
            cout << "Baseline: Rs. " << result.baseline << "\n";
            cout << "Gross savings: Rs. "
                 << result.grossSavings << "\n";
            cout << "Net savings: Rs. "
                 << result.netSavings << "\n";

            cout << "Decision: "
                 << (
                     result.decision == Decision::Accepted
                         ? "ACCEPTED"
                         : "REJECTED"
                 )
                 << "\n";

            cout << "Reason: " << result.reason << "\n";

            if (result.decision == Decision::Accepted) {
                netSavings += result.netSavings;
            }
        }

        cout << "\nTotal eligible net savings: Rs. "
             << netSavings << "\n";

        printSection("EXECUTION COMPLETED");

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
