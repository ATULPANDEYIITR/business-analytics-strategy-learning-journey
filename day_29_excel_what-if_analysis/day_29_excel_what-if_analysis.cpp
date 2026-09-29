/*
    Excel What-If Analysis Case Study
    Scenario Manager, Goal Seek, and Sensitivity Analysis

    C++17 industry-style case study:
    A capital-investment team evaluates a product launch.

    The modeled business has:
      - unit demand
      - selling price
      - variable cost
      - fixed costs
      - tax rate
      - initial investment

    The program progressively implements:
      1. A financial model
      2. Scenario Manager
      3. Goal Seek using bisection
      4. One-variable sensitivity analysis
      5. Two-variable sensitivity analysis
      6. Break-even analysis
      7. DCF sensitivity
      8. Numerical sensitivity
      9. Validation and failure handling
     10. Scenario-grid analysis

    Compile:
      g++ -std=c++17 -O2 -Wall -Wextra -pedantic main.cpp -o what_if

    Run:
      ./what_if
*/

#include <algorithm>
#include <cmath>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

struct ModelInputs {
    double unitsSold = 10000.0;
    double pricePerUnit = 50.0;
    double variableCostPerUnit = 28.0;
    double fixedCosts = 100000.0;
    double taxRate = 0.25;
    double initialInvestment = 250000.0;
};

struct ModelOutputs {
    double revenue = 0.0;
    double variableCost = 0.0;
    double grossProfit = 0.0;
    double operatingProfit = 0.0;
    double tax = 0.0;
    double netProfit = 0.0;
    double roi = 0.0;
    double breakEvenUnits = std::numeric_limits<double>::quiet_NaN();
};

void validateInputs(const ModelInputs& input) {
    if (input.unitsSold < 0.0) {
        throw std::invalid_argument("Units sold cannot be negative.");
    }

    if (input.pricePerUnit < 0.0) {
        throw std::invalid_argument("Price per unit cannot be negative.");
    }

    if (input.variableCostPerUnit < 0.0) {
        throw std::invalid_argument(
            "Variable cost per unit cannot be negative."
        );
    }

    if (input.fixedCosts < 0.0) {
        throw std::invalid_argument("Fixed costs cannot be negative.");
    }

    if (input.taxRate < 0.0 || input.taxRate > 1.0) {
        throw std::invalid_argument(
            "Tax rate must be between 0 and 1."
        );
    }

    if (input.initialInvestment <= 0.0) {
        throw std::invalid_argument(
            "Initial investment must be greater than zero."
        );
    }
}

ModelOutputs calculateModel(const ModelInputs& input) {
    validateInputs(input);

    ModelOutputs output;

    output.revenue =
        input.unitsSold * input.pricePerUnit;

    output.variableCost =
        input.unitsSold * input.variableCostPerUnit;

    output.grossProfit =
        output.revenue - output.variableCost;

    output.operatingProfit =
        output.grossProfit - input.fixedCosts;

    // Losses do not create a tax benefit in this simplified case study.
    output.tax =
        std::max(0.0, output.operatingProfit * input.taxRate);

    output.netProfit =
        output.operatingProfit - output.tax;

    output.roi =
        output.netProfit / input.initialInvestment;

    const double contributionMargin =
        input.pricePerUnit - input.variableCostPerUnit;

    if (contributionMargin > 0.0) {
        output.breakEvenUnits =
            input.fixedCosts / contributionMargin;
    }

    return output;
}

void printOutputs(
    const std::string& label,
    const ModelOutputs& output
) {
    std::cout << "\n--- " << label << " ---\n";
    std::cout << std::fixed << std::setprecision(2);

    std::cout << "Revenue:          $"
              << output.revenue << '\n';

    std::cout << "Variable Cost:    $"
              << output.variableCost << '\n';

    std::cout << "Gross Profit:     $"
              << output.grossProfit << '\n';

    std::cout << "Operating Profit: $"
              << output.operatingProfit << '\n';

    std::cout << "Tax:              $"
              << output.tax << '\n';

    std::cout << "Net Profit:       $"
              << output.netProfit << '\n';

    std::cout << "ROI:              "
              << output.roi * 100.0 << "%\n";

    if (std::isnan(output.breakEvenUnits)) {
        std::cout << "Break-even Units: Not achievable\n";
    } else {
        std::cout << "Break-even Units: "
                  << output.breakEvenUnits << '\n';
    }
}


// -----------------------------------------------------------------------------
// SCENARIO MANAGER
// -----------------------------------------------------------------------------

struct Scenario {
    std::string name;
    ModelInputs inputs;
};

class ScenarioManager {
private:
    ModelInputs baseInputs;
    std::vector<Scenario> scenarios;

public:
    explicit ScenarioManager(ModelInputs base)
        : baseInputs(base) {
        validateInputs(baseInputs);
    }

    void addScenario(
        const std::string& name,
        const ModelInputs& inputs
    ) {
        if (name.empty()) {
            throw std::invalid_argument(
                "Scenario name cannot be empty."
            );
        }

        validateInputs(inputs);

        scenarios.push_back({name, inputs});
    }

    const std::vector<Scenario>& getScenarios() const {
        return scenarios;
    }

    ModelOutputs evaluate(const Scenario& scenario) const {
        return calculateModel(scenario.inputs);
    }
};


// -----------------------------------------------------------------------------
// GOAL SEEK
// -----------------------------------------------------------------------------

double goalSeek(
    const std::function<double(double)>& functionToSolve,
    double target,
    double lower,
    double upper,
    double tolerance = 1e-8,
    int maxIterations = 200
) {
    if (lower >= upper) {
        throw std::invalid_argument(
            "Lower bound must be smaller than upper bound."
        );
    }

    double lowValue =
        functionToSolve(lower) - target;

    double highValue =
        functionToSolve(upper) - target;

    if (std::abs(lowValue) <= tolerance) {
        return lower;
    }

    if (std::abs(highValue) <= tolerance) {
        return upper;
    }

    // Bisection only works when the target is bracketed.
    if (lowValue * highValue > 0.0) {
        throw std::runtime_error(
            "Goal cannot be bracketed by the supplied range."
        );
    }

    double low = lower;
    double high = upper;

    for (int iteration = 0;
         iteration < maxIterations;
         ++iteration) {

        const double midpoint =
            (low + high) / 2.0;

        const double midpointValue =
            functionToSolve(midpoint) - target;

        if (std::abs(midpointValue) <= tolerance) {
            return midpoint;
        }

        if (lowValue * midpointValue <= 0.0) {
            high = midpoint;
            highValue = midpointValue;
        } else {
            low = midpoint;
            lowValue = midpointValue;
        }

        if (std::abs(high - low) <= tolerance) {
            return (low + high) / 2.0;
        }
    }

    return (low + high) / 2.0;
}


// -----------------------------------------------------------------------------
// ONE-VARIABLE SENSITIVITY
// -----------------------------------------------------------------------------

std::vector<std::pair<double, double>> oneVariableSensitivity(
    const ModelInputs& base,
    const std::vector<double>& values,
    const std::function<void(ModelInputs&, double)>& setter,
    const std::function<double(const ModelOutputs&)>& selector
) {
    std::vector<std::pair<double, double>> results;

    for (double value : values) {
        ModelInputs candidate = base;

        // The setter determines which single assumption changes.
        setter(candidate, value);

        const ModelOutputs output =
            calculateModel(candidate);

        results.emplace_back(
            value,
            selector(output)
        );
    }

    return results;
}


// -----------------------------------------------------------------------------
// TWO-VARIABLE SENSITIVITY
// -----------------------------------------------------------------------------

std::vector<std::vector<double>> twoVariableSensitivity(
    const ModelInputs& base,
    const std::vector<double>& rowValues,
    const std::vector<double>& columnValues,
    const std::function<void(ModelInputs&, double)>& rowSetter,
    const std::function<void(ModelInputs&, double)>& columnSetter,
    const std::function<double(const ModelOutputs&)>& selector
) {
    std::vector<std::vector<double>> matrix;

    for (double rowValue : rowValues) {
        std::vector<double> row;

        for (double columnValue : columnValues) {
            ModelInputs candidate = base;

            rowSetter(candidate, rowValue);
            columnSetter(candidate, columnValue);

            const ModelOutputs output =
                calculateModel(candidate);

            row.push_back(selector(output));
        }

        matrix.push_back(row);
    }

    return matrix;
}


// -----------------------------------------------------------------------------
// DCF
// -----------------------------------------------------------------------------

double presentValue(
    double cashFlow,
    double discountRate,
    int period
) {
    if (discountRate <= -1.0) {
        throw std::invalid_argument(
            "Discount rate must be greater than -100%."
        );
    }

    return cashFlow /
           std::pow(1.0 + discountRate, period);
}

double npv(
    const std::vector<double>& cashFlows,
    double discountRate
) {
    double total = 0.0;

    for (std::size_t period = 0;
         period < cashFlows.size();
         ++period) {

        total += presentValue(
            cashFlows[period],
            discountRate,
            static_cast<int>(period)
        );
    }

    return total;
}


// -----------------------------------------------------------------------------
// SENSITIVITY METRICS
// -----------------------------------------------------------------------------

double percentageChange(
    double oldValue,
    double newValue
) {
    if (oldValue == 0.0) {
        throw std::domain_error(
            "Percentage change is undefined when the base is zero."
        );
    }

    return (newValue - oldValue) /
           std::abs(oldValue);
}

double elasticity(
    double baseInput,
    double changedInput,
    double baseOutput,
    double changedOutput
) {
    const double inputChange =
        percentageChange(baseInput, changedInput);

    const double outputChange =
        percentageChange(baseOutput, changedOutput);

    if (inputChange == 0.0) {
        throw std::domain_error(
            "Elasticity cannot be calculated for zero input change."
        );
    }

    return outputChange / inputChange;
}

double numericalDerivative(
    const std::function<double(double)>& function,
    double x,
    double step = 1e-5
) {
    if (step <= 0.0) {
        throw std::invalid_argument(
            "Derivative step must be positive."
        );
    }

    return (
        function(x + step) -
        function(x - step)
    ) / (2.0 * step);
}


// -----------------------------------------------------------------------------
// SCENARIO GRID STATISTICS
// -----------------------------------------------------------------------------

struct GridStatistics {
    double minimum;
    double maximum;
    double mean;
    std::size_t profitableCases;
    std::size_t totalCases;
};

GridStatistics calculateGridStatistics(
    const ModelInputs& base
) {
    const std::vector<double> unitMultipliers{
        0.80, 0.90, 1.00, 1.10, 1.20
    };

    const std::vector<double> priceMultipliers{
        0.90, 0.95, 1.00, 1.05, 1.10
    };

    std::vector<double> profits;

    for (double unitMultiplier : unitMultipliers) {
        for (double priceMultiplier : priceMultipliers) {
            ModelInputs candidate = base;

            candidate.unitsSold =
                base.unitsSold * unitMultiplier;

            candidate.pricePerUnit =
                base.pricePerUnit * priceMultiplier;

            profits.push_back(
                calculateModel(candidate).netProfit
            );
        }
    }

    const double minimum =
        *std::min_element(
            profits.begin(),
            profits.end()
        );

    const double maximum =
        *std::max_element(
            profits.begin(),
            profits.end()
        );

    const double total =
        std::accumulate(
            profits.begin(),
            profits.end(),
            0.0
        );

    const double mean =
        total / static_cast<double>(profits.size());

    const std::size_t profitable =
        static_cast<std::size_t>(
            std::count_if(
                profits.begin(),
                profits.end(),
                [](double value) {
                    return value > 0.0;
                }
            )
        );

    return {
        minimum,
        maximum,
        mean,
        profitable,
        profits.size()
    };
}


// -----------------------------------------------------------------------------
// CASE STUDY
// -----------------------------------------------------------------------------

void runCaseStudy() {
    std::cout << "=====================================================\n";
    std::cout << "EXCEL WHAT-IF ANALYSIS CASE STUDY\n";
    std::cout << "Scenario Manager | Goal Seek | Sensitivity\n";
    std::cout << "=====================================================\n";

    // -------------------------------------------------------------------------
    // Stage 1: Base model
    // -------------------------------------------------------------------------

    const ModelInputs base;

    printOutputs(
        "BASE CASE",
        calculateModel(base)
    );

    // -------------------------------------------------------------------------
    // Stage 2: Scenario Manager
    // -------------------------------------------------------------------------

    std::cout << "\n\n================ SCENARIO MANAGER ================\n";

    ScenarioManager manager(base);

    manager.addScenario(
        "Base",
        base
    );

    ModelInputs optimistic = base;
    optimistic.unitsSold = 13000;
    optimistic.pricePerUnit = 55;
    optimistic.variableCostPerUnit = 26;

    manager.addScenario(
        "Optimistic",
        optimistic
    );

    ModelInputs conservative = base;
    conservative.unitsSold = 8000;
    conservative.pricePerUnit = 47;
    conservative.variableCostPerUnit = 30;

    manager.addScenario(
        "Conservative",
        conservative
    );

    for (const Scenario& scenario :
         manager.getScenarios()) {

        printOutputs(
            scenario.name,
            manager.evaluate(scenario)
        );
    }

    // -------------------------------------------------------------------------
    // Stage 3: Goal Seek
    // -------------------------------------------------------------------------

    std::cout
        << "\n\n================ GOAL SEEK ================\n";

    const double targetProfit = 100000.0;

    const auto profitFromUnits =
        [base](double units) {
            ModelInputs candidate = base;
            candidate.unitsSold = units;

            return calculateModel(candidate).netProfit;
        };

    const double requiredUnits =
        goalSeek(
            profitFromUnits,
            targetProfit,
            0.0,
            100000.0
        );

    std::cout << std::fixed
              << std::setprecision(2);

    std::cout
        << "Target profit: $"
        << targetProfit
        << '\n';

    std::cout
        << "Required units: "
        << requiredUnits
        << '\n';

    std::cout
        << "Calculated profit: $"
        << profitFromUnits(requiredUnits)
        << '\n';

    // -------------------------------------------------------------------------
    // Stage 4: Goal Seek for price
    // -------------------------------------------------------------------------

    std::cout
        << "\n================ PRICE GOAL SEEK ================\n";

    const double targetROI = 0.40;

    const auto roiFromPrice =
        [base](double price) {
            ModelInputs candidate = base;
            candidate.pricePerUnit = price;

            return calculateModel(candidate).roi;
        };

    const double requiredPrice =
        goalSeek(
            roiFromPrice,
            targetROI,
            base.variableCostPerUnit + 0.01,
            200.0
        );

    std::cout
        << "Target ROI: "
        << targetROI * 100.0
        << "%\n";

    std::cout
        << "Required price: $"
        << requiredPrice
        << '\n';

    // -------------------------------------------------------------------------
    // Stage 5: One-variable sensitivity
    // -------------------------------------------------------------------------

    std::cout
        << "\n\n================ ONE-VARIABLE SENSITIVITY ================\n";

    const std::vector<double> prices{
        40.0, 45.0, 50.0, 55.0, 60.0, 65.0
    };

    const auto priceSensitivity =
        oneVariableSensitivity(
            base,
            prices,
            [](ModelInputs& input, double value) {
                input.pricePerUnit = value;
            },
            [](const ModelOutputs& output) {
                return output.netProfit;
            }
        );

    for (const auto& [price, profit] :
         priceSensitivity) {

        std::cout
            << "Price $"
            << price
            << " -> Profit $"
            << profit
            << '\n';
    }

    // -------------------------------------------------------------------------
    // Stage 6: Two-variable sensitivity
    // -------------------------------------------------------------------------

    std::cout
        << "\n\n================ TWO-VARIABLE SENSITIVITY ================\n";

    const std::vector<double> units{
        7500.0, 10000.0, 12500.0, 15000.0
    };

    const std::vector<double> pricesForTable{
        45.0, 50.0, 55.0, 60.0
    };

    const auto matrix =
        twoVariableSensitivity(
            base,
            units,
            pricesForTable,
            [](ModelInputs& input, double value) {
                input.unitsSold = value;
            },
            [](ModelInputs& input, double value) {
                input.pricePerUnit = value;
            },
            [](const ModelOutputs& output) {
                return output.netProfit;
            }
        );

    std::cout << "Units \\ Price";

    for (double price : pricesForTable) {
        std::cout
            << std::setw(14)
            << price;
    }

    std::cout << '\n';

    for (std::size_t row = 0;
         row < matrix.size();
         ++row) {

        std::cout
            << std::setw(12)
            << units[row];

        for (double value : matrix[row]) {
            std::cout
                << std::setw(14)
                << value;
        }

        std::cout << '\n';
    }

    // -------------------------------------------------------------------------
    // Stage 7: Break-even
    // -------------------------------------------------------------------------

    std::cout
        << "\n\n================ BREAK-EVEN ================\n";

    const ModelOutputs baseOutput =
        calculateModel(base);

    if (std::isnan(baseOutput.breakEvenUnits)) {
        std::cout
            << "Break-even is not achievable.\n";
    } else {
        std::cout
            << "Break-even units: "
            << baseOutput.breakEvenUnits
            << '\n';
    }

    // -------------------------------------------------------------------------
    // Stage 8: DCF sensitivity
    // -------------------------------------------------------------------------

    std::cout
        << "\n\n================ DCF SENSITIVITY ================\n";

    const std::vector<double> cashFlows{
        -250000.0,
        80000.0,
        100000.0,
        120000.0,
        140000.0
    };

    const std::vector<double> discountRates{
        0.06, 0.08, 0.10, 0.12, 0.14
    };

    for (double rate : discountRates) {
        std::cout
            << "Discount rate "
            << rate * 100.0
            << "% -> NPV $"
            << npv(cashFlows, rate)
            << '\n';
    }

    // -------------------------------------------------------------------------
    // Stage 9: Numerical sensitivity
    // -------------------------------------------------------------------------

    std::cout
        << "\n\n================ NUMERICAL SENSITIVITY ================\n";

    const auto profitFromPrice =
        [base](double price) {
            ModelInputs candidate = base;
            candidate.pricePerUnit = price;

            return calculateModel(candidate).netProfit;
        };

    const double derivative =
        numericalDerivative(
            profitFromPrice,
            base.pricePerUnit,
            0.01
        );

    std::cout
        << "Approximate profit change per $1 price change: $"
        << derivative
        << '\n';

    const ModelInputs changedUnits = [] {
        ModelInputs candidate;
        candidate.unitsSold = 11000.0;
        return candidate;
    }();

    const double elasticityValue =
        elasticity(
            base.unitsSold,
            changedUnits.unitsSold,
            baseOutput.netProfit,
            calculateModel(changedUnits).netProfit
        );

    std::cout
        << "Approximate unit-demand elasticity: "
        << elasticityValue
        << '\n';

    // -------------------------------------------------------------------------
    // Stage 10: Scenario grid
    // -------------------------------------------------------------------------

    std::cout
        << "\n\n================ SCENARIO GRID ================\n";

    const GridStatistics grid =
        calculateGridStatistics(base);

    std::cout
        << "Total combinations: "
        << grid.totalCases
        << '\n';

    std::cout
        << "Minimum profit: $"
        << grid.minimum
        << '\n';

    std::cout
        << "Maximum profit: $"
        << grid.maximum
        << '\n';

    std::cout
        << "Average profit: $"
        << grid.mean
        << '\n';

    std::cout
        << "Profitable cases: "
        << grid.profitableCases
        << "/"
        << grid.totalCases
        << '\n';

    // -------------------------------------------------------------------------
    // Stage 11: Failure conditions
    // -------------------------------------------------------------------------

    std::cout
        << "\n\n================ VALIDATION AND FAILURE TESTS ================\n";

    try {
        ModelInputs invalid = base;
        invalid.taxRate = 1.5;
        calculateModel(invalid);
    } catch (const std::exception& error) {
        std::cout
            << "Validation caught invalid tax rate: "
            << error.what()
            << '\n';
    }

    try {
        goalSeek(
            [](double x) {
                return x * x;
            },
            10.0,
            1.0,
            2.0
        );
    } catch (const std::exception& error) {
        std::cout
            << "Goal Seek caught invalid bracket: "
            << error.what()
            << '\n';
    }

    std::cout
        << "\nCase study completed successfully.\n";
}


int main() {
    try {
        runCaseStudy();
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
