/*
 * Excel Fundamentals: Worksheets, Formulas, References and Formatting
 * ====================================================================
 *
 * This self-contained JavaScript program models important spreadsheet
 * concepts without requiring Excel or external npm packages.
 *
 * Covered:
 *   - Workbooks and worksheets
 *   - Rows, columns, cells and ranges
 *   - Values and formulas
 *   - Relative, absolute and mixed references
 *   - Formula evaluation
 *   - Spreadsheet functions
 *   - Formula copying
 *   - Dependency tracking
 *   - Formatting
 *   - Conditional formatting
 *   - Validation
 *   - Error handling
 *   - A practical sales model
 *
 * Run with:
 *   node excel_fundamentals.js
 */


// ============================================================================
// 1. COLUMN AND CELL ADDRESSING
// ============================================================================

function columnNumberToLetter(columnNumber) {
    if (!Number.isInteger(columnNumber) || columnNumber < 1) {
        throw new Error("Column number must be a positive integer.");
    }

    let number = columnNumber;
    let result = "";

    while (number > 0) {
        number -= 1;
        result = String.fromCharCode(65 + (number % 26)) + result;
        number = Math.floor(number / 26);
    }

    return result;
}


function columnLetterToNumber(columnLetters) {
    const cleaned = String(columnLetters).trim().toUpperCase();

    if (!/^[A-Z]+$/.test(cleaned)) {
        throw new Error(`Invalid column label: ${columnLetters}`);
    }

    let result = 0;

    for (const character of cleaned) {
        result = result * 26 + character.charCodeAt(0) - 64;
    }

    return result;
}


function parseCellReference(address) {
    const text = String(address).trim();

    const match = text.match(/^(\$?)([A-Za-z]{1,3})(\$?)([1-9][0-9]*)$/);

    if (!match) {
        throw new Error(`Invalid cell reference: ${address}`);
    }

    return {
        column: columnLetterToNumber(match[2]),
        row: Number(match[4]),
        columnAbsolute: match[1] === "$",
        rowAbsolute: match[3] === "$"
    };
}


function cellReferenceToAddress(reference) {
    const column = columnNumberToLetter(reference.column);
    const columnPart = reference.columnAbsolute ? `$${column}` : column;
    const rowPart = reference.rowAbsolute
        ? `$${reference.row}`
        : String(reference.row);

    return columnPart + rowPart;
}


function normalizeAddress(address) {
    const reference = parseCellReference(address);

    return `${columnNumberToLetter(reference.column)}${reference.row}`;
}


function shiftReference(address, rowDelta, columnDelta) {
    const reference = parseCellReference(address);

    const row = reference.rowAbsolute
        ? reference.row
        : reference.row + rowDelta;

    const column = reference.columnAbsolute
        ? reference.column
        : reference.column + columnDelta;

    if (row < 1 || column < 1) {
        throw new Error("Reference would leave the worksheet.");
    }

    return cellReferenceToAddress({
        ...reference,
        row,
        column
    });
}


console.log("\nCOLUMN AND REFERENCE EXAMPLES");

for (const number of [1, 26, 27, 52, 53]) {
    console.log(number, "->", columnNumberToLetter(number));
}

for (const address of ["A1", "$A$1", "A$1", "$A1"]) {
    console.log(
        address,
        "copied two rows and three columns ->",
        shiftReference(address, 2, 3)
    );
}


// ============================================================================
// 2. RANGE HANDLING
// ============================================================================

function expandRange(rangeText) {
    const match = String(rangeText)
        .trim()
        .match(
            /^\$?([A-Za-z]{1,3})\$?([1-9][0-9]*):\$?([A-Za-z]{1,3})\$?([1-9][0-9]*)$/
        );

    if (!match) {
        throw new Error(`Invalid range: ${rangeText}`);
    }

    let startColumn = columnLetterToNumber(match[1]);
    let startRow = Number(match[2]);
    let endColumn = columnLetterToNumber(match[3]);
    let endRow = Number(match[4]);

    if (startColumn > endColumn) {
        [startColumn, endColumn] = [endColumn, startColumn];
    }

    if (startRow > endRow) {
        [startRow, endRow] = [endRow, startRow];
    }

    const addresses = [];

    for (let row = startRow; row <= endRow; row += 1) {
        for (
            let column = startColumn;
            column <= endColumn;
            column += 1
        ) {
            addresses.push(
                `${columnNumberToLetter(column)}${row}`
            );
        }
    }

    return addresses;
}


console.log("\nRANGE EXAMPLE");
console.log(expandRange("A1:C3"));


// ============================================================================
// 3. FORMATTING MODEL
// ============================================================================

class CellFormat {
    constructor() {
        this.numberFormat = "General";
        this.bold = false;
        this.italic = false;
        this.horizontalAlignment = "general";
        this.verticalAlignment = "bottom";
        this.fill = null;
        this.fontName = "Calibri";
        this.fontSize = 11;
        this.fontColor = null;
        this.border = null;
        this.wrapText = false;
    }

    describe() {
        return {
            numberFormat: this.numberFormat,
            bold: this.bold,
            italic: this.italic,
            horizontalAlignment: this.horizontalAlignment,
            fill: this.fill,
            border: this.border
        };
    }
}


class ConditionalFormatRule {
    constructor(operatorName, threshold, displayFormat) {
        this.operatorName = operatorName;
        this.threshold = threshold;
        this.displayFormat = displayFormat;
    }

    applies(value) {
        if (typeof value !== "number" || !Number.isFinite(value)) {
            return false;
        }

        switch (this.operatorName) {
            case ">":
                return value > this.threshold;
            case ">=":
                return value >= this.threshold;
            case "<":
                return value < this.threshold;
            case "<=":
                return value <= this.threshold;
            case "==":
                return value === this.threshold;
            case "!=":
                return value !== this.threshold;
            default:
                throw new Error(
                    `Unsupported conditional operator: ${this.operatorName}`
                );
        }
    }
}


// ============================================================================
// 4. CELL AND WORKSHEET
// ============================================================================

class Cell {
    constructor(value = null, formula = null) {
        this.value = value;
        this.formula = formula;
        this.format = new CellFormat();
    }

    isFormula() {
        return this.formula !== null;
    }

    displayValue() {
        if (this.value === null || this.value === undefined) {
            return "";
        }

        const number = Number(this.value);

        switch (this.format.numberFormat) {
            case "0.00":
                return Number.isFinite(number)
                    ? number.toFixed(2)
                    : String(this.value);

            case "0":
                return Number.isFinite(number)
                    ? Math.round(number).toString()
                    : String(this.value);

            case "0.00%":
                return Number.isFinite(number)
                    ? `${(number * 100).toFixed(2)}%`
                    : String(this.value);

            case "$#,##0.00":
                return Number.isFinite(number)
                    ? `$${number.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}`
                    : String(this.value);

            default:
                return String(this.value);
        }
    }
}


class Worksheet {
    constructor(name) {
        if (!name || name.length > 31) {
            throw new Error(
                "Worksheet names must contain between 1 and 31 characters."
            );
        }

        this.name = name;
        this.cells = new Map();
        this.conditionalRules = new Map();
    }

    setValue(address, value) {
        this.cells.set(normalizeAddress(address), new Cell(value));
    }

    setFormula(address, formula) {
        if (typeof formula !== "string" || !formula.startsWith("=")) {
            throw new Error("A formula must begin with '='.");
        }

        this.cells.set(
            normalizeAddress(address),
            new Cell(null, formula)
        );
    }

    getCell(address) {
        const normalized = normalizeAddress(address);

        if (!this.cells.has(normalized)) {
            this.cells.set(normalized, new Cell());
        }

        return this.cells.get(normalized);
    }

    formatCell(address, changes) {
        const cell = this.getCell(address);

        for (const [property, value] of Object.entries(changes)) {
            if (!(property in cell.format)) {
                throw new Error(`Unknown formatting property: ${property}`);
            }

            cell.format[property] = value;
        }
    }

    addConditionalRule(address, rule) {
        const normalized = normalizeAddress(address);

        if (!this.conditionalRules.has(normalized)) {
            this.conditionalRules.set(normalized, []);
        }

        this.conditionalRules.get(normalized).push(rule);
    }

    usedRange() {
        if (this.cells.size === 0) {
            return {
                minRow: 1,
                maxRow: 1,
                minColumn: 1,
                maxColumn: 1
            };
        }

        const references = [...this.cells.keys()].map(parseCellReference);

        return {
            minRow: Math.min(...references.map(ref => ref.row)),
            maxRow: Math.max(...references.map(ref => ref.row)),
            minColumn: Math.min(...references.map(ref => ref.column)),
            maxColumn: Math.max(...references.map(ref => ref.column))
        };
    }

    printGrid() {
        const range = this.usedRange();

        console.log("");
        console.log(
            "      " +
            Array.from(
                { length: range.maxColumn - range.minColumn + 1 },
                (_, index) => {
                    const column =
                        range.minColumn + index;
                    return columnNumberToLetter(column)
                        .padStart(14)
                        .padEnd(18);
                }
            ).join("")
        );

        for (let row = range.minRow; row <= range.maxRow; row += 1) {
            let line = String(row).padStart(5) + " ";

            for (
                let column = range.minColumn;
                column <= range.maxColumn;
                column += 1
            ) {
                const address =
                    `${columnNumberToLetter(column)}${row}`;

                const value = this.getCell(address).displayValue();

                line += value.slice(0, 18).padStart(18);
            }

            console.log(line);
        }
    }
}


// ============================================================================
// 5. WORKBOOK
// ============================================================================

class Workbook {
    constructor() {
        this.worksheets = new Map();
    }

    addWorksheet(name) {
        if (this.worksheets.has(name)) {
            throw new Error(`Worksheet already exists: ${name}`);
        }

        const worksheet = new Worksheet(name);
        this.worksheets.set(name, worksheet);

        return worksheet;
    }

    getWorksheet(name) {
        if (!this.worksheets.has(name)) {
            throw new Error(`Worksheet not found: ${name}`);
        }

        return this.worksheets.get(name);
    }

    listWorksheets() {
        return [...this.worksheets.keys()];
    }
}


// ============================================================================
// 6. SPREADSHEET FUNCTIONS
// ============================================================================

function numericValues(values) {
    return values.filter(
        value =>
            typeof value === "number" &&
            Number.isFinite(value)
    );
}


function excelSUM(values) {
    return numericValues(values).reduce(
        (total, value) => total + value,
        0
    );
}


function excelAVERAGE(values) {
    const numbers = numericValues(values);

    if (numbers.length === 0) {
        throw new Error("#DIV/0!");
    }

    return excelSUM(numbers) / numbers.length;
}


function excelMIN(values) {
    const numbers = numericValues(values);

    if (numbers.length === 0) {
        throw new Error("#VALUE!");
    }

    return Math.min(...numbers);
}


function excelMAX(values) {
    const numbers = numericValues(values);

    if (numbers.length === 0) {
        throw new Error("#VALUE!");
    }

    return Math.max(...numbers);
}


function excelROUND(value, digits = 0) {
    if (!Number.isFinite(value)) {
        throw new Error("#NUM!");
    }

    const factor = 10 ** digits;
    return Math.round(value * factor) / factor;
}


function excelIF(condition, trueValue, falseValue) {
    return condition ? trueValue : falseValue;
}


function excelCOUNT(values) {
    return numericValues(values).length;
}


function excelCOUNTA(values) {
    return values.filter(
        value => value !== null && value !== undefined && value !== ""
    ).length;
}


// ============================================================================
// 7. SIMPLE FORMULA EVALUATOR
// ============================================================================

class FormulaError extends Error {}

class CircularReferenceError extends FormulaError {}


class FormulaEvaluator {
    constructor(worksheet) {
        this.worksheet = worksheet;
        this.evaluationStack = [];
    }

    evaluateCell(address) {
        const normalized = normalizeAddress(address);

        if (this.evaluationStack.includes(normalized)) {
            const cycle = [
                ...this.evaluationStack,
                normalized
            ].join(" -> ");

            throw new CircularReferenceError(
                `Circular reference detected: ${cycle}`
            );
        }

        const cell = this.worksheet.getCell(normalized);

        if (!cell.isFormula()) {
            return cell.value;
        }

        this.evaluationStack.push(normalized);

        try {
            return this.evaluateFormula(cell.formula);
        } finally {
            this.evaluationStack.pop();
        }
    }

    evaluateFormula(formula) {
        if (!formula.startsWith("=")) {
            throw new FormulaError(
                "Formula must begin with '='."
            );
        }

        const expression = formula.slice(1).trim();

        /*
         * This evaluator intentionally supports a restricted grammar rather
         * than using JavaScript eval(). That distinction is important:
         * arbitrary eval() would execute JavaScript instead of safely
         * interpreting spreadsheet expressions.
         */

        return this.evaluateExpression(expression);
    }

    evaluateExpression(expression) {
        const trimmed = expression.trim();

        // Remove one balanced pair of outer parentheses.
        if (
            trimmed.startsWith("(") &&
            trimmed.endsWith(")") &&
            this.isBalanced(trimmed.slice(1, -1))
        ) {
            return this.evaluateExpression(trimmed.slice(1, -1));
        }

        const functionMatch = trimmed.match(
            /^([A-Za-z_][A-Za-z0-9_]*)\((.*)\)$/
        );

        if (functionMatch && this.isBalanced(functionMatch[2])) {
            const functionName = functionMatch[1].toUpperCase();
            const argumentsList = splitArguments(functionMatch[2]);

            const argumentsValues = argumentsList.map(argument =>
                this.evaluateArgument(argument)
            );

            return this.callFunction(
                functionName,
                argumentsValues
            );
        }

        // Comparisons have lower precedence than arithmetic.
        const comparison = findTopLevelOperator(
            trimmed,
            ["<>", ">=", "<=", "=", ">", "<"]
        );

        if (comparison) {
            const left = this.evaluateExpression(
                trimmed.slice(0, comparison.index)
            );

            const right = this.evaluateExpression(
                trimmed.slice(
                    comparison.index + comparison.operator.length
                )
            );

            switch (comparison.operator) {
                case "=":
                    return left === right;
                case "<>":
                    return left !== right;
                case ">":
                    return left > right;
                case "<":
                    return left < right;
                case ">=":
                    return left >= right;
                case "<=":
                    return left <= right;
                default:
                    throw new FormulaError("Unsupported comparison.");
            }
        }

        const additive = findTopLevelOperator(
            trimmed,
            ["+", "-"]
        );

        if (additive) {
            const left = this.evaluateExpression(
                trimmed.slice(0, additive.index)
            );

            const right = this.evaluateExpression(
                trimmed.slice(
                    additive.index + additive.operator.length
                )
            );

            return additive.operator === "+"
                ? left + right
                : left - right;
        }

        const multiplicative = findTopLevelOperator(
            trimmed,
            ["*", "/"]
        );

        if (multiplicative) {
            const left = this.evaluateExpression(
                trimmed.slice(0, multiplicative.index)
            );

            const right = this.evaluateExpression(
                trimmed.slice(
                    multiplicative.index + multiplicative.operator.length
                )
            );

            if (multiplicative.operator === "/" && right === 0) {
                throw new FormulaError("#DIV/0!");
            }

            return multiplicative.operator === "*"
                ? left * right
                : left / right;
        }

        const exponent = findTopLevelOperator(
            trimmed,
            ["^"]
        );

        if (exponent) {
            const left = this.evaluateExpression(
                trimmed.slice(0, exponent.index)
            );

            const right = this.evaluateExpression(
                trimmed.slice(
                    exponent.index + exponent.operator.length
                )
            );

            return left ** right;
        }

        if (
            trimmed.startsWith('"') &&
            trimmed.endsWith('"')
        ) {
            return trimmed
                .slice(1, -1)
                .replace(/""/g, '"');
        }

        if (/^-?\d+(?:\.\d+)?$/.test(trimmed)) {
            return Number(trimmed);
        }

        const cellMatch = trimmed.match(
            /^\$?[A-Za-z]{1,3}\$?[1-9][0-9]*$/
        );

        if (cellMatch) {
            return this.evaluateCell(trimmed);
        }

        throw new FormulaError(
            `Unsupported expression: ${expression}`
        );
    }

    evaluateArgument(argument) {
        const trimmed = argument.trim();

        /*
         * A range is represented as an array of cell values. Functions such
         * as SUM flatten arrays, while ordinary arithmetic should receive
         * scalar values.
         */
        if (trimmed.includes(":")) {
            const addresses = expandRange(trimmed);

            return addresses.map(address =>
                this.evaluateCell(address)
            );
        }

        return this.evaluateExpression(trimmed);
    }

    callFunction(name, argumentsValues) {
        const flattened = argumentsValues.flat(Infinity);

        switch (name) {
            case "SUM":
                return excelSUM(flattened);

            case "AVERAGE":
                return excelAVERAGE(flattened);

            case "MIN":
                return excelMIN(flattened);

            case "MAX":
                return excelMAX(flattened);

            case "ROUND":
                if (argumentsValues.length < 1 ||
                    argumentsValues.length > 2) {
                    throw new FormulaError(
                        "ROUND requires one or two arguments."
                    );
                }

                return excelROUND(
                    argumentsValues[0],
                    argumentsValues.length === 2
                        ? argumentsValues[1]
                        : 0
                );

            case "IF":
                if (argumentsValues.length !== 3) {
                    throw new FormulaError(
                        "IF requires three arguments."
                    );
                }

                return excelIF(
                    argumentsValues[0],
                    argumentsValues[1],
                    argumentsValues[2]
                );

            case "COUNT":
                return excelCOUNT(flattened);

            case "COUNTA":
                return excelCOUNTA(flattened);

            default:
                throw new FormulaError(
                    `Unknown function: ${name}`
                );
        }
    }

    isBalanced(text) {
        let depth = 0;
        let inString = false;

        for (let index = 0; index < text.length; index += 1) {
            const character = text[index];

            if (character === '"') {
                if (inString && text[index + 1] === '"') {
                    index += 1;
                    continue;
                }

                inString = !inString;
                continue;
            }

            if (inString) {
                continue;
            }

            if (character === "(") {
                depth += 1;
            } else if (character === ")") {
                depth -= 1;

                if (depth < 0) {
                    return false;
                }
            }
        }

        return depth === 0 && !inString;
    }
}


function splitArguments(text) {
    const argumentsList = [];
    let start = 0;
    let depth = 0;
    let inString = false;

    for (let index = 0; index < text.length; index += 1) {
        const character = text[index];

        if (character === '"') {
            if (inString && text[index + 1] === '"') {
                index += 1;
                continue;
            }

            inString = !inString;
            continue;
        }

        if (inString) {
            continue;
        }

        if (character === "(") {
            depth += 1;
        } else if (character === ")") {
            depth -= 1;
        } else if (character === "," && depth === 0) {
            argumentsList.push(
                text.slice(start, index).trim()
            );
            start = index + 1;
        }
    }

    const finalArgument = text.slice(start).trim();

    if (finalArgument !== "" || text.trim() === "") {
        argumentsList.push(finalArgument);
    }

    return argumentsList;
}


function findTopLevelOperator(expression, operators) {
    let depth = 0;
    let inString = false;

    /*
     * Search from right to left for low-precedence operators.
     * This produces a compact educational parser rather than a full Excel
     * grammar.
     */
    for (let index = expression.length - 1; index >= 0; index -= 1) {
        const character = expression[index];

        if (character === '"') {
            let quoteCount = 0;

            for (let position = 0; position < index; position += 1) {
                if (expression[position] === '"') {
                    quoteCount += 1;
                }
            }

            inString = quoteCount % 2 === 1;
            continue;
        }

        if (inString) {
            continue;
        }

        if (character === ")") {
            depth += 1;
            continue;
        }

        if (character === "(") {
            depth -= 1;
            continue;
        }

        if (depth !== 0) {
            continue;
        }

        for (const operatorName of operators) {
            const start = index - operatorName.length + 1;

            if (
                start >= 0 &&
                expression.slice(
                    start,
                    index + 1
                ) === operatorName
            ) {
                // A leading minus is a unary operator, not subtraction.
                if (
                    operatorName === "-" &&
                    start === 0
                ) {
                    continue;
                }

                return {
                    index: start,
                    operator: operatorName
                };
            }
        }
    }

    return null;
}


// ============================================================================
// 8. FORMULA COPYING
// ============================================================================

function copyFormula(formula, rowDelta, columnDelta) {
    const pattern = /\$?[A-Za-z]{1,3}\$?[1-9][0-9]*/g;

    return formula.replace(pattern, reference =>
        shiftReference(
            reference,
            rowDelta,
            columnDelta
        )
    );
}


console.log("\nFORMULA COPYING");

for (let rowDelta = 0; rowDelta < 4; rowDelta += 1) {
    console.log(
        "=B2*C2 copied down",
        rowDelta,
        "row(s) ->",
        copyFormula("=B2*C2", rowDelta, 0)
    );
}

console.log(
    "=B2*$F$1 copied down one row ->",
    copyFormula("=B2*$F$1", 1, 0)
);


// ============================================================================
// 9. DEPENDENCY EXTRACTION
// ============================================================================

function extractReferences(formula) {
    const references = formula.match(
        /\$?[A-Za-z]{1,3}\$?[1-9][0-9]*/g
    ) || [];

    return references.map(normalizeAddress);
}


function buildDependencyGraph(worksheet) {
    const graph = new Map();

    for (const [address, cell] of worksheet.cells) {
        if (cell.formula) {
            graph.set(
                address,
                extractReferences(cell.formula)
            );
        }
    }

    return graph;
}


// ============================================================================
// 10. VALIDATION
// ============================================================================

function validatePositiveNumber(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        throw new Error("Value must be a finite number.");
    }

    if (number < 0) {
        throw new Error("Value cannot be negative.");
    }

    return number;
}


console.log("\nVALIDATION");

for (const value of [100, "250.5", -10, "hello", Infinity]) {
    try {
        console.log(value, "->", validatePositiveNumber(value));
    } catch (error) {
        console.log(value, "-> ERROR:", error.message);
    }
}


// ============================================================================
// 11. PRACTICAL SALES WORKBOOK
// ============================================================================

console.log("\nPRACTICAL SALES WORKBOOK");

const workbook = new Workbook();

const sales = workbook.addWorksheet("Sales");
const summary = workbook.addWorksheet("Summary");

sales.setValue("A1", "Product");
sales.setValue("B1", "Units");
sales.setValue("C1", "Unit Price");
sales.setValue("D1", "Revenue");
sales.setValue("E1", "Status");

const products = [
    ["Laptop", 5, 850],
    ["Monitor", 8, 250],
    ["Keyboard", 15, 45],
    ["Mouse", 25, 20]
];

products.forEach(([product, units, price], index) => {
    const row = index + 2;

    sales.setValue(`A${row}`, product);
    sales.setValue(`B${row}`, units);
    sales.setValue(`C${row}`, price);
    sales.setFormula(`D${row}`, `=B${row}*C${row}`);
    sales.setFormula(
        `E${row}`,
        `=IF(D${row}>=1000,"High","Normal")`
    );
});

sales.setValue("A6", "Total Revenue");
sales.setFormula("D6", "=SUM(D2:D5)");

sales.setValue("A7", "Average Revenue");
sales.setFormula("D7", "=AVERAGE(D2:D5)");

sales.setValue("A8", "Maximum Revenue");
sales.setFormula("D8", "=MAX(D2:D5)");

sales.setValue("A9", "Minimum Revenue");
sales.setFormula("D9", "=MIN(D2:D5)");


// ============================================================================
// 12. APPLY FORMATTING
// ============================================================================

for (const address of ["A1", "B1", "C1", "D1", "E1"]) {
    sales.formatCell(address, {
        bold: true,
        horizontalAlignment: "center",
        fill: "header",
        border: "bottom"
    });
}

for (let row = 2; row <= 9; row += 1) {
    sales.formatCell(`C${row}`, {
        numberFormat: "$#,##0.00",
        horizontalAlignment: "right"
    });

    sales.formatCell(`D${row}`, {
        numberFormat: "$#,##0.00",
        horizontalAlignment: "right"
    });
}


// ============================================================================
// 13. EVALUATION
// ============================================================================

const evaluator = new FormulaEvaluator(sales);

for (const [address, cell] of sales.cells) {
    if (!cell.formula) {
        continue;
    }

    try {
        cell.value = evaluator.evaluateCell(address);
    } catch (error) {
        cell.value = error.message;
    }
}

sales.printGrid();

console.log(
    "\nD6 format:",
    sales.getCell("D6").format.describe()
);


// ============================================================================
// 14. CONDITIONAL FORMATTING
// ============================================================================

const lowRevenueFormat = new CellFormat();
lowRevenueFormat.fill = "warning";
lowRevenueFormat.fontColor = "red";
lowRevenueFormat.bold = true;

const lowRevenueRule = new ConditionalFormatRule(
    "<",
    500,
    lowRevenueFormat
);

for (const address of ["D2", "D3", "D4", "D5"]) {
    sales.addConditionalRule(address, lowRevenueRule);

    const value = sales.getCell(address).value;

    console.log(
        address,
        "value=",
        value,
        "conditional formatting applies=",
        lowRevenueRule.applies(value)
    );
}


// ============================================================================
// 15. FORMULA AUDITING
// ============================================================================

function auditFormulas(worksheet) {
    const problems = [];

    for (const [address, cell] of worksheet.cells) {
        if (!cell.formula) {
            continue;
        }

        if (!cell.formula.startsWith("=")) {
            problems.push(
                `${address}: formula does not begin with '='.`
            );
        }

        const openParentheses =
            (cell.formula.match(/\(/g) || []).length;

        const closeParentheses =
            (cell.formula.match(/\)/g) || []).length;

        if (openParentheses !== closeParentheses) {
            problems.push(
                `${address}: unbalanced parentheses.`
            );
        }
    }

    return problems;
}


console.log("\nFORMULA AUDIT");
console.log(auditFormulas(sales));


// ============================================================================
// 16. ERROR HANDLING
// ============================================================================

console.log("\nERROR HANDLING");

const errorSheet = workbook.addWorksheet("Errors");
const errorEvaluator = new FormulaEvaluator(errorSheet);

errorSheet.setFormula("A1", "=10/0");

try {
    console.log(errorEvaluator.evaluateCell("A1"));
} catch (error) {
    console.log(
        "Expected spreadsheet-style error:",
        error.message
    );
}


// ============================================================================
// 17. CIRCULAR REFERENCE
// ============================================================================

const circularSheet = workbook.addWorksheet("Circular");

circularSheet.setFormula("A1", "=B1+1");
circularSheet.setFormula("B1", "=A1+1");

const circularEvaluator =
    new FormulaEvaluator(circularSheet);

try {
    console.log(circularEvaluator.evaluateCell("A1"));
} catch (error) {
    console.log(
        "Circular reference detected:",
        error.message
    );
}


// ============================================================================
// 18. ASYNCHRONOUS SPREADSHEET-LIKE PROCESSING
// ============================================================================

function calculateAsync(value, delayMilliseconds = 10) {
    /*
     * Promise-based execution demonstrates an application-level pattern
     * useful when spreadsheet values come from a remote API or other
     * asynchronous data source.
     */
    return new Promise(resolve => {
        setTimeout(() => {
            resolve(value * value);
        }, delayMilliseconds);
    });
}


async function asynchronousExample() {
    const values = [2, 3, 4];

    const results = await Promise.all(
        values.map(value => calculateAsync(value))
    );

    console.log(
        "\nAsynchronous calculation:",
        values,
        "->",
        results
    );
}


// ============================================================================
// 19. TESTS
// ============================================================================

function runTests() {
    if (columnNumberToLetter(1) !== "A") {
        throw new Error("Column conversion test failed.");
    }

    if (columnNumberToLetter(27) !== "AA") {
        throw new Error("Column conversion test failed.");
    }

    if (columnLetterToNumber("AA") !== 27) {
        throw new Error("Column conversion test failed.");
    }

    if (normalizeAddress("a1") !== "A1") {
        throw new Error("Address normalization test failed.");
    }

    if (
        JSON.stringify(expandRange("A1:B2")) !==
        JSON.stringify(["A1", "B1", "A2", "B2"])
    ) {
        throw new Error("Range expansion test failed.");
    }

    if (
        shiftReference("A1", 2, 1) !== "B3"
    ) {
        throw new Error("Reference shifting test failed.");
    }

    if (
        shiftReference("$A$1", 2, 1) !== "$A$1"
    ) {
        throw new Error("Absolute reference test failed.");
    }

    const testSheet = new Worksheet("Tests");

    testSheet.setValue("A1", 10);
    testSheet.setValue("A2", 20);
    testSheet.setFormula("A3", "=SUM(A1:A2)");

    const testEvaluator =
        new FormulaEvaluator(testSheet);

    if (testEvaluator.evaluateCell("A3") !== 30) {
        throw new Error("SUM test failed.");
    }

    testSheet.setFormula("B1", "=A1*2");

    if (testEvaluator.evaluateCell("B1") !== 20) {
        throw new Error("Cell reference test failed.");
    }

    testSheet.setFormula(
        "B2",
        '=IF(A2>10,"yes","no")'
    );

    if (testEvaluator.evaluateCell("B2") !== "yes") {
        throw new Error("IF test failed.");
    }

    if (
        copyFormula("=A1*$C$1", 2, 1) !==
        "=B3*$C$1"
    ) {
        throw new Error("Formula copy test failed.");
    }

    console.log("\nAll JavaScript tests passed.");
}


runTests();


// ============================================================================
// 20. OUTPUT AND WORKBOOK STRUCTURE
// ============================================================================

console.log("\nWORKBOOK STRUCTURE");
console.log(workbook.listWorksheets());

console.log("\nSALES DEPENDENCY GRAPH");

const dependencies =
    buildDependencyGraph(sales);

for (const [address, references] of dependencies) {
    console.log(
        `${address} depends on ${references.join(", ")}`
    );
}


// ============================================================================
// 21. STUDY NOTES
// ============================================================================

console.log(`
STUDY NOTES

A worksheet is a grid of rows and columns.
A cell is identified by a column and row, such as B4.
A range contains multiple cells, such as B2:D10.
A formula begins with = and expresses a calculation.
A relative reference changes when copied.
An absolute reference remains fixed.
A mixed reference fixes either the row or the column.
Formatting changes presentation without necessarily changing the underlying
value.
Conditional formatting applies visual rules based on cell values.
A dependency graph describes which cells are required to calculate another
cell.

Important spreadsheet engineering principles:
- Keep inputs distinguishable from calculations.
- Use absolute references for fixed assumptions.
- Avoid hard-coded values when they represent changeable business assumptions.
- Validate imported values.
- Handle divide-by-zero and invalid data explicitly.
- Avoid circular references unless iterative calculation is intentional.
- Use formatting to communicate meaning, not conceal errors.
- Keep formulas understandable and auditable.
- Avoid JavaScript eval() when interpreting spreadsheet expressions.
`);

asynchronousExample().catch(error => {
    console.error("Asynchronous example failed:", error);
});
