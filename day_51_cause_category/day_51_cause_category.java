import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

public class RootCauseAnalysis {

    enum CauseCategory {
        PEOPLE,
        PROCESS,
        TECHNOLOGY,
        DATA,
        ENVIRONMENT,
        MANAGEMENT
    }

    enum EvidenceStrength {
        WEAK(1),
        MODERATE(2),
        STRONG(3);

        private final int score;

        EvidenceStrength(int score) {
            this.score = score;
        }

        public int score() {
            return score;
        }
    }

    record Evidence(
        String observation,
        String source,
        EvidenceStrength strength
    ) {
        Evidence {
            Objects.requireNonNull(observation);
            Objects.requireNonNull(source);
            Objects.requireNonNull(strength);

            if (observation.isBlank() || source.isBlank()) {
                throw new IllegalArgumentException(
                    "Evidence observation and source are required."
                );
            }
        }
    }

    record WhyStep(
        String question,
        String answer,
        List<Evidence> evidence
    ) {
        WhyStep {
            if (question == null || question.isBlank()
                || answer == null || answer.isBlank()) {
                throw new IllegalArgumentException(
                    "A Why step requires a question and answer."
                );
            }

            evidence = List.copyOf(evidence);
        }
    }

    static final class Cause {
        private final String statement;
        private final CauseCategory category;
        private final List<Evidence> evidence;
        private final List<Cause> children = new ArrayList<>();

        Cause(
            String statement,
            CauseCategory category,
            List<Evidence> evidence
        ) {
            if (statement == null || statement.isBlank()) {
                throw new IllegalArgumentException(
                    "Cause statement is required."
                );
            }

            this.statement = statement;
            this.category = Objects.requireNonNull(category);
            this.evidence = List.copyOf(evidence);
        }

        void addChild(Cause child) {
            children.add(Objects.requireNonNull(child));
        }

        int evidenceScore() {
            return evidence.stream()
                .mapToInt(item -> item.strength().score())
                .sum();
        }

        String statement() {
            return statement;
        }

        CauseCategory category() {
            return category;
        }

        void print(String indentation) {
            System.out.printf(
                "%s[%s] %s%n",
                indentation,
                category,
                statement
            );

            for (Evidence item : evidence) {
                System.out.printf(
                    "%s  Evidence: %s (%s)%n",
                    indentation,
                    item.observation(),
                    item.source()
                );
            }

            for (Cause child : children) {
                child.print(indentation + "  ");
            }
        }
    }

    static final class FiveWhys {
        private final List<WhyStep> steps = new ArrayList<>();

        void add(
            String question,
            String answer,
            List<Evidence> evidence
        ) {
            if (steps.size() >= 5) {
                throw new IllegalStateException(
                    "Five Whys cannot contain more than five levels."
                );
            }

            steps.add(new WhyStep(question, answer, evidence));
        }

        String rootCause() {
            if (steps.isEmpty()) {
                throw new IllegalStateException("No Why analysis exists.");
            }

            return steps.get(steps.size() - 1).answer();
        }

        void print() {
            for (int i = 0; i < steps.size(); i++) {
                WhyStep step = steps.get(i);

                System.out.printf(
                    "Why %d: %s%n",
                    i + 1,
                    step.question()
                );
                System.out.printf(
                    "Answer: %s%n",
                    step.answer()
                );

                step.evidence().forEach(item ->
                    System.out.printf(
                        "  Evidence: %s [%s]%n",
                        item.observation(),
                        item.source()
                    )
                );
            }
        }
    }

    interface DiagnosticRule {
        boolean evaluate(DiagnosticContext context);
    }

    record DiagnosticContext(
        double beforeFailureRate,
        double afterFailureRate,
        int independentEvidenceSources,
        boolean correctiveControlImplemented
    ) {}

    static final class GovernancePolicy {
        private final int minimumEvidenceScore;
        private final int minimumIndependentSources;

        GovernancePolicy(
            int minimumEvidenceScore,
            int minimumIndependentSources
        ) {
            if (minimumEvidenceScore < 1
                || minimumIndependentSources < 1) {
                throw new IllegalArgumentException(
                    "Evidence thresholds must be positive."
                );
            }

            this.minimumEvidenceScore = minimumEvidenceScore;
            this.minimumIndependentSources = minimumIndependentSources;
        }

        boolean permitsAction(
            Cause cause,
            DiagnosticContext context
        ) {
            return cause.evidenceScore() >= minimumEvidenceScore
                && context.independentEvidenceSources()
                    >= minimumIndependentSources;
        }
    }

    static final class RCAService {
        private final String problem;
        private final FiveWhys whys = new FiveWhys();
        private final Map<CauseCategory, Cause> fishbone =
            new EnumMap<>(CauseCategory.class);
        private final List<Cause> hypotheses = new ArrayList<>();

        RCAService(String problem) {
            if (problem == null || problem.isBlank()) {
                throw new IllegalArgumentException(
                    "Problem statement is required."
                );
            }

            this.problem = problem;
        }

        void addCause(Cause cause) {
            fishbone.put(cause.category(), cause);
            hypotheses.add(cause);
        }

        void printReport() {
            System.out.println("ROOT CAUSE ANALYSIS");
            System.out.println("=".repeat(70));
            System.out.println("Problem: " + problem);

            System.out.println("\n5 WHYS");
            System.out.println("-".repeat(70));
            whys.print();

            System.out.println("\nFISHBONE DIAGNOSIS");
            System.out.println("-".repeat(70));

            fishbone.values().forEach(cause -> cause.print(""));

            System.out.println("\nHYPOTHESIS RANKING");
            System.out.println("-".repeat(70));

            hypotheses.stream()
                .sorted(
                    Comparator.comparingInt(Cause::evidenceScore)
                        .reversed()
                )
                .forEach(cause ->
                    System.out.printf(
                        "%s | score=%d%n",
                        cause.statement(),
                        cause.evidenceScore()
                    )
                );
        }
    }

    static double average(List<Double> values) {
        if (values == null || values.isEmpty()) {
            throw new IllegalArgumentException(
                "Measurements cannot be empty."
            );
        }

        return values.stream()
            .mapToDouble(Double::doubleValue)
            .average()
            .orElseThrow();
    }

    static boolean reductionVerified(
        List<Double> before,
        List<Double> after
    ) {
        return average(after) < average(before);
    }

    static Map<String, Long> recurringSignals(List<String> events) {
        return events.stream()
            .filter(event -> event != null && !event.isBlank())
            .map(String::trim)
            .collect(Collectors.groupingBy(
                event -> event,
                Collectors.counting()
            ));
    }

    public static void main(String[] args) {
        try {
            RCAService service = new RCAService(
                "Production orders were delayed because a warehouse "
                + "label-printing service repeatedly stopped."
            );

            service.whys.add(
                "Why were orders delayed?",
                "The label-printing service stopped processing jobs.",
                List.of(
                    new Evidence(
                        "The print queue stopped consuming jobs.",
                        "queue metrics",
                        EvidenceStrength.STRONG
                    )
                )
            );

            service.whys.add(
                "Why did the service stop processing jobs?",
                "Worker threads became blocked waiting for an unavailable printer.",
                List.of(
                    new Evidence(
                        "Worker utilization reached 100% while printer responses timed out.",
                        "application telemetry",
                        EvidenceStrength.STRONG
                    )
                )
            );

            service.whys.add(
                "Why were workers blocked by printer timeouts?",
                "The service had no bounded retry policy for unavailable printers.",
                List.of(
                    new Evidence(
                        "Retry attempts continued without a circuit limit.",
                        "application logs",
                        EvidenceStrength.STRONG
                    )
                )
            );

            service.whys.add(
                "Why was there no bounded retry policy?",
                "The reliability policy specified retries but not resource limits.",
                List.of(
                    new Evidence(
                        "Service policy contains retry count but no concurrency ceiling.",
                        "service policy",
                        EvidenceStrength.MODERATE
                    )
                )
            );

            service.whys.add(
                "Why did the reliability policy omit resource limits?",
                "Operational failure modes were not included in the service acceptance criteria.",
                List.of(
                    new Evidence(
                        "Acceptance checklist contains functional scenarios only.",
                        "delivery checklist",
                        EvidenceStrength.MODERATE
                    )
                )
            );

            Cause process = new Cause(
                "Service acceptance criteria omitted bounded-failure behavior.",
                CauseCategory.PROCESS,
                List.of(
                    new Evidence(
                        "No resilience acceptance criterion exists.",
                        "delivery checklist",
                        EvidenceStrength.STRONG
                    )
                )
            );

            Cause technology = new Cause(
                "Unbounded printer retries consumed worker capacity.",
                CauseCategory.TECHNOLOGY,
                List.of(
                    new Evidence(
                        "Workers remained occupied during printer outages.",
                        "runtime telemetry",
                        EvidenceStrength.STRONG
                    )
                )
            );

            Cause data = new Cause(
                "Printer timeout telemetry was not connected to an automatic circuit-breaker rule.",
                CauseCategory.DATA,
                List.of(
                    new Evidence(
                        "Timeout metrics existed without an automated control.",
                        "monitoring configuration",
                        EvidenceStrength.MODERATE
                    )
                )
            );

            process.addChild(new Cause(
                "Release validation tested successful printing but not printer unavailability.",
                CauseCategory.PROCESS,
                List.of(
                    new Evidence(
                        "Failure-mode test was absent.",
                        "integration test suite",
                        EvidenceStrength.MODERATE
                    )
                )
            ));

            service.addCause(process);
            service.addCause(technology);
            service.addCause(data);

            service.printReport();

            DiagnosticContext context = new DiagnosticContext(
                0.21,
                0.04,
                2,
                true
            );

            GovernancePolicy policy = new GovernancePolicy(5, 2);

            System.out.println("\nACTIONABILITY");
            System.out.println("-".repeat(70));

            System.out.printf(
                "Process hypothesis: %s%n",
                policy.permitsAction(process, context)
            );

            System.out.printf(
                "Technology hypothesis: %s%n",
                policy.permitsAction(technology, context)
            );

            List<Double> before = List.of(0.21, 0.20, 0.22, 0.21);
            List<Double> after = List.of(0.04, 0.05, 0.03, 0.04);

            System.out.println("\nCORRECTIVE CONTROL");
            System.out.println("-".repeat(70));
            System.out.printf(
                "Failure rate before: %.3f%n",
                average(before)
            );
            System.out.printf(
                "Failure rate after:  %.3f%n",
                average(after)
            );
            System.out.printf(
                "Reduction verified: %s%n",
                reductionVerified(before, after)
            );

            System.out.println("\nRECURRING SIGNALS");
            System.out.println("-".repeat(70));

            recurringSignals(List.of(
                "printer timeout",
                "worker saturation",
                "printer timeout",
                "printer timeout",
                "queue growth",
                "worker saturation"
            )).forEach(
                (signal, count) ->
                    System.out.printf(
                        "%s: %d%n",
                        signal,
                        count
                    )
            );

            System.out.println("\nROOT CAUSE");
            System.out.println("-".repeat(70));
            System.out.println(service.whys.rootCause());

            System.out.println(
                "\nInvestigation timestamp: " + Instant.now()
            );

        } catch (RuntimeException exception) {
            System.err.println(
                "RCA execution failed: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
