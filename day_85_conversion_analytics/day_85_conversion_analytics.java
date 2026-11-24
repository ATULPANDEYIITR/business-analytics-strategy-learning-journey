import java.time.Instant;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;

/*
 * Conversion Analytics and Funnel Optimization
 * Java 17
 *
 * Enterprise-oriented conversion measurement system.
 *
 * Components:
 * - Immutable event records
 * - Event validation and ingestion
 * - Customer journey reconstruction
 * - Funnel analysis
 * - Channel attribution
 * - Cohort analysis
 * - Experiment evaluation
 * - Optimization policies
 * - Analytics reporting
 */

public class ConversionAnalytics {

    // -----------------------------------------------------
    // 1. DOMAIN TYPES
    // -----------------------------------------------------

    enum FunnelStage {
        VISIT,
        PRODUCT_VIEW,
        ADD_TO_CART,
        CHECKOUT,
        PURCHASE
    }

    enum Priority {
        LOW,
        MEDIUM,
        HIGH
    }

    record AnalyticsEvent(
        String eventId,
        String userId,
        FunnelStage stage,
        Instant timestamp,
        String channel,
        String campaign,
        String experiment,
        double revenue
    ) {
        AnalyticsEvent {
            Objects.requireNonNull(eventId);
            Objects.requireNonNull(userId);
            Objects.requireNonNull(stage);
            Objects.requireNonNull(timestamp);
            Objects.requireNonNull(channel);
            Objects.requireNonNull(campaign);

            experiment = experiment == null
                ? "control"
                : experiment;

            if (
                eventId.isBlank() ||
                userId.isBlank() ||
                channel.isBlank() ||
                campaign.isBlank()
            ) {
                throw new IllegalArgumentException(
                    "Required event fields cannot be empty"
                );
            }

            if (!Double.isFinite(revenue) || revenue < 0) {
                throw new IllegalArgumentException(
                    "Invalid revenue"
                );
            }

            if (stage != FunnelStage.PURCHASE && revenue != 0) {
                throw new IllegalArgumentException(
                    "Revenue is permitted only for purchase events"
                );
            }
        }
    }

    record FunnelStep(
        FunnelStage stage,
        long users,
        long previousUsers,
        double conversionRate,
        double dropOffRate
    ) {}

    record FunnelReport(
        long visitors,
        long conversions,
        double overallConversionRate,
        List<FunnelStep> steps
    ) {
        FunnelReport {
            steps = List.copyOf(steps);
        }
    }

    record ChannelReport(
        String channel,
        long visitors,
        long conversions,
        double conversionRate,
        double revenue,
        double revenuePerVisitor
    ) {}

    record ExperimentResult(
        double controlRate,
        double treatmentRate,
        double absoluteLift,
        double relativeLift,
        double zScore,
        double pValue,
        boolean significant
    ) {}

    record OptimizationAction(
        String stage,
        Priority priority,
        String recommendation
    ) {}


    // -----------------------------------------------------
    // 2. EVENT STORE
    // -----------------------------------------------------

    static class EventStore {
        private final List<AnalyticsEvent> events =
            new ArrayList<>();

        private final Set<String> eventIds =
            new HashSet<>();

        public synchronized boolean add(AnalyticsEvent event) {
            Objects.requireNonNull(event);

            if (!eventIds.add(event.eventId())) {
                return false;
            }

            events.add(event);

            return true;
        }

        public synchronized int addBatch(
            List<AnalyticsEvent> batch
        ) {
            Objects.requireNonNull(batch);

            Set<String> incoming = new HashSet<>();

            // Validate the entire batch before changing the store.
            for (AnalyticsEvent event : batch) {
                Objects.requireNonNull(event);

                if (
                    eventIds.contains(event.eventId()) ||
                    !incoming.add(event.eventId())
                ) {
                    throw new IllegalArgumentException(
                        "Duplicate event in batch"
                    );
                }
            }

            events.addAll(batch);
            eventIds.addAll(incoming);

            return batch.size();
        }

        public synchronized List<AnalyticsEvent> snapshot() {
            return List.copyOf(events);
        }

        public synchronized int size() {
            return events.size();
        }
    }


    // -----------------------------------------------------
    // 3. METRIC SERVICE
    // -----------------------------------------------------

    static class MetricService {

        public static double conversionRate(
            long converted,
            long eligible
        ) {
            if (
                converted < 0 ||
                eligible < 0 ||
                converted > eligible
            ) {
                throw new IllegalArgumentException(
                    "Invalid conversion counts"
                );
            }

            return eligible == 0
                ? 0
                : 100.0 * converted / eligible;
        }

        public static double revenuePerVisitor(
            double revenue,
            long visitors
        ) {
            if (
                !Double.isFinite(revenue) ||
                revenue < 0 ||
                visitors < 0
            ) {
                throw new IllegalArgumentException(
                    "Invalid revenue metrics"
                );
            }

            return visitors == 0
                ? 0
                : revenue / visitors;
        }
    }


    // -----------------------------------------------------
    // 4. JOURNEY RECONSTRUCTION
    // -----------------------------------------------------

    static class UserJourney {
        private final Map<FunnelStage, Instant> firstEvents =
            new EnumMap<>(FunnelStage.class);

        void record(AnalyticsEvent event) {
            firstEvents.merge(
                event.stage(),
                event.timestamp(),
                (existing, incoming) ->
                    existing.isBefore(incoming)
                        ? existing
                        : incoming
            );
        }

        int reachedStages() {
            Instant previous = null;
            int reached = 0;

            for (FunnelStage stage : FunnelStage.values()) {
                Instant current = firstEvents.get(stage);

                if (current == null) {
                    break;
                }

                if (
                    previous != null &&
                    current.isBefore(previous)
                ) {
                    break;
                }

                previous = current;
                reached++;
            }

            return reached;
        }

        boolean visited() {
            return firstEvents.containsKey(FunnelStage.VISIT);
        }
    }

    static Map<String, UserJourney> buildJourneys(
        List<AnalyticsEvent> events
    ) {
        Map<String, UserJourney> journeys = new HashMap<>();

        for (AnalyticsEvent event : events) {
            journeys.computeIfAbsent(
                event.userId(),
                key -> new UserJourney()
            ).record(event);
        }

        return journeys;
    }


    // -----------------------------------------------------
    // 5. FUNNEL ANALYTICS SERVICE
    // -----------------------------------------------------

    static class FunnelAnalyticsService {

        public FunnelReport analyze(
            List<AnalyticsEvent> events
        ) {
            Map<String, UserJourney> journeys =
                buildJourneys(events);

            List<UserJourney> visitors = journeys.values()
                .stream()
                .filter(UserJourney::visited)
                .toList();

            long totalVisitors = visitors.size();

            long previous = totalVisitors;

            List<FunnelStep> steps = new ArrayList<>();

            for (FunnelStage stage : FunnelStage.values()) {
                final int requiredStages =
                    stage.ordinal() + 1;

                long reached = visitors.stream()
                    .filter(
                        journey ->
                            journey.reachedStages() >= requiredStages
                    )
                    .count();

                double rate = MetricService.conversionRate(
                    reached,
                    previous
                );

                steps.add(
                    new FunnelStep(
                        stage,
                        reached,
                        previous,
                        rate,
                        previous == 0 ? 0 : 100 - rate
                    )
                );

                previous = reached;
            }

            long conversions = steps.get(
                steps.size() - 1
            ).users();

            return new FunnelReport(
                totalVisitors,
                conversions,
                MetricService.conversionRate(
                    conversions,
                    totalVisitors
                ),
                steps
            );
        }
    }


    // -----------------------------------------------------
    // 6. ATTRIBUTION SERVICE
    // -----------------------------------------------------

    static class ChannelAnalyticsService {

        private static class ChannelAccumulator {
            Set<String> visitors = new HashSet<>();
            Set<String> buyers = new HashSet<>();
            double revenue = 0;
        }

        public List<ChannelReport> analyze(
            List<AnalyticsEvent> events
        ) {
            Map<String, ChannelAccumulator> channels =
                new TreeMap<>();

            for (AnalyticsEvent event : events) {
                ChannelAccumulator channel =
                    channels.computeIfAbsent(
                        event.channel(),
                        key -> new ChannelAccumulator()
                    );

                if (event.stage() == FunnelStage.VISIT) {
                    channel.visitors.add(event.userId());
                }

                if (event.stage() == FunnelStage.PURCHASE) {
                    channel.buyers.add(event.userId());
                    channel.revenue += event.revenue();
                }
            }

            List<ChannelReport> reports = new ArrayList<>();

            for (var entry : channels.entrySet()) {
                String name = entry.getKey();
                ChannelAccumulator data = entry.getValue();

                long visitors = data.visitors.size();

                long conversions = data.buyers.stream()
                    .filter(data.visitors::contains)
                    .count();

                reports.add(
                    new ChannelReport(
                        name,
                        visitors,
                        conversions,
                        MetricService.conversionRate(
                            conversions,
                            visitors
                        ),
                        data.revenue,
                        MetricService.revenuePerVisitor(
                            data.revenue,
                            visitors
                        )
                    )
                );
            }

            return List.copyOf(reports);
        }
    }


    // -----------------------------------------------------
    // 7. COHORT ANALYTICS
    // -----------------------------------------------------

    static class CohortAnalyticsService {

        public Map<YearMonth, Map<String, Double>> analyze(
            List<AnalyticsEvent> events
        ) {
            Map<String, Instant> firstVisit =
                new HashMap<>();

            Set<String> buyers = new HashSet<>();

            for (AnalyticsEvent event : events) {
                if (event.stage() == FunnelStage.VISIT) {
                    firstVisit.merge(
                        event.userId(),
                        event.timestamp(),
                        (a, b) -> a.isBefore(b) ? a : b
                    );
                }

                if (event.stage() == FunnelStage.PURCHASE) {
                    buyers.add(event.userId());
                }
            }

            Map<YearMonth, Set<String>> cohorts =
                new TreeMap<>();

            firstVisit.forEach((userId, timestamp) -> {
                YearMonth month = YearMonth.from(
                    timestamp.atZone(
                        java.time.ZoneOffset.UTC
                    )
                );

                cohorts.computeIfAbsent(
                    month,
                    key -> new HashSet<>()
                ).add(userId);
            });

            Map<YearMonth, Map<String, Double>> results =
                new LinkedHashMap<>();

            cohorts.forEach((month, users) -> {
                long conversions = users.stream()
                    .filter(buyers::contains)
                    .count();

                Map<String, Double> metrics = new LinkedHashMap<>();

                metrics.put("visitors", (double) users.size());
                metrics.put("conversions", (double) conversions);
                metrics.put(
                    "conversionRate",
                    MetricService.conversionRate(
                        conversions,
                        users.size()
                    )
                );

                results.put(
                    month,
                    Collections.unmodifiableMap(metrics)
                );
            });

            return Collections.unmodifiableMap(results);
        }
    }


    // -----------------------------------------------------
    // 8. EXPERIMENT SERVICE
    // -----------------------------------------------------

    static class ExperimentService {

        private static double normalCDF(double x) {
            return 0.5 * (
                1 + erf(x / Math.sqrt(2))
            );
        }

        private static double erf(double x) {
            double sign = x < 0 ? -1 : 1;
            double z = Math.abs(x);

            double t = 1.0 / (
                1.0 + 0.3275911 * z
            );

            double polynomial =
                (((((1.061405429 * t
                    - 1.453152027) * t
                    + 1.421413741) * t
                    - 0.284496736) * t
                    + 0.254829592) * t);

            return sign * (
                1 - polynomial * Math.exp(-z * z)
            );
        }

        public ExperimentResult evaluate(
            long controlConversions,
            long controlUsers,
            long treatmentConversions,
            long treatmentUsers
        ) {
            if (
                controlUsers <= 0 ||
                treatmentUsers <= 0 ||
                controlConversions < 0 ||
                treatmentConversions < 0 ||
                controlConversions > controlUsers ||
                treatmentConversions > treatmentUsers
            ) {
                throw new IllegalArgumentException(
                    "Invalid experiment population"
                );
            }

            double p1 =
                (double) controlConversions / controlUsers;

            double p2 =
                (double) treatmentConversions / treatmentUsers;

            double pooled =
                (double) (
                    controlConversions + treatmentConversions
                ) / (controlUsers + treatmentUsers);

            double standardError = Math.sqrt(
                pooled * (1 - pooled) *
                (1.0 / controlUsers + 1.0 / treatmentUsers)
            );

            double z = standardError == 0
                ? 0
                : (p2 - p1) / standardError;

            double pValue = 2 * (
                1 - normalCDF(Math.abs(z))
            );

            return new ExperimentResult(
                p1 * 100,
                p2 * 100,
                (p2 - p1) * 100,
                p1 == 0 ? 0 : (p2 - p1) / p1 * 100,
                z,
                pValue,
                pValue < 0.05
            );
        }
    }


    // -----------------------------------------------------
    // 9. OPTIMIZATION POLICY
    // -----------------------------------------------------

    static class OptimizationPolicy {

        public List<OptimizationAction> evaluate(
            FunnelReport report
        ) {
            if (report.visitors() == 0) {
                return List.of(
                    new OptimizationAction(
                        "acquisition",
                        Priority.HIGH,
                        "Collect sufficient visitor data."
                    )
                );
            }

            FunnelStep weakest = report.steps()
                .stream()
                .max(
                    Comparator.comparingDouble(
                        FunnelStep::dropOffRate
                    )
                )
                .orElseThrow();

            List<OptimizationAction> actions =
                new ArrayList<>();

            if (weakest.dropOffRate() >= 40) {
                actions.add(
                    new OptimizationAction(
                        weakest.stage().name(),
                        Priority.HIGH,
                        "Investigate friction at this funnel stage."
                    )
                );
            }

            if (report.overallConversionRate() < 2) {
                actions.add(
                    new OptimizationAction(
                        "ACQUISITION",
                        Priority.HIGH,
                        "Evaluate traffic quality and landing-page relevance."
                    )
                );
            }

            if (actions.isEmpty()) {
                actions.add(
                    new OptimizationAction(
                        "ALL_STAGES",
                        Priority.MEDIUM,
                        "Run controlled tests and monitor performance."
                    )
                );
            }

            return List.copyOf(actions);
        }
    }


    // -----------------------------------------------------
    // 10. SAMPLE DATA
    // -----------------------------------------------------

    static List<AnalyticsEvent> sampleEvents() {
        List<AnalyticsEvent> events = new ArrayList<>();

        FunnelStage[][] journeys = {
            FunnelStage.values(),
            {
                FunnelStage.VISIT,
                FunnelStage.PRODUCT_VIEW,
                FunnelStage.ADD_TO_CART,
                FunnelStage.CHECKOUT
            },
            {
                FunnelStage.VISIT,
                FunnelStage.PRODUCT_VIEW,
                FunnelStage.ADD_TO_CART,
                FunnelStage.PURCHASE
            },
            {
                FunnelStage.VISIT,
                FunnelStage.PRODUCT_VIEW
            },
            FunnelStage.values(),
            {
                FunnelStage.VISIT,
                FunnelStage.PRODUCT_VIEW
            },
            FunnelStage.values(),
            {
                FunnelStage.VISIT,
                FunnelStage.PRODUCT_VIEW,
                FunnelStage.ADD_TO_CART
            },
            {FunnelStage.VISIT},
            FunnelStage.values()
        };

        String[] channels = {
            "organic", "paid", "organic", "social",
            "paid", "social", "organic", "paid",
            "referral", "organic"
        };

        double[] revenue = {
            2500, 0, 1800, 0, 3200,
            0, 1500, 0, 0, 4100
        };

        Instant base = Instant.parse(
            "2026-11-01T10:00:00Z"
        );

        for (int i = 0; i < journeys.length; i++) {
            for (int j = 0; j < journeys[i].length; j++) {
                FunnelStage stage = journeys[i][j];

                events.add(
                    new AnalyticsEvent(
                        "event-" + i + "-" + j,
                        "user-" + (i + 1),
                        stage,
                        base.plusSeconds(
                            i * 1200L + j * 300L
                        ),
                        channels[i],
                        channels[i] + "_campaign",
                        "control",
                        stage == FunnelStage.PURCHASE
                            ? revenue[i]
                            : 0
                    )
                );
            }
        }

        return List.copyOf(events);
    }


    // -----------------------------------------------------
    // 11. REPORTING
    // -----------------------------------------------------

    static void printReport(
        FunnelReport funnel,
        List<ChannelReport> channels,
        Map<YearMonth, Map<String, Double>> cohorts,
        ExperimentResult experiment,
        List<OptimizationAction> actions
    ) {
        System.out.println("\nCONVERSION FUNNEL");

        System.out.println(
            "Visitors: " + funnel.visitors()
        );

        System.out.println(
            "Conversions: " + funnel.conversions()
        );

        System.out.printf(
            "Overall conversion: %.2f%%%n",
            funnel.overallConversionRate()
        );

        System.out.println("\nSTAGE PERFORMANCE");

        funnel.steps().forEach(step ->
            System.out.printf(
                "%-15s Users: %d Conversion: %.2f%% Drop-off: %.2f%%%n",
                step.stage(),
                step.users(),
                step.conversionRate(),
                step.dropOffRate()
            )
        );

        System.out.println("\nCHANNEL PERFORMANCE");

        channels.forEach(channel ->
            System.out.printf(
                "%-12s Visitors: %d Buyers: %d Rate: %.2f%% Revenue: %.2f%n",
                channel.channel(),
                channel.visitors(),
                channel.conversions(),
                channel.conversionRate(),
                channel.revenue()
            )
        );

        System.out.println("\nCOHORT PERFORMANCE");
        cohorts.forEach((month, metrics) ->
            System.out.println(month + " " + metrics)
        );

        System.out.println("\nA/B TEST");
        System.out.println(experiment);

        System.out.println("\nOPTIMIZATION ACTIONS");
        actions.forEach(System.out::println);
    }


    // -----------------------------------------------------
    // 12. APPLICATION ENTRY POINT
    // -----------------------------------------------------

    public static void main(String[] args) {

        try {
            EventStore store = new EventStore();

            List<AnalyticsEvent> events = sampleEvents();

            store.addBatch(events);

            FunnelAnalyticsService funnelService =
                new FunnelAnalyticsService();

            ChannelAnalyticsService channelService =
                new ChannelAnalyticsService();

            CohortAnalyticsService cohortService =
                new CohortAnalyticsService();

            ExperimentService experimentService =
                new ExperimentService();

            OptimizationPolicy optimizationPolicy =
                new OptimizationPolicy();

            List<AnalyticsEvent> snapshot = store.snapshot();

            FunnelReport funnel =
                funnelService.analyze(snapshot);

            List<ChannelReport> channels =
                channelService.analyze(snapshot);

            Map<YearMonth, Map<String, Double>> cohorts =
                cohortService.analyze(snapshot);

            ExperimentResult experiment =
                experimentService.evaluate(
                    120, 2000, 150, 2000
                );

            List<OptimizationAction> actions =
                optimizationPolicy.evaluate(funnel);

            printReport(
                funnel,
                channels,
                cohorts,
                experiment,
                actions
            );

            // Enterprise integrity checks.
            if (
                funnel.visitors() != 10 ||
                funnel.conversions() != 4
            ) {
                throw new IllegalStateException(
                    "Unexpected funnel results"
                );
            }

            if (store.add(events.get(0))) {
                throw new IllegalStateException(
                    "Duplicate ingestion was not rejected"
                );
            }

            if (
                MetricService.conversionRate(25, 100) != 25.0
            ) {
                throw new IllegalStateException(
                    "Metric validation failed"
                );
            }

            try {
                MetricService.conversionRate(10, 5);

                throw new IllegalStateException(
                    "Invalid conversion counts were accepted"
                );

            } catch (IllegalArgumentException expected) {
                System.out.println(
                    "\nInvalid metric correctly rejected."
                );
            }

            System.out.println(
                "\nAll validation checks passed."
            );

        } catch (Exception error) {
            System.err.println(
                "Application failure: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
