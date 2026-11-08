import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * Business Analytics Automation
 *
 * Enterprise-oriented sales analytics platform.
 *
 * Java 17, no external dependencies.
 *
 * Includes:
 * - Immutable transaction records
 * - Data quality controls
 * - Analytics job lifecycle
 * - Generic aggregation
 * - KPI and profitability evaluation
 * - Regional and product segmentation
 * - Monthly trend analysis
 * - Moving averages
 * - Revenue anomaly detection
 * - Report persistence
 * - Operational failure handling
 */
public class BusinessAnalyticsAutomation {

    enum JobStatus {
        PENDING, RUNNING, COMPLETED, FAILED
    }

    enum Severity {
        INFO, WARNING, ERROR
    }

    record Transaction(
        String id,
        LocalDate transactionDate,
        String region,
        String product,
        String category,
        int quantity,
        double unitPrice,
        double unitCost
    ) {
        Transaction {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Transaction ID required.");
            }

            if (transactionDate == null ||
                region == null || region.isBlank() ||
                product == null || product.isBlank() ||
                category == null || category.isBlank()) {
                throw new IllegalArgumentException("Invalid business dimensions.");
            }

            if (quantity < 0 ||
                !Double.isFinite(unitPrice) ||
                !Double.isFinite(unitCost) ||
                unitPrice < 0 || unitCost < 0) {
                throw new IllegalArgumentException("Invalid financial values.");
            }

            if (quantity > 0 && unitPrice == 0) {
                throw new IllegalArgumentException("Positive quantity requires a price.");
            }
        }

        double revenue() {
            return quantity * unitPrice;
        }

        double cost() {
            return quantity * unitCost;
        }

        double profit() {
            return revenue() - cost();
        }
    }

    record Metrics(
        long transactions,
        long units,
        double revenue,
        double cost,
        double profit,
        double marginPercent
    ) {}

    record QualityMetrics(
        int accepted,
        int rejected,
        int duplicates
    ) {}

    record Anomaly(
        String transactionId,
        String region,
        double revenue,
        double zScore
    ) {}

    record AnalyticsReport(
        String jobId,
        Instant generatedAt,
        Metrics summary,
        double averageTransactionValue,
        Map<String, Metrics> regionalPerformance,
        Map<String, Metrics> productPerformance,
        Map<String, Metrics> categoryPerformance,
        Map<String, Metrics> monthlyPerformance,
        List<Double> movingAverages,
        List<Anomaly> anomalies,
        QualityMetrics dataQuality
    ) {}

    static class AnalyticsException extends RuntimeException {
        AnalyticsException(String message) {
            super(message);
        }

        AnalyticsException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    interface ReportExporter {
        void export(AnalyticsReport report, Path directory)
            throws IOException;
    }

    static class CSVReportExporter implements ReportExporter {

        private static String escape(String value) {
            if (value.contains(",") ||
                value.contains("\"") ||
                value.contains("\n") ||
                value.contains("\r")) {
                return "\"" + value.replace("\"", "\"\"") + "\"";
            }

            return value;
        }

        @Override
        public void export(
            AnalyticsReport report,
            Path directory
        ) throws IOException {

            Files.createDirectories(directory);

            Path destination = directory.resolve("regional_report.csv");
            Path temporary = Files.createTempFile(
                directory, "regional-", ".tmp"
            );

            try {
                try (BufferedWriter writer = Files.newBufferedWriter(
                    temporary, StandardCharsets.UTF_8
                )) {
                    writer.write(
                        "region,transactions,units,revenue,cost,profit,margin_percent"
                    );
                    writer.newLine();

                    for (var entry : report.regionalPerformance().entrySet()) {
                        Metrics m = entry.getValue();

                        writer.write(String.join(",",
                            escape(entry.getKey()),
                            Long.toString(m.transactions()),
                            Long.toString(m.units()),
                            Double.toString(m.revenue()),
                            Double.toString(m.cost()),
                            Double.toString(m.profit()),
                            Double.toString(m.marginPercent())
                        ));

                        writer.newLine();
                    }
                }

                Files.move(
                    temporary,
                    destination,
                    java.nio.file.StandardCopyOption.REPLACE_EXISTING
                );

            } catch (IOException error) {
                Files.deleteIfExists(temporary);
                throw error;
            }
        }
    }

    static class AnalyticsEngine {

        private final List<Transaction> transactions;
        private final double anomalyThreshold;

        AnalyticsEngine(
            List<Transaction> transactions,
            double anomalyThreshold
        ) {
            if (transactions == null || transactions.isEmpty()) {
                throw new IllegalArgumentException("Transactions are required.");
            }

            if (!Double.isFinite(anomalyThreshold) ||
                anomalyThreshold <= 0) {
                throw new IllegalArgumentException("Invalid anomaly threshold.");
            }

            this.transactions = List.copyOf(transactions);
            this.anomalyThreshold = anomalyThreshold;
        }

        Metrics calculate(List<Transaction> items) {
            long units = 0;
            double revenue = 0;
            double cost = 0;

            for (Transaction item : items) {
                units += item.quantity();
                revenue += item.revenue();
                cost += item.cost();
            }

            double profit = revenue - cost;
            double margin = revenue == 0 ? 0 : profit / revenue * 100;

            return new Metrics(
                items.size(),
                units,
                round(revenue),
                round(cost),
                round(profit),
                round(margin)
            );
        }

        private static double round(double value) {
            return Math.round(value * 100.0) / 100.0;
        }

        <K> Map<String, Metrics> aggregate(
            Function<Transaction, K> classifier
        ) {
            Map<K, List<Transaction>> grouped = transactions.stream()
                .collect(Collectors.groupingBy(
                    classifier,
                    LinkedHashMap::new,
                    Collectors.toList()
                ));

            Map<String, Metrics> result = new LinkedHashMap<>();

            grouped.entrySet().stream()
                .sorted(Comparator.comparing(
                    entry -> entry.getKey().toString()
                ))
                .forEach(entry -> result.put(
                    entry.getKey().toString(),
                    calculate(entry.getValue())
                ));

            return Collections.unmodifiableMap(result);
        }

        List<Double> movingAverages(int windowSize) {
            if (windowSize < 1) {
                throw new IllegalArgumentException("Window must be positive.");
            }

            Map<YearMonth, Double> monthly = transactions.stream()
                .collect(Collectors.groupingBy(
                    item -> YearMonth.from(item.transactionDate()),
                    Collectors.summingDouble(Transaction::revenue)
                ));

            List<Double> values = monthly.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .map(Map.Entry::getValue)
                .toList();

            List<Double> averages = new ArrayList<>();

            for (int i = 0; i < values.size(); i++) {
                int start = Math.max(0, i - windowSize + 1);

                double sum = 0;

                for (int j = start; j <= i; j++) {
                    sum += values.get(j);
                }

                averages.add(round(sum / (i - start + 1)));
            }

            return List.copyOf(averages);
        }

        List<Anomaly> detectAnomalies() {
            if (transactions.size() < 3) {
                return List.of();
            }

            double mean = transactions.stream()
                .mapToDouble(Transaction::revenue)
                .average()
                .orElse(0);

            double variance = transactions.stream()
                .mapToDouble(t -> Math.pow(t.revenue() - mean, 2))
                .average()
                .orElse(0);

            double deviation = Math.sqrt(variance);

            if (deviation == 0) {
                return List.of();
            }

            return transactions.stream()
                .map(t -> new Anomaly(
                    t.id(),
                    t.region(),
                    round(t.revenue()),
                    (t.revenue() - mean) / deviation
                ))
                .filter(a -> Math.abs(a.zScore()) >= anomalyThreshold)
                .toList();
        }

        AnalyticsReport generate(
            String jobId,
            QualityMetrics quality
        ) {
            Metrics summary = calculate(transactions);

            return new AnalyticsReport(
                jobId,
                Instant.now(),
                summary,
                round(summary.revenue() / summary.transactions()),
                aggregate(Transaction::region),
                aggregate(Transaction::product),
                aggregate(Transaction::category),
                aggregate(t -> YearMonth.from(t.transactionDate())),
                movingAverages(3),
                detectAnomalies(),
                quality
            );
        }
    }

    static class CSVDataService {

        private final Path source;

        CSVDataService(Path source) {
            this.source = source;
        }

        private static List<String> parseCSVLine(String line) {
            List<String> fields = new ArrayList<>();
            StringBuilder field = new StringBuilder();
            boolean quoted = false;

            for (int i = 0; i < line.length(); i++) {
                char c = line.charAt(i);

                if (quoted) {
                    if (c == '"' && i + 1 < line.length()
                        && line.charAt(i + 1) == '"') {
                        field.append('"');
                        i++;
                    } else if (c == '"') {
                        quoted = false;
                    } else {
                        field.append(c);
                    }
                } else if (c == '"') {
                    if (!field.isEmpty()) {
                        throw new AnalyticsException("Invalid CSV quote.");
                    }
                    quoted = true;
                } else if (c == ',') {
                    fields.add(field.toString());
                    field.setLength(0);
                } else {
                    field.append(c);
                }
            }

            if (quoted) {
                throw new AnalyticsException("Unclosed CSV quote.");
            }

            fields.add(field.toString());
            return fields;
        }

        List<Transaction> load() throws IOException {
            if (!Files.exists(source)) {
                throw new AnalyticsException("Source CSV does not exist.");
            }

            List<Transaction> records = new ArrayList<>();
            Set<String> seen = new HashSet<>();

            int rejected = 0;
            int duplicates = 0;

            try (BufferedReader reader = Files.newBufferedReader(
                source, StandardCharsets.UTF_8
            )) {
                String header = reader.readLine();

                if (header == null ||
                    !header.equals(
                        "transaction_id,transaction_date,region,product," +
                        "category,quantity,unit_price,cost_per_unit"
                    )) {
                    throw new AnalyticsException("Invalid CSV header.");
                }

                String line;
                int row = 1;

                while ((line = reader.readLine()) != null) {
                    row++;

                    if (line.isBlank()) {
                        continue;
                    }

                    try {
                        List<String> fields = parseCSVLine(line);

                        if (fields.size() != 8) {
                            throw new AnalyticsException("Invalid column count.");
                        }

                        Transaction transaction = new Transaction(
                            fields.get(0),
                            LocalDate.parse(fields.get(1)),
                            fields.get(2),
                            fields.get(3),
                            fields.get(4),
                            Integer.parseInt(fields.get(5)),
                            Double.parseDouble(fields.get(6)),
                            Double.parseDouble(fields.get(7))
                        );

                        if (!seen.add(transaction.id())) {
                            duplicates++;
                            rejected++;
                            continue;
                        }

                        records.add(transaction);

                    } catch (RuntimeException error) {
                        rejected++;
                        System.err.println(
                            "Rejected row " + row + ": " + error.getMessage()
                        );
                    }
                }
            }

            if (records.isEmpty()) {
                throw new AnalyticsException("No valid records found.");
            }

            lastQuality = new QualityMetrics(
                records.size(), rejected, duplicates
            );

            return List.copyOf(records);
        }

        private QualityMetrics lastQuality =
            new QualityMetrics(0, 0, 0);

        QualityMetrics quality() {
            return lastQuality;
        }
    }

    static class AnalyticsJob {

        private final String id = UUID.randomUUID().toString();
        private JobStatus status = JobStatus.PENDING;

        private final CSVDataService dataService;
        private final ReportExporter exporter;
        private final Path outputDirectory;

        AnalyticsJob(
            CSVDataService dataService,
            ReportExporter exporter,
            Path outputDirectory
        ) {
            this.dataService = dataService;
            this.exporter = exporter;
            this.outputDirectory = outputDirectory;
        }

        private void transition(JobStatus next) {
            boolean valid = switch (status) {
                case PENDING -> next == JobStatus.RUNNING;
                case RUNNING ->
                    next == JobStatus.COMPLETED || next == JobStatus.FAILED;
                case COMPLETED, FAILED -> false;
            };

            if (!valid) {
                throw new AnalyticsException(
                    "Invalid job state transition: " + status + " -> " + next
                );
            }

            System.out.println("JOB: " + status + " -> " + next);
            status = next;
        }

        AnalyticsReport execute() {
            transition(JobStatus.RUNNING);

            try {
                List<Transaction> records = dataService.load();

                AnalyticsEngine engine = new AnalyticsEngine(records, 2.0);

                AnalyticsReport report = engine.generate(
                    id, dataService.quality()
                );

                exporter.export(report, outputDirectory);

                transition(JobStatus.COMPLETED);
                return report;

            } catch (Exception error) {
                transition(JobStatus.FAILED);
                throw new AnalyticsException(
                    "Analytics job failed: " + error.getMessage(), error
                );
            }
        }

        JobStatus status() {
            return status;
        }
    }

    private static void createSampleData(Path file) throws IOException {
        if (Files.exists(file)) {
            return;
        }

        Path parent = file.getParent();

        if (parent != null) {
            Files.createDirectories(parent);
        }

        List<String> rows = List.of(
            "transaction_id,transaction_date,region,product,category,quantity,unit_price,cost_per_unit",
            "T001,2026-01-05,North,Laptop,Electronics,3,75000,60000",
            "T002,2026-01-08,South,Phone,Electronics,8,25000,18000",
            "T003,2026-01-12,East,Desk,Furniture,5,12000,8000",
            "T004,2026-02-03,West,Laptop,Electronics,4,75000,60000",
            "T005,2026-02-09,North,Chair,Furniture,10,5000,3000",
            "T006,2026-02-15,South,Phone,Electronics,12,25000,18000",
            "T007,2026-03-02,East,Desk,Furniture,7,12000,8000",
            "T008,2026-03-10,West,Laptop,Electronics,2,75000,60000",
            "T009,2026-03-18,North,Phone,Electronics,15,25000,18000",
            "T010,2026-03-22,South,Chair,Furniture,9,5000,3000",
            "T011,2026-04-04,East,Laptop,Electronics,30,75000,60000",
            "T012,2026-04-12,West,Desk,Furniture,6,12000,8000"
        );

        Files.write(file, rows, StandardCharsets.UTF_8);
    }

    private static void printReport(AnalyticsReport report) {
        System.out.println("\nBUSINESS ANALYTICS REPORT");
        System.out.println("=========================");

        System.out.println("Job: " + report.jobId());
        System.out.println("Generated: " + report.generatedAt());

        System.out.println("\nKEY PERFORMANCE INDICATORS");
        System.out.println(report.summary());
        System.out.printf(
            "Average transaction value: %.2f%n",
            report.averageTransactionValue()
        );

        System.out.println("\nREGIONAL PERFORMANCE");
        report.regionalPerformance().forEach(
            (key, value) -> System.out.println(key + ": " + value)
        );

        System.out.println("\nPRODUCT PERFORMANCE");
        report.productPerformance().forEach(
            (key, value) -> System.out.println(key + ": " + value)
        );

        System.out.println("\nMONTHLY PERFORMANCE");
        report.monthlyPerformance().forEach(
            (key, value) -> System.out.println(key + ": " + value)
        );

        System.out.println("\nMOVING AVERAGES");
        System.out.println(report.movingAverages());

        System.out.println("\nANOMALIES");
        report.anomalies().forEach(System.out::println);

        System.out.println("\nDATA QUALITY");
        System.out.println(report.dataQuality());
    }

    private static void runTests() {
        Transaction item = new Transaction(
            "TEST", LocalDate.of(2026, 1, 1),
            "North", "Laptop", "Electronics",
            2, 1000, 700
        );

        if (item.revenue() != 2000 ||
            item.cost() != 1400 ||
            item.profit() != 600) {
            throw new AssertionError("Financial calculation test failed.");
        }

        AnalyticsEngine engine = new AnalyticsEngine(
            List.of(item), 2.0
        );

        Metrics metrics = engine.calculate(List.of(item));

        if (metrics.profit() != 600 ||
            metrics.marginPercent() != 30) {
            throw new AssertionError("KPI test failed.");
        }

        try {
            new Transaction(
                "BAD", LocalDate.now(), "North", "Laptop",
                "Electronics", -1, 100, 70
            );
            throw new AssertionError("Negative quantity accepted.");
        } catch (IllegalArgumentException expected) {
            // Expected validation failure.
        }

        System.out.println("All tests passed.");
    }

    public static void main(String[] args) {
        try {
            if (args.length > 0 && args[0].equals("--test")) {
                runTests();
                return;
            }

            Path input = Path.of(
                args.length > 0 ? args[0] : "sales_data.csv"
            );

            Path output = Path.of(
                args.length > 1 ? args[1] : "analytics_output"
            );

            createSampleData(input);

            CSVDataService dataService = new CSVDataService(input);

            AnalyticsJob job = new AnalyticsJob(
                dataService,
                new CSVReportExporter(),
                output
            );

            AnalyticsReport report = job.execute();
            printReport(report);

            System.out.println("\nFinal job status: " + job.status());
            System.out.println("Output directory: " + output);

        } catch (Exception error) {
            System.err.println("APPLICATION ERROR: " + error.getMessage());
            System.exit(1);
        }
    }
}
