"use strict";

/*
 * Exploratory Data Analysis
 * Event-driven dataset inspection using Node.js standard libraries.
 *
 * Features:
 * - CSV parsing with quoted-field handling
 * - Asynchronous dataset loading
 * - Schema validation and type classification
 * - Distribution profiling
 * - Missingness and duplicate detection
 * - Quantile and outlier analysis
 * - Pearson correlation
 * - Grouped aggregation
 * - Data-quality rules
 * - JSON report generation
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");

class EDAError extends Error {
    constructor(message) {
        super(message);
        this.name = "EDAError";
    }
}

class ValidationError extends EDAError {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class CsvParser {
    static parseLine(line) {
        const fields = [];
        let field = "";
        let quoted = false;

        for (let i = 0; i < line.length; i++) {
            const char = line[i];

            if (char === '"') {
                if (quoted && line[i + 1] === '"') {
                    field += '"';
                    i++;
                } else {
                    quoted = !quoted;
                }
            } else if (char === "," && !quoted) {
                fields.push(field);
                field = "";
            } else {
                field += char;
            }
        }

        if (quoted) {
            throw new ValidationError(
                "CSV contains an unterminated quoted field."
            );
        }

        fields.push(field);
        return fields;
    }

    static parse(content) {
        // Split CSV records while preserving newlines inside quoted fields.
        const records = [];
        let record = "";
        let quoted = false;

        for (let i = 0; i < content.length; i++) {
            const char = content[i];

            if (char === '"') {
                if (quoted && content[i + 1] === '"') {
                    record += '""';
                    i++;
                    continue;
                }
                quoted = !quoted;
                record += char;
            } else if (char === "\n" && !quoted) {
                records.push(record.replace(/\r$/, ""));
                record = "";
            } else {
                record += char;
            }
        }

        if (quoted) {
            throw new ValidationError(
                "CSV contains an unterminated quoted field."
            );
        }

        if (record.length > 0) {
            records.push(record.replace(/\r$/, ""));
        }

        const nonEmpty = records.filter(r => r.trim().length > 0);

        if (nonEmpty.length < 2) {
            throw new ValidationError(
                "CSV requires a header and at least one data row."
            );
        }

        const headers = this.parseLine(nonEmpty[0])
            .map(h => h.trim().replace(/^\uFEFF/, ""));

        if (
            headers.some(h => !h) ||
            new Set(headers).size !== headers.length
        ) {
            throw new ValidationError(
                "Column names must be non-empty and unique."
            );
        }

        const rows = nonEmpty.slice(1).map((line, index) => {
            const values = this.parseLine(line);

            if (values.length !== headers.length) {
                throw new ValidationError(
                    `Invalid field count on data row ${index + 1}.`
                );
            }

            return Object.fromEntries(
                headers.map((header, i) => [
                    header,
                    values[i].trim()
                ])
            );
        });

        return { headers, rows };
    }
}

class Dataset {
    constructor(headers, rows) {
        if (!Array.isArray(headers) || headers.length === 0) {
            throw new ValidationError("Dataset requires columns.");
        }

        if (new Set(headers).size !== headers.length) {
            throw new ValidationError("Duplicate column names.");
        }

        if (!Array.isArray(rows)) {
            throw new ValidationError("Rows must be an array.");
        }

        for (const [index, row] of rows.entries()) {
            if (
                !row ||
                typeof row !== "object" ||
                headers.some(h => !Object.hasOwn(row, h)) ||
                Object.keys(row).length !== headers.length
            ) {
                throw new ValidationError(
                    `Invalid row structure at index ${index}.`
                );
            }
        }

        this.headers = [...headers];
        this.rows = rows.map(row => ({ ...row }));
    }

    static async fromCSV(filePath) {
        try {
            const content = await fs.readFile(filePath, "utf8");
            const parsed = CsvParser.parse(content);
            return new Dataset(parsed.headers, parsed.rows);
        } catch (error) {
            if (error instanceof EDAError) throw error;

            throw new EDAError(
                `Dataset loading failed: ${error.message}`
            );
        }
    }

    static sample() {
        const headers = [
            "employee_id",
            "department",
            "salary",
            "experience",
            "rating"
        ];

        const rows = [
            ["E001", "Engineering", "85000", "5", "4.5"],
            ["E002", "Analytics", "72000", "3", "4.2"],
            ["E003", "Engineering", "95000", "8", "4.8"],
            ["E004", "Operations", "61000", "2", "3.9"],
            ["E005", "Analytics", "78000", "4", "4.4"],
            ["E006", "Engineering", "110000", "12", "4.9"],
            ["E007", "Operations", "", "3", "3.7"],
            ["E008", "Analytics", "75000", "4", ""],
            ["E009", "Engineering", "85000", "5", "4.5"],
            ["E010", "Operations", "58000", "1", "3.5"],
            ["E010", "Operations", "58000", "1", "3.5"]
        ].map(values =>
            Object.fromEntries(
                headers.map((header, i) => [header, values[i]])
            )
        );

        return new Dataset(headers, rows);
    }
}

class Statistics {
    static mean(values) {
        if (!values.length) return null;
        return values.reduce((sum, value) => sum + value, 0)
            / values.length;
    }

    static median(values) {
        if (!values.length) return null;

        const sorted = [...values].sort((a, b) => a - b);
        const middle = Math.floor(sorted.length / 2);

        return sorted.length % 2
            ? sorted[middle]
            : (sorted[middle - 1] + sorted[middle]) / 2;
    }

    static quantile(values, fraction) {
        if (!values.length || fraction < 0 || fraction > 1) {
            throw new ValidationError("Invalid quantile request.");
        }

        const sorted = [...values].sort((a, b) => a - b);
        const position = (sorted.length - 1) * fraction;
        const lower = Math.floor(position);
        const upper = Math.ceil(position);

        return sorted[lower] +
            (sorted[upper] - sorted[lower]) * (position - lower);
    }

    static variance(values) {
        if (values.length < 2) return 0;

        const average = this.mean(values);

        return values.reduce(
            (sum, value) => sum + (value - average) ** 2,
            0
        ) / (values.length - 1);
    }

    static correlation(first, second) {
        if (first.length !== second.length || first.length < 2) {
            return null;
        }

        const meanX = this.mean(first);
        const meanY = this.mean(second);

        let covariance = 0;
        let sumX = 0;
        let sumY = 0;

        for (let i = 0; i < first.length; i++) {
            const dx = first[i] - meanX;
            const dy = second[i] - meanY;

            covariance += dx * dy;
            sumX += dx * dx;
            sumY += dy * dy;
        }

        const denominator = Math.sqrt(sumX * sumY);

        return denominator === 0
            ? null
            : covariance / denominator;
    }
}

class EDAEngine extends EventEmitter {
    static MISSING = new Set([
        "",
        "na",
        "n/a",
        "null",
        "none",
        "nan",
        "missing"
    ]);

    constructor(dataset) {
        super();
        this.dataset = dataset;
        this.profiles = new Map();
    }

    isMissing(value) {
        return value === null ||
            value === undefined ||
            EDAEngine.MISSING.has(String(value).trim().toLowerCase());
    }

    toNumber(value) {
        if (this.isMissing(value)) return null;

        const number = Number(value);

        return Number.isFinite(number) ? number : null;
    }

    inferType(values) {
        const valid = values.filter(v => !this.isMissing(v));

        if (!valid.length) return "empty";

        if (valid.every(v => this.toNumber(v) !== null)) {
            return "numeric";
        }

        if (
            valid.every(v =>
                ["true", "false"].includes(String(v).toLowerCase())
            )
        ) {
            return "boolean";
        }

        if (
            valid.every(v =>
                /^\d{4}-\d{2}-\d{2}$/.test(String(v)) &&
                !Number.isNaN(Date.parse(v))
            )
        ) {
            return "date";
        }

        return "categorical";
    }

    profile(column) {
        const values = this.dataset.rows.map(row => row[column]);
        const valid = values.filter(v => !this.isMissing(v));
        const type = this.inferType(values);

        const profile = {
            column,
            type,
            total: values.length,
            missing: values.length - valid.length,
            unique: new Set(valid.map(String)).size,
            statistics: {},
            frequencies: {}
        };

        if (type === "numeric") {
            const numbers = valid.map(v => this.toNumber(v));

            const q1 = Statistics.quantile(numbers, 0.25);
            const median = Statistics.median(numbers);
            const q3 = Statistics.quantile(numbers, 0.75);
            const iqr = q3 - q1;

            const frequency = new Map();

            for (const number of numbers) {
                frequency.set(
                    number,
                    (frequency.get(number) || 0) + 1
                );
            }

            profile.statistics = {
                count: numbers.length,
                mean: Statistics.mean(numbers),
                median,
                minimum: Math.min(...numbers),
                maximum: Math.max(...numbers),
                variance: Statistics.variance(numbers),
                standardDeviation: Math.sqrt(
                    Statistics.variance(numbers)
                ),
                q1,
                q3,
                iqr,
                outliers: numbers.filter(
                    value =>
                        value < q1 - 1.5 * iqr ||
                        value > q3 + 1.5 * iqr
                ),
                frequencies: Object.fromEntries(frequency)
            };
        } else if (type === "categorical") {
            const frequency = new Map();

            for (const value of valid) {
                const key = String(value);
                frequency.set(key, (frequency.get(key) || 0) + 1);
            }

            profile.frequencies = Object.fromEntries(
                [...frequency.entries()]
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 10)
            );
        } else if (type === "date") {
            const dates = valid.map(v => String(v)).sort();

            profile.statistics = {
                earliest: dates[0],
                latest: dates[dates.length - 1]
            };
        }

        this.profiles.set(column, profile);
        return profile;
    }

    duplicates() {
        const seen = new Set();
        let count = 0;

        for (const row of this.dataset.rows) {
            // Stable field ordering avoids property-order differences.
            const key = JSON.stringify(
                this.dataset.headers.map(h => row[h])
            );

            if (seen.has(key)) count++;
            else seen.add(key);
        }

        return count;
    }

    correlations() {
        const numericColumns = [...this.profiles.entries()]
            .filter(([, profile]) => profile.type === "numeric")
            .map(([column]) => column);

        const result = {};

        for (let i = 0; i < numericColumns.length; i++) {
            for (
                let j = i + 1;
                j < numericColumns.length;
                j++
            ) {
                const first = numericColumns[i];
                const second = numericColumns[j];

                const pairs = this.dataset.rows
                    .map(row => [
                        this.toNumber(row[first]),
                        this.toNumber(row[second])
                    ])
                    .filter(pair =>
                        pair[0] !== null && pair[1] !== null
                    );

                if (pairs.length < 2) continue;

                const correlation = Statistics.correlation(
                    pairs.map(p => p[0]),
                    pairs.map(p => p[1])
                );

                if (correlation !== null) {
                    result[`${first}__${second}`] = correlation;
                }
            }
        }

        return result;
    }

    groupBy(category, measure) {
        if (
            !this.dataset.headers.includes(category) ||
            !this.dataset.headers.includes(measure)
        ) {
            throw new ValidationError("Unknown grouping or measure column.");
        }

        const groups = new Map();

        for (const row of this.dataset.rows) {
            if (this.isMissing(row[category])) continue;

            const value = this.toNumber(row[measure]);
            if (value === null) continue;

            const key = String(row[category]);

            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push(value);
        }

        return Object.fromEntries(
            [...groups.entries()]
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([key, values]) => [
                    key,
                    {
                        count: values.length,
                        mean: Statistics.mean(values),
                        median: Statistics.median(values),
                        minimum: Math.min(...values),
                        maximum: Math.max(...values)
                    }
                ])
        );
    }

    analyze() {
        this.emit("analysisStarted", {
            rows: this.dataset.rows.length,
            columns: this.dataset.headers.length
        });

        const profiles = this.dataset.headers.map(column =>
            this.profile(column)
        );

        const qualityIssues = [];

        if (this.duplicates() > 0) {
            qualityIssues.push(
                `${this.duplicates()} duplicate rows detected.`
            );
        }

        for (const profile of profiles) {
            if (profile.missing > 0) {
                qualityIssues.push(
                    `${profile.column}: ${profile.missing} missing values.`
                );
            }

            if (profile.unique <= 1 && profile.total > 0) {
                qualityIssues.push(
                    `${profile.column}: constant or single-valued column.`
                );
            }
        }

        const report = {
            generatedAt: new Date().toISOString(),
            dataset: {
                rows: this.dataset.rows.length,
                columns: this.dataset.headers.length,
                duplicateRows: this.duplicates()
            },
            profiles,
            correlations: this.correlations(),
            qualityIssues
        };

        this.emit("analysisCompleted", report);
        return report;
    }

    async saveReport(report, destination) {
        const absolutePath = path.resolve(destination);
        const directory = path.dirname(absolutePath);

        await fs.mkdir(directory, { recursive: true });

        const temporaryPath = `${absolutePath}.tmp`;

        try {
            await fs.writeFile(
                temporaryPath,
                JSON.stringify(report, null, 2),
                { encoding: "utf8", flag: "w" }
            );

            await fs.rename(temporaryPath, absolutePath);
        } catch (error) {
            await fs.rm(temporaryPath, { force: true }).catch(() => {});
            throw new EDAError(
                `Report writing failed: ${error.message}`
            );
        }
    }
}

function runTests() {
    const values = [1, 2, 3, 4, 5];

    if (Statistics.median(values) !== 3) {
        throw new Error("Median test failed.");
    }

    if (Statistics.quantile(values, 0.25) !== 2) {
        throw new Error("Quantile test failed.");
    }

    if (
        Math.abs(
            Statistics.correlation([1, 2, 3], [2, 4, 6]) - 1
        ) > 1e-10
    ) {
        throw new Error("Correlation test failed.");
    }

    if (
        Statistics.correlation([1, 1, 1], [2, 3, 4]) !== null
    ) {
        throw new Error("Constant column test failed.");
    }

    console.log("All tests passed.");
}

async function main() {
    const args = process.argv.slice(2);

    if (args.includes("--test")) {
        runTests();
        return;
    }

    const inputIndex = args.indexOf("--input");
    const outputIndex = args.indexOf("--output");
    const groupIndex = args.indexOf("--group");
    const measureIndex = args.indexOf("--measure");

    const dataset = inputIndex >= 0
        ? await Dataset.fromCSV(args[inputIndex + 1])
        : Dataset.sample();

    const engine = new EDAEngine(dataset);

    engine.on("analysisStarted", metadata => {
        console.log(
            `Analyzing ${metadata.rows} rows and ${metadata.columns} columns...`
        );
    });

    engine.on("analysisCompleted", report => {
        console.log(
            `Analysis completed. ${report.qualityIssues.length} quality findings.`
        );
    });

    const report = engine.analyze();

    console.log("\nEXPLORATORY DATA ANALYSIS");
    console.log(JSON.stringify(report, null, 2));

    if (groupIndex >= 0) {
        const measure = measureIndex >= 0
            ? args[measureIndex + 1]
            : "salary";

        console.log("\nGROUPED ANALYSIS");

        console.log(
            JSON.stringify(
                engine.groupBy(args[groupIndex + 1], measure),
                null,
                2
            )
        );
    }

    const output = outputIndex >= 0
        ? args[outputIndex + 1]
        : "eda_report.json";

    await engine.saveReport(report, output);

    console.log(`Report saved to ${path.resolve(output)}`);
}

if (require.main === module) {
    main().catch(error => {
        console.error(`ERROR: ${error.message}`);
        process.exitCode = 1;
    });
}

module.exports = {
    Dataset,
    CsvParser,
    Statistics,
    EDAEngine,
    ValidationError
};
