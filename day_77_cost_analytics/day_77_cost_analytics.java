import java.time.Instant;
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

/**
 * Enterprise Cost Analytics and Cost Optimization Platform.
 *
 * Java 17
 *
 * Features:
 * - Immutable financial domain records
 * - Cost classification and allocation
 * - Departmental budget management
 * - Unit economics
 * - Contribution analysis
 * - Optimization policies
 * - Approval workflows
 * - Audit history
 * - Enterprise service architecture
 */
public class CostAnalyticsEnterprise {

    enum CostType {
        FIXED,
        VARIABLE,
        SEMI_VARIABLE
    }

    enum CostBehavior {
        DIRECT,
        INDIRECT
    }

    enum Category {
        LABOR,
        MATERIALS,
        TECHNOLOGY,
        FACILITIES,
        LOGISTICS,
        ADMINISTRATION
    }

    enum ProposalStatus {
        PENDING,
        APPROVED,
        REJECTED
    }

    enum ApprovalRole {
        FINANCE_MANAGER,
        OPERATIONS_MANAGER,
        CFO
    }

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static void validateMoney(double value, String field) {
        if (!Double.isFinite(value) || value < 0) {
            throw new DomainException(
                field + " must be finite and non-negative."
            );
        }
    }

    static void validateText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new DomainException(field + " is required.");
        }
    }

    record CostRecord(
        String id,
        String costCenter,
        String period,
        Category category,
        CostType costType,
        CostBehavior behavior,
        double amount,
        double activityUnits,
        String description
    ) {
        CostRecord {
            validateText(id, "Record ID");
            validateText(costCenter, "Cost centre");
            validateText(period, "Period");
            validateText(description, "Description");

            Objects.requireNonNull(category);
            Objects.requireNonNull(costType);
            Objects.requireNonNull(behavior);

            validateMoney(amount, "Cost amount");
            validateMoney(activityUnits, "Activity units");
        }
    }

    record Budget(
        String costCenter,
        String period,
        double allocatedAmount
    ) {
        Budget {
            validateText(costCenter, "Cost centre");
            validateText(period, "Period");
            validateMoney(allocatedAmount, "Budget");
        }
    }

    record OptimizationProposal(
        String id,
        String name,
        Category category,
        double reductionRate,
        double implementationCost,
        double riskScore,
        String rationale
    ) {
        OptimizationProposal {
            validateText(id, "Proposal ID");
            validateText(name, "Proposal name");
            validateText(rationale, "Rationale");

            Objects.requireNonNull(category);

            if (
                !Double.isFinite(reductionRate)
                || reductionRate < 0
                || reductionRate > 1
            ) {
                throw new DomainException("Invalid reduction rate.");
            }

            validateMoney(implementationCost, "Implementation cost");

            if (
                !Double.isFinite(riskScore)
                || riskScore < 0
                || riskScore > 10
            ) {
                throw new DomainException("Risk must be between 0 and 10.");
            }
        }
    }

    record OptimizationDecision(
        String proposalId,
        double baselineCost,
        double grossSavings,
        double implementationCost,
        double netSavings,
        boolean eligible,
        String reason
    ) {}

    record Approval(
        String proposalId,
        String reviewer,
        ApprovalRole role,
        boolean approved,
        String comment,
        Instant timestamp
    ) {
        Approval {
            validateText(proposalId, "Proposal ID");
            validateText(reviewer, "Reviewer");
            validateText(comment, "Approval comment");
            Objects.requireNonNull(role);
            Objects.requireNonNull(timestamp);
        }
    }

    record AuditEvent(
        String eventId,
        String action,
        String actor,
        String entityId,
        Instant timestamp,
        String details
    ) {}

    record AnalyticsReport(
        String period,
        double totalCost,
        double unitCost,
        Map<String, Double> costCenters,
        Map<Category, Double> categories
    ) {
        AnalyticsReport {
            costCenters = Collections.unmodifiableMap(
                new HashMap<>(costCenters)
            );

            categories = Collections.unmodifiableMap(
                new EnumMap<>(categories)
            );
        }
    }

    interface CostRepository {
        void save(CostRecord record);

        List<CostRecord> findByPeriod(String period);

        List<CostRecord> findByCenter(
            String period,
            String costCenter
        );
    }

    static class InMemoryCostRepository implements CostRepository {
        private final Map<String, CostRecord> records =
            new HashMap<>();

        @Override
        public synchronized void save(CostRecord record) {
            Objects.requireNonNull(record);

            if (records.containsKey(record.id())) {
                throw new DomainException(
                    "Duplicate financial record: " + record.id()
                );
            }

            records.put(record.id(), record);
        }

        @Override
        public synchronized List<CostRecord> findByPeriod(
            String period
        ) {
            return records.values()
                .stream()
                .filter(record -> record.period().equals(period))
                .toList();
        }

        @Override
        public synchronized List<CostRecord> findByCenter(
            String period,
            String center
        ) {
            return records.values()
                .stream()
                .filter(record ->
                    record.period().equals(period)
                    && record.costCenter().equals(center)
                )
                .toList();
        }
    }

    static class AuditService {
        private final List<AuditEvent> events = new ArrayList<>();

        public synchronized void record(
            String action,
            String actor,
            String entityId,
            String details
        ) {
            validateText(action, "Action");
            validateText(actor, "Actor");
            validateText(entityId, "Entity ID");

            events.add(new AuditEvent(
                UUID.randomUUID().toString(),
                action,
                actor,
                entityId,
                Instant.now(),
                details
            ));
        }

        public synchronized List<AuditEvent> history() {
            return List.copyOf(events);
        }
    }

    static class CostAnalyticsService {
        private final CostRepository repository;

        CostAnalyticsService(CostRepository repository) {
            this.repository = repository;
        }

        public double totalCost(String period) {
            return repository.findByPeriod(period)
                .stream()
                .mapToDouble(CostRecord::amount)
                .sum();
        }

        public double unitCost(String period) {
            List<CostRecord> records =
                repository.findByPeriod(period);

            double cost = records.stream()
                .mapToDouble(CostRecord::amount)
                .sum();

            double activity = records.stream()
                .mapToDouble(CostRecord::activityUnits)
                .sum();

            if (activity <= 0) {
                throw new DomainException(
                    "Positive activity is required for unit cost."
                );
            }

            return cost / activity;
        }

        public Map<Category, Double> categoryReport(String period) {
            Map<Category, Double> result =
                new EnumMap<>(Category.class);

            for (CostRecord record :
                 repository.findByPeriod(period)) {

                result.merge(
                    record.category(),
                    record.amount(),
                    Double::sum
                );
            }

            return Collections.unmodifiableMap(result);
        }

        public Map<String, Double> costCenterReport(String period) {
            return repository.findByPeriod(period)
                .stream()
                .collect(Collectors.groupingBy(
                    CostRecord::costCenter,
                    Collectors.summingDouble(CostRecord::amount)
                ));
        }

        public Map<String, Double> breakEven(
            double fixedCost,
            double sellingPrice,
            double variableCost
        ) {
            validateMoney(fixedCost, "Fixed cost");
            validateMoney(sellingPrice, "Selling price");
            validateMoney(variableCost, "Variable cost");

            if (sellingPrice <= variableCost) {
                throw new DomainException(
                    "Selling price must exceed variable cost."
                );
            }

            double contribution = sellingPrice - variableCost;
            double units = Math.ceil(fixedCost / contribution);

            return Map.of(
                "contributionPerUnit", contribution,
                "contributionMarginPercent",
                    contribution / sellingPrice * 100,
                "breakEvenUnits", units,
                "breakEvenRevenue", units * sellingPrice
            );
        }

        public Map<String, Double> budgetVariance(
            Budget budget,
            double actual
        ) {
            validateMoney(actual, "Actual expenditure");

            double variance = budget.allocatedAmount() - actual;

            double percentage = budget.allocatedAmount() == 0
                ? 0
                : variance / budget.allocatedAmount() * 100;

            return Map.of(
                "budget", budget.allocatedAmount(),
                "actual", actual,
                "variance", variance,
                "variancePercent", percentage
            );
        }

        public Map<String, Map<String, Double>> allocateIndirect(
            String period
        ) {
            Map<String, Double> direct = new HashMap<>();
            double indirect = 0;

            for (CostRecord record :
                 repository.findByPeriod(period)) {

                if (record.behavior() == CostBehavior.DIRECT) {
                    direct.merge(
                        record.costCenter(),
                        record.amount(),
                        Double::sum
                    );
                } else {
                    indirect += record.amount();
                }
            }

            double base = direct.values()
                .stream()
                .mapToDouble(Double::doubleValue)
                .sum();

            if (base == 0 && indirect > 0) {
                throw new DomainException(
                    "No direct-cost allocation base exists."
                );
            }

            Map<String, Map<String, Double>> result =
                new HashMap<>();

            direct.forEach((center, amount) -> {
                double allocation = base == 0
                    ? 0
                    : indirect * amount / base;

                result.put(center, Map.of(
                    "directCost", amount,
                    "allocatedIndirect", allocation,
                    "totalCost", amount + allocation
                ));
            });

            return Collections.unmodifiableMap(result);
        }

        public AnalyticsReport generateReport(String period) {
            return new AnalyticsReport(
                period,
                totalCost(period),
                unitCost(period),
                costCenterReport(period),
                categoryReport(period)
            );
        }
    }

    static class OptimizationPolicy {
        private final double maximumRisk;
        private final double minimumReduction;
        private final double minimumNetSavings;

        OptimizationPolicy(
            double maximumRisk,
            double minimumReduction,
            double minimumNetSavings
        ) {
            if (
                !Double.isFinite(maximumRisk)
                || maximumRisk < 0
                || maximumRisk > 10
            ) {
                throw new DomainException("Invalid maximum risk.");
            }

            if (
                !Double.isFinite(minimumReduction)
                || minimumReduction < 0
                || minimumReduction > 1
            ) {
                throw new DomainException("Invalid reduction threshold.");
            }

            validateMoney(minimumNetSavings, "Minimum net savings");

            this.maximumRisk = maximumRisk;
            this.minimumReduction = minimumReduction;
            this.minimumNetSavings = minimumNetSavings;
        }

        boolean permits(
            OptimizationProposal proposal,
            double baseline,
            double netSavings
        ) {
            return baseline > 0
                && proposal.riskScore() <= maximumRisk
                && proposal.reductionRate() >= minimumReduction
                && netSavings >= minimumNetSavings;
        }
    }

    static class OptimizationService {
        private final CostRepository repository;
        private final OptimizationPolicy policy;

        OptimizationService(
            CostRepository repository,
            OptimizationPolicy policy
        ) {
            this.repository = repository;
            this.policy = policy;
        }

        public List<OptimizationDecision> evaluate(
            String period,
            List<OptimizationProposal> proposals
        ) {
            Map<Category, Double> baselines =
                new EnumMap<>(Category.class);

            for (CostRecord record :
                 repository.findByPeriod(period)) {

                baselines.merge(
                    record.category(),
                    record.amount(),
                    Double::sum
                );
            }

            List<OptimizationDecision> decisions =
                new ArrayList<>();

            for (OptimizationProposal proposal : proposals) {
                double baseline = baselines.getOrDefault(
                    proposal.category(),
                    0.0
                );

                double gross = baseline * proposal.reductionRate();

                double net = gross - proposal.implementationCost();

                boolean eligible = policy.permits(
                    proposal,
                    baseline,
                    net
                );

                String reason = eligible
                    ? "Meets optimization policy."
                    : baseline == 0
                        ? "No baseline expenditure."
                        : proposal.riskScore() > 5
                            ? "Risk exceeds policy."
                            : proposal.reductionRate() < 0.05
                                ? "Reduction is below policy."
                                : "Net savings are insufficient.";

                decisions.add(new OptimizationDecision(
                    proposal.id(),
                    baseline,
                    gross,
                    eligible ? proposal.implementationCost() : 0,
                    eligible ? net : 0,
                    eligible,
                    reason
                ));
            }

            return List.copyOf(decisions);
        }
    }

    static class ApprovalService {
        private final Map<String, List<Approval>> approvals =
            new HashMap<>();

        private final AuditService audit;

        ApprovalService(AuditService audit) {
            this.audit = audit;
        }

        public synchronized void submit(
            String proposalId,
            String reviewer,
            ApprovalRole role,
            boolean approved,
            String comment
        ) {
            validateText(proposalId, "Proposal ID");
            validateText(reviewer, "Reviewer");

            if (comment == null || comment.isBlank()) {
                throw new DomainException(
                    "An approval decision requires a comment."
                );
            }

            List<Approval> history = approvals.computeIfAbsent(
                proposalId,
                key -> new ArrayList<>()
            );

            boolean duplicateReviewer = history.stream()
                .anyMatch(item -> item.reviewer().equals(reviewer));

            if (duplicateReviewer) {
                throw new DomainException(
                    "Reviewer has already submitted a decision."
                );
            }

            Approval approval = new Approval(
                proposalId,
                reviewer,
                role,
                approved,
                comment,
                Instant.now()
            );

            history.add(approval);

            audit.record(
                "APPROVAL_SUBMITTED",
                reviewer,
                proposalId,
                comment
            );
        }

        public synchronized ProposalStatus status(
            String proposalId,
            int requiredApprovals
        ) {
            List<Approval> history = approvals.getOrDefault(
                proposalId,
                List.of()
            );

            if (history.stream().anyMatch(a -> !a.approved())) {
                return ProposalStatus.REJECTED;
            }

            long approved = history.stream()
                .filter(Approval::approved)
                .map(Approval::reviewer)
                .distinct()
                .count();

            return approved >= requiredApprovals
                ? ProposalStatus.APPROVED
                : ProposalStatus.PENDING;
        }
    }

    static void runTests() {
        InMemoryCostRepository repository =
            new InMemoryCostRepository();

        repository.save(new CostRecord(
            "T001", "TEST", "2026-10",
            Category.LABOR, CostType.FIXED,
            CostBehavior.DIRECT, 100, 10, "Test record"
        ));

        CostAnalyticsService analytics =
            new CostAnalyticsService(repository);

        if (analytics.unitCost("2026-10") != 10) {
            throw new AssertionError("Unit cost test failed.");
        }

        if (
            analytics.breakEven(1000, 100, 60)
                .get("breakEvenUnits") != 25
        ) {
            throw new AssertionError("Break-even test failed.");
        }

        try {
            repository.save(new CostRecord(
                "T001", "TEST", "2026-10",
                Category.LABOR, CostType.FIXED,
                CostBehavior.DIRECT, 100, 10, "Duplicate"
            ));

            throw new AssertionError("Duplicate accepted.");
        } catch (DomainException expected) {
            // Expected duplicate rejection.
        }

        System.out.println("All Java validation tests passed.");
    }

    public static void main(String[] args) {
        try {
            runTests();

            InMemoryCostRepository repository =
                new InMemoryCostRepository();

            String period = "2026-10";

            repository.save(new CostRecord(
                "C001", "PRODUCTION", period,
                Category.LABOR, CostType.FIXED,
                CostBehavior.DIRECT, 120000, 1000,
                "Production workforce"
            ));

            repository.save(new CostRecord(
                "C002", "PRODUCTION", period,
                Category.MATERIALS, CostType.VARIABLE,
                CostBehavior.DIRECT, 180000, 1000,
                "Raw material"
            ));

            repository.save(new CostRecord(
                "C003", "PRODUCTION", period,
                Category.FACILITIES, CostType.FIXED,
                CostBehavior.INDIRECT, 45000, 1000,
                "Factory facilities"
            ));

            repository.save(new CostRecord(
                "C004", "TECHNOLOGY", period,
                Category.TECHNOLOGY, CostType.SEMI_VARIABLE,
                CostBehavior.INDIRECT, 60000, 1000,
                "Cloud infrastructure"
            ));

            repository.save(new CostRecord(
                "C005", "LOGISTICS", period,
                Category.LOGISTICS, CostType.VARIABLE,
                CostBehavior.DIRECT, 35000, 1000,
                "Distribution"
            ));

            repository.save(new CostRecord(
                "C006", "ADMINISTRATION", period,
                Category.ADMINISTRATION, CostType.FIXED,
                CostBehavior.INDIRECT, 25000, 1000,
                "Administrative services"
            ));

            AuditService audit = new AuditService();

            CostAnalyticsService analytics =
                new CostAnalyticsService(repository);

            System.out.println("\nENTERPRISE COST ANALYTICS");
            System.out.println("==============================");

            AnalyticsReport report =
                analytics.generateReport(period);

            System.out.printf(
                "Total cost: Rs. %.2f%n",
                report.totalCost()
            );

            System.out.printf(
                "Unit cost: Rs. %.2f%n",
                report.unitCost()
            );

            System.out.println("\nCost centre report:");
            report.costCenters().forEach((center, amount) ->
                System.out.printf(
                    "%-25s Rs. %.2f%n",
                    center,
                    amount
                )
            );

            System.out.println("\nCategory report:");
            report.categories().forEach((category, amount) ->
                System.out.printf(
                    "%-20s Rs. %.2f%n",
                    category,
                    amount
                )
            );

            System.out.println("\nBreak-even analysis:");

            analytics.breakEven(150000, 500, 300)
                .forEach((key, value) ->
                    System.out.println(key + ": " + value)
                );

            System.out.println("\nBudget variance:");

            Budget budget = new Budget(
                "PRODUCTION",
                period,
                350000
            );

            analytics.budgetVariance(budget, 345000)
                .forEach((key, value) ->
                    System.out.println(key + ": " + value)
                );

            System.out.println("\nIndirect allocation:");

            analytics.allocateIndirect(period)
                .forEach((center, allocation) ->
                    System.out.println(center + ": " + allocation)
                );

            OptimizationPolicy policy =
                new OptimizationPolicy(5, 0.05, 1000);

            OptimizationService optimization =
                new OptimizationService(repository, policy);

            List<OptimizationProposal> proposals = List.of(
                new OptimizationProposal(
                    "P001",
                    "Cloud capacity rightsizing",
                    Category.TECHNOLOGY,
                    0.20,
                    3000,
                    2,
                    "Reduce unused cloud capacity."
                ),
                new OptimizationProposal(
                    "P002",
                    "Procurement consolidation",
                    Category.MATERIALS,
                    0.08,
                    5000,
                    3,
                    "Consolidate supplier purchases."
                ),
                new OptimizationProposal(
                    "P003",
                    "Logistics route optimization",
                    Category.LOGISTICS,
                    0.15,
                    2000,
                    4,
                    "Improve distribution efficiency."
                ),
                new OptimizationProposal(
                    "P004",
                    "High-risk workforce reduction",
                    Category.LABOR,
                    0.10,
                    1000,
                    9,
                    "Risk exceeds permitted threshold."
                )
            );

            List<OptimizationDecision> decisions =
                optimization.evaluate(period, proposals);

            System.out.println("\nOptimization decisions:");

            decisions.forEach(System.out::println);

            ApprovalService approvalService =
                new ApprovalService(audit);

            approvalService.submit(
                "P001",
                "finance.manager",
                ApprovalRole.FINANCE_MANAGER,
                true,
                "Financial savings validated."
            );

            approvalService.submit(
                "P001",
                "operations.manager",
                ApprovalRole.OPERATIONS_MANAGER,
                true,
                "Operational impact accepted."
            );

            System.out.println(
                "\nProposal P001 approval status: "
                + approvalService.status("P001", 2)
            );

            audit.record(
                "REPORT_GENERATED",
                "system",
                period,
                "Monthly cost report generated."
            );

            System.out.println("\nAudit events:");

            audit.history().forEach(System.out::println);

        } catch (DomainException error) {
            System.err.println(
                "Business validation failure: " + error.getMessage()
            );
            System.exit(1);
        } catch (Exception error) {
            System.err.println(
                "Application failure: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
