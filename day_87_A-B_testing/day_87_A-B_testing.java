import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicLong;

// ============================================================
// A/B TESTING: ENTERPRISE EXPERIMENT GOVERNANCE
// Java 17
// ============================================================

public class ABTestingEnterprise {

    enum Variant {
        CONTROL,
        TREATMENT
    }

    enum ExperimentStatus {
        DRAFT,
        RUNNING,
        COMPLETED,
        STOPPED
    }

    enum ReviewDecision {
        NOT_REVIEWED,
        APPROVED,
        REJECTED
    }

    static class ExperimentException extends RuntimeException {
        ExperimentException(String message) {
            super(message);
        }
    }

    static class ValidationException extends RuntimeException {
        ValidationException(String message) {
            super(message);
        }
    }

    record ExperimentPolicy(
        double allocationRatio,
        double alpha,
        double power,
        double baselineRate,
        double minimumDetectableEffect,
        int minimumDurationDays,
        boolean requireGuardrailApproval
    ) {
        ExperimentPolicy {
            if (!(allocationRatio > 0 && allocationRatio < 1)) {
                throw new ValidationException("Invalid allocation ratio.");
            }

            if (!(alpha > 0 && alpha < 1)) {
                throw new ValidationException("Invalid significance level.");
            }

            if (!(power > 0 && power < 1)) {
                throw new ValidationException("Invalid statistical power.");
            }

            if (!(baselineRate > 0 && baselineRate < 1)) {
                throw new ValidationException("Invalid baseline rate.");
            }

            if (!(minimumDetectableEffect > 0)) {
                throw new ValidationException("Invalid detectable effect.");
            }

            if (baselineRate + minimumDetectableEffect >= 1) {
                throw new ValidationException("Invalid treatment rate.");
            }

            if (minimumDurationDays < 1) {
                throw new ValidationException("Invalid experiment duration.");
            }
        }
    }

    record Participant(
        String participantId,
        Variant variant,
        long assignedAt
    ) {}

    record Outcome(
        boolean converted,
        double revenue,
        long recordedAt
    ) {
        Outcome {
            if (!Double.isFinite(revenue) || revenue < 0) {
                throw new ValidationException("Invalid revenue.");
            }
        }
    }

    record GroupMetrics(
        int participants,
        int conversions,
        double conversionRate,
        double totalRevenue,
        double averageRevenue
    ) {}

    record StatisticalResult(
        double absoluteLift,
        double relativeLift,
        double zScore,
        double pValue,
        double confidenceLower,
        double confidenceUpper,
        boolean statisticallySignificant,
        boolean practicallySignificant
    ) {}

    record ExperimentReport(
        String experimentId,
        String experimentName,
        GroupMetrics control,
        GroupMetrics treatment,
        StatisticalResult statistics
    ) {}

    static class StatisticalFunctions {

        static double normalCDF(double x) {
            return 0.5 * erfc(-x / Math.sqrt(2));
        }

        static double erfc(double x) {
            double z = Math.abs(x);
            double t = 1.0 / (1.0 + z / 2.0);

            double answer = t * Math.exp(
                -z * z - 1.26551223 +
                t * (
                    1.00002368 +
                    t * (
                        0.37409196 +
                        t * (
                            0.09678418 +
                            t * (
                                -0.18628806 +
                                t * (
                                    0.27886807 +
                                    t * (
                                        -1.13520398 +
                                        t * (
                                            1.48851587 +
                                            t * (
                                                -0.82215223 +
                                                t * 0.17087277
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            );

            return x >= 0 ? answer : 2 - answer;
        }

        static double inverseNormalCDF(double p) {
            if (!(p > 0 && p < 1)) {
                throw new ValidationException("Invalid probability.");
            }

            double[] a = {
                -39.6968302866538, 220.946098424521,
                -275.928510446969, 138.357751867269,
                -30.6647980661472, 2.50662827745924
            };

            double[] b = {
                -54.4760987982241, 161.585836858041,
                -155.698979859887, 66.8013118877197,
                -13.2806815528857
            };

            double[] c = {
                -0.00778489400243029, -0.322396458041136,
                -2.40075827716184, -2.54973253934373,
                4.37466414146497, 2.93816398269878
            };

            double[] d = {
                0.00778469570904146, 0.32246712907004,
                2.445134137143, 3.75440866190742
            };

            double low = 0.02425;
            double high = 1 - low;

            if (p < low) {
                double q = Math.sqrt(-2 * Math.log(p));

                return (((((c[0] * q + c[1]) * q + c[2]) * q +
                    c[3]) * q + c[4]) * q + c[5]) /
                    ((((d[0] * q + d[1]) * q + d[2]) * q +
                    d[3]) * q + 1);
            }

            if (p > high) {
                double q = Math.sqrt(-2 * Math.log(1 - p));

                return -(((((c[0] * q + c[1]) * q + c[2]) * q +
                    c[3]) * q + c[4]) * q + c[5]) /
                    ((((d[0] * q + d[1]) * q + d[2]) * q +
                    d[3]) * q + 1);
            }

            double q = p - 0.5;
            double r = q * q;

            return (((((a[0] * r + a[1]) * r + a[2]) * r +
                a[3]) * r + a[4]) * r + a[5]) * q /
                (((((b[0] * r + b[1]) * r + b[2]) * r +
                b[3]) * r + b[4]) * r + 1);
        }
    }

    static class SampleSizeCalculator {

        static int calculate(
            double baseline,
            double effect,
            double alpha,
            double power
        ) {
            double treatment = baseline + effect;

            if (!(baseline > 0 && baseline < 1)) {
                throw new ValidationException("Invalid baseline.");
            }

            if (!(treatment > baseline && treatment < 1)) {
                throw new ValidationException("Invalid treatment rate.");
            }

            double za = StatisticalFunctions.inverseNormalCDF(
                1 - alpha / 2
            );

            double zb = StatisticalFunctions.inverseNormalCDF(power);

            double pooled = (baseline + treatment) / 2;

            double numerator = Math.pow(
                za * Math.sqrt(2 * pooled * (1 - pooled)) +
                zb * Math.sqrt(
                    baseline * (1 - baseline) +
                    treatment * (1 - treatment)
                ),
                2
            );

            return (int) Math.ceil(
                numerator / (effect * effect)
            );
        }
    }

    static class ExperimentService {

        private final String experimentId;
        private final String name;
        private final ExperimentPolicy policy;

        private final Map<String, Participant> participants =
            new HashMap<>();

        private final Map<String, Outcome> outcomes =
            new HashMap<>();

        private final AtomicLong assignmentCounter =
            new AtomicLong();

        private ExperimentStatus status = ExperimentStatus.DRAFT;
        private ReviewDecision reviewDecision = ReviewDecision.NOT_REVIEWED;

        private long startedAt;
        private long completedAt;

        ExperimentService(
            String experimentId,
            String name,
            ExperimentPolicy policy
        ) {
            if (experimentId == null || experimentId.isBlank()) {
                throw new ValidationException("Experiment ID required.");
            }

            if (name == null || name.isBlank()) {
                throw new ValidationException("Experiment name required.");
            }

            this.experimentId = experimentId;
            this.name = name;
            this.policy = Objects.requireNonNull(policy);
        }

        synchronized void approveDesign() {
            if (status != ExperimentStatus.DRAFT) {
                throw new ExperimentException(
                    "Only draft experiments can be reviewed."
                );
            }

            reviewDecision = ReviewDecision.APPROVED;
        }

        synchronized void rejectDesign() {
            if (status != ExperimentStatus.DRAFT) {
                throw new ExperimentException(
                    "Only draft experiments can be rejected."
                );
            }

            reviewDecision = ReviewDecision.REJECTED;
        }

        synchronized void start() {
            if (status != ExperimentStatus.DRAFT) {
                throw new ExperimentException(
                    "Invalid experiment transition."
                );
            }

            if (reviewDecision != ReviewDecision.APPROVED) {
                throw new ExperimentException(
                    "Experiment design requires approval."
                );
            }

            status = ExperimentStatus.RUNNING;
            startedAt = System.currentTimeMillis();
        }

        synchronized Variant assign(String participantId) {
            requireRunning();

            if (participantId == null || participantId.isBlank()) {
                throw new ValidationException("Invalid participant ID.");
            }

            Participant existing = participants.get(participantId);

            if (existing != null) {
                return existing.variant();
            }

            long hash = stableHash(experimentId + ":" + participantId);

            long bucket = Long.remainderUnsigned(hash, 1_000_000);

            long threshold = (long) (
                policy.allocationRatio() * 1_000_000
            );

            Variant variant = bucket < threshold
                ? Variant.CONTROL
                : Variant.TREATMENT;

            Participant participant = new Participant(
                participantId,
                variant,
                System.currentTimeMillis()
            );

            participants.put(participantId, participant);
            assignmentCounter.incrementAndGet();

            return variant;
        }

        synchronized void recordOutcome(
            String participantId,
            boolean converted,
            double revenue
        ) {
            requireRunning();

            if (!participants.containsKey(participantId)) {
                throw new ExperimentException("Participant not assigned.");
            }

            if (outcomes.containsKey(participantId)) {
                throw new ExperimentException("Duplicate outcome.");
            }

            Outcome outcome = new Outcome(
                converted,
                revenue,
                System.currentTimeMillis()
            );

            outcomes.put(participantId, outcome);
        }

        synchronized void complete() {
            requireRunning();

            if (policy.requireGuardrailApproval()) {
                // A production implementation would evaluate persisted
                // guardrail metrics before allowing this transition.
                if (participants.size() == 0) {
                    throw new ExperimentException(
                        "No observations available for guardrail review."
                    );
                }
            }

            status = ExperimentStatus.COMPLETED;
            completedAt = System.currentTimeMillis();
        }

        synchronized void stop() {
            requireRunning();
            status = ExperimentStatus.STOPPED;
            completedAt = System.currentTimeMillis();
        }

        private long stableHash(String value) {
            try {
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                byte[] bytes = digest.digest(
                    value.getBytes(java.nio.charset.StandardCharsets.UTF_8)
                );

                long result = 0;

                for (int i = 0; i < 8; i++) {
                    result = (result << 8) | (bytes[i] & 0xffL);
                }

                return result;
            } catch (NoSuchAlgorithmException exception) {
                throw new IllegalStateException(
                    "SHA-256 is unavailable.", exception
                );
            }
        }

        private void requireRunning() {
            if (status != ExperimentStatus.RUNNING) {
                throw new ExperimentException("Experiment is not running.");
            }
        }

        private GroupMetrics calculateGroup(Variant variant) {
            int participantsCount = 0;
            int conversions = 0;
            double revenue = 0;

            for (Map.Entry<String, Participant> entry : participants.entrySet()) {
                Participant participant = entry.getValue();

                if (participant.variant() != variant) {
                    continue;
                }

                Outcome outcome = outcomes.get(entry.getKey());

                if (outcome == null) {
                    continue;
                }

                participantsCount++;

                if (outcome.converted()) {
                    conversions++;
                }

                revenue += outcome.revenue();
            }

            double rate = participantsCount == 0
                ? 0
                : (double) conversions / participantsCount;

            return new GroupMetrics(
                participantsCount,
                conversions,
                rate,
                revenue,
                participantsCount == 0 ? 0 : revenue / participantsCount
            );
        }

        synchronized ExperimentReport analyze() {
            if (
                status != ExperimentStatus.COMPLETED &&
                status != ExperimentStatus.STOPPED
            ) {
                throw new ExperimentException(
                    "Experiment must be closed before analysis."
                );
            }

            GroupMetrics control = calculateGroup(Variant.CONTROL);
            GroupMetrics treatment = calculateGroup(Variant.TREATMENT);

            if (
                control.participants() == 0 ||
                treatment.participants() == 0
            ) {
                throw new ExperimentException(
                    "Both groups require observed participants."
                );
            }

            double p1 = control.conversionRate();
            double p2 = treatment.conversionRate();

            double lift = p2 - p1;
            double relativeLift = p1 > 0 ? lift / p1 : 0;

            double pooled =
                (control.conversions() + treatment.conversions()) /
                (double) (
                    control.participants() + treatment.participants()
                );

            double pooledSE = Math.sqrt(
                pooled * (1 - pooled) *
                (1.0 / control.participants() +
                 1.0 / treatment.participants())
            );

            double z = pooledSE == 0 ? 0 : lift / pooledSE;
            double pValue = pooledSE == 0
                ? 1
                : 2 * StatisticalFunctions.normalCDF(-Math.abs(z));

            double ciSE = Math.sqrt(
                p1 * (1 - p1) / control.participants() +
                p2 * (1 - p2) / treatment.participants()
            );

            double critical = StatisticalFunctions.inverseNormalCDF(
                1 - policy.alpha() / 2
            );

            StatisticalResult statistics = new StatisticalResult(
                lift,
                relativeLift,
                z,
                pValue,
                lift - critical * ciSE,
                lift + critical * ciSE,
                pValue < policy.alpha(),
                lift >= policy.minimumDetectableEffect()
            );

            return new ExperimentReport(
                experimentId,
                name,
                control,
                treatment,
                statistics
            );
        }

        int assignedCount(Variant variant) {
            return (int) participants.values().stream()
                .filter(p -> p.variant() == variant)
                .count();
        }

        int getParticipantCount() {
            return participants.size();
        }

        int getObservedCount() {
            return outcomes.size();
        }

        ExperimentStatus getStatus() {
            return status;
        }

        long getStartedAt() {
            return startedAt;
        }

        long getCompletedAt() {
            return completedAt;
        }

        Map<String, Participant> participantSnapshot() {
            return Collections.unmodifiableMap(
                new HashMap<>(participants)
            );
        }
    }

    static class ExperimentReportingService {

        static void print(ExperimentReport report) {
            System.out.println("\n========== ENTERPRISE EXPERIMENT REPORT ==========");
            System.out.println("ID: " + report.experimentId());
            System.out.println("Name: " + report.experimentName());

            printGroup("CONTROL", report.control());
            printGroup("TREATMENT", report.treatment());

            StatisticalResult s = report.statistics();

            System.out.println("\nSTATISTICAL EVALUATION");
            System.out.printf("Absolute lift: %.4f%%%n", s.absoluteLift() * 100);
            System.out.printf("Relative lift: %.4f%%%n", s.relativeLift() * 100);
            System.out.printf("Z-score: %.4f%n", s.zScore());
            System.out.printf("P-value: %.6f%n", s.pValue());

            System.out.printf(
                "95%% confidence interval: [%.4f%%, %.4f%%]%n",
                s.confidenceLower() * 100,
                s.confidenceUpper() * 100
            );

            System.out.println(
                "Statistically significant: " +
                s.statisticallySignificant()
            );

            System.out.println(
                "Practically significant: " +
                s.practicallySignificant()
            );
        }

        private static void printGroup(
            String name,
            GroupMetrics metrics
        ) {
            System.out.println("\n" + name);
            System.out.println("Participants: " + metrics.participants());
            System.out.println("Conversions: " + metrics.conversions());
            System.out.printf(
                "Conversion rate: %.4f%%%n",
                metrics.conversionRate() * 100
            );
            System.out.printf(
                "Total revenue: %.2f%n",
                metrics.totalRevenue()
            );
            System.out.printf(
                "Revenue per participant: %.2f%n",
                metrics.averageRevenue()
            );
        }
    }

    public static void main(String[] args) {
        try {
            ExperimentPolicy policy = new ExperimentPolicy(
                0.5,
                0.05,
                0.80,
                0.10,
                0.02,
                7,
                false
            );

            int required = SampleSizeCalculator.calculate(
                0.10,
                0.02,
                0.05,
                0.80
            );

            System.out.println(
                "Required sample size per group: " + required
            );

            ExperimentService experiment = new ExperimentService(
                "enterprise-checkout-2026",
                "Enterprise Checkout Conversion Test",
                policy
            );

            // Design approval is independent of statistical approval.
            experiment.approveDesign();
            experiment.start();

            java.util.Random random = new java.util.Random(42);

            for (int i = 0; i < 20000; i++) {
                String participantId = "customer-" + i;

                Variant variant = experiment.assign(participantId);

                double conversionRate =
                    variant == Variant.CONTROL ? 0.10 : 0.12;

                boolean converted = random.nextDouble() < conversionRate;

                double revenue = converted
                    ? 20 + random.nextDouble() * 130
                    : 0;

                experiment.recordOutcome(
                    participantId,
                    converted,
                    revenue
                );
            }

            experiment.complete();

            ExperimentReport report = experiment.analyze();

            ExperimentReportingService.print(report);

            System.out.println("\nGOVERNANCE INFORMATION");
            System.out.println("Experiment state: " + experiment.getStatus());
            System.out.println("Assignments: " + experiment.getParticipantCount());
            System.out.println("Observed outcomes: " + experiment.getObservedCount());
            System.out.println(
                "Missing outcomes: " +
                (experiment.getParticipantCount() - experiment.getObservedCount())
            );

            System.out.println("\nEDGE CASE VALIDATION");

            try {
                experiment.assign("late-participant");
            } catch (ExperimentException exception) {
                System.out.println("State protection: " + exception.getMessage());
            }

            try {
                new ExperimentPolicy(
                    1.5, 0.05, 0.80, 0.10, 0.02, 7, false
                );
            } catch (ValidationException exception) {
                System.out.println("Policy validation: " + exception.getMessage());
            }

        } catch (Exception exception) {
            System.err.println(
                "Experiment execution failed: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
