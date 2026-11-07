import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.LinkedHashMap;
import java.util.Objects;
import java.util.Random;
import java.util.stream.Collectors;

/**
 * Statistical Analysis Enterprise Application.
 *
 * Statistical processing for examination and performance
 * monitoring datasets.
 *
 * Java 17 standard library only.
 */
public class StatisticalAnalysis {

    enum AnalysisStatus {
        CREATED,
        VALIDATING,
        PROCESSING,
        COMPLETED,
        FAILED
    }

    record RegressionResult(
        double slope,
        double intercept,
        double rSquared
    ) {}

    record ConfidenceInterval(
        double mean,
        double lower,
        double upper,
        double standardError
    ) {}

    record Dataset(
        String name,
        List<Double> observations,
        String unit
    ) {
        Dataset {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Dataset name cannot be empty."
                );
            }

            if (unit == null || unit.isBlank()) {
                throw new IllegalArgumentException(
                    "Measurement unit cannot be empty."
                );
            }

            Objects.requireNonNull(
                observations,
                "Observations are required."
            );

            observations = List.copyOf(observations);
        }
    }

    record StatisticalReport(
        String datasetName,
        int observations,
        double mean,
        double median,
        List<Double> modes,
        double minimum,
        double maximum,
        double range,
        double sampleVariance,
        double populationVariance,
        double sampleStandardDeviation,
        double populationStandardDeviation,
        double q1,
        double q3,
        Map<Double, Integer> frequency,
        List<Double> outliers,
        ConfidenceInterval confidenceInterval
    ) {}

    static class StatisticalException
        extends RuntimeException {

        StatisticalException(String message) {
            super(message);
        }
    }

    interface StatisticalPolicy {
        void validate(Dataset dataset);
    }

    static class DefaultStatisticalPolicy
        implements StatisticalPolicy {

        @Override
        public void validate(Dataset dataset) {
            if (dataset.observations().size() < 2) {
                throw new StatisticalException(
                    "At least two observations are required."
                );
            }

            for (Double value : dataset.observations()) {
                if (
                    value == null ||
                    !Double.isFinite(value)
                ) {
                    throw new StatisticalException(
                        "Dataset contains invalid observations."
                    );
                }
            }

            if (dataset.observations().size() > 1_000_000) {
                throw new StatisticalException(
                    "Dataset exceeds the configured size limit."
                );
            }
        }
    }

    static class StatisticalService {

        private final StatisticalPolicy policy;

        private AnalysisStatus status =
            AnalysisStatus.CREATED;

        private final Map<String, StatisticalReport> reports =
            new LinkedHashMap<>();

        StatisticalService(StatisticalPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        private void updateStatus(AnalysisStatus next) {
            this.status = next;

            System.out.println(
                "Analysis state: " + next
            );
        }

        public AnalysisStatus getStatus() {
            return status;
        }

        private List<Double> sorted(
            List<Double> values
        ) {
            List<Double> result =
                new ArrayList<>(values);

            Collections.sort(result);

            return result;
        }

        public double mean(List<Double> data) {
            return data.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow(() ->
                    new StatisticalException(
                        "Cannot calculate mean of empty data."
                    )
                );
        }

        public double median(List<Double> data) {
            List<Double> values = sorted(data);

            int middle = values.size() / 2;

            if (values.size() % 2 == 0) {
                return (
                    values.get(middle - 1) +
                    values.get(middle)
                ) / 2.0;
            }

            return values.get(middle);
        }

        public double percentile(
            List<Double> data,
            double percentage
        ) {
            if (
                !Double.isFinite(percentage) ||
                percentage < 0 ||
                percentage > 100
            ) {
                throw new IllegalArgumentException(
                    "Percentile must be between 0 and 100."
                );
            }

            List<Double> values = sorted(data);

            if (values.isEmpty()) {
                throw new StatisticalException(
                    "Percentile requires observations."
                );
            }

            double position =
                (values.size() - 1) * percentage / 100.0;

            int lower = (int) Math.floor(position);
            int upper = (int) Math.ceil(position);

            if (lower == upper) {
                return values.get(lower);
            }

            double fraction = position - lower;

            return values.get(lower) +
                fraction * (
                    values.get(upper) - values.get(lower)
                );
        }

        public double variance(
            List<Double> data,
            boolean sample
        ) {
            int size = data.size();

            if (size < (sample ? 2 : 1)) {
                throw new StatisticalException(
                    "Insufficient observations for variance."
                );
            }

            double average = mean(data);

            double total = data.stream()
                .mapToDouble(value ->
                    Math.pow(value - average, 2)
                )
                .sum();

            return total / (
                size - (sample ? 1 : 0)
            );
        }

        public double standardDeviation(
            List<Double> data,
            boolean sample
        ) {
            return Math.sqrt(variance(data, sample));
        }

        public Map<Double, Integer> frequency(
            List<Double> data
        ) {
            return data.stream().collect(
                Collectors.groupingBy(
                    value -> value,
                    TreeMap::new,
                    Collectors.summingInt(value -> 1)
                )
            );
        }

        public List<Double> modes(List<Double> data) {
            Map<Double, Integer> frequencies =
                frequency(data);

            int maximum = Collections.max(
                frequencies.values()
            );

            return frequencies.entrySet()
                .stream()
                .filter(entry ->
                    entry.getValue() == maximum
                )
                .map(Map.Entry::getKey)
                .sorted()
                .toList();
        }

        public double covariance(
            List<Double> x,
            List<Double> y
        ) {
            validatePairedData(x, y);

            double meanX = mean(x);
            double meanY = mean(y);

            double total = 0;

            for (int i = 0; i < x.size(); i++) {
                total +=
                    (x.get(i) - meanX) *
                    (y.get(i) - meanY);
            }

            return total / (x.size() - 1);
        }

        public double correlation(
            List<Double> x,
            List<Double> y
        ) {
            double stdX = standardDeviation(x, true);
            double stdY = standardDeviation(y, true);

            if (stdX == 0 || stdY == 0) {
                throw new StatisticalException(
                    "Correlation is undefined for constant data."
                );
            }

            return Math.max(
                -1,
                Math.min(
                    1,
                    covariance(x, y) / (stdX * stdY)
                )
            );
        }

        private void validatePairedData(
            List<Double> x,
            List<Double> y
        ) {
            if (
                x == null ||
                y == null ||
                x.size() < 2 ||
                x.size() != y.size()
            ) {
                throw new StatisticalException(
                    "Paired datasets require equal lengths "
                    + "and at least two observations."
                );
            }
        }

        public RegressionResult regression(
            List<Double> x,
            List<Double> y
        ) {
            validatePairedData(x, y);

            double meanX = mean(x);
            double meanY = mean(y);

            double numerator = 0;
            double denominator = 0;

            for (int i = 0; i < x.size(); i++) {
                numerator +=
                    (x.get(i) - meanX) *
                    (y.get(i) - meanY);

                denominator += Math.pow(
                    x.get(i) - meanX,
                    2
                );
            }

            if (denominator == 0) {
                throw new StatisticalException(
                    "Regression requires varying X values."
                );
            }

            double slope = numerator / denominator;
            double intercept = meanY - slope * meanX;

            double totalSS = 0;
            double residualSS = 0;

            for (int i = 0; i < x.size(); i++) {
                double prediction =
                    slope * x.get(i) + intercept;

                totalSS += Math.pow(
                    y.get(i) - meanY, 2
                );

                residualSS += Math.pow(
                    y.get(i) - prediction, 2
                );
            }

            double rSquared = totalSS == 0
                ? Double.NaN
                : 1 - residualSS / totalSS;

            return new RegressionResult(
                slope,
                intercept,
                rSquared
            );
        }

        public List<Double> outliers(
            List<Double> data
        ) {
            double q1 = percentile(data, 25);
            double q3 = percentile(data, 75);

            double iqr = q3 - q1;

            double lower = q1 - 1.5 * iqr;
            double upper = q3 + 1.5 * iqr;

            return data.stream()
                .filter(value ->
                    value < lower || value > upper
                )
                .toList();
        }

        public ConfidenceInterval confidenceInterval(
            List<Double> data,
            double z
        ) {
            if (!Double.isFinite(z) || z <= 0) {
                throw new IllegalArgumentException(
                    "Z-score must be positive and finite."
                );
            }

            if (data.size() < 2) {
                throw new StatisticalException(
                    "At least two observations are required."
                );
            }

            double average = mean(data);

            double standardError =
                standardDeviation(data, true) /
                Math.sqrt(data.size());

            double margin = z * standardError;

            return new ConfidenceInterval(
                average,
                average - margin,
                average + margin,
                standardError
            );
        }

        public StatisticalReport analyze(
            Dataset dataset
        ) {
            updateStatus(AnalysisStatus.VALIDATING);

            try {
                policy.validate(dataset);

                updateStatus(AnalysisStatus.PROCESSING);

                List<Double> values =
                    dataset.observations();

                double minimum = Collections.min(values);
                double maximum = Collections.max(values);

                Map<Double, Integer> frequencies =
                    frequency(values);

                StatisticalReport report =
                    new StatisticalReport(
                        dataset.name(),
                        values.size(),
                        mean(values),
                        median(values),
                        modes(values),
                        minimum,
                        maximum,
                        maximum - minimum,
                        variance(values, true),
                        variance(values, false),
                        standardDeviation(values, true),
                        standardDeviation(values, false),
                        percentile(values, 25),
                        percentile(values, 75),
                        Map.copyOf(frequencies),
                        outliers(values),
                        confidenceInterval(values, 1.96)
                    );

                reports.put(dataset.name(), report);

                updateStatus(AnalysisStatus.COMPLETED);

                return report;

            } catch (RuntimeException error) {
                updateStatus(AnalysisStatus.FAILED);
                throw error;
            }
        }

        public StatisticalReport findReport(String name) {
            return reports.get(name);
        }
    }

    static class BootstrapService {

        private final Random random;

        BootstrapService(long seed) {
            random = new Random(seed);
        }

        public ConfidenceInterval estimate(
            List<Double> data,
            int iterations
        ) {
            if (
                data == null ||
                data.size() < 2 ||
                iterations < 100 ||
                iterations > 1_000_000
            ) {
                throw new IllegalArgumentException(
                    "Invalid bootstrap parameters."
                );
            }

            for (Double value : data) {
                if (
                    value == null ||
                    !Double.isFinite(value)
                ) {
                    throw new IllegalArgumentException(
                        "Bootstrap data must be finite."
                    );
                }
            }

            List<Double> estimates =
                new ArrayList<>(iterations);

            for (int i = 0; i < iterations; i++) {
                double total = 0;

                for (int j = 0; j < data.size(); j++) {
                    total += data.get(
                        random.nextInt(data.size())
                    );
                }

                estimates.add(total / data.size());
            }

            StatisticalService service =
                new StatisticalService(
                    new DefaultStatisticalPolicy()
                );

            return new ConfidenceInterval(
                service.mean(estimates),
                service.percentile(estimates, 2.5),
                service.percentile(estimates, 97.5),
                0
            );
        }
    }

    private static List<Double> values(double... input) {
        List<Double> result = new ArrayList<>();

        for (double value : input) {
            result.add(value);
        }

        return List.copyOf(result);
    }

    private static void runTests(
        StatisticalService service
    ) {
        List<Double> testData =
            values(10, 20, 20, 30, 40);

        if (Math.abs(service.mean(testData) - 24) > 1e-9) {
            throw new AssertionError("Mean test failed.");
        }

        if (service.median(testData) != 20) {
            throw new AssertionError("Median test failed.");
        }

        if (!service.modes(testData).equals(List.of(20.0))) {
            throw new AssertionError("Mode test failed.");
        }

        try {
            service.correlation(
                values(1, 1, 1),
                values(2, 3, 4)
            );

            throw new AssertionError(
                "Constant data should be rejected."
            );

        } catch (StatisticalException expected) {
            // Expected validation result.
        }

        System.out.println("All statistical tests passed.");
    }

    public static void main(String[] args) {
        StatisticalService service =
            new StatisticalService(
                new DefaultStatisticalPolicy()
            );

        List<Double> scores = values(
            45, 52, 56, 60, 62, 65, 67, 68,
            70, 72, 72, 75, 78, 80, 82, 85,
            88, 90, 92, 95, 98, 100, 105, 150
        );

        Dataset dataset = new Dataset(
            "Examination Performance",
            scores,
            "marks"
        );

        System.out.println(
            "ENTERPRISE STATISTICAL ANALYSIS"
        );

        try {
            StatisticalReport report =
                service.analyze(dataset);

            System.out.println("\nDESCRIPTIVE REPORT");
            System.out.println("Dataset: " + report.datasetName());
            System.out.println("Observations: " + report.observations());
            System.out.println("Mean: " + report.mean());
            System.out.println("Median: " + report.median());
            System.out.println("Modes: " + report.modes());
            System.out.println("Minimum: " + report.minimum());
            System.out.println("Maximum: " + report.maximum());
            System.out.println("Range: " + report.range());
            System.out.println(
                "Sample variance: " + report.sampleVariance()
            );
            System.out.println(
                "Population variance: "
                + report.populationVariance()
            );
            System.out.println(
                "Sample standard deviation: "
                + report.sampleStandardDeviation()
            );
            System.out.println(
                "Q1: " + report.q1()
            );
            System.out.println(
                "Q3: " + report.q3()
            );
            System.out.println(
                "Frequency: " + report.frequency()
            );
            System.out.println(
                "Outliers: " + report.outliers()
            );

            System.out.println(
                "\nCONFIDENCE INTERVAL"
            );

            System.out.println(report.confidenceInterval());

            List<Double> hours = values(
                1, 2, 2, 3, 3, 4, 4, 5,
                5, 6, 6, 7, 7, 8, 8, 9
            );

            List<Double> performance = values(
                35, 42, 45, 48, 52, 55, 58, 62,
                65, 68, 70, 74, 77, 81, 85, 90
            );

            System.out.println("\nCORRELATION");

            System.out.println(
                service.correlation(hours, performance)
            );

            System.out.println("\nREGRESSION");

            System.out.println(
                service.regression(hours, performance)
            );

            System.out.println("\nBOOTSTRAP");

            BootstrapService bootstrap =
                new BootstrapService(42);

            System.out.println(
                bootstrap.estimate(scores, 2000)
            );

            runTests(service);

        } catch (StatisticalException error) {
            System.err.println(
                "Statistical processing failed: "
                + error.getMessage()
            );

            System.exit(1);
        }
    }
}
