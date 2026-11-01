import java.util.Arrays;
import java.util.DoubleSummaryStatistics;
import java.util.Random;
import java.util.function.DoubleUnaryOperator;
import java.util.stream.IntStream;

public class NumPyNumericalComputing {

    enum RiskState {
        NORMAL,
        ALERT
    }

    record SensorReading(
        double temperature,
        double humidity,
        double pressure,
        double vibration
    ) {
        SensorReading {
            if (!Double.isFinite(temperature)
                    || !Double.isFinite(humidity)
                    || !Double.isFinite(pressure)
                    || !Double.isFinite(vibration)) {
                throw new IllegalArgumentException(
                    "All sensor values must be finite"
                );
            }
        }

        double[] asArray() {
            return new double[] {
                temperature,
                humidity,
                pressure,
                vibration
            };
        }
    }

    record RiskResult(int recordNumber, double score, RiskState state) {}

    interface NumericalPolicy {
        RiskResult evaluate(int recordNumber, double score);
    }

    static final class WeightedRiskPolicy implements NumericalPolicy {
        private final double threshold;

        WeightedRiskPolicy(double threshold) {
            if (!Double.isFinite(threshold) || threshold < 0.0) {
                throw new IllegalArgumentException(
                    "Threshold must be finite and non-negative"
                );
            }
            this.threshold = threshold;
        }

        @Override
        public RiskResult evaluate(int recordNumber, double score) {
            RiskState state =
                score >= threshold ? RiskState.ALERT : RiskState.NORMAL;

            return new RiskResult(recordNumber, score, state);
        }
    }

    static final class Matrix {
        private final int rows;
        private final int columns;
        private final double[][] values;

        Matrix(double[][] source) {
            if (source == null || source.length == 0) {
                throw new IllegalArgumentException(
                    "Matrix cannot be empty"
                );
            }

            int expectedColumns = source[0].length;

            if (expectedColumns == 0) {
                throw new IllegalArgumentException(
                    "Matrix must contain at least one column"
                );
            }

            this.rows = source.length;
            this.columns = expectedColumns;
            this.values = new double[rows][columns];

            for (int row = 0; row < rows; row++) {
                if (source[row] == null || source[row].length != columns) {
                    throw new IllegalArgumentException(
                        "All matrix rows must have equal lengths"
                    );
                }

                for (int column = 0; column < columns; column++) {
                    double value = source[row][column];

                    if (!Double.isFinite(value)) {
                        throw new IllegalArgumentException(
                            "Matrix values must be finite"
                        );
                    }

                    values[row][column] = value;
                }
            }
        }

        int rows() {
            return rows;
        }

        int columns() {
            return columns;
        }

        double get(int row, int column) {
            validateIndex(row, column);
            return values[row][column];
        }

        double[] row(int row) {
            if (row < 0 || row >= rows) {
                throw new IndexOutOfBoundsException(
                    "Row index out of range"
                );
            }
            return Arrays.copyOf(values[row], columns);
        }

        double[] column(int column) {
            if (column < 0 || column >= columns) {
                throw new IndexOutOfBoundsException(
                    "Column index out of range"
                );
            }

            double[] result = new double[rows];

            for (int row = 0; row < rows; row++) {
                result[row] = values[row][column];
            }

            return result;
        }

        double[] meanByColumn() {
            double[] means = new double[columns];

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    means[column] += values[row][column];
                }
            }

            for (int column = 0; column < columns; column++) {
                means[column] /= rows;
            }

            return means;
        }

        double[] minByColumn() {
            double[] minimums = new double[columns];
            Arrays.fill(minimums, Double.POSITIVE_INFINITY);

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    minimums[column] = Math.min(
                        minimums[column],
                        values[row][column]
                    );
                }
            }

            return minimums;
        }

        double[] maxByColumn() {
            double[] maximums = new double[columns];
            Arrays.fill(maximums, Double.NEGATIVE_INFINITY);

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    maximums[column] = Math.max(
                        maximums[column],
                        values[row][column]
                    );
                }
            }

            return maximums;
        }

        Matrix broadcastAdd(double[] vector) {
            if (vector.length != columns) {
                throw new IllegalArgumentException(
                    "Broadcast vector size must equal column count"
                );
            }

            double[][] result = new double[rows][columns];

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    result[row][column] =
                        values[row][column] + vector[column];
                }
            }

            return new Matrix(result);
        }

        Matrix normalizeColumns() {
            double[] minimums = minByColumn();
            double[] maximums = maxByColumn();

            double[][] result = new double[rows][columns];

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    double range = maximums[column] - minimums[column];

                    result[row][column] =
                        range == 0.0
                            ? 0.0
                            : (values[row][column] - minimums[column])
                                / range;
                }
            }

            return new Matrix(result);
        }

        double[] weightedRows(double[] weights) {
            if (weights.length != columns) {
                throw new IllegalArgumentException(
                    "Weight count must equal column count"
                );
            }

            double[] scores = new double[rows];

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    scores[row] += values[row][column] * weights[column];
                }
            }

            return scores;
        }

        Matrix map(DoubleUnaryOperator operator) {
            double[][] result = new double[rows][columns];

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    double transformed =
                        operator.applyAsDouble(values[row][column]);

                    if (!Double.isFinite(transformed)) {
                        throw new ArithmeticException(
                            "Transformation produced a non-finite value"
                        );
                    }

                    result[row][column] = transformed;
                }
            }

            return new Matrix(result);
        }

        private void validateIndex(int row, int column) {
            if (row < 0 || row >= rows || column < 0 || column >= columns) {
                throw new IndexOutOfBoundsException(
                    "Matrix index out of range"
                );
            }
        }
    }

    static double[] zScores(Matrix matrix) {
        double[] means = matrix.meanByColumn();
        double[] result = new double[matrix.rows() * matrix.columns()];

        for (int column = 0; column < matrix.columns(); column++) {
            double squared = 0.0;

            for (int row = 0; row < matrix.rows(); row++) {
                double difference =
                    matrix.get(row, column) - means[column];
                squared += difference * difference;
            }

            double standardDeviation =
                Math.sqrt(squared / matrix.rows());

            double safeDeviation =
                standardDeviation == 0.0 ? 1.0 : standardDeviation;

            for (int row = 0; row < matrix.rows(); row++) {
                result[row * matrix.columns() + column] =
                    (matrix.get(row, column) - means[column])
                        / safeDeviation;
            }
        }

        return result;
    }

    static boolean[] detectAnomalies(
        Matrix matrix,
        double threshold
    ) {
        if (!Double.isFinite(threshold) || threshold <= 0.0) {
            throw new IllegalArgumentException(
                "Threshold must be positive"
            );
        }

        double[] scores = zScores(matrix);
        boolean[] result = new boolean[matrix.rows()];

        for (int row = 0; row < matrix.rows(); row++) {
            for (int column = 0; column < matrix.columns(); column++) {
                double score =
                    scores[row * matrix.columns() + column];

                if (Math.abs(score) >= threshold) {
                    result[row] = true;
                    break;
                }
            }
        }

        return result;
    }

    static void printArray(String label, double[] values) {
        System.out.println(label + Arrays.toString(values));
    }

    static Matrix createMeasurements() {
        SensorReading[] readings = {
            new SensorReading(22.4, 45.0, 1012.3, 0.12),
            new SensorReading(23.1, 46.5, 1011.8, 0.15),
            new SensorReading(24.8, 49.2, 1010.4, 0.18),
            new SensorReading(26.7, 54.0, 1008.9, 0.31),
            new SensorReading(28.4, 58.1, 1007.5, 0.42),
            new SensorReading(29.1, 61.0, 1006.2, 0.55),
            new SensorReading(27.8, 57.3, 1007.1, 0.38),
            new SensorReading(25.6, 51.4, 1009.2, 0.22)
        };

        double[][] matrix = new double[readings.length][4];

        for (int row = 0; row < readings.length; row++) {
            matrix[row] = readings[row].asArray();
        }

        return new Matrix(matrix);
    }

    static void demonstrateStreams(Matrix matrix) {
        System.out.println("\n=== Stream-based statistics ===");

        for (int column = 0; column < matrix.columns(); column++) {
            DoubleSummaryStatistics statistics =
                Arrays.stream(matrix.column(column))
                    .summaryStatistics();

            System.out.printf(
                "Column %d: count=%d min=%.3f max=%.3f mean=%.3f%n",
                column,
                statistics.getCount(),
                statistics.getMin(),
                statistics.getMax(),
                statistics.getAverage()
            );
        }

        long highTemperatureRecords =
            IntStream.range(0, matrix.rows())
                .filter(row -> matrix.get(row, 0) >= 27.0)
                .count();

        System.out.println(
            "Records with temperature >= 27 C: "
                + highTemperatureRecords
        );
    }

    static void demonstrateRandomGeneration() {
        System.out.println("\n=== Reproducible random values ===");

        Random random = new Random(20261101L);

        double[] values =
            IntStream.range(0, 8)
                .mapToDouble(i -> 100.0 + random.nextGaussian() * 15.0)
                .toArray();

        printArray("Samples: ", values);
    }

    public static void main(String[] args) {
        try {
            Matrix measurements = createMeasurements();

            System.out.println("=== Matrix dimensions ===");
            System.out.println(
                "Rows=" + measurements.rows()
                    + " Columns=" + measurements.columns()
            );

            printArray(
                "First row: ",
                measurements.row(0)
            );

            printArray(
                "Temperature column: ",
                measurements.column(0)
            );

            printArray(
                "Column means: ",
                measurements.meanByColumn()
            );

            System.out.println("\n=== Broadcasting ===");

            Matrix adjusted =
                measurements.broadcastAdd(
                    new double[] {1.0, -2.0, 0.5, 0.0}
                );

            printArray(
                "Adjusted first row: ",
                adjusted.row(0)
            );

            System.out.println("\n=== Normalization ===");

            Matrix normalized =
                measurements.normalizeColumns();

            double[] scores =
                normalized.weightedRows(
                    new double[] {0.35, 0.20, 0.25, 0.20}
                );

            NumericalPolicy policy =
                new WeightedRiskPolicy(0.60);

            for (int row = 0; row < scores.length; row++) {
                RiskResult result =
                    policy.evaluate(row + 1, scores[row]);

                System.out.printf(
                    "Record %d: score=%.3f state=%s%n",
                    result.recordNumber(),
                    result.score(),
                    result.state()
                );
            }

            System.out.println("\n=== Anomaly detection ===");

            boolean[] anomalies =
                detectAnomalies(measurements, 2.0);

            System.out.println(
                "Anomalies: " + Arrays.toString(anomalies)
            );

            demonstrateStreams(measurements);
            demonstrateRandomGeneration();

            System.out.println("\n=== Edge-case validation ===");

            Matrix constant =
                new Matrix(
                    new double[][] {
                        {5.0, 5.0},
                        {5.0, 5.0},
                        {5.0, 5.0}
                    }
                );

            Matrix constantNormalized =
                constant.normalizeColumns();

            for (int row = 0; row < constantNormalized.rows(); row++) {
                for (
                    int column = 0;
                    column < constantNormalized.columns();
                    column++
                ) {
                    if (constantNormalized.get(row, column) != 0.0) {
                        throw new AssertionError(
                            "Zero-range normalization failed"
                        );
                    }
                }
            }

            System.out.println(
                "Zero-range normalization handled safely."
            );

            try {
                measurements.get(100, 0);
            } catch (IndexOutOfBoundsException error) {
                System.out.println(
                    "Invalid index rejected: "
                        + error.getMessage()
                );
            }

            try {
                measurements.weightedRows(
                    new double[] {1.0, 2.0}
                );
            } catch (IllegalArgumentException error) {
                System.out.println(
                    "Invalid weight vector rejected: "
                        + error.getMessage()
                );
            }

            System.out.println(
                "\nNumerical computing workflow completed successfully."
            );

        } catch (RuntimeException error) {
            System.err.println(
                "Fatal numerical processing error: "
                    + error.getMessage()
            );
            System.exit(1);
        }
    }
}
