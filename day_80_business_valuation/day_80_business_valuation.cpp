#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * BUSINESS VALUATION AND GOVERNANCE ENGINE
 *
 * Implements:
 * 1. DCF valuation
 * 2. WACC calculation
 * 3. FCFF forecasting
 * 4. Gordon Growth terminal value
 * 5. Comparable company analysis
 * 6. Enterprise-to-equity bridge
 * 7. Scenario evaluation
 * 8. Sensitivity analysis
 *
 * Standard: C++17
 * External libraries: None
 */

using namespace std;

class ValuationError : public runtime_error {
public:
    explicit ValuationError(const string& message)
        : runtime_error(message) {}
};

enum class Scenario {
    Bear,
    Base,
    Bull
};

struct FinancialStatements {
    double revenue;
    double ebit;
    double depreciation;
    double capex;
    double workingCapitalIncrease;
    double taxRate;
    double cash;
    double debt;
    double shares;
};

struct CapitalStructure {
    double costOfEquity;
    double costOfDebt;
    double equityWeight;
    double debtWeight;
};

struct ForecastAssumptions {
    vector<double> growthRates;
    vector<double> ebitMargins;
    double taxRate;
    double depreciationRate;
    double capexRate;
    double workingCapitalRate;
    double terminalGrowth;
};

struct ForecastYear {
    int year;
    double revenue;
    double ebit;
    double nopat;
    double depreciation;
    double capex;
    double workingCapitalChange;
    double fcff;
    double discountFactor;
    double presentValue;
};

struct DCFResult {
    double wacc;
    double explicitValue;
    double terminalValue;
    double terminalPresentValue;
    double enterpriseValue;
    double equityValue;
    double valuePerShare;
    double terminalContribution;
    vector<ForecastYear> forecast;
};

struct ComparableCompany {
    string name;
    double enterpriseValue;
    double revenue;
    double ebitda;
    double netIncome;

    double evRevenue() const {
        return enterpriseValue / revenue;
    }

    double evEbitda() const {
        return enterpriseValue / ebitda;
    }

    double peRatio() const {
        return enterpriseValue / netIncome;
    }
};

struct ScenarioResult {
    Scenario scenario;
    DCFResult result;
};

void validatePositive(double value, const string& field) {
    if (!isfinite(value) || value <= 0) {
        throw ValuationError(field + " must be positive.");
    }
}

void validateNonNegative(double value, const string& field) {
    if (!isfinite(value) || value < 0) {
        throw ValuationError(field + " cannot be negative.");
    }
}

void validateRate(double value, const string& field) {
    if (!isfinite(value) || value < 0 || value >= 1) {
        throw ValuationError(field + " must be between 0 and 1.");
    }
}

void validateFinancials(const FinancialStatements& f) {
    validatePositive(f.revenue, "Revenue");
    validatePositive(f.shares, "Shares");
    validateNonNegative(f.depreciation, "Depreciation");
    validateNonNegative(f.capex, "Capital expenditure");
    validateNonNegative(f.cash, "Cash");
    validateNonNegative(f.debt, "Debt");
    validateRate(f.taxRate, "Tax rate");

    if (!isfinite(f.ebit) || f.ebit < 0) {
        throw ValuationError(
            "This model requires non-negative operating income."
        );
    }
}

void validateCapital(const CapitalStructure& c) {
    validateRate(c.costOfEquity, "Cost of equity");
    validateRate(c.costOfDebt, "Cost of debt");

    if (c.equityWeight < 0 || c.debtWeight < 0) {
        throw ValuationError("Capital weights cannot be negative.");
    }

    if (abs(c.equityWeight + c.debtWeight - 1.0) > 1e-9) {
        throw ValuationError("Capital weights must sum to 1.");
    }
}

void validateForecast(const ForecastAssumptions& a) {
    if (a.growthRates.empty() ||
        a.growthRates.size() != a.ebitMargins.size()) {
        throw ValuationError("Invalid forecast period configuration.");
    }

    for (double growth : a.growthRates) {
        if (!isfinite(growth) || growth <= -1) {
            throw ValuationError("Invalid revenue growth rate.");
        }
    }

    for (double margin : a.ebitMargins) {
        validateRate(margin, "EBIT margin");
    }

    validateRate(a.taxRate, "Forecast tax rate");
    validateRate(a.depreciationRate, "Depreciation rate");
    validateRate(a.capexRate, "Capital expenditure rate");
    validateRate(a.workingCapitalRate, "Working capital rate");
    validateRate(a.terminalGrowth, "Terminal growth rate");
}

class ValuationEngine {
private:
    FinancialStatements financials;
    CapitalStructure capital;
    ForecastAssumptions assumptions;

    double calculateWACC() const {
        return
            capital.equityWeight * capital.costOfEquity +
            capital.debtWeight * capital.costOfDebt *
            (1.0 - financials.taxRate);
    }

public:
    ValuationEngine(
        FinancialStatements f,
        CapitalStructure c,
        ForecastAssumptions a
    ) : financials(move(f)),
        capital(move(c)),
        assumptions(move(a)) {

        validateFinancials(financials);
        validateCapital(capital);
        validateForecast(assumptions);

        const double wacc = calculateWACC();

        if (wacc <= 0 || wacc <= assumptions.terminalGrowth) {
            throw ValuationError(
                "WACC must exceed terminal growth."
            );
        }
    }

    vector<ForecastYear> project(double discountRate) const {
        vector<ForecastYear> forecast;

        double revenue = financials.revenue;

        double previousWorkingCapital =
            revenue * assumptions.workingCapitalRate;

        for (size_t i = 0; i < assumptions.growthRates.size(); ++i) {
            revenue *= 1.0 + assumptions.growthRates[i];

            const double ebit =
                revenue * assumptions.ebitMargins[i];

            const double nopat =
                ebit * (1.0 - assumptions.taxRate);

            const double depreciation =
                revenue * assumptions.depreciationRate;

            const double capex =
                revenue * assumptions.capexRate;

            const double currentWorkingCapital =
                revenue * assumptions.workingCapitalRate;

            const double workingCapitalChange =
                currentWorkingCapital - previousWorkingCapital;

            // FCFF is measured before financing costs.
            const double fcff =
                nopat +
                depreciation -
                capex -
                workingCapitalChange;

            const double discountFactor =
                1.0 / pow(1.0 + discountRate, static_cast<double>(i + 1));

            forecast.push_back({
                static_cast<int>(i + 1),
                revenue,
                ebit,
                nopat,
                depreciation,
                capex,
                workingCapitalChange,
                fcff,
                discountFactor,
                fcff * discountFactor
            });

            previousWorkingCapital = currentWorkingCapital;
        }

        return forecast;
    }

    DCFResult calculate() const {
        const double wacc = calculateWACC();

        vector<ForecastYear> forecast = project(wacc);

        double explicitValue = 0;

        for (const auto& year : forecast) {
            explicitValue += year.presentValue;
        }

        const double finalFCFF = forecast.back().fcff;

        const double terminalValue =
            finalFCFF * (1.0 + assumptions.terminalGrowth) /
            (wacc - assumptions.terminalGrowth);

        const double terminalPV =
            terminalValue /
            pow(1.0 + wacc, static_cast<double>(forecast.size()));

        const double enterpriseValue = explicitValue + terminalPV;

        // Cash and debt reconcile enterprise value to equity value.
        const double equityValue =
            enterpriseValue + financials.cash - financials.debt;

        return {
            wacc,
            explicitValue,
            terminalValue,
            terminalPV,
            enterpriseValue,
            equityValue,
            equityValue / financials.shares,
            terminalPV / enterpriseValue,
            move(forecast)
        };
    }

    vector<vector<double>> sensitivity(
        const vector<double>& waccChanges,
        const vector<double>& growthChanges
    ) const {
        const DCFResult base = calculate();

        vector<vector<double>> matrix;

        for (double waccChange : waccChanges) {
            const double adjustedWACC =
                base.wacc + waccChange;

            vector<double> row;

            for (double growthChange : growthChanges) {
                const double adjustedGrowth =
                    assumptions.terminalGrowth + growthChange;

                if (
                    adjustedWACC <= 0 ||
                    adjustedGrowth < 0 ||
                    adjustedGrowth >= adjustedWACC
                ) {
                    row.push_back(numeric_limits<double>::quiet_NaN());
                    continue;
                }

                double explicitValue = 0;

                for (const auto& year : base.forecast) {
                    explicitValue +=
                        year.fcff /
                        pow(
                            1.0 + adjustedWACC,
                            static_cast<double>(year.year)
                        );
                }

                const double terminalValue =
                    base.forecast.back().fcff *
                    (1.0 + adjustedGrowth) /
                    (adjustedWACC - adjustedGrowth);

                const double terminalPV =
                    terminalValue /
                    pow(
                        1.0 + adjustedWACC,
                        static_cast<double>(base.forecast.size())
                    );

                row.push_back(explicitValue + terminalPV);
            }

            matrix.push_back(move(row));
        }

        return matrix;
    }
};

class ComparableValuator {
private:
    vector<ComparableCompany> companies;

    static double median(vector<double> values) {
        if (values.empty()) {
            throw ValuationError("Cannot calculate an empty median.");
        }

        sort(values.begin(), values.end());

        const size_t middle = values.size() / 2;

        if (values.size() % 2 == 0) {
            return (values[middle - 1] + values[middle]) / 2.0;
        }

        return values[middle];
    }

public:
    explicit ComparableValuator(
        vector<ComparableCompany> data
    ) : companies(move(data)) {
        if (companies.empty()) {
            throw ValuationError("Comparable dataset is empty.");
        }

        for (const auto& company : companies) {
            if (company.name.empty()) {
                throw ValuationError("Company name is required.");
            }

            validatePositive(company.enterpriseValue, "Comparable EV");
            validatePositive(company.revenue, "Comparable revenue");
            validatePositive(company.ebitda, "Comparable EBITDA");
            validatePositive(company.netIncome, "Comparable net income");
        }
    }

    map<string, double> calculateMultiples() const {
        vector<double> evRevenue;
        vector<double> evEbitda;
        vector<double> pe;

        for (const auto& company : companies) {
            evRevenue.push_back(company.evRevenue());
            evEbitda.push_back(company.evEbitda());
            pe.push_back(company.peRatio());
        }

        return {
            {"EV/Revenue", median(evRevenue)},
            {"EV/EBITDA", median(evEbitda)},
            {"P/E", median(pe)}
        };
    }

    map<string, double> valueTarget(
        double revenue,
        double ebitda,
        double netIncome,
        double cash,
        double debt,
        double shares
    ) const {
        validatePositive(revenue, "Target revenue");
        validatePositive(ebitda, "Target EBITDA");
        validatePositive(netIncome, "Target net income");
        validateNonNegative(cash, "Target cash");
        validateNonNegative(debt, "Target debt");
        validatePositive(shares, "Target shares");

        const auto multiples = calculateMultiples();

        const double evByRevenue =
            revenue * multiples.at("EV/Revenue");

        const double evByEBITDA =
            ebitda * multiples.at("EV/EBITDA");

        const double equityByPE =
            netIncome * multiples.at("P/E");

        const double equityByRevenue =
            evByRevenue + cash - debt;

        const double equityByEBITDA =
            evByEBITDA + cash - debt;

        return {
            {"EV by Revenue", evByRevenue},
            {"EV by EBITDA", evByEBITDA},
            {"Equity by Revenue", equityByRevenue},
            {"Equity by EBITDA", equityByEBITDA},
            {"Equity by P/E", equityByPE},
            {"Price by Revenue", equityByRevenue / shares},
            {"Price by EBITDA", equityByEBITDA / shares},
            {"Price by P/E", equityByPE / shares}
        };
    }
};

ForecastAssumptions getScenario(Scenario scenario) {
    switch (scenario) {
        case Scenario::Bear:
            return {
                {0.04, 0.035, 0.03, 0.025, 0.02},
                {0.15, 0.15, 0.155, 0.16, 0.16},
                0.25, 0.035, 0.06, 0.12, 0.02
            };

        case Scenario::Base:
            return {
                {0.10, 0.09, 0.08, 0.07, 0.06},
                {0.18, 0.19, 0.20, 0.205, 0.21},
                0.25, 0.04, 0.055, 0.10, 0.03
            };

        case Scenario::Bull:
            return {
                {0.16, 0.14, 0.12, 0.10, 0.08},
                {0.20, 0.21, 0.22, 0.23, 0.23},
                0.25, 0.045, 0.05, 0.09, 0.035
            };
    }

    throw ValuationError("Unknown scenario.");
}

string scenarioName(Scenario scenario) {
    switch (scenario) {
        case Scenario::Bear: return "BEAR";
        case Scenario::Base: return "BASE";
        case Scenario::Bull: return "BULL";
    }

    return "UNKNOWN";
}

void printDCF(const string& name, const DCFResult& result) {
    cout << "\n" << string(72, '=') << "\n";
    cout << name << " CASE DCF VALUATION\n";
    cout << string(72, '=') << "\n";

    cout << fixed << setprecision(2);

    cout << "WACC:                  " << result.wacc * 100 << "%\n";
    cout << "Explicit value:        " << result.explicitValue << "\n";
    cout << "Terminal value:        " << result.terminalValue << "\n";
    cout << "Terminal present value:" << result.terminalPresentValue << "\n";
    cout << "Enterprise value:      " << result.enterpriseValue << "\n";
    cout << "Equity value:          " << result.equityValue << "\n";
    cout << "Value per share:       " << result.valuePerShare << "\n";
    cout << "Terminal contribution: "
         << result.terminalContribution * 100 << "%\n";

    cout << "\nForecast cash flows\n";

    for (const auto& year : result.forecast) {
        cout << "Year " << year.year
             << " | Revenue: " << year.revenue
             << " | EBIT: " << year.ebit
             << " | FCFF: " << year.fcff
             << " | PV: " << year.presentValue
             << "\n";
    }
}

int main() {
    try {
        cout << "BUSINESS VALUATION ENGINE\n";
        cout << "Currency: INR millions unless stated otherwise\n";

        FinancialStatements financials{
            1000.0,
            180.0,
            40.0,
            55.0,
            10.0,
            0.25,
            100.0,
            300.0,
            50.0
        };

        CapitalStructure capital{
            0.14,
            0.09,
            0.70,
            0.30
        };

        vector<ScenarioResult> results;

        for (Scenario scenario : {
            Scenario::Bear,
            Scenario::Base,
            Scenario::Bull
        }) {
            ValuationEngine engine(
                financials,
                capital,
                getScenario(scenario)
            );

            DCFResult result = engine.calculate();

            printDCF(scenarioName(scenario), result);

            results.push_back({scenario, result});

            if (scenario == Scenario::Base) {
                cout << "\nDCF SENSITIVITY ANALYSIS\n";

                const auto matrix = engine.sensitivity(
                    {-0.01, 0.0, 0.01},
                    {-0.01, 0.0, 0.01}
                );

                for (const auto& row : matrix) {
                    for (double value : row) {
                        if (isnan(value)) {
                            cout << setw(14) << "INVALID";
                        } else {
                            cout << setw(14) << value;
                        }
                    }
                    cout << "\n";
                }
            }
        }

        vector<ComparableCompany> companies{
            {"Alpha Technologies", 1800, 1200, 240, 140},
            {"Beta Systems", 2100, 1500, 300, 175},
            {"Gamma Digital", 1650, 1100, 220, 125},
            {"Delta Software", 2400, 1600, 320, 190}
        };

        ComparableValuator comparableValuator(companies);

        const auto multiples =
            comparableValuator.calculateMultiples();

        cout << "\n" << string(72, '=') << "\n";
        cout << "COMPARABLE COMPANY ANALYSIS\n";
        cout << string(72, '=') << "\n";

        for (const auto& company : companies) {
            cout << company.name
                 << " | EV/Revenue: " << company.evRevenue()
                 << " | EV/EBITDA: " << company.evEbitda()
                 << " | P/E: " << company.peRatio()
                 << "\n";
        }

        for (const auto& [name, value] : multiples) {
            cout << "Median " << name << ": "
                 << value << "x\n";
        }

        const auto target =
            comparableValuator.valueTarget(
                1000,
                220,
                120,
                100,
                300,
                50
            );

        cout << "\nTARGET COMPANY VALUATION\n";

        for (const auto& [name, value] : target) {
            cout << left << setw(24) << name
                 << right << value << "\n";
        }

        // Verify the enterprise-to-equity reconciliation.
        const DCFResult& base = results[1].result;

        assert(base.enterpriseValue > 0);
        assert(base.forecast.size() == 5);

        assert(abs(
            base.equityValue -
            (base.enterpriseValue + financials.cash - financials.debt)
        ) < 1e-8);

        cout << "\nAll valuation integrity checks passed.\n";

        return 0;
    }
    catch (const exception& error) {
        cerr << "Valuation error: " << error.what() << "\n";
        return 1;
    }
}
