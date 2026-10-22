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

struct Metric {
    std::string name;
    double current;
    double previous;
    double target;
    std::string unit;

    double change() const {
        return current - previous;
    }

    double changePercent() const {
        if (previous == 0.0) {
            if (current == 0.0) return 0.0;
            return std::numeric_limits<double>::infinity();
        }
        return (change() / previous) * 100.0;
    }

    double targetGap() const {
        return current - target;
    }
};

enum class Priority {
    Critical,
    High,
    Medium,
    Low
};

struct Insight {
    std::string metric;
    Priority priority;
    std::string observation;
    std::string implication;
    std::string action;
};

class GovernanceStoryEngine {
private:
    std::vector<Metric> metrics_;

    static int priorityRank(Priority priority) {
        switch (priority) {
            case Priority::Critical: return 0;
            case Priority::High: return 1;
            case Priority::Medium: return 2;
            case Priority::Low: return 3;
        }
        return 4;
    }

    static std::string priorityName(Priority priority) {
        switch (priority) {
            case Priority::Critical: return "CRITICAL";
            case Priority::High: return "HIGH";
            case Priority::Medium: return "MEDIUM";
            case Priority::Low: return "LOW";
        }
        return "UNKNOWN";
    }

    static Priority classify(double changePercent) {
        if (changePercent <= -10.0) return Priority::Critical;
        if (changePercent < -3.0) return Priority::High;
        if (changePercent >= 10.0) return Priority::High;
        if (changePercent >= 3.0) return Priority::Medium;
        return Priority::Low;
    }

    static void validateMetric(const Metric& metric) {
        if (metric.name.empty()) {
            throw std::invalid_argument("Metric name cannot be empty.");
        }

        if (!std::isfinite(metric.current) ||
            !std::isfinite(metric.previous) ||
            !std::isfinite(metric.target)) {
            throw std::invalid_argument(
                "Metric values must be finite."
            );
        }
    }

    static Insight buildInsight(const Metric& metric) {
        const double change = metric.changePercent();
        const Priority priority = classify(change);

        std::string implication;
        std::string action;

        if (change <= -10.0) {
            implication =
                metric.name +
                " has materially deteriorated and represents a decision risk.";
            action =
                "Segment the decline, identify the largest driver, assign ownership, "
                "and establish a corrective measurement.";
        } else if (change < -3.0) {
            implication =
                metric.name +
                " is deteriorating enough to require targeted investigation.";
            action =
                "Break the metric into meaningful business dimensions before "
                "choosing an intervention.";
        } else if (change >= 10.0) {
            implication =
                metric.name +
                " is improving strongly and may represent a scalable opportunity.";
            action =
                "Identify the causal operating behavior and test whether it can "
                "be replicated without degrading other metrics.";
        } else if (change >= 3.0) {
            implication =
                metric.name +
                " is improving, but persistence and target attainment should be checked.";
            action =
                "Monitor the movement across segments and validate whether the "
                "improvement remains consistent.";
        } else {
            implication =
                metric.name +
                " is relatively stable and provides a weaker immediate decision signal.";
            action =
                "Continue monitoring while prioritizing metrics with greater "
                "movement or business consequence.";
        }

        std::ostringstream observation;
        observation << metric.name
                    << " changed from "
                    << metric.previous << metric.unit
                    << " to "
                    << metric.current << metric.unit
                    << ".";

        return {
            metric.name,
            priority,
            observation.str(),
            implication,
            action
        };
    }

public:
    explicit GovernanceStoryEngine(std::vector<Metric> metrics)
        : metrics_(std::move(metrics)) {
        if (metrics_.empty()) {
            throw std::invalid_argument("At least one metric is required.");
        }

        std::map<std::string, bool> seen;

        for (const auto& metric : metrics_) {
            validateMetric(metric);

            if (seen.contains(metric.name)) {
                throw std::invalid_argument(
                    "Duplicate metric: " + metric.name
                );
            }

            seen[metric.name] = true;
        }
    }

    std::vector<Insight> createInsights() const {
        std::vector<Insight> insights;

        for (const auto& metric : metrics_) {
            insights.push_back(buildInsight(metric));
        }

        std::sort(
            insights.begin(),
            insights.end(),
            [](const Insight& left, const Insight& right) {
                return priorityRank(left.priority) <
                       priorityRank(right.priority);
            }
        );

        return insights;
    }

    void printExecutiveStory() const {
        const auto insights = createInsights();

        const auto& lead = insights.front();

        const int improved = static_cast<int>(
            std::count_if(
                metrics_.begin(),
                metrics_.end(),
                [](const Metric& metric) {
                    return metric.change() > 0.0;
                }
            )
        );

        const int declined = static_cast<int>(
            std::count_if(
                metrics_.begin(),
                metrics_.end(),
                [](const Metric& metric) {
                    return metric.change() < 0.0;
                }
            )
        );

        std::cout << "BUSINESS STORY\n";
        std::cout << "==============\n";
        std::cout << "Headline: " << lead.observation << '\n';
        std::cout << "Why it matters: " << lead.implication << '\n';
        std::cout << "Action: " << lead.action << '\n';
        std::cout << "Portfolio signal: "
                  << improved << " improved, "
                  << declined << " declined, "
                  << static_cast<int>(metrics_.size()) - improved - declined
                  << " stable.\n\n";

        std::cout << "DECISION SIGNALS\n";
        std::cout << "================\n";

        std::cout << std::fixed << std::setprecision(2);

        for (const auto& insight : insights) {
            const auto metricIt = std::find_if(
                metrics_.begin(),
                metrics_.end(),
                [&insight](const Metric& metric) {
                    return metric.name == insight.metric;
                }
            );

            std::cout << '[' << priorityName(insight.priority) << "] "
                      << insight.metric
                      << " | change "
                      << metricIt->changePercent()
                      << "% | target gap "
                      << metricIt->targetGap()
                      << '\n';

            std::cout << "Observation: "
                      << insight.observation << '\n';
            std::cout << "Implication: "
                      << insight.implication << '\n';
            std::cout << "Action: "
                      << insight.action << "\n\n";
        }
    }
};

int main() {
    try {
        std::vector<Metric> metrics{
            {"Revenue", 12.4, 10.8, 12.0, "M"},
            {"Conversion Rate", 4.7, 5.3, 5.0, "%"},
            {"Customer Retention", 91.0, 88.0, 90.0, "%"},
            {"Support Cost", 1.9, 1.6, 1.7, "M"},
            {"Gross Margin", 37.5, 35.8, 36.0, "%"}
        };

        GovernanceStoryEngine engine(std::move(metrics));
        engine.printExecutiveStory();
    } catch (const std::exception& exception) {
        std::cerr << "Unable to generate business story: "
                  << exception.what() << '\n';
        return 1;
    }

    return 0;
}
