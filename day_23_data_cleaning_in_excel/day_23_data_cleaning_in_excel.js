/*
 * Data Cleaning in Excel
 * ======================
 *
 * A self-contained JavaScript study file demonstrating spreadsheet-style
 * cleaning, standardization, validation, duplicate detection, profiling,
 * audit trails, quality scoring, and a realistic data-cleaning pipeline.
 *
 * The examples are intentionally implemented with standard JavaScript so that
 * the file can run in Node.js without external npm packages.
 *
 * The JavaScript perspective is useful for understanding:
 * - text and array processing
 * - functional transformations
 * - validation
 * - JSON-based datasets
 * - browser/application-side cleaning
 * - asynchronous processing patterns
 * - deterministic data pipelines
 */

"use strict";

// ============================================================================
// SECTION 1: RAW DATASET
// ============================================================================

const rawData = [
    {
        customerId: " C001 ",
        name: "  Rahul Sharma ",
        email: "RAHUL.SHARMA@EXAMPLE.COM ",
        phone: "98765 43210",
        city: " lucknow",
        state: "UP",
        amount: "₹ 12,500",
        orderDate: "15/09/2026",
        category: " electronics ",
        age: "29"
    },
    {
        customerId: "C002",
        name: "PRIYA SINGH",
        email: "priya.singh@example.com",
        phone: "+91-9876543211",
        city: "Lucknow ",
        state: "Uttar Pradesh",
        amount: "15000",
        orderDate: "2026-09-16",
        category: "Electronics",
        age: "31"
    },
    {
        customerId: "C003",
        name: " Amit Kumar ",
        email: " amit.kumar@example.com",
        phone: "98765-43212",
        city: "KANPUR",
        state: "UP",
        amount: "₹8,750.50",
        orderDate: "16-09-2026",
        category: "electronics",
        age: "twenty-eight"
    },
    {
        customerId: "C004",
        name: "Neha Verma",
        email: "neha.verma@example.com",
        phone: "9876543213",
        city: "Kanpur",
        state: "U.P.",
        amount: "10,000",
        orderDate: "17/09/2026",
        category: " Home Appliances ",
        age: "42"
    },
    {
        customerId: "C005",
        name: "Suresh Patel",
        email: "",
        phone: "9876543214",
        city: "Delhi",
        state: "Delhi",
        amount: "12500",
        orderDate: "",
        category: "home appliance",
        age: "37"
    },
    {
        customerId: "C005",
        name: " Suresh Patel ",
        email: "",
        phone: "9876543214",
        city: "Delhi ",
        state: "Delhi",
        amount: "12500",
        orderDate: "",
        category: "Home Appliances",
        age: "37"
    },
    {
        customerId: "C006",
        name: "Meera Joshi",
        email: "meera.joshi@example.com",
        phone: "09876543215",
        city: "Delhi",
        state: "DL",
        amount: "-500",
        orderDate: "31/09/2026",
        category: "Furniture",
        age: "150"
    },
    {
        customerId: "C007",
        name: "Arjun Mehta",
        email: "arjun.mehta@example",
        phone: "9876543216",
        city: "Lucknow",
        state: "Uttar Pradesh",
        amount: "1O,500",
        orderDate: "18/09/2026",
        category: "Furniture",
        age: "34"
    }
];


// ============================================================================
// SECTION 2: BASIC DISPLAY
// ============================================================================

function printTitle(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function printTable(rows) {
    if (rows.length === 0) {
        console.log("(empty dataset)");
        return;
    }

    console.table(rows);
}

printTitle("RAW DATASET");
printTable(rawData);


// ============================================================================
// SECTION 3: MISSING VALUE DETECTION
// ============================================================================

function isMissing(value) {
    return (
        value === null ||
        value === undefined ||
        (typeof value === "string" && value.trim() === "")
    );
}

function countMissing(rows, property) {
    return rows.filter(row => isMissing(row[property])).length;
}

printTitle("MISSING VALUE PROFILE");

for (const property of Object.keys(rawData[0])) {
    console.log(
        `${property}: ${countMissing(rawData, property)} missing`
    );
}


// ============================================================================
// SECTION 4: TEXT NORMALIZATION
// ============================================================================

function cleanWhitespace(value) {
    if (typeof value !== "string") {
        return value;
    }

    return value
        .replace(/\u00A0/g, " ")
        .replace(/[\u0000-\u001F\u007F]/g, "")
        .replace(/\s+/g, " ")
        .trim();
}

function titleCase(value) {
    if (isMissing(value)) {
        return null;
    }

    return cleanWhitespace(value)
        .toLowerCase()
        .replace(/\b\w/g, character => character.toUpperCase());
}

function normalizeEmail(value) {
    if (isMissing(value)) {
        return null;
    }

    return cleanWhitespace(value).toLowerCase();
}

function normalizeCity(value) {
    return titleCase(value);
}

function normalizeName(value) {
    return titleCase(value);
}


// ============================================================================
// SECTION 5: CONTROLLED VOCABULARIES
// ============================================================================

const categoryMap = new Map([
    ["electronics", "Electronics"],
    ["electronic", "Electronics"],
    ["home appliance", "Home Appliances"],
    ["home appliances", "Home Appliances"],
    ["furniture", "Furniture"]
]);

const stateMap = new Map([
    ["up", "Uttar Pradesh"],
    ["u.p.", "Uttar Pradesh"],
    ["uttar pradesh", "Uttar Pradesh"],
    ["dl", "Delhi"],
    ["delhi", "Delhi"]
]);

function normalizeCategory(value) {
    if (isMissing(value)) {
        return null;
    }

    const key = cleanWhitespace(value).toLowerCase();

    return categoryMap.get(key) ?? titleCase(key);
}

function normalizeState(value) {
    if (isMissing(value)) {
        return null;
    }

    const key = cleanWhitespace(value).toLowerCase();

    return stateMap.get(key) ?? titleCase(key);
}


// ============================================================================
// SECTION 6: PHONE NORMALIZATION
// ============================================================================

function normalizePhone(value) {
    if (isMissing(value)) {
        return null;
    }

    let digits = String(value).replace(/\D/g, "");

    if (digits.startsWith("91") && digits.length === 12) {
        digits = digits.slice(2);
    }

    if (digits.startsWith("0") && digits.length === 11) {
        digits = digits.slice(1);
    }

    return digits.length === 10 ? digits : null;
}


// ============================================================================
// SECTION 7: EMAIL VALIDATION
// ============================================================================

const emailPattern =
    /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$/;

function validateEmail(value) {
    if (isMissing(value)) {
        return false;
    }

    return emailPattern.test(String(value).trim());
}


// ============================================================================
// SECTION 8: CURRENCY PARSING
// ============================================================================

function parseCurrency(value) {
    if (isMissing(value)) {
        return null;
    }

    const text = String(value)
        .replace(/₹/g, "")
        .replace(/\$/g, "")
        .replace(/,/g, "")
        .replace(/\s/g, "");

    /*
     * JavaScript Number is convenient for demonstrations, but financial
     * applications should consider decimal arithmetic libraries or integer
     * minor units when exact monetary calculations are required.
     */
    if (!/^-?\d+(?:\.\d+)?$/.test(text)) {
        return null;
    }

    const number = Number(text);

    return Number.isFinite(number) ? number : null;
}


// ============================================================================
// SECTION 9: DATE PARSING
// ============================================================================

function parseDate(value) {
    if (isMissing(value)) {
        return null;
    }

    const text = cleanWhitespace(String(value));

    let day;
    let month;
    let year;

    let match = text.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);

    if (match) {
        day = Number(match[1]);
        month = Number(match[2]);
        year = Number(match[3]);
    } else {
        match = text.match(/^(\d{2})-(\d{2})-(\d{4})$/);

        if (match) {
            day = Number(match[1]);
            month = Number(match[2]);
            year = Number(match[3]);
        } else {
            match = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);

            if (!match) {
                return null;
            }

            year = Number(match[1]);
            month = Number(match[2]);
            day = Number(match[3]);
        }
    }

    const parsed = new Date(Date.UTC(year, month - 1, day));

    /*
     * JavaScript Date can normalize invalid dates automatically.
     * Therefore we explicitly compare the resulting components.
     */
    if (
        parsed.getUTCFullYear() !== year ||
        parsed.getUTCMonth() !== month - 1 ||
        parsed.getUTCDate() !== day
    ) {
        return null;
    }

    return parsed;
}

function formatDate(value) {
    const parsed = parseDate(value);

    if (!parsed) {
        return null;
    }

    return parsed.toISOString().slice(0, 10);
}


// ============================================================================
// SECTION 10: AGE VALIDATION
// ============================================================================

function parseAge(value) {
    if (isMissing(value)) {
        return null;
    }

    if (!/^-?\d+$/.test(String(value).trim())) {
        return null;
    }

    const age = Number(value);

    if (!Number.isInteger(age) || age < 0 || age > 120) {
        return null;
    }

    return age;
}


// ============================================================================
// SECTION 11: CLEAN ONE RECORD
// ============================================================================

function cleanCustomer(row) {
    return {
        customerId: cleanWhitespace(row.customerId),
        name: normalizeName(row.name),
        email: normalizeEmail(row.email),
        phone: normalizePhone(row.phone),
        city: normalizeCity(row.city),
        state: normalizeState(row.state),
        amount: parseCurrency(row.amount),
        orderDate: formatDate(row.orderDate),
        category: normalizeCategory(row.category),
        age: parseAge(row.age)
    };
}

function cleanDataset(rows) {
    return rows.map(cleanCustomer);
}

const cleanedData = cleanDataset(rawData);

printTitle("CLEANED DATA");
printTable(cleanedData);


// ============================================================================
// SECTION 12: VALIDATION
// ============================================================================

function validateCustomerId(value) {
    return /^C\d{3}$/.test(String(value ?? ""));
}

function validateAmount(value) {
    return (
        typeof value === "number" &&
        Number.isFinite(value) &&
        value >= 0
    );
}

function validateCategory(value) {
    return [
        "Electronics",
        "Home Appliances",
        "Furniture"
    ].includes(value);
}

function validateRow(row) {
    const errors = [];

    const required = [
        "customerId",
        "name",
        "phone",
        "city",
        "state",
        "category"
    ];

    for (const property of required) {
        if (isMissing(row[property])) {
            errors.push(`${property} is required`);
        }
    }

    if (!validateCustomerId(row.customerId)) {
        errors.push("customerId has invalid format");
    }

    if (row.email !== null && !validateEmail(row.email)) {
        errors.push("email has invalid format");
    }

    if (!validateAmount(row.amount)) {
        errors.push("amount is invalid or negative");
    }

    if (row.orderDate !== null && !parseDate(row.orderDate)) {
        errors.push("orderDate is invalid");
    }

    if (row.age === null) {
        errors.push("age is invalid or missing");
    }

    if (!validateCategory(row.category)) {
        errors.push("category is outside the controlled vocabulary");
    }

    return errors;
}

printTitle("ROW VALIDATION");

cleanedData.forEach((row, index) => {
    const errors = validateRow(row);

    console.log(
        `Row ${index + 2}: ${errors.length === 0 ? "VALID" : "INVALID"}`
    );

    errors.forEach(error => console.log(`  - ${error}`));
});


// ============================================================================
// SECTION 13: CROSS-FIELD VALIDATION
// ============================================================================

function validateRelationships(row) {
    const errors = [];

    if (
        ["Lucknow", "Kanpur"].includes(row.city) &&
        row.state !== "Uttar Pradesh"
    ) {
        errors.push("city/state relationship is inconsistent");
    }

    if (
        row.amount !== null &&
        typeof row.amount === "number" &&
        row.amount < 0
    ) {
        errors.push("amount cannot be negative");
    }

    return errors;
}

printTitle("CROSS-FIELD VALIDATION");

cleanedData.forEach((row, index) => {
    const errors = validateRelationships(row);

    if (errors.length > 0) {
        console.log(`Row ${index + 2}:`);
        errors.forEach(error => console.log(`  - ${error}`));
    }
});


// ============================================================================
// SECTION 14: DUPLICATE DETECTION
// ============================================================================

function findDuplicates(rows, property) {
    const groups = new Map();

    rows.forEach((row, index) => {
        const value = row[property];

        if (!groups.has(value)) {
            groups.set(value, []);
        }

        groups.get(value).push(index + 2);
    });

    return [...groups.entries()]
        .filter(([, indexes]) => indexes.length > 1)
        .map(([value, indexes]) => ({
            value,
            rows: indexes
        }));
}

printTitle("DUPLICATES BY CUSTOMER ID");

console.table(findDuplicates(cleanedData, "customerId"));


// ============================================================================
// SECTION 15: EXACT DUPLICATES
// ============================================================================

function createRowSignature(row) {
    return JSON.stringify(row, Object.keys(row).sort());
}

function findExactDuplicates(rows) {
    const groups = new Map();

    rows.forEach((row, index) => {
        const signature = createRowSignature(row);

        if (!groups.has(signature)) {
            groups.set(signature, []);
        }

        groups.get(signature).push(index + 2);
    });

    return [...groups.values()].filter(
        indexes => indexes.length > 1
    );
}

console.log("Exact duplicate row groups:");
console.log(findExactDuplicates(cleanedData));


// ============================================================================
// SECTION 16: DATA QUALITY SCORES
// ============================================================================

function completenessScore(rows, requiredProperties) {
    if (rows.length === 0 || requiredProperties.length === 0) {
        return 100;
    }

    const totalCells = rows.length * requiredProperties.length;

    const populatedCells = rows.reduce(
        (count, row) =>
            count +
            requiredProperties.filter(
                property => !isMissing(row[property])
            ).length,
        0
    );

    return (populatedCells / totalCells) * 100;
}

function uniquenessScore(rows, property) {
    const values = rows
        .map(row => row[property])
        .filter(value => !isMissing(value));

    if (values.length === 0) {
        return 0;
    }

    return (new Set(values).size / values.length) * 100;
}

function validityScore(rows) {
    if (rows.length === 0) {
        return 100;
    }

    const validRows = rows.filter(
        row =>
            validateRow(row).length === 0 &&
            validateRelationships(row).length === 0
    ).length;

    return (validRows / rows.length) * 100;
}

const requiredProperties = [
    "customerId",
    "name",
    "phone",
    "city",
    "state",
    "category"
];

printTitle("DATA QUALITY SCORES");

console.log(
    `Completeness: ${completenessScore(
        cleanedData,
        requiredProperties
    ).toFixed(2)}%`
);

console.log(
    `Customer ID uniqueness: ${uniquenessScore(
        cleanedData,
        "customerId"
    ).toFixed(2)}%`
);

console.log(
    `Validity: ${validityScore(cleanedData).toFixed(2)}%`
);


// ============================================================================
// SECTION 17: AUDIT TRAIL
// ============================================================================

function createAuditTrail(before, after) {
    const changes = [];

    for (let index = 0; index < before.length; index++) {
        const oldRow = before[index];
        const newRow = after[index];

        const properties = new Set([
            ...Object.keys(oldRow),
            ...Object.keys(newRow)
        ]);

        for (const property of properties) {
            const oldValue = oldRow[property];
            const newValue = newRow[property];

            if (String(oldValue) !== String(newValue)) {
                changes.push({
                    row: index + 2,
                    column: property,
                    before: oldValue,
                    after: newValue
                });
            }
        }
    }

    return changes;
}

printTitle("AUDIT TRAIL");

console.table(createAuditTrail(rawData, cleanedData));


// ============================================================================
// SECTION 18: CONTROLLED FILTERING
// ============================================================================

function filterRows(rows, predicate) {
    return rows.filter(predicate);
}

const highValueOrders = filterRows(
    cleanedData,
    row => typeof row.amount === "number" && row.amount >= 10000
);

printTitle("ORDERS >= 10000");
console.table(highValueOrders);


// ============================================================================
// SECTION 19: SORTING
// ============================================================================

function sortByAmountDescending(rows) {
    return [...rows].sort((a, b) => {
        const amountA = a.amount ?? -Infinity;
        const amountB = b.amount ?? -Infinity;

        return amountB - amountA;
    });
}

printTitle("SORTED BY AMOUNT");
console.table(sortByAmountDescending(cleanedData));


// ============================================================================
// SECTION 20: GROUPING AND AGGREGATION
// ============================================================================

function groupSum(rows, groupProperty, valueProperty) {
    const totals = new Map();

    for (const row of rows) {
        const group = row[groupProperty];
        const value = row[valueProperty];

        if (
            isMissing(group) ||
            typeof value !== "number" ||
            !Number.isFinite(value)
        ) {
            continue;
        }

        totals.set(
            group,
            (totals.get(group) ?? 0) + value
        );
    }

    return Object.fromEntries(totals);
}

printTitle("AMOUNT BY CATEGORY");
console.table(groupSum(cleanedData, "category", "amount"));


// ============================================================================
// SECTION 21: OUTLIER DETECTION
// ============================================================================

function calculateMean(values) {
    if (values.length === 0) {
        return 0;
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function calculatePopulationStandardDeviation(values) {
    if (values.length === 0) {
        return 0;
    }

    const mean = calculateMean(values);

    const squaredDifferences = values.map(
        value => (value - mean) ** 2
    );

    return Math.sqrt(
        calculateMean(squaredDifferences)
    );
}

function calculateZScores(values) {
    const mean = calculateMean(values);
    const standardDeviation =
        calculatePopulationStandardDeviation(values);

    if (standardDeviation === 0) {
        return values.map(() => 0);
    }

    return values.map(
        value => (value - mean) / standardDeviation
    );
}

const amounts = cleanedData
    .map(row => row.amount)
    .filter(value => typeof value === "number");

printTitle("AMOUNT Z-SCORES");

calculateZScores(amounts).forEach(
    (score, index) => {
        console.log(
            `${amounts[index].toFixed(2)} -> z=${score.toFixed(3)}`
        );
    }
);


// ============================================================================
// SECTION 22: FUNCTIONAL DATA PIPELINE
// ============================================================================

const pipelineSteps = [
    {
        name: "whitespace normalization",
        transform: rows =>
            rows.map(row => {
                const result = {};

                for (const [key, value] of Object.entries(row)) {
                    result[key] = cleanWhitespace(value);
                }

                return result;
            })
    },
    {
        name: "customer normalization",
        transform: rows => rows.map(cleanCustomer)
    }
];

function runPipeline(rows, steps) {
    return steps.reduce(
        (currentRows, step) => {
            console.log(`Pipeline step: ${step.name}`);
            return step.transform(currentRows);
        },
        structuredClone(rows)
    );
}

printTitle("PIPELINE EXECUTION");

const pipelineResult = runPipeline(rawData, pipelineSteps);

console.table(pipelineResult);


// ============================================================================
// SECTION 23: ASYNCHRONOUS CLEANING
// ============================================================================

function cleanDatasetAsync(rows) {
    /*
     * The timeout demonstrates an asynchronous boundary similar to an
     * application receiving data from a file upload, API, database, or
     * browser event.
     */
    return new Promise(resolve => {
        setTimeout(() => {
            resolve(cleanDataset(rows));
        }, 10);
    });
}

async function demonstrateAsyncCleaning() {
    const result = await cleanDatasetAsync(rawData);

    console.log(
        `Asynchronous cleaning produced ${result.length} records.`
    );
}


// ============================================================================
// SECTION 24: VALIDATION TESTS
// ============================================================================

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

function runTests() {
    assert(
        cleanWhitespace("   hello    world  ") === "hello world",
        "whitespace normalization"
    );

    assert(
        normalizeEmail(" USER@EXAMPLE.COM ") === "user@example.com",
        "email normalization"
    );

    assert(
        normalizePhone("+91-9876543211") === "9876543211",
        "phone normalization"
    );

    assert(
        parseCurrency("₹ 12,500") === 12500,
        "currency parsing"
    );

    assert(
        parseCurrency("1O,500") === null,
        "invalid numeric text rejection"
    );

    assert(
        formatDate("15/09/2026") === "2026-09-15",
        "date conversion"
    );

    assert(
        formatDate("31/09/2026") === null,
        "invalid date rejection"
    );

    assert(
        parseAge("29") === 29,
        "valid age"
    );

    assert(
        parseAge("150") === null,
        "age range validation"
    );

    assert(
        validateEmail("person@example.com"),
        "valid email"
    );

    assert(
        !validateEmail("person@example"),
        "invalid email"
    );

    console.log("All JavaScript data-cleaning tests passed.");
}


// ============================================================================
// SECTION 25: CSV GENERATION
// ============================================================================

function escapeCsvValue(value) {
    if (value === null || value === undefined) {
        return "";
    }

    const text = String(value);

    if (
        text.includes(",") ||
        text.includes('"') ||
        text.includes("\n")
    ) {
        return `"${text.replace(/"/g, '""')}"`;
    }

    return text;
}

function convertToCsv(rows) {
    if (rows.length === 0) {
        return "";
    }

    const columns = Object.keys(rows[0]);

    const header = columns
        .map(escapeCsvValue)
        .join(",");

    const body = rows.map(row =>
        columns
            .map(column => escapeCsvValue(row[column]))
            .join(",")
    );

    return [header, ...body].join("\n");
}

printTitle("CSV EXPORT PREVIEW");
console.log(convertToCsv(cleanedData));


// ============================================================================
// SECTION 26: IDEMPOTENCE
// ============================================================================

function datasetsEqual(left, right) {
    return JSON.stringify(left) === JSON.stringify(right);
}

const cleanedAgain = cleanDataset(cleanedData);

console.log(
    `Idempotence test: ${
        datasetsEqual(cleanedData, cleanedAgain)
            ? "PASSED"
            : "FAILED"
    }`
);


// ============================================================================
// SECTION 27: DATA-CLEANING PRINCIPLES
// ============================================================================

printTitle("DATA-CLEANING PRINCIPLES");

const principles = [
    "Preserve raw data before transformation.",
    "Profile data before deciding how to clean it.",
    "Separate standardization from validation.",
    "Use controlled vocabularies for categorical fields.",
    "Do not silently invent missing information.",
    "Reject impossible dates rather than automatically changing them.",
    "Treat duplicate detection as a business-rule decision.",
    "Validate relationships between columns.",
    "Keep an audit trail for important transformations.",
    "Use explicit tests for edge cases.",
    "Prefer deterministic and repeatable transformations.",
    "Consider privacy and security when handling personal data."
];

principles.forEach(
    (principle, index) =>
        console.log(`${index + 1}. ${principle}`)
);


// ============================================================================
// SECTION 28: RUN TESTS AND ASYNC DEMONSTRATION
// ============================================================================

runTests();

demonstrateAsyncCleaning()
    .then(() => {
        printTitle("END OF DATA CLEANING IN EXCEL JAVASCRIPT STUDY FILE");
    })
    .catch(error => {
        console.error("Cleaning pipeline failed:", error);
        process.exitCode = 1;
    });
