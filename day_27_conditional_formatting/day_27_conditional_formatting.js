/*
 * Conditional Formatting: Identifying Trends, Anomalies, and Exceptions
 *
 * This standalone JavaScript file demonstrates spreadsheet-style
 * conditional-formatting concepts using ordinary JavaScript.
 *
 * The examples cover:
 *   - threshold rules
 *   - range rules
 *   - missing-value detection
 *   - duplicate detection
 *   - rule precedence
 *   - data bars
 *   - color scales
 *   - moving averages
 *   - trend detection
 *   - z-score anomaly detection
 *   - IQR outlier detection
 *   - business exceptions
 *   - validation
 *   - performance considerations
 *   - browser-ready HTML generation
 *
 * It can run in Node.js and the generated HTML can be opened in a browser.
 */

"use strict";

// ============================================================================
// 1. DATA
// ============================================================================

const salesData = [
    { month: "Jan", sales: 82000, target: 80000, growth: 0.04, returns: 1200 },
    { month: "Feb", sales: 84500, target: 81000, growth: 0.03, returns: 1300 },
    { month: "Mar", sales: 87000, target: 83000, growth: 0.03, returns: 1400 },
    { month: "Apr", sales: 61000, target: 84000, growth: -0.30, returns: 3100 },
    { month: "May", sales: 89000, target: 85000, growth: 0.46, returns: 1500 },
    { month: "Jun", sales: 91000, target: 87000, growth: 0.02, returns: 1600 },
    { month: "Jul", sales: 91000, target: 88000, growth: 0.00, returns: 1700 },
    { month: "Aug", sales: null, target: 90000, growth: null, returns: 1800 },
    { month: "Sep", sales: 93000, target: 92000, growth: 0.02, returns: 1900 },
    { month: "Oct", sales: 210000, target: 94000, growth: 1.26, returns: 2200 },
    { month: "Nov", sales: 95000, target: 96000, growth: -0.55, returns: 7000 },
    { month: "Dec", sales: 99000, target: 98000, growth: 0.04, returns: 2000 }
];


// ============================================================================
// 2. VALIDATION
// ============================================================================

function isFiniteNumber(value) {
    return typeof value === "number" && Number.isFinite(value);
}

function validateRow(row) {
    if (!row || typeof row !== "object") {
        return false;
    }

    if (typeof row.month !== "string") {
        return false;
    }

    if (!isFiniteNumber(row.target) || !isFiniteNumber(row.returns)) {
        return false;
    }

    if (row.sales !== null && !isFiniteNumber(row.sales)) {
        return false;
    }

    if (row.growth !== null && !isFiniteNumber(row.growth)) {
        return false;
    }

    return true;
}

function validateDataset(rows) {
    return Array.isArray(rows) && rows.every(validateRow);
}


// ============================================================================
// 3. BASIC CONDITIONAL RULES
// ============================================================================

function greaterThan(threshold) {
    return value => isFiniteNumber(value) && value > threshold;
}

function lessThan(threshold) {
    return value => isFiniteNumber(value) && value < threshold;
}

function between(low, high) {
    return value =>
        isFiniteNumber(value) &&
        value >= low &&
        value <= high;
}

function isBlank(value) {
    return value === null || value === undefined || value === "";
}


// ============================================================================
// 4. DUPLICATE DETECTION
// ============================================================================

function duplicateValues(values) {
    const counts = new Map();

    for (const value of values) {
        if (!isFiniteNumber(value)) {
            continue;
        }

        counts.set(value, (counts.get(value) || 0) + 1);
    }

    return new Set(
        [...counts.entries()]
            .filter(([, count]) => count > 1)
            .map(([value]) => value)
    );
}


// ============================================================================
// 5. STATISTICAL FUNCTIONS
// ============================================================================

function average(values) {
    if (values.length === 0) {
        return null;
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function populationStandardDeviation(values) {
    if (values.length === 0) {
        return null;
    }

    const meanValue = average(values);

    const variance =
        values.reduce(
            (sum, value) => sum + Math.pow(value - meanValue, 2),
            0
        ) / values.length;

    return Math.sqrt(variance);
}

function zScore(value, values) {
    if (!isFiniteNumber(value) || values.length === 0) {
        return null;
    }

    const meanValue = average(values);
    const deviation = populationStandardDeviation(values);

    if (deviation === 0) {
        return null;
    }

    return (value - meanValue) / deviation;
}


// ============================================================================
// 6. QUARTILES AND IQR
// ============================================================================

function percentile(values, fraction) {
    if (values.length === 0) {
        return null;
    }

    if (fraction < 0 || fraction > 1) {
        throw new RangeError("Percentile fraction must be between 0 and 1.");
    }

    const sorted = [...values].sort((a, b) => a - b);

    const position = (sorted.length - 1) * fraction;
    const lowerIndex = Math.floor(position);
    const upperIndex = Math.ceil(position);

    if (lowerIndex === upperIndex) {
        return sorted[lowerIndex];
    }

    const weight = position - lowerIndex;

    return (
        sorted[lowerIndex] +
        (sorted[upperIndex] - sorted[lowerIndex]) * weight
    );
}

function iqrBounds(values) {
    if (values.length < 4) {
        return null;
    }

    const q1 = percentile(values, 0.25);
    const q3 = percentile(values, 0.75);
    const iqr = q3 - q1;

    return {
        lower: q1 - 1.5 * iqr,
        upper: q3 + 1.5 * iqr
    };
}


// ============================================================================
// 7. MOVING AVERAGE
// ============================================================================

function movingAverage(values, windowSize) {
    if (!Number.isInteger(windowSize) || windowSize <= 0) {
        throw new RangeError("windowSize must be a positive integer.");
    }

    const result = [];

    for (let index = 0; index < values.length; index++) {
        const start = Math.max(0, index - windowSize + 1);

        const window = values
            .slice(start, index + 1)
            .filter(isFiniteNumber);

        if (window.length < windowSize) {
            result.push(null);
        } else {
            result.push(average(window));
        }
    }

    return result;
}


// ============================================================================
// 8. LINEAR TREND
// ============================================================================

function linearSlope(values) {
    const points = values
        .map((value, index) => ({ x: index, y: value }))
        .filter(point => isFiniteNumber(point.y));

    if (points.length < 2) {
        return null;
    }

    const xMean = average(points.map(point => point.x));
    const yMean = average(points.map(point => point.y));

    let numerator = 0;
    let denominator = 0;

    for (const point of points) {
        numerator += (point.x - xMean) * (point.y - yMean);
        denominator += Math.pow(point.x - xMean, 2);
    }

    if (denominator === 0) {
        return null;
    }

    return numerator / denominator;
}

function classifyTrend(values) {
    const validValues = values.filter(isFiniteNumber);
    const slope = linearSlope(values);

    if (slope === null || validValues.length === 0) {
        return "insufficient-data";
    }

    const meanValue = average(validValues);

    if (meanValue === 0) {
        return Math.abs(slope) < Number.EPSILON
            ? "flat"
            : slope > 0
                ? "up"
                : "down";
    }

    const relativeSlope = slope / Math.abs(meanValue);

    if (relativeSlope > 0.01) {
        return "up";
    }

    if (relativeSlope < -0.01) {
        return "down";
    }

    return "flat";
}


// ============================================================================
// 9. COLOR SCALE
// ============================================================================

function interpolateChannel(start, end, ratio) {
    const clamped = Math.max(0, Math.min(1, ratio));
    return Math.round(start + (end - start) * clamped);
}

function rgbToHex(red, green, blue) {
    const channel = value =>
        Math.max(0, Math.min(255, Math.round(value)))
            .toString(16)
            .padStart(2, "0");

    return `#${channel(red)}${channel(green)}${channel(blue)}`;
}

function colorScale(value, minimum, maximum) {
    if (maximum === minimum) {
        return "#D9EAD3";
    }

    const ratio = (value - minimum) / (maximum - minimum);

    // Low values are pale red; high values are pale green.
    const red = interpolateChannel(255, 190, ratio);
    const green = interpolateChannel(220, 255, ratio);
    const blue = interpolateChannel(220, 200, ratio);

    return rgbToHex(red, green, blue);
}


// ============================================================================
// 10. DATA BAR
// ============================================================================

function dataBarPercentage(value, minimum, maximum) {
    if (maximum === minimum) {
        return 100;
    }

    const ratio = (value - minimum) / (maximum - minimum);

    return Math.max(0, Math.min(100, ratio * 100));
}


// ============================================================================
// 11. BUSINESS EXCEPTIONS
// ============================================================================

function targetException(row) {
    if (row.sales === null) {
        return "Missing sales value";
    }

    if (!isFiniteNumber(row.sales) || !isFiniteNumber(row.target)) {
        return "Invalid numeric data";
    }

    if (row.target === 0) {
        return "Target is zero";
    }

    const ratio = row.sales / row.target;

    if (ratio < 0.80) {
        return "Severely below target";
    }

    if (ratio < 1.00) {
        return "Below target";
    }

    if (ratio > 1.50) {
        return "Unusually high sales";
    }

    return null;
}

function returnException(row) {
    if (
        !isFiniteNumber(row.sales) ||
        !isFiniteNumber(row.returns) ||
        row.sales === 0
    ) {
        return null;
    }

    const returnRate = row.returns / row.sales;

    if (returnRate >= 0.05) {
        return `High return rate: ${(returnRate * 100).toFixed(1)}%`;
    }

    return null;
}


// ============================================================================
// 12. RULE OBJECTS
// ============================================================================

const styles = {
    critical: {
        background: "#8B0000",
        foreground: "#FFFFFF",
        marker: "CRITICAL"
    },

    warning: {
        background: "#FFD966",
        foreground: "#000000",
        marker: "WARNING"
    },

    information: {
        background: "#D9EAF7",
        foreground: "#000000",
        marker: "INFO"
    },

    good: {
        background: "#D9EAD3",
        foreground: "#000000",
        marker: "GOOD"
    },

    normal: {
        background: "#FFFFFF",
        foreground: "#000000",
        marker: "NORMAL"
    }
};

function createRule(name, condition, style, priority, stopIfTrue = false) {
    return {
        name,
        condition,
        style,
        priority,
        stopIfTrue
    };
}


// ============================================================================
// 13. RULE ENGINE
// ============================================================================

function applyRules(values, rules) {
    const orderedRules = [...rules].sort(
        (first, second) => first.priority - second.priority
    );

    return values.map(value => {
        const result = {
            value,
            style: styles.normal,
            reasons: []
        };

        for (const rule of orderedRules) {
            let matched = false;

            try {
                matched = rule.condition(value, values);
            } catch {
                matched = false;
            }

            if (!matched) {
                continue;
            }

            result.reasons.push(rule.name);

            if (result.style === styles.normal) {
                result.style = rule.style;
            }

            if (rule.stopIfTrue) {
                break;
            }
        }

        return result;
    });
}


// ============================================================================
// 14. SALES ANALYSIS
// ============================================================================

function analyzeSales(rows) {
    const salesValues = rows
        .map(row => row.sales)
        .filter(isFiniteNumber);

    const duplicateSet = duplicateValues(salesValues);
    const bounds = iqrBounds(salesValues);

    const minimum = Math.min(...salesValues);
    const maximum = Math.max(...salesValues);

    return rows.map(row => {
        const value = row.sales;

        let z = null;
        let iqrOutlier = false;
        let duplicate = false;
        let percentileClass = "missing";

        if (isFiniteNumber(value)) {
            z = zScore(value, salesValues);
            duplicate = duplicateSet.has(value);

            if (bounds !== null) {
                iqrOutlier =
                    value < bounds.lower ||
                    value > bounds.upper;
            }

            const low = percentile(salesValues, 0.10);
            const high = percentile(salesValues, 0.90);

            if (value < low) {
                percentileClass = "low";
            } else if (value > high) {
                percentileClass = "high";
            } else {
                percentileClass = "normal";
            }
        }

        return {
            ...row,
            zScore: z,
            iqrOutlier,
            duplicate,
            percentileClass,
            targetException: targetException(row),
            returnException: returnException(row),
            color: isFiniteNumber(value)
                ? colorScale(value, minimum, maximum)
                : styles.critical.background,
            dataBarPercentage: isFiniteNumber(value)
                ? dataBarPercentage(value, minimum, maximum)
                : 0
        };
    });
}


// ============================================================================
// 15. HTML REPORT
// ============================================================================

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatNumber(value) {
    if (value === null || value === undefined) {
        return "MISSING";
    }

    return new Intl.NumberFormat("en-US").format(value);
}

function formatPercentage(value) {
    if (value === null || value === undefined) {
        return "MISSING";
    }

    return `${(value * 100).toFixed(1)}%`;
}

function generateHtml(rows) {
    const analyzed = analyzeSales(rows);

    const tableRows = analyzed.map(row => {
        const salesStyle = row.sales === null
            ? `background:${styles.critical.background};color:white;font-weight:bold`
            : `background:${row.color}`;

        const bar =
            row.sales === null
                ? "MISSING"
                : `
                    <div style="
                        width:180px;
                        height:14px;
                        background:#333;
                        border-radius:4px;
                        overflow:hidden;
                    ">
                        <div style="
                            width:${row.dataBarPercentage.toFixed(1)}%;
                            height:100%;
                            background:#4caf50;
                        "></div>
                    </div>
                `;

        const flags = [
            row.targetException,
            row.returnException,
            row.iqrOutlier ? "IQR outlier" : null,
            row.duplicate ? "Duplicate sales value" : null
        ].filter(Boolean);

        return `
            <tr>
                <td>${escapeHtml(row.month)}</td>
                <td style="${salesStyle}">
                    ${escapeHtml(formatNumber(row.sales))}
                </td>
                <td>${escapeHtml(formatNumber(row.target))}</td>
                <td>${escapeHtml(formatPercentage(row.growth))}</td>
                <td>${escapeHtml(formatNumber(row.returns))}</td>
                <td>${escapeHtml(flags.join(" | ") || "None")}</td>
                <td>${bar}</td>
            </tr>
        `;
    }).join("");

    return `
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Conditional Formatting Analysis</title>
<style>
body {
    margin: 0;
    padding: 30px;
    background: #111;
    color: #eee;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 1200px;
    margin: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    background: #1c1c1c;
}

th, td {
    border: 1px solid #444;
    padding: 10px;
}

th {
    background: #292929;
}

td {
    text-align: right;
}

td:first-child,
th:first-child,
td:nth-child(6),
th:nth-child(6) {
    text-align: left;
}

.badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    background: #333;
}
</style>
</head>
<body>
<div class="container">
<h1>Conditional Formatting Analysis</h1>
<p>
The table combines threshold rules, anomaly detection,
exception detection, color scales, and data bars.
</p>
<table>
<thead>
<tr>
<th>Month</th>
<th>Sales</th>
<th>Target</th>
<th>Growth</th>
<th>Returns</th>
<th>Exceptions</th>
<th>Magnitude</th>
</tr>
</thead>
<tbody>
${tableRows}
</tbody>
</table>
</div>
</body>
</html>
`;
}


// ============================================================================
// 16. CONSOLE REPORT
// ============================================================================

function printReport(rows) {
    const analyzed = analyzeSales(rows);

    console.log("\nCONDITIONAL FORMATTING REPORT");
    console.log("=".repeat(100));

    console.log(
        "Month | Sales      | Target     | Growth | Z-Score | " +
        "IQR | Duplicate | Exceptions"
    );

    console.log("-".repeat(100));

    for (const row of analyzed) {
        const z =
            row.zScore === null
                ? "N/A"
                : row.zScore.toFixed(2);

        const exceptions = [
            row.targetException,
            row.returnException,
            row.iqrOutlier ? "IQR outlier" : null,
            row.duplicate ? "Duplicate" : null
        ].filter(Boolean);

        console.log(
            `${row.month.padStart(5)} | ` +
            `${formatNumber(row.sales).padStart(10)} | ` +
            `${formatNumber(row.target).padStart(10)} | ` +
            `${formatPercentage(row.growth).padStart(6)} | ` +
            `${z.padStart(7)} | ` +
            `${String(row.iqrOutlier).padStart(3)} | ` +
            `${String(row.duplicate).padStart(9)} | ` +
            `${exceptions.join(", ") || "None"}`
        );
    }
}


// ============================================================================
// 17. RULE PRECEDENCE DEMONSTRATION
// ============================================================================

function demonstrateRulePrecedence() {
    const values = [null, 50000, 150000];

    const rules = [
        createRule(
            "Missing",
            value => isBlank(value),
            styles.critical,
            1,
            true
        ),

        createRule(
            "Low",
            lessThan(70000),
            styles.warning,
            2
        ),

        createRule(
            "High",
            greaterThan(100000),
            styles.information,
            3
        )
    ];

    const results = applyRules(values, rules);

    console.log("\nRULE PRECEDENCE");
    console.log("=".repeat(60));

    for (const result of results) {
        console.log(
            `value=${result.value} | ` +
            `style=${result.style.marker} | ` +
            `rules=${result.reasons.join(", ")}`
        );
    }
}


// ============================================================================
// 18. ASYNCHRONOUS DEMONSTRATION
// ============================================================================

function delay(milliseconds) {
    return new Promise(resolve => {
        setTimeout(resolve, milliseconds);
    });
}

async function runAsynchronousAnalysis(rows) {
    /*
     * Conditional formatting in web applications often occurs after
     * asynchronous data retrieval. This function models that architecture.
     *
     * It does not make a network request, so the example remains
     * completely self-contained.
     */
    await delay(10);

    return analyzeSales(rows);
}


// ============================================================================
// 19. PERFORMANCE DEMONSTRATION
// ============================================================================

function benchmark(rows, iterations = 1000) {
    if (!Number.isInteger(iterations) || iterations <= 0) {
        throw new RangeError("iterations must be a positive integer.");
    }

    const start = performance.now();

    for (let index = 0; index < iterations; index++) {
        analyzeSales(rows);
    }

    const elapsed = performance.now() - start;

    return {
        iterations,
        elapsedMilliseconds: elapsed,
        averageMilliseconds: elapsed / iterations
    };
}


// ============================================================================
// 20. TESTS
// ============================================================================

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

function runTests() {
    assert(
        isFiniteNumber(42),
        "42 should be recognized as a finite number"
    );

    assert(
        !isFiniteNumber(Infinity),
        "Infinity should not be recognized as a finite number"
    );

    assert(
        isBlank(null),
        "null should be considered blank"
    );

    assert(
        movingAverage([10, 20, 30], 2)[1] === 15,
        "two-period moving average should equal 15"
    );

    assert(
        zScore(10, [10, 10, 10]) === null,
        "constant population has no usable z-score"
    );

    assert(
        targetException({
            sales: 50000,
            target: 100000
        }) === "Severely below target",
        "target exception should identify severe underperformance"
    );

    assert(
        validateDataset(salesData),
        "provided dataset should pass validation"
    );

    console.log("\nAll JavaScript tests passed.");
}


// ============================================================================
// 21. MAIN EXECUTION
// ============================================================================

async function main() {
    if (!validateDataset(salesData)) {
        throw new Error("Dataset validation failed.");
    }

    printReport(salesData);

    console.log("\nTREND ANALYSIS");
    console.log("=".repeat(60));

    const sales = salesData.map(row => row.sales);

    console.log(
        "3-period moving average:",
        movingAverage(sales, 3)
    );

    console.log(
        "Overall trend:",
        classifyTrend(sales)
    );

    console.log(
        "Regression slope:",
        linearSlope(sales)
    );

    demonstrateRulePrecedence();

    const analyzed = await runAsynchronousAnalysis(salesData);

    console.log(
        "\nAsynchronous analysis completed for",
        analyzed.length,
        "records."
    );

    const html = generateHtml(salesData);

    /*
     * In Node.js the HTML is printed rather than written to disk so that
     * the example remains dependency-free. In a browser application,
     * document.body.innerHTML or a DOM container could receive this HTML.
     */
    console.log("\nGenerated HTML length:", html.length, "characters.");

    console.log("\nPERFORMANCE SAMPLE");
    console.log("=".repeat(60));
    console.log(benchmark(salesData, 500));

    runTests();
}

main().catch(error => {
    console.error("Execution error:", error.message);
    process.exitCode = 1;
});
