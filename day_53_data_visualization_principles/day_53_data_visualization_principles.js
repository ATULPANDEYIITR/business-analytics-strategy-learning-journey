"use strict";

/*
 * Data Visualization Principles
 *
 * This Node.js program evaluates analytical intent and data structure rather
 * than blindly assigning a chart type. The event-driven layer emits an
 * audit trail whenever a recommendation is produced.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

class VisualizationError extends Error {}

class VisualizationEngine extends EventEmitter {
    constructor() {
        super();
        this.rules = new Map([
            ["comparison", this.#comparison.bind(this)],
            ["ranking", this.#comparison.bind(this)],
            ["relationship", this.#relationship.bind(this)],
            ["distribution", this.#distribution.bind(this)],
            ["composition", this.#composition.bind(this)],
            ["trend", this.#trend.bind(this)],
            ["matrix", this.#matrix.bind(this)],
        ]);
    }

    recommend(request) {
        this.#validateRequest(request);

        const purpose = String(request.purpose).toLowerCase().trim();
        const rule = this.rules.get(purpose);

        if (!rule) {
            throw new VisualizationError(
                `Unsupported analytical purpose: ${purpose}`
            );
        }

        const recommendations = rule(request)
            .sort((a, b) => b.score - a.score);

        if (recommendations.length === 0) {
            throw new VisualizationError(
                "The supplied data does not support a reliable chart recommendation."
            );
        }

        const result = {
            purpose,
            generatedAt: new Date().toISOString(),
            recommendations,
        };

        this.emit("recommendation", result);
        return result;
    }

    #validateRequest(request) {
        if (!request || typeof request !== "object") {
            throw new VisualizationError("A request object is required.");
        }

        if (!request.purpose) {
            throw new VisualizationError("Analytical purpose is required.");
        }

        for (const key of ["values", "x", "y"]) {
            if (request[key] !== undefined) {
                validateNumbers(request[key], key);
            }
        }

        if (request.categories !== undefined) {
            if (!Array.isArray(request.categories) ||
                request.categories.length === 0) {
                throw new VisualizationError(
                    "categories must be a non-empty array."
                );
            }
        }

        if (request.values !== undefined &&
            request.categories !== undefined &&
            request.values.length !== request.categories.length) {
            throw new VisualizationError(
                "categories and values must have equal lengths."
            );
        }

        if (request.x !== undefined &&
            request.y !== undefined &&
            request.x.length !== request.y.length) {
            throw new VisualizationError("x and y must have equal lengths.");
        }
    }

    #comparison({ categories, values }) {
        if (!categories || !values) {
            throw new VisualizationError(
                "Comparison requires categories and values."
            );
        }

        const uniqueCount = new Set(categories.map(String)).size;

        return [
            {
                chart: "horizontal bar chart",
                score: uniqueCount > 20 ? 0.80 : 0.96,
                purpose: "compare categories",
                reason:
                    "A common quantitative axis supports direct comparison of category lengths.",
                warnings: uniqueCount > 20
                    ? ["Many categories require filtering or aggregation."]
                    : ["Sort categories when ranking is the analytical goal."],
            },
            {
                chart: "dot plot",
                score: 0.91,
                purpose: "compare precise values",
                reason:
                    "Position on a shared scale allows compact and accurate comparison.",
                warnings: [
                    "Direct labels may be useful when the category count is small.",
                ],
            },
        ];
    }

    #relationship({ x, y }) {
        const correlation = correlationCoefficient(x, y);

        return [
            {
                chart: "scatter plot",
                score: 0.98,
                purpose: "show a relationship",
                reason:
                    `Each observation is preserved; Pearson correlation is ${correlation.toFixed(3)}.`,
                warnings: [
                    "Correlation does not establish causation.",
                    "Dense datasets may require transparency or aggregation.",
                ],
            },
        ];
    }

    #distribution({ values }) {
        if (!values) {
            throw new VisualizationError(
                "Distribution analysis requires numeric values."
            );
        }

        return [
            {
                chart: "histogram",
                score: 0.97,
                purpose: "show distribution",
                reason:
                    "Bins reveal concentration, skewness, spread, and possible outliers.",
                warnings: [
                    "The bin width can materially change the visible pattern.",
                ],
            },
            {
                chart: "box plot",
                score: 0.93,
                purpose: "compare distribution summaries",
                reason:
                    "Quartiles and extreme observations remain visible with compact encoding.",
                warnings: [
                    "A box plot hides some multimodal distribution shape.",
                ],
            },
        ];
    }

    #composition({ categories, values }) {
        if (!categories || !values) {
            throw new VisualizationError(
                "Composition analysis requires categories and values."
            );
        }

        const total = values.reduce((sum, value) => sum + value, 0);
        const invalid = total <= 0 || values.some(value => value < 0);

        return [
            {
                chart: "100% stacked bar chart",
                score: invalid ? 0.20 : 0.95,
                purpose: "show composition",
                reason:
                    "A shared baseline makes component proportions easier to compare.",
                warnings: invalid
                    ? ["Composition values must be non-negative and have a positive total."]
                    : ["Limit the number of components for readable labels."],
            },
            {
                chart: "pie chart",
                score: !invalid && categories.length <= 5 ? 0.60 : 0.25,
                purpose: "show simple composition",
                reason:
                    "Angular and area differences communicate broad part-to-whole structure.",
                warnings: [
                    "Avoid many slices.",
                    "Use bars when precise comparison is important.",
                ],
            },
        ];
    }

    #trend({ values }) {
        if (!values) {
            throw new VisualizationError(
                "Trend analysis requires ordered values."
            );
        }

        return [
            {
                chart: "line chart",
                score: 0.98,
                purpose: "show temporal change",
                reason:
                    "Connected observations make direction and turning points visible.",
                warnings: [
                    "Only connect observations when their ordering is meaningful.",
                ],
            },
        ];
    }

    #matrix({ matrix }) {
        if (!Array.isArray(matrix) || matrix.length === 0) {
            throw new VisualizationError("matrix must be a non-empty array.");
        }

        const width = matrix[0].length;
        if (width === 0 || matrix.some(row => !Array.isArray(row) ||
            row.length !== width)) {
            throw new VisualizationError(
                "matrix must contain equally sized numeric rows."
            );
        }

        matrix.forEach(row => validateNumbers(row, "matrix row"));

        return [
            {
                chart: "heatmap",
                score: 0.97,
                purpose: "show two-dimensional patterns",
                reason:
                    "Color intensity provides a compact representation of a rectangular value matrix.",
                warnings: [
                    "Use a perceptually ordered scale.",
                    "Annotate cells when exact values are important.",
                ],
            },
        ];
    }
}

function validateNumbers(values, name) {
    if (!Array.isArray(values) || values.length === 0) {
        throw new VisualizationError(`${name} must be a non-empty array.`);
    }

    for (const value of values) {
        if (
            typeof value !== "number" ||
            !Number.isFinite(value)
        ) {
            throw new VisualizationError(
                `${name} contains an invalid numeric value.`
            );
        }
    }
}

function correlationCoefficient(x, y) {
    validateNumbers(x, "x");
    validateNumbers(y, "y");

    if (x.length !== y.length) {
        throw new VisualizationError("x and y must have equal lengths.");
    }

    const meanX = x.reduce((a, b) => a + b, 0) / x.length;
    const meanY = y.reduce((a, b) => a + b, 0) / y.length;

    let numerator = 0;
    let denominatorX = 0;
    let denominatorY = 0;

    for (let i = 0; i < x.length; i++) {
        const dx = x[i] - meanX;
        const dy = y[i] - meanY;
        numerator += dx * dy;
        denominatorX += dx * dx;
        denominatorY += dy * dy;
    }

    const denominator = Math.sqrt(denominatorX * denominatorY);
    return denominator === 0 ? 0 : numerator / denominator;
}

function renderTextTable(result) {
    const lines = [
        `Analytical purpose: ${result.purpose}`,
        `Generated: ${result.generatedAt}`,
        "",
        "Chart recommendations:",
    ];

    for (const item of result.recommendations) {
        lines.push(
            `${item.chart.padEnd(25)} score=${item.score.toFixed(2)}`,
            `  Purpose: ${item.purpose}`,
            `  Reason: ${item.reason}`,
            `  Warnings: ${item.warnings.join(" ")}`,
            ""
        );
    }

    return lines.join("\n");
}

async function saveAudit(result, filePath) {
    /*
     * JSON serialization keeps the audit data portable. The program writes
     * only its own generated structure and never evaluates imported content.
     */
    await fs.writeFile(
        filePath,
        JSON.stringify(result, null, 2),
        { encoding: "utf8", flag: "wx" }
    );
}

async function main() {
    const engine = new VisualizationEngine();

    engine.on("recommendation", result => {
        console.log(renderTextTable(result));
    });

    engine.on("error", error => {
        console.error(`Visualization engine error: ${error.message}`);
    });

    const demand = {
        purpose: "ranking",
        categories: ["Cloud", "Security", "Data", "Networking", "Applications"],
        values: [1840, 1320, 1610, 940, 2110],
    };

    const relationship = {
        purpose: "relationship",
        x: [12, 18, 21, 27, 30, 35, 41, 48],
        y: [17, 15, 14, 12, 11, 9, 8, 6],
    };

    const matrix = {
        purpose: "matrix",
        matrix: [
            [92, 84, 76],
            [71, 88, 94],
            [63, 79, 91],
            [55, 68, 83],
        ],
    };

    try {
        const rankingResult = engine.recommend(demand);
        engine.recommend(relationship);
        engine.recommend(matrix);

        /*
         * The filename is intentionally not overwritten. This prevents a
         * visualization audit from silently replacing an existing artifact.
         *
         * Uncomment only when a new destination is intended:
         * await saveAudit(rankingResult, "./visualization-audit.json");
         */
        void rankingResult;
    } catch (error) {
        engine.emit("error", error);
        process.exitCode = 1;
    }

    try {
        engine.recommend({
            purpose: "composition",
            categories: ["Product", "Support", "Operations", "Other"],
            values: [52, 21, 17, 10],
        });
    } catch (error) {
        engine.emit("error", error);
        process.exitCode = 1;
    }
}

main().catch(error => {
    console.error(`Fatal error: ${error.message}`);
    process.exitCode = 1;
});
