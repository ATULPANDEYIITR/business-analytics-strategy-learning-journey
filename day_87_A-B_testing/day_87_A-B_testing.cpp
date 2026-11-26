#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

// ============================================================
// A/B TESTING: REPOSITORY-INDEPENDENT EXPERIMENT ENGINE
// C++17
// ============================================================

enum class Variant {
    Control,
    Treatment
};

enum class ExperimentStatus {
    Draft,
    Running,
    Completed,
    Stopped
};

struct ExperimentPolicy {
    double allocationRatio = 0.5;
    double alpha = 0.05;
    double power = 0.80;
    double baselineRate = 0.10;
    double minimumDetectableEffect = 0.02;

    void validate() const {
        if (!(allocationRatio > 0 && allocationRatio < 1))
            throw std::invalid_argument("Invalid allocation ratio.");

        if (!(alpha > 0 && alpha < 1))
            throw std::invalid_argument("Invalid significance level.");

        if (!(power > 0 && power < 1))
            throw std::invalid_argument("Invalid statistical power.");

        if (!(baselineRate > 0 && baselineRate < 1))
            throw std::invalid_argument("Invalid baseline rate.");

        if (!(minimumDetectableEffect > 0))
            throw std::invalid_argument("Invalid minimum detectable effect.");

        if (baselineRate + minimumDetectableEffect >= 1)
            throw std::invalid_argument("Treatment rate must be below one.");
    }
};

struct Participant {
    std::string id;
    Variant variant;
    bool hasOutcome = false;
    bool converted = false;
    double revenue = 0.0;
};

struct GroupMetrics {
    std::size_t participants = 0;
    std::size_t conversions = 0;
    double revenue = 0.0;

    double conversionRate() const {
        return participants == 0
            ? 0.0
            : static_cast<double>(conversions) / participants;
    }

    double averageRevenue() const {
        return participants == 0 ? 0.0 : revenue / participants;
    }
};

struct AnalysisResult {
    GroupMetrics control;
    GroupMetrics treatment;
    double absoluteLift = 0.0;
    double relativeLift = 0.0;
    double zScore = 0.0;
    double pValue = 1.0;
    double ciLower = 0.0;
    double ciUpper = 0.0;
    bool statisticallySignificant = false;
    bool practicallySignificant = false;
};

class Statistics {
public:
    static double normalCDF(double x) {
        return 0.5 * std::erfc(-x / std::sqrt(2.0));
    }

    static double inverseNormalCDF(double p) {
        if (!(p > 0 && p < 1))
            throw std::invalid_argument("Probability outside valid range.");

        // Acklam approximation.
        static const double a[] = {
            -39.6968302866538, 220.946098424521,
            -275.928510446969, 138.357751867269,
            -30.6647980661472, 2.50662827745924
        };

        static const double b[] = {
            -54.4760987982241, 161.585836858041,
            -155.698979859887, 66.8013118877197,
            -13.2806815528857
        };

        static const double c[] = {
            -0.00778489400243029, -0.322396458041136,
            -2.40075827716184, -2.54973253934373,
            4.37466414146497, 2.93816398269878
        };

        static const double d[] = {
            0.00778469570904146, 0.32246712907004,
            2.445134137143, 3.75440866190742
        };

        const double low = 0.02425;
        const double high = 1.0 - low;

        if (p < low) {
            double q = std::sqrt(-2.0 * std::log(p));
            return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) /
                   ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0);
        }

        if (p > high) {
            double q = std::sqrt(-2.0 * std::log(1.0-p));
            return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) /
                    ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0);
        }

        double q = p - 0.5;
        double r = q * q;

        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q /
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1.0);
    }
};

class ExperimentDesigner {
public:
    static std::size_t requiredSampleSize(
        double baseline,
        double effect,
        double alpha = 0.05,
        double power = 0.80
    ) {
        double treatment = baseline + effect;

        if (!(baseline > 0 && baseline < 1))
            throw std::invalid_argument("Invalid baseline rate.");

        if (!(treatment > baseline && treatment < 1))
            throw std::invalid_argument("Invalid treatment rate.");

        if (!(alpha > 0 && alpha < 1 && power > 0 && power < 1))
            throw std::invalid_argument("Invalid statistical parameters.");

        double za = Statistics::inverseNormalCDF(1 - alpha / 2);
        double zb = Statistics::inverseNormalCDF(power);

        double pooled = (baseline + treatment) / 2;

        double numerator = std::pow(
            za * std::sqrt(2 * pooled * (1 - pooled)) +
            zb * std::sqrt(
                baseline * (1 - baseline) +
                treatment * (1 - treatment)
            ),
            2
        );

        return static_cast<std::size_t>(
            std::ceil(numerator / (effect * effect))
        );
    }
};

class Experiment {
private:
    std::string id;
    std::string name;
    ExperimentPolicy policy;
    ExperimentStatus status = ExperimentStatus::Draft;

    std::map<std::string, Participant> participants;

public:
    Experiment(
        std::string experimentId,
        std::string experimentName,
        ExperimentPolicy experimentPolicy
    ) : id(std::move(experimentId)),
        name(std::move(experimentName)),
        policy(experimentPolicy) {

        if (id.empty() || name.empty())
            throw std::invalid_argument("Experiment identity is required.");

        policy.validate();
    }

    void start() {
        if (status != ExperimentStatus::Draft)
            throw std::logic_error("Experiment cannot be started.");

        status = ExperimentStatus::Running;
    }

    Variant assign(const std::string& participantId) {
        requireRunning();

        if (participantId.empty())
            throw std::invalid_argument("Participant ID cannot be empty.");

        auto existing = participants.find(participantId);

        if (existing != participants.end())
            return existing->second.variant;

        // Deterministic assignment supports repeat visits.
        std::hash<std::string> hasher;
        std::size_t hashValue = hasher(id + ":" + participantId);

        double bucket = static_cast<double>(
            hashValue % 1000000
        ) / 1000000.0;

        Variant variant = bucket < policy.allocationRatio
            ? Variant::Control
            : Variant::Treatment;

        participants.emplace(
            participantId,
            Participant{participantId, variant}
        );

        return variant;
    }

    void recordOutcome(
        const std::string& participantId,
        bool converted,
        double revenue
    ) {
        requireRunning();

        auto it = participants.find(participantId);

        if (it == participants.end())
            throw std::invalid_argument("Participant not assigned.");

        if (it->second.hasOutcome)
            throw std::logic_error("Outcome already recorded.");

        if (!std::isfinite(revenue) || revenue < 0)
            throw std::invalid_argument("Invalid revenue.");

        it->second.converted = converted;
        it->second.revenue = revenue;
        it->second.hasOutcome = true;
    }

    void complete() {
        requireRunning();
        status = ExperimentStatus::Completed;
    }

    void stop() {
        requireRunning();
        status = ExperimentStatus::Stopped;
    }

    GroupMetrics calculateMetrics(Variant variant) const {
        GroupMetrics metrics;

        for (const auto& entry : participants) {
            const Participant& p = entry.second;

            if (p.variant != variant || !p.hasOutcome)
                continue;

            metrics.participants++;
            metrics.conversions += p.converted ? 1 : 0;
            metrics.revenue += p.revenue;
        }

        return metrics;
    }

    AnalysisResult analyze() const {
        if (
            status != ExperimentStatus::Completed &&
            status != ExperimentStatus::Stopped
        ) {
            throw std::logic_error("Experiment must be closed before analysis.");
        }

        AnalysisResult result;

        result.control = calculateMetrics(Variant::Control);
        result.treatment = calculateMetrics(Variant::Treatment);

        const auto& c = result.control;
        const auto& t = result.treatment;

        if (c.participants == 0 || t.participants == 0)
            throw std::runtime_error("Both groups require observations.");

        double p1 = c.conversionRate();
        double p2 = t.conversionRate();

        result.absoluteLift = p2 - p1;
        result.relativeLift = p1 > 0 ? result.absoluteLift / p1 : 0.0;

        double pooled = static_cast<double>(
            c.conversions + t.conversions
        ) / (c.participants + t.participants);

        double pooledSE = std::sqrt(
            pooled * (1 - pooled) *
            (1.0 / c.participants + 1.0 / t.participants)
        );

        if (pooledSE > 0) {
            result.zScore = result.absoluteLift / pooledSE;
            result.pValue = 2 * Statistics::normalCDF(
                -std::abs(result.zScore)
            );
        }

        // Unpooled standard error for the confidence interval.
        double ciSE = std::sqrt(
            p1 * (1 - p1) / c.participants +
            p2 * (1 - p2) / t.participants
        );

        double critical = Statistics::inverseNormalCDF(
            1 - policy.alpha / 2
        );

        result.ciLower = result.absoluteLift - critical * ciSE;
        result.ciUpper = result.absoluteLift + critical * ciSE;

        result.statisticallySignificant =
            result.pValue < policy.alpha;

        result.practicallySignificant =
            result.absoluteLift >= policy.minimumDetectableEffect;

        return result;
    }

    std::size_t assignedCount(Variant variant) const {
        return std::count_if(
            participants.begin(),
            participants.end(),
            [variant](const auto& entry) {
                return entry.second.variant == variant;
            }
        );
    }

    std::size_t participantCount() const {
        return participants.size();
    }

    std::size_t observedCount() const {
        return std::count_if(
            participants.begin(),
            participants.end(),
            [](const auto& entry) {
                return entry.second.hasOutcome;
            }
        );
    }

    const std::string& getName() const {
        return name;
    }

private:
    void requireRunning() const {
        if (status != ExperimentStatus::Running)
            throw std::logic_error("Experiment is not running.");
    }
};

class SampleRatioMonitor {
public:
    static double check(
        std::size_t control,
        std::size_t treatment,
        double expectedControlRatio = 0.5
    ) {
        if (control + treatment == 0)
            throw std::invalid_argument("No assignments available.");

        if (!(expectedControlRatio > 0 && expectedControlRatio < 1))
            throw std::invalid_argument("Invalid expected ratio.");

        double total = control + treatment;

        double expectedControl = total * expectedControlRatio;
        double expectedTreatment = total * (1 - expectedControlRatio);

        double chiSquare =
            std::pow(control - expectedControl, 2) / expectedControl +
            std::pow(treatment - expectedTreatment, 2) / expectedTreatment;

        return std::erfc(std::sqrt(chiSquare / 2));
    }
};

void printReport(const Experiment& experiment) {
    AnalysisResult r = experiment.analyze();

    std::cout << "\n========== EXPERIMENT REPORT ==========\n";
    std::cout << experiment.getName() << "\n";

    auto printGroup = [](const std::string& name, const GroupMetrics& m) {
        std::cout << "\n" << name << "\n";
        std::cout << "Participants: " << m.participants << "\n";
        std::cout << "Conversions: " << m.conversions << "\n";
        std::cout << "Conversion rate: " << m.conversionRate() * 100 << "%\n";
        std::cout << "Revenue: " << m.revenue << "\n";
        std::cout << "Average revenue: " << m.averageRevenue() << "\n";
    };

    printGroup("CONTROL", r.control);
    printGroup("TREATMENT", r.treatment);

    std::cout << "\n========== STATISTICAL COMPARISON ==========\n";
    std::cout << "Absolute lift: " << r.absoluteLift * 100 << "%\n";
    std::cout << "Relative lift: " << r.relativeLift * 100 << "%\n";
    std::cout << "Z-score: " << r.zScore << "\n";
    std::cout << "P-value: " << r.pValue << "\n";
    std::cout << "95% CI: ["
              << r.ciLower * 100 << "%, "
              << r.ciUpper * 100 << "%]\n";

    std::cout << "Statistically significant: "
              << std::boolalpha << r.statisticallySignificant << "\n";

    std::cout << "Practically significant: "
              << r.practicallySignificant << "\n";

    std::cout << "Observed participants: "
              << experiment.observedCount() << "\n";
}

int main() {
    try {
        ExperimentPolicy policy;
        policy.allocationRatio = 0.5;
        policy.alpha = 0.05;
        policy.power = 0.80;
        policy.baselineRate = 0.10;
        policy.minimumDetectableEffect = 0.02;

        policy.validate();

        std::size_t required = ExperimentDesigner::requiredSampleSize(
            0.10, 0.02, 0.05, 0.80
        );

        std::cout << "Required sample size per group: "
                  << required << "\n";

        Experiment experiment(
            "checkout-2026",
            "Checkout Conversion Optimization",
            policy
        );

        experiment.start();

        std::mt19937 generator(42);
        std::uniform_real_distribution<double> probability(0.0, 1.0);
        std::uniform_real_distribution<double> revenue(20.0, 150.0);

        const std::size_t total = 20000;

        for (std::size_t i = 0; i < total; ++i) {
            std::string id = "customer-" + std::to_string(i);

            Variant variant = experiment.assign(id);

            double conversionRate =
                variant == Variant::Control ? 0.10 : 0.12;

            bool converted = probability(generator) < conversionRate;

            experiment.recordOutcome(
                id,
                converted,
                converted ? revenue(generator) : 0.0
            );
        }

        experiment.complete();

        printReport(experiment);

        std::size_t control = experiment.assignedCount(Variant::Control);
        std::size_t treatment = experiment.assignedCount(Variant::Treatment);

        double mismatchP = SampleRatioMonitor::check(
            control,
            treatment,
            0.5
        );

        std::cout << "\n========== SAMPLE RATIO CHECK ==========\n";
        std::cout << "Control assignments: " << control << "\n";
        std::cout << "Treatment assignments: " << treatment << "\n";
        std::cout << "SRM p-value: " << mismatchP << "\n";
        std::cout << "Mismatch detected: "
                  << (mismatchP < 0.001 ? "YES" : "NO") << "\n";

        std::cout << "\n========== EDGE CASES ==========\n";

        try {
            experiment.assign("late-user");
        } catch (const std::exception& e) {
            std::cout << "Assignment rejected: " << e.what() << "\n";
        }

        try {
            ExperimentPolicy invalid;
            invalid.allocationRatio = 1.5;
            invalid.validate();
        } catch (const std::exception& e) {
            std::cout << "Policy rejected: " << e.what() << "\n";
        }

    } catch (const std::exception& error) {
        std::cerr << "Experiment failure: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
