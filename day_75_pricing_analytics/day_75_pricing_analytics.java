import java.util.*;
import java.util.stream.Collectors;

/**
 * Pricing Analytics Enterprise Engine
 *
 * Java 17
 *
 * Models:
 * - Product and customer segments
 * - Pricing strategies
 * - Demand elasticity
 * - Pricing approval workflows
 * - Enterprise pricing policies
 * - Price optimization
 * - Competitor intelligence
 * - Immutable recommendation records
 */

public class PricingAnalyticsEnterprise {

    enum PricingStrategy {
        COST_PLUS,
        VALUE_BASED,
        COMPETITIVE,
        PENETRATION,
        PREMIUM,
        DYNAMIC
    }

    enum Objective {
        REVENUE,
        PROFIT
    }

    enum ApprovalStatus {
        APPROVED,
        REJECTED,
        PENDING
    }

    enum RecommendationStatus {
        PROPOSED,
        APPROVED,
        REJECTED
    }

    static class PricingException extends RuntimeException {
        PricingException(String message) {
            super(message);
        }
    }

    record Product(
        String id,
        String name,
        double unitCost,
        double referencePrice,
        double minimumPrice,
        double maximumPrice,
        int inventory
    ) {
        Product {
            Objects.requireNonNull(id);
            Objects.requireNonNull(name);

            if (id.isBlank() || name.isBlank() ||
                !Double.isFinite(unitCost) ||
                !Double.isFinite(referencePrice) ||
                !Double.isFinite(minimumPrice) ||
                !Double.isFinite(maximumPrice) ||
                unitCost < 0 ||
                referencePrice <= 0 ||
                minimumPrice <= unitCost ||
                maximumPrice < minimumPrice ||
                inventory < 0) {
                throw new PricingException("Invalid product.");
            }
        }
    }

    record CustomerSegment(
        String name,
        double baseDemand,
        double elasticity
    ) {
        CustomerSegment {
            if (name == null || name.isBlank() ||
                baseDemand < 0 ||
                elasticity >= 0 ||
                !Double.isFinite(elasticity)) {
                throw new PricingException(
                    "Invalid customer segment."
                );
            }
        }
    }

    record Competitor(
        String name,
        double price
    ) {
        Competitor {
            if (name == null || name.isBlank() || price <= 0 ||
                !Double.isFinite(price)) {
                throw new PricingException(
                    "Invalid competitor information."
                );
            }
        }
    }

    record ReviewDecision(
        String reviewer,
        ApprovalStatus status,
        String rationale
    ) {
        ReviewDecision {
            if (reviewer == null || reviewer.isBlank()) {
                throw new PricingException(
                    "Reviewer identity is required."
                );
            }

            Objects.requireNonNull(status);
            Objects.requireNonNull(rationale);
        }
    }

    record PricingMetrics(
        double price,
        double demand,
        double revenue,
        double variableCost,
        double profit,
        double margin
    ) {}

    record PricingRecommendation(
        String productId,
        PricingStrategy strategy,
        Objective objective,
        PricingMetrics metrics,
        RecommendationStatus status,
        List<String> policyViolations
    ) {
        PricingRecommendation {
            policyViolations = List.copyOf(policyViolations);
        }
    }

    interface DemandModel {
        double forecast(double price);
    }

    static final class ConstantElasticityModel
            implements DemandModel {

        private final double basePrice;
        private final List<CustomerSegment> segments;

        ConstantElasticityModel(
            double basePrice,
            List<CustomerSegment> segments
        ) {
            if (basePrice <= 0 || segments.isEmpty()) {
                throw new PricingException(
                    "Invalid demand model configuration."
                );
            }

            this.basePrice = basePrice;
            this.segments = List.copyOf(segments);
        }

        @Override
        public double forecast(double price) {
            if (price <= 0) {
                throw new PricingException(
                    "Price must be positive."
                );
            }

            return segments.stream()
                .mapToDouble(segment ->
                    segment.baseDemand() *
                    Math.pow(
                        price / basePrice,
                        segment.elasticity()
                    )
                )
                .sum();
        }
    }

    static final class PricingPolicy {

        private final double minimumMargin;
        private final double maximumDiscount;
        private final int requiredApprovals;
        private final Set<PricingStrategy> permittedStrategies;

        PricingPolicy(
            double minimumMargin,
            double maximumDiscount,
            int requiredApprovals,
            Set<PricingStrategy> permittedStrategies
        ) {
            if (minimumMargin < 0 ||
                minimumMargin >= 1 ||
                maximumDiscount < 0 ||
                maximumDiscount >= 1 ||
                requiredApprovals < 0 ||
                permittedStrategies.isEmpty()) {
                throw new PricingException(
                    "Invalid pricing policy."
                );
            }

            this.minimumMargin = minimumMargin;
            this.maximumDiscount = maximumDiscount;
            this.requiredApprovals = requiredApprovals;

            this.permittedStrategies =
                Set.copyOf(permittedStrategies);
        }

        List<String> evaluate(
            Product product,
            PricingMetrics metrics,
            PricingStrategy strategy,
            int approvalCount
        ) {
            List<String> violations = new ArrayList<>();

            if (!permittedStrategies.contains(strategy)) {
                violations.add("Strategy not authorized.");
            }

            if (metrics.price() < product.minimumPrice() ||
                metrics.price() > product.maximumPrice()) {
                violations.add("Price outside permitted boundaries.");
            }

            if (metrics.margin() < minimumMargin) {
                violations.add("Minimum margin not achieved.");
            }

            double lowestDiscountPrice =
                product.referencePrice() * (1 - maximumDiscount);

            if (metrics.price() < lowestDiscountPrice) {
                violations.add("Maximum discount exceeded.");
            }

            if (approvalCount < requiredApprovals) {
                violations.add("Insufficient approvals.");
            }

            if (metrics.demand() > product.inventory()) {
                violations.add("Inventory capacity exceeded.");
            }

            return List.copyOf(violations);
        }
    }

    static final class ApprovalService {

        private final Map<String, ReviewDecision> decisions =
            new LinkedHashMap<>();

        void submit(ReviewDecision decision) {
            if (decisions.containsKey(decision.reviewer())) {
                throw new PricingException(
                    "Reviewer has already submitted a decision."
                );
            }

            decisions.put(decision.reviewer(), decision);
        }

        int approvedCount() {
            return (int) decisions.values().stream()
                .filter(d -> d.status() == ApprovalStatus.APPROVED)
                .count();
        }

        boolean hasRejection() {
            return decisions.values().stream()
                .anyMatch(d -> d.status() == ApprovalStatus.REJECTED);
        }

        List<ReviewDecision> decisions() {
            return List.copyOf(decisions.values());
        }
    }

    static final class PricingService {

        private final Product product;
        private final DemandModel demandModel;
        private final PricingPolicy policy;
        private final ApprovalService approvalService;

        private final List<PricingRecommendation> history =
            new ArrayList<>();

        PricingService(
            Product product,
            DemandModel demandModel,
            PricingPolicy policy,
            ApprovalService approvalService
        ) {
            this.product = Objects.requireNonNull(product);
            this.demandModel = Objects.requireNonNull(demandModel);
            this.policy = Objects.requireNonNull(policy);
            this.approvalService =
                Objects.requireNonNull(approvalService);
        }

        PricingMetrics calculate(double price) {
            if (price <= 0) {
                throw new PricingException(
                    "Price must be positive."
                );
            }

            double demand = Math.min(
                demandModel.forecast(price),
                product.inventory()
            );

            double revenue = price * demand;
            double variableCost = product.unitCost() * demand;
            double profit = revenue - variableCost;
            double margin = revenue == 0 ? 0 : profit / revenue;

            return new PricingMetrics(
                price,
                demand,
                revenue,
                variableCost,
                profit,
                margin
            );
        }

        PricingRecommendation optimize(
            Objective objective,
            double step,
            PricingStrategy strategy
        ) {
            if (step <= 0 || !Double.isFinite(step)) {
                throw new PricingException(
                    "Invalid optimization step."
                );
            }

            if (approvalService.hasRejection()) {
                throw new PricingException(
                    "Rejected pricing proposal cannot be approved."
                );
            }

            PricingRecommendation best = null;

            for (
                double price = product.minimumPrice();
                price <= product.maximumPrice() + 1e-9;
                price += step
            ) {
                PricingMetrics metrics = calculate(price);

                List<String> violations = policy.evaluate(
                    product,
                    metrics,
                    strategy,
                    approvalService.approvedCount()
                );

                if (!violations.isEmpty()) {
                    continue;
                }

                PricingRecommendation candidate =
                    new PricingRecommendation(
                        product.id(),
                        strategy,
                        objective,
                        metrics,
                        RecommendationStatus.PROPOSED,
                        violations
                    );

                if (best == null ||
                    score(metrics, objective) >
                    score(best.metrics(), objective) ||
                    (score(metrics, objective) ==
                     score(best.metrics(), objective) &&
                     price > best.metrics().price())) {

                    best = candidate;
                }
            }

            if (best == null) {
                throw new PricingException(
                    "No eligible pricing recommendation exists."
                );
            }

            history.add(best);
            return best;
        }

        private double score(
            PricingMetrics metrics,
            Objective objective
        ) {
            return objective == Objective.PROFIT
                ? metrics.profit()
                : metrics.revenue();
        }

        List<PricingRecommendation> history() {
            return List.copyOf(history);
        }
    }

    static final class MarketAnalyzer {

        static double averageCompetitorPrice(
            List<Competitor> competitors
        ) {
            if (competitors.isEmpty()) {
                throw new PricingException(
                    "Competitor information is missing."
                );
            }

            return competitors.stream()
                .mapToDouble(Competitor::price)
                .average()
                .orElseThrow();
        }

        static double costPlusPrice(
            Product product,
            double markup
        ) {
            if (markup < 0 || !Double.isFinite(markup)) {
                throw new PricingException(
                    "Invalid markup."
                );
            }

            return product.unitCost() * (1 + markup);
        }

        static double estimateElasticity(
            Map<Double, Double> observations
        ) {
            List<Map.Entry<Double, Double>> valid =
                observations.entrySet().stream()
                    .filter(entry ->
                        entry.getKey() > 0 &&
                        entry.getValue() > 0
                    )
                    .collect(Collectors.toList());

            if (valid.size() < 3) {
                throw new PricingException(
                    "At least three observations are required."
                );
            }

            double meanX = valid.stream()
                .mapToDouble(e -> Math.log(e.getKey()))
                .average().orElseThrow();

            double meanY = valid.stream()
                .mapToDouble(e -> Math.log(e.getValue()))
                .average().orElseThrow();

            double numerator = 0;
            double denominator = 0;

            for (var observation : valid) {
                double x = Math.log(observation.getKey());
                double y = Math.log(observation.getValue());

                numerator += (x - meanX) * (y - meanY);
                denominator += Math.pow(x - meanX, 2);
            }

            if (denominator < 1e-12) {
                throw new PricingException(
                    "Insufficient price variation."
                );
            }

            double elasticity = numerator / denominator;

            if (elasticity >= 0) {
                throw new PricingException(
                    "Unexpected positive elasticity."
                );
            }

            return elasticity;
        }
    }

    public static void main(String[] args) {

        try {
            Product product = new Product(
                "ENT-500",
                "Enterprise Analytics Platform",
                220,
                500,
                300,
                900,
                1000
            );

            List<CustomerSegment> segments = List.of(
                new CustomerSegment("SMB", 75, -1.5),
                new CustomerSegment("Corporate", 45, -0.9),
                new CustomerSegment("Enterprise", 25, -0.6)
            );

            DemandModel model = new ConstantElasticityModel(
                product.referencePrice(),
                segments
            );

            PricingPolicy policy = new PricingPolicy(
                0.20,
                0.40,
                2,
                EnumSet.allOf(PricingStrategy.class)
            );

            ApprovalService approvals = new ApprovalService();

            approvals.submit(new ReviewDecision(
                "Pricing Manager",
                ApprovalStatus.APPROVED,
                "Margin and cost structure validated."
            ));

            approvals.submit(new ReviewDecision(
                "Commercial Director",
                ApprovalStatus.APPROVED,
                "Market positioning accepted."
            ));

            PricingService service = new PricingService(
                product,
                model,
                policy,
                approvals
            );

            Map<Double, Double> historical = new LinkedHashMap<>();

            historical.put(400.0, 150.0);
            historical.put(450.0, 133.0);
            historical.put(500.0, 115.0);
            historical.put(550.0, 105.0);
            historical.put(600.0, 94.0);
            historical.put(650.0, 86.0);

            double elasticity =
                MarketAnalyzer.estimateElasticity(historical);

            List<Competitor> competitors = List.of(
                new Competitor("Market A", 520),
                new Competitor("Market B", 540),
                new Competitor("Market C", 560)
            );

            double benchmark =
                MarketAnalyzer.averageCompetitorPrice(competitors);

            double costPlus =
                MarketAnalyzer.costPlusPrice(product, 0.60);

            System.out.printf(
                "Estimated elasticity: %.4f%n",
                elasticity
            );

            System.out.printf(
                "Competitor average: %.2f%n",
                benchmark
            );

            System.out.printf(
                "Cost-plus reference: %.2f%n",
                costPlus
            );

            PricingRecommendation profit = service.optimize(
                Objective.PROFIT,
                5,
                PricingStrategy.DYNAMIC
            );

            PricingRecommendation revenue = service.optimize(
                Objective.REVENUE,
                5,
                PricingStrategy.DYNAMIC
            );

            printRecommendation(profit);
            printRecommendation(revenue);

            if (profit.metrics().demand() > product.inventory()) {
                throw new PricingException(
                    "Inventory constraint violated."
                );
            }

            System.out.println("\nRecommendation history:");

            service.history().forEach(item ->
                System.out.printf(
                    "%s | %s | Price %.2f | Profit %.2f%n",
                    item.productId(),
                    item.objective(),
                    item.metrics().price(),
                    item.metrics().profit()
                )
            );

            System.out.println(
                "\nEnterprise pricing validations passed."
            );

        } catch (PricingException exception) {
            System.err.println(
                "Pricing error: " + exception.getMessage()
            );
            System.exit(1);
        }
    }

    private static void printRecommendation(
        PricingRecommendation recommendation
    ) {
        PricingMetrics m = recommendation.metrics();

        System.out.println("\nPRICING RECOMMENDATION");
        System.out.println("-----------------------------");
        System.out.println("Product: " + recommendation.productId());
        System.out.println("Strategy: " + recommendation.strategy());
        System.out.println("Objective: " + recommendation.objective());

        System.out.printf("Price: %.2f%n", m.price());
        System.out.printf("Demand: %.2f%n", m.demand());
        System.out.printf("Revenue: %.2f%n", m.revenue());
        System.out.printf("Variable cost: %.2f%n", m.variableCost());
        System.out.printf("Profit: %.2f%n", m.profit());
        System.out.printf("Margin: %.2f%%%n", m.margin() * 100);

        System.out.println(
            "Status: " + recommendation.status()
        );
    }
}
