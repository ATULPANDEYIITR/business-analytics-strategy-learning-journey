/*
 * Excel Functions: A Comprehensive JavaScript Study File
 *
 * This file models spreadsheet-style functions using standard JavaScript.
 * The examples progress from basic aggregation and logical formulas to
 * text manipulation, conditional aggregation, lookup functions, dates,
 * dynamic-array-style operations, financial calculations, validation,
 * asynchronous calculation, and a practical sales analysis.
 */

"use strict";

// ============================================================================
// 1. BASIC UTILITIES
// ============================================================================

function section(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function demo(label, value) {
    console.log(`${label.padEnd(38)} ${value}`);
}

function flatten(values) {
    const result = [];

    for (const value of values) {
        if (Array.isArray(value)) {
            result.push(...flatten(value));
        } else {
            result.push(value);
        }
    }

    return result;
}

function numericValues(values) {
    return flatten(values).filter(
        value => typeof value === "number" && Number.isFinite(value)
    );
}

// ============================================================================
// 2. AGGREGATION FUNCTIONS
// ============================================================================

function excelSUM(...args) {
    return numericValues(args).reduce((total, value) => total + value, 0);
}

function excelAVERAGE(...args) {
    const values = numericValues(args);
    if (values.length === 0) {
        throw new Error("#DIV/0!");
    }
    return excelSUM(values) / values.length;
}

function excelMIN(...args) {
    const values = numericValues(args);
    if (values.length === 0) {
        throw new Error("#MIN!");
    }
    return Math.min(...values);
}

function excelMAX(...args) {
    const values = numericValues(args);
    if (values.length === 0) {
        throw new Error("#MAX!");
    }
    return Math.max(...values);
}

function excelCOUNT(...args) {
    return numericValues(args).length;
}

function excelCOUNTA(...args) {
    return flatten(args).filter(value => value !== null && value !== "").length;
}

function excelCOUNTBLANK(...args) {
    return flatten(args).filter(value => value === null || value === "").length;
}

function excelPRODUCT(...args) {
    return numericValues(args).reduce((product, value) => product * value, 1);
}

// ============================================================================
// 3. MATHEMATICAL FUNCTIONS
// ============================================================================

function excelROUND(number, digits = 0) {
    const factor = 10 ** digits;
    return Math.round((number + Number.EPSILON) * factor) / factor;
}

function excelROUNDUP(number, digits = 0) {
    const factor = 10 ** digits;
    return number >= 0
        ? Math.ceil(number * factor) / factor
        : Math.floor(number * factor) / factor;
}

function excelROUNDDOWN(number, digits = 0) {
    const factor = 10 ** digits;
    return number >= 0
        ? Math.floor(number * factor) / factor
        : Math.ceil(number * factor) / factor;
}

function excelINT(number) {
    return Math.floor(number);
}

function excelTRUNC(number, digits = 0) {
    const factor = 10 ** digits;
    return Math.trunc(number * factor) / factor;
}

function excelABS(number) {
    return Math.abs(number);
}

function excelSIGN(number) {
    return Math.sign(number);
}

function excelPOWER(number, power) {
    return number ** power;
}

function excelSQRT(number) {
    if (number < 0) {
        throw new Error("#NUM!");
    }
    return Math.sqrt(number);
}

function excelMOD(number, divisor) {
    if (divisor === 0) {
        throw new Error("#DIV/0!");
    }
    return ((number % divisor) + divisor) % divisor;
}

function excelQUOTIENT(numerator, denominator) {
    if (denominator === 0) {
        throw new Error("#DIV/0!");
    }
    return Math.trunc(numerator / denominator);
}

function excelCEILING(number, significance = 1) {
    if (significance === 0) {
        return 0;
    }
    return Math.ceil(number / significance) * significance;
}

function excelFLOOR(number, significance = 1) {
    if (significance === 0) {
        return 0;
    }
    return Math.floor(number / significance) * significance;
}

// ============================================================================
// 4. LOGICAL FUNCTIONS
// ============================================================================

function excelIF(condition, trueValue, falseValue) {
    return condition ? trueValue : falseValue;
}

function excelIFS(...pairs) {
    if (pairs.length % 2 !== 0) {
        throw new Error("IFS requires condition/value pairs.");
    }

    for (let index = 0; index < pairs.length; index += 2) {
        if (pairs[index]) {
            return pairs[index + 1];
        }
    }

    throw new Error("#N/A");
}

function excelAND(...conditions) {
    return conditions.every(Boolean);
}

function excelOR(...conditions) {
    return conditions.some(Boolean);
}

function excelNOT(condition) {
    return !condition;
}

function excelXOR(...conditions) {
    return conditions.filter(Boolean).length % 2 === 1;
}

function excelIFERROR(expression, fallback) {
    try {
        return expression();
    } catch {
        return fallback;
    }
}

// ============================================================================
// 5. TEXT FUNCTIONS
// ============================================================================

function excelUPPER(text) {
    return String(text).toUpperCase();
}

function excelLOWER(text) {
    return String(text).toLowerCase();
}

function excelPROPER(text) {
    return String(text)
        .toLowerCase()
        .replace(/\b\w/g, character => character.toUpperCase());
}

function excelLEN(text) {
    return String(text).length;
}

function excelTRIM(text) {
    return String(text).trim().replace(/\s+/g, " ");
}

function excelLEFT(text, count = 1) {
    return String(text).slice(0, count);
}

function excelRIGHT(text, count = 1) {
    return count === 0 ? "" : String(text).slice(-count);
}

function excelMID(text, start, count) {
    if (start < 1) {
        throw new Error("#VALUE!");
    }
    return String(text).slice(start - 1, start - 1 + count);
}

function excelFIND(findText, withinText, start = 1) {
    const index = String(withinText).indexOf(String(findText), start - 1);
    if (index === -1) {
        throw new Error("#VALUE!");
    }
    return index + 1;
}

function excelSEARCH(searchText, withinText, start = 1) {
    const index = String(withinText)
        .toLowerCase()
        .indexOf(String(searchText).toLowerCase(), start - 1);

    if (index === -1) {
        throw new Error("#VALUE!");
    }

    return index + 1;
}

function excelSUBSTITUTE(text, oldText, newText) {
    return String(text).split(oldText).join(newText);
}

function excelREPLACE(oldText, start, count, newText) {
    if (start < 1) {
        throw new Error("#VALUE!");
    }

    return (
        oldText.slice(0, start - 1) +
        newText +
        oldText.slice(start - 1 + count)
    );
}

function excelCONCAT(...values) {
    return values.map(String).join("");
}

function excelTEXTJOIN(delimiter, ignoreEmpty, ...values) {
    let items = flatten(values);

    if (ignoreEmpty) {
        items = items.filter(value => value !== null && value !== "");
    }

    return items.map(value => value ?? "").join(delimiter);
}

function excelEXACT(first, second) {
    return String(first) === String(second);
}

function excelVALUE(text) {
    const cleaned = String(text).replace(/[$,]/g, "").trim();
    const result = Number(cleaned);

    if (Number.isNaN(result)) {
        throw new Error("#VALUE!");
    }

    return result;
}

// ============================================================================
// 6. CONDITIONAL AGGREGATION
// ============================================================================

function wildcardMatch(value, pattern) {
    const escaped = String(pattern)
        .replace(/[.+^${}()|[\]\\]/g, "\\$&")
        .replace(/\*/g, ".*")
        .replace(/\?/g, ".");

    return new RegExp(`^${escaped}$`, "i").test(String(value));
}

function matchesCriteria(value, criteria) {
    if (typeof criteria === "function") {
        return Boolean(criteria(value));
    }

    if (typeof criteria === "number") {
        return value === criteria;
    }

    const text = String(criteria);
    const operators = [">=", "<=", "<>", ">", "<", "="];

    for (const operator of operators) {
        if (text.startsWith(operator)) {
            const targetText = text.slice(operator.length);
            const targetNumber = Number(targetText);

            const left = Number.isNaN(targetNumber)
                ? String(value)
                : Number(value);
            const right = Number.isNaN(targetNumber)
                ? targetText
                : targetNumber;

            switch (operator) {
                case ">=":
                    return left >= right;
                case "<=":
                    return left <= right;
                case "<>":
                    return left !== right;
                case ">":
                    return left > right;
                case "<":
                    return left < right;
                default:
                    return left === right;
            }
        }
    }

    if (text.includes("*") || text.includes("?")) {
        return wildcardMatch(value, text);
    }

    return String(value).toLowerCase() === text.toLowerCase();
}

function excelCOUNTIF(values, criteria) {
    return values.filter(value => matchesCriteria(value, criteria)).length;
}

function excelSUMIF(criteriaRange, criteria, sumRange = criteriaRange) {
    if (criteriaRange.length !== sumRange.length) {
        throw new Error("#VALUE!");
    }

    return sumRange.reduce(
        (total, value, index) =>
            matchesCriteria(criteriaRange[index], criteria)
                ? total + Number(value)
                : total,
        0
    );
}

function excelSUMIFS(sumRange, ...criteriaPairs) {
    if (criteriaPairs.length % 2 !== 0) {
        throw new Error("SUMIFS requires range/criteria pairs.");
    }

    let indices = Array.from({ length: sumRange.length }, (_, index) => index);

    for (let index = 0; index < criteriaPairs.length; index += 2) {
        const range = criteriaPairs[index];
        const criteria = criteriaPairs[index + 1];

        if (range.length !== sumRange.length) {
            throw new Error("#VALUE!");
        }

        indices = indices.filter(
            rowIndex => matchesCriteria(range[rowIndex], criteria)
        );
    }

    return indices.reduce((total, index) => total + Number(sumRange[index]), 0);
}

// ============================================================================
// 7. LOOKUP FUNCTIONS
// ============================================================================

function excelVLOOKUP(lookupValue, table, columnIndex, approximate = false) {
    if (columnIndex < 1) {
        throw new Error("#VALUE!");
    }

    if (approximate) {
        let best = null;

        for (const row of table) {
            if (row[0] <= lookupValue) {
                best = row;
            } else {
                break;
            }
        }

        if (!best) {
            throw new Error("#N/A");
        }

        return best[columnIndex - 1];
    }

    const row = table.find(candidate => candidate[0] === lookupValue);

    if (!row) {
        throw new Error("#N/A");
    }

    return row[columnIndex - 1];
}

function excelINDEX(matrix, row, column) {
    if (row < 1 || column < 1) {
        throw new Error("#VALUE!");
    }

    if (!matrix[row - 1] || matrix[row - 1][column - 1] === undefined) {
        throw new Error("#REF!");
    }

    return matrix[row - 1][column - 1];
}

function excelMATCH(lookupValue, values, matchType = 0) {
    if (matchType === 0) {
        const index = values.findIndex(value => value === lookupValue);

        if (index === -1) {
            throw new Error("#N/A");
        }

        return index + 1;
    }

    if (matchType === 1) {
        let position = null;

        values.forEach((value, index) => {
            if (value <= lookupValue) {
                position = index + 1;
            }
        });

        if (position === null) {
            throw new Error("#N/A");
        }

        return position;
    }

    if (matchType === -1) {
        const index = values.findIndex(value => value >= lookupValue);

        if (index === -1) {
            throw new Error("#N/A");
        }

        return index + 1;
    }

    throw new Error("#VALUE!");
}

function excelXLOOKUP(
    lookupValue,
    lookupArray,
    returnArray,
    notFound = "#N/A"
) {
    if (lookupArray.length !== returnArray.length) {
        throw new Error("#VALUE!");
    }

    const index = lookupArray.findIndex(value => value === lookupValue);

    return index === -1 ? notFound : returnArray[index];
}

// ============================================================================
// 8. DATE FUNCTIONS
// ============================================================================

function excelDATE(year, month, day) {
    const normalizedYear = year + Math.floor((month - 1) / 12);
    const normalizedMonth = ((month - 1) % 12 + 12) % 12;
    return new Date(Date.UTC(normalizedYear, normalizedMonth, day));
}

function excelYEAR(value) {
    return value.getUTCFullYear();
}

function excelMONTH(value) {
    return value.getUTCMonth() + 1;
}

function excelDAY(value) {
    return value.getUTCDate();
}

function excelDAYS(endDate, startDate) {
    return Math.round(
        (endDate.getTime() - startDate.getTime()) / 86400000
    );
}

function excelEOMONTH(startDate, months = 0) {
    return new Date(
        Date.UTC(
            startDate.getUTCFullYear(),
            startDate.getUTCMonth() + months + 1,
            0
        )
    );
}

function excelEDATE(startDate, months) {
    const year = startDate.getUTCFullYear();
    const month = startDate.getUTCMonth() + months;
    const day = startDate.getUTCDate();

    const target = new Date(Date.UTC(year, month, 1));
    const lastDay = new Date(
        Date.UTC(target.getUTCFullYear(), target.getUTCMonth() + 1, 0)
    ).getUTCDate();

    target.setUTCDate(Math.min(day, lastDay));
    return target;
}

function excelNETWORKDAYS(startDate, endDate, holidays = new Set()) {
    let current = new Date(startDate.getTime());
    let total = 0;

    while (current <= endDate) {
        const weekday = current.getUTCDay();

        if (
            weekday !== 0 &&
            weekday !== 6 &&
            !holidays.has(current.toISOString().slice(0, 10))
        ) {
            total++;
        }

        current.setUTCDate(current.getUTCDate() + 1);
    }

    return total;
}

function formatDate(value) {
    return value.toISOString().slice(0, 10);
}

// ============================================================================
// 9. STATISTICAL FUNCTIONS
// ============================================================================

function excelMEDIAN(...args) {
    const values = numericValues(args).sort((a, b) => a - b);

    if (values.length === 0) {
        throw new Error("#NUM!");
    }

    const middle = Math.floor(values.length / 2);

    return values.length % 2
        ? values[middle]
        : (values[middle - 1] + values[middle]) / 2;
}

function excelMODE(...args) {
    const values = numericValues(args);
    const counts = new Map();

    for (const value of values) {
        counts.set(value, (counts.get(value) || 0) + 1);
    }

    const highest = Math.max(...counts.values());

    if (highest <= 1) {
        throw new Error("#N/A");
    }

    return [...counts.entries()]
        .filter(([, count]) => count === highest)
        .sort((a, b) => a[0] - b[0])[0][0];
}

function excelSTDEVP(...args) {
    const values = numericValues(args);

    if (values.length === 0) {
        throw new Error("#DIV/0!");
    }

    const average = excelAVERAGE(values);

    return Math.sqrt(
        values.reduce(
            (sum, value) => sum + (value - average) ** 2,
            0
        ) / values.length
    );
}

function excelPERCENTILE(values, percentile) {
    if (percentile < 0 || percentile > 1 || values.length === 0) {
        throw new Error("#NUM!");
    }

    const ordered = [...values].sort((a, b) => a - b);
    const position = (ordered.length - 1) * percentile;
    const lower = Math.floor(position);
    const upper = Math.ceil(position);

    if (lower === upper) {
        return ordered[lower];
    }

    const weight = position - lower;
    return ordered[lower] +
        (ordered[upper] - ordered[lower]) * weight;
}

// ============================================================================
// 10. DYNAMIC ARRAY STYLE FUNCTIONS
// ============================================================================

function excelFILTER(rows, include) {
    if (rows.length !== include.length) {
        throw new Error("#VALUE!");
    }

    const result = rows.filter((_, index) => include[index]);

    if (result.length === 0) {
        throw new Error("#CALC!");
    }

    return result;
}

function excelSORT(rows, columnIndex, descending = false) {
    return [...rows].sort((first, second) => {
        const comparison =
            first[columnIndex] < second[columnIndex]
                ? -1
                : first[columnIndex] > second[columnIndex]
                    ? 1
                    : 0;

        return descending ? -comparison : comparison;
    });
}

function excelUNIQUE(values) {
    return [...new Set(values)];
}

function excelTRANSPOSE(matrix) {
    if (matrix.length === 0) {
        return [];
    }

    const width = matrix[0].length;

    if (matrix.some(row => row.length !== width)) {
        throw new Error("#N/A");
    }

    return Array.from(
        { length: width },
        (_, column) => matrix.map(row => row[column])
    );
}

// ============================================================================
// 11. FINANCIAL FUNCTIONS
// ============================================================================

function excelPMT(rate, periods, presentValue, futureValue = 0) {
    if (periods <= 0) {
        throw new Error("#NUM!");
    }

    if (rate === 0) {
        return -(presentValue + futureValue) / periods;
    }

    const factor = (1 + rate) ** periods;

    return -(
        rate * (presentValue * factor + futureValue)
    ) / (factor - 1);
}

function excelFV(rate, periods, payment, presentValue = 0) {
    if (periods < 0) {
        throw new Error("#NUM!");
    }

    if (rate === 0) {
        return -(presentValue + payment * periods);
    }

    const factor = (1 + rate) ** periods;

    return -(presentValue * factor + payment * (factor - 1) / rate);
}

function excelNPV(rate, ...cashFlows) {
    return cashFlows.reduce(
        (total, cashFlow, index) =>
            total + cashFlow / (1 + rate) ** (index + 1),
        0
    );
}

// ============================================================================
// 12. ERROR HANDLING
// ============================================================================

function safeDivide(numerator, denominator) {
    if (denominator === 0) {
        throw new Error("#DIV/0!");
    }

    return numerator / denominator;
}

// ============================================================================
// 13. PRACTICAL SALES DATA
// ============================================================================

const salesData = [
    {
        orderId: "ORD001",
        date: "2026-01-05",
        region: "North",
        salesperson: "Asha",
        product: "Laptop",
        units: 4,
        revenue: 240000,
        cost: 190000
    },
    {
        orderId: "ORD002",
        date: "2026-01-08",
        region: "South",
        salesperson: "Rahul",
        product: "Monitor",
        units: 8,
        revenue: 144000,
        cost: 112000
    },
    {
        orderId: "ORD003",
        date: "2026-01-12",
        region: "West",
        salesperson: "Neha",
        product: "Laptop",
        units: 3,
        revenue: 180000,
        cost: 141000
    },
    {
        orderId: "ORD004",
        date: "2026-01-15",
        region: "East",
        salesperson: "Vikram",
        product: "Keyboard",
        units: 20,
        revenue: 60000,
        cost: 38000
    },
    {
        orderId: "ORD005",
        date: "2026-02-02",
        region: "North",
        salesperson: "Asha",
        product: "Monitor",
        units: 10,
        revenue: 180000,
        cost: 140000
    },
    {
        orderId: "ORD006",
        date: "2026-02-09",
        region: "South",
        salesperson: "Rahul",
        product: "Laptop",
        units: 5,
        revenue: 300000,
        cost: 235000
    },
    {
        orderId: "ORD007",
        date: "2026-02-17",
        region: "West",
        salesperson: "Neha",
        product: "Keyboard",
        units: 30,
        revenue: 90000,
        cost: 57000
    },
    {
        orderId: "ORD008",
        date: "2026-03-04",
        region: "East",
        salesperson: "Vikram",
        product: "Laptop",
        units: 2,
        revenue: 120000,
        cost: 94000
    },
    {
        orderId: "ORD009",
        date: "2026-03-11",
        region: "North",
        salesperson: "Asha",
        product: "Keyboard",
        units: 25,
        revenue: 75000,
        cost: 47500
    },
    {
        orderId: "ORD010",
        date: "2026-03-20",
        region: "South",
        salesperson: "Rahul",
        product: "Monitor",
        units: 12,
        revenue: 216000,
        cost: 168000
    }
];

// ============================================================================
// 14. DEMONSTRATIONS
// ============================================================================

function demonstrateBasics() {
    section("1. Basic aggregation");

    const values = [10, 20, 30, 40, 50];

    demo("SUM", excelSUM(values));
    demo("AVERAGE", excelAVERAGE(values));
    demo("MIN", excelMIN(values));
    demo("MAX", excelMAX(values));
    demo("COUNT", excelCOUNT(values));
    demo("COUNTA", excelCOUNTA(values, ["Excel", "Python", ""]));
    demo("COUNTBLANK", excelCOUNTBLANK(["", null, 0, "text"]));
    demo("PRODUCT", excelPRODUCT(2, 3, 4));
}

function demonstrateMath() {
    section("2. Mathematical functions");

    demo("ROUND", excelROUND(123.4567, 2));
    demo("ROUNDUP", excelROUNDUP(123.451, 2));
    demo("ROUNDDOWN", excelROUNDDOWN(123.459, 2));
    demo("INT(-4.8)", excelINT(-4.8));
    demo("TRUNC(-4.876, 2)", excelTRUNC(-4.876, 2));
    demo("ABS(-42)", excelABS(-42));
    demo("SIGN(-42)", excelSIGN(-42));
    demo("POWER(2, 8)", excelPOWER(2, 8));
    demo("SQRT(144)", excelSQRT(144));
    demo("MOD(17, 5)", excelMOD(17, 5));
    demo("QUOTIENT(17, 5)", excelQUOTIENT(17, 5));
    demo("CEILING(17.1, 5)", excelCEILING(17.1, 5));
    demo("FLOOR(17.9, 5)", excelFLOOR(17.9, 5));
}

function demonstrateLogic() {
    section("3. Logical functions");

    const score = 84;
    const attendance = 91;

    demo("AND", excelAND(score >= 50, attendance >= 75));
    demo("OR", excelOR(score >= 90, attendance >= 90));
    demo("NOT", excelNOT(score < 50));
    demo("XOR", excelXOR(true, false, false));
    demo("IF", excelIF(score >= 50, "Pass", "Fail"));

    const grade = excelIFS(
        score >= 90, "A",
        score >= 80, "B",
        score >= 70, "C",
        score >= 60, "D",
        true, "F"
    );

    demo("IFS", grade);

    demo(
        "IFERROR",
        excelIFERROR(() => 10 / 0, "Unavailable")
    );
}

function demonstrateText() {
    section("4. Text functions");

    const text = "  excel functions are powerful  ";

    demo("UPPER", excelUPPER(text));
    demo("LOWER", excelLOWER(text));
    demo("PROPER", excelPROPER(text));
    demo("LEN", excelLEN(text));
    demo("TRIM", excelTRIM(text));
    demo("LEFT", excelLEFT("Spreadsheet", 6));
    demo("RIGHT", excelRIGHT("Spreadsheet", 5));
    demo("MID", excelMID("Spreadsheet", 3, 5));
    demo("FIND", excelFIND("sheet", "Spreadsheet"));
    demo("SEARCH", excelSEARCH("SHEET", "Spreadsheet"));
    demo("SUBSTITUTE", excelSUBSTITUTE("Excel Excel", "Excel", "Formula"));
    demo("REPLACE", excelREPLACE("Spreadsheet", 1, 11, "Excel"));
    demo("CONCAT", excelCONCAT("Excel", " ", "Functions"));
    demo("TEXTJOIN", excelTEXTJOIN(", ", true, ["Excel", "", "Python", "C++"]));
    demo("EXACT", excelEXACT("Excel", "Excel"));
    demo("VALUE", excelVALUE("$12,500.50"));
}

function demonstrateConditional() {
    section("5. Conditional aggregation");

    const regions = ["North", "South", "North", "West", "South", "North"];
    const revenue = [100, 150, 120, 80, 170, 90];

    demo("COUNTIF North", excelCOUNTIF(regions, "North"));
    demo("COUNTIF S*", excelCOUNTIF(regions, "S*"));
    demo("SUMIF North", excelSUMIF(regions, "North", revenue));
    demo(
        "SUMIFS North and revenue >= 100",
        excelSUMIFS(revenue, regions, "North", revenue, ">=100")
    );
}

function demonstrateLookup() {
    section("6. Lookup and reference");

    const products = [
        ["P100", "Laptop", 60000],
        ["P200", "Monitor", 18000],
        ["P300", "Keyboard", 3000],
        ["P400", "Mouse", 1500]
    ];

    demo("VLOOKUP P200", excelVLOOKUP("P200", products, 2));
    demo("INDEX row 2 col 3", excelINDEX(products, 2, 3));
    demo("MATCH P400", excelMATCH("P400", products.map(row => row[0])));
    demo(
        "XLOOKUP P100",
        excelXLOOKUP(
            "P100",
            products.map(row => row[0]),
            products.map(row => row[2])
        )
    );
}

function demonstrateDates() {
    section("7. Date functions");

    const start = excelDATE(2026, 1, 15);
    const end = excelDATE(2026, 3, 20);

    demo("DATE", formatDate(excelDATE(2026, 2, 28)));
    demo("YEAR", excelYEAR(start));
    demo("MONTH", excelMONTH(start));
    demo("DAY", excelDAY(start));
    demo("DAYS", excelDAYS(end, start));
    demo("EOMONTH", formatDate(excelEOMONTH(start, 1)));
    demo("EDATE", formatDate(excelEDATE(start, 2)));

    const holidays = new Set(["2026-01-26"]);

    demo(
        "NETWORKDAYS",
        excelNETWORKDAYS(
            excelDATE(2026, 1, 1),
            excelDATE(2026, 1, 31),
            holidays
        )
    );
}

function demonstrateStatistics() {
    section("8. Statistical functions");

    const values = [10, 12, 12, 14, 15, 18, 20, 25];

    demo("MEDIAN", excelMEDIAN(values));
    demo("MODE", excelMODE(values));
    demo("STDEV.P", excelSTDEVP(values));
    demo("PERCENTILE 75%", excelPERCENTILE(values, 0.75));
}

function demonstrateDynamicArrays() {
    section("9. Dynamic-array-style operations");

    const rows = [
        ["Asha", "North", 240000],
        ["Rahul", "South", 300000],
        ["Neha", "West", 180000],
        ["Vikram", "East", 120000]
    ];

    console.log("FILTER:");
    console.table(excelFILTER(rows, rows.map(row => row[2] >= 200000)));

    console.log("SORT:");
    console.table(excelSORT(rows, 2, true));

    demo("UNIQUE regions", excelUNIQUE(rows.map(row => row[1])).join(", "));
    console.log("TRANSPOSE:", excelTRANSPOSE([[1, 2, 3], [4, 5, 6]]));
}

function demonstrateFinance() {
    section("10. Financial functions");

    const monthlyRate = 0.08 / 12;
    const months = 60;
    const principal = 500000;

    demo(
        "PMT",
        excelPMT(monthlyRate, months, principal).toFixed(2)
    );

    demo(
        "FV",
        excelFV(0.01, 36, -10000).toFixed(2)
    );

    demo(
        "NPV",
        excelNPV(0.10, -10000, 3000, 4000, 5000).toFixed(2)
    );
}

// ============================================================================
// 15. ADVANCED SALES ANALYTICS
// ============================================================================

function performSalesAnalysis() {
    section("11. Advanced sales analysis");

    const totalRevenue = excelSUM(salesData.map(row => row.revenue));
    const totalCost = excelSUM(salesData.map(row => row.cost));
    const totalProfit = totalRevenue - totalCost;
    const margin = totalProfit / totalRevenue;

    demo("Total revenue", totalRevenue);
    demo("Total cost", totalCost);
    demo("Total profit", totalProfit);
    demo("Profit margin", `${(margin * 100).toFixed(2)}%`);

    const regions = excelUNIQUE(salesData.map(row => row.region));

    console.log("\nRegional revenue:");

    for (const region of regions) {
        const value = excelSUM(
            salesData
                .filter(row => row.region === region)
                .map(row => row.revenue)
        );

        console.log(`  ${region.padEnd(10)} ${value.toLocaleString()}`);
    }

    console.log("\nHigh-value orders:");

    const highValueOrders = excelFILTER(
        salesData,
        salesData.map(row => row.revenue >= 180000)
    );

    for (const order of highValueOrders) {
        console.log(
            `  ${order.orderId} | ${order.product} | ${order.revenue.toLocaleString()}`
        );
    }

    const profits = salesData.map(
        row => excelIF(
            row.revenue > row.cost,
            row.revenue - row.cost,
            0
        )
    );

    demo("Calculated profit", excelSUM(profits));
}

// ============================================================================
// 16. ASYNCHRONOUS FORMULA ENGINE CONCEPT
// ============================================================================

async function asynchronousCalculation(formulaFunction) {
    // A browser or application may calculate formulas after receiving data
    // from a server. Promise-based code demonstrates that execution model.
    return Promise.resolve().then(formulaFunction);
}

async function demonstrateAsyncCalculation() {
    section("12. Asynchronous calculation pattern");

    const result = await asynchronousCalculation(
        () => excelSUM([100, 200, 300])
    );

    demo("Asynchronously calculated SUM", result);
}

// ============================================================================
// 17. PERFORMANCE COMPARISON
// ============================================================================

function demonstrateLookupPerformance() {
    section("13. Lookup performance");

    const records = Array.from(
        { length: 10000 },
        (_, index) => ({
            id: `P${String(index).padStart(5, "0")}`,
            price: index * 10
        })
    );

    const target = "P09999";

    const linearRecord = records.find(record => record.id === target);

    // Map acts as an index. Construction costs O(n), repeated lookup is
    // approximately O(1) on average.
    const index = new Map(
        records.map(record => [record.id, record.price])
    );

    const indexedPrice = index.get(target);

    demo("Linear lookup", linearRecord.price);
    demo("Indexed lookup", indexedPrice);
    demo("Linear complexity", "O(n)");
    demo("Map lookup average complexity", "O(1)");
    demo("Index construction", "O(n)");
}

// ============================================================================
// 18. EDGE CASES
// ============================================================================

function demonstrateEdgeCases() {
    section("14. Edge cases and errors");

    demo("SUM ignores text", excelSUM([10, "20", 30]));
    demo("COUNT ignores text", excelCOUNT([10, "20", 30]));
    demo("COUNTBLANK", excelCOUNTBLANK([null, "", 0, "text"]));
    demo("Case-insensitive COUNTIF", excelCOUNTIF(["north", "North"], "NORTH"));

    try {
        excelAVERAGE([]);
    } catch (error) {
        demo("AVERAGE empty range", error.message);
    }

    try {
        excelVLOOKUP("P999", [["P100", "Laptop"]], 2);
    } catch (error) {
        demo("VLOOKUP missing", error.message);
    }

    demo(
        "IFERROR missing lookup",
        excelIFERROR(
            () => excelVLOOKUP("P999", [["P100", "Laptop"]], 2),
            "Not Available"
        )
    );
}

// ============================================================================
// 19. MAIN
// ============================================================================

async function main() {
    console.log("EXCEL FUNCTIONS: COMPREHENSIVE JAVASCRIPT STUDY");

    demonstrateBasics();
    demonstrateMath();
    demonstrateLogic();
    demonstrateText();
    demonstrateConditional();
    demonstrateLookup();
    demonstrateDates();
    demonstrateStatistics();
    demonstrateDynamicArrays();
    demonstrateFinance();
    performSalesAnalysis();
    await demonstrateAsyncCalculation();
    demonstrateLookupPerformance();
    demonstrateEdgeCases();

    section("15. Completion");
    console.log("All JavaScript Excel-function demonstrations completed.");
}

main().catch(error => {
    console.error("Program failed:", error);
    process.exitCode = 1;
});
