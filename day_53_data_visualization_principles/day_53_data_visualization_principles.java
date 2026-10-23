import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

public class VisualizationGovernance {

    enum AnalyticalIntent {
        COMPARISON,
        RELATIONSHIP,
        DISTRIBUTION,
        COMPOSITION,
        TREND,
        MATRIX
    }

    enum ChartType {
        HORIZONTAL_BAR,
        DOT_PLOT,
        SCATTER_PLOT,
        HISTOGRAM,
        BOX_PLOT,
        STACKED_BAR,
        PIE,
        LINE,
        HEATMAP
    }

    enum ReviewState {
        PROPOSED,
        VALIDATED,
        REJECTED
    }

    record Recommendation(
        ChartType chart,
        double score,
        String purpose,
        String rationale,
        List<String> warnings
    ) {
        Recommendation {
            Objects.requireNonNull(chart);
            Objects.requireNonNull(purpose);
            Objects.requireNonNull(rationale);
            warnings = List.copyOf(warnings);

            if (score < 0.0 || score > 1.0) {
                throw new IllegalArgumentException("score must be between 0 and 1");
            }
        }
    }

    record VisualizationRequest(
        AnalyticalIntent intent,
        List<String> categories,
        List<Double> values,
        List<Double> x,
        List<Double> y,
        List<List<Double>> matrix,
        boolean ordered
    ) {
        VisualizationRequest {
            Objects.requireNonNull(intent);
            categories = categories == null ? List.of() : List.copyOf(categories);
            values = values == null ? List.of() : List.copyOf(values);
            x = x == null ? List.of() : List.copyOf(x);
            y = y == null ? List.of() : List.copyOf(y);
            matrix = matrix == null
                ? List.of()
                : matrix.stream().map(List::copyOf).toList();
        }
    }

    record Evaluation(
        Instant evaluatedAt,
        ReviewState state,
        VisualizationRequest request,
        List<Recommendation> recommendations,
        List<String> policyViolations
    ) {
        Evaluation {
            recommendations = List.copyOf(recommendations);
            policyViolations = List.copyOf(policyViolations);
        }

        boolean accepted() {
            return state == ReviewState.VALIDATED && policyViolations.isEmpty();
        }
    }

    static final class VisualizationPolicy {
        private final Map<AnalyticalIntent, Integer> minimumObservations =
            new EnumMap<>(AnalyticalIntent.class);

        VisualizationPolicy() {
            minimumObservations.put(AnalyticalIntent.COMPARISON, 1);
            minimumObservations.put(AnalyticalIntent.RELATIONSHIP, 2);
            minimumObservations.put(AnalyticalIntent.DISTRIBUTION, 2);
            minimumObservations.put(AnalyticalIntent.COMPOSITION, 1);
            minimumObservations.put(AnalyticalIntent.TREND, 2);
            minimumObservations.put(AnalyticalIntent.MATRIX, 1);
        }

        List<String> validate(VisualizationRequest request) {
            List<String> violations = new ArrayList<>();

            switch (request.intent()) {
                case COMPARISON, COMPOSITION -> {
                    if (request.categories().isEmpty() ||
                        request.categories().size() != request.values().size()) {
                        violations.add(
                            "Category and value collections must be non-empty and equal in size."
                        );
                    }
                    validateNumbers(request.values(), "values", violations);
                }

                case RELATIONSHIP -> {
                    if (request.x().size() != request.y().size() ||
                        request.x().size() < 2) {
                        violations.add(
                            "Relationship analysis requires equally sized x/y data with at least two observations."
                        );
                    }
                    validateNumbers(request.x(), "x", violations);
                    validateNumbers(request.y(), "y", violations);
                }

                case DISTRIBUTION, TREND -> {
                    int minimum =
                        minimumObservations.get(request.intent());

                    if (request.values().size() < minimum) {
                        violations.add(
                            "Insufficient observations for " +
                            request.intent().name().toLowerCase()
                        );
                    }
                    validateNumbers(request.values(), "values", violations);
                }

                case MATRIX -> validateMatrix(request.matrix(), violations);
            }

            return violations;
        }

        private static void validateNumbers(
            List<Double> values,
            String name,
            List<String> violations
        ) {
            for (Double value : values) {
                if (value == null || !Double.isFinite(value)) {
                    violations.add(name + " contains a non-finite value.");
                    return;
                }
            }
        }

        private static void validateMatrix(
            List<List<Double>> matrix,
            List<String> violations
        ) {
            if (matrix.isEmpty() || matrix.getFirst().isEmpty()) {
                violations.add("Matrix must contain non-empty rows.");
                return;
            }

            int width = matrix.getFirst().size();

            for (List<Double> row : matrix) {
                if (row.size() != width) {
                    violations.add("Matrix rows must have equal widths.");
                    return;
                }

                validateNumbers(row, "matrix row", violations);
            }
        }
    }

    static final class RecommendationService {
        private final VisualizationPolicy policy;

        RecommendationService(VisualizationPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        Evaluation evaluate(VisualizationRequest request) {
            List<String> violations = policy.validate(request);

            if (!violations.isEmpty()) {
                return new Evaluation(
                    Instant.now(),
                    ReviewState.REJECTED,
                    request,
                    List.of(),
                    violations
                );
            }

            List<Recommendation> recommendations =
                switch (request.intent()) {
                    case COMPARISON -> comparison(request);
                    case RELATIONSHIP -> relationship(request);
                    case DISTRIBUTION -> distribution();
                    case COMPOSITION -> composition(request);
                    case TREND -> trend();
                    case MATRIX -> matrix();
                };

            recommendations = recommendations.stream()
                .sorted(Comparator.comparingDouble(
                    Recommendation::score
                ).reversed())
                .toList();

            return new Evaluation(
                Instant.now(),
                ReviewState.VALIDATED,
                request,
                recommendations,
                List.of()
            );
        }

        private List<Recommendation> comparison(
            VisualizationRequest request
        ) {
            Set<String> unique =
                Set.copyOf(request.categories());

            double score =
                unique.size() > 20 ? 0.80 : 0.96;

            return List.of(
                new Recommendation(
                    ChartType.HORIZONTAL_BAR,
                    score,
                    "compare categories",
                    "A common quantitative axis supports direct comparison of category magnitudes.",
                    List.of(
                        unique.size() > 20
                            ? "Many categories require filtering or grouping."
                            : "Sort categories when ranking is important."
                    )
                ),
                new Recommendation(
                    ChartType.DOT_PLOT,
                    0.91,
                    "compare precise values",
                    "Position on a shared scale gives compact and accurate comparison.",
                    List.of(
                        "Direct labels are useful when category count is small."
                    )
                )
            );
        }

        private List<Recommendation> relationship(
            VisualizationRequest request
        ) {
            double r = correlation(request.x(), request.y());

            return List.of(
                new Recommendation(
                    ChartType.SCATTER_PLOT,
                    0.98,
                    "show a relationship",
                    "Each observation remains visible for association and outlier analysis; correlation is "
                        + String.format("%.3f", r) + ".",
                    List.of(
                        "Correlation does not establish causation.",
                        "Dense datasets may require aggregation or transparency."
                    )
                )
            );
        }

        private List<Recommendation> distribution() {
            return List.of(
                new Recommendation(
                    ChartType.HISTOGRAM,
                    0.97,
                    "show distribution",
                    "Bins expose concentration, spread, skewness, and possible outliers.",
                    List.of(
                        "Bin width can materially change the visible pattern."
                    )
                ),
                new Recommendation(
                    ChartType.BOX_PLOT,
                    0.93,
                    "compare distribution summaries",
                    "Quartiles and extreme observations provide a compact distribution summary.",
                    List.of(
                        "A box plot hides some multimodal shape."
                    )
                )
            );
        }

        private List<Recommendation> composition(
            VisualizationRequest request
        ) {
            double total =
                request.values().stream()
                    .mapToDouble(Double::doubleValue)
                    .sum();

            boolean invalid =
                total <= 0 ||
                request.values().stream()
                    .anyMatch(value -> value < 0);

            return List.of(
                new Recommendation(
                    ChartType.STACKED_BAR,
                    invalid ? 0.20 : 0.95,
                    "show composition",
                    "A common baseline makes component proportions easier to compare.",
                    List.of(
                        invalid
                            ? "Parts of a whole must be non-negative with a positive total."
                            : "Keep the number of components limited."
                    )
                ),
                new Recommendation(
                    ChartType.PIE,
                    !invalid && request.categories().size() <= 5
                        ? 0.60
                        : 0.25,
                    "show simple composition",
                    "Pie slices communicate broad part-to-whole structure when categories are few.",
                    List.of(
                        "Use bars when precise comparison matters.",
                        "Avoid many slices."
                    )
                )
            );
        }

        private List<Recommendation> trend() {
            return List.of(
                new Recommendation(
                    ChartType.LINE,
                    0.98,
                    "show ordered change",
                    "Connected observations emphasize direction, turning points, and temporal movement.",
                    List.of(
                        "Connect observations only when the ordering represents meaningful continuity."
                    )
                )
            );
        }

        private List<Recommendation> matrix() {
            return List.of(
                new Recommendation(
                    ChartType.HEATMAP,
                    0.97,
                    "show two-dimensional patterns",
                    "Color intensity compactly represents values across two dimensions.",
                    List.of(
                        "Use a perceptually ordered color scale.",
                        "Annotate cells when exact values matter."
                    )
                )
            );
        }

        private static double correlation(
            List<Double> x,
            List<Double> y
        ) {
            double meanX =
                x.stream().mapToDouble(Double::doubleValue).average().orElse(0);
            double meanY =
                y.stream().mapToDouble(Double::doubleValue).average().orElse(0);

            double numerator = 0;
            double xx = 0;
            double yy = 0;

            for (int i = 0; i < x.size(); i++) {
                double dx = x.get(i) - meanX;
                double dy = y.get(i) - meanY;
                numerator += dx * dy;
                xx += dx * dx;
                yy += dy * dy;
            }

            double denominator = Math.sqrt(xx * yy);
            return denominator == 0 ? 0 : numerator / denominator;
        }
    }

    static void printEvaluation(Evaluation evaluation) {
        System.out.println("\nState: " + evaluation.state());
        System.out.println("Evaluated: " + evaluation.evaluatedAt());

        if (!evaluation.policyViolations().isEmpty()) {
            for (String violation : evaluation.policyViolations()) {
                System.out.println("Policy violation: " + violation);
            }
            return;
        }

        for (Recommendation recommendation : evaluation.recommendations()) {
            System.out.printf(
                "%-22s score=%.2f%n",
                recommendation.chart(),
                recommendation.score()
            );
            System.out.println("  Purpose: " + recommendation.purpose());
            System.out.println("  Rationale: " + recommendation.rationale());

            for (String warning : recommendation.warnings()) {
                System.out.println("  Warning: " + warning);
            }
        }
    }

    public static void main(String[] args) {
        VisualizationPolicy policy = new VisualizationPolicy();
        RecommendationService service =
            new RecommendationService(policy);

        VisualizationRequest comparison =
            new VisualizationRequest(
                AnalyticalIntent.COMPARISON,
                List.of(
                    "Cloud",
                    "Security",
                    "Data",
                    "Networking",
                    "Applications"
                ),
                List.of(1840.0, 1320.0, 1610.0, 940.0, 2110.0),
                List.of(),
                List.of(),
                List.of(),
                false
            );

        VisualizationRequest relationship =
            new VisualizationRequest(
                AnalyticalIntent.RELATIONSHIP,
                List.of(),
                List.of(),
                List.of(12.0, 18.0, 21.0, 27.0, 30.0, 35.0, 41.0, 48.0),
                List.of(17.0, 15.0, 14.0, 12.0, 11.0, 9.0, 8.0, 6.0),
                List.of(),
                false
            );

        VisualizationRequest matrix =
            new VisualizationRequest(
                AnalyticalIntent.MATRIX,
                List.of(),
                List.of(),
                List.of(),
                List.of(),
                List.of(
                    List.of(92.0, 84.0, 76.0),
                    List.of(71.0, 88.0, 94.0),
                    List.of(63.0, 79.0, 91.0),
                    List.of(55.0, 68.0, 83.0)
                ),
                false
            );

        System.out.println("COMPARISON");
        printEvaluation(service.evaluate(comparison));

        System.out.println("\nRELATIONSHIP");
        printEvaluation(service.evaluate(relationship));

        System.out.println("\nMATRIX");
        printEvaluation(service.evaluate(matrix));

        System.out.println("\nINVALID REQUEST");
        VisualizationRequest invalid =
            new VisualizationRequest(
                AnalyticalIntent.COMPOSITION,
                List.of("Product", "Support", "Operations"),
                List.of(80.0, -10.0, 30.0),
                List.of(),
                List.of(),
                List.of(),
                false
            );

        printEvaluation(service.evaluate(invalid));
    }
}
