import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Collectors;

/*
 * Enterprise Exploratory Data Analysis
 *
 * Capabilities:
 * - Typed dataset representation
 * - Schema validation
 * - Numeric and categorical profiling
 * - Missing-value management
 * - Distribution statistics
 * - Outlier identification
 * - Correlation analysis
 * - Department-level aggregation
 * - Data-quality assessment
 * - Immutable analytical results
 */

public class ExploratoryDataAnalysis {

    enum DataType {
        NUMERIC,
        CATEGORICAL,
        DATE,
        EMPTY
    }

    enum QualitySeverity {
        INFO,
        WARNING,
        CRITICAL
    }

    record Employee(
        String employeeId,
        String department,
        String salary,
        String experience,
        String rating
    ) {}

    record QualityIssue(
        String column,
        QualitySeverity severity,
        String message
    ) {}

    record NumericProfile(
        int count,
        double mean,
        double median,
        double minimum,
        double maximum,
        double variance,
        double standardDeviation,
        double q1,
        double q3,
        double iqr,
        List<Double> outliers
    ) {
        NumericProfile {
            outliers = List.copyOf(outliers);
        }
    }

    record ColumnProfile(
        String name,
        DataType type,
        int total,
        int missing,
        int unique,
        NumericProfile numericProfile,
        Map<String, Long> frequencies
    ) {
        ColumnProfile {
            frequencies = Map.copyOf(frequencies);
        }
    }

    record AnalysisResult(
        int totalRows,
        int totalColumns,
        int duplicateRows,
        List<ColumnProfile> profiles,
        Map<String, Double> correlations,
        List<QualityIssue> issues
    ) {
        AnalysisResult {
            profiles = List.copyOf(profiles);
            correlations = Map.copyOf(correlations);
            issues = List.copyOf(issues);
        }
    }

    static class AnalysisException extends RuntimeException {
        AnalysisException(String message) {
            super(message);
        }
    }

    static class Dataset {
        private final List<Employee> employees;

        Dataset(List<Employee> employees) {
            if (employees == null) {
                throw new AnalysisException("Dataset cannot be null.");
            }

            this.employees = List.copyOf(employees);

            for (Employee employee : this.employees) {
                if (employee == null) {
                    throw new AnalysisException(
                        "Dataset contains a null record."
                    );
                }

                if (
                    employee.employeeId() == null ||
                    employee.employeeId().isBlank()
                ) {
                    throw new AnalysisException(
                        "Employee ID cannot be empty."
                    );
                }
            }
        }

        List<Employee> records() {
            return employees;
        }

        static Dataset sample() {
            return new Dataset(List.of(
                new Employee("E001", "Engineering", "85000", "5", "4.5"),
                new Employee("E002", "Analytics", "72000", "3", "4.2"),
                new Employee("E003", "Engineering", "95000", "8", "4.8"),
                new Employee("E004", "Operations", "61000", "2", "3.9"),
                new Employee("E005", "Analytics", "78000", "4", "4.4"),
                new Employee("E006", "Engineering", "110000", "12", "4.9"),
                new Employee("E007", "Operations", "", "3", "3.7"),
                new Employee("E008", "Analytics", "75000", "4", ""),
                new Employee("E009", "Engineering", "85000", "5", "4.5"),
                new Employee("E010", "Operations", "58000", "1", "3.5"),
                new Employee("E010", "Operations", "58000", "1", "3.5")
            ));
        }
    }

    interface ColumnExtractor {
        String extract(Employee employee);
    }

    static class StatisticsService {

        double mean(List<Double> values) {
            if (values.isEmpty()) {
                throw new AnalysisException(
                    "Mean requires at least one observation."
                );
            }

            return values.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow();
        }

        double quantile(List<Double> values, double fraction) {
            if (
                values.isEmpty() ||
                fraction < 0 ||
                fraction > 1
            ) {
                throw new AnalysisException(
                    "Invalid quantile input."
                );
            }

            List<Double> sorted = values.stream()
                .sorted()
                .toList();

            double position = (sorted.size() - 1) * fraction;

            int lower = (int) Math.floor(position);
            int upper = (int) Math.ceil(position);

            return sorted.get(lower)
                + (sorted.get(upper) - sorted.get(lower))
                * (position - lower);
        }

        double median(List<Double> values) {
            return quantile(values, 0.5);
        }

        double variance(List<Double> values) {
            if (values.size() < 2) return 0;

            double average = mean(values);

            return values.stream()
                .mapToDouble(value ->
                    Math.pow(value - average, 2)
                )
                .sum() / (values.size() - 1);
        }

        double correlation(
            List<Double> first,
            List<Double> second
        ) {
            if (
                first.size() != second.size() ||
                first.size() < 2
            ) {
                throw new AnalysisException(
                    "Correlation requires aligned observations."
                );
            }

            double meanX = mean(first);
            double meanY = mean(second);

            double numerator = 0;
            double sumX = 0;
            double sumY = 0;

            for (int i = 0; i < first.size(); i++) {
                double dx = first.get(i) - meanX;
                double dy = second.get(i) - meanY;

                numerator += dx * dy;
                sumX += dx * dx;
                sumY += dy * dy;
            }

            double denominator = Math.sqrt(sumX * sumY);

            if (denominator == 0) {
                throw new AnalysisException(
                    "Correlation is undefined for constant data."
                );
            }

            return numerator / denominator;
        }
    }

    static class EDAService {

        private final Dataset dataset;
        private final StatisticsService statistics =
            new StatisticsService();

        private static final Set<String> MISSING =
            Set.of("", "na", "n/a", "null", "none", "nan", "missing");

        EDAService(Dataset dataset) {
            this.dataset = dataset;
        }

        boolean isMissing(String value) {
            return value == null ||
                MISSING.contains(value.trim().toLowerCase());
        }

        Double parseNumber(String value) {
            if (isMissing(value)) return null;

            try {
                double number = Double.parseDouble(value);

                return Double.isFinite(number) ? number : null;
            } catch (NumberFormatException exception) {
                return null;
            }
        }

        Map<String, ColumnExtractor> schema() {
            Map<String, ColumnExtractor> columns =
                new LinkedHashMap<>();

            columns.put("employee_id", Employee::employeeId);
            columns.put("department", Employee::department);
            columns.put("salary", Employee::salary);
            columns.put("experience", Employee::experience);
            columns.put("rating", Employee::rating);

            return columns;
        }

        DataType inferType(List<String> values) {
            List<String> valid = values.stream()
                .filter(value -> !isMissing(value))
                .toList();

            if (valid.isEmpty()) return DataType.EMPTY;

            if (valid.stream().allMatch(
                value -> parseNumber(value) != null
            )) {
                return DataType.NUMERIC;
            }

            if (valid.stream().allMatch(value -> {
                try {
                    LocalDate.parse(value);
                    return true;
                } catch (Exception exception) {
                    return false;
                }
            })) {
                return DataType.DATE;
            }

            return DataType.CATEGORICAL;
        }

        NumericProfile numericProfile(List<Double> values) {
            if (values.isEmpty()) return null;

            double average = statistics.mean(values);
            double median = statistics.median(values);
            double variance = statistics.variance(values);
            double q1 = statistics.quantile(values, 0.25);
            double q3 = statistics.quantile(values, 0.75);
            double iqr = q3 - q1;

            double minimum = Collections.min(values);
            double maximum = Collections.max(values);

            double lower = q1 - 1.5 * iqr;
            double upper = q3 + 1.5 * iqr;

            List<Double> outliers = values.stream()
                .filter(value -> value < lower || value > upper)
                .toList();

            return new NumericProfile(
                values.size(),
                average,
                median,
                minimum,
                maximum,
                variance,
                Math.sqrt(variance),
                q1,
                q3,
                iqr,
                outliers
            );
        }

        ColumnProfile profile(
            String name,
            ColumnExtractor extractor
        ) {
            List<String> values = dataset.records().stream()
                .map(extractor::extract)
                .toList();

            int missing = (int) values.stream()
                .filter(this::isMissing)
                .count();

            List<String> valid = values.stream()
                .filter(value -> !isMissing(value))
                .toList();

            DataType type = inferType(values);

            Map<String, Long> frequencies =
                valid.stream().collect(
                    Collectors.groupingBy(
                        value -> value,
                        TreeMap::new,
                        Collectors.counting()
                    )
                );

            NumericProfile numeric = null;

            if (type == DataType.NUMERIC) {
                List<Double> numbers = valid.stream()
                    .map(this::parseNumber)
                    .toList();

                numeric = numericProfile(numbers);
            }

            return new ColumnProfile(
                name,
                type,
                values.size(),
                missing,
                (int) valid.stream().distinct().count(),
                numeric,
                frequencies
            );
        }

        int duplicateCount() {
            Set<Employee> unique = new HashSet<>();

            int duplicates = 0;

            for (Employee employee : dataset.records()) {
                if (!unique.add(employee)) {
                    duplicates++;
                }
            }

            return duplicates;
        }

        Map<String, Double> correlations() {
            List<Employee> records = dataset.records();

            List<Double> salaries = new ArrayList<>();
            List<Double> experience = new ArrayList<>();

            for (Employee employee : records) {
                Double salary = parseNumber(employee.salary());
                Double years = parseNumber(employee.experience());

                if (salary != null && years != null) {
                    salaries.add(salary);
                    experience.add(years);
                }
            }

            Map<String, Double> result = new LinkedHashMap<>();

            if (salaries.size() >= 2) {
                try {
                    result.put(
                        "salary__experience",
                        statistics.correlation(salaries, experience)
                    );
                } catch (AnalysisException ignored) {
                    // Constant columns do not produce a valid coefficient.
                }
            }

            return result;
        }

        Map<String, Map<String, Double>> groupedSalaryAnalysis() {
            Map<String, List<Double>> groups = new TreeMap<>();

            for (Employee employee : dataset.records()) {
                if (isMissing(employee.department())) continue;

                Double salary = parseNumber(employee.salary());

                if (salary == null) continue;

                groups.computeIfAbsent(
                    employee.department(),
                    ignored -> new ArrayList<>()
                ).add(salary);
            }

            Map<String, Map<String, Double>> result =
                new LinkedHashMap<>();

            for (var entry : groups.entrySet()) {
                List<Double> values = entry.getValue();

                Map<String, Double> metrics = new LinkedHashMap<>();

                metrics.put("count", (double) values.size());
                metrics.put("mean", statistics.mean(values));
                metrics.put("median", statistics.median(values));
                metrics.put("minimum", Collections.min(values));
                metrics.put("maximum", Collections.max(values));

                result.put(entry.getKey(), Map.copyOf(metrics));
            }

            return result;
        }

        List<QualityIssue> qualityAssessment(
            List<ColumnProfile> profiles
        ) {
            List<QualityIssue> issues = new ArrayList<>();

            if (dataset.records().isEmpty()) {
                issues.add(new QualityIssue(
                    "dataset",
                    QualitySeverity.CRITICAL,
                    "Dataset contains no records."
                ));
            }

            if (duplicateCount() > 0) {
                issues.add(new QualityIssue(
                    "dataset",
                    QualitySeverity.WARNING,
                    duplicateCount() + " duplicate records detected."
                ));
            }

            for (ColumnProfile profile : profiles) {
                if (profile.missing() > 0) {
                    issues.add(new QualityIssue(
                        profile.name(),
                        QualitySeverity.WARNING,
                        profile.missing() + " missing values detected."
                    ));
                }

                if (
                    profile.unique() <= 1 &&
                    profile.total() > 0
                ) {
                    issues.add(new QualityIssue(
                        profile.name(),
                        QualitySeverity.INFO,
                        "Column is constant or single-valued."
                    ));
                }
            }

            return issues;
        }

        AnalysisResult analyze() {
            List<ColumnProfile> profiles = schema().entrySet()
                .stream()
                .map(entry ->
                    profile(entry.getKey(), entry.getValue())
                )
                .toList();

            return new AnalysisResult(
                dataset.records().size(),
                schema().size(),
                duplicateCount(),
                profiles,
                correlations(),
                qualityAssessment(profiles)
            );
        }
    }

    static void printReport(AnalysisResult result) {
        System.out.println("ENTERPRISE EXPLORATORY DATA ANALYSIS");
        System.out.println("====================================");

        System.out.println("Rows: " + result.totalRows());
        System.out.println("Columns: " + result.totalColumns());
        System.out.println("Duplicate rows: " + result.duplicateRows());

        System.out.println("\nCOLUMN PROFILES");

        for (ColumnProfile profile : result.profiles()) {
            System.out.println("\n" + profile.name());
            System.out.println("Type: " + profile.type());
            System.out.println("Missing: " + profile.missing());
            System.out.println("Unique: " + profile.unique());

            if (profile.numericProfile() != null) {
                NumericProfile numeric = profile.numericProfile();

                System.out.println("Mean: " + numeric.mean());
                System.out.println("Median: " + numeric.median());
                System.out.println("Minimum: " + numeric.minimum());
                System.out.println("Maximum: " + numeric.maximum());
                System.out.println(
                    "Standard deviation: "
                    + numeric.standardDeviation()
                );
                System.out.println("Outliers: " + numeric.outliers());
            }

            if (!profile.frequencies().isEmpty()) {
                System.out.println(
                    "Frequencies: " + profile.frequencies()
                );
            }
        }

        System.out.println("\nGROUPED SALARY ANALYSIS");

        EDAService service = new EDAService(Dataset.sample());

        service.groupedSalaryAnalysis().forEach(
            (department, metrics) ->
                System.out.println(department + ": " + metrics)
        );

        System.out.println("\nCORRELATIONS");
        System.out.println(result.correlations());

        System.out.println("\nDATA QUALITY ISSUES");

        result.issues().forEach(issue ->
            System.out.println(
                issue.severity() + " | "
                + issue.column() + " | "
                + issue.message()
            )
        );
    }

    static void runTests() {
        StatisticsService statistics = new StatisticsService();

        if (statistics.median(List.of(1.0, 2.0, 3.0)) != 2.0) {
            throw new AssertionError("Median test failed.");
        }

        if (statistics.quantile(
            List.of(1.0, 2.0, 3.0, 4.0, 5.0),
            0.25
        ) != 2.0) {
            throw new AssertionError("Quantile test failed.");
        }

        if (statistics.correlation(
            List.of(1.0, 2.0, 3.0),
            List.of(2.0, 4.0, 6.0)
        ) < 0.999999) {
            throw new AssertionError("Correlation test failed.");
        }

        System.out.println("All tests passed.");
    }

    public static void main(String[] args) {
        try {
            if (
                args.length > 0 &&
                args[0].equals("--test")
            ) {
                runTests();
                return;
            }

            Dataset dataset = Dataset.sample();
            EDAService service = new EDAService(dataset);

            AnalysisResult result = service.analyze();

            printReport(result);

        } catch (AnalysisException exception) {
            System.err.println(
                "ANALYSIS ERROR: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
