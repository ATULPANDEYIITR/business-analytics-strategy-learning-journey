import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class BusinessStorytelling {

    enum Priority {
        CRITICAL,
        HIGH,
        MEDIUM,
        LOW
    }

    enum MetricDirection {
        IMPROVING,
        DECLINING,
        STABLE
    }

    record Metric(
        String name,
        double current,
        double previous,
        double target,
        String unit
    ) {
        Metric {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Metric name is required.");
            }

            if (!Double.isFinite(current)
                    || !Double.isFinite(previous)
                    || !Double.isFinite(target)) {
                throw new IllegalArgumentException(
                    "Metric values must be finite."
                );
            }

            unit = unit == null ? "" : unit;
        }

        double change() {
            return current - previous;
        }

        double changePercent() {
            if (previous == 0.0) {
                return current == 0.0 ? 0.0 : Double.POSITIVE_INFINITY;
            }
            return (change() / previous) * 100.0;
        }

        double targetGap() {
            return current - target;
        }

        MetricDirection direction() {
            if (change() > 0.0) {
                return MetricDirection.IMPROVING;
            }
            if (change() < 0.0) {
                return MetricDirection.DECLINING;
            }
            return MetricDirection.STABLE;
        }
    }

    record Insight(
        Metric metric,
        Priority priority,
        String observation,
        String implication,
        String action
    ) {}

    interface StoryPolicy {
        Priority classify(Metric metric);

        String implication(Metric metric, Priority priority);

        String action(Metric metric, Priority priority);
    }

    static final class ExecutiveStoryPolicy implements StoryPolicy {

        @Override
        public Priority classify(Metric metric) {
            double change = metric.changePercent();

            if (change <= -10.0) {
                return Priority.CRITICAL;
            }
            if (change < -3.0) {
                return Priority.HIGH;
            }
            if (change >= 10.0) {
                return Priority.HIGH;
            }
            if (change >= 3.0) {
                return Priority.MEDIUM;
            }
            return Priority.LOW;
        }

        @Override
        public String implication(Metric metric, Priority priority) {
            return switch (priority) {
                case CRITICAL ->
                    metric.name()
                        + " has materially deteriorated and creates a significant "
                        + "business risk.";
                case HIGH ->
                    metric.change() < 0
                        ? metric.name()
                            + " is deteriorating enough to require targeted investigation."
                        : metric.name()
                            + " is improving strongly and may represent a scalable opportunity.";
                case MEDIUM ->
                    metric.name()
                        + " is improving, but persistence and target attainment "
                        + "should be tested.";
                case LOW ->
                    metric.name()
                        + " is relatively stable and provides a weaker immediate "
                        + "decision signal.";
            };
        }

        @Override
        public String action(Metric metric, Priority priority) {
            return switch (priority) {
                case CRITICAL ->
                    "Segment the deterioration, identify the largest driver, "
                    + "assign ownership, and establish a corrective measurement.";
                case HIGH ->
                    metric.change() < 0
                        ? "Break the decline into customer, product, channel, and "
                          + "time dimensions before selecting an intervention."
                        : "Identify the operating behavior behind the improvement "
                          + "and test whether it can be scaled safely.";
                case MEDIUM ->
                    "Monitor the movement across important segments and validate "
                    + "that the improvement persists.";
                case LOW ->
                    "Continue monitoring while prioritizing metrics with greater "
                    + "movement or business consequence.";
            };
        }
    }

    static final class StoryService {
        private final List<Metric> metrics;
        private final StoryPolicy policy;

        StoryService(List<Metric> metrics, StoryPolicy policy) {
            if (metrics == null || metrics.isEmpty()) {
                throw new IllegalArgumentException(
                    "At least one metric is required."
                );
            }

            if (policy == null) {
                throw new IllegalArgumentException("A story policy is required.");
            }

            Set<String> names = new HashSet<>();

            for (Metric metric : metrics) {
                if (!names.add(metric.name().toLowerCase())) {
                    throw new IllegalArgumentException(
                        "Duplicate metric: " + metric.name()
                    );
                }
            }

            this.metrics = List.copyOf(metrics);
            this.policy = policy;
        }

        List<Insight> generateInsights() {
            List<Insight> result = new ArrayList<>();

            for (Metric metric : metrics) {
                Priority priority = policy.classify(metric);

                String observation = String.format(
                    "%s changed from %.2f%s to %.2f%s.",
                    metric.name(),
                    metric.previous(),
                    metric.unit(),
                    metric.current(),
                    metric.unit()
                );

                result.add(
                    new Insight(
                        metric,
                        priority,
                        observation,
                        policy.implication(metric, priority),
                        policy.action(metric, priority)
                    )
                );
            }

            result.sort(
                Comparator.comparingInt(
                    insight -> insight.priority().ordinal()
                )
            );

            return List.copyOf(result);
        }

        String createExecutiveNarrative() {
            List<Insight> insights = generateInsights();
            Insight lead = insights.getFirst();

            Map<MetricDirection, Long> distribution =
                new EnumMap<>(MetricDirection.class);

            for (MetricDirection direction : MetricDirection.values()) {
                distribution.put(direction, 0L);
            }

            for (Metric metric : metrics) {
                distribution.compute(
                    metric.direction(),
                    (key, value) -> value + 1
                );
            }

            return """
                BUSINESS STORY
                ==============
                Headline: %s

                What happened:
                %s

                Why it matters:
                %s

                What should happen next:
                %s

                Portfolio signal:
                Improving: %d
                Declining: %d
                Stable: %d
                """.formatted(
                    lead.observation(),
                    lead.observation(),
                    lead.implication(),
                    lead.action(),
                    distribution.get(MetricDirection.IMPROVING),
                    distribution.get(MetricDirection.DECLINING),
                    distribution.get(MetricDirection.STABLE)
                );
        }

        void printDecisionBrief() {
            System.out.println(createExecutiveNarrative());
            System.out.println("ACTIONABLE INSIGHTS");
            System.out.println("===================");

            for (Insight insight : generateInsights()) {
                Metric metric = insight.metric();

                System.out.printf(
                    "%n[%s] %s%n",
                    insight.priority(),
                    metric.name()
                );
                System.out.printf(
                    "Change: %.2f%%%n",
                    metric.changePercent()
                );
                System.out.printf(
                    "Target gap: %.2f%s%n",
                    metric.targetGap(),
                    metric.unit()
                );
                System.out.println(
                    "Implication: " + insight.implication()
                );
                System.out.println(
                    "Action: " + insight.action()
                );
            }
        }
    }

    public static void main(String[] args) {
        List<Metric> metrics = List.of(
            new Metric("Revenue", 12.4, 10.8, 12.0, "M"),
            new Metric("Conversion Rate", 4.7, 5.3, 5.0, "%"),
            new Metric("Customer Retention", 91.0, 88.0, 90.0, "%"),
            new Metric("Support Cost", 1.9, 1.6, 1.7, "M"),
            new Metric("Gross Margin", 37.5, 35.8, 36.0, "%")
        );

        StoryPolicy policy = new ExecutiveStoryPolicy();
        StoryService service = new StoryService(metrics, policy);

        service.printDecisionBrief();
    }
}
