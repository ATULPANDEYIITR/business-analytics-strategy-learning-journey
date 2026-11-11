#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class Category {
    Profitability,
    Liquidity,
    Leverage,
    Efficiency
};

string categoryName(Category category) {
    switch (category) {
        case Category::Profitability: return "Profitability";
        case Category::Liquidity: return "Liquidity";
        case Category::Leverage: return "Leverage";
        case Category::Efficiency: return "Efficiency";
    }
    throw logic_error("Unknown ratio category.");
}

struct FinancialStatements {
    string company;
    string period;

    double revenue;
    double costOfGoodsSold;
    double operatingExpenses;
    double operatingIncome;
    double netIncome;

    double totalAssets;
    double currentAssets;
    double inventory;
    double cash;
    double accountsReceivable;

    double totalLiabilities;
    double currentLiabilities;
    double totalDebt;
    double shareholdersEquity;

    double interestExpense;
    double inventoryBeginning;
    double inventoryEnding;
    double receivablesBeginning;
    double receivablesEnding;
};

struct Ratio {
    string name;
    Category category;
    optional<double> value;
    string unit;
    string interpretation;
};

class FinancialDataValidator {
public:
    static void validate(const FinancialStatements& d) {
        if (d.company.empty() || d.period.empty()) {
            throw invalid_argument(
                "Company and financial period are required."
            );
        }

        const vector<pair<string, double>> fields = {
            {"revenue", d.revenue},
            {"costOfGoodsSold", d.costOfGoodsSold},
            {"operatingExpenses", d.operatingExpenses},
            {"operatingIncome", d.operatingIncome},
            {"netIncome", d.netIncome},
            {"totalAssets", d.totalAssets},
            {"currentAssets", d.currentAssets},
            {"inventory", d.inventory},
            {"cash", d.cash},
            {"accountsReceivable", d.accountsReceivable},
            {"totalLiabilities", d.totalLiabilities},
            {"currentLiabilities", d.currentLiabilities},
            {"totalDebt", d.totalDebt},
            {"shareholdersEquity", d.shareholdersEquity},
            {"interestExpense", d.interestExpense},
            {"inventoryBeginning", d.inventoryBeginning},
            {"inventoryEnding", d.inventoryEnding},
            {"receivablesBeginning", d.receivablesBeginning},
            {"receivablesEnding", d.receivablesEnding}
        };

        for (const auto& [name, value] : fields) {
            if (!isfinite(value) || value < 0) {
                throw invalid_argument(
                    "Invalid financial value: " + name
                );
            }
        }

        if (d.currentAssets > d.totalAssets ||
            d.cash > d.currentAssets ||
            d.inventory > d.currentAssets ||
            d.currentLiabilities > d.totalLiabilities ||
            d.totalDebt > d.totalLiabilities) {
            throw invalid_argument(
                "Financial statement consistency validation failed."
            );
        }
    }
};

class RatioEngine {
private:
    const FinancialStatements& data;
    vector<Ratio> ratios;

    static optional<double> divide(
        double numerator,
        double denominator
    ) {
        if (denominator == 0.0) {
            return nullopt;
        }

        return numerator / denominator;
    }

    void add(
        string name,
        Category category,
        double numerator,
        double denominator,
        string unit,
        string interpretation
    ) {
        ratios.push_back({
            move(name),
            category,
            divide(numerator, denominator),
            move(unit),
            move(interpretation)
        });
    }

public:
    explicit RatioEngine(const FinancialStatements& statements)
        : data(statements) {
        FinancialDataValidator::validate(data);
    }

    void calculateProfitability() {
        double grossProfit =
            data.revenue - data.costOfGoodsSold;

        add(
            "Gross Profit Margin",
            Category::Profitability,
            grossProfit,
            data.revenue,
            "%",
            "Gross profit relative to revenue."
        );

        add(
            "Operating Profit Margin",
            Category::Profitability,
            data.operatingIncome,
            data.revenue,
            "%",
            "Operating profitability."
        );

        add(
            "Net Profit Margin",
            Category::Profitability,
            data.netIncome,
            data.revenue,
            "%",
            "Net profitability."
        );

        add(
            "Return on Assets",
            Category::Profitability,
            data.netIncome,
            data.totalAssets,
            "%",
            "Profit relative to assets."
        );

        add(
            "Return on Equity",
            Category::Profitability,
            data.netIncome,
            data.shareholdersEquity,
            "%",
            "Profit relative to shareholders' equity."
        );
    }

    void calculateLiquidity() {
        add(
            "Current Ratio",
            Category::Liquidity,
            data.currentAssets,
            data.currentLiabilities,
            "x",
            "Current asset coverage."
        );

        add(
            "Quick Ratio",
            Category::Liquidity,
            data.currentAssets - data.inventory,
            data.currentLiabilities,
            "x",
            "Liquid asset coverage excluding inventory."
        );

        add(
            "Cash Ratio",
            Category::Liquidity,
            data.cash,
            data.currentLiabilities,
            "x",
            "Immediate cash coverage."
        );
    }

    void calculateLeverage() {
        add(
            "Debt-to-Equity Ratio",
            Category::Leverage,
            data.totalDebt,
            data.shareholdersEquity,
            "x",
            "Debt financing relative to equity."
        );

        add(
            "Debt-to-Assets Ratio",
            Category::Leverage,
            data.totalDebt,
            data.totalAssets,
            "%",
            "Assets financed through debt."
        );

        add(
            "Debt Ratio",
            Category::Leverage,
            data.totalLiabilities,
            data.totalAssets,
            "%",
            "Assets financed through liabilities."
        );

        add(
            "Interest Coverage Ratio",
            Category::Leverage,
            data.operatingIncome,
            data.interestExpense,
            "x",
            "Operating income available for interest."
        );
    }

    void calculateEfficiency() {
        double averageInventory =
            (data.inventoryBeginning + data.inventoryEnding) / 2.0;

        double averageReceivables =
            (data.receivablesBeginning + data.receivablesEnding) / 2.0;

        add(
            "Inventory Turnover",
            Category::Efficiency,
            data.costOfGoodsSold,
            averageInventory,
            "x",
            "Inventory replacement frequency."
        );

        add(
            "Receivables Turnover",
            Category::Efficiency,
            data.revenue,
            averageReceivables,
            "x",
            "Receivables collection efficiency."
        );

        add(
            "Total Asset Turnover",
            Category::Efficiency,
            data.revenue,
            data.totalAssets,
            "x",
            "Revenue generated per unit of assets."
        );

        add(
            "Days Sales Outstanding",
            Category::Efficiency,
            averageReceivables * 365,
            data.revenue,
            "days",
            "Estimated receivables collection period."
        );

        add(
            "Days Inventory Outstanding",
            Category::Efficiency,
            averageInventory * 365,
            data.costOfGoodsSold,
            "days",
            "Estimated inventory holding period."
        );
    }

    void analyze() {
        ratios.clear();

        calculateProfitability();
        calculateLiquidity();
        calculateLeverage();
        calculateEfficiency();
    }

    const vector<Ratio>& getRatios() const {
        return ratios;
    }

    void display() const {
        cout << "\nFINANCIAL RATIO ANALYSIS\n";
        cout << string(85, '=') << '\n';
        cout << "Company: " << data.company << '\n';
        cout << "Period:  " << data.period << '\n';

        for (Category category : {
            Category::Profitability,
            Category::Liquidity,
            Category::Leverage,
            Category::Efficiency
        }) {
            cout << "\n" << categoryName(category) << '\n';
            cout << string(85, '-') << '\n';

            for (const auto& ratio : ratios) {
                if (ratio.category != category) {
                    continue;
                }

                cout << left << setw(30) << ratio.name;

                if (ratio.value.has_value()) {
                    cout << fixed << setprecision(4)
                         << *ratio.value << " "
                         << ratio.unit;
                } else {
                    cout << "N/A (undefined denominator)";
                }

                cout << '\n';
                cout << "  " << ratio.interpretation << '\n';
            }
        }
    }

    map<string, size_t> categoryCounts() const {
        map<string, size_t> counts;

        for (const auto& ratio : ratios) {
            counts[categoryName(ratio.category)]++;
        }

        return counts;
    }
};

FinancialStatements createSample() {
    return {
        "Apex Manufacturing Ltd.",
        "FY2025-26",

        12000000,
        7200000,
        2400000,
        2400000,
        1500000,

        10000000,
        4000000,
        1200000,
        800000,
        1000000,

        5000000,
        2000000,
        3000000,
        5000000,

        400000,
        1000000,
        1200000,
        800000,
        1000000
    };
}

void runTests() {
    auto data = createSample();
    RatioEngine engine(data);

    engine.analyze();

    if (engine.getRatios().size() != 17) {
        throw runtime_error("Incorrect ratio count.");
    }

    map<string, double> expected = {
        {"Gross Profit Margin", 0.4},
        {"Current Ratio", 2.0},
        {"Quick Ratio", 1.4},
        {"Debt-to-Equity Ratio", 0.6},
        {"Interest Coverage Ratio", 6.0}
    };

    for (const auto& [name, value] : expected) {
        auto it = find_if(
            engine.getRatios().begin(),
            engine.getRatios().end(),
            [&](const Ratio& r) {
                return r.name == name;
            }
        );

        if (it == engine.getRatios().end() ||
            !it->value.has_value() ||
            abs(*it->value - value) > 1e-9) {
            throw runtime_error(
                "Test failed for " + name
            );
        }
    }

    // Zero denominators must produce undefined values.
    auto zeroData = createSample();
    zeroData.revenue = 0;
    zeroData.operatingIncome = 0;
    zeroData.netIncome = 0;
    zeroData.costOfGoodsSold = 0;

    RatioEngine zeroEngine(zeroData);
    zeroEngine.analyze();

    if (zeroEngine.getRatios().front().value.has_value()) {
        throw runtime_error("Zero denominator test failed.");
    }

    auto invalidData = createSample();
    invalidData.cash = -1;

    try {
        RatioEngine invalidEngine(invalidData);
        throw runtime_error("Negative value was accepted.");
    } catch (const invalid_argument&) {
        // Expected validation failure.
    }

    cout << "All C++17 tests passed.\n";
}

int main() {
    try {
        FinancialStatements data = createSample();

        RatioEngine engine(data);
        engine.analyze();
        engine.display();

        cout << "\nCATEGORY COUNTS\n";

        for (const auto& [category, count] :
             engine.categoryCounts()) {
            cout << category << ": " << count << '\n';
        }

        runTests();

    } catch (const exception& error) {
        cerr << "Financial analysis failed: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
