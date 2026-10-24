import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class BusinessChartGovernance {

    enum ChartType {
        BAR,
        LINE,
        SCATTER,
        HISTOGRAM,
        BOX
    }

    enum ReviewState {
        ACCEPTED,
        REJECTED
    }

    record SalesRecord(
        String month,
        String region,
        double revenue,
        int orders,
        double marketingSpend,
        double deliveryDays
    ) {
        SalesRecord {
            Objects.requireNonNull(month, "month is required");
            Objects.requireNonNull(region, "region is required");

            if (month.isBlank() || region.isBlank()) {
                throw new ChartValidationException(
                    "Month and region cannot be blank."
                );
            }

            if (revenue < 0 ||
                orders < 0 ||
                marketingSpend < 0 ||
                deliveryDays < 0) {
                throw new ChartValidationException(
                    "Business measures cannot be negative."
                );
            }
        }
    }

    record ChartDecision(
        ChartType type,
        ReviewState state,
        String reason
    ) {}

    record BoxStatistics(
        double minimum,
        double q1,
        double median,
        double q3,
        double maximum,
        List<Double> outliers
    ) {}

    static class ChartValidationException
        extends RuntimeException {

        ChartValidationException(String message) {
            super(message);
        }
    }

    interface ChartPolicy {
        ChartDecision evaluate(List<SalesRecord> records);
    }

    static final class MinimumObservationPolicy
        implements ChartPolicy {

        private final ChartType type;
        private final int minimum;

        MinimumObservationPolicy(
            ChartType type,
            int minimum
        ) {
            this.type = type;
            this.minimum = minimum;
        }

        @Override
        public ChartDecision evaluate(
            List<SalesRecord> records
        ) {
            if (records.size() < minimum) {
                return new ChartDecision(
                    type,
                    ReviewState.REJECTED,
                    "At least " + minimum
                        + " observations are required."
                );
            }

            return new ChartDecision(
                type,
                ReviewState.ACCEPTED,
                "Observation count is valid."
            );
        }
    }

    static final class ChartService {
        private final Map<ChartType, ChartPolicy> policies =
            new EnumMap<>(ChartType.class);

        ChartService() {
            policies.put(
                ChartType.BAR,
                new MinimumObservationPolicy(ChartType.BAR, 1)
            );
            policies.put(
                ChartType.LINE,
                new MinimumObservationPolicy(ChartType.LINE, 2)
            );
            policies.put(
                ChartType.SCATTER,
                new MinimumObservationPolicy(ChartType.SCATTER, 2)
            );
            policies.put(
                ChartType.HISTOGRAM,
                new MinimumObservationPolicy(ChartType.HISTOGRAM, 2)
            );
            policies.put(
                ChartType.BOX,
                new MinimumObservationPolicy(ChartType.BOX, 5)
            );
        }

        List<ChartDecision> evaluate(
            List<SalesRecord> records
        ) {
            if (records == null || records.isEmpty()) {
                throw new ChartValidationException(
                    "Chart service requires records."
                );
            }

            List<ChartDecision> decisions = new ArrayList<>();

            for (ChartType type : ChartType.values()) {
                decisions.add(
                    policies.get(type).evaluate(records)
                );
            }

            return List.copyOf(decisions);
        }

        Map<String, Double> aggregate(
            List<SalesRecord> records,
            java.util.function.Function<SalesRecord, String> key
        ) {
            Map<String, Double> result =
                new LinkedHashMap<>();

            records.stream()
                .collect(
                    java.util.stream.Collectors.groupingBy(
                        key,
                        LinkedHashMap::new,
                        java.util.stream.Collectors.summingDouble(
                            SalesRecord::revenue
                        )
                    )
                )
                .entrySet()
                .stream()
                .sorted(
                    Map.Entry.comparingByKey()
                )
                .forEach(
                    entry -> result.put(
                        entry.getKey(),
                        entry.getValue()
                    )
                );

            return result;
        }

        double correlation(List<SalesRecord> records) {
            if (records.size() < 2) {
                throw new ChartValidationException(
                    "Scatter analysis requires two observations."
                );
            }

            double xMean = records.stream()
                .mapToDouble(SalesRecord::marketingSpend)
                .average()
                .orElseThrow();

            double yMean = records.stream()
                .mapToDouble(SalesRecord::revenue)
                .average()
                .orElseThrow();

            double numerator = 0;
            double xVariance = 0;
            double yVariance = 0;

            for (SalesRecord record : records) {
                double dx = record.marketingSpend() - xMean;
                double dy = record.revenue() - yMean;

                numerator += dx * dy;
                xVariance += dx * dx;
                yVariance += dy * dy;
            }

            double denominator =
                Math.sqrt(xVariance * yVariance);

            if (denominator == 0) {
                throw new ChartValidationException(
                    "Correlation is undefined for zero variance."
                );
            }

            return numerator / denominator;
        }

        BoxStatistics boxStatistics(
            List<SalesRecord> records
        ) {
            List<Double> values = records.stream()
                .map(SalesRecord::deliveryDays)
                .sorted()
                .toList();

            if (values.isEmpty()) {
                throw new ChartValidationException(
                    "Box statistics require data."
                );
            }

            double q1 = percentile(values, 0.25);
            double median = percentile(values, 0.50);
            double q3 = percentile(values, 0.75);

            double iqr = q3 - q1;
            double lowerFence = q1 - 1.5 * iqr;
            double upperFence = q3 + 1.5 * iqr;

            List<Double> outliers = values.stream()
                .filter(value ->
                    value < lowerFence || value > upperFence
                )
                .toList();

            List<Double> regular = values.stream()
                .filter(value ->
                    value >= lowerFence && value <= upperFence
                )
                .toList();

            return new BoxStatistics(
                regular.stream()
                    .min(Comparator.naturalOrder())
                    .orElseThrow(),
                q1,
                median,
                q3,
                regular.stream()
                    .max(Comparator.naturalOrder())
                    .orElseThrow(),
                outliers
            );
        }

        private double percentile(
            List<Double> sorted,
            double fraction
        ) {
            double position =
                (sorted.size() - 1) * fraction;

            int lower = (int) Math.floor(position);
            int upper = (int) Math.ceil(position);

            if (lower == upper) {
                return sorted.get(lower);
            }

            double weight = position - lower;

            return sorted.get(lower) * (1 - weight)
                + sorted.get(upper) * weight;
        }

        Map<Double, Long> histogram(
            List<SalesRecord> records,
            double width
        ) {
            if (width <= 0) {
                throw new ChartValidationException(
                    "Histogram width must be positive."
                );
            }

            return records.stream()
                .map(SalesRecord::revenue)
                .collect(
                    java.util.stream.Collectors.groupingBy(
                        value -> Math.floor(value / width) * width,
                        java.util.TreeMap::new,
                        java.util.stream.Collectors.counting()
                    )
                );
        }
    }

    private static List<SalesRecord> sampleData() {
        return List.of(
            new SalesRecord("2026-01", "North", 72000, 410, 11000, 3.2),
            new SalesRecord("2026-01", "South", 64000, 390, 9500, 4.1),
            new SalesRecord("2026-01", "West", 81000, 450, 12500, 2.8),
            new SalesRecord("2026-02", "North", 76000, 425, 11500, 3.4),
            new SalesRecord("2026-02", "South", 68000, 402, 10200, 4.0),
            new SalesRecord("2026-02", "West", 87000, 478, 13100, 2.6),
            new SalesRecord("2026-03", "North", 83000, 440, 12000, 3.6),
            new SalesRecord("2026-03", "South", 70000, 410, 10500, 4.4),
            new SalesRecord("2026-03", "West", 92000, 495, 13800, 2.9),
            new SalesRecord("2026-04", "North", 88000, 462, 12700, 3.5),
            new SalesRecord("2026-04", "South", 73000, 421, 10800, 4.2),
            new SalesRecord("2026-04", "West", 97000, 510, 14500, 2.7),
            new SalesRecord("2026-05", "North", 91000, 475, 13000, 3.8),
            new SalesRecord("2026-05", "South", 76000, 430, 11100, 4.5),
            new SalesRecord("2026-05", "West", 103000, 535, 15100, 2.5),
            new SalesRecord("2026-06", "North", 96000, 490, 13600, 3.7),
            new SalesRecord("2026-06", "South", 79000, 442, 11400, 4.3),
            new SalesRecord("2026-06", "West", 108000, 552, 15700, 2.8),
            new SalesRecord("2026-06", "West", 155000, 600, 22000, 9.5)
        );
    }

    public static void main(String[] args) {
        try {
            List<SalesRecord> records = sampleData();
            ChartService service = new ChartService();

            System.out.println("BUSINESS CHART GOVERNANCE\n");

            System.out.println("BAR CHART - REVENUE BY REGION");
            service.aggregate(
                records,
                SalesRecord::region
            ).forEach(
                (region, revenue) ->
                    System.out.printf(
                        "%-8s %.0f%n",
                        region,
                        revenue
                    )
            );

            System.out.println("\nLINE CHART - MONTHLY REVENUE");
            service.aggregate(
                records,
                SalesRecord::month
            ).forEach(
                (month, revenue) ->
                    System.out.printf(
                        "%s -> %.0f%n",
                        month,
                        revenue
                    )
            );

            System.out.printf(
                "%nSCATTER CORRELATION: %.3f%n",
                service.correlation(records)
            );

            System.out.println("\nHISTOGRAM");
            service.histogram(records, 20000)
                .forEach(
                    (lowerBound, count) ->
                        System.out.printf(
                            "%.0f-%.0f : %d%n",
                            lowerBound,
                            lowerBound + 20000,
                            count
                        )
                );

            BoxStatistics box =
                service.boxStatistics(records);

            System.out.println("\nBOX PLOT");
            System.out.println("Minimum: " + box.minimum());
            System.out.println("Q1: " + box.q1());
            System.out.println("Median: " + box.median());
            System.out.println("Q3: " + box.q3());
            System.out.println("Maximum: " + box.maximum());
            System.out.println("Outliers: " + box.outliers());

            System.out.println("\nCHART POLICY DECISIONS");
            service.evaluate(records)
                .forEach(System.out::println);

        } catch (ChartValidationException error) {
            System.err.println(
                "Validation failure: " + error.getMessage()
            );
            System.exit(2);
        }
    }
}
