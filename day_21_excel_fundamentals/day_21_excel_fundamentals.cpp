/*
 * Excel Fundamentals: Worksheets, Formulas, References and Formatting
 * ====================================================================
 *
 * Industry-style case study:
 *     A small financial sales workbook engine.
 *
 * The program demonstrates:
 *     - Workbook and worksheet architecture
 *     - Cells and ranges
 *     - Spreadsheet-style formulas
 *     - Relative, absolute, and mixed references
 *     - Formula evaluation
 *     - Dependency tracking
 *     - Formatting metadata
 *     - Conditional formatting
 *     - Validation
 *     - Error handling
 *     - Circular-reference detection
 *     - Aggregation
 *     - Reporting
 *     - Complexity and memory considerations
 *
 * Compile:
 *     g++ -std=c++17 -O2 -Wall -Wextra -pedantic excel_fundamentals.cpp -o excel_fundamentals
 *
 * Run:
 *     ./excel_fundamentals
 *
 * The implementation intentionally uses only the C++ standard library.
 */

#include <algorithm>
#include <cassert>
#include <cctype>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;


// ============================================================================
// 1. GENERAL UTILITIES
// ============================================================================

string trim(const string& text) {
    const auto first = text.find_first_not_of(" \t\r\n");

    if (first == string::npos) {
        return "";
    }

    const auto last = text.find_last_not_of(" \t\r\n");

    return text.substr(first, last - first + 1);
}


string toUpper(string text) {
    transform(
        text.begin(),
        text.end(),
        text.begin(),
        [](unsigned char character) {
            return static_cast<char>(toupper(character));
        }
    );

    return text;
}


bool isFinite(double value) {
    return std::isfinite(value);
}


// ============================================================================
// 2. COLUMN CONVERSION
// ============================================================================

string columnNumberToLetter(int columnNumber) {
    if (columnNumber < 1) {
        throw invalid_argument(
            "Column number must be at least 1."
        );
    }

    string result;
    int number = columnNumber;

    while (number > 0) {
        number -= 1;

        char character =
            static_cast<char>('A' + (number % 26));

        result.insert(result.begin(), character);

        number /= 26;
    }

    return result;
}


int columnLetterToNumber(const string& columnLetters) {
    string cleaned = toUpper(trim(columnLetters));

    if (cleaned.empty()) {
        throw invalid_argument("Column label cannot be empty.");
    }

    int result = 0;

    for (char character : cleaned) {
        if (character < 'A' || character > 'Z') {
            throw invalid_argument(
                "Column label contains an invalid character."
            );
        }

        result =
            result * 26 +
            (character - 'A' + 1);
    }

    return result;
}


// ============================================================================
// 3. CELL REFERENCES
// ============================================================================

struct CellReference {
    int column = 1;
    int row = 1;
    bool columnAbsolute = false;
    bool rowAbsolute = false;

    string address() const {
        string columnText =
            columnNumberToLetter(column);

        if (columnAbsolute) {
            columnText = "$" + columnText;
        }

        string rowText =
            rowAbsolute
                ? "$" + to_string(row)
                : to_string(row);

        return columnText + rowText;
    }

    CellReference shifted(
        int rowDelta,
        int columnDelta
    ) const {
        const int newRow =
            rowAbsolute ? row : row + rowDelta;

        const int newColumn =
            columnAbsolute
                ? column
                : column + columnDelta;

        if (newRow < 1 || newColumn < 1) {
            throw invalid_argument(
                "Shifted reference would leave worksheet."
            );
        }

        CellReference result = *this;

        result.row = newRow;
        result.column = newColumn;

        return result;
    }
};


CellReference parseCellReference(const string& input) {
    const string text = trim(input);

    static const regex pattern(
        R"(^(\$?)([A-Za-z]{1,3})(\$?)([1-9][0-9]*)$)"
    );

    smatch match;

    if (!regex_match(text, match, pattern)) {
        throw invalid_argument(
            "Invalid cell reference: " + input
        );
    }

    CellReference result;

    result.column =
        columnLetterToNumber(match[2].str());

    result.row =
        stoi(match[4].str());

    result.columnAbsolute =
        match[1].str() == "$";

    result.rowAbsolute =
        match[3].str() == "$";

    return result;
}


string normalizeAddress(const string& address) {
    CellReference reference =
        parseCellReference(address);

    reference.columnAbsolute = false;
    reference.rowAbsolute = false;

    return reference.address();
}


// ============================================================================
// 4. RANGE REPRESENTATION
// ============================================================================

vector<string> expandRange(const string& rangeText) {
    static const regex pattern(
        R"(^\$?([A-Za-z]{1,3})\$?([1-9][0-9]*):\$?([A-Za-z]{1,3})\$?([1-9][0-9]*)$)"
    );

    smatch match;

    if (!regex_match(
            trim(rangeText),
            match,
            pattern
        )) {
        throw invalid_argument(
            "Invalid range: " + rangeText
        );
    }

    int startColumn =
        columnLetterToNumber(match[1].str());

    int startRow =
        stoi(match[2].str());

    int endColumn =
        columnLetterToNumber(match[3].str());

    int endRow =
        stoi(match[4].str());

    if (startColumn > endColumn) {
        swap(startColumn, endColumn);
    }

    if (startRow > endRow) {
        swap(startRow, endRow);
    }

    vector<string> addresses;

    for (int row = startRow; row <= endRow; ++row) {
        for (
            int column = startColumn;
            column <= endColumn;
            ++column
        ) {
            addresses.push_back(
                columnNumberToLetter(column) +
                to_string(row)
            );
        }
    }

    return addresses;
}


// ============================================================================
// 5. SPREADSHEET ERRORS
// ============================================================================

class FormulaError : public runtime_error {
public:
    explicit FormulaError(const string& message)
        : runtime_error(message) {}
};


class CircularReferenceError : public FormulaError {
public:
    explicit CircularReferenceError(const string& message)
        : FormulaError(message) {}
};


// ============================================================================
// 6. FORMATTING MODEL
// ============================================================================

struct CellFormat {
    string numberFormat = "General";
    bool bold = false;
    bool italic = false;
    string horizontalAlignment = "general";
    string verticalAlignment = "bottom";
    string fill = "";
    string fontName = "Calibri";
    int fontSize = 11;
    string fontColor = "";
    string border = "";
    bool wrapText = false;
};


struct ConditionalFormatRule {
    string operation;
    double threshold = 0.0;
    CellFormat displayFormat;

    bool applies(double value) const {
        if (!isFinite(value)) {
            return false;
        }

        if (operation == ">") {
            return value > threshold;
        }

        if (operation == ">=") {
            return value >= threshold;
        }

        if (operation == "<") {
            return value < threshold;
        }

        if (operation == "<=") {
            return value <= threshold;
        }

        if (operation == "==") {
            return value == threshold;
        }

        if (operation == "!=") {
            return value != threshold;
        }

        throw invalid_argument(
            "Unsupported conditional operator."
        );
    }
};


// ============================================================================
// 7. CELL
// ============================================================================

class Cell {
public:
    optional<double> numericValue;
    optional<string> textValue;
    optional<bool> booleanValue;
    optional<string> formula;
    CellFormat format;

    bool isFormula() const {
        return formula.has_value();
    }

    void setValue(double value) {
        numericValue = value;
        textValue.reset();
        booleanValue.reset();
        formula.reset();
    }

    void setValue(const string& value) {
        textValue = value;
        numericValue.reset();
        booleanValue.reset();
        formula.reset();
    }

    void setValue(bool value) {
        booleanValue = value;
        numericValue.reset();
        textValue.reset();
        formula.reset();
    }

    void setFormula(const string& expression) {
        if (
            expression.empty() ||
            expression.front() != '='
        ) {
            throw invalid_argument(
                "Formula must begin with '='."
            );
        }

        formula = expression;

        numericValue.reset();
        textValue.reset();
        booleanValue.reset();
    }

    string displayValue() const {
        if (numericValue.has_value()) {
            ostringstream output;

            if (format.numberFormat == "$#,##0.00") {
                output << "$"
                       << fixed
                       << setprecision(2)
                       << *numericValue;
            }
            else if (format.numberFormat == "0.00%") {
                output << fixed
                       << setprecision(2)
                       << (*numericValue * 100.0)
                       << "%";
            }
            else if (format.numberFormat == "0.00") {
                output << fixed
                       << setprecision(2)
                       << *numericValue;
            }
            else {
                output << *numericValue;
            }

            return output.str();
        }

        if (textValue.has_value()) {
            return *textValue;
        }

        if (booleanValue.has_value()) {
            return *booleanValue ? "TRUE" : "FALSE";
        }

        return "";
    }
};


// ============================================================================
// 8. WORKSHEET
// ============================================================================

class Worksheet {
private:
    string name;

    map<string, Cell> cells;

    map<string, vector<ConditionalFormatRule>>
        conditionalRules;

public:
    explicit Worksheet(string worksheetName)
        : name(move(worksheetName)) {

        if (
            name.empty() ||
            name.size() > 31
        ) {
            throw invalid_argument(
                "Worksheet name must contain 1 to 31 characters."
            );
        }
    }

    const string& getName() const {
        return name;
    }

    void setValue(
        const string& address,
        double value
    ) {
        cells[normalizeAddress(address)]
            .setValue(value);
    }

    void setValue(
        const string& address,
        const string& value
    ) {
        cells[normalizeAddress(address)]
            .setValue(value);
    }

    void setValue(
        const string& address,
        bool value
    ) {
        cells[normalizeAddress(address)]
            .setValue(value);
    }

    void setFormula(
        const string& address,
        const string& formula
    ) {
        cells[normalizeAddress(address)]
            .setFormula(formula);
    }

    Cell& getCell(const string& address) {
        return cells[normalizeAddress(address)];
    }

    const Cell& getCell(const string& address) const {
        auto iterator =
            cells.find(normalizeAddress(address));

        if (iterator == cells.end()) {
            static const Cell emptyCell;
            return emptyCell;
        }

        return iterator->second;
    }

    void formatCell(
        const string& address,
        const CellFormat& format
    ) {
        getCell(address).format = format;
    }

    void addConditionalRule(
        const string& address,
        const ConditionalFormatRule& rule
    ) {
        conditionalRules[
            normalizeAddress(address)
        ].push_back(rule);
    }

    const map<string, Cell>& getCells() const {
        return cells;
    }

    void printGrid() const {
        if (cells.empty()) {
            cout << "(empty worksheet)\n";
            return;
        }

        int minimumRow =
            numeric_limits<int>::max();

        int maximumRow = 1;

        int minimumColumn =
            numeric_limits<int>::max();

        int maximumColumn = 1;

        for (const auto& [address, cell] : cells) {
            CellReference reference =
                parseCellReference(address);

            minimumRow =
                min(minimumRow, reference.row);

            maximumRow =
                max(maximumRow, reference.row);

            minimumColumn =
                min(minimumColumn, reference.column);

            maximumColumn =
                max(maximumColumn, reference.column);
        }

        cout << "\n      ";

        for (
            int column = minimumColumn;
            column <= maximumColumn;
            ++column
        ) {
            cout
                << setw(18)
                << columnNumberToLetter(column);
        }

        cout << '\n';

        for (
            int row = minimumRow;
            row <= maximumRow;
            ++row
        ) {
            cout
                << setw(5)
                << row
                << " ";

            for (
                int column = minimumColumn;
                column <= maximumColumn;
                ++column
            ) {
                const string address =
                    columnNumberToLetter(column) +
                    to_string(row);

                cout
                    << setw(18)
                    << getCell(address).displayValue();
            }

            cout << '\n';
        }
    }
};


// ============================================================================
// 9. WORKBOOK
// ============================================================================

class Workbook {
private:
    map<string, Worksheet> worksheets;

public:
    Worksheet& addWorksheet(const string& name) {
        if (worksheets.contains(name)) {
            throw invalid_argument(
                "Worksheet already exists: " + name
            );
        }

        auto [iterator, inserted] =
            worksheets.emplace(
                piecewise_construct,
                forward_as_tuple(name),
                forward_as_tuple(name)
            );

        return iterator->second;
    }

    Worksheet& getWorksheet(const string& name) {
        auto iterator = worksheets.find(name);

        if (iterator == worksheets.end()) {
            throw out_of_range(
                "Worksheet not found: " + name
            );
        }

        return iterator->second;
    }

    vector<string> listWorksheets() const {
        vector<string> names;

        for (const auto& [name, worksheet] : worksheets) {
            names.push_back(name);
        }

        return names;
    }
};


// ============================================================================
// 10. FORMULA PARSER
// ============================================================================

class FormulaEvaluator {
private:
    Worksheet& worksheet;

    vector<string> evaluationStack;

    static bool isNumeric(const string& text) {
        if (text.empty()) {
            return false;
        }

        char* endPointer = nullptr;

        const double value =
            strtod(text.c_str(), &endPointer);

        return endPointer != text.c_str() &&
               *endPointer == '\0' &&
               isFinite(value);
    }

    static double toNumber(
        const string& text
    ) {
        if (!isNumeric(text)) {
            throw FormulaError(
                "#VALUE! Cannot convert value to number."
            );
        }

        return stod(text);
    }

    static vector<string> splitArguments(
        const string& text
    ) {
        vector<string> result;

        int depth = 0;
        bool insideString = false;

        size_t start = 0;

        for (
            size_t index = 0;
            index < text.size();
            ++index
        ) {
            const char character = text[index];

            if (character == '"') {
                insideString = !insideString;
            }

            if (insideString) {
                continue;
            }

            if (character == '(') {
                ++depth;
            }
            else if (character == ')') {
                --depth;
            }
            else if (
                character == ',' &&
                depth == 0
            ) {
                result.push_back(
                    trim(
                        text.substr(
                            start,
                            index - start
                        )
                    )
                );

                start = index + 1;
            }
        }

        result.push_back(
            trim(text.substr(start))
        );

        return result;
    }

    static size_t findTopLevelOperator(
        const string& expression,
        const vector<string>& operators
    ) {
        int depth = 0;
        bool insideString = false;

        if (expression.empty()) {
            return string::npos;
        }

        for (
            size_t reverseIndex = expression.size();
            reverseIndex > 0;
            --reverseIndex
        ) {
            const size_t index =
                reverseIndex - 1;

            const char character =
                expression[index];

            if (character == '"') {
                insideString = !insideString;
                continue;
            }

            if (insideString) {
                continue;
            }

            if (character == ')') {
                ++depth;
                continue;
            }

            if (character == '(') {
                --depth;
                continue;
            }

            if (depth != 0) {
                continue;
            }

            for (const string& operation : operators) {
                if (
                    index + 1 >= operation.size() &&
                    expression.substr(
                        index + 1 - operation.size(),
                        operation.size()
                    ) == operation
                ) {
                    const size_t position =
                        index + 1 - operation.size();

                    if (
                        operation == "-" &&
                        position == 0
                    ) {
                        continue;
                    }

                    return position;
                }
            }
        }

        return string::npos;
    }

    static string operatorAt(
        const string& expression,
        size_t position,
        const vector<string>& operators
    ) {
        for (const string& operation : operators) {
            if (
                expression.compare(
                    position,
                    operation.size(),
                    operation
                ) == 0
            ) {
                return operation;
            }
        }

        return "";
    }

    double evaluateArgument(
        const string& argument
    ) {
        const string cleaned =
            trim(argument);

        if (
            cleaned.find(':') != string::npos
        ) {
            const vector<string> addresses =
                expandRange(cleaned);

            /*
             * A range is not itself a scalar. It is converted into an
             * aggregate collection and consumed by functions such as SUM.
             */
            double sum = 0.0;

            for (const string& address : addresses) {
                const string value =
                    evaluateCell(address);

                if (isNumeric(value)) {
                    sum += stod(value);
                }
            }

            /*
             * The evaluator's public representation is intentionally simple.
             * Range aggregation is therefore handled in callFunction.
             */
            return sum;
        }

        return evaluateExpression(cleaned);
    }

    double evaluateExpression(
        const string& expression
    ) {
        const string cleaned =
            trim(expression);

        if (cleaned.empty()) {
            throw FormulaError(
                "#VALUE! Empty expression."
            );
        }

        /*
         * String literals are treated as text. The full Excel language has
         * many more text operations; this case study focuses on numeric and
         * logical calculations.
         */
        if (
            cleaned.front() == '"' &&
            cleaned.back() == '"' &&
            cleaned.size() >= 2
        ) {
            throw FormulaError(
                "Text literals must be used through IF in this case study."
            );
        }

        /*
         * Function calls.
         *
         * Example:
         *     SUM(B2:B5)
         *     ROUND(B2, 2)
         */
        const regex functionPattern(
            R"(^([A-Za-z_][A-Za-z0-9_]*)\((.*)\)$)"
        );

        smatch functionMatch;

        if (
            regex_match(
                cleaned,
                functionMatch,
                functionPattern
            )
        ) {
            const string functionName =
                toUpper(functionMatch[1].str());

            const vector<string> arguments =
                splitArguments(
                    functionMatch[2].str()
                );

            return callFunction(
                functionName,
                arguments
            );
        }

        /*
         * Comparisons have lower precedence than arithmetic.
         */
        const vector<string> comparisonOperators = {
            "<>",
            ">=",
            "<=",
            "=",
            ">",
            "<"
        };

        const size_t comparisonPosition =
            findTopLevelOperator(
                cleaned,
                comparisonOperators
            );

        if (
            comparisonPosition != string::npos
        ) {
            const string operation =
                operatorAt(
                    cleaned,
                    comparisonPosition,
                    comparisonOperators
                );

            const string leftText =
                cleaned.substr(
                    0,
                    comparisonPosition
                );

            const string rightText =
                cleaned.substr(
                    comparisonPosition +
                    operation.size()
                );

            const double left =
                evaluateExpression(leftText);

            const double right =
                evaluateExpression(rightText);

            bool result = false;

            if (operation == "=") {
                result = left == right;
            }
            else if (operation == "<>") {
                result = left != right;
            }
            else if (operation == ">") {
                result = left > right;
            }
            else if (operation == "<") {
                result = left < right;
            }
            else if (operation == ">=") {
                result = left >= right;
            }
            else if (operation == "<=") {
                result = left <= right;
            }

            return result ? 1.0 : 0.0;
        }

        const vector<string> additiveOperators = {
            "+",
            "-"
        };

        const size_t additivePosition =
            findTopLevelOperator(
                cleaned,
                additiveOperators
            );

        if (
            additivePosition != string::npos
        ) {
            const string operation =
                operatorAt(
                    cleaned,
                    additivePosition,
                    additiveOperators
                );

            const double left =
                evaluateExpression(
                    cleaned.substr(
                        0,
                        additivePosition
                    )
                );

            const double right =
                evaluateExpression(
                    cleaned.substr(
                        additivePosition +
                        operation.size()
                    )
                );

            return operation == "+"
                ? left + right
                : left - right;
        }

        const vector<string> multiplicativeOperators = {
            "*",
            "/"
        };

        const size_t multiplicativePosition =
            findTopLevelOperator(
                cleaned,
                multiplicativeOperators
            );

        if (
            multiplicativePosition != string::npos
        ) {
            const string operation =
                operatorAt(
                    cleaned,
                    multiplicativePosition,
                    multiplicativeOperators
                );

            const double left =
                evaluateExpression(
                    cleaned.substr(
                        0,
                        multiplicativePosition
                    )
                );

            const double right =
                evaluateExpression(
                    cleaned.substr(
                        multiplicativePosition +
                        operation.size()
                    )
                );

            if (
                operation == "/" &&
                right == 0.0
            ) {
                throw FormulaError("#DIV/0!");
            }

            return operation == "*"
                ? left * right
                : left / right;
        }

        const size_t exponentPosition =
            findTopLevelOperator(
                cleaned,
                {"^"}
            );

        if (
            exponentPosition != string::npos
        ) {
            const double left =
                evaluateExpression(
                    cleaned.substr(
                        0,
                        exponentPosition
                    )
                );

            const double right =
                evaluateExpression(
                    cleaned.substr(
                        exponentPosition + 1
                    )
                );

            return pow(left, right);
        }

        if (
            cleaned.front() == '(' &&
            cleaned.back() == ')'
        ) {
            return evaluateExpression(
                cleaned.substr(
                    1,
                    cleaned.size() - 2
                )
            );
        }

        if (isNumeric(cleaned)) {
            return stod(cleaned);
        }

        /*
         * Cell references are resolved recursively. The stack detects
         * circular references such as A1 -> B1 -> A1.
         */
        static const regex cellPattern(
            R"(^\$?[A-Za-z]{1,3}\$?[1-9][0-9]*$)"
        );

        if (
            regex_match(
                cleaned,
                cellPattern
            )
        ) {
            const string value =
                evaluateCell(cleaned);

            return toNumber(value);
        }

        throw FormulaError(
            "#VALUE! Unsupported expression: " +
            cleaned
        );
    }

    string callFunction(
        const string& name,
        const vector<string>& arguments
    ) {
        if (name == "SUM") {
            double total = 0.0;

            for (const string& argument : arguments) {
                const string cleaned =
                    trim(argument);

                if (
                    cleaned.find(':') !=
                    string::npos
                ) {
                    for (
                        const string& address :
                        expandRange(cleaned)
                    ) {
                        const string value =
                            evaluateCell(address);

                        if (isNumeric(value)) {
                            total += stod(value);
                        }
                    }
                }
                else {
                    total +=
                        evaluateArgument(cleaned);
                }
            }

            return to_string(total);
        }

        if (name == "AVERAGE") {
            double total = 0.0;
            int count = 0;

            for (const string& argument : arguments) {
                const string cleaned =
                    trim(argument);

                if (
                    cleaned.find(':') !=
                    string::npos
                ) {
                    for (
                        const string& address :
                        expandRange(cleaned)
                    ) {
                        const string value =
                            evaluateCell(address);

                        if (isNumeric(value)) {
                            total += stod(value);
                            ++count;
                        }
                    }
                }
                else {
                    total +=
                        evaluateArgument(cleaned);

                    ++count;
                }
            }

            if (count == 0) {
                throw FormulaError("#DIV/0!");
            }

            return to_string(
                total / count
            );
        }

        if (
            name == "MIN" ||
            name == "MAX"
        ) {
            vector<double> values;

            for (const string& argument : arguments) {
                const string cleaned =
                    trim(argument);

                if (
                    cleaned.find(':') !=
                    string::npos
                ) {
                    for (
                        const string& address :
                        expandRange(cleaned)
                    ) {
                        const string value =
                            evaluateCell(address);

                        if (isNumeric(value)) {
                            values.push_back(
                                stod(value)
                            );
                        }
                    }
                }
                else {
                    values.push_back(
                        evaluateArgument(cleaned)
                    );
                }
            }

            if (values.empty()) {
                throw FormulaError("#VALUE!");
            }

            const double result =
                name == "MIN"
                    ? *min_element(
                        values.begin(),
                        values.end()
                    )
                    : *max_element(
                        values.begin(),
                        values.end()
                    );

            return to_string(result);
        }

        if (name == "ROUND") {
            if (
                arguments.empty() ||
                arguments.size() > 2
            ) {
                throw FormulaError(
                    "ROUND expects one or two arguments."
                );
            }

            const double number =
                evaluateArgument(arguments[0]);

            int digits = 0;

            if (arguments.size() == 2) {
                digits =
                    static_cast<int>(
                        evaluateArgument(arguments[1])
                    );
            }

            const double factor =
                pow(10.0, digits);

            return to_string(
                round(number * factor) / factor
            );
        }

        if (name == "IF") {
            if (arguments.size() != 3) {
                throw FormulaError(
                    "IF expects three arguments."
                );
            }

            /*
             * The case study returns numeric 1/0 because its central
             * calculation engine is numeric. A production spreadsheet engine
             * would use a richer variant type supporting text, numbers,
             * dates, errors, and arrays.
             */
            const double condition =
                evaluateExpression(arguments[0]);

            if (condition != 0.0) {
                const string trueValue =
                    trim(arguments[1]);

                if (
                    trueValue.size() >= 2 &&
                    trueValue.front() == '"' &&
                    trueValue.back() == '"'
                ) {
                    /*
                     * Text results are stored as a numeric sentinel only for
                     * this compact evaluator. The worksheet itself supports
                     * text values separately.
                     */
                    return "1";
                }

                return to_string(
                    evaluateArgument(trueValue)
                );
            }

            const string falseValue =
                trim(arguments[2]);

            if (
                falseValue.size() >= 2 &&
                falseValue.front() == '"' &&
                falseValue.back() == '"'
            ) {
                return "0";
            }

            return to_string(
                evaluateArgument(falseValue)
            );
        }

        throw FormulaError(
            "Unknown function: " + name
        );
    }

public:
    explicit FormulaEvaluator(
        Worksheet& worksheetReference
    )
        : worksheet(worksheetReference) {}

    string evaluateCell(
        const string& address
    ) {
        const string normalized =
            normalizeAddress(address);

        if (
            find(
                evaluationStack.begin(),
                evaluationStack.end(),
                normalized
            ) != evaluationStack.end()
        ) {
            ostringstream cycle;

            cycle
                << "Circular reference detected: ";

            for (
                const string& item :
                evaluationStack
            ) {
                cycle << item << " -> ";
            }

            cycle << normalized;

            throw CircularReferenceError(
                cycle.str()
            );
        }

        Cell& cell =
            worksheet.getCell(normalized);

        if (!cell.isFormula()) {
            if (cell.numericValue.has_value()) {
                return to_string(
                    *cell.numericValue
                );
            }

            if (cell.booleanValue.has_value()) {
                return *cell.booleanValue
                    ? "1"
                    : "0";
            }

            if (cell.textValue.has_value()) {
                /*
                 * Text cannot participate directly in this numeric evaluator.
                 */
                return *cell.textValue;
            }

            return "";
        }

        evaluationStack.push_back(normalized);

        try {
            const string expression =
                cell.formula->substr(1);

            const double result =
                evaluateExpression(expression);

            evaluationStack.pop_back();

            return to_string(result);
        }
        catch (...) {
            evaluationStack.pop_back();
            throw;
        }
    }
};


// ============================================================================
// 11. FORMULA COPYING
// ============================================================================

string copyFormula(
    const string& formula,
    int rowDelta,
    int columnDelta
) {
    static const regex referencePattern(
        R"(\$?[A-Za-z]{1,3}\$?[1-9][0-9]*)"
    );

    string result;
    size_t lastPosition = 0;

    auto begin =
        sregex_iterator(
            formula.begin(),
            formula.end(),
            referencePattern
        );

    auto end =
        sregex_iterator();

    for (
        auto iterator = begin;
        iterator != end;
        ++iterator
    ) {
        const smatch& match = *iterator;

        result += formula.substr(
            lastPosition,
            match.position() - lastPosition
        );

        const CellReference reference =
            parseCellReference(match.str());

        result +=
            reference
                .shifted(
                    rowDelta,
                    columnDelta
                )
                .address();

        lastPosition =
            match.position() +
            match.length();
    }

    result += formula.substr(lastPosition);

    return result;
}


// ============================================================================
// 12. DEPENDENCY GRAPH
// ============================================================================

vector<string> extractReferences(
    const string& formula
) {
    static const regex referencePattern(
        R"(\$?[A-Za-z]{1,3}\$?[1-9][0-9]*)"
    );

    vector<string> references;

    auto begin =
        sregex_iterator(
            formula.begin(),
            formula.end(),
            referencePattern
        );

    auto end =
        sregex_iterator();

    for (
        auto iterator = begin;
        iterator != end;
        ++iterator
    ) {
        references.push_back(
            normalizeAddress(iterator->str())
        );
    }

    return references;
}


map<string, vector<string>>
buildDependencyGraph(
    const Worksheet& worksheet
) {
    map<string, vector<string>> graph;

    for (
        const auto& [address, cell] :
        worksheet.getCells()
    ) {
        if (cell.formula.has_value()) {
            graph[address] =
                extractReferences(
                    *cell.formula
                );
        }
    }

    return graph;
}


// ============================================================================
// 13. FORMATTING HELPERS
// ============================================================================

CellFormat headerFormat() {
    CellFormat format;

    format.bold = true;
    format.horizontalAlignment = "center";
    format.fill = "header";
    format.border = "bottom";

    return format;
}


CellFormat currencyFormat() {
    CellFormat format;

    format.numberFormat = "$#,##0.00";
    format.horizontalAlignment = "right";

    return format;
}


CellFormat percentageFormat() {
    CellFormat format;

    format.numberFormat = "0.00%";
    format.horizontalAlignment = "right";

    return format;
}


// ============================================================================
// 14. BUSINESS VALIDATION
// ============================================================================

double validatePositive(
    double value,
    const string& fieldName
) {
    if (!isFinite(value)) {
        throw invalid_argument(
            fieldName +
            " must be finite."
        );
    }

    if (value < 0.0) {
        throw invalid_argument(
            fieldName +
            " cannot be negative."
        );
    }

    return value;
}


// ============================================================================
// 15. INDUSTRY-STYLE SALES CASE STUDY
// ============================================================================

struct ProductRecord {
    string name;
    double units;
    double unitPrice;
};


void populateSalesModel(
    Worksheet& sales
) {
    sales.setValue("A1", "Product");
    sales.setValue("B1", "Units");
    sales.setValue("C1", "Unit Price");
    sales.setValue("D1", "Revenue");
    sales.setValue("E1", "Target");

    const vector<ProductRecord> products = {
        {"Laptop", 5, 850.0},
        {"Monitor", 8, 250.0},
        {"Keyboard", 15, 45.0},
        {"Mouse", 25, 20.0},
        {"Printer", 4, 275.0}
    };

    for (
        size_t index = 0;
        index < products.size();
        ++index
    ) {
        const int row =
            static_cast<int>(index) + 2;

        const ProductRecord& product =
            products[index];

        validatePositive(
            product.units,
            "Units"
        );

        validatePositive(
            product.unitPrice,
            "Unit price"
        );

        sales.setValue(
            "A" + to_string(row),
            product.name
        );

        sales.setValue(
            "B" + to_string(row),
            product.units
        );

        sales.setValue(
            "C" + to_string(row),
            product.unitPrice
        );

        /*
         * Relative references are intentional:
         * when this formula is copied downward, B2*C2 becomes B3*C3, etc.
         */
        sales.setFormula(
            "D" + to_string(row),
            "=B" + to_string(row) +
            "*C" + to_string(row)
        );

        sales.setValue(
            "E" + to_string(row),
            1000.0
        );
    }

    sales.setValue("A7", "Total Revenue");
    sales.setFormula("D7", "=SUM(D2:D6)");

    sales.setValue("A8", "Average Revenue");
    sales.setFormula("D8", "=AVERAGE(D2:D6)");

    sales.setValue("A9", "Maximum Revenue");
    sales.setFormula("D9", "=MAX(D2:D6)");

    sales.setValue("A10", "Minimum Revenue");
    sales.setFormula("D10", "=MIN(D2:D6)");

    /*
     * This fixed target demonstrates an absolute-reference concept.
     *
     * In an Excel workbook, a design might put the target in a separate
     * assumptions cell such as $G$1 and use =D2/$G$1.
     */
    sales.setValue("G1", "Target");
    sales.setValue("H1", 1000.0);

    for (int row = 2; row <= 6; ++row) {
        sales.setFormula(
            "F" + to_string(row),
            "=D" + to_string(row) +
            "/$H$1"
        );
    }
}


// ============================================================================
// 16. EVALUATE MODEL
// ============================================================================

void evaluateFormulas(
    Worksheet& worksheet
) {
    FormulaEvaluator evaluator(worksheet);

    for (
        const auto& [address, cell] :
        worksheet.getCells()
    ) {
        if (!cell.formula.has_value()) {
            continue;
        }

        try {
            const string result =
                evaluator.evaluateCell(address);

            if (
                result.empty() ||
                !isFinite(stod(result))
            ) {
                continue;
            }

            worksheet.getCell(address)
                .setValue(stod(result));
        }
        catch (const FormulaError& error) {
            cout
                << "Formula error in "
                << address
                << ": "
                << error.what()
                << '\n';
        }
    }
}


// ============================================================================
// 17. REPORT FORMATTING
// ============================================================================

void formatSalesModel(
    Worksheet& sales
) {
    const CellFormat header =
        headerFormat();

    for (
        const string& address :
        {"A1", "B1", "C1", "D1", "E1", "G1"}
    ) {
        sales.formatCell(
            address,
            header
        );
    }

    const CellFormat currency =
        currencyFormat();

    for (int row = 2; row <= 10; ++row) {
        sales.formatCell(
            "C" + to_string(row),
            currency
        );

        sales.formatCell(
            "D" + to_string(row),
            currency
        );

        sales.formatCell(
            "E" + to_string(row),
            currency
        );

        sales.formatCell(
            "H" + to_string(row),
            currency
        );
    }

    const CellFormat percentage =
        percentageFormat();

    for (int row = 2; row <= 6; ++row) {
        sales.formatCell(
            "F" + to_string(row),
            percentage
        );
    }
}


// ============================================================================
// 18. CONDITIONAL FORMATTING
// ============================================================================

void demonstrateConditionalFormatting(
    Worksheet& sales
) {
    CellFormat warningFormat;

    warningFormat.bold = true;
    warningFormat.fill = "warning";
    warningFormat.fontColor = "red";

    ConditionalFormatRule rule;

    rule.operation = "<";
    rule.threshold = 500.0;
    rule.displayFormat = warningFormat;

    cout
        << "\nCONDITIONAL FORMATTING\n";

    for (int row = 2; row <= 6; ++row) {
        const string address =
            "D" + to_string(row);

        const Cell& cell =
            sales.getCell(address);

        if (!cell.numericValue.has_value()) {
            continue;
        }

        cout
            << address
            << " = "
            << *cell.numericValue
            << ", rule applies = "
            << boolalpha
            << rule.applies(
                *cell.numericValue
            )
            << '\n';
    }
}


// ============================================================================
// 19. DEPENDENCY AUDIT
// ============================================================================

void printDependencyGraph(
    const Worksheet& worksheet
) {
    cout
        << "\nDEPENDENCY GRAPH\n";

    const auto graph =
        buildDependencyGraph(worksheet);

    for (
        const auto& [address, references] :
        graph
    ) {
        cout
            << address
            << " depends on: ";

        for (size_t index = 0;
             index < references.size();
             ++index) {

            if (index > 0) {
                cout << ", ";
            }

            cout << references[index];
        }

        cout << '\n';
    }
}


// ============================================================================
// 20. REFERENCE DEMONSTRATION
// ============================================================================

void demonstrateReferences() {
    cout
        << "\nREFERENCE TYPES\n";

    const vector<string> references = {
        "A1",
        "$A$1",
        "A$1",
        "$A1"
    };

    for (
        const string& text :
        references
    ) {
        CellReference reference =
            parseCellReference(text);

        cout
            << setw(6)
            << text
            << " -> copied by "
            << "2 rows and 3 columns -> "
            << reference
                .shifted(2, 3)
                .address()
            << '\n';
    }

    cout
        << "\nFORMULA COPYING\n";

    const string formula =
        "=B2*$H$1";

    for (int rowDelta = 0;
         rowDelta < 4;
         ++rowDelta) {

        cout
            << formula
            << " copied down "
            << rowDelta
            << " rows -> "
            << copyFormula(
                formula,
                rowDelta,
                0
            )
            << '\n';
    }
}


// ============================================================================
// 21. ERROR TESTING
// ============================================================================

void demonstrateErrors() {
    cout
        << "\nERROR HANDLING\n";

    Workbook workbook;

    Worksheet& worksheet =
        workbook.addWorksheet("Errors");

    worksheet.setFormula(
        "A1",
        "=10/0"
    );

    FormulaEvaluator evaluator(
        worksheet
    );

    try {
        evaluator.evaluateCell("A1");
    }
    catch (const FormulaError& error) {
        cout
            << "Expected error: "
            << error.what()
            << '\n';
    }
}


// ============================================================================
// 22. CIRCULAR REFERENCE TEST
// ============================================================================

void demonstrateCircularReference() {
    cout
        << "\nCIRCULAR REFERENCE\n";

    Workbook workbook;

    Worksheet& worksheet =
        workbook.addWorksheet("Circular");

    worksheet.setFormula(
        "A1",
        "=B1+1"
    );

    worksheet.setFormula(
        "B1",
        "=A1+1"
    );

    FormulaEvaluator evaluator(
        worksheet
    );

    try {
        evaluator.evaluateCell("A1");
    }
    catch (
        const CircularReferenceError& error
    ) {
        cout
            << error.what()
            << '\n';
    }
}


// ============================================================================
// 23. TEST SUITE
// ============================================================================

void runTests() {
    assert(
        columnNumberToLetter(1) == "A"
    );

    assert(
        columnNumberToLetter(26) == "Z"
    );

    assert(
        columnNumberToLetter(27) == "AA"
    );

    assert(
        columnLetterToNumber("A") == 1
    );

    assert(
        columnLetterToNumber("AA") == 27
    );

    assert(
        normalizeAddress("a1") == "A1"
    );

    const vector<string> range =
        expandRange("A1:B2");

    assert(
        range.size() == 4
    );

    assert(
        range[0] == "A1"
    );

    assert(
        range[3] == "B2"
    );

    assert(
        parseCellReference(
            "$A$1"
        ).shifted(4, 4).address()
        == "$A$1"
    );

    assert(
        copyFormula(
            "=A1*$C$1",
            2,
            1
        )
        == "=B3*$C$1"
    );

    Workbook workbook;

    Worksheet& worksheet =
        workbook.addWorksheet("Tests");

    worksheet.setValue("A1", 10.0);
    worksheet.setValue("A2", 20.0);

    worksheet.setFormula(
        "A3",
        "=SUM(A1:A2)"
    );

    FormulaEvaluator evaluator(
        worksheet
    );

    const double result =
        stod(
            evaluator.evaluateCell("A3")
        );

    assert(
        abs(result - 30.0) < 1e-9
    );

    worksheet.setFormula(
        "B1",
        "=A1*2"
    );

    assert(
        abs(
            stod(
                evaluator.evaluateCell("B1")
            ) - 20.0
        ) < 1e-9
    );

    cout
        << "\nAll C++ tests passed.\n";
}


// ============================================================================
// 24. ARCHITECTURAL NOTES
// ============================================================================

void printArchitectureNotes() {
    cout
        << R"(
ARCHITECTURE AND PERFORMANCE NOTES

Workbook
    Owns worksheets and provides the document-level container.

Worksheet
    Owns cells, formatting metadata, and conditional rules.

Cell
    Stores a value, formula, and presentation metadata.

CellReference
    Separates coordinate semantics from the worksheet implementation.

FormulaEvaluator
    Resolves references recursively and evaluates a restricted formula
    language.

Dependency graph
    Provides a basis for formula auditing and recalculation ordering.

Complexity
    Direct cell lookup in std::map is O(log n).
    A production spreadsheet engine often uses hash maps or specialized
    structures for very large sparse worksheets.
    Expanding an r-by-c range is O(r*c).
    Evaluating a formula chain can be proportional to the number of
    dependencies visited.

Memory
    Sparse storage is appropriate when most worksheet cells are empty.
    A dense matrix can be faster for heavily populated rectangular data but
    consumes more memory when large empty regions exist.

Production considerations
    A complete spreadsheet engine requires a much larger grammar, richer
    value types, dates, errors, text operations, lookup functions, arrays,
    named ranges, cross-sheet references, workbook links, recalculation
    scheduling, dependency invalidation, formatting inheritance, charts,
    data validation, persistence, and compatibility rules.

Security
    Formula input should never be passed to an unrestricted programming
    language evaluator.
    Macros, external links, imported content, and embedded objects require
    separate trust and security controls.
    Hidden cells and worksheet protection should not be treated as
    encryption or as a secure location for secrets.
)";
}


// ============================================================================
// 25. MAIN
// ============================================================================

int main() {
    cout
        << string(
            78,
            '='
        )
        << '\n';

    cout
        << "EXCEL FUNDAMENTALS: WORKSHEETS, FORMULAS, "
        << "REFERENCES AND FORMATTING\n";

    cout
        << string(
            78,
            '='
        )
        << '\n';

    cout
        << "\nBASIC TERMINOLOGY\n"
        << "Workbook: a file containing worksheets.\n"
        << "Worksheet: a grid of rows and columns.\n"
        << "Cell: the intersection of a row and column.\n"
        << "Range: a rectangular group of cells.\n"
        << "Formula: an expression beginning with '='.\n"
        << "Reference: a cell or range used by a formula.\n"
        << "Formatting: presentation applied to a cell.\n";

    demonstrateReferences();

    Workbook workbook;

    Worksheet& sales =
        workbook.addWorksheet("Sales");

    populateSalesModel(sales);

    formatSalesModel(sales);

    cout
        << "\nSALES MODEL BEFORE FORMULA EVALUATION\n";

    sales.printGrid();

    cout
        << "\nEVALUATING FORMULAS\n";

    evaluateFormulas(sales);

    sales.printGrid();

    demonstrateConditionalFormatting(sales);

    printDependencyGraph(sales);

    demonstrateErrors();

    demonstrateCircularReference();

    runTests();

    printArchitectureNotes();

    cout
        << "\nWORKBOOK SHEETS\n";

    for (
        const string& name :
        workbook.listWorksheets()
    ) {
        cout
            << "- "
            << name
            << '\n';
    }

    cout
        << R"(
CASE STUDY FLOW

Raw sales inputs
       |
       v
Cell references
       |
       v
Revenue formulas
       |
       v
Aggregate formulas
       |
       v
Formatting and conditional rules
       |
       v
Business report

The same fundamental spreadsheet ideas apply to budgets, payroll,
inventory, forecasting, financial models, project schedules, operational
reports, and many other tabular business systems.
)";

    cout
        << "\nProgram completed successfully.\n";

    return 0;
}
