import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

/*
 * Funnel Analysis enterprise model.
 *
 * The program separates event capture, customer state, segment analysis,
 * timing analysis, and conversion policy. This keeps customer-journey
 * data independent from the service that evaluates the funnel.
 */
public class FunnelAnalysis {

    enum FunnelStage {
        LANDING("Visited Landing Page"),
        PRODUCT("Viewed Product"),
        CART("Added to Cart"),
        CHECKOUT("Started Checkout"),
        PURCHASE("Purchased");

        private final String label;

        FunnelStage(String label) {
            this.label = label;
        }

        public String label() {
            return label;
        }
    }

    record FunnelEvent(FunnelStage stage, int minute) {
        FunnelEvent {
            Objects.requireNonNull(stage, "stage");

            if (minute < 0) {
                throw new IllegalArgumentException(
                    "Event minute cannot be negative."
                );
            }
        }
    }

    static final class CustomerJourney {
        private final String customerId;
        private final String segment;
        private final List<FunnelEvent> events = new ArrayList<>();
        private final double revenue;

        CustomerJourney(String customerId, String segment, double revenue) {
            if (customerId == null || customerId.isBlank()) {
                throw new IllegalArgumentException(
                    "Customer ID is required."
                );
            }

            if (segment == null || segment.isBlank()) {
                throw new IllegalArgumentException(
                    "Customer segment is required."
                );
            }

            if (!Double.isFinite(revenue) || revenue < 0) {
                throw new IllegalArgumentException(
                    "Revenue must be finite and non-negative."
                );
            }

            this.customerId = customerId;
            this.segment = segment;
            this.revenue = revenue;
        }

        void addEvent(FunnelStage stage, int minute) {
            Objects.requireNonNull(stage, "stage");

            if (!events.isEmpty()) {
                FunnelEvent previous = events.get(events.size() - 1);

                if (stage.ordinal() <= previous.stage().ordinal()) {
                    throw new IllegalStateException(
                        "Funnel stages must progress forward."
                    );
                }

                if (minute < previous.minute()) {
                    throw new IllegalStateException(
                        "Event time cannot move backwards."
                    );
                }
            }

            events.add(new FunnelEvent(stage, minute));
        }

        boolean reached(FunnelStage stage) {
            return events.stream()
                .anyMatch(event -> event.stage() == stage);
        }

        Optional<Integer> timestamp(FunnelStage stage) {
            return events.stream()
                .filter(event -> event.stage() == stage)
                .map(FunnelEvent::minute)
                .findFirst();
        }

        boolean converted() {
            return reached(FunnelStage.PURCHASE);
        }

        String customerId() {
            return customerId;
        }

        String segment() {
            return segment;
        }

        double revenue() {
            return revenue;
        }

        List<FunnelEvent> events() {
            return List.copyOf(events);
        }
    }

    record StageMetric(
        FunnelStage stage,
        int users,
        Double conversionFromPrevious,
        Double conversionFromEntry,
        Double dropOff
    ) {}

    record SegmentMetric(
        String segment,
        int users,
        int converters,
        double conversionRate,
        double revenue
    ) {}

    interface FunnelPolicy {
        boolean accepts(CustomerJourney journey);

        String policyName();
    }

    static final class CompletedJourneyPolicy implements FunnelPolicy {
        @Override
        public boolean accepts(CustomerJourney journey) {
            return journey.converted();
        }

        @Override
        public String policyName() {
            return "Completed Purchase";
        }
    }

    static final class FunnelService {
        private final List<CustomerJourney> journeys;
        private final List<FunnelStage> stages;
        private final FunnelPolicy conversionPolicy;

        FunnelService(
            List<CustomerJourney> journeys,
            FunnelPolicy conversionPolicy
        ) {
            this.journeys = List.copyOf(journeys);
            this.stages = List.of(FunnelStage.values());
            this.conversionPolicy = Objects.requireNonNull(
                conversionPolicy,
                "conversionPolicy"
            );

            validateUniqueCustomers();
        }

        private void validateUniqueCustomers() {
            long unique = journeys.stream()
                .map(CustomerJourney::customerId)
                .distinct()
                .count();

            if (unique != journeys.size()) {
                throw new IllegalArgumentException(
                    "Customer IDs must be unique."
                );
            }
        }

        private List<CustomerJourney> usersAt(FunnelStage stage) {
            return journeys.stream()
                .filter(journey -> journey.reached(stage))
                .toList();
        }

        List<StageMetric> stageMetrics() {
            List<StageMetric> result = new ArrayList<>();

            int entryUsers = journeys.size();
            Integer previousUsers = null;

            for (FunnelStage stage : stages) {
                int currentUsers = usersAt(stage).size();

                Double previousConversion = null;
                Double dropOff = null;

                if (previousUsers != null) {
                    previousConversion = previousUsers == 0
                        ? 0.0
                        : (double) currentUsers / previousUsers;

                    dropOff = 1.0 - previousConversion;
                }

                double entryConversion = entryUsers == 0
                    ? 0.0
                    : (double) currentUsers / entryUsers;

                result.add(
                    new StageMetric(
                        stage,
                        currentUsers,
                        previousConversion,
                        entryConversion,
                        dropOff
                    )
                );

                previousUsers = currentUsers;
            }

            return result;
        }

        List<SegmentMetric> segmentMetrics() {
            Map<String, List<CustomerJourney>> groups =
                journeys.stream()
                    .collect(
                        Collectors.groupingBy(
                            CustomerJourney::segment,
                            LinkedHashMap::new,
                            Collectors.toList()
                        )
                    );

            return groups.entrySet()
                .stream()
                .map(entry -> {
                    String segment = entry.getKey();
                    List<CustomerJourney> segmentJourneys = entry.getValue();

                    List<CustomerJourney> converters =
                        segmentJourneys.stream()
                            .filter(conversionPolicy::accepts)
                            .toList();

                    double revenue = converters.stream()
                        .mapToDouble(CustomerJourney::revenue)
                        .sum();

                    double rate = segmentJourneys.isEmpty()
                        ? 0.0
                        : (double) converters.size() /
                          segmentJourneys.size();

                    return new SegmentMetric(
                        segment,
                        segmentJourneys.size(),
                        converters.size(),
                        rate,
                        revenue
                    );
                })
                .sorted(Comparator.comparing(SegmentMetric::segment))
                .toList();
        }

        Optional<StageMetric> largestDropOff() {
            return stageMetrics().stream()
                .filter(metric -> metric.dropOff() != null)
                .max(
                    Comparator.comparingDouble(StageMetric::dropOff)
                );
        }

        OptionalDoubleResult medianTimeToConversion() {
            List<Integer> durations = journeys.stream()
                .filter(CustomerJourney::converted)
                .map(
                    journey -> {
                        int start = journey
                            .timestamp(FunnelStage.LANDING)
                            .orElseThrow();
                        int end = journey
                            .timestamp(FunnelStage.PURCHASE)
                            .orElseThrow();

                        return end - start;
                    }
                )
                .sorted()
                .toList();

            if (durations.isEmpty()) {
                return new OptionalDoubleResult(null);
            }

            int middle = durations.size() / 2;

            if (durations.size() % 2 == 0) {
                return new OptionalDoubleResult(
                    (durations.get(middle - 1) + durations.get(middle)) / 2.0
                );
            }

            return new OptionalDoubleResult(
                durations.get(middle).doubleValue()
            );
        }

        Map<String, Long> pathDistribution() {
            return journeys.stream()
                .map(this::path)
                .collect(
                    Collectors.groupingBy(
                        Function.identity(),
                        LinkedHashMap::new,
                        Collectors.counting()
                    )
                );
        }

        private String path(CustomerJourney journey) {
            return journey.events()
                .stream()
                .map(event -> event.stage().label())
                .collect(Collectors.joining(" -> "));
        }

        void printReport() {
            System.out.println("\nFUNNEL ANALYSIS");
            System.out.println("=".repeat(78));

            for (StageMetric metric : stageMetrics()) {
                String previous = metric.conversionFromPrevious() == null
                    ? "n/a"
                    : String.format(
                        "%.1f%%",
                        metric.conversionFromPrevious() * 100
                    );

                String dropOff = metric.dropOff() == null
                    ? "n/a"
                    : String.format(
                        "%.1f%%",
                        metric.dropOff() * 100
                    );

                System.out.printf(
                    "%-24s users=%-3d previous=%-7s entry=%.1f%% dropOff=%s%n",
                    metric.stage().label(),
                    metric.users(),
                    previous,
                    metric.conversionFromEntry() * 100,
                    dropOff
                );
            }

            largestDropOff().ifPresent(metric ->
                System.out.printf(
                    "%nLargest drop-off: %s (%.1f%%)%n",
                    metric.stage().label(),
                    metric.dropOff() * 100
                )
            );

            System.out.println("\nSEGMENT PERFORMANCE");
            System.out.println("-".repeat(78));

            for (SegmentMetric metric : segmentMetrics()) {
                System.out.printf(
                    "%-10s users=%-3d converters=%-3d conversion=%.1f%% revenue=$%.2f%n",
                    metric.segment(),
                    metric.users(),
                    metric.converters(),
                    metric.conversionRate() * 100,
                    metric.revenue()
                );
            }

            System.out.println("\nCONVERSION TIMING");
            System.out.println("-".repeat(78));

            medianTimeToConversion().value().ifPresentOrElse(
                median -> System.out.printf(
                    "Median time to purchase: %.1f minutes%n",
                    median
                ),
                () -> System.out.println(
                    "No completed journeys are available."
                )
            );

            System.out.println("\nPATH DISTRIBUTION");
            System.out.println("-".repeat(78));

            pathDistribution().forEach(
                (path, count) ->
                    System.out.printf("%d  %s%n", count, path)
            );

            System.out.println(
                "\nConversion policy: " +
                conversionPolicy.policyName()
            );
        }
    }

    static final class OptionalDoubleResult {
        private final Double value;

        OptionalDoubleResult(Double value) {
            this.value = value;
        }

        Optional<Double> value() {
            return Optional.ofNullable(value);
        }
    }

    static CustomerJourney journey(
        String id,
        String segment,
        double revenue,
        Object[][] events
    ) {
        CustomerJourney journey =
            new CustomerJourney(id, segment, revenue);

        for (Object[] event : events) {
            journey.addEvent(
                (FunnelStage) event[0],
                (Integer) event[1]
            );
        }

        return journey;
    }

    public static void main(String[] args) {
        List<CustomerJourney> journeys = new ArrayList<>();

        journeys.add(
            journey(
                "C001",
                "mobile",
                129.0,
                new Object[][] {
                    {FunnelStage.LANDING, 0},
                    {FunnelStage.PRODUCT, 4},
                    {FunnelStage.CART, 9},
                    {FunnelStage.CHECKOUT, 15},
                    {FunnelStage.PURCHASE, 23}
                }
            )
        );

        journeys.add(
            journey(
                "C002",
                "mobile",
                0.0,
                new Object[][] {
                    {FunnelStage.LANDING, 1},
                    {FunnelStage.PRODUCT, 6},
                    {FunnelStage.CART, 12},
                    {FunnelStage.CHECKOUT, 21}
                }
            )
        );

        journeys.add(
            journey(
                "C003",
                "desktop",
                249.0,
                new Object[][] {
                    {FunnelStage.LANDING, 2},
                    {FunnelStage.PRODUCT, 5},
                    {FunnelStage.CART, 14},
                    {FunnelStage.CHECKOUT, 20},
                    {FunnelStage.PURCHASE, 32}
                }
            )
        );

        journeys.add(
            journey(
                "C004",
                "desktop",
                0.0,
                new Object[][] {
                    {FunnelStage.LANDING, 3},
                    {FunnelStage.PRODUCT, 8}
                }
            )
        );

        journeys.add(
            journey(
                "C005",
                "mobile",
                0.0,
                new Object[][] {
                    {FunnelStage.LANDING, 10},
                    {FunnelStage.PRODUCT, 14},
                    {FunnelStage.CART, 19}
                }
            )
        );

        journeys.add(
            journey(
                "C006",
                "desktop",
                89.0,
                new Object[][] {
                    {FunnelStage.LANDING, 11},
                    {FunnelStage.PRODUCT, 16},
                    {FunnelStage.CART, 22},
                    {FunnelStage.CHECKOUT, 30},
                    {FunnelStage.PURCHASE, 41}
                }
            )
        );

        journeys.add(
            journey(
                "C007",
                "tablet",
                0.0,
                new Object[][] {
                    {FunnelStage.LANDING, 13},
                    {FunnelStage.PRODUCT, 18},
                    {FunnelStage.CART, 26},
                    {FunnelStage.CHECKOUT, 40}
                }
            )
        );

        journeys.add(
            journey(
                "C008",
                "tablet",
                0.0,
                new Object[][] {
                    {FunnelStage.LANDING, 15},
                    {FunnelStage.PRODUCT, 21}
                }
            )
        );

        journeys.add(
            journey(
                "C009",
                "mobile",
                159.0,
                new Object[][] {
                    {FunnelStage.LANDING, 18},
                    {FunnelStage.PRODUCT, 23},
                    {FunnelStage.CART, 31},
                    {FunnelStage.CHECKOUT, 37},
                    {FunnelStage.PURCHASE, 48}
                }
            )
        );

        journeys.add(
            journey(
                "C010",
                "desktop",
                0.0,
                new Object[][] {
                    {FunnelStage.LANDING, 20},
                    {FunnelStage.PRODUCT, 24},
                    {FunnelStage.CART, 30}
                }
            )
        );

        FunnelService service =
            new FunnelService(
                journeys,
                new CompletedJourneyPolicy()
            );

        service.printReport();

        System.out.println("\nVALIDATION CASE");
        System.out.println("=".repeat(78));

        try {
            journey(
                "INVALID",
                "mobile",
                0.0,
                new Object[][] {
                    {FunnelStage.PRODUCT, 50},
                    {FunnelStage.LANDING, 55}
                }
            );
        } catch (IllegalStateException error) {
            System.out.println(
                "Rejected invalid journey: " + error.getMessage()
            );
        }
    }
}
