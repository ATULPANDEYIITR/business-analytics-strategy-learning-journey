import java.util.ArrayList;
import java.util.Comparator;
import java.util.DoubleSummaryStatistics;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

public class ExploratoryDataAnalysis {

    enum Dimension {
        REGION,
        CATEGORY
    }

    enum AnomalyMethod {
        IQR,
        LOCAL_Z_SCORE
    }

    record Observation(
        String date,
        double value,
        String region,
        String category
    ) {
        Observation {
            Objects.requireNonNull(date);
            Objects.requireNonNull(region);
            Objects.requireNonNull(category);

            if (!Double.isFinite(value)) {
                throw new IllegalArgumentException(
                    "Observation value must be finite."
                );
            }

            if (date.isBlank() ||
                region.isBlank() ||
                category.isBlank()) {
                throw new IllegalArgumentException(
                    "Observation dimensions cannot be blank."
                );
            }
        }
    }

    record Statistics(
        long count,
        double mean,
        double median,
        double minimum,
        double maximum,
        double q1,
        double q3,
        double standardDeviation
    ) {
        double iqr() {
            return q3 - q1;
        }
    }

    record Anomaly(
        Observation observation,
        AnomalyMethod method,
        double score
    ) {}

    static final class AnalysisException extends RuntimeException {
        AnalysisException(String message) {
            super(message);
        }
    }

    static final class AnalysisService {

        private final List<Observation> observations;

        AnalysisService(List<Observation> observations) {
            if (observations == null || observations.isEmpty()) {
                throw new AnalysisException(
                    "EDA requires at least one observation."
                );
            }

            this.observations = List.copyOf(observations);
        }

        private List<Double> values() {
            return observations.stream()
                .map(Observation::value)
                .toList();
        }

        private double mean(List<Double> values) {
            return values.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow(() ->
                    new AnalysisException("No numeric observations."));
        }

        private double percentile(
            List<Double> source,
            double percentage
        ) {
            if (source.isEmpty()) {
                throw new AnalysisException(
                    "Cannot calculate percentile for empty data."
                );
            }

            List<Double> sorted = source.stream()
                .sorted()
                .toList();

            double position =
                (sorted.size() - 1) * percentage / 100.0;

            int lower = (int) Math.floor(position);
            int upper = (int) Math.ceil(position);

            if (lower == upper) {
                return sorted.get(lower);
            }

            double fraction = position - lower;

            return sorted.get(lower) +
                (sorted.get(upper) - sorted.get(lower)) *
                fraction;
        }

        private double standardDeviation(List<Double> values) {
            if (values.size() < 2) {
                return 0.0;
            }

            double average = mean(values);

            double variance = values.stream()
                .mapToDouble(
                    value -> Math.pow(value - average, 2)
                )
                .sum() / (values.size() - 1);

            return Math.sqrt(variance);
        }

        Statistics describe() {
            List<Double> data = values();
            DoubleSummaryStatistics summary =
                data.stream()
                    .mapToDouble(Double::doubleValue)
                    .summaryStatistics();

            return new Statistics(
                summary.getCount(),
                summary.getAverage(),
                percentile(data, 50),
                summary.getMin(),
                summary.getMax(),
                percentile(data, 25),
                percentile(data, 75),
                standardDeviation(data)
            );
        }

        Map<String, Double> meanBy(Dimension dimension) {
            Function<Observation, String> classifier =
                dimension == Dimension.REGION
                    ? Observation::region
                    : Observation::category;

            return observations.stream()
                .collect(
                    Collectors.groupingBy(
                        classifier,
                        Collectors.averagingDouble(
                            Observation::value
                        )
                    )
                );
        }

        List<Anomaly> detectIqrAnomalies() {
            List<Double> data = values();

            double q1 = percentile(data, 25);
            double q3 = percentile(data, 75);
            double iqr = q3 - q1;

            double lower = q1 - 1.5 * iqr;
            double upper = q3 + 1.5 * iqr;

            List<Anomaly> result = new ArrayList<>();

            for (Observation observation : observations) {
                if (observation.value() < lower ||
                    observation.value() > upper) {
                    double distance =
                        observation.value() < lower
                            ? lower - observation.value()
                            : observation.value() - upper;

                    result.add(
                        new Anomaly(
                            observation,
                            AnomalyMethod.IQR,
                            distance
                        )
                    );
                }
            }

            return result;
        }

        List<Anomaly> detectLocalAnomalies(int window) {
            if (window < 2) {
                throw new AnalysisException(
                    "Local anomaly window must be at least two."
                );
            }

            List<Anomaly> result = new ArrayList<>();

            for (int index = 0; index < observations.size(); index++) {
                int start = Math.max(0, index - window);
                int end = Math.min(
                    observations.size(),
                    index + window + 1
                );

                List<Double> neighborhood = new ArrayList<>();

                for (int candidate = start;
                     candidate < end;
                     candidate++) {

                    if (candidate != index) {
                        neighborhood.add(
                            observations.get(candidate).value()
                        );
                    }
                }

                if (neighborhood.size() < 2) {
                    continue;
                }

                double localMean = mean(neighborhood);
                double localStd = standardDeviation(neighborhood);

                if (localStd == 0.0) {
                    continue;
                }

                double score =
                    Math.abs(
                        observations.get(index).value() -
                        localMean
                    ) / localStd;

                if (score >= 2.5) {
                    result.add(
                        new Anomaly(
                            observations.get(index),
                            AnomalyMethod.LOCAL_Z_SCORE,
                            score
                        )
                    );
                }
            }

            return result;
        }

        Optional<String> highestMeanCategory() {
            return meanBy(Dimension.CATEGORY)
                .entrySet()
                .stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey);
        }

        Map<String, Double> dailyMeans() {
            return observations.stream()
                .collect(
                    Collectors.groupingBy(
                        Observation::date,
                        Collectors.averagingDouble(
                            Observation::value
                        )
                    )
                )
                .entrySet()
                .stream()
                .sorted(Map.Entry.comparingByKey())
                .collect(
                    Collectors.toMap(
                        Map.Entry::getKey,
                        Map.Entry::getValue,
                        (left, right) -> left,
                        java.util.LinkedHashMap::new
                    )
                );
        }

        double trendSlope() {
            List<Double> values =
                new ArrayList<>(dailyMeans().values());

            if (values.size() < 2) {
                throw new AnalysisException(
                    "Trend requires multiple daily observations."
                );
            }

            double xMean =
                (values.size() - 1) / 2.0;

            double yMean = mean(values);

            double numerator = 0.0;
            double denominator = 0.0;

            for (int index = 0; index < values.size(); index++) {
                double x = index;

                numerator +=
                    (x - xMean) *
                    (values.get(index) - yMean);

                denominator +=
                    Math.pow(x - xMean, 2);
            }

            return numerator / denominator;
        }
    }

    private static List<Observation> buildData() {
        List<Observation> data = new ArrayList<>();

        double[] north = {
            101, 104, 106, 109, 112, 114, 116, 118, 119, 121,
            123, 125, 127, 128, 130, 132, 134, 136, 138, 140,
            142, 145, 147, 149, 151, 154, 157, 159, 162, 220
        };

        double[] south = {
            165, 168, 170, 173, 176, 178, 181, 184, 186, 189,
            191, 194, 197, 199, 202, 205, 207, 210, 212, 215,
            217, 219, 222, 225, 228, 230, 233, 235, 238, 150
        };

        for (int index = 0; index < north.length; index++) {
            data.add(
                new Observation(
                    String.format("2026-09-%02d", index + 1),
                    north[index],
                    "North",
                    "Infrastructure"
                )
            );
        }

        for (int index = 0; index < south.length; index++) {
            data.add(
                new Observation(
                    String.format("2026-10-%02d", index + 1),
                    south[index],
                    "South",
                    "Security"
                )
            );
        }

        return data;
    }

    public static void main(String[] args) {
        AnalysisService service =
            new AnalysisService(buildData());

        Statistics statistics = service.describe();

        System.out.println("Exploratory Data Analysis");
        System.out.println("==========================");
        System.out.printf("Count: %.0f%n",
            (double) statistics.count());
        System.out.printf("Mean: %.3f%n",
            statistics.mean());
        System.out.printf("Median: %.3f%n",
            statistics.median());
        System.out.printf("Q1: %.3f%n",
            statistics.q1());
        System.out.printf("Q3: %.3f%n",
            statistics.q3());
        System.out.printf("IQR: %.3f%n",
            statistics.iqr());
        System.out.printf("Std Dev: %.3f%n",
            statistics.standardDeviation());

        System.out.println("\nRegional means");
        service.meanBy(Dimension.REGION)
            .forEach(
                (region, value) ->
                    System.out.printf(
                        "%s: %.3f%n",
                        region,
                        value
                    )
            );

        System.out.println("\nCategory means");
        service.meanBy(Dimension.CATEGORY)
            .forEach(
                (category, value) ->
                    System.out.printf(
                        "%s: %.3f%n",
                        category,
                        value
                    )
            );

        System.out.println("\nIQR anomalies");
        service.detectIqrAnomalies()
            .forEach(
                anomaly ->
                    System.out.printf(
                        "%s: %.2f, distance %.2f%n",
                        anomaly.observation().date(),
                        anomaly.observation().value(),
                        anomaly.score()
                    )
            );

        System.out.println("\nLocal anomalies");
        service.detectLocalAnomalies(3)
            .forEach(
                anomaly ->
                    System.out.printf(
                        "%s: %.2f, local z-score %.2f%n",
                        anomaly.observation().date(),
                        anomaly.observation().value(),
                        anomaly.score()
                    )
            );

        System.out.printf(
            "%nDaily trend slope: %.4f%n",
            service.trendSlope()
        );

        service.highestMeanCategory()
            .ifPresent(
                category ->
                    System.out.println(
                        "Highest mean category: " + category
                    )
            );
    }
}
