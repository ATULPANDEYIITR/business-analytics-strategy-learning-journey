/*
 * Advanced Excel: INDEX, MATCH, Dynamic Arrays, and Advanced Formulas
 * ===================================================================
 *
 * This JavaScript study file models the logic behind advanced Excel
 * calculations. JavaScript is particularly useful for demonstrating:
 *
 *   - array transformations
 *   - filtering and mapping
 *   - functional programming
 *   - reusable functions
 *   - object-oriented data modeling
 *   - validation
 *   - sorting
 *   - lookup indexes
 *   - dynamic-array behavior
 *   - asynchronous data-processing patterns
 *
 * No external npm packages are required.
 *
 * Run:
 *   node advanced_excel_formulas.js
 */


"use strict";


// ============================================================================
// 1. DATA MODEL
// ============================================================================

class SalesRecord {
    constructor(
        orderId,
        region,
        salesperson,
        product,
        category,
        month,
        units,
        revenue,
        cost
    ) {
        this.orderId = orderId;
        this.region = region;
        this.salesperson = salesperson;
        this.product = product;
        this.category = category;
        this.month = month;
        this.units = units;
        this.revenue = revenue;
        this.cost = cost;
    }

    get profit() {
        return this.revenue - this.cost;
    }

    get margin() {
        return this.revenue === 0 ? 0 : this.profit / this.revenue;
    }
}


const records = [
    new SalesRecord("O1001", "North", "Asha", "Laptop Pro", "Computers", "Jan", 8, 96000, 72000),
    new SalesRecord("O1002", "South", "Ravi", "Laptop Pro", "Computers", "Jan", 6, 72000, 54000),
    new SalesRecord("O1003", "West", "Neha", "Tablet X", "Tablets", "Jan", 12, 60000, 42000),
    new SalesRecord("O1004", "East", "Vikram", "Phone Z", "Phones", "Jan", 20, 100000, 70000),
    new SalesRecord("O1005", "North", "Asha", "Tablet X", "Tablets", "Feb", 15, 75000, 52500),
    new SalesRecord("O1006", "South", "Ravi", "Phone Z", "Phones", "Feb", 17, 85000, 59500),
    new SalesRecord("O1007", "West", "Neha", "Laptop Pro", "Computers", "Feb", 10, 120000, 90000),
    new SalesRecord("O1008", "East", "Vikram", "Tablet X", "Tablets", "Feb", 9, 45000, 31500),
    new SalesRecord("O1009", "North", "Asha", "Phone Z", "Phones", "Mar", 25, 125000, 87500),
    new SalesRecord("O1010", "South", "Ravi", "Tablet X", "Tablets", "Mar", 14, 70000, 49000),
    new SalesRecord("O1011", "West", "Neha", "Phone Z", "Phones", "Mar", 22, 110000, 77000),
    new SalesRecord("O1012", "East", "Vikram", "Laptop Pro", "Computers", "Mar", 7, 84000, 63000)
];


// ============================================================================
// 2. DISPLAY HELPERS
// ============================================================================

function section(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}


function printRows(rows) {
    for (const row of rows) {
        console.log(row.join(" | "));
    }
}


// ============================================================================
// 3. INDEX
// ============================================================================

function excelIndex(array, rowNumber, columnNumber = null) {
    /*
     * Excel uses one-based positions.
     * JavaScript arrays use zero-based indexes.
     *
     * =INDEX(A2:A10, 3)
     * becomes excelIndex(range, 3)
     *
     * =INDEX(A2:D10, 3, 2)
     * becomes excelIndex(table, 3, 2)
     */

    if (!Number.isInteger(rowNumber) || rowNumber < 1) {
        throw new RangeError("INDEX row number must be a positive integer.");
    }

    if (rowNumber > array.length) {
        throw new RangeError("INDEX row is outside the supplied range.");
    }

    if (columnNumber === null) {
        return array[rowNumber - 1];
    }

    if (!Number.isInteger(columnNumber) || columnNumber < 1) {
        throw new RangeError("INDEX column number must be a positive integer.");
    }

    const row = array[rowNumber - 1];

    if (!Array.isArray(row)) {
        throw new TypeError("A column number requires a two-dimensional array.");
    }

    if (columnNumber > row.length) {
        throw new RangeError("INDEX column is outside the supplied range.");
    }

    return row[columnNumber - 1];
}


// ============================================================================
// 4. MATCH
// ============================================================================

function excelMatch(lookupValue, lookupArray, matchType = 0) {
    /*
     * matchType 0:
     *   Exact match.
     *
     * matchType 1:
     *   Largest value <= lookupValue.
     *   Data must be ascending.
     *
     * matchType -1:
     *   Smallest value >= lookupValue.
     *   Data must be descending.
     */

    if (!Array.isArray(lookupArray) || lookupArray.length === 0) {
        throw new RangeError("MATCH requires a non-empty array.");
    }

    if (matchType === 0) {
        const index = lookupArray.findIndex(value => value === lookupValue);

        if (index === -1) {
            throw new Error(`MATCH could not find ${String(lookupValue)}.`);
        }

        return index + 1;
    }

    if (matchType === 1) {
        let candidate = -1;

        for (let i = 0; i < lookupArray.length; i++) {
            if (lookupArray[i] <= lookupValue) {
                candidate = i;
            } else {
                break;
            }
        }

        if (candidate === -1) {
            throw new Error("No approximate MATCH result exists.");
        }

        return candidate + 1;
    }

    if (matchType === -1) {
        let candidate = -1;

        for (let i = 0; i < lookupArray.length; i++) {
            if (lookupArray[i] >= lookupValue) {
                candidate = i;
            } else {
                break;
            }
        }

        if (candidate === -1) {
            throw new Error("No reverse approximate MATCH result exists.");
        }

        return candidate + 1;
    }

    throw new RangeError("matchType must be -1, 0, or 1.");
}


// ============================================================================
// 5. INDEX + MATCH
// ============================================================================

function indexMatch(returnValues, lookupValues, lookupValue) {
    /*
     * Conceptual Excel formula:
     *
     * =INDEX(return_range, MATCH(lookup_value, lookup_range, 0))
     */

    const position = excelMatch(lookupValue, lookupValues, 0);
    return excelIndex(returnValues, position);
}


// ============================================================================
// 6. TWO-WAY LOOKUP
// ============================================================================

function twoWayLookup(
    table,
    rowLabels,
    columnLabels,
    rowKey,
    columnKey
) {
    /*
     * Conceptual formula:
     *
     * =INDEX(
     *     data,
     *     MATCH(rowKey, rowLabels, 0),
     *     MATCH(columnKey, columnLabels, 0)
     * )
     */

    const rowPosition = excelMatch(rowKey, rowLabels, 0);
    const columnPosition = excelMatch(columnKey, columnLabels, 0);

    return excelIndex(table, rowPosition, columnPosition);
}


// ============================================================================
// 7. MULTI-CRITERIA LOOKUP
// ============================================================================

function multiCriteriaLookup(data, criteria) {
    /*
     * Excel can combine Boolean conditions:
     *
     * (Region=selectedRegion) *
     * (Product=selectedProduct) *
     * (Month=selectedMonth)
     *
     * The JavaScript equivalent is an every-style logical test.
     */

    const record = data.find(item =>
        item.region === criteria.region &&
        item.product === criteria.product &&
        item.month === criteria.month
    );

    if (!record) {
        throw new Error("No record satisfies all lookup criteria.");
    }

    return record;
}


// ============================================================================
// 8. FILTER
// ============================================================================

function excelFilter(array, predicate, ifEmpty = []) {
    /*
     * Dynamic-array behavior:
     *
     * =FILTER(array, condition)
     *
     * Unlike a single-value lookup, FILTER can return an arbitrary number
     * of matching records.
     */

    const result = array.filter(predicate);
    return result.length > 0 ? result : ifEmpty;
}


// ============================================================================
// 9. UNIQUE
// ============================================================================

function excelUnique(values) {
    /*
     * JavaScript Set naturally models a UNIQUE dynamic-array operation.
     *
     * =UNIQUE(A2:A100)
     */

    return [...new Set(values)];
}


// ============================================================================
// 10. SORT AND SORTBY
// ============================================================================

function excelSort(values, descending = false) {
    return [...values].sort((a, b) => {
        const comparison = a < b ? -1 : a > b ? 1 : 0;
        return descending ? -comparison : comparison;
    });
}


function excelSortBy(data, keyFunction, descending = false) {
    return [...data].sort((a, b) => {
        const left = keyFunction(a);
        const right = keyFunction(b);

        const comparison = left < right ? -1 : left > right ? 1 : 0;

        return descending ? -comparison : comparison;
    });
}


// ============================================================================
// 11. SEQUENCE
// ============================================================================

function excelSequence(rows, columns = 1, start = 1, step = 1) {
    if (!Number.isInteger(rows) || rows < 1) {
        throw new RangeError("SEQUENCE rows must be positive.");
    }

    if (!Number.isInteger(columns) || columns < 1) {
        throw new RangeError("SEQUENCE columns must be positive.");
    }

    const result = [];
    let current = start;

    for (let row = 0; row < rows; row++) {
        const currentRow = [];

        for (let column = 0; column < columns; column++) {
            currentRow.push(current);
            current += step;
        }

        result.push(currentRow);
    }

    return result;
}


// ============================================================================
// 12. TAKE
// ============================================================================

function excelTake(matrix, rows = null, columns = null) {
    let result = matrix.map(row => [...row]);

    if (rows !== null) {
        result = rows >= 0
            ? result.slice(0, rows)
            : result.slice(rows);
    }

    if (columns !== null) {
        result = result.map(row =>
            columns >= 0
                ? row.slice(0, columns)
                : row.slice(columns)
        );
    }

    return result;
}


// ============================================================================
// 13. DROP
// ============================================================================

function excelDrop(matrix, rows = 0, columns = 0) {
    let result = matrix.map(row => [...row]);

    if (rows > 0) {
        result = result.slice(rows);
    } else if (rows < 0) {
        result = result.slice(0, rows);
    }

    if (columns > 0) {
        result = result.map(row => row.slice(columns));
    } else if (columns < 0) {
        result = result.map(row => row.slice(0, columns));
    }

    return result;
}


// ============================================================================
// 14. CHOOSECOLS
// ============================================================================

function excelChooseCols(matrix, ...columnNumbers) {
    return matrix.map(row =>
        columnNumbers.map(columnNumber => {
            const index = columnNumber > 0
                ? columnNumber - 1
                : row.length + columnNumber;

            if (index < 0 || index >= row.length) {
                throw new RangeError("CHOOSECOLS index is outside the array.");
            }

            return row[index];
        })
    );
}


// ============================================================================
// 15. CHOOSEROWS
// ============================================================================

function excelChooseRows(matrix, ...rowNumbers) {
    return rowNumbers.map(rowNumber => {
        const index = rowNumber > 0
            ? rowNumber - 1
            : matrix.length + rowNumber;

        if (index < 0 || index >= matrix.length) {
            throw new RangeError("CHOOSEROWS index is outside the array.");
        }

        return [...matrix[index]];
    });
}


// ============================================================================
// 16. HSTACK
// ============================================================================

function excelHStack(...arrays) {
    if (arrays.length === 0) {
        return [];
    }

    const rowCount = Math.max(...arrays.map(array => array.length));
    const result = Array.from({ length: rowCount }, () => []);

    for (const array of arrays) {
        const width = array.length > 0 ? array[0].length : 0;

        for (let row = 0; row < rowCount; row++) {
            if (row < array.length) {
                result[row].push(...array[row]);
            } else {
                result[row].push(...Array(width).fill("#N/A"));
            }
        }
    }

    return result;
}


// ============================================================================
// 17. VSTACK
// ============================================================================

function excelVStack(...arrays) {
    const width = Math.max(
        0,
        ...arrays.flat().map(row => row.length)
    );

    return arrays.flatMap(array =>
        array.map(row => [
            ...row,
            ...Array(width - row.length).fill("#N/A")
        ])
    );
}


// ============================================================================
// 18. IFERROR / IFNA
// ============================================================================

function excelIfError(operation, fallback) {
    try {
        return operation();
    } catch {
        return fallback;
    }
}


function excelIfNa(operation, fallback) {
    try {
        return operation();
    } catch (error) {
        if (error instanceof Error) {
            return fallback;
        }
        throw error;
    }
}


// ============================================================================
// 19. CONDITIONAL AGGREGATION
// ============================================================================

function sumIf(data, predicate, valueFunction) {
    return data
        .filter(predicate)
        .reduce((total, item) => total + valueFunction(item), 0);
}


function countIf(data, predicate) {
    return data.filter(predicate).length;
}


function averageIf(data, predicate, valueFunction) {
    const selected = data
        .filter(predicate)
        .map(valueFunction);

    if (selected.length === 0) {
        throw new Error("AVERAGEIFS has no qualifying values.");
    }

    return selected.reduce((sum, value) => sum + value, 0) / selected.length;
}


// ============================================================================
// 20. SUMPRODUCT
// ============================================================================

function sumProduct(first, second) {
    if (first.length !== second.length) {
        throw new RangeError("SUMPRODUCT arrays must have equal lengths.");
    }

    return first.reduce(
        (total, value, index) => total + value * second[index],
        0
    );
}


function weightedAverage(values, weights) {
    const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);

    if (totalWeight === 0) {
        throw new Error("Weighted average requires non-zero weights.");
    }

    return sumProduct(values, weights) / totalWeight;
}


// ============================================================================
// 21. LET-STYLE COMPUTATION
// ============================================================================

function calculateRegionalMetrics(data, region) {
    /*
     * LET encourages naming intermediate calculations.
     *
     * Instead of repeating FILTER several times, calculate it once and
     * derive several outputs from the same logical subset.
     */

    const regionalRecords = data.filter(item => item.region === region);

    const revenues = regionalRecords.map(item => item.revenue);
    const profits = regionalRecords.map(item => item.profit);

    const totalRevenue = revenues.reduce((sum, value) => sum + value, 0);
    const totalProfit = profits.reduce((sum, value) => sum + value, 0);

    const averageRevenue = revenues.length > 0
        ? totalRevenue / revenues.length
        : 0;

    const margin = totalRevenue === 0
        ? 0
        : totalProfit / totalRevenue;

    return {
        region,
        orders: regionalRecords.length,
        totalRevenue,
        totalProfit,
        averageRevenue,
        margin
    };
}


// ============================================================================
// 22. LAMBDA-STYLE REUSABLE FUNCTION
// ============================================================================

const marginCalculator = (revenue, cost) => {
    if (revenue === 0) {
        return 0;
    }

    return (revenue - cost) / revenue;
};


// ============================================================================
// 23. WILDCARD MATCHING
// ============================================================================

function wildcardToRegExp(pattern) {
    let expression = "^";

    for (let index = 0; index < pattern.length; index++) {
        const character = pattern[index];

        if (character === "~" && index + 1 < pattern.length) {
            index++;
            expression += characterEscape(pattern[index]);
            continue;
        }

        if (character === "*") {
            expression += ".*";
        } else if (character === "?") {
            expression += ".";
        } else {
            expression += characterEscape(character);
        }
    }

    expression += "$";

    return new RegExp(expression, "i");
}


function characterEscape(character) {
    return character.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}


function wildcardMatch(pattern, value) {
    return wildcardToRegExp(pattern).test(value);
}


// ============================================================================
// 24. APPROXIMATE LOOKUP
// ============================================================================

function approximateLookupAscending(
    lookupValue,
    thresholds,
    results
) {
    if (thresholds.length !== results.length) {
        throw new RangeError("Thresholds and results must have equal lengths.");
    }

    if (thresholds.length === 0) {
        throw new RangeError("Threshold table cannot be empty.");
    }

    for (let i = 1; i < thresholds.length; i++) {
        if (thresholds[i] < thresholds[i - 1]) {
            throw new Error("Thresholds must be ascending.");
        }
    }

    let position = -1;

    for (let i = 0; i < thresholds.length; i++) {
        if (thresholds[i] <= lookupValue) {
            position = i;
        } else {
            break;
        }
    }

    if (position === -1) {
        throw new Error("Value is below the first threshold.");
    }

    return results[position];
}


// ============================================================================
// 25. RANKING
// ============================================================================

function rankDescending(value, values) {
    return 1 + values.filter(other => other > value).length;
}


// ============================================================================
// 26. RUNNING TOTAL
// ============================================================================

function runningTotal(values) {
    let total = 0;

    return values.map(value => {
        total += value;
        return total;
    });
}


// ============================================================================
// 27. RUNNING AVERAGE
// ============================================================================

function runningAverage(values) {
    let total = 0;

    return values.map((value, index) => {
        total += value;
        return total / (index + 1);
    });
}


// ============================================================================
// 28. DISTINCT COUNT
// ============================================================================

function distinctCount(values) {
    return excelUnique(values).length;
}


// ============================================================================
// 29. LOOKUP INDEX FOR PERFORMANCE
// ============================================================================

function buildOrderIndex(data) {
    /*
     * Repeatedly scanning a large Excel range is conceptually O(n) per
     * lookup. Building an index once changes repeated exact lookups to
     * average O(1).
     */

    const index = new Map();

    for (const record of data) {
        index.set(record.orderId, record);
    }

    return index;
}


// ============================================================================
// 30. ASYNCHRONOUS DATA-PROCESSING EXAMPLE
// ============================================================================

async function processDynamicArrayAsync(data, predicate) {
    /*
     * A spreadsheet formula calculates synchronously inside the workbook.
     * JavaScript applications may need to combine calculation logic with
     * asynchronous APIs. This function demonstrates that application-level
     * pattern without requiring a network request.
     */

    await Promise.resolve();

    return excelFilter(data, predicate);
}


// ============================================================================
// 31. MAIN
// ============================================================================

async function main() {
    section("ADVANCED EXCEL FORMULAS: JAVASCRIPT STUDY IMPLEMENTATION");

    console.log(
        [
            "INDEX returns a value by position.",
            "MATCH returns a position.",
            "INDEX + MATCH combines both operations.",
            "Dynamic arrays produce variable-sized result sets.",
            "LET names intermediate calculations.",
            "LAMBDA creates reusable calculation logic."
        ].join("\n")
    );


    // ------------------------------------------------------------------------
    // INDEX
    // ------------------------------------------------------------------------

    section("1. INDEX");

    const matrix = [
        ["North", 120000, 0.25],
        ["South", 90000, 0.20],
        ["West", 150000, 0.30],
        ["East", 110000, 0.22]
    ];

    console.log("INDEX row 3:", excelIndex(matrix, 3));
    console.log("INDEX row 2, column 2:", excelIndex(matrix, 2, 2));


    // ------------------------------------------------------------------------
    // MATCH
    // ------------------------------------------------------------------------

    section("2. MATCH");

    const products = ["Laptop Pro", "Tablet X", "Phone Z"];

    console.log(
        "Exact MATCH:",
        excelMatch("Tablet X", products, 0)
    );

    const thresholds = [0, 10000, 50000, 100000];

    console.log(
        "Approximate MATCH:",
        excelMatch(75000, thresholds, 1)
    );


    // ------------------------------------------------------------------------
    // INDEX + MATCH
    // ------------------------------------------------------------------------

    section("3. INDEX + MATCH");

    const prices = [12000, 5000, 3000];

    console.log(
        "Tablet X price:",
        indexMatch(prices, products, "Tablet X")
    );


    // ------------------------------------------------------------------------
    // TWO-WAY LOOKUP
    // ------------------------------------------------------------------------

    section("4. TWO-WAY INDEX + MATCH");

    const regions = ["North", "South", "West", "East"];
    const months = ["Jan", "Feb", "Mar"];

    const revenueTable = [
        [96000, 75000, 125000],
        [72000, 85000, 70000],
        [60000, 120000, 110000],
        [100000, 45000, 84000]
    ];

    console.log(
        "West / Feb revenue:",
        twoWayLookup(
            revenueTable,
            regions,
            months,
            "West",
            "Feb"
        )
    );


    // ------------------------------------------------------------------------
    // MULTI-CRITERIA
    // ------------------------------------------------------------------------

    section("5. MULTI-CRITERIA LOOKUP");

    const multiResult = multiCriteriaLookup(records, {
        region: "North",
        product: "Tablet X",
        month: "Feb"
    });

    console.log("Matching order:", multiResult.orderId);
    console.log("Revenue:", multiResult.revenue);


    // ------------------------------------------------------------------------
    // FILTER
    // ------------------------------------------------------------------------

    section("6. FILTER");

    const northRecords = excelFilter(
        records,
        record => record.region === "North"
    );

    printRows(
        northRecords.map(record => [
            record.orderId,
            record.product,
            record.month,
            record.revenue
        ])
    );

    const highProfitRecords = excelFilter(
        records,
        record => record.profit >= 30000
    );

    console.log(
        "Profit >= 30000:",
        highProfitRecords.map(record => record.orderId)
    );


    // ------------------------------------------------------------------------
    // UNIQUE
    // ------------------------------------------------------------------------

    section("7. UNIQUE");

    console.log(
        "Unique regions:",
        excelUnique(records.map(record => record.region))
    );

    console.log(
        "Unique products:",
        excelUnique(records.map(record => record.product))
    );


    // ------------------------------------------------------------------------
    // SORTBY
    // ------------------------------------------------------------------------

    section("8. SORTBY");

    const topOrders = excelSortBy(
        records,
        record => record.profit,
        true
    ).slice(0, 5);

    printRows(
        topOrders.map(record => [
            record.orderId,
            record.product,
            record.region,
            record.profit
        ])
    );


    // ------------------------------------------------------------------------
    // SEQUENCE
    // ------------------------------------------------------------------------

    section("9. SEQUENCE");

    console.log(
        "SEQUENCE(3, 4, 10, 10):",
        excelSequence(3, 4, 10, 10)
    );


    // ------------------------------------------------------------------------
    // TAKE / DROP
    // ------------------------------------------------------------------------

    section("10. TAKE AND DROP");

    const table = [
        ["Order", "Region", "Product", "Revenue", "Profit"],
        ["O1001", "North", "Laptop Pro", 96000, 24000],
        ["O1002", "South", "Laptop Pro", 72000, 18000],
        ["O1003", "West", "Tablet X", 60000, 18000],
        ["O1004", "East", "Phone Z", 100000, 30000]
    ];

    console.log("TAKE:");
    printRows(excelTake(table, 3));

    console.log("\nDROP:");
    printRows(excelDrop(table, 1));


    // ------------------------------------------------------------------------
    // CHOOSECOLS / CHOOSEROWS
    // ------------------------------------------------------------------------

    section("11. CHOOSECOLS AND CHOOSEROWS");

    console.log("CHOOSECOLS:");
    printRows(excelChooseCols(table, 1, 3, 5));

    console.log("\nCHOOSEROWS:");
    printRows(excelChooseRows(table, 1, -1));


    // ------------------------------------------------------------------------
    // HSTACK / VSTACK
    // ------------------------------------------------------------------------

    section("12. HSTACK AND VSTACK");

    const left = [
        ["A", 10],
        ["B", 20]
    ];

    const right = [
        ["X"],
        ["Y"]
    ];

    console.log("HSTACK:");
    printRows(excelHStack(left, right));

    console.log("\nVSTACK:");
    printRows(excelVStack(left, right));


    // ------------------------------------------------------------------------
    // CONDITIONAL AGGREGATION
    // ------------------------------------------------------------------------

    section("13. SUMIFS, COUNTIFS, AVERAGEIFS");

    console.log(
        "North revenue:",
        sumIf(
            records,
            record => record.region === "North",
            record => record.revenue
        )
    );

    console.log(
        "North orders:",
        countIf(
            records,
            record => record.region === "North"
        )
    );

    console.log(
        "North average revenue:",
        averageIf(
            records,
            record => record.region === "North",
            record => record.revenue
        )
    );

    console.log(
        "North Phone Z revenue:",
        sumIf(
            records,
            record =>
                record.region === "North" &&
                record.product === "Phone Z",
            record => record.revenue
        )
    );


    // ------------------------------------------------------------------------
    // SUMPRODUCT
    // ------------------------------------------------------------------------

    section("14. SUMPRODUCT");

    const units = records.map(record => record.units);
    const revenues = records.map(record => record.revenue);

    console.log(
        "Revenue total:",
        sumProduct(Array(revenues.length).fill(1), revenues)
    );

    console.log(
        "Weighted average:",
        weightedAverage(
            [100, 200, 300],
            [2, 3, 5]
        )
    );


    // ------------------------------------------------------------------------
    // LET
    // ------------------------------------------------------------------------

    section("15. LET-STYLE CALCULATION");

    console.log(
        calculateRegionalMetrics(records, "North")
    );


    // ------------------------------------------------------------------------
    // LAMBDA
    // ------------------------------------------------------------------------

    section("16. LAMBDA-STYLE FUNCTION");

    for (const [revenue, cost] of [
        [1000, 700],
        [5000, 3000],
        [0, 0]
    ]) {
        console.log(
            `Revenue=${revenue}, Cost=${cost}, Margin=${(
                marginCalculator(revenue, cost) * 100
            ).toFixed(2)}%`
        );
    }


    // ------------------------------------------------------------------------
    // WILDCARDS
    // ------------------------------------------------------------------------

    section("17. WILDCARD MATCHING");

    for (const pattern of ["Laptop*", "?hone Z", "Tablet ?"]) {
        console.log(
            pattern,
            "->",
            products.filter(product =>
                wildcardMatch(pattern, product)
            )
        );
    }


    // ------------------------------------------------------------------------
    // APPROXIMATE LOOKUP
    // ------------------------------------------------------------------------

    section("18. APPROXIMATE LOOKUP");

    const levels = [
        "Bronze",
        "Silver",
        "Gold",
        "Platinum"
    ];

    for (const revenue of [
        5000,
        10000,
        25000,
        50000,
        75000,
        100000,
        150000
    ]) {
        console.log(
            revenue,
            "->",
            approximateLookupAscending(
                revenue,
                thresholds,
                levels
            )
        );
    }


    // ------------------------------------------------------------------------
    // RANKING
    // ------------------------------------------------------------------------

    section("19. RANKING");

    const profits = records.map(record => record.profit);

    printRows(
        records.map(record => [
            record.orderId,
            record.profit,
            rankDescending(record.profit, profits)
        ])
    );


    // ------------------------------------------------------------------------
    // RUNNING CALCULATIONS
    // ------------------------------------------------------------------------

    section("20. RUNNING CALCULATIONS");

    const monthlyRevenue = ["Jan", "Feb", "Mar"].map(month =>
        records
            .filter(record => record.month === month)
            .reduce((sum, record) => sum + record.revenue, 0)
    );

    console.log("Monthly revenue:", monthlyRevenue);
    console.log("Running total:", runningTotal(monthlyRevenue));
    console.log("Running average:", runningAverage(monthlyRevenue));


    // ------------------------------------------------------------------------
    // DISTINCT COUNT
    // ------------------------------------------------------------------------

    section("21. DISTINCT COUNT");

    console.log(
        "Distinct salespeople:",
        distinctCount(records.map(record => record.salesperson))
    );


    // ------------------------------------------------------------------------
    // PERFORMANCE INDEX
    // ------------------------------------------------------------------------

    section("22. PERFORMANCE-ORIENTED LOOKUP INDEX");

    const orderIndex = buildOrderIndex(records);

    console.log(
        "Indexed order O1007:",
        orderIndex.get("O1007")
    );

    console.log(
        "Missing order:",
        orderIndex.get("O9999") ?? "Not Found"
    );


    // ------------------------------------------------------------------------
    // ASYNCHRONOUS DYNAMIC ARRAY
    // ------------------------------------------------------------------------

    section("23. ASYNCHRONOUS APPLICATION PATTERN");

    const asyncResult = await processDynamicArrayAsync(
        records,
        record => record.profit >= 30000
    );

    console.log(
        "Async filtered orders:",
        asyncResult.map(record => record.orderId)
    );


    // ------------------------------------------------------------------------
    // ERROR HANDLING
    // ------------------------------------------------------------------------

    section("24. ERROR HANDLING");

    const missingValue = excelIfNa(
        () => excelMatch(
            "Missing",
            ["A", "B", "C"],
            0
        ),
        "Not Found"
    );

    console.log("IFNA-style result:", missingValue);

    const divisionFallback = excelIfError(
        () => 10 / 0,
        "Calculation Error"
    );

    /*
     * JavaScript produces Infinity for ordinary floating-point division by
     * zero rather than throwing an exception. A production implementation
     * should explicitly validate denominators when Infinity is unacceptable.
     */
    console.log(
        "JavaScript division result:",
        divisionFallback
    );


    // ------------------------------------------------------------------------
    // IMPORTANT DISTINCTIONS
    // ------------------------------------------------------------------------

    section("25. IMPORTANT DISTINCTIONS");

    printRows([
        ["INDEX", "Returns a value by position"],
        ["MATCH", "Returns a position"],
        ["INDEX + MATCH", "Combines position lookup and value retrieval"],
        ["FILTER", "Returns all qualifying records"],
        ["UNIQUE", "Returns distinct values"],
        ["SORT / SORTBY", "Creates ordered dynamic results"],
        ["LET", "Names intermediate calculations"],
        ["LAMBDA", "Creates reusable calculation logic"],
        ["SUMIFS", "Conditional numeric aggregation"],
        ["SUMPRODUCT", "Element-wise multiplication followed by aggregation"]
    ]);

    console.log("\nStudy complete.");
}


main().catch(error => {
    console.error("Program failed:", error.message);
    process.exitCode = 1;
});
