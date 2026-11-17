import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/*
 * BUDGET PREPARATION AND VARIANCE ANALYSIS
 *
 * Java 17 enterprise budgeting application.
 *
 * Features:
 * - Immutable financial domain records
 * - Department allocation
 * - Budget approval workflow
 * - Policy-based validation
 * - Static and flexible budgeting
 * - Actual ledger management
 * - Variance analysis
 * - Forecasting
 * - Utilization reporting
 * - Audit events
 * - Transaction validation
 */

public class BudgetManagement {

    private static final BigDecimal ZERO = new BigDecimal("0.00");
    private static final BigDecimal HUNDRED = new BigDecimal("100");

    // -----------------------------------------------------
    // Financial utilities
    // -----------------------------------------------------

    static BigDecimal money(BigDecimal value) {
        Objects.requireNonNull(value, "Financial amount is required.");

        if (value.signum() < 0) {
            throw new IllegalArgumentException(
                "Financial amounts cannot be negative."
            );
        }

        return value.setScale(2, RoundingMode.HALF_UP);
    }

    static BigDecimal money(String value) {
        try {
            return money(new BigDecimal(value));
        } catch (NumberFormatException exception) {
            throw new IllegalArgumentException(
                "Invalid financial amount: " + value,
                exception
            );
        }
    }

    static BigDecimal signed(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
    }

    static BigDecimal percentage(
        BigDecimal numerator,
        BigDecimal denominator
    ) {
        if (denominator.signum() == 0) {
            return ZERO;
        }

        return numerator
            .multiply(HUNDRED)
            .divide(denominator, 2, RoundingMode.HALF_UP);
    }

    static void requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(
                field + " is required."
            );
        }
    }

    // -----------------------------------------------------
    // Enumerations
    // -----------------------------------------------------

    enum AccountType {
        REVENUE,
        EXPENSE
    }

    enum CostBehavior {
        FIXED,
        VARIABLE,
        MIXED
    }

    enum BudgetStatus {
        DRAFT,
        SUBMITTED,
        APPROVED,
        REJECTED,
        CLOSED
    }

    enum VarianceStatus {
        FAVORABLE,
        UNFAVORABLE,
        ON_TARGET
    }

    enum Role {
        DEPARTMENT_MANAGER,
        FINANCE_MANAGER,
        FINANCE_CONTROLLER,
        CFO,
        AUDITOR
    }

    // -----------------------------------------------------
    // Domain records
    // -----------------------------------------------------

    record Department(
        String id,
        String name,
        BigDecimal spendingLimit
    ) {
        Department {
            requireText(id, "Department ID");
            requireText(name, "Department name");
            spendingLimit = money(spendingLimit);
        }
    }

    record BudgetLine(
        String code,
        String description,
        String departmentId,
        AccountType accountType,
        CostBehavior behavior,
        BigDecimal fixedAmount,
        BigDecimal variableRate,
        BigDecimal plannedActivity
    ) {
        BudgetLine {
            requireText(code, "Account code");
            requireText(description, "Description");
            requireText(departmentId, "Department ID");

            Objects.requireNonNull(accountType);
            Objects.requireNonNull(behavior);

            fixedAmount = money(fixedAmount);
            variableRate = money(variableRate);
            plannedActivity = money(plannedActivity);

            if (accountType == AccountType.REVENUE &&
                behavior != CostBehavior.FIXED) {
                throw new IllegalArgumentException(
                    "Revenue must use the revenue planning model."
                );
            }
        }

        BigDecimal plannedAmount() {
            if (accountType == AccountType.REVENUE ||
                behavior == CostBehavior.FIXED) {
                return fixedAmount;
            }

            BigDecimal variable = variableRate
                .multiply(plannedActivity);

            if (behavior == CostBehavior.VARIABLE) {
                return money(variable);
            }

            return money(fixedAmount.add(variable));
        }

        BigDecimal flexibleAmount(BigDecimal activity) {
            if (accountType != AccountType.EXPENSE) {
                throw new IllegalStateException(
                    "Flexible budgeting requires an expense account."
                );
            }

            activity = money(activity);

            if (behavior == CostBehavior.FIXED) {
                return fixedAmount;
            }

            BigDecimal variable = money(
                variableRate.multiply(activity)
            );

            return behavior == CostBehavior.VARIABLE
                ? variable
                : money(fixedAmount.add(variable));
        }
    }

    record ActualTransaction(
        String id,
        String budgetId,
        String accountCode,
        String departmentId,
        int period,
        BigDecimal amount,
        AccountType accountType,
        BigDecimal activity
    ) {
        ActualTransaction {
            requireText(id, "Transaction ID");
            requireText(budgetId, "Budget ID");
            requireText(accountCode, "Account code");
            requireText(departmentId, "Department ID");

            if (period < 1 || period > 12) {
                throw new IllegalArgumentException(
                    "Period must be between 1 and 12."
                );
            }

            amount = money(amount);
            activity = money(activity);
            Objects.requireNonNull(accountType);
        }
    }

    record VarianceResult(
        String accountCode,
        String departmentId,
        AccountType accountType,
        BigDecimal budget,
        BigDecimal actual,
        BigDecimal variance,
        BigDecimal percentage,
        VarianceStatus status
    ) {}

    record AuditEvent(
        String eventId,
        String budgetId,
        String action,
        String actor,
        LocalDateTime timestamp,
        String details
    ) {}

    // -----------------------------------------------------
    // Custom exceptions
    // -----------------------------------------------------

    static class BudgetValidationException extends RuntimeException {
        BudgetValidationException(String message) {
            super(message);
        }
    }

    static class BudgetStateException extends RuntimeException {
        BudgetStateException(String message) {
            super(message);
        }
    }

    static class AuthorizationException extends RuntimeException {
        AuthorizationException(String message) {
            super(message);
        }
    }

    // -----------------------------------------------------
    // Role authorization
    // -----------------------------------------------------

    static class AuthorizationService {

        boolean canSubmit(Role role) {
            return role == Role.DEPARTMENT_MANAGER ||
                role == Role.FINANCE_MANAGER;
        }

        boolean canApprove(Role role) {
            return role == Role.FINANCE_CONTROLLER ||
                role == Role.CFO;
        }

        boolean canReject(Role role) {
            return canApprove(role);
        }
    }

    // -----------------------------------------------------
    // Budget aggregate
    // -----------------------------------------------------

    static class Budget {

        private final String id;
        private final int fiscalYear;
        private final Map<String, Department> departments;

        private final Map<String, BudgetLine> lines =
            new HashMap<>();

        private final List<AuditEvent> auditEvents =
            new ArrayList<>();

        private BudgetStatus status = BudgetStatus.DRAFT;
        private int revision = 1;

        Budget(
            String id,
            int fiscalYear,
            Map<String, Department> departments
        ) {
            requireText(id, "Budget ID");

            if (fiscalYear < 2000 || fiscalYear > 2200) {
                throw new IllegalArgumentException(
                    "Invalid fiscal year."
                );
            }

            this.id = id;
            this.fiscalYear = fiscalYear;
            this.departments = Map.copyOf(departments);
        }

        String id() {
            return id;
        }

        int fiscalYear() {
            return fiscalYear;
        }

        BudgetStatus status() {
            return status;
        }

        int revision() {
            return revision;
        }

        List<BudgetLine> lines() {
            return List.copyOf(lines.values());
        }

        List<AuditEvent> auditEvents() {
            return List.copyOf(auditEvents);
        }

        void addLine(BudgetLine line) {
            if (status != BudgetStatus.DRAFT) {
                throw new BudgetStateException(
                    "Budget is not editable."
                );
            }

            if (!departments.containsKey(line.departmentId())) {
                throw new BudgetValidationException(
                    "Unknown department."
                );
            }

            String key = line.departmentId() + ":" + line.code();

            if (lines.putIfAbsent(key, line) != null) {
                throw new BudgetValidationException(
                    "Duplicate budget account."
                );
            }
        }

        BigDecimal total(AccountType type) {
            return money(
                lines.values().stream()
                    .filter(line -> line.accountType() == type)
                    .map(BudgetLine::plannedAmount)
                    .reduce(ZERO, BigDecimal::add)
            );
        }

        BigDecimal plannedProfit() {
            return signed(
                total(AccountType.REVENUE)
                    .subtract(total(AccountType.EXPENSE))
            );
        }

        void transition(
            BudgetStatus expected,
            BudgetStatus next,
            String actor,
            String details
        ) {
            if (status != expected) {
                throw new BudgetStateException(
                    "Invalid transition: " +
                    status + " -> " + next
                );
            }

            status = next;

            auditEvents.add(new AuditEvent(
                UUID.randomUUID().toString(),
                id,
                next.name(),
                actor,
                LocalDateTime.now(),
                details
            ));
        }

        void close(String actor) {
            transition(
                BudgetStatus.APPROVED,
                BudgetStatus.CLOSED,
                actor,
                "Fiscal budget closed."
            );
        }
    }

    // -----------------------------------------------------
    // Approval and budget policies
    // -----------------------------------------------------

    static class BudgetPolicy {

        private final boolean enforceDepartmentLimits;
        private final int maximumRevision;

        BudgetPolicy(
            boolean enforceDepartmentLimits,
            int maximumRevision
        ) {
            this.enforceDepartmentLimits =
                enforceDepartmentLimits;

            if (maximumRevision < 1) {
                throw new IllegalArgumentException(
                    "Maximum revision must be positive."
                );
            }

            this.maximumRevision = maximumRevision;
        }

        List<String> evaluate(Budget budget) {
            List<String> errors = new ArrayList<>();

            if (budget.lines().isEmpty()) {
                errors.add("Budget has no line items.");
                return errors;
            }

            Map<String, BigDecimal> totals = new HashMap<>();

            for (BudgetLine line : budget.lines()) {
                if (line.accountType() == AccountType.EXPENSE) {
                    totals.merge(
                        line.departmentId(),
                        line.plannedAmount(),
                        BigDecimal::add
                    );
                }
            }

            if (enforceDepartmentLimits) {
                for (var entry : totals.entrySet()) {
                    Department department = budget.departments.get(
                        entry.getKey()
                    );

                    if (entry.getValue().compareTo(
                        department.spendingLimit()
                    ) > 0) {
                        errors.add(
                            department.id() +
                            " exceeds its spending limit."
                        );
                    }
                }
            }

            if (budget.revision() > maximumRevision) {
                errors.add("Revision limit exceeded.");
            }

            return errors;
        }
    }

    static class BudgetWorkflow {

        private final BudgetPolicy policy;
        private final AuthorizationService authorization;

        BudgetWorkflow(
            BudgetPolicy policy,
            AuthorizationService authorization
        ) {
            this.policy = policy;
            this.authorization = authorization;
        }

        void submit(Budget budget, String actor, Role role) {
            if (!authorization.canSubmit(role)) {
                throw new AuthorizationException(
                    "Role cannot submit budgets."
                );
            }

            List<String> errors = policy.evaluate(budget);

            if (!errors.isEmpty()) {
                throw new BudgetValidationException(
                    String.join("; ", errors)
                );
            }

            budget.transition(
                BudgetStatus.DRAFT,
                BudgetStatus.SUBMITTED,
                actor,
                "Budget submitted for approval."
            );
        }

        void approve(Budget budget, String actor, Role role) {
            if (!authorization.canApprove(role)) {
                throw new AuthorizationException(
                    "Role cannot approve budgets."
                );
            }

            budget.transition(
                BudgetStatus.SUBMITTED,
                BudgetStatus.APPROVED,
                actor,
                "Budget approved."
            );
        }

        void reject(
            Budget budget,
            String actor,
            Role role,
            String reason
        ) {
            if (!authorization.canReject(role)) {
                throw new AuthorizationException(
                    "Role cannot reject budgets."
                );
            }

            requireText(reason, "Rejection reason");

            budget.transition(
                BudgetStatus.SUBMITTED,
                BudgetStatus.REJECTED,
                actor,
                reason
            );
        }
    }

    // -----------------------------------------------------
    // Actual ledger
    // -----------------------------------------------------

    static class ActualLedger {

        private final Map<String, ActualTransaction> transactions =
            new HashMap<>();

        void record(
            ActualTransaction transaction,
            Budget budget
        ) {
            if (budget.status() != BudgetStatus.APPROVED) {
                throw new BudgetStateException(
                    "Budget must be approved."
                );
            }

            if (!transaction.budgetId().equals(budget.id())) {
                throw new BudgetValidationException(
                    "Budget identifier mismatch."
                );
            }

            boolean matching = budget.lines().stream()
                .anyMatch(line ->
                    line.code().equals(transaction.accountCode()) &&
                    line.departmentId().equals(
                        transaction.departmentId()
                    ) &&
                    line.accountType() == transaction.accountType()
                );

            if (!matching) {
                throw new BudgetValidationException(
                    "No corresponding budget line."
                );
            }

            if (transactions.putIfAbsent(
                transaction.id(),
                transaction
            ) != null) {
                throw new BudgetValidationException(
                    "Duplicate transaction."
                );
            }
        }

        BigDecimal aggregate(
            String budgetId,
            BudgetLine line,
            Integer period
        ) {
            return money(
                transactions.values().stream()
                    .filter(transaction ->
                        transaction.budgetId().equals(budgetId) &&
                        transaction.accountCode().equals(line.code()) &&
                        transaction.departmentId().equals(
                            line.departmentId()
                        ) &&
                        transaction.accountType() == line.accountType() &&
                        (period == null ||
                            transaction.period() == period)
                    )
                    .map(ActualTransaction::amount)
                    .reduce(ZERO, BigDecimal::add)
            );
        }
    }

    // -----------------------------------------------------
    // Variance analysis service
    // -----------------------------------------------------

    static class VarianceService {

        VarianceStatus classify(
            AccountType type,
            BigDecimal variance
        ) {
            if (variance.signum() == 0) {
                return VarianceStatus.ON_TARGET;
            }

            boolean favorable =
                type == AccountType.REVENUE
                    ? variance.signum() > 0
                    : variance.signum() < 0;

            return favorable
                ? VarianceStatus.FAVORABLE
                : VarianceStatus.UNFAVORABLE;
        }

        List<VarianceResult> analyze(
            Budget budget,
            ActualLedger ledger,
            Integer period
        ) {
            if (budget.status() != BudgetStatus.APPROVED) {
                throw new BudgetStateException(
                    "Budget must be approved before analysis."
                );
            }

            if (period != null &&
                (period < 1 || period > 12)) {
                throw new IllegalArgumentException(
                    "Invalid accounting period."
                );
            }

            return budget.lines().stream()
                .map(line -> {
                    BigDecimal planned = period == null
                        ? line.plannedAmount()
                        : money(
                            line.plannedAmount()
                                .divide(
                                    new BigDecimal("12"),
                                    2,
                                    RoundingMode.HALF_UP
                                )
                        );

                    BigDecimal actual = ledger.aggregate(
                        budget.id(),
                        line,
                        period
                    );

                    BigDecimal variance = signed(
                        actual.subtract(planned)
                    );

                    return new VarianceResult(
                        line.code(),
                        line.departmentId(),
                        line.accountType(),
                        planned,
                        actual,
                        variance,
                        percentage(variance, planned),
                        classify(line.accountType(), variance)
                    );
                })
                .toList();
        }

        List<VarianceResult> analyzeFlexible(
            Budget budget,
            ActualLedger ledger,
            int period,
            Map<String, BigDecimal> activityByDepartment
        ) {
            if (period < 1 || period > 12) {
                throw new IllegalArgumentException("Invalid period.");
            }

            return budget.lines().stream()
                .filter(line ->
                    line.accountType() == AccountType.EXPENSE
                )
                .map(line -> {
                    BigDecimal activity = activityByDepartment.getOrDefault(
                        line.departmentId(),
                        ZERO
                    );

                    BigDecimal planned =
                        line.flexibleAmount(activity);

                    BigDecimal actual = ledger.aggregate(
                        budget.id(),
                        line,
                        period
                    );

                    BigDecimal variance = signed(
                        actual.subtract(planned)
                    );

                    return new VarianceResult(
                        line.code(),
                        line.departmentId(),
                        AccountType.EXPENSE,
                        planned,
                        actual,
                        variance,
                        percentage(variance, planned),
                        classify(AccountType.EXPENSE, variance)
                    );
                })
                .toList();
        }
    }

    // -----------------------------------------------------
    // Reporting service
    // -----------------------------------------------------

    static class ReportingService {

        static Map<String, BigDecimal[]> departmentSummary(
            List<VarianceResult> results
        ) {
            Map<String, BigDecimal[]> summary = new HashMap<>();

            for (VarianceResult result : results) {
                BigDecimal[] figures = summary.computeIfAbsent(
                    result.departmentId(),
                    key -> new BigDecimal[] {
                        ZERO, ZERO, ZERO
                    }
                );

                figures[0] = figures[0].add(result.budget());
                figures[1] = figures[1].add(result.actual());
                figures[2] = figures[2].add(result.variance());
            }

            return summary;
        }

        static BigDecimal forecast(
            BigDecimal actual,
            int elapsedMonths
        ) {
            if (elapsedMonths < 1 || elapsedMonths > 12) {
                throw new IllegalArgumentException(
                    "Elapsed months must be 1 to 12."
                );
            }

            return money(
                actual.multiply(new BigDecimal("12"))
                    .divide(
                        BigDecimal.valueOf(elapsedMonths),
                        2,
                        RoundingMode.HALF_UP
                    )
            );
        }

        static BigDecimal utilization(
            BigDecimal actual,
            BigDecimal budget
        ) {
            if (budget.signum() <= 0) {
                throw new IllegalArgumentException(
                    "Budget must be positive."
                );
            }

            return percentage(actual, budget);
        }

        static void print(List<VarianceResult> results) {
            System.out.println("\nBUDGET VARIANCE REPORT");

            System.out.printf(
                "%-12s %-12s %14s %14s %14s %12s %s%n",
                "ACCOUNT",
                "DEPARTMENT",
                "BUDGET",
                "ACTUAL",
                "VARIANCE",
                "VARIANCE %",
                "STATUS"
            );

            for (VarianceResult row : results) {
                System.out.printf(
                    "%-12s %-12s %14s %14s %14s %12s %s%n",
                    row.accountCode(),
                    row.departmentId(),
                    row.budget().toPlainString(),
                    row.actual().toPlainString(),
                    row.variance().toPlainString(),
                    row.percentage().toPlainString(),
                    row.status()
                );
            }
        }
    }

    // -----------------------------------------------------
    // Application entry point
    // -----------------------------------------------------

    public static void main(String[] args) {

        try {
            Map<String, Department> departments = Map.of(
                "FIN",
                new Department(
                    "FIN", "Finance", money("500000")
                ),
                "OPS",
                new Department(
                    "OPS", "Operations", money("900000")
                ),
                "IT",
                new Department(
                    "IT", "Technology", money("600000")
                )
            );

            Budget budget = new Budget(
                "BUDGET-2027",
                2027,
                departments
            );

            budget.addLine(new BudgetLine(
                "REV001",
                "Service revenue",
                "FIN",
                AccountType.REVENUE,
                CostBehavior.FIXED,
                money("3000000"),
                ZERO,
                ZERO
            ));

            budget.addLine(new BudgetLine(
                "EXP001",
                "Salaries",
                "FIN",
                AccountType.EXPENSE,
                CostBehavior.FIXED,
                money("360000"),
                ZERO,
                ZERO
            ));

            budget.addLine(new BudgetLine(
                "EXP002",
                "Production materials",
                "OPS",
                AccountType.EXPENSE,
                CostBehavior.VARIABLE,
                ZERO,
                money("120"),
                money("5000")
            ));

            budget.addLine(new BudgetLine(
                "EXP003",
                "IT infrastructure",
                "IT",
                AccountType.EXPENSE,
                CostBehavior.MIXED,
                money("180000"),
                money("20"),
                money("5000")
            ));

            BudgetWorkflow workflow = new BudgetWorkflow(
                new BudgetPolicy(true, 10),
                new AuthorizationService()
            );

            workflow.submit(
                budget,
                "Operations Manager",
                Role.DEPARTMENT_MANAGER
            );

            workflow.approve(
                budget,
                "Finance Controller",
                Role.FINANCE_CONTROLLER
            );

            System.out.println("BUDGET PREPARATION");
            System.out.println("Budget: " + budget.id());
            System.out.println("Fiscal year: " + budget.fiscalYear());
            System.out.println("Status: " + budget.status());
            System.out.println(
                "Revenue: " + budget.total(AccountType.REVENUE)
            );
            System.out.println(
                "Expenses: " + budget.total(AccountType.EXPENSE)
            );
            System.out.println(
                "Planned profit: " + budget.plannedProfit()
            );

            ActualLedger ledger = new ActualLedger();

            ledger.record(new ActualTransaction(
                "TX001", budget.id(), "REV001", "FIN",
                1, money("280000"), AccountType.REVENUE, ZERO
            ), budget);

            ledger.record(new ActualTransaction(
                "TX002", budget.id(), "EXP001", "FIN",
                1, money("30000"), AccountType.EXPENSE, ZERO
            ), budget);

            ledger.record(new ActualTransaction(
                "TX003", budget.id(), "EXP002", "OPS",
                1, money("55000"), AccountType.EXPENSE, money("450")
            ), budget);

            ledger.record(new ActualTransaction(
                "TX004", budget.id(), "EXP003", "IT",
                1, money("19000"), AccountType.EXPENSE, money("500")
            ), budget);

            VarianceService varianceService = new VarianceService();

            List<VarianceResult> annual =
                varianceService.analyze(budget, ledger, null);

            ReportingService.print(annual);

            System.out.println("\nMONTHLY VARIANCE");

            List<VarianceResult> monthly =
                varianceService.analyze(budget, ledger, 1);

            ReportingService.print(monthly);

            System.out.println("\nFLEXIBLE BUDGET VARIANCE");

            List<VarianceResult> flexible =
                varianceService.analyzeFlexible(
                    budget,
                    ledger,
                    1,
                    Map.of(
                        "OPS", money("450"),
                        "IT", money("500")
                    )
                );

            ReportingService.print(flexible);

            System.out.println("\nDEPARTMENT SUMMARY");

            ReportingService.departmentSummary(annual)
                .forEach((department, values) ->
                    System.out.printf(
                        "%s | Budget: %s | Actual: %s | Variance: %s%n",
                        department,
                        values[0],
                        values[1],
                        values[2]
                    )
                );

            System.out.println("\nFORECASTING");

            System.out.println(
                "Projected annual expense: " +
                ReportingService.forecast(
                    money("55000"),
                    1
                )
            );

            System.out.println("\nUTILIZATION");

            System.out.println(
                "Operations utilization: " +
                ReportingService.utilization(
                    money("55000"),
                    money("600000")
                ) + "%"
            );

            System.out.println("\nVALIDATION");

            if (varianceService.classify(
                AccountType.REVENUE,
                money("100")
            ) != VarianceStatus.FAVORABLE) {
                throw new IllegalStateException(
                    "Revenue classification failed."
                );
            }

            if (varianceService.classify(
                AccountType.EXPENSE,
                money("100")
            ) != VarianceStatus.UNFAVORABLE) {
                throw new IllegalStateException(
                    "Expense classification failed."
                );
            }

            if (varianceService.classify(
                AccountType.EXPENSE,
                ZERO
            ) != VarianceStatus.ON_TARGET) {
                throw new IllegalStateException(
                    "Zero variance classification failed."
                );
            }

            try {
                ledger.record(new ActualTransaction(
                    "TX001", budget.id(), "REV001", "FIN",
                    1, money("100"), AccountType.REVENUE, ZERO
                ), budget);
            } catch (BudgetValidationException exception) {
                System.out.println(exception.getMessage());
            }

            System.out.println(
                "Audit events recorded: " + budget.auditEvents().size()
            );

            System.out.println("All validation checks passed.");

        } catch (RuntimeException exception) {
            System.err.println(
                "Budget management failure: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
