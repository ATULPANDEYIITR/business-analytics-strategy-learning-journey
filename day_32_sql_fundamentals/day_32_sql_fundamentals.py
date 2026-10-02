#!/usr/bin/env python3
"""
SQL Fundamentals: SELECT, FROM, WHERE and Basic Queries

A self-contained SQLite learning program covering:
- SELECT and FROM
- selecting specific columns
- aliases
- expressions and calculated columns
- DISTINCT
- WHERE filtering
- comparison and logical operators
- NULL handling
- LIKE, IN, BETWEEN
- CASE expressions
- ORDER BY and LIMIT as practical extensions of basic queries
- aggregate queries and GROUP BY as a bridge to intermediate SQL
- parameterized queries
- query validation and error handling
- realistic business data
- query-result inspection and performance considerations

The program uses only Python's standard library.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import Any, Iterable, Sequence


DATABASE_NAME = ":memory:"


@dataclass(frozen=True)
class QueryResult:
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]

    def print(self, title: str) -> None:
        print(f"\n--- {title} ---")
        if not self.rows:
            print("(no rows)")
            return

        widths = []
        for index, column in enumerate(self.columns):
            values = [str(row[index]) for row in self.rows]
            widths.append(max(len(column), *(len(value) for value in values)))

        header = " | ".join(
            column.ljust(widths[index])
            for index, column in enumerate(self.columns)
        )
        separator = "-+-".join("-" * width for width in widths)

        print(header)
        print(separator)

        for row in self.rows:
            print(
                " | ".join(
                    str(value).ljust(widths[index])
                    for index, value in enumerate(row)
                )
            )


def execute_query(
    connection: sqlite3.Connection,
    sql: str,
    parameters: Sequence[Any] = (),
) -> QueryResult:
    """
    Execute a read query and convert the result into a small immutable
    structure. Parameter values are supplied separately from SQL text,
    which prevents user-provided values from being interpreted as SQL.
    """
    try:
        cursor = connection.execute(sql, parameters)
        columns = tuple(description[0] for description in cursor.description or ())
        rows = tuple(tuple(row) for row in cursor.fetchall())
        return QueryResult(columns, rows)
    except sqlite3.Error as exc:
        raise RuntimeError(f"SQL execution failed: {exc}") from exc


def create_schema(connection: sqlite3.Connection) -> None:
    """
    Create a small but realistic company database.

    The tables are deliberately simple so SELECT and WHERE remain the
    focus rather than table design.
    """
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            department TEXT NOT NULL,
            job_title TEXT NOT NULL,
            city TEXT NOT NULL,
            salary INTEGER NOT NULL CHECK (salary > 0),
            years_experience INTEGER NOT NULL CHECK (years_experience >= 0),
            employment_status TEXT NOT NULL
                CHECK (employment_status IN ('Active', 'On Leave', 'Inactive')),
            manager_id INTEGER,
            FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE projects (
            project_id INTEGER PRIMARY KEY,
            project_name TEXT NOT NULL,
            department TEXT NOT NULL,
            status TEXT NOT NULL
                CHECK (status IN ('Planned', 'Active', 'Completed', 'Paused')),
            budget INTEGER NOT NULL CHECK (budget >= 0)
        );

        CREATE TABLE employee_projects (
            employee_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            assigned_role TEXT NOT NULL,
            PRIMARY KEY (employee_id, project_id),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );
        """
    )


def seed_data(connection: sqlite3.Connection) -> None:
    employees = [
        (1, "Anita Rao", "Engineering", "Senior Backend Engineer", "Bengaluru", 1450000, 8, "Active", None),
        (2, "Rohan Mehta", "Engineering", "Software Engineer", "Pune", 920000, 4, "Active", 1),
        (3, "Sara Khan", "Engineering", "Data Engineer", "Hyderabad", 1180000, 6, "Active", 1),
        (4, "Vikram Singh", "Finance", "Financial Analyst", "Mumbai", 840000, 5, "Active", None),
        (5, "Neha Sharma", "Product", "Product Manager", "Delhi", 1320000, 7, "Active", None),
        (6, "Arjun Nair", "Engineering", "QA Engineer", "Kochi", 760000, 3, "On Leave", 1),
        (7, "Meera Iyer", "Sales", "Account Executive", "Chennai", 680000, 2, "Active", None),
        (8, "Kabir Das", "Engineering", "Platform Engineer", "Noida", 1250000, 7, "Active", 1),
        (9, "Pooja Verma", "HR", "People Operations Specialist", "Lucknow", 620000, 3, "Active", None),
        (10, "Dev Malhotra", "Finance", "Senior Financial Analyst", "Mumbai", 1090000, 9, "Inactive", 4),
        (11, "Ishita Bose", "Product", "Product Analyst", "Kolkata", 880000, 3, "Active", 5),
        (12, "Rahul Joshi", "Sales", "Sales Operations Analyst", "Jaipur", 720000, 4, "Active", 7),
        (13, "Nitin Kapoor", "Engineering", "Security Engineer", "Gurugram", 1370000, 8, "Active", 1),
        (14, "Ayesha Ali", "Product", "UX Researcher", "Bengaluru", 970000, 5, "On Leave", 5),
    ]

    projects = [
        (101, "Cloud Migration", "Engineering", "Active", 2800000),
        (102, "Risk Analytics", "Finance", "Active", 1600000),
        (103, "Customer Portal", "Product", "Completed", 2200000),
        (104, "Security Hardening", "Engineering", "Active", 1900000),
        (105, "Sales Forecasting", "Sales", "Planned", 1100000),
    ]

    employee_projects = [
        (1, 101, "Technical Lead"),
        (2, 101, "Backend Developer"),
        (3, 101, "Data Engineer"),
        (8, 101, "Platform Engineer"),
        (13, 104, "Security Lead"),
        (1, 104, "Engineering Sponsor"),
        (4, 102, "Project Analyst"),
        (10, 102, "Senior Analyst"),
        (5, 103, "Product Lead"),
        (11, 103, "Product Analyst"),
        (7, 105, "Business Owner"),
        (12, 105, "Sales Analyst"),
    ]

    connection.executemany(
        """
        INSERT INTO employees (
            employee_id, full_name, department, job_title, city,
            salary, years_experience, employment_status, manager_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        employees,
    )
    connection.executemany(
        """
        INSERT INTO projects (
            project_id, project_name, department, status, budget
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        projects,
    )
    connection.executemany(
        """
        INSERT INTO employee_projects (
            employee_id, project_id, assigned_role
        )
        VALUES (?, ?, ?)
        """,
        employee_projects,
    )
    connection.commit()


def demonstrate_select_and_from(connection: sqlite3.Connection) -> None:
    """
    FROM identifies the source relation and SELECT identifies the values
    to return from that source.
    """
    execute_query(
        connection,
        "SELECT * FROM employees",
    ).print("SELECT * FROM employees")

    execute_query(
        connection,
        """
        SELECT employee_id, full_name, department
        FROM employees
        """,
    ).print("Selecting specific columns")


def demonstrate_aliases_and_expressions(connection: sqlite3.Connection) -> None:
    """
    SQL can return computed expressions without changing stored data.
    Aliases make those result columns meaningful to callers.
    """
    execute_query(
        connection,
        """
        SELECT
            full_name AS employee,
            job_title AS role,
            salary,
            salary * 0.10 AS estimated_bonus
        FROM employees
        WHERE employment_status = 'Active'
        """,
    ).print("Aliases and calculated columns")

    execute_query(
        connection,
        """
        SELECT
            full_name,
            department || ' / ' || job_title AS position
        FROM employees
        WHERE department = 'Engineering'
        """,
    ).print("String expression")


def demonstrate_where_comparisons(connection: sqlite3.Connection) -> None:
    """
    WHERE removes rows that do not satisfy a condition.

    Comparison operators are evaluated per row:
    =, !=, <>, >, >=, <, <=
    """
    execute_query(
        connection,
        """
        SELECT full_name, salary
        FROM employees
        WHERE salary >= 1200000
        """,
    ).print("Salary threshold")

    execute_query(
        connection,
        """
        SELECT full_name, department, years_experience
        FROM employees
        WHERE department = 'Engineering'
          AND years_experience >= 7
        """,
    ).print("Multiple conditions with AND")

    execute_query(
        connection,
        """
        SELECT full_name, department
        FROM employees
        WHERE department = 'Finance'
           OR department = 'Product'
        """,
    ).print("Alternative conditions with OR")

    execute_query(
        connection,
        """
        SELECT full_name, employment_status
        FROM employees
        WHERE employment_status != 'Inactive'
        """,
    ).print("Not-equal filtering")


def demonstrate_in_between_like(connection: sqlite3.Connection) -> None:
    """
    IN expresses membership in a finite set, BETWEEN expresses an inclusive
    range, and LIKE performs pattern matching.
    """
    execute_query(
        connection,
        """
        SELECT full_name, city, department
        FROM employees
        WHERE city IN ('Mumbai', 'Bengaluru', 'Pune')
        """,
    ).print("IN")

    execute_query(
        connection,
        """
        SELECT full_name, salary
        FROM employees
        WHERE salary BETWEEN 800000 AND 1200000
        """,
    ).print("BETWEEN")

    execute_query(
        connection,
        """
        SELECT full_name, job_title
        FROM employees
        WHERE job_title LIKE '%Engineer%'
        """,
    ).print("LIKE with a substring")

    execute_query(
        connection,
        """
        SELECT full_name
        FROM employees
        WHERE full_name LIKE 'A%'
        """,
    ).print("LIKE with a prefix")


def demonstrate_logical_precedence(connection: sqlite3.Connection) -> None:
    """
    AND has higher logical precedence than OR. Parentheses make the intended
    business rule explicit and prevent accidental broad matches.
    """
    execute_query(
        connection,
        """
        SELECT full_name, department, salary
        FROM employees
        WHERE department = 'Engineering'
          AND salary >= 1200000
           OR department = 'Product'
        """,
    ).print("AND before OR")

    execute_query(
        connection,
        """
        SELECT full_name, department, salary
        FROM employees
        WHERE
            (
                department = 'Engineering'
                AND salary >= 1200000
            )
            OR department = 'Product'
        """,
    ).print("Explicit parentheses")


def demonstrate_null(connection: sqlite3.Connection) -> None:
    """
    NULL means an unknown or missing value. It is not compared with = NULL.
    SQL uses IS NULL and IS NOT NULL for null tests.

    The sample data has NULL manager_id values for employees without a
    recorded manager.
    """
    execute_query(
        connection,
        """
        SELECT full_name, manager_id
        FROM employees
        WHERE manager_id IS NULL
        """,
    ).print("IS NULL")

    execute_query(
        connection,
        """
        SELECT full_name, manager_id
        FROM employees
        WHERE manager_id IS NOT NULL
        """,
    ).print("IS NOT NULL")

    # This intentionally demonstrates a common mistake. It normally returns
    # no rows because NULL = NULL evaluates to UNKNOWN rather than TRUE.
    execute_query(
        connection,
        """
        SELECT full_name
        FROM employees
        WHERE manager_id = NULL
        """,
    ).print("Incorrect NULL comparison")


def demonstrate_distinct(connection: sqlite3.Connection) -> None:
    """
    DISTINCT removes duplicate result combinations. It applies to the
    complete selected row, not to one column independently.
    """
    execute_query(
        connection,
        """
        SELECT DISTINCT department
        FROM employees
        """,
    ).print("Distinct departments")

    execute_query(
        connection,
        """
        SELECT DISTINCT department, city
        FROM employees
        ORDER BY department, city
        """,
    ).print("Distinct department/city combinations")


def demonstrate_order_and_limit(connection: sqlite3.Connection) -> None:
    """
    ORDER BY controls result ordering. LIMIT restricts how many rows are
    returned. Neither changes the stored data.
    """
    execute_query(
        connection,
        """
        SELECT full_name, salary
        FROM employees
        WHERE employment_status = 'Active'
        ORDER BY salary DESC
        LIMIT 5
        """,
    ).print("Highest active salaries")

    execute_query(
        connection,
        """
        SELECT full_name, years_experience
        FROM employees
        WHERE department = 'Engineering'
        ORDER BY years_experience ASC, full_name ASC
        """,
    ).print("Multiple sort keys")


def demonstrate_case(connection: sqlite3.Connection) -> None:
    """
    CASE allows a query to classify rows according to business rules while
    keeping the classification in the result rather than storing it.
    """
    execute_query(
        connection,
        """
        SELECT
            full_name,
            salary,
            CASE
                WHEN salary >= 1300000 THEN 'Senior compensation band'
                WHEN salary >= 900000 THEN 'Mid compensation band'
                ELSE 'Entry compensation band'
            END AS compensation_band
        FROM employees
        ORDER BY salary DESC
        """,
    ).print("CASE classification")


def demonstrate_aggregates_and_grouping(connection: sqlite3.Connection) -> None:
    """
    Aggregate functions turn multiple rows into measurements.

    This extends basic SELECT/WHERE knowledge toward analytical queries:
    COUNT counts rows, AVG calculates a mean, MIN and MAX find boundaries,
    and GROUP BY creates one result group for each department.
    """
    execute_query(
        connection,
        """
        SELECT
            COUNT(*) AS employee_count,
            ROUND(AVG(salary), 2) AS average_salary,
            MIN(salary) AS minimum_salary,
            MAX(salary) AS maximum_salary
        FROM employees
        WHERE employment_status = 'Active'
        """,
    ).print("Active employee metrics")

    execute_query(
        connection,
        """
        SELECT
            department,
            COUNT(*) AS employee_count,
            ROUND(AVG(salary), 2) AS average_salary
        FROM employees
        WHERE employment_status = 'Active'
        GROUP BY department
        ORDER BY average_salary DESC
        """,
    ).print("Department-level metrics")


def demonstrate_related_tables(connection: sqlite3.Connection) -> None:
    """
    A basic query often begins with one table, but real applications need
    related information. This query joins employees to their project
    assignments while retaining the SELECT/FROM/WHERE structure.
    """
    execute_query(
        connection,
        """
        SELECT
            e.full_name,
            p.project_name,
            p.status AS project_status,
            ep.assigned_role
        FROM employees AS e
        JOIN employee_projects AS ep
            ON ep.employee_id = e.employee_id
        JOIN projects AS p
            ON p.project_id = ep.project_id
        WHERE p.status = 'Active'
        ORDER BY p.project_name, e.full_name
        """,
    ).print("Employees assigned to active projects")


def demonstrate_parameterized_queries(connection: sqlite3.Connection) -> None:
    """
    Never concatenate untrusted values directly into SQL.

    Parameter binding keeps the SQL structure separate from data. This is
    both safer and easier to reason about when values originate from forms,
    APIs, command-line input, or other external systems.
    """
    requested_department = "Engineering"
    minimum_salary = 1_000_000

    execute_query(
        connection,
        """
        SELECT full_name, department, salary
        FROM employees
        WHERE department = ?
          AND salary >= ?
        ORDER BY salary DESC
        """,
        (requested_department, minimum_salary),
    ).print("Parameterized query")


def demonstrate_dynamic_filter_safely(connection: sqlite3.Connection) -> None:
    """
    Parameter placeholders represent values, not SQL identifiers.

    When an application needs an optional filter, construct only trusted SQL
    fragments and continue to bind all user-controlled values separately.
    """
    allowed_sort_columns = {
        "name": "full_name",
        "salary": "salary",
        "experience": "years_experience",
    }

    requested_sort = "salary"
    requested_department = "Engineering"

    sort_column = allowed_sort_columns.get(requested_sort)
    if sort_column is None:
        raise ValueError("Unsupported sort option")

    sql = f"""
        SELECT full_name, department, salary, years_experience
        FROM employees
        WHERE department = ?
        ORDER BY {sort_column} DESC
    """

    execute_query(connection, sql, (requested_department,)).print(
        "Safe dynamic ordering"
    )


def demonstrate_validation(connection: sqlite3.Connection) -> None:
    """
    Application-level validation should reject malformed filter values before
    they become query parameters. SQL still validates database constraints,
    but validation can provide clearer errors to an application user.
    """
    def find_employees(minimum_salary: int) -> QueryResult:
        if not isinstance(minimum_salary, int):
            raise TypeError("minimum_salary must be an integer")
        if minimum_salary < 0:
            raise ValueError("minimum_salary cannot be negative")

        return execute_query(
            connection,
            """
            SELECT full_name, salary
            FROM employees
            WHERE salary >= ?
            ORDER BY salary DESC
            """,
            (minimum_salary,),
        )

    find_employees(1_100_000).print("Validated filter")

    try:
        find_employees(-1)
    except ValueError as exc:
        print(f"\nValidation failure handled: {exc}")


def demonstrate_transaction_failure(connection: sqlite3.Connection) -> None:
    """
    SELECT statements are read operations, but applications commonly mix
    reads with writes. A failed write should not leave partially applied
    changes. The example deliberately violates a CHECK constraint.
    """
    try:
        with connection:
            connection.execute(
                """
                INSERT INTO employees (
                    full_name, department, job_title, city,
                    salary, years_experience, employment_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "Invalid Example",
                    "Engineering",
                    "Test Role",
                    "Remote",
                    -100,
                    2,
                    "Active",
                ),
            )
    except sqlite3.IntegrityError as exc:
        print(f"\nDatabase validation failure handled: {exc}")


def demonstrate_explain_query_plan(connection: sqlite3.Connection) -> None:
    """
    EXPLAIN QUERY PLAN provides a practical way to inspect how SQLite intends
    to execute a query. It is useful when a WHERE filter becomes slow as
    data volume increases.
    """
    connection.execute(
        """
        CREATE INDEX idx_employees_department
        ON employees(department)
        """
    )

    result = execute_query(
        connection,
        """
        EXPLAIN QUERY PLAN
        SELECT full_name, salary
        FROM employees
        WHERE department = ?
          AND salary >= ?
        """,
        ("Engineering", 1_000_000),
    )
    result.print("Query plan for an indexed filter")


def demonstrate_query_boundaries(connection: sqlite3.Connection) -> None:
    """
    A useful way to reason about a SELECT statement is to separate:
    - FROM: where candidate rows come from
    - WHERE: which candidate rows survive
    - SELECT: which values are projected into the result

    The following query makes all three stages visible through its output.
    """
    execute_query(
        connection,
        """
        SELECT
            employee_id,
            full_name,
            department,
            salary,
            salary / 12.0 AS monthly_salary
        FROM employees
        WHERE department = 'Finance'
          AND employment_status = 'Active'
          AND salary > 800000
        """,
    ).print("FROM + WHERE + SELECT")


def demonstrate_edge_cases(connection: sqlite3.Connection) -> None:
    """
    Edge cases matter because SQL uses three-valued logic. A predicate can
    evaluate to TRUE, FALSE, or UNKNOWN. WHERE keeps only TRUE rows.

    The salary table has no NULL salary because salary is NOT NULL, while
    manager_id intentionally permits NULL.
    """
    execute_query(
        connection,
        """
        SELECT full_name, manager_id
        FROM employees
        WHERE NOT (manager_id IS NULL)
        """,
    ).print("NOT applied to a NULL test")

    execute_query(
        connection,
        """
        SELECT full_name, department
        FROM employees
        WHERE department NOT IN ('Engineering', 'Finance')
        ORDER BY department, full_name
        """,
    ).print("NOT IN")


def run_all_demonstrations() -> None:
    print("SQL FUNDAMENTALS")
    print("================")
    print("Database: SQLite in memory")
    print("Focus: SELECT, FROM, WHERE, and practical basic-query behavior")

    with closing(sqlite3.connect(DATABASE_NAME)) as connection:
        create_schema(connection)
        seed_data(connection)

        demonstrate_select_and_from(connection)
        demonstrate_aliases_and_expressions(connection)
        demonstrate_where_comparisons(connection)
        demonstrate_in_between_like(connection)
        demonstrate_logical_precedence(connection)
        demonstrate_null(connection)
        demonstrate_distinct(connection)
        demonstrate_order_and_limit(connection)
        demonstrate_case(connection)
        demonstrate_aggregates_and_grouping(connection)
        demonstrate_related_tables(connection)
        demonstrate_parameterized_queries(connection)
        demonstrate_dynamic_filter_safely(connection)
        demonstrate_validation(connection)
        demonstrate_transaction_failure(connection)
        demonstrate_explain_query_plan(connection)
        demonstrate_query_boundaries(connection)
        demonstrate_edge_cases(connection)

    print("\nAll SQL demonstrations completed successfully.")


if __name__ == "__main__":
    run_all_demonstrations()
