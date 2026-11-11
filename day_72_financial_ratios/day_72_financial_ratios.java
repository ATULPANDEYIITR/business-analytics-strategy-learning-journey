import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.OptionalDouble;
import java.util.Set;
import java.util.stream.Collectors;

/*
 * FINANCIAL RATIOS
 * Enterprise financial analysis and reporting system.
 *
 * Runtime: Java 17
 * File: FinancialRatioAnalysis.java
 * Dependencies: Java standard library only.
 */

public class FinancialRatioAnalysis {

    enum RatioCategory {
        PROFITABILITY,
        LIQUIDITY,
        LEVERAGE,
        EFFICIENCY
    }

    enum AnalysisState {
        CREATED,
        VALIDATED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    static class FinancialDataException extends RuntimeException {
        FinancialDataException(String message) {
            super(message);
        }
    }

    static class AnalysisException extends RuntimeException {
        AnalysisException(String message) {
            super(message);
        }
    }

    record FinancialStatements(
        String company,
        String period,

        double revenue,
        double costOfGoodsSold,
        double operatingExpenses,
        double operatingIncome,
        double netIncome,

        double totalAssets,
        double currentAssets,
        double inventory,
        double cash,
        double accountsReceivable,

        double totalLiabilities,
        double currentLiabilities,
        double totalDebt,
        double shareholdersEquity,

        double interestExpense,
        double inventoryBeginning,
        double inventoryEnding,
        double receivablesBeginning,
        double receivablesEnding
    ) {
        FinancialStatements {
            Objects.requireNonNull(company);
            Objects.requireNonNull(period);

            validate();
        }

        void validate() {
            if (company.isBlank() || period.isBlank()) {
                throw new FinancialDataException(
                    "Company and period are required."
                );
            }

            double[] values = {
                revenue,
                costOfGoodsSold,
                operatingExpenses,
                operatingIncome,
                netIncome,
                totalAssets,
                currentAssets,
                inventory,
                cash,
                accountsReceivable,
                totalLiabilities,
                currentLiabilities,
                totalDebt,
                shareholdersEquity,
                interestExpense,
                inventoryBeginning,
                inventoryEnding,
                receivablesBeginning,
                receivablesEnding
            };

            for (double value : values) {
                if (!Double.isFinite(value) || value < 0) {
                    throw new FinancialDataException(
                        "Financial values must be finite and non-negative."
                    );
                }
            }

            if (currentAssets > totalAssets ||
                cash > currentAssets ||
                inventory > currentAssets ||
                currentLiabilities > totalLiabilities ||
                totalDebt > totalLiabilities) {

                throw new FinancialDataException(
                    "Financial statement consistency validation failed."
                );
            }
        }
    }

    record RatioResult(
        String name,
        RatioCategory category,
        OptionalDouble value,
        String unit,
        String interpretation
    ) {
        RatioResult {
            Objects.requireNonNull(name);
            Objects.requireNonNull(category);
            Objects.requireNonNull(value);
            Objects.requireNonNull(unit);
            Objects.requireNonNull(interpretation);
        }
    }

    interface RatioPolicy {
        boolean isAcceptable(RatioResult result);
        String description();
    }

    static class ThresholdPolicy implements RatioPolicy {
        private final Map<String, Double> minimums;

        ThresholdPolicy(Map<String, Double> minimums) {
            this.minimums = Map.copyOf(minimums);
        }

        @Override
        public boolean isAcceptable(RatioResult result) {
            if (result.value().isEmpty()) {
                return false;
            }

            Double minimum = minimums.get(result.name());

            if (minimum == null) {
                return true;
            }

            return result.value().getAsDouble() >= minimum;
        }

        @Override
        public String description() {
            return "Configured minimum financial ratio thresholds.";
        }
    }

    static class FinancialRatioService {

        private final FinancialStatements statements;
        private final List<RatioResult> results = new ArrayList<>();
        private AnalysisState state = AnalysisState.CREATED;

        FinancialRatioService(FinancialStatements statements) {
            this.statements = Objects.requireNonNull(statements);
            this.state = AnalysisState.VALIDATED;
        }

        private OptionalDouble divide(
            double numerator,
            double denominator
        ) {
            if (denominator == 0) {
                return OptionalDouble.empty();
            }

            return OptionalDouble.of(numerator / denominator);
        }

        private void add(
            String name,
            RatioCategory category,
            double numerator,
            double denominator,
            String unit,
            String interpretation
        ) {
            results.add(
                new RatioResult(
                    name,
                    category,
                    divide(numerator, denominator),
                    unit,
                    interpretation
                )
            );
        }

        private void calculateProfitability() {
            double grossProfit =
                statements.revenue() -
                statements.costOfGoodsSold();

            add(
                "Gross Profit Margin",
                RatioCategory.PROFITABILITY,
                grossProfit,
                statements.revenue(),
                "%",
                "Gross profit relative to revenue."
            );

            add(
                "Operating Profit Margin",
                RatioCategory.PROFITABILITY,
                statements.operatingIncome(),
                statements.revenue(),
                "%",
                "Operating profitability."
            );

            add(
                "Net Profit Margin",
                RatioCategory.PROFITABILITY,
                statements.netIncome(),
                statements.revenue(),
                "%",
                "Net profitability."
            );

            add(
                "Return on Assets",
                RatioCategory.PROFITABILITY,
                statements.netIncome(),
                statements.totalAssets(),
                "%",
                "Profit relative to total assets."
            );

            add(
                "Return on Equity",
                RatioCategory.PROFITABILITY,
                statements.netIncome(),
                statements.shareholdersEquity(),
                "%",
                "Profit relative to shareholders' equity."
            );
        }

        private void calculateLiquidity() {
            add(
                "Current Ratio",
                RatioCategory.LIQUIDITY,
                statements.currentAssets(),
                statements.currentLiabilities(),
                "x",
                "Short-term asset coverage."
            );

            add(
                "Quick Ratio",
                RatioCategory.LIQUIDITY,
                statements.currentAssets() - statements.inventory(),
                statements.currentLiabilities(),
                "x",
                "Liquid asset coverage excluding inventory."
            );

            add(
                "Cash Ratio",
                RatioCategory.LIQUIDITY,
                statements.cash(),
                statements.currentLiabilities(),
                "x",
                "Immediate cash coverage."
            );
        }

        private void calculateLeverage() {
            add(
                "Debt-to-Equity Ratio",
                RatioCategory.LEVERAGE,
                statements.totalDebt(),
                statements.shareholdersEquity(),
                "x",
                "Debt relative to shareholders' equity."
            );

            add(
                "Debt-to-Assets Ratio",
                RatioCategory.LEVERAGE,
                statements.totalDebt(),
                statements.totalAssets(),
                "%",
                "Assets financed by debt."
            );

            add(
                "Debt Ratio",
                RatioCategory.LEVERAGE,
                statements.totalLiabilities(),
                statements.totalAssets(),
                "%",
                "Assets financed by liabilities."
            );

            add(
                "Interest Coverage Ratio",
                RatioCategory.LEVERAGE,
                statements.operatingIncome(),
                statements.interestExpense(),
                "x",
                "Operating income available for interest."
            );
        }

        private void calculateEfficiency() {
            double averageInventory =
                (statements.inventoryBeginning() +
                 statements.inventoryEnding()) / 2.0;

            double averageReceivables =
                (statements.receivablesBeginning() +
                 statements.receivablesEnding()) / 2.0;

            add(
                "Inventory Turnover",
                RatioCategory.EFFICIENCY,
                statements.costOfGoodsSold(),
                averageInventory,
                "x",
                "Inventory replacement frequency."
            );

            add(
                "Receivables Turnover",
                RatioCategory.EFFICIENCY,
                statements.revenue(),
                averageReceivables,
                "x",
                "Receivables collection efficiency."
            );

            add(
                "Total Asset Turnover",
                RatioCategory.EFFICIENCY,
                statements.revenue(),
                statements.totalAssets(),
                "x",
                "Revenue generated per unit of assets."
            );

            add(
                "Days Sales Outstanding",
                RatioCategory.EFFICIENCY,
                averageReceivables * 365,
                statements.revenue(),
                "days",
                "Estimated receivables collection period."
            );

            add(
                "Days Inventory Outstanding",
                RatioCategory.EFFICIENCY,
                averageInventory * 365,
                statements.costOfGoodsSold(),
                "days",
                "Estimated inventory holding period."
            );
        }

        public synchronized List<RatioResult> analyze() {
            if (state == AnalysisState.RUNNING) {
                throw new AnalysisException(
                    "Analysis is already running."
                );
            }

            state = AnalysisState.RUNNING;
            results.clear();

            try {
                calculateProfitability();
                calculateLiquidity();
                calculateLeverage();
                calculateEfficiency();

                state = AnalysisState.COMPLETED;

                return List.copyOf(results);

            } catch (RuntimeException exception) {
                state = AnalysisState.FAILED;
                results.clear();

                throw new AnalysisException(
                    "Financial analysis failed: " +
                    exception.getMessage()
                );
            }
        }

        public AnalysisState getState() {
            return state;
        }

        public Map<RatioCategory, List<RatioResult>> groupedResults() {
            if (state != AnalysisState.COMPLETED) {
                throw new AnalysisException(
                    "Analysis must complete before reporting."
                );
            }

            EnumMap<RatioCategory, List<RatioResult>> grouped =
                new EnumMap<>(RatioCategory.class);

            for (RatioCategory category : RatioCategory.values()) {
                List<RatioResult> categoryResults =
                    results.stream()
                        .filter(r -> r.category() == category)
                        .toList();

                grouped.put(category, categoryResults);
            }

            return Map.copyOf(grouped);
        }

        public List<String> evaluate(RatioPolicy policy) {
            Objects.requireNonNull(policy);

            if (state != AnalysisState.COMPLETED) {
                throw new AnalysisException(
                    "Cannot evaluate incomplete analysis."
                );
            }

            return results.stream()
                .filter(result -> !policy.isAcceptable(result))
                .map(RatioResult::name)
                .toList();
        }

        public void display() {
            System.out.println("\nFINANCIAL RATIO REPORT");
            System.out.println("Company: " + statements.company());
            System.out.println("Period: " + statements.period());

            for (var entry : groupedResults().entrySet()) {
                System.out.println(
                    "\n" + entry.getKey()
                );

                for (RatioResult result : entry.getValue()) {
                    String value = result.value().isPresent()
                        ? String.format(
                            "%.4f %s",
                            result.value().getAsDouble(),
                            result.unit()
                        )
                        : "N/A (undefined denominator)";

                    System.out.printf(
                        "%-30s %s%n",
                        result.name(),
                        value
                    );

                    System.out.println(
                        "  " + result.interpretation()
                    );
                }
            }
        }
    }

    static FinancialStatements sampleData() {
        return new FinancialStatements(
            "Apex Manufacturing Ltd.",
            "FY2025-26",

            12000000,
            7200000,
            2400000,
            2400000,
            1500000,

            10000000,
            4000000,
            1200000,
            800000,
            1000000,

            5000000,
            2000000,
            3000000,
            5000000,

            400000,
            1000000,
            1200000,
            800000,
            1000000
        );
    }

    static void runTests() {
        FinancialRatioService service =
            new FinancialRatioService(sampleData());

        List<RatioResult> results = service.analyze();

        if (results.size() != 17) {
            throw new AssertionError("Expected 17 ratios.");
        }

        Map<String, Double> expected = Map.of(
            "Gross Profit Margin", 0.4,
            "Current Ratio", 2.0,
            "Quick Ratio", 1.4,
            "Debt-to-Equity Ratio", 0.6,
            "Interest Coverage Ratio", 6.0
        );

        for (RatioResult result : results) {
            if (expected.containsKey(result.name())) {
                double actual = result.value().orElseThrow();

                if (Math.abs(
                    actual - expected.get(result.name())
                ) > 1e-9) {
                    throw new AssertionError(
                        "Incorrect value: " + result.name()
                    );
                }
            }
        }

        // Undefined ratios are represented without division errors.
        FinancialStatements zeroData = new FinancialStatements(
            "Zero Revenue Ltd.",
            "FY2025-26",
            0, 0, 0, 0, 0,
            1000, 500, 100, 100, 100,
            400, 200, 200, 600,
            0, 50, 50, 50, 50
        );

        FinancialRatioService zeroService =
            new FinancialRatioService(zeroData);

        List<RatioResult> zeroResults = zeroService.analyze();

        if (zeroResults.get(0).value().isPresent()) {
            throw new AssertionError(
                "Zero denominator should be undefined."
            );
        }

        Set<String> uniqueNames = results.stream()
            .map(RatioResult::name)
            .collect(Collectors.toSet());

        if (uniqueNames.size() != results.size()) {
            throw new AssertionError("Duplicate ratios detected.");
        }

        try {
            new FinancialStatements(
                "Invalid Ltd.",
                "FY2025-26",
                -100, 0, 0, 0, 0,
                1000, 500, 100, 100, 100,
                400, 200, 200, 600,
                0, 50, 50, 50, 50
            );

            throw new AssertionError(
                "Negative financial values were accepted."
            );

        } catch (FinancialDataException expectedException) {
            // Expected.
        }

        System.out.println("\nAll Java 17 tests passed.");
    }

    public static void main(String[] args) {
        try {
            FinancialRatioService service =
                new FinancialRatioService(sampleData());

            service.analyze();
            service.display();

            ThresholdPolicy policy = new ThresholdPolicy(
                Map.of(
                    "Current Ratio", 1.5,
                    "Interest Coverage Ratio", 2.0
                )
            );

            System.out.println("\nPOLICY EVALUATION");
            System.out.println(policy.description());

            List<String> failed = service.evaluate(policy);

            if (failed.isEmpty()) {
                System.out.println("All configured thresholds passed.");
            } else {
                System.out.println(
                    "Threshold failures: " + failed
                );
            }

            runTests();

        } catch (RuntimeException exception) {
            System.err.println(
                "Financial analysis failed: " +
                exception.getMessage()
            );

            System.exit(1);
        }
    }
}
