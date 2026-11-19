import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

/*
 * ENTERPRISE BUSINESS VALUATION SYSTEM
 *
 * Java 17 implementation.
 *
 * Components:
 * - Immutable financial domain records
 * - Capital structure and WACC service
 * - DCF forecasting service
 * - Gordon Growth terminal valuation
 * - Comparable company analysis
 * - Scenario management
 * - Valuation policy validation
 * - Sensitivity analysis
 * - Enterprise-to-equity reconciliation
 */

public class BusinessValuation {

    enum Scenario {
        BEAR,
        BASE,
        BULL
    }

    static class ValuationException extends RuntimeException {
        public ValuationException(String message) {
            super(message);
        }
    }

    static final class Validation {

        private Validation() {}

        static void positive(double value, String field) {
            if (!Double.isFinite(value) || value <= 0) {
                throw new ValuationException(
                    field + " must be positive."
                );
            }
        }

        static void nonNegative(double value, String field) {
            if (!Double.isFinite(value) || value < 0) {
                throw new ValuationException(
                    field + " cannot be negative."
                );
            }
        }

        static void rate(double value, String field) {
            if (!Double.isFinite(value) || value < 0 || value >= 1) {
                throw new ValuationException(
                    field + " must be between 0 and 1."
                );
            }
        }
    }

    record FinancialStatements(
        double revenue,
        double ebit,
        double depreciation,
        double capex,
        double workingCapitalIncrease,
        double taxRate,
        double cash,
        double debt,
        double shares
    ) {
        FinancialStatements {
            Validation.positive(revenue, "Revenue");
            Validation.positive(shares, "Shares");
            Validation.nonNegative(depreciation, "Depreciation");
            Validation.nonNegative(capex, "Capital expenditure");
            Validation.nonNegative(cash, "Cash");
            Validation.nonNegative(debt, "Debt");
            Validation.rate(taxRate, "Tax rate");

            if (!Double.isFinite(ebit) || ebit < 0) {
                throw new ValuationException(
                    "EBIT must be non-negative in this model."
                );
            }
        }
    }

    record CapitalStructure(
        double costOfEquity,
        double costOfDebt,
        double equityWeight,
        double debtWeight
    ) {
        CapitalStructure {
            Validation.rate(costOfEquity, "Cost of equity");
            Validation.rate(costOfDebt, "Cost of debt");

            if (
                !Double.isFinite(equityWeight) ||
                !Double.isFinite(debtWeight) ||
                equityWeight < 0 ||
                debtWeight < 0
            ) {
                throw new ValuationException(
                    "Invalid capital structure weights."
                );
            }

            if (Math.abs(equityWeight + debtWeight - 1) > 1e-9) {
                throw new ValuationException(
                    "Capital weights must sum to 1."
                );
            }
        }
    }

    record ForecastAssumptions(
        List<Double> growthRates,
        List<Double> ebitMargins,
        double taxRate,
        double depreciationRate,
        double capexRate,
        double workingCapitalRate,
        double terminalGrowth
    ) {
        ForecastAssumptions {
            Objects.requireNonNull(growthRates);
            Objects.requireNonNull(ebitMargins);

            growthRates = List.copyOf(growthRates);
            ebitMargins = List.copyOf(ebitMargins);

            if (
                growthRates.isEmpty() ||
                growthRates.size() != ebitMargins.size()
            ) {
                throw new ValuationException(
                    "Invalid forecast period configuration."
                );
            }

            for (double growth : growthRates) {
                if (!Double.isFinite(growth) || growth <= -1) {
                    throw new ValuationException(
                        "Growth must exceed -100%."
                    );
                }
            }

            ebitMargins.forEach(
                value -> Validation.rate(value, "EBIT margin")
            );

            Validation.rate(taxRate, "Forecast tax rate");
            Validation.rate(depreciationRate, "Depreciation rate");
            Validation.rate(capexRate, "Capex rate");
            Validation.rate(workingCapitalRate, "Working capital rate");
            Validation.rate(terminalGrowth, "Terminal growth");
        }
    }

    record ForecastYear(
        int year,
        double revenue,
        double ebit,
        double nopat,
        double depreciation,
        double capex,
        double workingCapitalChange,
        double fcff,
        double discountFactor,
        double presentValue
    ) {}

    record DCFResult(
        double wacc,
        double explicitValue,
        double terminalValue,
        double terminalPresentValue,
        double enterpriseValue,
        double equityValue,
        double valuePerShare,
        double terminalContribution,
        List<ForecastYear> forecast
    ) {
        DCFResult {
            forecast = List.copyOf(forecast);
        }
    }

    record ComparableCompany(
        String name,
        double enterpriseValue,
        double revenue,
        double ebitda,
        double netIncome
    ) {
        ComparableCompany {
            if (name == null || name.isBlank()) {
                throw new ValuationException(
                    "Comparable company name is required."
                );
            }

            Validation.positive(enterpriseValue, "Comparable EV");
            Validation.positive(revenue, "Comparable revenue");
            Validation.positive(ebitda, "Comparable EBITDA");
            Validation.positive(netIncome, "Comparable net income");
        }

        double evRevenue() {
            return enterpriseValue / revenue;
        }

        double evEbitda() {
            return enterpriseValue / ebitda;
        }

        double peRatio() {
            return enterpriseValue / netIncome;
        }
    }

    static final class CapitalCostService {

        private CapitalCostService() {}

        static double calculateWACC(
            FinancialStatements financials,
            CapitalStructure capital
        ) {
            return
                capital.equityWeight() * capital.costOfEquity()
                + capital.debtWeight()
                * capital.costOfDebt()
                * (1 - financials.taxRate());
        }
    }

    static final class DCFService {

        private final FinancialStatements financials;
        private final ForecastAssumptions assumptions;
        private final double wacc;

        DCFService(
            FinancialStatements financials,
            CapitalStructure capital,
            ForecastAssumptions assumptions
        ) {
            this.financials = Objects.requireNonNull(financials);
            this.assumptions = Objects.requireNonNull(assumptions);

            this.wacc = CapitalCostService.calculateWACC(
                financials,
                capital
            );

            if (
                wacc <= 0 ||
                wacc <= assumptions.terminalGrowth()
            ) {
                throw new ValuationException(
                    "WACC must exceed terminal growth."
                );
            }
        }

        List<ForecastYear> forecast(double discountRate) {
            List<ForecastYear> periods = new ArrayList<>();

            double revenue = financials.revenue();

            double previousWorkingCapital =
                revenue * assumptions.workingCapitalRate();

            for (int i = 0; i < assumptions.growthRates().size(); i++) {
                revenue *= 1 + assumptions.growthRates().get(i);

                double ebit =
                    revenue * assumptions.ebitMargins().get(i);

                double nopat =
                    ebit * (1 - assumptions.taxRate());

                double depreciation =
                    revenue * assumptions.depreciationRate();

                double capex =
                    revenue * assumptions.capexRate();

                double currentWorkingCapital =
                    revenue * assumptions.workingCapitalRate();

                double workingCapitalChange =
                    currentWorkingCapital - previousWorkingCapital;

                // FCFF excludes financing expenses and interest payments.
                double fcff =
                    nopat
                    + depreciation
                    - capex
                    - workingCapitalChange;

                double discountFactor =
                    1 / Math.pow(1 + discountRate, i + 1);

                periods.add(
                    new ForecastYear(
                        i + 1,
                        revenue,
                        ebit,
                        nopat,
                        depreciation,
                        capex,
                        workingCapitalChange,
                        fcff,
                        discountFactor,
                        fcff * discountFactor
                    )
                );

                previousWorkingCapital = currentWorkingCapital;
            }

            return List.copyOf(periods);
        }

        DCFResult calculate() {
            List<ForecastYear> periods = forecast(wacc);

            double explicitValue = periods.stream()
                .mapToDouble(ForecastYear::presentValue)
                .sum();

            double finalFCFF =
                periods.get(periods.size() - 1).fcff();

            double terminalValue =
                finalFCFF * (1 + assumptions.terminalGrowth())
                / (wacc - assumptions.terminalGrowth());

            double terminalPV =
                terminalValue /
                Math.pow(1 + wacc, periods.size());

            double enterpriseValue = explicitValue + terminalPV;

            double equityValue =
                enterpriseValue
                + financials.cash()
                - financials.debt();

            return new DCFResult(
                wacc,
                explicitValue,
                terminalValue,
                terminalPV,
                enterpriseValue,
                equityValue,
                equityValue / financials.shares(),
                terminalPV / enterpriseValue,
                periods
            );
        }

        Map<String, Double> sensitivity(
            List<Double> waccChanges,
            List<Double> growthChanges
        ) {
            List<ForecastYear> baseForecast = forecast(wacc);
            double finalFCFF =
                baseForecast.get(baseForecast.size() - 1).fcff();

            Map<String, Double> results = new TreeMap<>();

            for (double waccChange : waccChanges) {
                double adjustedWACC = wacc + waccChange;

                for (double growthChange : growthChanges) {
                    double adjustedGrowth =
                        assumptions.terminalGrowth() + growthChange;

                    if (
                        adjustedWACC <= 0 ||
                        adjustedGrowth < 0 ||
                        adjustedGrowth >= adjustedWACC
                    ) {
                        continue;
                    }

                    double explicit = baseForecast.stream()
                        .mapToDouble(year ->
                            year.fcff() /
                            Math.pow(1 + adjustedWACC, year.year())
                        )
                        .sum();

                    double terminal =
                        finalFCFF * (1 + adjustedGrowth)
                        / (adjustedWACC - adjustedGrowth);

                    double terminalPV =
                        terminal /
                        Math.pow(adjustedWACC + 1, baseForecast.size());

                    String key = String.format(
                        "WACC=%.2f%%, Growth=%.2f%%",
                        adjustedWACC * 100,
                        adjustedGrowth * 100
                    );

                    results.put(key, explicit + terminalPV);
                }
            }

            return Collections.unmodifiableMap(results);
        }
    }

    static final class ComparableValuationService {

        private final List<ComparableCompany> companies;

        ComparableValuationService(List<ComparableCompany> companies) {
            if (companies == null || companies.isEmpty()) {
                throw new ValuationException(
                    "At least one comparable company is required."
                );
            }

            this.companies = List.copyOf(companies);
        }

        private double median(List<Double> values) {
            List<Double> sorted = new ArrayList<>(values);
            sorted.sort(Comparator.naturalOrder());

            int middle = sorted.size() / 2;

            if (sorted.size() % 2 == 0) {
                return (
                    sorted.get(middle - 1) +
                    sorted.get(middle)
                ) / 2.0;
            }

            return sorted.get(middle);
        }

        Map<String, Double> calculateMultiples() {
            double evRevenue = median(
                companies.stream()
                    .map(ComparableCompany::evRevenue)
                    .toList()
            );

            double evEbitda = median(
                companies.stream()
                    .map(ComparableCompany::evEbitda)
                    .toList()
            );

            double pe = median(
                companies.stream()
                    .map(ComparableCompany::peRatio)
                    .toList()
            );

            return Map.of(
                "EV/Revenue", evRevenue,
                "EV/EBITDA", evEbitda,
                "P/E", pe
            );
        }

        Map<String, Double> valueTarget(
            double revenue,
            double ebitda,
            double netIncome,
            double cash,
            double debt,
            double shares
        ) {
            Validation.positive(revenue, "Target revenue");
            Validation.positive(ebitda, "Target EBITDA");
            Validation.positive(netIncome, "Target net income");
            Validation.nonNegative(cash, "Target cash");
            Validation.nonNegative(debt, "Target debt");
            Validation.positive(shares, "Target shares");

            Map<String, Double> multiples = calculateMultiples();

            double evRevenue =
                revenue * multiples.get("EV/Revenue");

            double evEbitda =
                ebitda * multiples.get("EV/EBITDA");

            double equityPE =
                netIncome * multiples.get("P/E");

            double equityRevenue = evRevenue + cash - debt;
            double equityEbitda = evEbitda + cash - debt;

            return Map.of(
                "EV by Revenue", evRevenue,
                "EV by EBITDA", evEbitda,
                "Equity by Revenue", equityRevenue,
                "Equity by EBITDA", equityEbitda,
                "Equity by P/E", equityPE,
                "Price by Revenue", equityRevenue / shares,
                "Price by EBITDA", equityEbitda / shares,
                "Price by P/E", equityPE / shares
            );
        }
    }

    static final class ValuationPolicy {

        private final double maximumTerminalContribution;
        private final double minimumWACC;
        private final double maximumWACC;

        ValuationPolicy(
            double maximumTerminalContribution,
            double minimumWACC,
            double maximumWACC
        ) {
            Validation.rate(
                maximumTerminalContribution,
                "Maximum terminal contribution"
            );

            if (minimumWACC <= 0 || maximumWACC <= minimumWACC) {
                throw new ValuationException(
                    "Invalid WACC policy limits."
                );
            }

            this.maximumTerminalContribution =
                maximumTerminalContribution;

            this.minimumWACC = minimumWACC;
            this.maximumWACC = maximumWACC;
        }

        List<String> evaluate(DCFResult result) {
            List<String> issues = new ArrayList<>();

            if (
                result.terminalContribution() >
                maximumTerminalContribution
            ) {
                issues.add("Terminal contribution exceeds policy.");
            }

            if (result.wacc() < minimumWACC) {
                issues.add("WACC is below policy.");
            }

            if (result.wacc() > maximumWACC) {
                issues.add("WACC exceeds policy.");
            }

            if (result.equityValue() <= 0) {
                issues.add("Equity value is not positive.");
            }

            return List.copyOf(issues);
        }
    }

    static ForecastAssumptions assumptions(Scenario scenario) {
        return switch (scenario) {
            case BEAR -> new ForecastAssumptions(
                List.of(0.04, 0.035, 0.03, 0.025, 0.02),
                List.of(0.15, 0.15, 0.155, 0.16, 0.16),
                0.25, 0.035, 0.06, 0.12, 0.02
            );

            case BASE -> new ForecastAssumptions(
                List.of(0.10, 0.09, 0.08, 0.07, 0.06),
                List.of(0.18, 0.19, 0.20, 0.205, 0.21),
                0.25, 0.04, 0.055, 0.10, 0.03
            );

            case BULL -> new ForecastAssumptions(
                List.of(0.16, 0.14, 0.12, 0.10, 0.08),
                List.of(0.20, 0.21, 0.22, 0.23, 0.23),
                0.25, 0.045, 0.05, 0.09, 0.035
            );
        };
    }

    static void printResult(Scenario scenario, DCFResult result) {
        System.out.println("\n" + "=".repeat(70));
        System.out.println(scenario + " CASE DCF VALUATION");
        System.out.println("=".repeat(70));

        System.out.printf("WACC: %.2f%%%n", result.wacc() * 100);
        System.out.printf(
            "Explicit value: %.2f%n",
            result.explicitValue()
        );
        System.out.printf(
            "Terminal value: %.2f%n",
            result.terminalValue()
        );
        System.out.printf(
            "Terminal present value: %.2f%n",
            result.terminalPresentValue()
        );
        System.out.printf(
            "Enterprise value: %.2f%n",
            result.enterpriseValue()
        );
        System.out.printf(
            "Equity value: %.2f%n",
            result.equityValue()
        );
        System.out.printf(
            "Value per share: %.2f%n",
            result.valuePerShare()
        );
        System.out.printf(
            "Terminal contribution: %.2f%%%n",
            result.terminalContribution() * 100
        );

        System.out.println("\nForecast");

        for (ForecastYear year : result.forecast()) {
            System.out.printf(
                "Year %d | Revenue %.2f | EBIT %.2f | FCFF %.2f | PV %.2f%n",
                year.year(),
                year.revenue(),
                year.ebit(),
                year.fcff(),
                year.presentValue()
            );
        }
    }

    public static void main(String[] args) {
        try {
            System.out.println("ENTERPRISE BUSINESS VALUATION SYSTEM");
            System.out.println(
                "Currency: INR millions unless stated otherwise"
            );

            FinancialStatements financials =
                new FinancialStatements(
                    1000,
                    180,
                    40,
                    55,
                    10,
                    0.25,
                    100,
                    300,
                    50
                );

            CapitalStructure capital =
                new CapitalStructure(
                    0.14,
                    0.09,
                    0.70,
                    0.30
                );

            Map<Scenario, DCFResult> results =
                new EnumMap<>(Scenario.class);

            ValuationPolicy policy =
                new ValuationPolicy(0.85, 0.01, 0.30);

            for (Scenario scenario : Scenario.values()) {
                DCFService service = new DCFService(
                    financials,
                    capital,
                    assumptions(scenario)
                );

                DCFResult result = service.calculate();

                results.put(scenario, result);

                printResult(scenario, result);

                List<String> issues = policy.evaluate(result);

                System.out.println("\nPolicy evaluation");

                if (issues.isEmpty()) {
                    System.out.println("PASS");
                } else {
                    issues.forEach(
                        issue -> System.out.println("REVIEW: " + issue)
                    );
                }

                if (scenario == Scenario.BASE) {
                    System.out.println("\nSensitivity analysis");

                    Map<String, Double> sensitivity =
                        service.sensitivity(
                            List.of(-0.01, 0.0, 0.01),
                            List.of(-0.01, 0.0, 0.01)
                        );

                    sensitivity.forEach(
                        (key, value) ->
                            System.out.printf(
                                "%s | EV: %.2f%n",
                                key,
                                value
                            )
                    );
                }
            }

            List<ComparableCompany> companies = List.of(
                new ComparableCompany(
                    "Alpha Technologies", 1800, 1200, 240, 140
                ),
                new ComparableCompany(
                    "Beta Systems", 2100, 1500, 300, 175
                ),
                new ComparableCompany(
                    "Gamma Digital", 1650, 1100, 220, 125
                ),
                new ComparableCompany(
                    "Delta Software", 2400, 1600, 320, 190
                )
            );

            ComparableValuationService comparableService =
                new ComparableValuationService(companies);

            System.out.println("\nCOMPARABLE COMPANY ANALYSIS");

            companies.forEach(company ->
                System.out.printf(
                    "%s | EV/Revenue %.2fx | EV/EBITDA %.2fx | P/E %.2fx%n",
                    company.name(),
                    company.evRevenue(),
                    company.evEbitda(),
                    company.peRatio()
                )
            );

            comparableService.calculateMultiples().forEach(
                (name, value) ->
                    System.out.printf(
                        "Median %s: %.2fx%n",
                        name,
                        value
                    )
            );

            System.out.println("\nTARGET VALUATION");

            comparableService.valueTarget(
                1000,
                220,
                120,
                100,
                300,
                50
            ).forEach(
                (name, value) ->
                    System.out.printf(
                        "%-24s %.2f%n",
                        name,
                        value
                    )
            );

            DCFResult base = results.get(Scenario.BASE);

            if (base == null || base.enterpriseValue() <= 0) {
                throw new ValuationException(
                    "Base valuation integrity check failed."
                );
            }

            double reconciledEquity =
                base.enterpriseValue()
                + financials.cash()
                - financials.debt();

            if (
                Math.abs(reconciledEquity - base.equityValue()) > 1e-8
            ) {
                throw new ValuationException(
                    "Enterprise-to-equity reconciliation failed."
                );
            }

            System.out.println(
                "\nAll enterprise valuation checks passed."
            );

        } catch (ValuationException exception) {
            System.err.println(
                "Valuation failure: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
