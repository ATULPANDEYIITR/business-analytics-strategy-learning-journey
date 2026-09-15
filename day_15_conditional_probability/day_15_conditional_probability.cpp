/*
 * Conditional Probability for Business Decisions Under Uncertainty
 * =================================================================
 *
 * C++17 case study:
 * A retail company must decide whether to launch a major product campaign.
 *
 * The system combines:
 *   - customer segmentation
 *   - conditional probabilities
 *   - Bayesian updating
 *   - demand scenarios
 *   - expected monetary value
 *   - risk measurements
 *   - fraud/risk classification
 *   - campaign simulation
 *   - validation
 *
 * Compile:
 *   g++ -std=c++17 -O2 conditional_probability_business.cpp -o business_probability
 *
 * Run:
 *   ./business_probability
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

using namespace std;


// ---------------------------------------------------------------------------
// 1. GENERAL UTILITIES
// ---------------------------------------------------------------------------

constexpr double EPSILON = 1e-9;

void section(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}

void printProbability(const string& label, double value) {
    cout << left << setw(38)
         << label
         << fixed << setprecision(2)
         << value * 100.0
         << "%\n";
}

bool approximatelyEqual(double a, double b, double tolerance = EPSILON) {
    return fabs(a - b) <= tolerance;
}


// ---------------------------------------------------------------------------
// 2. BASIC PROBABILITY
// ---------------------------------------------------------------------------

double probability(long long eventCount, long long totalCount) {
    if (totalCount <= 0) {
        throw invalid_argument(
            "Total count must be positive."
        );
    }

    if (eventCount < 0 || eventCount > totalCount) {
        throw invalid_argument(
            "Event count must be between zero and total count."
        );
    }

    return static_cast<double>(eventCount) /
           static_cast<double>(totalCount);
}


// ---------------------------------------------------------------------------
// 3. CONDITIONAL PROBABILITY
// ---------------------------------------------------------------------------

double conditionalProbability(
    long long jointCount,
    long long conditionCount
) {
    if (conditionCount <= 0) {
        throw invalid_argument(
            "Conditioning count must be positive."
        );
    }

    if (jointCount < 0 || jointCount > conditionCount) {
        throw invalid_argument(
            "Joint count must be between zero and condition count."
        );
    }

    return static_cast<double>(jointCount) /
           static_cast<double>(conditionCount);
}


// ---------------------------------------------------------------------------
// 4. BAYES' THEOREM
// ---------------------------------------------------------------------------

double bayes(
    double prior,
    double likelihoodGivenCondition,
    double likelihoodGivenNotCondition
) {
    if (prior < 0.0 || prior > 1.0) {
        throw invalid_argument(
            "Prior probability must be between zero and one."
        );
    }

    if (likelihoodGivenCondition < 0.0 ||
        likelihoodGivenCondition > 1.0 ||
        likelihoodGivenNotCondition < 0.0 ||
        likelihoodGivenNotCondition > 1.0) {
        throw invalid_argument(
            "Likelihoods must be between zero and one."
        );
    }

    const double evidenceProbability =
        likelihoodGivenCondition * prior +
        likelihoodGivenNotCondition * (1.0 - prior);

    if (evidenceProbability <= EPSILON) {
        throw domain_error(
            "Evidence has approximately zero probability."
        );
    }

    return (
        likelihoodGivenCondition * prior
    ) / evidenceProbability;
}


// ---------------------------------------------------------------------------
// 5. EXPECTED VALUE
// ---------------------------------------------------------------------------

struct Scenario {
    string name;
    double probability;
    double payoff;
};

double expectedValue(
    const vector<Scenario>& scenarios
) {
    double probabilitySum = 0.0;

    for (const auto& scenario : scenarios) {
        if (scenario.probability < 0.0 ||
            scenario.probability > 1.0) {
            throw invalid_argument(
                "Scenario probability must be between zero and one."
            );
        }

        probabilitySum += scenario.probability;
    }

    if (!approximatelyEqual(probabilitySum, 1.0)) {
        throw invalid_argument(
            "Scenario probabilities must sum to one."
        );
    }

    double result = 0.0;

    for (const auto& scenario : scenarios) {
        result += scenario.probability * scenario.payoff;
    }

    return result;
}


pair<double, double> expectedValueAndVariance(
    const vector<Scenario>& scenarios
) {
    const double mean = expectedValue(scenarios);

    double variance = 0.0;

    for (const auto& scenario : scenarios) {
        variance +=
            scenario.probability *
            pow(scenario.payoff - mean, 2.0);
    }

    return {mean, variance};
}


// ---------------------------------------------------------------------------
// 6. CUSTOMER SEGMENT
// ---------------------------------------------------------------------------

struct CustomerSegment {
    string name;
    double populationShare;
    double conversionRate;
};

double overallConversion(
    const vector<CustomerSegment>& segments
) {
    double shareSum = 0.0;
    double conversion = 0.0;

    for (const auto& segment : segments) {
        if (segment.populationShare < 0.0 ||
            segment.populationShare > 1.0 ||
            segment.conversionRate < 0.0 ||
            segment.conversionRate > 1.0) {
            throw invalid_argument(
                "Segment probabilities must be between zero and one."
            );
        }

        shareSum += segment.populationShare;

        conversion +=
            segment.populationShare *
            segment.conversionRate;
    }

    if (!approximatelyEqual(shareSum, 1.0)) {
        throw invalid_argument(
            "Segment population shares must sum to one."
        );
    }

    return conversion;
}


// ---------------------------------------------------------------------------
// 7. CUSTOMER RISK MODEL
// ---------------------------------------------------------------------------

enum class RiskLevel {
    Low,
    Medium,
    High
};

string riskLevelName(RiskLevel level) {
    switch (level) {
        case RiskLevel::Low:
            return "Low";
        case RiskLevel::Medium:
            return "Medium";
        case RiskLevel::High:
            return "High";
    }

    return "Unknown";
}

RiskLevel classifyRisk(double probabilityOfDefault) {
    if (probabilityOfDefault < 0.03) {
        return RiskLevel::Low;
    }

    if (probabilityOfDefault < 0.10) {
        return RiskLevel::Medium;
    }

    return RiskLevel::High;
}

struct Customer {
    string id;
    double probabilityOfDefault;
};


// ---------------------------------------------------------------------------
// 8. BUSINESS DECISION
// ---------------------------------------------------------------------------

struct Decision {
    string name;
    map<string, double> payoffs;

    double expectedPayoff(
        const map<string, double>& stateProbabilities
    ) const {
        double result = 0.0;

        for (const auto& [state, stateProbability]
             : stateProbabilities) {

            const auto payoffIterator =
                payoffs.find(state);

            if (payoffIterator == payoffs.end()) {
                throw invalid_argument(
                    "Decision does not define payoff for state: " +
                    state
                );
            }

            result +=
                stateProbability *
                payoffIterator->second;
        }

        return result;
    }

    double bestCase() const {
        if (payoffs.empty()) {
            throw invalid_argument(
                "Decision has no payoffs."
            );
        }

        return max_element(
            payoffs.begin(),
            payoffs.end(),
            [](const auto& left, const auto& right) {
                return left.second < right.second;
            }
        )->second;
    }

    double worstCase() const {
        if (payoffs.empty()) {
            throw invalid_argument(
                "Decision has no payoffs."
            );
        }

        return min_element(
            payoffs.begin(),
            payoffs.end(),
            [](const auto& left, const auto& right) {
                return left.second < right.second;
            }
        )->second;
    }
};


// ---------------------------------------------------------------------------
// 9. CONFUSION MATRIX
// ---------------------------------------------------------------------------

struct ConfusionMatrix {
    long long truePositive;
    long long falsePositive;
    long long trueNegative;
    long long falseNegative;

    double precision() const {
        const long long denominator =
            truePositive + falsePositive;

        if (denominator == 0) {
            throw domain_error(
                "Precision denominator is zero."
            );
        }

        return probability(
            truePositive,
            denominator
        );
    }

    double recall() const {
        const long long denominator =
            truePositive + falseNegative;

        if (denominator == 0) {
            throw domain_error(
                "Recall denominator is zero."
            );
        }

        return probability(
            truePositive,
            denominator
        );
    }

    double specificity() const {
        const long long denominator =
            trueNegative + falsePositive;

        if (denominator == 0) {
            throw domain_error(
                "Specificity denominator is zero."
            );
        }

        return probability(
            trueNegative,
            denominator
        );
    }
};


// ---------------------------------------------------------------------------
// 10. MONTE CARLO CAMPAIGN SIMULATION
// ---------------------------------------------------------------------------

struct SimulationResult {
    long long trials;
    long long successes;

    double successRate() const {
        if (trials == 0) {
            return 0.0;
        }

        return static_cast<double>(successes) /
               static_cast<double>(trials);
    }
};

SimulationResult simulateConversion(
    long long trials,
    double conversionProbability,
    unsigned int seed
) {
    if (trials <= 0) {
        throw invalid_argument(
            "Simulation trials must be positive."
        );
    }

    if (conversionProbability < 0.0 ||
        conversionProbability > 1.0) {
        throw invalid_argument(
            "Conversion probability must be between zero and one."
        );
    }

    mt19937 generator(seed);
    bernoulli_distribution experiment(
        conversionProbability
    );

    long long successes = 0;

    for (long long i = 0; i < trials; ++i) {
        if (experiment(generator)) {
            ++successes;
        }
    }

    return {trials, successes};
}


// ---------------------------------------------------------------------------
// 11. PROBABILITY TABLE
// ---------------------------------------------------------------------------

class ProbabilityTable {
private:
    map<string, map<string, double>> table;

public:
    explicit ProbabilityTable(
        map<string, map<string, double>> input
    )
        : table(move(input)) {

        if (table.empty()) {
            throw invalid_argument(
                "Probability table cannot be empty."
            );
        }

        double total = 0.0;

        for (const auto& [rowName, row] : table) {
            if (row.empty()) {
                throw invalid_argument(
                    "Probability table contains an empty row."
                );
            }

            for (const auto& [columnName, value] : row) {
                if (value < 0.0) {
                    throw invalid_argument(
                        "Joint probabilities cannot be negative."
                    );
                }

                total += value;
            }
        }

        if (!approximatelyEqual(total, 1.0)) {
            throw invalid_argument(
                "Joint probabilities must sum to one."
            );
        }
    }

    double marginalRow(
        const string& rowName
    ) const {
        const auto rowIterator =
            table.find(rowName);

        if (rowIterator == table.end()) {
            throw out_of_range(
                "Unknown row: " + rowName
            );
        }

        double result = 0.0;

        for (const auto& [column, value]
             : rowIterator->second) {
            result += value;
        }

        return result;
    }

    double marginalColumn(
        const string& columnName
    ) const {
        double result = 0.0;

        for (const auto& [rowName, row]
             : table) {

            auto iterator =
                row.find(columnName);

            if (iterator != row.end()) {
                result += iterator->second;
            }
        }

        return result;
    }

    double joint(
        const string& rowName,
        const string& columnName
    ) const {
        return table.at(rowName).at(columnName);
    }

    double conditionalColumnGivenRow(
        const string& columnName,
        const string& rowName
    ) const {
        const double denominator =
            marginalRow(rowName);

        if (denominator <= EPSILON) {
            throw domain_error(
                "Cannot condition on a zero-probability row."
            );
        }

        return joint(rowName, columnName) /
               denominator;
    }

    double conditionalRowGivenColumn(
        const string& rowName,
        const string& columnName
    ) const {
        const double denominator =
            marginalColumn(columnName);

        if (denominator <= EPSILON) {
            throw domain_error(
                "Cannot condition on a zero-probability column."
            );
        }

        return joint(rowName, columnName) /
               denominator;
    }
};


// ---------------------------------------------------------------------------
// 12. DECISION ANALYSIS SYSTEM
// ---------------------------------------------------------------------------

class DecisionAnalysisSystem {
private:
    map<string, double> marketStates;
    vector<Decision> decisions;

public:
    DecisionAnalysisSystem(
        map<string, double> states,
        vector<Decision> decisionList
    )
        : marketStates(move(states)),
          decisions(move(decisionList)) {

        double totalProbability = 0.0;

        for (const auto& [state, p] : marketStates) {
            if (p < 0.0 || p > 1.0) {
                throw invalid_argument(
                    "State probability is invalid."
                );
            }

            totalProbability += p;
        }

        if (!approximatelyEqual(totalProbability, 1.0)) {
            throw invalid_argument(
                "Market-state probabilities must sum to one."
            );
        }

        if (decisions.empty()) {
            throw invalid_argument(
                "At least one decision is required."
            );
        }
    }

    const Decision& bestExpectedValueDecision() const {
        return *max_element(
            decisions.begin(),
            decisions.end(),
            [this](const Decision& a, const Decision& b) {
                return a.expectedPayoff(marketStates) <
                       b.expectedPayoff(marketStates);
            }
        );
    }

    double expectedValueWithPerfectInformation() const {
        double result = 0.0;

        for (const auto& [state, stateProbability]
             : marketStates) {

            double bestPayoff =
                -numeric_limits<double>::infinity();

            for (const auto& decision : decisions) {
                const auto payoffIterator =
                    decision.payoffs.find(state);

                if (payoffIterator == decision.payoffs.end()) {
                    throw invalid_argument(
                        "Missing state payoff."
                    );
                }

                bestPayoff =
                    max(
                        bestPayoff,
                        payoffIterator->second
                    );
            }

            result +=
                stateProbability * bestPayoff;
        }

        return result;
    }

    double expectedValueOfPerfectInformation() const {
        const Decision& best =
            bestExpectedValueDecision();

        const double bestWithoutInformation =
            best.expectedPayoff(marketStates);

        return
            expectedValueWithPerfectInformation() -
            bestWithoutInformation;
    }

    void printDecisionAnalysis() const {
        cout << left
             << setw(20)
             << "Decision"
             << setw(20)
             << "Expected Value"
             << setw(18)
             << "Worst Case"
             << "Best Case\n";

        cout << string(75, '-') << "\n";

        for (const auto& decision : decisions) {
            cout << left
                 << setw(20)
                 << decision.name
                 << "₹"
                 << setw(19)
                 << fixed
                 << setprecision(0)
                 << decision.expectedPayoff(marketStates)
                 << "₹"
                 << setw(17)
                 << decision.worstCase()
                 << "₹"
                 << decision.bestCase()
                 << "\n";
        }
    }
};


// ---------------------------------------------------------------------------
// 13. MAIN CASE STUDY
// ---------------------------------------------------------------------------

int main() {
    try {
        cout << fixed << setprecision(4);

        // -------------------------------------------------------------------
        // Basic probability
        // -------------------------------------------------------------------

        section("1. Basic probability");

        const long long visitors = 10000;
        const long long purchases = 1800;

        const double purchaseRate =
            probability(purchases, visitors);

        printProbability(
            "Observed purchase probability",
            purchaseRate
        );


        // -------------------------------------------------------------------
        // Conditional probability
        // -------------------------------------------------------------------

        section("2. Conditional probability");

        const long long mobileVisitors = 6000;
        const long long mobilePurchases = 1500;

        const double pMobile =
            probability(mobileVisitors, visitors);

        const double pMobileAndPurchase =
            probability(mobilePurchases, visitors);

        const double pPurchaseGivenMobile =
            pMobileAndPurchase / pMobile;

        printProbability(
            "P(Mobile)",
            pMobile
        );

        printProbability(
            "P(Mobile and Purchase)",
            pMobileAndPurchase
        );

        printProbability(
            "P(Purchase | Mobile)",
            pPurchaseGivenMobile
        );


        // -------------------------------------------------------------------
        // Reverse conditional probability
        // -------------------------------------------------------------------

        section("3. Reverse conditional probability");

        const long long totalCustomers = 10000;
        const long long purchasingCustomers = 2000;
        const long long mobilePurchasingCustomers = 1200;

        const double pMobileGivenPurchase =
            probability(
                mobilePurchasingCustomers,
                purchasingCustomers
            );

        const double pPurchaseGivenMobile2 =
            conditionalProbability(
                mobilePurchasingCustomers,
                mobileVisitors
            );

        printProbability(
            "P(Mobile | Purchase)",
            pMobileGivenPurchase
        );

        printProbability(
            "P(Purchase | Mobile)",
            pPurchaseGivenMobile2
        );


        // -------------------------------------------------------------------
        // Bayes theorem
        // -------------------------------------------------------------------

        section("4. Bayes' theorem: fraud detection");

        const double fraudPrior = 0.01;
        const double flagGivenFraud = 0.95;
        const double flagGivenLegitimate = 0.05;

        const double fraudGivenFlag =
            bayes(
                fraudPrior,
                flagGivenFraud,
                flagGivenLegitimate
            );

        printProbability(
            "P(Fraud | Flag)",
            fraudGivenFlag
        );

        cout
            << "Interpretation: a positive fraud signal does not imply "
            << "that fraud is certain. The low base rate matters.\n";


        // -------------------------------------------------------------------
        // Total probability
        // -------------------------------------------------------------------

        section("5. Law of total probability");

        const vector<CustomerSegment> segments = {
            {"North", 0.25, 0.12},
            {"South", 0.35, 0.08},
            {"East", 0.20, 0.15},
            {"West", 0.20, 0.10}
        };

        const double totalConversion =
            overallConversion(segments);

        printProbability(
            "Overall conversion",
            totalConversion
        );


        // -------------------------------------------------------------------
        // Customer risk
        // -------------------------------------------------------------------

        section("6. Customer risk classification");

        const vector<Customer> customers = {
            {"C001", 0.015},
            {"C002", 0.075},
            {"C003", 0.220},
            {"C004", 0.110}
        };

        cout
            << left
            << setw(10)
            << "ID"
            << setw(20)
            << "Default Probability"
            << "Risk\n";

        cout << string(48, '-') << "\n";

        for (const auto& customer : customers) {
            cout
                << left
                << setw(10)
                << customer.id
                << setw(20)
                << customer.probabilityOfDefault
                << riskLevelName(
                    classifyRisk(
                        customer.probabilityOfDefault
                    )
                )
                << "\n";
        }


        // -------------------------------------------------------------------
        // Confusion matrix
        // -------------------------------------------------------------------

        section("7. Classification metrics");

        const ConfusionMatrix matrix {
            760,
            140,
            8500,
            600
        };

        printProbability(
            "Precision",
            matrix.precision()
        );

        printProbability(
            "Recall",
            matrix.recall()
        );

        printProbability(
            "Specificity",
            matrix.specificity()
        );


        // -------------------------------------------------------------------
        // Monte Carlo
        // -------------------------------------------------------------------

        section("8. Monte Carlo conversion simulation");

        const SimulationResult simulation =
            simulateConversion(
                100000,
                0.18,
                42
            );

        printProbability(
            "Simulated conversion",
            simulation.successRate()
        );

        printProbability(
            "Theoretical conversion",
            0.18
        );


        // -------------------------------------------------------------------
        // Probability table
        // -------------------------------------------------------------------

        section("9. Joint probability table");

        /*
         * Each cell represents a joint probability.
         *
         *                 Buy       No Buy
         * New             0.08       0.42
         * Returning       0.20       0.30
         *
         * The total equals 1.
         */

        const ProbabilityTable customerTable({
            {
                "New",
                {
                    {"Buy", 0.08},
                    {"NoBuy", 0.42}
                }
            },
            {
                "Returning",
                {
                    {"Buy", 0.20},
                    {"NoBuy", 0.30}
                }
            }
        });

        printProbability(
            "P(Buy | Returning)",
            customerTable.conditionalColumnGivenRow(
                "Buy",
                "Returning"
            )
        );

        printProbability(
            "P(Returning | Buy)",
            customerTable.conditionalRowGivenColumn(
                "Returning",
                "Buy"
            )
        );


        // -------------------------------------------------------------------
        // Market decision
        // -------------------------------------------------------------------

        section("10. Product launch decision");

        /*
         * The company has three choices:
         *
         * Large launch:
         *   High demand   -> ₹600,000
         *   Normal demand -> ₹180,000
         *   Low demand    -> -₹250,000
         *
         * Small launch:
         *   High demand   -> ₹300,000
         *   Normal demand -> ₹140,000
         *   Low demand    -> ₹20,000
         *
         * Delay:
         *   High demand   -> ₹100,000
         *   Normal demand -> ₹80,000
         *   Low demand    -> ₹50,000
         */

        const map<string, double> marketStates = {
            {"High", 0.30},
            {"Normal", 0.50},
            {"Low", 0.20}
        };

        const vector<Decision> decisions = {
            {
                "Large launch",
                {
                    {"High", 600000},
                    {"Normal", 180000},
                    {"Low", -250000}
                }
            },
            {
                "Small launch",
                {
                    {"High", 300000},
                    {"Normal", 140000},
                    {"Low", 20000}
                }
            },
            {
                "Delay",
                {
                    {"High", 100000},
                    {"Normal", 80000},
                    {"Low", 50000}
                }
            }
        };

        const DecisionAnalysisSystem decisionSystem(
            marketStates,
            decisions
        );

        decisionSystem.printDecisionAnalysis();

        const Decision& bestDecision =
            decisionSystem.bestExpectedValueDecision();

        cout
            << "\nBest expected-value decision: "
            << bestDecision.name
            << "\n";

        cout
            << "Expected value with perfect information: ₹"
            << decisionSystem
                .expectedValueWithPerfectInformation()
            << "\n";

        cout
            << "Expected value of perfect information: ₹"
            << decisionSystem
                .expectedValueOfPerfectInformation()
            << "\n";


        // -------------------------------------------------------------------
        // Risk comparison
        // -------------------------------------------------------------------

        section("11. Expected value versus risk");

        const vector<Scenario> risky = {
            {"High return", 0.50, 300000},
            {"Loss", 0.50, -100000}
        };

        const vector<Scenario> stable = {
            {"Good result", 0.90, 120000},
            {"Weak result", 0.10, 80000}
        };

        for (const auto& [name, scenarios] :
             vector<pair<string, vector<Scenario>>>{
                 {"Risky", risky},
                 {"Stable", stable}
             }) {

            const auto [mean, variance] =
                expectedValueAndVariance(scenarios);

            cout
                << left
                << setw(10)
                << name
                << "Expected Value = ₹"
                << setw(12)
                << mean
                << "Standard Deviation = ₹"
                << sqrt(variance)
                << "\n";
        }


        // -------------------------------------------------------------------
        // Bayesian update
        // -------------------------------------------------------------------

        section("12. Bayesian market update");

        double priorGoodMarket = 0.30;

        cout
            << "Initial probability of strong market: "
            << priorGoodMarket
            << "\n";

        priorGoodMarket =
            bayes(
                priorGoodMarket,
                0.80,
                0.30
            );

        cout
            << "After positive sales signal: "
            << priorGoodMarket
            << "\n";

        priorGoodMarket =
            bayes(
                priorGoodMarket,
                0.70,
                0.40
            );

        cout
            << "After positive retention signal: "
            << priorGoodMarket
            << "\n";


        // -------------------------------------------------------------------
        // Decision threshold
        // -------------------------------------------------------------------

        section("13. Preventive action threshold");

        const double preventiveCost = 10000;
        const double lossWithoutProtection = 80000;
        const double lossWithProtection = 10000;

        const double riskReduction =
            lossWithoutProtection -
            lossWithProtection;

        const double breakEvenProbability =
            preventiveCost /
            riskReduction;

        printProbability(
            "Break-even event probability",
            breakEvenProbability
        );

        cout
            << "If the estimated event probability is above this threshold, "
            << "the preventive action has positive expected monetary value.\n";


        // -------------------------------------------------------------------
        // A/B testing
        // -------------------------------------------------------------------

        section("14. A/B testing");

        const long long controlVisitors = 5000;
        const long long controlConversions = 450;

        const long long treatmentVisitors = 5000;
        const long long treatmentConversions = 550;

        const double controlRate =
            probability(
                controlConversions,
                controlVisitors
            );

        const double treatmentRate =
            probability(
                treatmentConversions,
                treatmentVisitors
            );

        const double absoluteLift =
            treatmentRate - controlRate;

        const double relativeLift =
            absoluteLift / controlRate;

        printProbability(
            "Control conversion",
            controlRate
        );

        printProbability(
            "Treatment conversion",
            treatmentRate
        );

        printProbability(
            "Absolute lift",
            absoluteLift
        );

        cout
            << "Relative lift: "
            << relativeLift * 100.0
            << "%\n";


        // -------------------------------------------------------------------
        // Statistical uncertainty
        // -------------------------------------------------------------------

        section("15. Approximate sampling uncertainty");

        const double standardError =
            sqrt(
                treatmentRate *
                (1.0 - treatmentRate) /
                static_cast<double>(treatmentVisitors)
            );

        const double marginOfError =
            1.96 * standardError;

        printProbability(
            "Approximate 95% margin of error",
            marginOfError
        );


        // -------------------------------------------------------------------
        // Edge-case validation
        // -------------------------------------------------------------------

        section("16. Edge-case handling");

        try {
            conditionalProbability(1, 0);
        }
        catch (const exception& error) {
            cout
                << "Handled zero-probability condition: "
                << error.what()
                << "\n";
        }

        try {
            probability(20, 10);
        }
        catch (const exception& error) {
            cout
                << "Handled invalid event count: "
                << error.what()
                << "\n";
        }

        try {
            bayes(1.5, 0.8, 0.2);
        }
        catch (const exception& error) {
            cout
                << "Handled invalid Bayesian prior: "
                << error.what()
                << "\n";
        }


        // -------------------------------------------------------------------
        // Embedded tests
        // -------------------------------------------------------------------

        section("17. Embedded tests");

        if (!approximatelyEqual(
                conditionalProbability(25, 100),
                0.25
            )) {
            throw runtime_error(
                "Conditional probability test failed."
            );
        }

        if (!approximatelyEqual(
                probability(18, 100),
                0.18
            )) {
            throw runtime_error(
                "Probability test failed."
            );
        }

        if (!approximatelyEqual(
                bayes(0.5, 0.8, 0.2),
                0.8
            )) {
            throw runtime_error(
                "Bayes test failed."
            );
        }

        if (!approximatelyEqual(
                overallConversion({
                    {"A", 0.5, 0.10},
                    {"B", 0.5, 0.20}
                }),
                0.15
            )) {
            throw runtime_error(
                "Weighted probability test failed."
            );
        }

        cout
            << "All embedded tests passed.\n";


        // -------------------------------------------------------------------
        // Complexity and architecture notes
        // -------------------------------------------------------------------

        section("18. Implementation characteristics");

        cout
            << "Conditional probability calculation: O(1)\n"
            << "Bayesian update: O(1)\n"
            << "Expected value across n states: O(n)\n"
            << "Probability-table marginalization: O(rows * columns)\n"
            << "Monte Carlo simulation: O(trials)\n"
            << "Decision evaluation: O(decisions * states)\n"
            << "Memory use is dominated by stored scenario and table data.\n";

        cout
            << "\nThe architecture separates probability mathematics, "
            << "customer segmentation, risk classification, simulation, "
            << "and decision analysis so each component can be validated "
            << "independently.\n";


        // -------------------------------------------------------------------
        // Final business interpretation
        // -------------------------------------------------------------------

        section("19. Business interpretation");

        cout
            << "The system demonstrates a central principle of decision "
            << "analysis: probabilities must be interpreted relative to "
            << "the information currently available.\n";

        cout
            << "A conditional probability changes the reference population. "
            << "Bayesian updating changes beliefs after evidence. Expected "
            << "value converts uncertain financial outcomes into a comparable "
            << "decision metric.\n";

        cout
            << "The model does not establish causality merely because one "
            << "conditional probability is higher than another. Business "
            << "decisions still require attention to selection effects, "
            << "confounding variables, data quality, model assumptions, "
            << "and the cost of incorrect decisions.\n";

        return 0;
    }
    catch (const exception& error) {
        cerr
            << "\nFatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
