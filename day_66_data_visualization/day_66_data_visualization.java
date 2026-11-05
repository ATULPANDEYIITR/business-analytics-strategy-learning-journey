import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

public class BusinessVisualization {

    enum ReportStatus {
        CREATED,
        VALIDATED,
        PUBLISHED,
        FAILED
    }

    enum ChartType {
        BAR,
        LINE,
        COMBINED,
        KPI
    }

    record MonthlyRecord(
        String month,
        double revenue,
        double expenses,
        int orders,
        int customers,
        double target
    ) {
        MonthlyRecord {
            if (month == null || month.isBlank()) {
                throw new IllegalArgumentException("Month is required.");
            }

            if (!Double.isFinite(revenue) ||
                !Double.isFinite(expenses) ||
                !Double.isFinite(target)) {
                throw new IllegalArgumentException(
                    "Financial values must be finite."
                );
            }

            if (revenue < 0 || expenses < 0 || target <= 0 ||
                orders < 0 || customers < 0) {
                throw new IllegalArgumentException(
                    "Invalid business metric."
                );
            }

            if (orders > 0 && customers > orders) {
                throw new IllegalArgumentException(
                    "Customers cannot exceed orders."
                );
            }
        }

        double profit() {
            return revenue - expenses;
        }

        double margin() {
            return revenue > 0
                ? profit() / revenue * 100.0
                : 0.0;
        }

        double achievement() {
            return revenue / target * 100.0;
        }
    }

    record KPI(String name, double value, String unit) {}

    record ChartSpecification(
        ChartType type,
        String title,
        String xAxis,
        String yAxis,
        List<String> series
    ) {
        ChartSpecification {
            series = List.copyOf(series);

            if (title == null || title.isBlank()) {
                throw new IllegalArgumentException(
                    "Chart title is required."
                );
            }

            if (series.isEmpty()) {
                throw new IllegalArgumentException(
                    "Chart must contain at least one series."
                );
            }
        }
    }

    static class BusinessException extends RuntimeException {
        BusinessException(String message) {
            super(message);
        }
    }

    static class BusinessRepository {
        private final List<MonthlyRecord> records;

        BusinessRepository(List<MonthlyRecord> input) {
            if (input == null || input.isEmpty()) {
                throw new BusinessException("Dataset is empty.");
            }

            Set<String> months = new HashSet<>();

            for (MonthlyRecord record : input) {
                if (!months.add(record.month())) {
                    throw new BusinessException(
                        "Duplicate reporting month: " + record.month()
                    );
                }
            }

            records = List.copyOf(input);
        }

        List<MonthlyRecord> findAll() {
            return records;
        }
    }

    static class ReportingPolicy {
        private final double minimumMargin;
        private final double targetAchievementThreshold;

        ReportingPolicy(
            double minimumMargin,
            double targetAchievementThreshold
        ) {
            if (minimumMargin < -100 || minimumMargin > 100) {
                throw new IllegalArgumentException(
                    "Invalid margin threshold."
                );
            }

            if (targetAchievementThreshold <= 0) {
                throw new IllegalArgumentException(
                    "Invalid target threshold."
                );
            }

            this.minimumMargin = minimumMargin;
            this.targetAchievementThreshold =
                targetAchievementThreshold;
        }

        boolean acceptableMargin(MonthlyRecord record) {
            return record.margin() >= minimumMargin;
        }

        boolean achievedTarget(MonthlyRecord record) {
            return record.achievement() >= targetAchievementThreshold;
        }
    }

    static class AnalyticsService {
        private final BusinessRepository repository;
        private final ReportingPolicy policy;

        AnalyticsService(
            BusinessRepository repository,
            ReportingPolicy policy
        ) {
            this.repository = repository;
            this.policy = policy;
        }

        List<KPI> calculateKPIs() {
            List<MonthlyRecord> records = repository.findAll();

            double revenue = records.stream()
                .mapToDouble(MonthlyRecord::revenue)
                .sum();

            double expenses = records.stream()
                .mapToDouble(MonthlyRecord::expenses)
                .sum();

            double profit = revenue - expenses;

            double margin = revenue > 0
                ? profit / revenue * 100
                : 0;

            int orders = records.stream()
                .mapToInt(MonthlyRecord::orders)
                .sum();

            return List.of(
                new KPI("Revenue", revenue, "INR"),
                new KPI("Expenses", expenses, "INR"),
                new KPI("Profit", profit, "INR"),
                new KPI("Profit Margin", margin, "%"),
                new KPI("Orders", orders, "count")
            );
        }

        Map<String, Boolean> evaluatePolicy() {
            return repository.findAll().stream()
                .collect(Collectors.toUnmodifiableMap(
                    MonthlyRecord::month,
                    record -> policy.acceptableMargin(record)
                        && policy.achievedTarget(record)
                ));
        }

        List<MonthlyRecord> underperformingPeriods() {
            return repository.findAll().stream()
                .filter(record -> !policy.achievedTarget(record))
                .sorted(Comparator.comparingDouble(
                    MonthlyRecord::achievement
                ))
                .toList();
        }

        List<Double> movingAverage(int window) {
            List<MonthlyRecord> records = repository.findAll();

            if (window < 1 || window > records.size()) {
                throw new IllegalArgumentException(
                    "Invalid moving-average window."
                );
            }

            List<Double> result = new ArrayList<>();

            for (int i = 0; i <= records.size() - window; i++) {
                double average = records.subList(i, i + window)
                    .stream()
                    .mapToDouble(MonthlyRecord::revenue)
                    .average()
                    .orElse(0);

                result.add(average);
            }

            return List.copyOf(result);
        }

        double revenueExpenseCorrelation() {
            List<MonthlyRecord> records = repository.findAll();

            if (records.size() < 2) {
                throw new BusinessException(
                    "At least two observations are required."
                );
            }

            double meanX = records.stream()
                .mapToDouble(MonthlyRecord::revenue)
                .average().orElse(0);

            double meanY = records.stream()
                .mapToDouble(MonthlyRecord::expenses)
                .average().orElse(0);

            double covariance = 0;
            double varianceX = 0;
            double varianceY = 0;

            for (MonthlyRecord record : records) {
                double x = record.revenue() - meanX;
                double y = record.expenses() - meanY;

                covariance += x * y;
                varianceX += x * x;
                varianceY += y * y;
            }

            double denominator = Math.sqrt(varianceX * varianceY);

            return denominator == 0 ? 0 : covariance / denominator;
        }
    }

    static class VisualizationService {
        private final Path outputDirectory;

        VisualizationService(Path outputDirectory) {
            this.outputDirectory = outputDirectory;
        }

        void validateSpecifications(
            List<ChartSpecification> specifications
        ) {
            Set<String> titles = new HashSet<>();

            for (ChartSpecification specification : specifications) {
                if (!titles.add(specification.title())) {
                    throw new BusinessException(
                        "Duplicate chart title."
                    );
                }
            }
        }

        void exportDashboardData(
            BusinessRepository repository,
            AnalyticsService analytics
        ) throws IOException {
            Files.createDirectories(outputDirectory);

            Path destination = outputDirectory.resolve(
                "enterprise_dashboard.csv"
            );

            Path temporary = outputDirectory.resolve(
                "enterprise_dashboard.csv.tmp"
            );

            try {
                try (BufferedWriter writer = Files.newBufferedWriter(
                    temporary,
                    StandardCharsets.UTF_8
                )) {
                    writer.write(
                        "month,revenue,expenses,profit,margin,"
                        + "target,achievement,orders,customers"
                    );
                    writer.newLine();

                    for (MonthlyRecord record : repository.findAll()) {
                        writer.write(String.join(",",
                            record.month(),
                            Double.toString(record.revenue()),
                            Double.toString(record.expenses()),
                            Double.toString(record.profit()),
                            Double.toString(record.margin()),
                            Double.toString(record.target()),
                            Double.toString(record.achievement()),
                            Integer.toString(record.orders()),
                            Integer.toString(record.customers())
                        ));
                        writer.newLine();
                    }
                }

                // Atomic replacement prevents readers from seeing partial output.
                try {
                    Files.move(
                        temporary,
                        destination,
                        java.nio.file.StandardCopyOption.ATOMIC_MOVE,
                        java.nio.file.StandardCopyOption.REPLACE_EXISTING
                    );
                } catch (java.nio.file.AtomicMoveNotSupportedException ex) {
                    Files.move(
                        temporary,
                        destination,
                        java.nio.file.StandardCopyOption.REPLACE_EXISTING
                    );
                }

            } catch (IOException exception) {
                Files.deleteIfExists(temporary);
                throw new IOException(
                    "Dashboard export failed: " + exception.getMessage(),
                    exception
                );
            }
        }
    }

    static class ReportWorkflow {
        private ReportStatus status = ReportStatus.CREATED;

        ReportStatus getStatus() {
            return status;
        }

        void publish(
            BusinessRepository repository,
            AnalyticsService analytics,
            VisualizationService visualization
        ) throws IOException {
            if (status != ReportStatus.CREATED) {
                throw new BusinessException(
                    "Report has already been processed."
                );
            }

            try {
                if (repository.findAll().isEmpty()) {
                    throw new BusinessException("No reporting data.");
                }

                status = ReportStatus.VALIDATED;

                visualization.exportDashboardData(
                    repository,
                    analytics
                );

                status = ReportStatus.PUBLISHED;

            } catch (RuntimeException | IOException exception) {
                status = ReportStatus.FAILED;
                throw exception;
            }
        }
    }

    public static void main(String[] args) {
        List<MonthlyRecord> records = List.of(
            new MonthlyRecord("January", 450000, 310000, 420, 350, 430000),
            new MonthlyRecord("February", 480000, 325000, 450, 370, 450000),
            new MonthlyRecord("March", 520000, 340000, 490, 395, 500000),
            new MonthlyRecord("April", 495000, 350000, 465, 380, 510000),
            new MonthlyRecord("May", 560000, 365000, 530, 425, 530000),
            new MonthlyRecord("June", 590000, 375000, 560, 445, 550000),
            new MonthlyRecord("July", 610000, 390000, 580, 460, 580000),
            new MonthlyRecord("August", 575000, 385000, 550, 440, 590000),
            new MonthlyRecord("September", 650000, 405000, 610, 490, 620000),
            new MonthlyRecord("October", 680000, 420000, 640, 510, 650000),
            new MonthlyRecord("November", 710000, 440000, 670, 535, 680000),
            new MonthlyRecord("December", 780000, 465000, 740, 590, 720000)
        );

        try {
            BusinessRepository repository =
                new BusinessRepository(records);

            ReportingPolicy policy =
                new ReportingPolicy(15.0, 100.0);

            AnalyticsService analytics =
                new AnalyticsService(repository, policy);

            VisualizationService visualization =
                new VisualizationService(Path.of("business_reports_java"));

            ReportWorkflow workflow = new ReportWorkflow();

            System.out.println("ENTERPRISE BUSINESS DASHBOARD");
            System.out.println("Generated: " + Instant.now());

            System.out.println("\nKEY PERFORMANCE INDICATORS");

            analytics.calculateKPIs().forEach(kpi ->
                System.out.printf(
                    "%-18s %15.2f %s%n",
                    kpi.name(),
                    kpi.value(),
                    kpi.unit()
                )
            );

            System.out.println("\nPOLICY EVALUATION");

            analytics.evaluatePolicy().forEach((month, eligible) ->
                System.out.printf(
                    "%-12s %s%n",
                    month,
                    eligible ? "PASS" : "REVIEW REQUIRED"
                )
            );

            System.out.println("\nUNDERPERFORMING PERIODS");

            analytics.underperformingPeriods().forEach(record ->
                System.out.printf(
                    "%s: %.2f%%%n",
                    record.month(),
                    record.achievement()
                )
            );

            System.out.println("\nTHREE-MONTH MOVING AVERAGE");

            analytics.movingAverage(3).forEach(value ->
                System.out.printf("INR %.2f%n", value)
            );

            System.out.printf(
                "%nRevenue-expense correlation: %.4f%n",
                analytics.revenueExpenseCorrelation()
            );

            List<ChartSpecification> charts = List.of(
                new ChartSpecification(
                    ChartType.COMBINED,
                    "Revenue and Target",
                    "Month",
                    "INR",
                    List.of("Revenue", "Target")
                ),
                new ChartSpecification(
                    ChartType.BAR,
                    "Monthly Profit",
                    "Month",
                    "INR",
                    List.of("Profit")
                ),
                new ChartSpecification(
                    ChartType.KPI,
                    "Executive KPIs",
                    "Metric",
                    "Value",
                    List.of("Revenue", "Expenses", "Profit")
                )
            );

            visualization.validateSpecifications(charts);

            workflow.publish(repository, analytics, visualization);

            System.out.println(
                "\nReport status: " + workflow.getStatus()
            );

            System.out.println(
                "CSV saved in business_reports_java/"
            );

        } catch (Exception exception) {
            System.err.println(
                "Reporting failure: " + exception.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
