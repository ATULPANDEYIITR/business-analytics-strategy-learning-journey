import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

public class ParetoBusinessPrioritization {

    enum Priority {
        CORE,
        THRESHOLD,
        REMAINDER
    }

    record BusinessItem(
            String name,
            String category,
            double value
    ) {
        BusinessItem {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                        "Item name cannot be empty."
                );
            }

            if (category == null || category.isBlank()) {
                throw new IllegalArgumentException(
                        "Category cannot be empty."
                );
            }

            if (!Double.isFinite(value) || value < 0) {
                throw new IllegalArgumentException(
                        "Value must be finite and non-negative."
                );
            }

            name = name.trim();
            category = category.trim();
        }
    }

    record ParetoRecord(
            BusinessItem item,
            int rank,
            double share,
            double cumulativeShare,
            Priority priority
    ) {}

    record PrioritizationPolicy(
            double targetShare,
            int maximumFocusedItems
    ) {
        PrioritizationPolicy {
            if (!Double.isFinite(targetShare)
                    || targetShare <= 0
                    || targetShare > 1) {
                throw new IllegalArgumentException(
                        "Target share must be between 0 and 1."
                );
            }

            if (maximumFocusedItems < 0) {
                throw new IllegalArgumentException(
                        "Maximum focused items cannot be negative."
                );
            }
        }
    }

    static final class ParetoService {

        private final PrioritizationPolicy policy;

        ParetoService(PrioritizationPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        List<ParetoRecord> analyze(
                List<BusinessItem> input
        ) {
            validate(input);

            double total = input.stream()
                    .mapToDouble(BusinessItem::value)
                    .sum();

            List<BusinessItem> ordered = new ArrayList<>(input);

            ordered.sort(
                    Comparator
                            .comparingDouble(
                                    BusinessItem::value
                            )
                            .reversed()
                            .thenComparing(BusinessItem::name)
            );

            List<ParetoRecord> results = new ArrayList<>();
            double cumulative = 0.0;

            for (int index = 0;
                 index < ordered.size();
                 index++) {

                BusinessItem item = ordered.get(index);
                double share = item.value() / total;
                double previous = cumulative;
                cumulative += share;

                Priority priority;

                if (previous < policy.targetShare()
                        && cumulative >= policy.targetShare()) {
                    priority = Priority.THRESHOLD;
                } else if (previous < policy.targetShare()) {
                    priority = Priority.CORE;
                } else {
                    priority = Priority.REMAINDER;
                }

                results.add(
                        new ParetoRecord(
                                item,
                                index + 1,
                                share,
                                cumulative,
                                priority
                        )
                );
            }

            return List.copyOf(results);
        }

        List<ParetoRecord> selectFocusedItems(
                List<ParetoRecord> results
        ) {
            List<ParetoRecord> selected = new ArrayList<>();
            double captured = 0.0;

            for (ParetoRecord record : results) {
                if (policy.maximumFocusedItems() > 0
                        && selected.size()
                        >= policy.maximumFocusedItems()) {
                    break;
                }

                selected.add(record);
                captured += record.share();

                if (captured >= policy.targetShare()) {
                    break;
                }
            }

            return List.copyOf(selected);
        }

        Map<String, Double> categoryTotals(
                List<BusinessItem> items
        ) {
            Map<String, Double> totals = new HashMap<>();

            for (BusinessItem item : items) {
                totals.merge(
                        item.category(),
                        item.value(),
                        Double::sum
                );
            }

            return Map.copyOf(totals);
        }

        private static void validate(
                List<BusinessItem> items
        ) {
            if (items == null || items.isEmpty()) {
                throw new IllegalArgumentException(
                        "At least one business item is required."
                );
            }

            Set<String> names = new HashSet<>();
            double total = 0.0;

            for (BusinessItem item : items) {
                Objects.requireNonNull(
                        item,
                        "Business item cannot be null."
                );

                String normalized =
                        item.name().toLowerCase();

                if (!names.add(normalized)) {
                    throw new IllegalArgumentException(
                            "Duplicate item: " + item.name()
                    );
                }

                total += item.value();
            }

            if (!Double.isFinite(total) || total <= 0) {
                throw new IllegalArgumentException(
                        "Total business value must be greater than zero."
                );
            }
        }
    }

    private static List<BusinessItem> sampleData() {
        return List.of(
                new BusinessItem(
                        "Enterprise accounts",
                        "Customers",
                        420000
                ),
                new BusinessItem(
                        "SMB accounts",
                        "Customers",
                        160000
                ),
                new BusinessItem(
                        "Support tickets",
                        "Operations",
                        90000
                ),
                new BusinessItem(
                        "Cloud infrastructure",
                        "Technology",
                        75000
                ),
                new BusinessItem(
                        "Marketing campaigns",
                        "Marketing",
                        60000
                ),
                new BusinessItem(
                        "Training programs",
                        "People",
                        40000
                ),
                new BusinessItem(
                        "Internal tooling",
                        "Technology",
                        25000
                ),
                new BusinessItem(
                        "Legacy reporting",
                        "Operations",
                        15000
                ),
                new BusinessItem(
                        "Office services",
                        "Operations",
                        10000
                ),
                new BusinessItem(
                        "Other requests",
                        "Operations",
                        5000
                )
        );
    }

    private static void printReport(
            List<ParetoRecord> records
    ) {
        System.out.printf(
                "%n%-6s %-28s %12s %10s %13s %12s%n",
                "Rank",
                "Item",
                "Value",
                "Share",
                "Cumulative",
                "Priority"
        );

        System.out.println("-".repeat(90));

        for (ParetoRecord record : records) {
            System.out.printf(
                    "%-6d %-28s %12.2f %9.1f%% %12.1f%% %12s%n",
                    record.rank(),
                    truncate(record.item().name(), 27),
                    record.item().value(),
                    record.share() * 100,
                    record.cumulativeShare() * 100,
                    record.priority()
            );
        }
    }

    private static String truncate(
            String value,
            int maximum
    ) {
        return value.length() <= maximum
                ? value
                : value.substring(0, maximum);
    }

    private static void runTests() {
        ParetoService service =
                new ParetoService(
                        new PrioritizationPolicy(0.80, 0)
                );

        List<ParetoRecord> results =
                service.analyze(sampleData());

        if (results.size() != 10) {
            throw new AssertionError(
                    "Unexpected result count."
            );
        }

        if (!results.get(0)
                .item()
                .name()
                .equals("Enterprise accounts")) {
            throw new AssertionError(
                    "Ranking failed."
            );
        }

        double finalShare =
                results.get(results.size() - 1)
                        .cumulativeShare();

        if (Math.abs(finalShare - 1.0) > 1e-10) {
            throw new AssertionError(
                    "Shares do not total 100%."
            );
        }

        boolean rejected = false;

        try {
            service.analyze(
                    List.of(
                            new BusinessItem(
                                    "Zero",
                                    "Test",
                                    0
                            )
                    )
            );
        } catch (IllegalArgumentException expected) {
            rejected = true;
        }

        if (!rejected) {
            throw new AssertionError(
                    "Zero-total input was not rejected."
            );
        }

        System.out.println("Self-tests passed.");
    }

    public static void main(String[] args) {
        try {
            List<BusinessItem> data = sampleData();

            ParetoService service =
                    new ParetoService(
                            new PrioritizationPolicy(
                                    0.80,
                                    0
                            )
                    );

            List<ParetoRecord> results =
                    service.analyze(data);

            List<ParetoRecord> focused =
                    service.selectFocusedItems(results);

            printReport(results);

            System.out.println("\nFocused management set");
            System.out.println("----------------------");

            double captured = focused.stream()
                    .mapToDouble(ParetoRecord::share)
                    .sum();

            System.out.printf(
                    "Items selected: %d%n",
                    focused.size()
            );

            System.out.printf(
                    "Value captured: %.1f%%%n",
                    captured * 100
            );

            for (ParetoRecord record : focused) {
                System.out.println(
                        " - " + record.item().name()
                );
            }

            System.out.println("\nCategory totals");

            service.categoryTotals(data)
                    .entrySet()
                    .stream()
                    .sorted(
                            Map.Entry
                                    .<String, Double>comparingByValue()
                                    .reversed()
                    )
                    .forEach(entry ->
                            System.out.printf(
                                    "%-25s %12.2f%n",
                                    entry.getKey(),
                                    entry.getValue()
                            )
                    );

            runTests();
        } catch (RuntimeException error) {
            System.err.println(
                    "Analysis failed: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
