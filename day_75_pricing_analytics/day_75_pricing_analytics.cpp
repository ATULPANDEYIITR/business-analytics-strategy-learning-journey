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

enum class PricingStrategy {
    CostPlus,
    Competitive,
    ValueBased,
    Dynamic
};

enum class Objective {
    Revenue,
    Profit
};

enum class ReviewStatus {
    Approved,
    Rejected,
    Pending
};

struct Product {
    string id;
    string name;
    double unitCost;
    double referencePrice;
    double minimumPrice;
    double maximumPrice;
    int inventory;
};

struct Segment {
    string name;
    double baseDemand;
    double elasticity;
};

struct Review {
    string reviewer;
    ReviewStatus status;
    string comment;
};

struct PricingPolicy {
    double minimumMargin;
    double maximumDiscount;
    bool requireApproval;
    int requiredApprovals;
};

struct PriceMetrics {
    double price = 0;
    double demand = 0;
    double revenue = 0;
    double cost = 0;
    double profit = 0;
    double margin = 0;
};

struct Recommendation {
    PriceMetrics metrics;
    Objective objective;
    bool eligible = false;
    vector<string> violations;
};

class PricingException : public runtime_error {
public:
    explicit PricingException(const string& message)
        : runtime_error(message) {}
};

class DemandForecaster {
private:
    double basePrice;
    vector<Segment> segments;

public:
    DemandForecaster(double referencePrice,
                     vector<Segment> customerSegments)
        : basePrice(referencePrice),
          segments(move(customerSegments)) {

        if (basePrice <= 0 || segments.empty()) {
            throw PricingException("Invalid demand model.");
        }

        for (const auto& segment : segments) {
            if (segment.baseDemand < 0 ||
                segment.elasticity >= 0 ||
                !isfinite(segment.elasticity)) {
                throw PricingException("Invalid segment parameters.");
            }
        }
    }

    double forecast(double price) const {
        if (price <= 0) {
            throw PricingException("Price must be positive.");
        }

        double totalDemand = 0;

        for (const auto& segment : segments) {
            totalDemand += segment.baseDemand *
                pow(price / basePrice, segment.elasticity);
        }

        return totalDemand;
    }
};

class PricingAnalytics {
private:
    Product product;
    DemandForecaster forecaster;
    PricingPolicy policy;
    vector<Review> reviews;

public:
    PricingAnalytics(Product p,
                     DemandForecaster f,
                     PricingPolicy pol)
        : product(move(p)),
          forecaster(move(f)),
          policy(pol) {

        if (product.id.empty() ||
            product.unitCost < 0 ||
            product.referencePrice <= 0 ||
            product.minimumPrice <= product.unitCost ||
            product.maximumPrice < product.minimumPrice ||
            product.inventory < 0) {
            throw PricingException("Invalid product configuration.");
        }

        if (policy.minimumMargin < 0 ||
            policy.minimumMargin >= 1 ||
            policy.maximumDiscount < 0 ||
            policy.maximumDiscount >= 1 ||
            policy.requiredApprovals < 0) {
            throw PricingException("Invalid pricing policy.");
        }
    }

    void addReview(const Review& review) {
        if (review.reviewer.empty()) {
            throw PricingException("Reviewer identity is required.");
        }

        auto duplicate = find_if(
            reviews.begin(),
            reviews.end(),
            [&](const Review& existing) {
                return existing.reviewer == review.reviewer;
            }
        );

        if (duplicate != reviews.end()) {
            throw PricingException("Duplicate reviewer.");
        }

        reviews.push_back(review);
    }

    PriceMetrics evaluate(double price) const {
        if (price < product.minimumPrice ||
            price > product.maximumPrice) {
            throw PricingException("Price outside allowed boundaries.");
        }

        double demand = min(
            forecaster.forecast(price),
            static_cast<double>(product.inventory)
        );

        PriceMetrics result;

        result.price = price;
        result.demand = demand;
        result.revenue = price * demand;
        result.cost = product.unitCost * demand;
        result.profit = result.revenue - result.cost;
        result.margin = result.revenue > 0
            ? result.profit / result.revenue
            : 0;

        return result;
    }

    vector<string> validate(const PriceMetrics& metrics) const {
        vector<string> violations;

        double minimumPermittedPrice =
            product.referencePrice *
            (1.0 - policy.maximumDiscount);

        if (metrics.price < minimumPermittedPrice) {
            violations.push_back("Maximum discount exceeded.");
        }

        if (metrics.margin < policy.minimumMargin) {
            violations.push_back("Minimum margin not achieved.");
        }

        if (metrics.demand > product.inventory) {
            violations.push_back("Inventory capacity exceeded.");
        }

        return violations;
    }

    bool approvalsSatisfied() const {
        int approved = 0;

        for (const auto& review : reviews) {
            if (review.status == ReviewStatus::Approved) {
                ++approved;
            }
        }

        return approved >= policy.requiredApprovals;
    }

    Recommendation optimize(
        Objective objective,
        double step
    ) const {

        if (step <= 0 || !isfinite(step)) {
            throw PricingException("Invalid optimization step.");
        }

        optional<Recommendation> best;

        for (double price = product.minimumPrice;
             price <= product.maximumPrice + 1e-9;
             price += step) {

            PriceMetrics metrics = evaluate(price);
            vector<string> violations = validate(metrics);

            bool eligible = violations.empty();

            if (policy.requireApproval && !approvalsSatisfied()) {
                eligible = false;
                violations.push_back("Approval requirements not satisfied.");
            }

            if (!eligible) {
                continue;
            }

            Recommendation candidate{
                metrics,
                objective,
                true,
                violations
            };

            double score = objective == Objective::Profit
                ? metrics.profit
                : metrics.revenue;

            if (!best) {
                best = candidate;
                continue;
            }

            double previousScore =
                objective == Objective::Profit
                    ? best->metrics.profit
                    : best->metrics.revenue;

            if (score > previousScore ||
                (score == previousScore &&
                 metrics.price > best->metrics.price)) {
                best = candidate;
            }
        }

        if (!best) {
            throw PricingException(
                "No candidate satisfies pricing governance."
            );
        }

        return *best;
    }

    void printReport(const Recommendation& recommendation) const {
        const auto& m = recommendation.metrics;

        cout << fixed << setprecision(2);
        cout << "\nPRICING RECOMMENDATION\n";
        cout << "------------------------------\n";
        cout << "Product: " << product.name << '\n';
        cout << "Recommended price: " << m.price << '\n';
        cout << "Expected demand: " << m.demand << '\n';
        cout << "Expected revenue: " << m.revenue << '\n';
        cout << "Expected variable cost: " << m.cost << '\n';
        cout << "Expected contribution: " << m.profit << '\n';
        cout << "Contribution margin: " << m.margin * 100 << "%\n";
        cout << "Governance eligible: "
             << (recommendation.eligible ? "YES" : "NO") << '\n';
    }
};

double estimateElasticity(
    const vector<pair<double, double>>& observations
) {
    vector<pair<double, double>> transformed;

    for (const auto& observation : observations) {
        if (observation.first > 0 && observation.second > 0) {
            transformed.emplace_back(
                log(observation.first),
                log(observation.second)
            );
        }
    }

    if (transformed.size() < 3) {
        throw PricingException("Insufficient observations.");
    }

    double meanX = 0;
    double meanY = 0;

    for (const auto& item : transformed) {
        meanX += item.first;
        meanY += item.second;
    }

    meanX /= transformed.size();
    meanY /= transformed.size();

    double numerator = 0;
    double denominator = 0;

    for (const auto& item : transformed) {
        numerator +=
            (item.first - meanX) * (item.second - meanY);

        denominator +=
            pow(item.first - meanX, 2);
    }

    if (denominator < 1e-12) {
        throw PricingException("Insufficient price variation.");
    }

    double elasticity = numerator / denominator;

    if (elasticity >= 0) {
        throw PricingException("Unexpected positive demand elasticity.");
    }

    return elasticity;
}

int main() {
    try {
        Product product{
            "PRD-101",
            "Enterprise Data Platform",
            220.0,
            500.0,
            300.0,
            900.0,
            1000
        };

        vector<Segment> segments{
            {"SMB", 75.0, -1.5},
            {"Corporate", 45.0, -0.9},
            {"Enterprise", 25.0, -0.6}
        };

        DemandForecaster forecaster(
            product.referencePrice,
            segments
        );

        PricingPolicy policy{
            0.20,
            0.40,
            true,
            2
        };

        PricingAnalytics engine(
            product,
            forecaster,
            policy
        );

        vector<pair<double, double>> historicalData{
            {400, 150},
            {450, 133},
            {500, 115},
            {550, 105},
            {600, 94},
            {650, 86},
            {700, 80}
        };

        double elasticity = estimateElasticity(historicalData);

        cout << fixed << setprecision(4);
        cout << "Estimated elasticity: "
             << elasticity << "\n";

        engine.addReview({
            "Pricing Manager",
            ReviewStatus::Approved,
            "Contribution margin reviewed."
        });

        engine.addReview({
            "Commercial Director",
            ReviewStatus::Approved,
            "Commercial feasibility reviewed."
        });

        Recommendation profit = engine.optimize(
            Objective::Profit,
            5.0
        );

        Recommendation revenue = engine.optimize(
            Objective::Revenue,
            5.0
        );

        engine.printReport(profit);

        cout << "\nREVENUE OPTIMIZATION\n";
        engine.printReport(revenue);

        // An unapproved price must not pass governance.
        PricingPolicy restrictivePolicy{
            0.20,
            0.40,
            true,
            3
        };

        PricingAnalytics restrictedEngine(
            product,
            forecaster,
            restrictivePolicy
        );

        restrictedEngine.addReview({
            "Pricing Manager",
            ReviewStatus::Approved,
            "Initial approval."
        });

        bool blocked = false;

        try {
            restrictedEngine.optimize(
                Objective::Profit,
                5.0
            );
        } catch (const PricingException&) {
            blocked = true;
        }

        if (!blocked) {
            throw PricingException(
                "Approval control test failed."
            );
        }

        // Verify the resulting price and inventory boundaries.
        if (profit.metrics.price < product.minimumPrice ||
            profit.metrics.price > product.maximumPrice ||
            profit.metrics.demand > product.inventory) {
            throw PricingException("Optimization validation failed.");
        }

        cout << "\nAll governance and pricing tests passed.\n";

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
