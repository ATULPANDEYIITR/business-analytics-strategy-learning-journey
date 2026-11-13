#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * BREAK-EVEN ANALYSIS AND GOVERNANCE ENGINE
 *
 * C++17
 *
 * Implements:
 * - Financial cost classification
 * - Contribution margin
 * - Break-even calculations
 * - Target-profit evaluation
 * - Multi-product weighted contribution
 * - Profitability policy evaluation
 * - Margin of safety
 * - Operating leverage
 * - Scenario and sensitivity analysis
 */

enum class CostType {
    Fixed,
    Variable
};

enum class ReviewStatus {
    Pass,
    Warning,
    Fail
};

struct CostItem {
    string name;
    double amount;
    CostType type;
};

struct Product {
    string name;
    double sellingPrice;
    double variableCost;
    double salesMix;
};

struct FinancialResult {
    double revenue;
    double fixedCosts;
    double variableCosts;
    double contribution;
    double profit;
    double breakEvenUnits;
    double breakEvenRevenue;
    double marginOfSafety;
    double marginOfSafetyRatio;
    int practicalBreakEvenUnits;
    int targetProfitUnits;
};

struct Policy {
    double minimumMarginOfSafety;
    double minimumContributionRatio;
    bool rejectOperatingLoss;
};

struct PolicyResult {
    ReviewStatus status;
    vector<string> violations;
};

class CostLedger {
private:
    vector<CostItem> items;

public:
    void add(
        const string& name,
        double amount,
        CostType type
    ) {
        if (name.empty()) {
            throw invalid_argument("Cost name cannot be empty.");
        }

        if (!isfinite(amount) || amount < 0) {
            throw invalid_argument(
                "Cost must be finite and non-negative."
            );
        }

        auto duplicate = find_if(
            items.begin(),
            items.end(),
            [&](const CostItem& item) {
                return item.name == name;
            }
        );

        if (duplicate != items.end()) {
            throw invalid_argument("Duplicate cost item.");
        }

        items.push_back({name, amount, type});
    }

    double total(CostType type) const {
        return accumulate(
            items.begin(),
            items.end(),
            0.0,
            [&](double sum, const CostItem& item) {
                return sum +
                    (item.type == type ? item.amount : 0.0);
            }
        );
    }

    const vector<CostItem>& getItems() const {
        return items;
    }
};

class BreakEvenEngine {
private:
    double sellingPrice;
    double variableCost;
    double fixedCosts;

    void validate() const {
        if (
            !isfinite(sellingPrice) ||
            !isfinite(variableCost) ||
            !isfinite(fixedCosts)
        ) {
            throw invalid_argument("Non-finite financial input.");
        }

        if (sellingPrice <= 0 || variableCost < 0 ||
            fixedCosts < 0) {
            throw invalid_argument("Invalid financial input.");
        }

        if (sellingPrice <= variableCost) {
            throw domain_error(
                "Contribution margin must be positive."
            );
        }
    }

public:
    BreakEvenEngine(
        double price,
        double variable,
        double fixed
    )
        : sellingPrice(price),
          variableCost(variable),
          fixedCosts(fixed) {
        validate();
    }

    double contributionPerUnit() const {
        return sellingPrice - variableCost;
    }

    double contributionMarginRatio() const {
        return contributionPerUnit() / sellingPrice;
    }

    double breakEvenUnits() const {
        return fixedCosts / contributionPerUnit();
    }

    double breakEvenRevenue() const {
        return fixedCosts / contributionMarginRatio();
    }

    FinancialResult calculate(
        int units,
        double targetProfit = 0
    ) const {
        if (units < 0 || !isfinite(targetProfit) ||
            targetProfit < 0) {
            throw invalid_argument("Invalid sales or target profit.");
        }

        double revenue = units * sellingPrice;
        double variable = units * variableCost;
        double contribution = revenue - variable;
        double profit = contribution - fixedCosts;

        double bep = breakEvenUnits();

        double safety = units - bep;

        double safetyRatio = units > 0
            ? safety / units
            : -1.0;

        return {
            revenue,
            fixedCosts,
            variable,
            contribution,
            profit,
            bep,
            breakEvenRevenue(),
            safety,
            safetyRatio,
            static_cast<int>(ceil(bep)),
            static_cast<int>(
                ceil((fixedCosts + targetProfit) /
                     contributionPerUnit())
            )
        };
    }

    double operatingLeverage(int units) const {
        auto result = calculate(units);

        if (result.profit <= 0) {
            throw domain_error(
                "Operating leverage is undefined when profit is non-positive."
            );
        }

        return result.contribution / result.profit;
    }

    double getSellingPrice() const {
        return sellingPrice;
    }

    double getVariableCost() const {
        return variableCost;
    }

    double getFixedCosts() const {
        return fixedCosts;
    }
};

class ProductPortfolio {
private:
    vector<Product> products;

public:
    void add(const Product& product) {
        if (product.name.empty()) {
            throw invalid_argument("Product name is required.");
        }

        if (
            !isfinite(product.sellingPrice) ||
            !isfinite(product.variableCost) ||
            !isfinite(product.salesMix) ||
            product.sellingPrice <= 0 ||
            product.variableCost < 0 ||
            product.variableCost >= product.sellingPrice ||
            product.salesMix <= 0
        ) {
            throw invalid_argument("Invalid product configuration.");
        }

        auto duplicate = find_if(
            products.begin(),
            products.end(),
            [&](const Product& p) {
                return p.name == product.name;
            }
        );

        if (duplicate != products.end()) {
            throw invalid_argument("Duplicate product.");
        }

        products.push_back(product);
    }

    double weightedContribution() const {
        if (products.empty()) {
            throw domain_error("Portfolio is empty.");
        }

        double totalMix = accumulate(
            products.begin(),
            products.end(),
            0.0,
            [](double sum, const Product& p) {
                return sum + p.salesMix;
            }
        );

        return accumulate(
            products.begin(),
            products.end(),
            0.0,
            [&](double sum, const Product& p) {
                double weight = p.salesMix / totalMix;

                return sum + weight *
                    (p.sellingPrice - p.variableCost);
            }
        );
    }

    double breakEvenUnits(double fixedCosts) const {
        if (!isfinite(fixedCosts) || fixedCosts < 0) {
            throw invalid_argument("Invalid fixed costs.");
        }

        return fixedCosts / weightedContribution();
    }

    void printAllocation(double fixedCosts) const {
        double totalMix = accumulate(
            products.begin(),
            products.end(),
            0.0,
            [](double sum, const Product& p) {
                return sum + p.salesMix;
            }
        );

        double totalUnits = breakEvenUnits(fixedCosts);

        cout << "\nPRODUCT BREAK-EVEN ALLOCATION\n";

        for (const auto& product : products) {
            double mix = product.salesMix / totalMix;

            cout << left << setw(15) << product.name
                 << " Mix: " << fixed << setprecision(2)
                 << mix * 100 << "%"
                 << " | Units: " << totalUnits * mix
                 << '\n';
        }
    }
};

class GovernanceEngine {
private:
    Policy policy;

public:
    explicit GovernanceEngine(const Policy& p) : policy(p) {
        if (
            !isfinite(p.minimumMarginOfSafety) ||
            !isfinite(p.minimumContributionRatio) ||
            p.minimumMarginOfSafety < 0 ||
            p.minimumMarginOfSafety > 1 ||
            p.minimumContributionRatio < 0 ||
            p.minimumContributionRatio > 1
        ) {
            throw invalid_argument("Invalid profitability policy.");
        }
    }

    PolicyResult evaluate(
        const FinancialResult& result,
        double contributionRatio
    ) const {
        PolicyResult output{
            ReviewStatus::Pass,
            {}
        };

        if (
            policy.rejectOperatingLoss &&
            result.profit < 0
        ) {
            output.violations.push_back(
                "Operating loss detected."
            );
        }

        if (result.marginOfSafetyRatio < 0) {
            output.violations.push_back(
                "Sales are below break-even."
            );
        } else if (
            result.marginOfSafetyRatio <
            policy.minimumMarginOfSafety
        ) {
            output.violations.push_back(
                "Margin of safety is below policy threshold."
            );
        }

        if (
            contributionRatio <
            policy.minimumContributionRatio
        ) {
            output.violations.push_back(
                "Contribution margin ratio is insufficient."
            );
        }

        if (!output.violations.empty()) {
            output.status = ReviewStatus::Fail;
        }

        return output;
    }
};

void printResult(const FinancialResult& result) {
    cout << fixed << setprecision(2);

    cout << "Revenue:                 "
         << result.revenue << '\n';

    cout << "Fixed costs:             "
         << result.fixedCosts << '\n';

    cout << "Variable costs:          "
         << result.variableCosts << '\n';

    cout << "Total contribution:      "
         << result.contribution << '\n';

    cout << "Operating profit:        "
         << result.profit << '\n';

    cout << "Exact break-even units:  "
         << result.breakEvenUnits << '\n';

    cout << "Practical break-even:    "
         << result.practicalBreakEvenUnits << '\n';

    cout << "Break-even revenue:      "
         << result.breakEvenRevenue << '\n';

    cout << "Margin of safety:        "
         << result.marginOfSafety << '\n';

    cout << "Target profit units:     "
         << result.targetProfitUnits << '\n';
}

void runSensitivity(
    const BreakEvenEngine& base,
    const vector<double>& priceChanges,
    const vector<double>& costChanges
) {
    cout << "\nSENSITIVITY ANALYSIS\n";

    for (double priceChange : priceChanges) {
        for (double costChange : costChanges) {
            double price =
                base.getSellingPrice() * (1 + priceChange);

            double variable =
                base.getVariableCost() * (1 + costChange);

            cout << "Price change: "
                 << priceChange * 100
                 << "%, Variable cost change: "
                 << costChange * 100 << "% ";

            try {
                BreakEvenEngine scenario(
                    price,
                    variable,
                    base.getFixedCosts()
                );

                cout << "Break-even: "
                     << scenario.breakEvenUnits()
                     << " units\n";

            } catch (const exception& error) {
                cout << "Rejected: " << error.what() << '\n';
            }
        }
    }
}

int main() {
    try {
        cout << string(65, '=') << '\n';
        cout << "BREAK-EVEN ANALYSIS ENGINE\n";
        cout << string(65, '=') << '\n';

        CostLedger ledger;

        ledger.add("Factory Rent", 80000, CostType::Fixed);
        ledger.add("Salaries", 120000, CostType::Fixed);
        ledger.add("Insurance", 20000, CostType::Fixed);

        ledger.add("Raw Materials", 250, CostType::Variable);
        ledger.add("Packaging", 50, CostType::Variable);
        ledger.add("Direct Labour", 100, CostType::Variable);

        double fixed = ledger.total(CostType::Fixed);
        double variable = ledger.total(CostType::Variable);

        cout << "\nCOST CLASSIFICATION\n";
        cout << "Fixed costs: " << fixed << '\n';
        cout << "Variable cost items: " << variable << '\n';

        BreakEvenEngine engine(1000, 400, fixed);

        cout << "\nUNIT ECONOMICS\n";
        cout << "Contribution/unit: "
             << engine.contributionPerUnit() << '\n';

        cout << "Contribution margin ratio: "
             << engine.contributionMarginRatio() * 100
             << "%\n";

        cout << "\nBREAK-EVEN AND PROFIT ANALYSIS\n";

        auto result = engine.calculate(600, 200000);
        printResult(result);

        cout << "\nOPERATING LEVERAGE\n";
        cout << engine.operatingLeverage(600) << "x\n";

        cout << "\nPROFITABILITY POLICY\n";

        GovernanceEngine governance({
            0.15,
            0.40,
            true
        });

        auto decision = governance.evaluate(
            result,
            engine.contributionMarginRatio()
        );

        cout << "Policy result: "
             << (
                 decision.status == ReviewStatus::Pass
                     ? "PASS"
                     : "FAIL"
             )
             << '\n';

        for (const auto& violation : decision.violations) {
            cout << "- " << violation << '\n';
        }

        cout << "\nMULTI-PRODUCT ANALYSIS\n";

        ProductPortfolio portfolio;

        portfolio.add({
            "Standard", 1000, 400, 60
        });

        portfolio.add({
            "Premium", 1500, 650, 40
        });

        cout << "Weighted contribution: "
             << portfolio.weightedContribution() << '\n';

        cout << "Weighted break-even units: "
             << portfolio.breakEvenUnits(220000) << '\n';

        portfolio.printAllocation(220000);

        runSensitivity(
            engine,
            {-0.10, 0.0, 0.10},
            {-0.10, 0.0, 0.10}
        );

        cout << "\nEDGE-CASE VALIDATION\n";

        try {
            BreakEvenEngine invalid(100, 100, 500);
        } catch (const exception& error) {
            cout << "Correctly rejected invalid model: "
                 << error.what() << '\n';
        }

        try {
            engine.calculate(-5);
        } catch (const exception& error) {
            cout << "Correctly rejected negative sales: "
                 << error.what() << '\n';
        }

        cout << "\nAUTOMATED ASSERTIONS\n";

        if (engine.contributionPerUnit() != 600) {
            throw runtime_error("Contribution assertion failed.");
        }

        if (engine.calculate(600).profit != 140000) {
            throw runtime_error("Profit assertion failed.");
        }

        if (engine.calculate(600).practicalBreakEvenUnits != 367) {
            throw runtime_error("Break-even assertion failed.");
        }

        if (engine.calculate(0).profit != -220000) {
            throw runtime_error("Zero-sales assertion failed.");
        }

        cout << "All assertions passed.\n";

    } catch (const exception& error) {
        cerr << "Execution error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
