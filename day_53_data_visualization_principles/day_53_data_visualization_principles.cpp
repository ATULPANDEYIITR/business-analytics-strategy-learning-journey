#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using namespace std;

enum class AnalyticalIntent {
    Comparison,
    Relationship,
    Distribution,
    Composition,
    Trend,
    Matrix
};

enum class ChartType {
    HorizontalBar,
    DotPlot,
    ScatterPlot,
    Histogram,
    BoxPlot,
    StackedBar,
    Pie,
    Line,
    Heatmap
};

struct DataSet {
    vector<string> categories;
    vector<double> values;
    vector<double> x;
    vector<double> y;
    vector<vector<double>> matrix;
    bool ordered = false;
};

struct Recommendation {
    ChartType chart;
    double score;
    string rationale;
    vector<string> warnings;
};

class VisualizationException : public runtime_error {
public:
    explicit VisualizationException(const string& message)
        : runtime_error(message) {}
};

static string chartName(ChartType chart) {
    switch (chart) {
        case ChartType::HorizontalBar: return "Horizontal bar chart";
        case ChartType::DotPlot: return "Dot plot";
        case ChartType::ScatterPlot: return "Scatter plot";
        case ChartType::Histogram: return "Histogram";
        case ChartType::BoxPlot: return "Box plot";
        case ChartType::StackedBar: return "100% stacked bar chart";
        case ChartType::Pie: return "Pie chart";
        case ChartType::Line: return "Line chart";
        case ChartType::Heatmap: return "Heatmap";
    }
    return "Unknown";
}

class RepositoryLikeAuditTrail {
    /*
     * The governance analogy is intentionally avoided here: visualization
     * selection is treated as a data-quality and analytical-intent decision.
     * This audit object records why a chart was selected so decisions remain
     * inspectable rather than becoming opaque UI behavior.
     */
public:
    void record(const Recommendation& recommendation) {
        records.push_back(recommendation);
    }

    void print() const {
        cout << "\nDecision audit\n";
        for (const auto& record : records) {
            cout << "  " << chartName(record.chart)
                 << " score=" << fixed << setprecision(2)
                 << record.score << "\n";
            cout << "    " << record.rationale << "\n";
            for (const auto& warning : record.warnings) {
                cout << "    warning: " << warning << "\n";
            }
        }
    }

private:
    vector<Recommendation> records;
};

class VisualizationEngine {
public:
    vector<Recommendation> recommend(
        AnalyticalIntent intent,
        const DataSet& data
    ) const {
        validate(intent, data);

        switch (intent) {
            case AnalyticalIntent::Comparison:
                return comparison(data);
            case AnalyticalIntent::Relationship:
                return relationship(data);
            case AnalyticalIntent::Distribution:
                return distribution(data);
            case AnalyticalIntent::Composition:
                return composition(data);
            case AnalyticalIntent::Trend:
                return trend(data);
            case AnalyticalIntent::Matrix:
                return matrix(data);
        }

        throw VisualizationException("Unsupported analytical intent.");
    }

private:
    static void validateNumbers(
        const vector<double>& values,
        const string& name
    ) {
        if (values.empty()) {
            throw VisualizationException(name + " cannot be empty.");
        }

        for (double value : values) {
            if (!isfinite(value)) {
                throw VisualizationException(
                    name + " contains a non-finite value."
                );
            }
        }
    }

    static void validate(
        AnalyticalIntent intent,
        const DataSet& data
    ) {
        switch (intent) {
            case AnalyticalIntent::Comparison:
            case AnalyticalIntent::Composition:
                if (data.categories.empty() ||
                    data.categories.size() != data.values.size()) {
                    throw VisualizationException(
                        "Categorical comparison requires equal category/value arrays."
                    );
                }
                validateNumbers(data.values, "values");
                break;

            case AnalyticalIntent::Relationship:
                if (data.x.empty() || data.x.size() != data.y.size()) {
                    throw VisualizationException(
                        "Relationship analysis requires equally sized x/y arrays."
                    );
                }
                validateNumbers(data.x, "x");
                validateNumbers(data.y, "y");
                break;

            case AnalyticalIntent::Distribution:
            case AnalyticalIntent::Trend:
                validateNumbers(data.values, "values");
                break;

            case AnalyticalIntent::Matrix:
                if (data.matrix.empty() || data.matrix.front().empty()) {
                    throw VisualizationException(
                        "Matrix must contain at least one non-empty row."
                    );
                }

                {
                    const size_t width = data.matrix.front().size();
                    for (const auto& row : data.matrix) {
                        if (row.size() != width) {
                            throw VisualizationException(
                                "Matrix rows must have equal widths."
                            );
                        }
                        validateNumbers(row, "matrix row");
                    }
                }
                break;
        }
    }

    static vector<Recommendation> comparison(const DataSet& data) {
        const size_t categoryCount =
            set<string>(data.categories.begin(), data.categories.end()).size();

        vector<Recommendation> results;

        results.push_back({
            ChartType::HorizontalBar,
            categoryCount > 20 ? 0.80 : 0.96,
            "A shared quantitative axis makes category magnitudes directly comparable.",
            categoryCount > 20
                ? vector<string>{"Many categories should be filtered or grouped."}
                : vector<string>{"Sort categories when the analytical goal is ranking."}
        });

        results.push_back({
            ChartType::DotPlot,
            0.91,
            "A position encoding provides precise comparison with less visual mass than bars.",
            {"Direct labels may be appropriate for a small number of categories."}
        });

        return results;
    }

    static double correlation(
        const vector<double>& x,
        const vector<double>& y
    ) {
        const double meanX =
            accumulate(x.begin(), x.end(), 0.0) / x.size();
        const double meanY =
            accumulate(y.begin(), y.end(), 0.0) / y.size();

        double numerator = 0.0;
        double xx = 0.0;
        double yy = 0.0;

        for (size_t i = 0; i < x.size(); ++i) {
            const double dx = x[i] - meanX;
            const double dy = y[i] - meanY;
            numerator += dx * dy;
            xx += dx * dx;
            yy += dy * dy;
        }

        const double denominator = sqrt(xx * yy);
        return denominator == 0.0 ? 0.0 : numerator / denominator;
    }

    static vector<Recommendation> relationship(const DataSet& data) {
        const double r = correlation(data.x, data.y);

        return {{
            ChartType::ScatterPlot,
            0.98,
            "Every observation remains visible, making association, clusters, and outliers inspectable. Pearson r=" +
                to_string(r),
            {
                "Correlation does not establish causation.",
                "Very dense data may require aggregation or transparency."
            }
        }};
    }

    static vector<Recommendation> distribution(const DataSet&) {
        return {
            {
                ChartType::Histogram,
                0.97,
                "Binning reveals concentration, spread, skewness, and possible outliers.",
                {"Bin width can materially change the apparent distribution."}
            },
            {
                ChartType::BoxPlot,
                0.93,
                "Quartiles and extreme observations provide a compact distribution summary.",
                {"A box plot hides some multimodal shape."}
            }
        };
    }

    static vector<Recommendation> composition(const DataSet& data) {
        const double total =
            accumulate(data.values.begin(), data.values.end(), 0.0);
        const bool invalid =
            total <= 0.0 ||
            any_of(
                data.values.begin(),
                data.values.end(),
                [](double value) { return value < 0.0; }
            );

        return {
            {
                ChartType::StackedBar,
                invalid ? 0.20 : 0.95,
                "A common baseline supports comparison of component proportions.",
                invalid
                    ? vector<string>{
                        "Composition values must be non-negative with a positive total."
                    }
                    : vector<string>{
                        "Limit component count so labels remain readable."
                    }
            },
            {
                ChartType::Pie,
                (!invalid && data.categories.size() <= 5) ? 0.60 : 0.25,
                "Pie slices can communicate broad part-to-whole structure when categories are few.",
                {
                    "Avoid many slices.",
                    "Use a bar-based structure when precise comparisons matter."
                }
            }
        };
    }

    static vector<Recommendation> trend(const DataSet&) {
        return {{
            ChartType::Line,
            0.98,
            "Connected positions emphasize ordered change and turning points.",
            {"Only connect observations when the ordering represents meaningful continuity."}
        }};
    }

    static vector<Recommendation> matrix(const DataSet&) {
        return {{
            ChartType::Heatmap,
            0.97,
            "Color intensity provides a compact encoding for a two-dimensional value matrix.",
            {
                "Use an ordered perceptual scale.",
                "Annotate cells when exact values are required."
            }
        }};
    }
};

static void printRecommendations(
    const vector<Recommendation>& recommendations
) {
    vector<Recommendation> ordered = recommendations;

    sort(
        ordered.begin(),
        ordered.end(),
        [](const Recommendation& a, const Recommendation& b) {
            return a.score > b.score;
        }
    );

    for (const auto& item : ordered) {
        cout << "  " << chartName(item.chart)
             << " | score=" << fixed << setprecision(2)
             << item.score << "\n";
        cout << "    " << item.rationale << "\n";

        for (const auto& warning : item.warnings) {
            cout << "    warning: " << warning << "\n";
        }
    }
}

int main() {
    try {
        VisualizationEngine engine;
        RepositoryLikeAuditTrail audit;

        DataSet serviceDemand{
            {"Cloud", "Security", "Data", "Networking", "Applications"},
            {1840, 1320, 1610, 940, 2110},
            {},
            {},
            {},
            false
        };

        cout << "SERVICE DEMAND COMPARISON\n";
        auto comparison =
            engine.recommend(AnalyticalIntent::Comparison, serviceDemand);
        printRecommendations(comparison);
        for (const auto& item : comparison) {
            audit.record(item);
        }

        DataSet incidentAnalysis;
        incidentAnalysis.x = {12, 18, 21, 27, 30, 35, 41, 48};
        incidentAnalysis.y = {17, 15, 14, 12, 11, 9, 8, 6};

        cout << "\nRESPONSE TIME AND INCIDENT COUNT\n";
        auto relationship =
            engine.recommend(AnalyticalIntent::Relationship, incidentAnalysis);
        printRecommendations(relationship);
        for (const auto& item : relationship) {
            audit.record(item);
        }

        DataSet monthlyDemand;
        monthlyDemand.values =
            {82, 91, 88, 105, 113, 121, 117, 129, 138, 145, 141, 154};

        cout << "\nMONTHLY DEMAND\n";
        auto trend =
            engine.recommend(AnalyticalIntent::Trend, monthlyDemand);
        printRecommendations(trend);

        DataSet allocation{
            {"Product", "Support", "Operations", "Other"},
            {52, 21, 17, 10},
            {},
            {},
            {},
            false
        };

        cout << "\nRESOURCE COMPOSITION\n";
        auto composition =
            engine.recommend(AnalyticalIntent::Composition, allocation);
        printRecommendations(composition);

        DataSet performanceMatrix;
        performanceMatrix.matrix = {
            {92, 84, 76},
            {71, 88, 94},
            {63, 79, 91},
            {55, 68, 83}
        };

        cout << "\nPERFORMANCE MATRIX\n";
        auto heatmap =
            engine.recommend(AnalyticalIntent::Matrix, performanceMatrix);
        printRecommendations(heatmap);

        cout << "\nAUDIT TRAIL\n";
        audit.print();

        // Failure case: negative values are not valid parts of a whole.
        DataSet invalidComposition{
            {"A", "B", "C"},
            {40, -10, 70},
            {},
            {},
            {},
            false
        };

        auto invalid =
            engine.recommend(
                AnalyticalIntent::Composition,
                invalidComposition
            );

        cout << "\nINVALID COMPOSITION CHECK\n";
        printRecommendations(invalid);

        return 0;
    }
    catch (const VisualizationException& error) {
        cerr << "Visualization validation error: "
             << error.what() << '\n';
        return 1;
    }
    catch (const exception& error) {
        cerr << "Unexpected error: " << error.what() << '\n';
        return 2;
    }
}
