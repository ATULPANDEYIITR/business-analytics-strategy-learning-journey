import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Collectors;

public class WindowFunctions {
    enum Metric {
        REVENUE,
        UNITS
    }

    record MonthlySales(
            long id,
            String salesperson,
            String region,
            YearMonth month,
            BigDecimal revenue,
            int units) {

        MonthlySales {
            if (id <= 0) {
                throw new IllegalArgumentException("ID must be positive");
            }
            if (salesperson == null || salesperson.isBlank()) {
                throw new IllegalArgumentException("Salesperson is required");
            }
            if (region == null || region.isBlank()) {
                throw new IllegalArgumentException("Region is required");
            }
            Objects.requireNonNull(month, "Month is required");
            Objects.requireNonNull(revenue, "Revenue is required");

            if (revenue.signum() < 0) {
                throw new IllegalArgumentException("Revenue cannot be negative");
            }
            if (units < 0) {
                throw new IllegalArgumentException("Units cannot be negative");
            }
        }
    }

    record WindowResult(
            MonthlySales sale,
            long rowNumber,
            long rank,
            long denseRank,
            BigDecimal runningTotal,
            BigDecimal movingAverage,
            BigDecimal previousRevenue,
            BigDecimal nextRevenue,
            BigDecimal percentChange) {
    }

    static final class SalesAnalyticsService {
        private final List<MonthlySales> sales;

        SalesAnalyticsService(List<MonthlySales> input) {
            Objects.requireNonNull(input, "Sales cannot be null");

            Set<Long> identifiers = new HashSet<>();
            for (MonthlySales sale : input) {
                if (!identifiers.add(sale.id())) {
                    throw new IllegalArgumentException(
                            "Duplicate sales ID: " + sale.id());
                }
            }

            this.sales = List.copyOf(input);
        }

        Map<String, List<WindowResult>> analyze(Metric metric) {
            Objects.requireNonNull(metric, "Metric is required");

            Map<String, List<MonthlySales>> partitions = sales.stream()
                    .collect(Collectors.groupingBy(
                            MonthlySales::region,
                            TreeMap::new,
                            Collectors.toList()));

            Map<String, List<WindowResult>> result = new LinkedHashMap<>();
            for (Map.Entry<String, List<MonthlySales>> entry
                    : partitions.entrySet()) {
                result.put(entry.getKey(), analyzePartition(entry.getValue(), metric));
            }
            return result;
        }

        private List<WindowResult> analyzePartition(
                List<MonthlySales> partition,
                Metric metric) {

            List<MonthlySales> chronological = partition.stream()
                    .sorted(Comparator.comparing(MonthlySales::month)
                            .thenComparingLong(MonthlySales::id))
                    .toList();

            Comparator<MonthlySales> revenueOrder = Comparator
                    .comparing((MonthlySales sale) -> value(sale, metric))
                    .reversed()
                    .thenComparingLong(MonthlySales::id);

            List<MonthlySales> ranked = chronological.stream()
                    .sorted(revenueOrder)
                    .toList();

            Map<Long, long[]> ranks = calculateRanks(ranked, metric);

            List<WindowResult> output = new ArrayList<>();
            BigDecimal running = BigDecimal.ZERO;

            for (int index = 0; index < chronological.size(); index++) {
                MonthlySales current = chronological.get(index);
                BigDecimal currentValue = value(current, metric);
                running = running.add(currentValue);

                // The frame is the current month and at most one prior row.
                int start = Math.max(0, index - 1);
                BigDecimal frameTotal = BigDecimal.ZERO;
                for (int frameIndex = start; frameIndex <= index; frameIndex++) {
                    frameTotal = frameTotal.add(
                            value(chronological.get(frameIndex), metric));
                }
                BigDecimal average = frameTotal.divide(
                        BigDecimal.valueOf(index - start + 1),
                        2,
                        RoundingMode.HALF_UP);

                BigDecimal previous = index > 0
                        ? value(chronological.get(index - 1), metric)
                        : null;
                BigDecimal next = index + 1 < chronological.size()
                        ? value(chronological.get(index + 1), metric)
                        : null;

                BigDecimal change = null;
                if (previous != null && previous.signum() != 0) {
                    change = currentValue.subtract(previous)
                            .multiply(BigDecimal.valueOf(100))
                            .divide(previous, 2, RoundingMode.HALF_UP);
                }

                long[] rankValues = ranks.get(current.id());
                output.add(new WindowResult(
                        current,
                        rankValues[0],
                        rankValues[1],
                        rankValues[2],
                        running,
                        average,
                        previous,
                        next,
                        change));
            }

            return List.copyOf(output);
        }

        private Map<Long, long[]> calculateRanks(
                List<MonthlySales> ordered,
                Metric metric) {

            Map<Long, long[]> result = new LinkedHashMap<>();
            BigDecimal previous = null;
            long rank = 0;
            long denseRank = 0;

            for (int index = 0; index < ordered.size(); index++) {
                MonthlySales sale = ordered.get(index);
                BigDecimal current = value(sale, metric);

                if (previous == null || current.compareTo(previous) != 0) {
                    rank = index + 1L;
                    denseRank++;
                }

                result.put(sale.id(), new long[] {
                        index + 1L, rank, denseRank
                });
                previous = current;
            }

            return result;
        }

        private BigDecimal value(MonthlySales sale, Metric metric) {
            return switch (metric) {
                case REVENUE -> sale.revenue();
                case UNITS -> BigDecimal.valueOf(sale.units());
            };
        }
    }

    private static List<MonthlySales> sampleData() {
        return List.of(
                new MonthlySales(1, "Asha", "North",
                        YearMonth.of(2026, 1), new BigDecimal("12000.00"), 12),
                new MonthlySales(2, "Ravi", "North",
                        YearMonth.of(2026, 1), new BigDecimal("12000.00"), 10),
                new MonthlySales(3, "Meera", "North",
                        YearMonth.of(2026, 1), new BigDecimal("9000.00"), 9),
                new MonthlySales(4, "Asha", "North",
                        YearMonth.of(2026, 2), new BigDecimal("15000.00"), 15),
                new MonthlySales(5, "Ravi", "North",
                        YearMonth.of(2026, 2), new BigDecimal("11000.00"), 11),
                new MonthlySales(6, "Meera", "North",
                        YearMonth.of(2026, 2), new BigDecimal("11000.00"), 10),
                new MonthlySales(7, "Asha", "North",
                        YearMonth.of(2026, 3), new BigDecimal("14000.00"), 14),
                new MonthlySales(8, "Ravi", "North",
                        YearMonth.of(2026, 3), new BigDecimal("16000.00"), 16),
                new MonthlySales(9, "Meera", "North",
                        YearMonth.of(2026, 3), new BigDecimal("10000.00"), 10),
                new MonthlySales(10, "Kabir", "South",
                        YearMonth.of(2026, 1), new BigDecimal("8000.00"), 8),
                new MonthlySales(11, "Nila", "South",
                        YearMonth.of(2026, 1), new BigDecimal("10000.00"), 10),
                new MonthlySales(12, "Kabir", "South",
                        YearMonth.of(2026, 2), new BigDecimal("12000.00"), 12),
                new MonthlySales(13, "Nila", "South",
                        YearMonth.of(2026, 2), new BigDecimal("10000.00"), 9),
                new MonthlySales(14, "Kabir", "South",
                        YearMonth.of(2026, 3), new BigDecimal("12000.00"), 11),
                new MonthlySales(15, "Nila", "South",
                        YearMonth.of(2026, 3), new BigDecimal("14000.00"), 14));
    }

    private static void printReport(
            Map<String, List<WindowResult>> report) {

        for (Map.Entry<String, List<WindowResult>> region : report.entrySet()) {
            System.out.println("\nRegion: " + region.getKey());
            System.out.printf(
                    "%-8s %-10s %-9s %-10s %-14s %-14s %-12s%n",
                    "Month", "Revenue", "Row No.", "Rank",
                    "Dense Rank", "Running Total", "Change");

            for (WindowResult row : region.getValue()) {
                String change = row.percentChange() == null
                        ? "N/A"
                        : row.percentChange() + "%";

                System.out.printf(
                        "%-8s %-10s %-9d %-10d %-14d %-14s %-12s%n",
                        row.sale().month(),
                        row.sale().revenue(),
                        row.rowNumber(),
                        row.rank(),
                        row.denseRank(),
                        row.runningTotal(),
                        change);
            }
        }
    }

    public static void main(String[] args) {
        SalesAnalyticsService service =
                new SalesAnalyticsService(sampleData());

        System.out.println("Revenue analytics");
        printReport(service.analyze(Metric.REVENUE));

        System.out.println("\nUnit-volume analytics");
        printReport(service.analyze(Metric.UNITS));

        try {
            MonthlySales duplicate = sampleData().get(0);
            new SalesAnalyticsService(List.of(duplicate, duplicate));
        } catch (IllegalArgumentException exception) {
            System.out.println(
                    "\nRejected invalid input: " + exception.getMessage());
        }
    }
}
