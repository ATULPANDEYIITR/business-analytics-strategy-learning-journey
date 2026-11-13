import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.LinkedHashMap;
import java.util.stream.Collectors;

/*
 * BREAK-EVEN ANALYSIS
 * Enterprise Cost-Volume-Profit Management System
 *
 * Java 17
 *
 * Features:
 * - Typed financial domain model
 * - Immutable cost and product records
 * - Cost classification
 * - Contribution margin calculations
 * - Break-even and target-profit services
 * - Multi-product portfolio evaluation
 * - Enterprise profitability policies
 * - Validation and custom exceptions
 * - Scenario analysis and reporting
 */

public class Main {

    enum CostType {
        FIXED,
        VARIABLE
    }

    enum DecisionStatus {
        APPROVED,
        REJECTED,
        WARNING
    }

    record CostItem(
        String name,
        double amount,
        CostType type
    ) {
        CostItem {
            if (name == null || name.isBlank()) {
                throw new ValidationException(
                    "Cost name is required."
                );
            }

            requireFiniteNonNegative(amount, "Cost amount");

            if (type == null) {
                throw new ValidationException(
                    "Cost classification is required."
                );
            }
        }
    }

    record Product(
        String name,
        double sellingPrice,
        double variableCost,
        double salesMix
    ) {
        Product {
            if (name == null || name.isBlank()) {
                throw new ValidationException(
                    "Product name is required."
                );
            }

            requireFinitePositive(
                sellingPrice,
                "Selling price"
            );

            requireFiniteNonNegative(
                variableCost,
                "Variable cost"
            );

            requireFinitePositive(
                salesMix,
                "Sales mix"
            );

            if (variableCost >= sellingPrice) {
                throw new ValidationException(
                    "Product contribution must be positive."
                );
            }
        }

        double contribution() {
            return sellingPrice - variableCost;
        }
    }

    record CostTotals(
        double fixed,
        double variable
    ) {}

    record FinancialResult(
        double revenue,
        double totalVariableCosts,
        double fixedCosts,
        double totalCosts,
        double contribution,
        double operatingProfit,
        double contributionMarginRatio,
        double exactBreakEvenUnits,
        int practicalBreakEvenUnits,
        double breakEvenRevenue,
        int targetProfitUnits,
        double marginOfSafetyUnits,
        Double marginOfSafetyRatio
    ) {}

    record Policy(
        double minimumMarginOfSafety,
        double minimumContributionRatio,
        int minimumApprovals
    ) {
        Policy {
            if (
                !Double.isFinite(minimumMarginOfSafety) ||
                minimumMarginOfSafety < 0 ||
                minimumMarginOfSafety > 1
            ) {
                throw new ValidationException(
                    "Invalid margin-of-safety policy."
                );
            }

            if (
                !Double.isFinite(minimumContributionRatio) ||
                minimumContributionRatio < 0 ||
                minimumContributionRatio > 1
            ) {
                throw new ValidationException(
                    "Invalid contribution policy."
                );
            }

            if (minimumApprovals < 0) {
                throw new ValidationException(
                    "Minimum approvals cannot be negative."
                );
            }
        }
    }

    record PolicyDecision(
        DecisionStatus status,
        List<String> violations
    ) {
        PolicyDecision {
            violations = List.copyOf(violations);
        }
    }

    static class FinancialException
        extends RuntimeException {

        FinancialException(String message) {
            super(message);
        }
    }

    static class ValidationException
        extends FinancialException {

        ValidationException(String message) {
            super(message);
        }
    }

    static void requireFiniteNonNegative(
        double value,
        String field
    ) {
        if (!Double.isFinite(value) || value < 0) {
            throw new ValidationException(
                field + " must be finite and non-negative."
            );
        }
    }

    static void requireFinitePositive(
        double value,
        String field
    ) {
        if (!Double.isFinite(value) || value <= 0) {
            throw new ValidationException(
                field + " must be finite and positive."
            );
        }
    }

    static class CostLedger {

        private final Map<String, CostItem> items =
            new LinkedHashMap<>();

        void add(CostItem item) {
            if (items.containsKey(item.name())) {
                throw new ValidationException(
                    "Duplicate cost: " + item.name()
                );
            }

            items.put(item.name(), item);
        }

        CostTotals calculateTotals() {
            double fixed = 0;
            double variable = 0;

            for (CostItem item : items.values()) {
                if (item.type() == CostType.FIXED) {
                    fixed += item.amount();
                } else {
                    variable += item.amount();
                }
            }

            return new CostTotals(fixed, variable);
        }

        List<CostItem> getItems() {
            return List.copyOf(items.values());
        }
    }

    interface AnalysisService {
        FinancialResult analyze(
            int units,
            double targetProfit
        );
    }

    static class BreakEvenService
        implements AnalysisService {

        private final double sellingPrice;
        private final double variableCost;
        private final double fixedCosts;

        BreakEvenService(
            double sellingPrice,
            double variableCost,
            double fixedCosts
        ) {
            requireFinitePositive(
                sellingPrice,
                "Selling price"
            );

            requireFiniteNonNegative(
                variableCost,
                "Variable cost"
            );

            requireFiniteNonNegative(
                fixedCosts,
                "Fixed costs"
            );

            if (variableCost >= sellingPrice) {
                throw new ValidationException(
                    "Contribution margin must be positive."
                );
            }

            this.sellingPrice = sellingPrice;
            this.variableCost = variableCost;
            this.fixedCosts = fixedCosts;
        }

        double contributionPerUnit() {
            return sellingPrice - variableCost;
        }

        double contributionMarginRatio() {
            return contributionPerUnit() / sellingPrice;
        }

        double breakEvenUnits() {
            return fixedCosts / contributionPerUnit();
        }

        double breakEvenRevenue() {
            return fixedCosts / contributionMarginRatio();
        }

        @Override
        public FinancialResult analyze(
            int units,
            double targetProfit
        ) {
            if (units < 0) {
                throw new ValidationException(
                    "Sales units cannot be negative."
                );
            }

            requireFiniteNonNegative(
                targetProfit,
                "Target profit"
            );

            double revenue = units * sellingPrice;

            double variableTotal = units * variableCost;

            double contribution =
                revenue - variableTotal;

            double totalCosts =
                fixedCosts + variableTotal;

            double profit =
                revenue - totalCosts;

            double bep = breakEvenUnits();

            double marginOfSafety = units - bep;

            Double safetyRatio = units == 0
                ? null
                : marginOfSafety / units;

            int targetUnits = (int) Math.ceil(
                (fixedCosts + targetProfit) /
                contributionPerUnit()
            );

            return new FinancialResult(
                revenue,
                variableTotal,
                fixedCosts,
                totalCosts,
                contribution,
                profit,
                contributionMarginRatio(),
                bep,
                (int) Math.ceil(bep),
                breakEvenRevenue(),
                targetUnits,
                marginOfSafety,
                safetyRatio
            );
        }

        double operatingLeverage(int units) {
            FinancialResult result = analyze(units, 0);

            if (result.operatingProfit() <= 0) {
                throw new FinancialException(
                    "Operating leverage is undefined for "
                    + "non-positive operating profit."
                );
            }

            return result.contribution() /
                result.operatingProfit();
        }

        double getSellingPrice() {
            return sellingPrice;
        }

        double getVariableCost() {
            return variableCost;
        }

        double getFixedCosts() {
            return fixedCosts;
        }
    }

    static class PortfolioService {

        private final List<Product> products =
            new ArrayList<>();

        void register(Product product) {
            boolean exists = products.stream()
                .anyMatch(
                    p -> p.name().equals(product.name())
                );

            if (exists) {
                throw new ValidationException(
                    "Duplicate product: " + product.name()
                );
            }

            products.add(product);
        }

        double weightedContribution() {
            if (products.isEmpty()) {
                throw new FinancialException(
                    "No products registered."
                );
            }

            double totalMix = products.stream()
                .mapToDouble(Product::salesMix)
                .sum();

            return products.stream()
                .mapToDouble(
                    p -> (
                        p.salesMix() / totalMix
                    ) * p.contribution()
                )
                .sum();
        }

        double breakEvenUnits(double fixedCosts) {
            requireFiniteNonNegative(
                fixedCosts,
                "Fixed costs"
            );

            return fixedCosts / weightedContribution();
        }

        Map<String, Double> allocation(double fixedCosts) {
            double totalMix = products.stream()
                .mapToDouble(Product::salesMix)
                .sum();

            double totalUnits = breakEvenUnits(fixedCosts);

            Map<String, Double> result =
                new LinkedHashMap<>();

            for (Product product : products) {
                double weight =
                    product.salesMix() / totalMix;

                result.put(
                    product.name(),
                    totalUnits * weight
                );
            }

            return Collections.unmodifiableMap(result);
        }
    }

    static class PolicyService {

        private final Policy policy;

        PolicyService(Policy policy) {
            this.policy = policy;
        }

        PolicyDecision evaluate(
            FinancialResult result,
            int eligibleApprovals
        ) {
            List<String> violations =
                new ArrayList<>();

            if (result.operatingProfit() < 0) {
                violations.add("Operating loss detected.");
            }

            if (
                result.marginOfSafetyRatio() == null ||
                result.marginOfSafetyRatio() <
                    policy.minimumMarginOfSafety()
            ) {
                violations.add(
                    "Margin of safety below required threshold."
                );
            }

            if (
                result.contributionMarginRatio() <
                    policy.minimumContributionRatio()
            ) {
                violations.add(
                    "Contribution margin below policy threshold."
                );
            }

            if (eligibleApprovals < policy.minimumApprovals()) {
                violations.add(
                    "Insufficient eligible approvals."
                );
            }

            DecisionStatus status =
                violations.isEmpty()
                    ? DecisionStatus.APPROVED
                    : DecisionStatus.REJECTED;

            return new PolicyDecision(
                status,
                violations
            );
        }
    }

    static List<FinancialResult> runScenarios(
        BreakEvenService service,
        List<Integer> salesLevels
    ) {
        return salesLevels.stream()
            .map(units -> service.analyze(units, 0))
            .collect(Collectors.toUnmodifiableList());
    }

    static void printResult(FinancialResult result) {
        System.out.printf(
            "Revenue:                 %,.2f%n",
            result.revenue()
        );

        System.out.printf(
            "Variable costs:          %,.2f%n",
            result.totalVariableCosts()
        );

        System.out.printf(
            "Fixed costs:              %,.2f%n",
            result.fixedCosts()
        );

        System.out.printf(
            "Contribution:             %,.2f%n",
            result.contribution()
        );

        System.out.printf(
            "Operating profit:         %,.2f%n",
            result.operatingProfit()
        );

        System.out.printf(
            "Contribution margin:      %.2f%%%n",
            result.contributionMarginRatio() * 100
        );

        System.out.printf(
            "Exact break-even units:   %.2f%n",
            result.exactBreakEvenUnits()
        );

        System.out.printf(
            "Practical break-even:     %d%n",
            result.practicalBreakEvenUnits()
        );

        System.out.printf(
            "Break-even revenue:       %,.2f%n",
            result.breakEvenRevenue()
        );

        System.out.printf(
            "Target-profit units:      %d%n",
            result.targetProfitUnits()
        );

        System.out.printf(
            "Margin of safety:         %.2f%n",
            result.marginOfSafetyUnits()
        );
    }

    public static void main(String[] args) {

        System.out.println("=".repeat(65));
        System.out.println(
            "ENTERPRISE BREAK-EVEN ANALYSIS SYSTEM"
        );
        System.out.println("=".repeat(65));

        try {
            CostLedger ledger = new CostLedger();

            ledger.add(new CostItem(
                "Factory Rent",
                80000,
                CostType.FIXED
            ));

            ledger.add(new CostItem(
                "Salaries",
                120000,
                CostType.FIXED
            ));

            ledger.add(new CostItem(
                "Insurance",
                20000,
                CostType.FIXED
            ));

            ledger.add(new CostItem(
                "Raw Materials",
                250,
                CostType.VARIABLE
            ));

            ledger.add(new CostItem(
                "Packaging",
                50,
                CostType.VARIABLE
            ));

            ledger.add(new CostItem(
                "Direct Labour",
                100,
                CostType.VARIABLE
            ));

            CostTotals totals = ledger.calculateTotals();

            System.out.println("\nCOST CLASSIFICATION");

            System.out.printf(
                "Fixed costs: %.2f%n",
                totals.fixed()
            );

            System.out.printf(
                "Variable cost items: %.2f%n",
                totals.variable()
            );

            BreakEvenService service =
                new BreakEvenService(
                    1000,
                    400,
                    totals.fixed()
                );

            System.out.println("\nUNIT ECONOMICS");

            System.out.printf(
                "Contribution/unit: %.2f%n",
                service.contributionPerUnit()
            );

            System.out.printf(
                "Contribution margin: %.2f%%%n",
                service.contributionMarginRatio() * 100
            );

            System.out.println("\nBREAK-EVEN ANALYSIS");

            FinancialResult result =
                service.analyze(600, 200000);

            printResult(result);

            System.out.println("\nOPERATING LEVERAGE");

            System.out.printf(
                "%.2fx%n",
                service.operatingLeverage(600)
            );

            System.out.println("\nMULTI-PRODUCT ANALYSIS");

            PortfolioService portfolio =
                new PortfolioService();

            portfolio.register(new Product(
                "Standard",
                1000,
                400,
                60
            ));

            portfolio.register(new Product(
                "Premium",
                1500,
                650,
                40
            ));

            System.out.printf(
                "Weighted contribution: %.2f%n",
                portfolio.weightedContribution()
            );

            System.out.printf(
                "Weighted break-even units: %.2f%n",
                portfolio.breakEvenUnits(220000)
            );

            portfolio.allocation(220000)
                .forEach((name, units) ->
                    System.out.printf(
                        "%s break-even allocation: %.2f units%n",
                        name,
                        units
                    )
                );

            System.out.println("\nPROFITABILITY POLICY");

            Policy policy = new Policy(
                0.15,
                0.40,
                2
            );

            PolicyService policyService =
                new PolicyService(policy);

            PolicyDecision decision =
                policyService.evaluate(result, 2);

            System.out.println(
                "Decision: " + decision.status()
            );

            decision.violations().forEach(
                System.out::println
            );

            System.out.println("\nSALES SCENARIOS");

            List<FinancialResult> scenarios =
                runScenarios(
                    service,
                    List.of(200, 300, 367, 400, 600, 1000)
                );

            for (FinancialResult scenario : scenarios) {
                System.out.printf(
                    "Units: %4d | Profit: %12.2f%n",
                    (int) Math.round(
                        scenario.revenue() /
                        service.getSellingPrice()
                    ),
                    scenario.operatingProfit()
                );
            }

            System.out.println("\nEDGE-CASE VALIDATION");

            try {
                new BreakEvenService(
                    100,
                    100,
                    500
                );
            } catch (ValidationException exception) {
                System.out.println(
                    "Correctly rejected zero contribution."
                );
            }

            try {
                service.analyze(-10, 0);
            } catch (ValidationException exception) {
                System.out.println(
                    "Correctly rejected negative sales."
                );
            }

            System.out.println("\nAUTOMATED ASSERTIONS");

            if (service.contributionPerUnit() != 600) {
                throw new AssertionError(
                    "Contribution calculation failed."
                );
            }

            if (
                service.analyze(600, 0).operatingProfit()
                != 140000
            ) {
                throw new AssertionError(
                    "Operating profit calculation failed."
                );
            }

            if (service.breakEvenUnits() != 220000.0 / 600) {
                throw new AssertionError(
                    "Break-even calculation failed."
                );
            }

            if (service.analyze(0, 0).operatingProfit() != -220000) {
                throw new AssertionError(
                    "Zero-sales calculation failed."
                );
            }

            System.out.println("All assertions passed.");

        } catch (FinancialException exception) {
            System.err.println(
                "Financial processing error: " +
                exception.getMessage()
            );

            System.exitCode = 1;

        } catch (Exception exception) {
            System.err.println(
                "System error: " + exception.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
