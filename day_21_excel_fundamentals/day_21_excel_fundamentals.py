"""
Excel Fundamentals: Worksheets, Formulas, References and Formatting
====================================================================

A self-contained study program that models the core ideas behind spreadsheet
workbooks and Excel-style worksheets without requiring an external package.

The program teaches:
    - Workbook and worksheet concepts
    - Rows, columns, cells, ranges, and coordinates
    - Values, labels, formulas, and data types
    - Formula parsing and evaluation
    - Arithmetic and comparison operators
    - Cell references
    - Relative, absolute, and mixed references
    - Range references
    - Common spreadsheet functions
    - Formula dependencies
    - Error handling
    - Formatting concepts
    - Number formats
    - Alignment and styling
    - Conditional formatting concepts
    - Validation concepts
    - Copying formulas
    - Practical financial and business examples
    - Edge cases and common mistakes
    - Dependency inspection
    - CSV-like output
    - A small spreadsheet engine implemented in Python

The implementation intentionally uses only the Python standard library.
It is an educational model of spreadsheet behavior, not a replacement for
Microsoft Excel or another full spreadsheet application.
"""

from __future__ import annotations

import ast
import copy
import math
import operator
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple


# ============================================================================
# SECTION 1: BASIC SPREADSHEET TERMINOLOGY
# ============================================================================

print("=" * 78)
print("EXCEL FUNDAMENTALS: WORKSHEETS, FORMULAS, REFERENCES AND FORMATTING")
print("=" * 78)

print(
    """
A spreadsheet is organized primarily around these concepts:

Workbook
    A file containing one or more worksheets.

Worksheet
    A grid made from rows and columns.

Column
    A vertical sequence identified by letters such as A, B, C, ..., Z, AA.

Row
    A horizontal sequence identified by numbers such as 1, 2, 3, ...

Cell
    The intersection of one column and one row. Example: B4.

Range
    A rectangular collection of cells. Example: A1:C5.

Value
    Data stored in a cell, such as 125, 3.14, or a date.

Label
    Text used to describe data, such as "Revenue".

Formula
    An expression beginning with = that calculates a result.

Reference
    A cell or range used by a formula, such as A1 or B2:B10.

Formatting
    The visual and presentation rules applied to cells, such as number
    format, alignment, font emphasis, or fill.
"""
)


# ============================================================================
# SECTION 2: COLUMN LETTER / NUMBER CONVERSION
# ============================================================================

def column_number_to_letter(column_number: int) -> str:
    """Convert 1 -> A, 26 -> Z, 27 -> AA, etc."""
    if column_number < 1:
        raise ValueError("Column number must be at least 1.")

    letters: List[str] = []
    number = column_number

    while number:
        number, remainder = divmod(number - 1, 26)
        letters.append(chr(ord("A") + remainder))

    return "".join(reversed(letters))


def column_letter_to_number(column_letters: str) -> int:
    """Convert A -> 1, Z -> 26, AA -> 27, etc."""
    cleaned = column_letters.strip().upper()

    if not cleaned or not cleaned.isalpha():
        raise ValueError(f"Invalid column label: {column_letters!r}")

    result = 0

    for character in cleaned:
        if not "A" <= character <= "Z":
            raise ValueError(f"Invalid column label: {column_letters!r}")
        result = result * 26 + (ord(character) - ord("A") + 1)

    return result


print("\nCOLUMN CONVERSION")
for number in [1, 2, 26, 27, 28, 52, 53]:
    letter = column_number_to_letter(number)
    print(f"{number:>3} -> {letter}")

for letter in ["A", "Z", "AA", "AB", "AZ", "BA"]:
    print(f"{letter:>3} -> {column_letter_to_number(letter)}")


# ============================================================================
# SECTION 3: CELL REFERENCES
# ============================================================================

CELL_REFERENCE_PATTERN = re.compile(
    r"^\$?([A-Za-z]{1,3})\$?([1-9][0-9]*)$"
)


@dataclass(frozen=True)
class CellReference:
    """
    Represents an Excel-style cell reference.

    Examples:
        A1
        $A$1
        A$1
        $A1

    column_absolute:
        True when the column contains $.

    row_absolute:
        True when the row contains $.
    """

    column: int
    row: int
    column_absolute: bool = False
    row_absolute: bool = False

    @classmethod
    def parse(cls, reference: str) -> "CellReference":
        match = CELL_REFERENCE_PATTERN.match(reference.strip())

        if not match:
            raise ValueError(f"Invalid cell reference: {reference!r}")

        raw = reference.strip()
        column_letters = match.group(1)
        row_number = int(match.group(2))

        column_absolute = raw.startswith("$")
        row_absolute = "$" in raw[len(column_letters) + int(column_absolute):]

        return cls(
            column=column_letter_to_number(column_letters),
            row=row_number,
            column_absolute=column_absolute,
            row_absolute=row_absolute,
        )

    def address(self) -> str:
        """Return the reference in Excel-like notation."""
        column = column_number_to_letter(self.column)
        column_part = f"${column}" if self.column_absolute else column
        row_part = f"${self.row}" if self.row_absolute else str(self.row)
        return column_part + row_part

    def shifted(self, row_delta: int, column_delta: int) -> "CellReference":
        """
        Simulate copying a formula.

        Relative coordinates move.
        Absolute coordinates stay fixed.
        """
        new_row = self.row if self.row_absolute else self.row + row_delta
        new_column = (
            self.column
            if self.column_absolute
            else self.column + column_delta
        )

        if new_row < 1 or new_column < 1:
            raise ValueError("A shifted reference would leave the worksheet.")

        return CellReference(
            column=new_column,
            row=new_row,
            column_absolute=self.column_absolute,
            row_absolute=self.row_absolute,
        )


print("\nREFERENCE TYPES")
for text in ["A1", "$A$1", "A$1", "$A1", "B7"]:
    reference = CellReference.parse(text)
    print(
        f"{text:>5} -> column={reference.column}, row={reference.row}, "
        f"column_absolute={reference.column_absolute}, "
        f"row_absolute={reference.row_absolute}"
    )

print("\nCOPYING REFERENCES")
original = CellReference.parse("A1")
for row_delta, column_delta in [(0, 0), (1, 0), (2, 1), (4, 3)]:
    print(
        f"A1 copied by rows={row_delta}, columns={column_delta}: "
        f"{original.shifted(row_delta, column_delta).address()}"
    )

print("\nABSOLUTE AND MIXED REFERENCES")
for reference_text in ["A1", "$A$1", "A$1", "$A1"]:
    reference = CellReference.parse(reference_text)
    copied = reference.shifted(3, 2)
    print(f"{reference_text:>5} -> copied to {copied.address()}")


# ============================================================================
# SECTION 4: FORMATTING MODEL
# ============================================================================

@dataclass
class CellFormat:
    """
    A simplified representation of common spreadsheet formatting.

    Excel supports many more formatting features. These properties model
    common concepts without requiring an Excel-specific library.
    """

    number_format: str = "General"
    bold: bool = False
    italic: bool = False
    horizontal_alignment: str = "general"
    vertical_alignment: str = "bottom"
    fill: Optional[str] = None
    font_name: str = "Calibri"
    font_size: int = 11
    font_color: Optional[str] = None
    border: Optional[str] = None
    wrap_text: bool = False

    def describe(self) -> str:
        attributes = [
            f"number_format={self.number_format!r}",
            f"bold={self.bold}",
            f"italic={self.italic}",
            f"alignment={self.horizontal_alignment!r}",
        ]

        if self.fill:
            attributes.append(f"fill={self.fill!r}")

        if self.border:
            attributes.append(f"border={self.border!r}")

        return "CellFormat(" + ", ".join(attributes) + ")"


@dataclass
class ConditionalFormatRule:
    """Represents a simplified conditional-formatting rule."""

    operator_name: str
    threshold: float
    display_format: CellFormat

    def applies(self, value: Any) -> bool:
        if not isinstance(value, (int, float)):
            return False

        operations = {
            ">": operator.gt,
            ">=": operator.ge,
            "<": operator.lt,
            "<=": operator.le,
            "==": operator.eq,
            "!=": operator.ne,
        }

        if self.operator_name not in operations:
            raise ValueError(
                f"Unsupported conditional operator: {self.operator_name}"
            )

        return operations[self.operator_name](value, self.threshold)


# ============================================================================
# SECTION 5: CELL AND WORKSHEET
# ============================================================================

@dataclass
class Cell:
    """A spreadsheet cell containing a value or formula plus formatting."""

    value: Any = None
    formula: Optional[str] = None
    format: CellFormat = field(default_factory=CellFormat)

    def is_formula(self) -> bool:
        return self.formula is not None

    def display_value(self) -> str:
        if self.value is None:
            return ""

        if self.format.number_format == "0.00":
            try:
                return f"{float(self.value):.2f}"
            except (ValueError, TypeError):
                return str(self.value)

        if self.format.number_format == "0":
            try:
                return f"{float(self.value):.0f}"
            except (ValueError, TypeError):
                return str(self.value)

        if self.format.number_format == "0.00%":
            try:
                return f"{float(self.value) * 100:.2f}%"
            except (ValueError, TypeError):
                return str(self.value)

        if self.format.number_format == "$#,##0.00":
            try:
                return f"${float(self.value):,.2f}"
            except (ValueError, TypeError):
                return str(self.value)

        return str(self.value)


class Worksheet:
    """A simplified worksheet implementation."""

    def __init__(self, name: str):
        if not name or len(name) > 31:
            raise ValueError(
                "Worksheet names must contain 1 to 31 characters."
            )

        self.name = name
        self.cells: Dict[str, Cell] = {}
        self.conditional_rules: Dict[str, List[ConditionalFormatRule]] = {}

    def set_value(self, address: str, value: Any) -> None:
        """Store a literal value."""
        normalized = normalize_address(address)
        self.cells[normalized] = Cell(value=value)

    def set_formula(self, address: str, formula: str) -> None:
        """Store a formula without evaluating it yet."""
        if not formula.startswith("="):
            raise ValueError("A formula must begin with '='.")

        normalized = normalize_address(address)
        self.cells[normalized] = Cell(formula=formula)

    def get_cell(self, address: str) -> Cell:
        normalized = normalize_address(address)

        if normalized not in self.cells:
            self.cells[normalized] = Cell()

        return self.cells[normalized]

    def format_cell(self, address: str, **changes: Any) -> None:
        """Change selected formatting properties."""
        cell = self.get_cell(address)

        for property_name, value in changes.items():
            if not hasattr(cell.format, property_name):
                raise AttributeError(
                    f"Unknown formatting property: {property_name}"
                )

            setattr(cell.format, property_name, value)

    def add_conditional_rule(
        self,
        address: str,
        rule: ConditionalFormatRule,
    ) -> None:
        normalized = normalize_address(address)
        self.conditional_rules.setdefault(normalized, []).append(rule)

    def used_range(self) -> Tuple[int, int, int, int]:
        """Return min row, max row, min column, max column."""
        if not self.cells:
            return (1, 1, 1, 1)

        coordinates = [
            CellReference.parse(address)
            for address in self.cells
        ]

        rows = [reference.row for reference in coordinates]
        columns = [reference.column for reference in coordinates]

        return (
            min(rows),
            max(rows),
            min(columns),
            max(columns),
        )

    def print_grid(self, max_width: int = 18) -> None:
        """Print a readable representation of the used worksheet area."""
        min_row, max_row, min_column, max_column = self.used_range()

        header = [" " * 6]

        for column in range(min_column, max_column + 1):
            header.append(
                f"{column_number_to_letter(column):^{max_width}}"
            )

        print("".join(header))
        print("-" * (6 + max_width * (max_column - min_column + 1)))

        for row in range(min_row, max_row + 1):
            output = [f"{row:>5} "]

            for column in range(min_column, max_column + 1):
                address = (
                    f"{column_number_to_letter(column)}{row}"
                )
                value = self.get_cell(address).display_value()
                output.append(f"{value[:max_width]:^{max_width}}")

            print("".join(output))


def normalize_address(address: str) -> str:
    """Normalize references such as a1 into A1."""
    reference = CellReference.parse(address)
    return reference.address().replace("$", "")


# ============================================================================
# SECTION 6: WORKBOOK
# ============================================================================

class Workbook:
    """A workbook containing multiple worksheets."""

    def __init__(self):
        self.worksheets: Dict[str, Worksheet] = {}

    def add_worksheet(self, name: str) -> Worksheet:
        if name in self.worksheets:
            raise ValueError(f"Worksheet already exists: {name!r}")

        worksheet = Worksheet(name)
        self.worksheets[name] = worksheet
        return worksheet

    def get_worksheet(self, name: str) -> Worksheet:
        if name not in self.worksheets:
            raise KeyError(f"Worksheet not found: {name!r}")

        return self.worksheets[name]

    def list_worksheets(self) -> List[str]:
        return list(self.worksheets.keys())


# ============================================================================
# SECTION 7: BASIC WORKBOOK EXAMPLE
# ============================================================================

print("\nBASIC WORKBOOK EXAMPLE")

workbook = Workbook()
sales = workbook.add_worksheet("Sales")
summary = workbook.add_worksheet("Summary")

sales.set_value("A1", "Product")
sales.set_value("B1", "Units")
sales.set_value("C1", "Price")
sales.set_value("D1", "Revenue")

sales.set_value("A2", "Laptop")
sales.set_value("B2", 5)
sales.set_value("C2", 850)

sales.set_value("A3", "Monitor")
sales.set_value("B3", 8)
sales.set_value("C3", 250)

sales.set_value("A4", "Keyboard")
sales.set_value("B4", 15)
sales.set_value("C4", 45)

sales.print_grid()


# ============================================================================
# SECTION 8: FORMULA FUNCTIONS
# ============================================================================

def excel_sum(values: Iterable[Any]) -> float:
    """Simplified SUM: ignore non-numeric values."""
    total = 0.0

    for value in values:
        if isinstance(value, bool):
            continue

        if isinstance(value, (int, float)):
            total += value

    return total


def excel_average(values: Iterable[Any]) -> float:
    """Simplified AVERAGE."""
    numeric_values = [
        value
        for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]

    if not numeric_values:
        raise ValueError("#DIV/0!")

    return sum(numeric_values) / len(numeric_values)


def excel_min(values: Iterable[Any]) -> float:
    numeric_values = [
        value
        for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]

    if not numeric_values:
        raise ValueError("#VALUE!")

    return min(numeric_values)


def excel_max(values: Iterable[Any]) -> float:
    numeric_values = [
        value
        for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]

    if not numeric_values:
        raise ValueError("#VALUE!")

    return max(numeric_values)


def excel_round(value: float, digits: int = 0) -> float:
    return round(value, digits)


def excel_if(condition: bool, value_if_true: Any, value_if_false: Any) -> Any:
    return value_if_true if condition else value_if_false


def excel_count(values: Iterable[Any]) -> int:
    return sum(
        1
        for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    )


def excel_counta(values: Iterable[Any]) -> int:
    return sum(1 for value in values if value is not None and value != "")


print("\nCOMMON FUNCTION EXAMPLES")
numbers = [10, 20, 30, 40, "text", None]
print("SUM:", excel_sum(numbers))
print("AVERAGE:", excel_average(numbers))
print("MIN:", excel_min(numbers))
print("MAX:", excel_max(numbers))
print("ROUND:", excel_round(12.34567, 2))
print("IF:", excel_if(85 >= 50, "Pass", "Fail"))
print("COUNT:", excel_count(numbers))
print("COUNTA:", excel_counta(numbers))


# ============================================================================
# SECTION 9: RANGE PARSING
# ============================================================================

RANGE_PATTERN = re.compile(
    r"^\$?([A-Za-z]{1,3})\$?([1-9][0-9]*):\$?([A-Za-z]{1,3})\$?([1-9][0-9]*)$"
)


def expand_range(range_text: str) -> List[str]:
    """
    Expand A1:C3 into:
        A1, B1, C1, A2, B2, C2, A3, B3, C3
    """
    match = RANGE_PATTERN.match(range_text.strip())

    if not match:
        raise ValueError(f"Invalid range: {range_text!r}")

    start_column = column_letter_to_number(match.group(1))
    start_row = int(match.group(2))
    end_column = column_letter_to_number(match.group(3))
    end_row = int(match.group(4))

    if start_column > end_column:
        start_column, end_column = end_column, start_column

    if start_row > end_row:
        start_row, end_row = end_row, start_row

    addresses: List[str] = []

    for row in range(start_row, end_row + 1):
        for column in range(start_column, end_column + 1):
            addresses.append(
                f"{column_number_to_letter(column)}{row}"
            )

    return addresses


print("\nRANGE EXPANSION")
print("A1:C3 ->", expand_range("A1:C3"))


# ============================================================================
# SECTION 10: FORMULA TOKENIZATION
# ============================================================================

TOKEN_PATTERN = re.compile(
    r"""
    (?P<space>\s+)
    |
    (?P<number>\d+(?:\.\d+)?)
    |
    (?P<string>"(?:[^"]|"")*")
    |
    (?P<cell>\$?[A-Za-z]{1,3}\$?\d+)
    |
    (?P<operator><=|>=|<>|=|\+|-|\*|/|\^|<|>)
    |
    (?P<comma>,)
    |
    (?P<colon>:)
    |
    (?P<lparen>\()
    |
    (?P<rparen>\))
    |
    (?P<identifier>[A-Za-z_][A-Za-z0-9_.]*)
    """,
    re.VERBOSE,
)


def tokenize_formula(formula: str) -> List[Tuple[str, str]]:
    """
    Tokenize a small Excel-like formula language.

    This is intentionally smaller than Excel's actual formula grammar.
    """
    if not formula.startswith("="):
        raise ValueError("Formula must begin with '='.")

    expression = formula[1:]
    position = 0
    tokens: List[Tuple[str, str]] = []

    while position < len(expression):
        match = TOKEN_PATTERN.match(expression, position)

        if not match:
            raise ValueError(
                f"Unsupported formula character near: "
                f"{expression[position:]!r}"
            )

        token_type = match.lastgroup
        token_value = match.group(token_type)

        if token_type != "space":
            tokens.append((token_type, token_value))

        position = match.end()

    return tokens


print("\nFORMULA TOKENIZATION")
example_formula = "=SUM(B2:B4)*$C$1"
print(example_formula)
print(tokenize_formula(example_formula))


# ============================================================================
# SECTION 11: SAFE EXPRESSION EVALUATION
# ============================================================================

class FormulaError(Exception):
    """Base class for spreadsheet formula errors."""


class CircularReferenceError(FormulaError):
    """Raised when a formula directly or indirectly references itself."""


class SpreadsheetEvaluator:
    """
    Evaluates a useful subset of Excel-style formulas.

    Supported:
        arithmetic
        comparisons
        cell references
        ranges
        SUM
        AVERAGE
        MIN
        MAX
        ROUND
        IF
        COUNT
        COUNTA

    The evaluator converts supported syntax into a Python AST and only permits
    a controlled set of AST nodes. It does not execute arbitrary Python code.
    """

    FUNCTION_NAMES = {
        "SUM",
        "AVERAGE",
        "MIN",
        "MAX",
        "ROUND",
        "IF",
        "COUNT",
        "COUNTA",
    }

    def __init__(self, worksheet: Worksheet):
        self.worksheet = worksheet
        self.evaluation_stack: List[str] = []

    def evaluate_cell(self, address: str) -> Any:
        normalized = normalize_address(address)

        if normalized in self.evaluation_stack:
            cycle = " -> ".join(self.evaluation_stack + [normalized])
            raise CircularReferenceError(
                f"Circular reference detected: {cycle}"
            )

        cell = self.worksheet.get_cell(normalized)

        if not cell.is_formula():
            return cell.value

        self.evaluation_stack.append(normalized)

        try:
            return self.evaluate_formula(cell.formula or "")
        finally:
            self.evaluation_stack.pop()

    def evaluate_formula(self, formula: str) -> Any:
        translated = self.translate_formula(formula)

        try:
            tree = ast.parse(translated, mode="eval")
        except SyntaxError as exc:
            raise FormulaError(
                f"Invalid formula syntax: {formula!r}"
            ) from exc

        return self.evaluate_ast(tree.body)

    def translate_formula(self, formula: str) -> str:
        """
        Translate supported Excel operators into Python-like expressions.

        Excel:
            ^  -> **
            <> -> !=

        Cell references are converted into calls to CELL().
        """
        tokens = tokenize_formula(formula)
        output: List[str] = []

        for token_type, token_value in tokens:
            if token_type == "operator":
                if token_value == "^":
                    output.append("**")
                elif token_value == "<>":
                    output.append("!=")
                else:
                    output.append(token_value)

            elif token_type == "cell":
                output.append(f'CELL("{normalize_address(token_value)}")')

            elif token_type == "identifier":
                upper = token_value.upper()

                if upper in self.FUNCTION_NAMES:
                    output.append(upper)
                else:
                    raise FormulaError(
                        f"Unknown identifier: {token_value}"
                    )

            elif token_type == "colon":
                # Ranges need function-aware parsing. A colon by itself is
                # converted to a marker and handled in evaluate_range_form.
                output.append(" RANGE_SEPARATOR ")

            elif token_type == "number":
                output.append(token_value)

            elif token_type == "string":
                # Excel strings use double quotes. A doubled quote inside an
                # Excel string represents a literal quote.
                content = token_value[1:-1].replace('""', '"')
                output.append(repr(content))

            elif token_type in {"comma", "lparen", "rparen"}:
                output.append(token_value)

            else:
                raise FormulaError(
                    f"Unsupported token: {token_type} {token_value}"
                )

        result = "".join(output)

        # Replace simple range syntax such as CELL("A1") RANGE_SEPARATOR
        # CELL("A3") with RANGE("A1","A3").
        range_pattern = re.compile(
            r'CELL\("([A-Z]+\d+)"\)\s*RANGE_SEPARATOR\s*'
            r'CELL\("([A-Z]+\d+)"\)'
        )

        result = range_pattern.sub(
            r'RANGE("\1","\2")',
            result,
        )

        return result

    def evaluate_ast(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.UnaryOp):
            operand = self.evaluate_ast(node.operand)

            if isinstance(node.op, ast.USub):
                return -operand

            if isinstance(node.op, ast.UAdd):
                return +operand

            raise FormulaError("Unsupported unary operator.")

        if isinstance(node, ast.BinOp):
            left = self.evaluate_ast(node.left)
            right = self.evaluate_ast(node.right)

            operations = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: self.safe_divide,
                ast.Pow: operator.pow,
                ast.Mod: operator.mod,
            }

            for node_type, function in operations.items():
                if isinstance(node.op, node_type):
                    try:
                        return function(left, right)
                    except ZeroDivisionError as exc:
                        raise FormulaError("#DIV/0!") from exc
                    except (ValueError, OverflowError) as exc:
                        raise FormulaError("#NUM!") from exc

            raise FormulaError("Unsupported binary operator.")

        if isinstance(node, ast.Compare):
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise FormulaError(
                    "Only simple comparisons are supported."
                )

            left = self.evaluate_ast(node.left)
            right = self.evaluate_ast(node.comparators[0])
            comparison = node.ops[0]

            operations = {
                ast.Eq: operator.eq,
                ast.NotEq: operator.ne,
                ast.Lt: operator.lt,
                ast.LtE: operator.le,
                ast.Gt: operator.gt,
                ast.GtE: operator.ge,
            }

            for node_type, function in operations.items():
                if isinstance(comparison, node_type):
                    return function(left, right)

            raise FormulaError("Unsupported comparison operator.")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise FormulaError("Unsupported function call.")

            function_name = node.func.id.upper()

            if function_name == "CELL":
                if len(node.args) != 1:
                    raise FormulaError("CELL requires one address.")

                address = self.evaluate_ast(node.args[0])
                return self.evaluate_cell(address)

            if function_name == "RANGE":
                if len(node.args) != 2:
                    raise FormulaError("RANGE requires two addresses.")

                start = self.evaluate_ast(node.args[0])
                end = self.evaluate_ast(node.args[1])

                values = [
                    self.evaluate_cell(address)
                    for address in expand_range(f"{start}:{end}")
                ]

                return values

            if function_name in self.FUNCTION_NAMES:
                arguments = [
                    self.evaluate_ast(argument)
                    for argument in node.args
                ]

                return self.call_function(function_name, arguments)

            raise FormulaError(
                f"Unsupported function: {function_name}"
            )

        if isinstance(node, ast.Name):
            raise FormulaError(
                f"Unexpected identifier: {node.id}"
            )

        raise FormulaError(
            f"Unsupported formula expression: {type(node).__name__}"
        )

    @staticmethod
    def safe_divide(left: Any, right: Any) -> float:
        if right == 0:
            raise ZeroDivisionError
        return left / right

    def flatten_arguments(self, arguments: Sequence[Any]) -> List[Any]:
        flattened: List[Any] = []

        for argument in arguments:
            if isinstance(argument, list):
                flattened.extend(argument)
            else:
                flattened.append(argument)

        return flattened

    def call_function(self, name: str, arguments: List[Any]) -> Any:
        values = self.flatten_arguments(arguments)

        if name == "SUM":
            return excel_sum(values)

        if name == "AVERAGE":
            return excel_average(values)

        if name == "MIN":
            return excel_min(values)

        if name == "MAX":
            return excel_max(values)

        if name == "ROUND":
            if not arguments:
                raise FormulaError("ROUND requires at least one argument.")

            number = arguments[0]

            if len(arguments) == 1:
                digits = 0
            elif len(arguments) == 2:
                digits = int(arguments[1])
            else:
                raise FormulaError(
                    "ROUND accepts one or two arguments."
                )

            return excel_round(number, digits)

        if name == "IF":
            if len(arguments) != 3:
                raise FormulaError(
                    "IF requires condition, true result, and false result."
                )

            return excel_if(arguments[0], arguments[1], arguments[2])

        if name == "COUNT":
            return excel_count(values)

        if name == "COUNTA":
            return excel_counta(values)

        raise FormulaError(f"Unsupported function: {name}")


# ============================================================================
# SECTION 12: FORMULA EXAMPLES
# ============================================================================

print("\nFORMULA EVALUATION")

sales.set_formula("D2", "=B2*C2")
sales.set_formula("D3", "=B3*C3")
sales.set_formula("D4", "=B4*C4")

evaluator = SpreadsheetEvaluator(sales)

for address in ["D2", "D3", "D4"]:
    print(f"{address} = {evaluator.evaluate_cell(address)}")

sales.set_formula("D5", "=SUM(D2:D4)")
sales.set_formula("D6", "=AVERAGE(D2:D4)")
sales.set_formula("D7", "=MAX(D2:D4)")
sales.set_formula("D8", "=MIN(D2:D4)")

for address in ["D5", "D6", "D7", "D8"]:
    print(f"{address} = {evaluator.evaluate_cell(address)}")


# ============================================================================
# SECTION 13: ARITHMETIC AND COMPARISON EXAMPLES
# ============================================================================

print("\nARITHMETIC AND COMPARISON FORMULAS")

test_formulas = [
    "=10+5",
    "=10-5",
    "=10*5",
    "=10/5",
    "=2^3",
    "=10>5",
    "=10=5",
    "=10<>5",
]

for formula in test_formulas:
    try:
        print(f"{formula:>10} -> {evaluator.evaluate_formula(formula)}")
    except FormulaError as error:
        print(f"{formula:>10} -> ERROR {error}")


# ============================================================================
# SECTION 14: IF AND ROUND
# ============================================================================

sales.set_value("E2", 82.567)
sales.set_formula("F2", '=ROUND(E2,2)')
sales.set_formula("G2", '=IF(E2>=50,"Pass","Fail")')

for address in ["E2", "F2", "G2"]:
    try:
        print(f"{address} = {evaluator.evaluate_cell(address)}")
    except FormulaError as error:
        print(f"{address} -> ERROR {error}")


# ============================================================================
# SECTION 15: RELATIVE, ABSOLUTE, AND MIXED REFERENCES
# ============================================================================

print("\nREFERENCE BEHAVIOR")

reference_examples = [
    ("A1", "normal relative reference"),
    ("$A$1", "absolute row and column"),
    ("A$1", "absolute row, relative column"),
    ("$A1", "relative row, absolute column"),
]

for address, explanation in reference_examples:
    reference = CellReference.parse(address)
    copied = reference.shifted(2, 3)

    print(
        f"{address:>5} | {explanation:<35} | "
        f"copied two rows and three columns -> {copied.address()}"
    )


# ============================================================================
# SECTION 16: COPYING A FORMULA
# ============================================================================

def copy_formula(
    formula: str,
    row_delta: int,
    column_delta: int,
) -> str:
    """
    Shift cell references in a formula as Excel does when a formula is copied.

    This educational implementation handles ordinary A1 references.
    """
    reference_pattern = re.compile(
        r"\$?[A-Za-z]{1,3}\$?[1-9][0-9]*"
    )

    def replace(match: re.Match[str]) -> str:
        reference = CellReference.parse(match.group(0))
        return reference.shifted(row_delta, column_delta).address()

    return reference_pattern.sub(replace, formula)


print("\nFORMULA COPYING")

original_formula = "=B2*C2"
for row_delta in range(4):
    print(
        f"{original_formula} copied down {row_delta} row(s) -> "
        f"{copy_formula(original_formula, row_delta, 0)}"
    )

mixed_formula = "=B2*$F$1"
print(
    "Mixed example:",
    mixed_formula,
    "copied one row down ->",
    copy_formula(mixed_formula, 1, 0),
)


# ============================================================================
# SECTION 17: PRACTICAL FINANCIAL WORKSHEET
# ============================================================================

print("\nPRACTICAL FINANCIAL WORKSHEET")

finance = workbook.add_worksheet("Financial Model")

finance.set_value("A1", "Quarter")
finance.set_value("B1", "Revenue")
finance.set_value("C1", "Operating Cost")
finance.set_value("D1", "Operating Profit")
finance.set_value("E1", "Margin")

quarters = [
    ("Q1", 120000, 75000),
    ("Q2", 145000, 88000),
    ("Q3", 165000, 92000),
    ("Q4", 190000, 110000),
]

for row_number, (quarter, revenue, cost) in enumerate(quarters, start=2):
    finance.set_value(f"A{row_number}", quarter)
    finance.set_value(f"B{row_number}", revenue)
    finance.set_value(f"C{row_number}", cost)
    finance.set_formula(f"D{row_number}", f"=B{row_number}-C{row_number}")
    finance.set_formula(
        f"E{row_number}",
        f"=D{row_number}/B{row_number}",
    )

finance.set_formula("B6", "=SUM(B2:B5)")
finance.set_formula("C6", "=SUM(C2:C5)")
finance.set_formula("D6", "=SUM(D2:D5)")
finance.set_formula("E6", "=D6/B6")

for address in ["B6", "C6", "D6", "E6"]:
    print(f"{address} = {SpreadsheetEvaluator(finance).evaluate_cell(address)}")


# ============================================================================
# SECTION 18: FORMATTING EXAMPLES
# ============================================================================

print("\nFORMATTING")

for address in ["A1", "B1", "C1", "D1", "E1"]:
    finance.format_cell(
        address,
        bold=True,
        horizontal_alignment="center",
        fill="header",
        border="bottom",
    )

for row_number in range(2, 7):
    for column in ["B", "C", "D"]:
        finance.format_cell(
            f"{column}{row_number}",
            number_format="$#,##0.00",
            horizontal_alignment="right",
        )

    finance.format_cell(
        f"E{row_number}",
        number_format="0.00%",
        horizontal_alignment="right",
    )

print(finance.get_cell("D2").format.describe())
print(finance.get_cell("E2").format.describe())

print("\nFORMATTED FINANCIAL GRID")
evaluator_finance = SpreadsheetEvaluator(finance)

for address, cell in finance.cells.items():
    if cell.formula:
        try:
            cell.value = evaluator_finance.evaluate_cell(address)
        except FormulaError as error:
            cell.value = str(error)

finance.print_grid()


# ============================================================================
# SECTION 19: CONDITIONAL FORMATTING
# ============================================================================

print("\nCONDITIONAL FORMATTING")

profit_rule = ConditionalFormatRule(
    operator_name="<",
    threshold=40000,
    display_format=CellFormat(
        fill="warning",
        font_color="red",
        bold=True,
    ),
)

finance.add_conditional_rule("D2", profit_rule)
finance.add_conditional_rule("D3", profit_rule)
finance.add_conditional_rule("D4", profit_rule)
finance.add_conditional_rule("D5", profit_rule)

for address in ["D2", "D3", "D4", "D5"]:
    value = finance.get_cell(address).value
    triggered = profit_rule.applies(value)

    print(
        f"{address}: value={value}, "
        f"conditional_rule_applies={triggered}"
    )


# ============================================================================
# SECTION 20: DATA TYPES
# ============================================================================

print("\nDATA TYPES")

data_types = {
    "Text": "Laptop",
    "Integer": 25,
    "Decimal": 25.75,
    "Boolean": True,
    "Blank": None,
}

for name, value in data_types.items():
    print(
        f"{name:<10} -> Python type={type(value).__name__:<10} "
        f"value={value!r}"
    )

print(
    """
Spreadsheet applications distinguish between displayed text and the
underlying value. A number formatted as currency is still fundamentally a
number. A date is also represented internally as a numeric/date value by
spreadsheet applications, while formatting controls how it is displayed.
"""
)


# ============================================================================
# SECTION 21: INPUT VALIDATION
# ============================================================================

def validate_positive_number(value: Any) -> float:
    """Convert a value to a positive number or raise a clear error."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Value must be numeric.") from exc

    if not math.isfinite(number):
        raise ValueError("Value must be finite.")

    if number < 0:
        raise ValueError("Value cannot be negative.")

    return number


print("\nVALIDATION")

for value in [100, "250.50", -10, "not a number", float("inf")]:
    try:
        print(value, "->", validate_positive_number(value))
    except ValueError as error:
        print(value, "-> ERROR:", error)


# ============================================================================
# SECTION 22: DECIMAL PRECISION
# ============================================================================

print("\nDECIMAL PRECISION")

binary_result = 0.1 + 0.2
decimal_result = Decimal("0.1") + Decimal("0.2")

print("Binary floating-point:", binary_result)
print("Decimal arithmetic:", decimal_result)

print(
    """
Spreadsheet financial models often require careful treatment of rounding.
Floating-point arithmetic can contain small representation errors. The
important distinction is between the stored value and the displayed value.
Formatting a number to two decimals does not necessarily change the stored
number. Explicit ROUND-style calculations are appropriate when the business
rule requires the calculation itself to be rounded.
"""
)


# ============================================================================
# SECTION 23: ERROR CONDITIONS
# ============================================================================

print("\nERROR CONDITIONS")

error_examples = [
    "=10/0",
    "=AVERAGE()",
    "=UNKNOWN(10)",
    "=10+",
]

for formula in error_examples:
    try:
        print(formula, "->", evaluator.evaluate_formula(formula))
    except FormulaError as error:
        print(formula, "->", type(error).__name__, str(error))


# ============================================================================
# SECTION 24: CIRCULAR REFERENCES
# ============================================================================

print("\nCIRCULAR REFERENCE")

cycle_sheet = workbook.add_worksheet("Circular Test")
cycle_sheet.set_formula("A1", "=B1+1")
cycle_sheet.set_formula("B1", "=A1+1")

cycle_evaluator = SpreadsheetEvaluator(cycle_sheet)

try:
    print(cycle_evaluator.evaluate_cell("A1"))
except CircularReferenceError as error:
    print("Detected:", error)


# ============================================================================
# SECTION 25: DEPENDENCY EXTRACTION
# ============================================================================

def extract_references(formula: str) -> List[str]:
    """
    Extract simple A1 references from a formula.

    Range endpoints are returned individually. A full spreadsheet engine would
    maintain a richer dependency graph, including sheet-qualified references.
    """
    references = re.findall(
        r"(?<![A-Za-z0-9_])(\$?[A-Za-z]{1,3}\$?[1-9][0-9]*)",
        formula,
    )

    return [normalize_address(reference) for reference in references]


print("\nDEPENDENCY EXTRACTION")

dependency_formula = "=B2*C2+SUM(D2:D5)"
print(dependency_formula)
print("References:", extract_references(dependency_formula))


def dependency_graph(worksheet: Worksheet) -> Dict[str, List[str]]:
    """Create a simple formula dependency graph."""
    graph: Dict[str, List[str]] = {}

    for address, cell in worksheet.cells.items():
        if cell.formula:
            graph[address] = extract_references(cell.formula)

    return graph


print("Financial model dependency graph:")
for address, dependencies in dependency_graph(finance).items():
    print(f"  {address} depends on {dependencies}")


# ============================================================================
# SECTION 26: FORMULA AUDITING
# ============================================================================

def audit_formulas(worksheet: Worksheet) -> List[str]:
    """
    Return formulas that contain obvious structural problems.

    This is intentionally a lightweight educational auditor rather than an
    Excel-compatible formula validator.
    """
    problems: List[str] = []

    for address, cell in worksheet.cells.items():
        if not cell.formula:
            continue

        formula = cell.formula

        if not formula.startswith("="):
            problems.append(
                f"{address}: formula does not begin with '='."
            )

        if formula.count("(") != formula.count(")"):
            problems.append(
                f"{address}: parentheses are unbalanced."
            )

        if formula.endswith(("+", "-", "*", "/")):
            problems.append(
                f"{address}: formula appears to end with an operator."
            )

    return problems


print("\nFORMULA AUDIT")
print(audit_formulas(finance))


# ============================================================================
# SECTION 27: CSV EXPORT
# ============================================================================

def worksheet_to_csv_lines(
    worksheet: Worksheet,
    evaluator: Optional[SpreadsheetEvaluator] = None,
) -> List[str]:
    """
    Export the used range as CSV-like text.

    This implementation performs simple CSV escaping and evaluates formulas
    when an evaluator is supplied.
    """
    min_row, max_row, min_column, max_column = worksheet.used_range()
    lines: List[str] = []

    for row in range(min_row, max_row + 1):
        values: List[str] = []

        for column in range(min_column, max_column + 1):
            address = f"{column_number_to_letter(column)}{row}"
            cell = worksheet.get_cell(address)

            value = cell.value

            if cell.formula and evaluator:
                try:
                    value = evaluator.evaluate_cell(address)
                except FormulaError as error:
                    value = str(error)

            text = "" if value is None else str(value)
            text = text.replace('"', '""')

            if any(character in text for character in [",", '"', "\n"]):
                text = f'"{text}"'

            values.append(text)

        lines.append(",".join(values))

    return lines


print("\nCSV-LIKE EXPORT")
for line in worksheet_to_csv_lines(finance, evaluator_finance):
    print(line)


# ============================================================================
# SECTION 28: FORMULA REFERENCE COMPARISON
# ============================================================================

print("\nREFERENCE COMPARISON")

comparison_sheet = workbook.add_worksheet("Reference Demo")

comparison_sheet.set_value("A1", 100)
comparison_sheet.set_value("B1", 0.10)

comparison_sheet.set_formula("C1", "=A1*B1")
comparison_sheet.set_formula("D1", "=A1*$B$1")
comparison_sheet.set_formula("E1", "=A1*B$1")
comparison_sheet.set_formula("F1", "=A1*$B1")

comparison_evaluator = SpreadsheetEvaluator(comparison_sheet)

for address in ["C1", "D1", "E1", "F1"]:
    print(
        address,
        "formula=",
        comparison_sheet.get_cell(address).formula,
        "value=",
        comparison_evaluator.evaluate_cell(address),
    )


# ============================================================================
# SECTION 29: PRACTICAL PAYROLL EXAMPLE
# ============================================================================

print("\nPAYROLL EXAMPLE")

payroll = workbook.add_worksheet("Payroll")

headers = [
    "Employee",
    "Hours",
    "Rate",
    "Gross Pay",
    "Tax Rate",
    "Tax",
    "Net Pay",
]

for column, header in enumerate(headers, start=1):
    payroll.set_value(
        f"{column_number_to_letter(column)}1",
        header,
    )

employees = [
    ("Anita", 40, 650, 0.10),
    ("Rahul", 42, 700, 0.12),
    ("Meera", 38, 800, 0.15),
]

for row, employee in enumerate(employees, start=2):
    name, hours, rate, tax_rate = employee

    payroll.set_value(f"A{row}", name)
    payroll.set_value(f"B{row}", hours)
    payroll.set_value(f"C{row}", rate)
    payroll.set_formula(f"D{row}", f"=B{row}*C{row}")
    payroll.set_value(f"E{row}", tax_rate)
    payroll.set_formula(f"F{row}", f"=D{row}*E{row}")
    payroll.set_formula(f"G{row}", f"=D{row}-F{row}")

payroll_evaluator = SpreadsheetEvaluator(payroll)

for row in range(2, 5):
    print(
        payroll.get_cell(f"A{row}").value,
        "gross=",
        payroll_evaluator.evaluate_cell(f"D{row}"),
        "tax=",
        payroll_evaluator.evaluate_cell(f"F{row}"),
        "net=",
        payroll_evaluator.evaluate_cell(f"G{row}"),
    )


# ============================================================================
# SECTION 30: PERFORMANCE CONSIDERATIONS
# ============================================================================

print("\nPERFORMANCE CONSIDERATIONS")

print(
    """
Important spreadsheet performance factors include:

1. Formula count
   A workbook with thousands or millions of formulas has more calculation work.

2. Dependency chains
   Long chains such as A1 -> B1 -> C1 -> D1 require dependent calculations.

3. Volatile calculations
   Functions that recalculate frequently can increase workbook calculation cost.

4. Large ranges
   Formulas that repeatedly scan very large ranges can become expensive.

5. Repeated calculations
   A well-designed model avoids performing the same expensive calculation
   unnecessarily.

6. Formatting volume
   Excessive unique formatting can increase workbook complexity.

7. External links
   References to other workbooks or external data sources can introduce
   additional latency and failure conditions.

8. Circular references
   Iterative calculation can be useful for some models but adds complexity
   and must be intentionally configured.
"""
)


# ============================================================================
# SECTION 31: SECURITY CONSIDERATIONS
# ============================================================================

print("\nSECURITY CONSIDERATIONS")

print(
    """
Spreadsheet security requires attention to several areas:

- Do not treat a workbook as inherently trusted.
- Review formulas before using a workbook from an untrusted source.
- Be careful with macros and executable content.
- External links can expose or retrieve information.
- Hidden worksheets and hidden columns are not reliable security boundaries.
- Protecting a worksheet is not equivalent to encrypting a file.
- Avoid placing passwords, API keys, tokens, or other secrets in cells.
- Validate imported data before using it in calculations.
- Watch for formula injection when spreadsheet data is generated from
  untrusted text.
- Keep business-critical workbooks versioned and reviewed.
"""
)


# ============================================================================
# SECTION 32: COMMON MISTAKES
# ============================================================================

print("\nCOMMON MISTAKES")

mistakes = [
    (
        "Typing numbers as text",
        "Calculations may ignore or mishandle values that look numeric but "
        "are stored as text."
    ),
    (
        "Incorrect references",
        "A formula can silently point to the wrong row or column."
    ),
    (
        "Forgetting absolute references",
        "A tax rate or exchange rate may move unexpectedly when a formula "
        "is copied."
    ),
    (
        "Hard-coding repeated constants",
        "Changing a business assumption becomes difficult when the same "
        "number is embedded in many formulas."
    ),
    (
        "Formatting instead of calculating",
        "Displaying two decimals does not necessarily round the underlying "
        "stored value."
    ),
    (
        "Hidden errors",
        "Blank-looking or suppressed errors can conceal broken logic."
    ),
    (
        "Poor structure",
        "Mixing raw inputs, calculations, presentation, and assumptions "
        "without organization makes models difficult to audit."
    ),
]

for mistake, consequence in mistakes:
    print(f"- {mistake}: {consequence}")


# ============================================================================
# SECTION 33: BEST-PRACTICE MODEL STRUCTURE
# ============================================================================

print("\nBEST-PRACTICE MODEL STRUCTURE")

print(
    """
A maintainable spreadsheet model commonly separates:

Inputs
    Assumptions, imported values, rates, dates, and user-controlled values.

Calculations
    Intermediate calculations and business logic.

Outputs
    Reports, metrics, charts, and decision-support information.

Formatting
    Formatting should improve readability and communicate meaning rather
    than hide errors.

Naming
    Clear worksheet names, consistent labels, and predictable cell layouts
    make auditing easier.

Traceability
    Important outputs should be traceable back to source inputs and formulas.
"""
)


# ============================================================================
# SECTION 34: SIMPLE TEST SUITE
# ============================================================================

def run_tests() -> None:
    """Run deterministic tests for the educational spreadsheet engine."""
    assert column_number_to_letter(1) == "A"
    assert column_number_to_letter(26) == "Z"
    assert column_number_to_letter(27) == "AA"

    assert column_letter_to_number("A") == 1
    assert column_letter_to_number("Z") == 26
    assert column_letter_to_number("AA") == 27

    assert normalize_address("a1") == "A1"
    assert expand_range("A1:B2") == ["A1", "B1", "A2", "B2"]

    sheet = Worksheet("Tests")
    sheet.set_value("A1", 10)
    sheet.set_value("A2", 20)
    sheet.set_formula("A3", "=SUM(A1:A2)")

    test_evaluator = SpreadsheetEvaluator(sheet)

    assert test_evaluator.evaluate_cell("A3") == 30

    sheet.set_formula("B1", "=A1*2")
    assert test_evaluator.evaluate_cell("B1") == 20

    sheet.set_formula("B2", "=IF(A2>10,\"yes\",\"no\")")
    assert test_evaluator.evaluate_cell("B2") == "yes"

    assert copy_formula("=A1*$C$1", 2, 1) == "=B3*$C$1"

    print("All tests passed.")


print("\nRUNNING TESTS")
run_tests()


# ============================================================================
# SECTION 35: FINAL STUDY DEMONSTRATION
# ============================================================================

print("\nFINAL STUDY DEMONSTRATION")

study = Workbook()
worksheet = study.add_worksheet("Fundamentals")

worksheet.set_value("A1", "Item")
worksheet.set_value("B1", "Quantity")
worksheet.set_value("C1", "Unit Price")
worksheet.set_value("D1", "Amount")
worksheet.set_value("E1", "Status")

items = [
    ("Notebook", 10, 80),
    ("Pen", 25, 20),
    ("Bag", 4, 950),
    ("Calculator", 3, 1200),
]

for row, (item, quantity, price) in enumerate(items, start=2):
    worksheet.set_value(f"A{row}", item)
    worksheet.set_value(f"B{row}", quantity)
    worksheet.set_value(f"C{row}", price)
    worksheet.set_formula(f"D{row}", f"=B{row}*C{row}")
    worksheet.set_formula(
        f"E{row}",
        f'=IF(D{row}>=1000,"High","Normal")',
    )

worksheet.set_value("A6", "Total")
worksheet.set_formula("D6", "=SUM(D2:D5)")

worksheet.set_formula("D7", "=AVERAGE(D2:D5)")
worksheet.set_value("A7", "Average")

for address in ["A1", "B1", "C1", "D1", "E1"]:
    worksheet.format_cell(
        address,
        bold=True,
        horizontal_alignment="center",
        fill="header",
        border="bottom",
    )

for row in range(2, 8):
    worksheet.format_cell(
        f"C{row}",
        number_format="$#,##0.00",
        horizontal_alignment="right",
    )
    worksheet.format_cell(
        f"D{row}",
        number_format="$#,##0.00",
        horizontal_alignment="right",
    )

final_evaluator = SpreadsheetEvaluator(worksheet)

for address, cell in worksheet.cells.items():
    if cell.formula:
        try:
            cell.value = final_evaluator.evaluate_cell(address)
        except FormulaError as error:
            cell.value = str(error)

worksheet.print_grid()

print("\nWORKBOOK SHEETS")
print(study.list_worksheets())

print(
    """
The complete model demonstrates the central spreadsheet relationship:

    DATA -> REFERENCES -> FORMULAS -> CALCULATIONS -> OUTPUTS -> FORMATTING

A reliable spreadsheet keeps these layers understandable. Values provide
inputs, references connect cells, formulas express calculations, functions
encapsulate common operations, and formatting communicates the result to a
human reader.
"""
)

print("=" * 78)
print("END OF EXCEL FUNDAMENTALS STUDY PROGRAM")
print("=" * 78)
