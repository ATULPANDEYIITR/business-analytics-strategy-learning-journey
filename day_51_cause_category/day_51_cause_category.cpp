#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

enum class CauseCategory {
    People,
    Process,
    Technology,
    Data,
    Environment,
    Management
};

enum class EvidenceStrength {
    Weak = 1,
    Moderate = 2,
    Strong = 3
};

std::string categoryName(CauseCategory category) {
    switch (category) {
        case CauseCategory::People: return "People";
        case CauseCategory::Process: return "Process";
        case CauseCategory::Technology: return "Technology";
        case CauseCategory::Data: return "Data";
        case CauseCategory::Environment: return "Environment";
        case CauseCategory::Management: return "Management";
    }
    return "Unknown";
}

struct Evidence {
    std::string observation;
    std::string source;
    EvidenceStrength strength;

    int score() const {
        return static_cast<int>(strength);
    }
};

struct ReviewFinding {
    std::string message;
    bool confirmed;
};

class Cause {
private:
    std::string statement_;
    CauseCategory category_;
    std::vector<Evidence> evidence_;
    std::vector<Cause> children_;

public:
    Cause(
        std::string statement,
        CauseCategory category,
        std::vector<Evidence> evidence = {}
    )
        : statement_(std::move(statement)),
          category_(category),
          evidence_(std::move(evidence)) {
        if (statement_.empty()) {
            throw std::invalid_argument("Cause statement cannot be empty.");
        }
    }

    void addChild(Cause child) {
        children_.push_back(std::move(child));
    }

    int evidenceScore() const {
        return std::accumulate(
            evidence_.begin(),
            evidence_.end(),
            0,
            [](int total, const Evidence& item) {
                return total + item.score();
            }
        );
    }

    CauseCategory category() const {
        return category_;
    }

    const std::string& statement() const {
        return statement_;
    }

    void print(int depth = 0) const {
        std::cout << std::string(depth * 2, ' ')
                  << "[" << categoryName(category_) << "] "
                  << statement_ << "\n";

        for (const auto& item : evidence_) {
            std::cout << std::string(depth * 2 + 2, ' ')
                      << "Evidence: " << item.observation
                      << " (" << item.source << ")\n";
        }

        for (const auto& child : children_) {
            child.print(depth + 1);
        }
    }
};

class FiveWhys {
private:
    struct Step {
        std::string question;
        std::string answer;
        std::vector<Evidence> evidence;
    };

    std::vector<Step> steps_;

public:
    void addStep(
        std::string question,
        std::string answer,
        std::vector<Evidence> evidence
    ) {
        if (steps_.size() >= 5) {
            throw std::logic_error("Five Whys cannot exceed five causal levels.");
        }

        if (question.empty() || answer.empty()) {
            throw std::invalid_argument("Why question and answer are required.");
        }

        steps_.push_back({
            std::move(question),
            std::move(answer),
            std::move(evidence)
        });
    }

    const std::string& rootCause() const {
        if (steps_.empty()) {
            throw std::logic_error("No Why analysis exists.");
        }

        return steps_.back().answer;
    }

    void print() const {
        for (std::size_t i = 0; i < steps_.size(); ++i) {
            std::cout << "Why " << i + 1 << ": "
                      << steps_[i].question << "\n";
            std::cout << "Answer: " << steps_[i].answer << "\n";

            for (const auto& evidence : steps_[i].evidence) {
                std::cout << "  Evidence: "
                          << evidence.observation
                          << " [" << evidence.source << "]\n";
            }
        }
    }
};

class MergeGate {
private:
    int minimumEvidenceScore_;
    bool requireIndependentEvidence_;

public:
    MergeGate(int minimumEvidenceScore, bool requireIndependentEvidence)
        : minimumEvidenceScore_(minimumEvidenceScore),
          requireIndependentEvidence_(requireIndependentEvidence) {}

    bool hypothesisIsActionable(
        const Cause& cause,
        const std::vector<std::string>& independentSources
    ) const {
        if (cause.evidenceScore() < minimumEvidenceScore_) {
            return false;
        }

        if (!requireIndependentEvidence_) {
            return true;
        }

        return independentSources.size() >= 2;
    }
};

double average(const std::vector<double>& values) {
    if (values.empty()) {
        throw std::invalid_argument("At least one measurement is required.");
    }

    return std::accumulate(values.begin(), values.end(), 0.0)
           / static_cast<double>(values.size());
}

bool reductionVerified(
    const std::vector<double>& before,
    const std::vector<double>& after
) {
    return average(after) < average(before);
}

std::map<std::string, int> recurringSignals(
    const std::vector<std::string>& events
) {
    std::map<std::string, int> counts;

    for (const auto& event : events) {
        if (!event.empty()) {
            ++counts[event];
        }
    }

    return counts;
}

int main() {
    try {
        const std::string problem =
            "A manufacturing line experienced repeated motor shutdowns "
            "during the afternoon production shift.";

        FiveWhys whys;

        whys.addStep(
            "Why did the production line stop?",
            "The motor protection controller triggered a thermal shutdown.",
            {
                {
                    "Thermal protection state changed to shutdown.",
                    "controller event log",
                    EvidenceStrength::Strong
                }
            }
        );

        whys.addStep(
            "Why did the motor reach the thermal shutdown threshold?",
            "Cooling airflow around the motor was insufficient.",
            {
                {
                    "Motor temperature increased while fan airflow declined.",
                    "sensor telemetry",
                    EvidenceStrength::Strong
                }
            }
        );

        whys.addStep(
            "Why was cooling airflow insufficient?",
            "The cooling filter was heavily obstructed.",
            {
                {
                    "Filter differential pressure exceeded the maintenance limit.",
                    "maintenance telemetry",
                    EvidenceStrength::Strong
                }
            }
        );

        whys.addStep(
            "Why was the filter heavily obstructed?",
            "Filter replacement intervals did not reflect the observed dust load.",
            {
                {
                    "Replacement intervals were fixed despite seasonal dust variation.",
                    "maintenance records",
                    EvidenceStrength::Moderate
                }
            }
        );

        whys.addStep(
            "Why were replacement intervals not adjusted to dust conditions?",
            "The maintenance process did not use differential-pressure measurements "
            "as an input to preventive-maintenance decisions.",
            {
                {
                    "Maintenance workflow contains no pressure-based trigger.",
                    "maintenance procedure",
                    EvidenceStrength::Moderate
                }
            }
        );

        Cause processCause(
            "Preventive maintenance ignored measured filter pressure.",
            CauseCategory::Process,
            {
                {
                    "No pressure-based replacement rule exists.",
                    "maintenance procedure",
                    EvidenceStrength::Strong
                }
            }
        );

        Cause technologyCause(
            "Cooling performance degraded as filter resistance increased.",
            CauseCategory::Technology,
            {
                {
                    "Airflow dropped while pressure differential increased.",
                    "sensor telemetry",
                    EvidenceStrength::Strong
                }
            }
        );

        Cause dataCause(
            "The plant collected pressure data but did not use it in maintenance decisions.",
            CauseCategory::Data,
            {
                {
                    "Pressure telemetry exists without a maintenance trigger.",
                    "sensor database",
                    EvidenceStrength::Moderate
                }
            }
        );

        processCause.addChild(Cause(
            "The maintenance checklist used elapsed time instead of condition data.",
            CauseCategory::Process,
            {
                {
                    "Checklist specifies calendar intervals.",
                    "maintenance checklist",
                    EvidenceStrength::Moderate
                }
            }
        ));

        std::cout << "ROOT CAUSE ANALYSIS\n";
        std::cout << std::string(70, '=') << "\n";
        std::cout << "Problem: " << problem << "\n\n";

        std::cout << "5 WHYS\n";
        std::cout << std::string(70, '-') << "\n";
        whys.print();

        std::cout << "\nFISHBONE DIAGNOSIS\n";
        std::cout << std::string(70, '-') << "\n";
        processCause.print();
        technologyCause.print();
        dataCause.print();

        MergeGate evidenceGate(5, true);

        const std::vector<std::string> independentSources = {
            "maintenance procedure",
            "maintenance telemetry"
        };

        std::cout << "\nHYPOTHESIS VALIDATION\n";
        std::cout << std::string(70, '-') << "\n";

        std::cout << "Process cause actionable: "
                  << std::boolalpha
                  << evidenceGate.hypothesisIsActionable(
                         processCause,
                         independentSources
                     )
                  << "\n";

        std::cout << "Technology cause actionable: "
                  << evidenceGate.hypothesisIsActionable(
                         technologyCause,
                         independentSources
                     )
                  << "\n";

        std::vector<double> temperatureBefore = {91, 94, 93, 95};
        std::vector<double> temperatureAfter = {82, 84, 83, 81};

        std::cout << "\nCORRECTIVE-ACTION VALIDATION\n";
        std::cout << std::string(70, '-') << "\n";
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "Before average: "
                  << average(temperatureBefore) << "\n";
        std::cout << "After average:  "
                  << average(temperatureAfter) << "\n";
        std::cout << "Reduction verified: "
                  << reductionVerified(
                         temperatureBefore,
                         temperatureAfter
                     )
                  << "\n";

        std::cout << "\nRECURRING FAILURE SIGNALS\n";
        std::cout << std::string(70, '-') << "\n";

        const auto signals = recurringSignals({
            "filter pressure high",
            "thermal shutdown",
            "filter pressure high",
            "airflow low",
            "filter pressure high",
            "thermal shutdown"
        });

        for (const auto& [signal, count] : signals) {
            std::cout << signal << ": " << count << "\n";
        }

        std::cout << "\nROOT CAUSE\n";
        std::cout << std::string(70, '-') << "\n";
        std::cout << whys.rootCause() << "\n";

    } catch (const std::exception& error) {
        std::cerr << "RCA execution failed: "
                  << error.what() << "\n";
        return 1;
    }

    return 0;
}
