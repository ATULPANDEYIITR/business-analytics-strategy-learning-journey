# SQL Fundamentals: SELECT, FROM, WHERE and Basic Queries

## Scope

This repository develops the foundations required to read and write practical SQL queries.

The central relationship is:

`FROM` identifies the source relation, `WHERE` filters rows from that source, and `SELECT` determines the values and expressions returned to the caller.

The implementations extend that foundation with closely related query mechanisms such as aliases, calculated columns, `DISTINCT`, comparison operators, `AND` and `OR`, `IN`, `BETWEEN`, `LIKE`, `NULL` handling, `ORDER BY`, `LIMIT`, `CASE`, parameterized filtering, and basic joins.

The three implementations deliberately approach the subject differently:

- The Python program uses a real SQLite database and executes actual SQL statements.
- The JavaScript program builds a small relational query model to expose query stages through JavaScript functions and asynchronous execution.
- The C++ program treats the same ideas as a typed technical case study and models relational filtering, projection, joins, validation, and query-planning concerns with C++17 data structures.

## Relational Thinking Behind a Basic Query

A SQL query is easier to understand when the roles of its clauses are separated.

Consider the conceptual query:

`SELECT full_name, salary FROM employees WHERE department = 'Engineering';`

`FROM employees` establishes the source relation. The database considers rows from the `employees` table.

`WHERE department = 'Engineering'` evaluates a predicate against those candidate rows. Rows that do not satisfy the predicate are excluded.

`SELECT full_name, salary` projects the surviving rows into a result containing only the requested columns.

The stored table is not modified by this operation. A `SELECT` query produces a result set.

This distinction is important because a table can contain twenty columns while a particular query may expose only two. The query defines the shape of the returned result without changing the underlying schema.

## SELECT

`SELECT` controls the result columns.

A broad query such as `SELECT * FROM employees` requests every column from the source. This is convenient while inspecting a small table, but production queries generally benefit from selecting the columns that the application actually needs.

For example:

`SELECT full_name, department, salary FROM employees;`

returns three columns even though the employee table contains additional attributes.

Expressions can also be selected:

`SELECT full_name, salary / 12.0 AS monthly_salary FROM employees;`

Here `monthly_salary` is an alias for a calculated expression. The calculation belongs to the query result and does not automatically create a stored `monthly_salary` column.

Aliases are useful when database column names are not sufficiently descriptive for the consumer of the result. They are also useful for calculated values.

## FROM

`FROM` identifies the table or relational source from which the query obtains candidate rows.

For a simple query:

`SELECT full_name FROM employees;`

the source is `employees`.

For a related-data query, `FROM` can establish one table and joins can introduce related tables:

`FROM employees AS e JOIN employee_projects AS ep ON ep.employee_id = e.employee_id`

The alias `e` gives the `employees` table a shorter query-local name. It does not rename the actual database table.

The Python implementation uses real SQLite tables for employees, projects, and employee-project assignments. This makes `FROM` an actual database operation rather than a simulated collection lookup.

## WHERE

`WHERE` applies row-level filtering.

A predicate such as:

`WHERE salary >= 1000000`

keeps rows whose salary satisfies the comparison.

Common comparison operators include:

- `=` for equality
- `<>` or `!=` for inequality, depending on SQL dialect
- `>` for greater than
- `>=` for greater than or equal to
- `<` for less than
- `<=` for less than or equal to

Multiple conditions can be combined:

`WHERE department = 'Engineering' AND salary >= 1000000`

requires both conditions to be true.

An alternative condition can use `OR`:

`WHERE department = 'Finance' OR department = 'Product'`

Parentheses are important when a business rule combines `AND` and `OR`. SQL evaluates `AND` with higher precedence than `OR`, so explicit grouping makes the intended rule easier to verify.

For example:

`WHERE (department = 'Engineering' AND salary >= 1200000) OR department = 'Product'`

clearly expresses that either the Engineering rule or the Product rule should match.

## Filtering with IN

`IN` is useful when a column must match one value from a known set.

For example:

`WHERE city IN ('Mumbai', 'Bengaluru', 'Pune')`

is clearer than writing a long series of equality comparisons joined by `OR`.

The Python implementation executes an actual `IN` predicate against SQLite. The JavaScript implementation provides an `sqlIn` helper based on JavaScript membership behavior, while the C++ program uses an `unordered_set` to represent the finite collection of acceptable values.

`IN` should be distinguished from arbitrary substring matching. It tests membership in discrete values.

## Filtering with BETWEEN

`BETWEEN` represents an inclusive range.

For example:

`WHERE salary BETWEEN 800000 AND 1200000`

includes salaries equal to `800000` and `1200000`.

The Python implementation executes this predicate directly in SQLite. The JavaScript and C++ implementations explicitly model inclusive lower and upper bounds.

Range boundaries matter in reporting systems because changing `BETWEEN` to strict comparisons changes whether the boundary values are included.

## Pattern Matching with LIKE

`LIKE` is intended for pattern-based text matching.

A pattern such as:

`WHERE job_title LIKE '%Engineer%'`

matches values containing `Engineer`.

The `%` wildcard represents any sequence of characters. `_` represents a single character.

A prefix search such as:

`WHERE full_name LIKE 'A%'`

looks for values beginning with `A`.

Pattern matching has performance implications. A search beginning with `%`, such as `LIKE '%Engineer%'`, can be harder for a database engine to optimize with an ordinary index because the beginning of the stored value is unknown.

The JavaScript implementation includes a small `sqlLike` function to demonstrate the meaning of `%` and `_` without installing a database package.

## NULL Is Not an Ordinary Value

`NULL` represents a missing, unknown, or unavailable value.

It should not normally be tested with:

`WHERE manager_id = NULL`

The correct SQL form is:

`WHERE manager_id IS NULL`

and the inverse is:

`WHERE manager_id IS NOT NULL`

SQL uses three-valued logic for expressions involving `NULL`: a predicate can evaluate to true, false, or unknown. A `WHERE` clause retains rows for which the predicate is true.

This is different from treating missing data as an ordinary string such as `"None"` or a magic numeric value such as `0`.

The Python schema permits `manager_id` to be `NULL`, allowing the script to demonstrate `IS NULL` and `IS NOT NULL` against a real SQLite database.

The C++ case study uses `std::optional<int>` to model the same distinction. An empty optional represents the absence of a manager without assigning an artificial manager identifier.

## DISTINCT

`DISTINCT` removes duplicate result rows.

For example:

`SELECT DISTINCT department FROM employees;`

returns each department once.

The important detail is that distinctness applies to the selected result combination. If two columns are selected:

`SELECT DISTINCT department, city FROM employees;`

then uniqueness is evaluated across the pair `(department, city)` rather than independently for each column.

`DISTINCT` is a result-shaping operation. It does not modify the source table.

The Python implementation demonstrates both a single-column distinct result and distinct combinations of department and city. The JavaScript implementation builds distinct result objects using serialized row values. The C++ program maintains a set of already observed department names.

## ORDER BY and LIMIT

`ORDER BY` determines result ordering.

For example:

`ORDER BY salary DESC`

requests salaries from highest to lowest.

Multiple sort keys can be used when ties need deterministic ordering:

`ORDER BY salary DESC, full_name ASC`

`LIMIT` restricts the number of returned rows:

`ORDER BY salary DESC LIMIT 5`

This is useful for queries such as top-five compensation reports, but ordering should normally accompany a limiting operation when the application needs a meaningful definition of "top."

The Python implementation executes `ORDER BY` and `LIMIT` in SQLite. The JavaScript and C++ implementations explicitly sort copies of the filtered data before restricting the result size.

## CASE Expressions

`CASE` provides conditional result logic.

The Python implementation classifies employees according to salary:

`CASE WHEN salary >= 1300000 THEN 'Senior compensation band' WHEN salary >= 900000 THEN 'Mid compensation band' ELSE 'Entry compensation band' END`

This is different from `WHERE`.

`WHERE` decides whether a row remains in the result.

`CASE` can assign a calculated value to a row that has already been selected.

That distinction is useful when a report needs all employees but also needs each employee labeled according to a business rule.

## Aggregate Queries and GROUP BY

Basic row retrieval naturally leads to analytical queries.

The Python implementation includes:

`COUNT(*)`

`AVG(salary)`

`MIN(salary)`

`MAX(salary)`

and a grouped department query.

For example:

`SELECT department, COUNT(*) AS employee_count FROM employees GROUP BY department;`

changes the granularity of the result. Instead of one result row per employee, the query produces one result row per department.

`WHERE` remains a row-level filter. It is applied before grouping in the logical query-processing model.

This distinction becomes important when moving from basic retrieval to reporting queries.

## JOINs and Related Tables

Real databases frequently separate related information into multiple tables.

The sample schema contains:

- `employees`, which stores employee attributes
- `projects`, which stores project attributes
- `employee_projects`, which connects employees to projects

A join can retrieve related information:

`SELECT e.full_name, p.project_name, ep.assigned_role FROM employees AS e JOIN employee_projects AS ep ON ep.employee_id = e.employee_id JOIN projects AS p ON p.project_id = ep.project_id WHERE p.status = 'Active';`

The query uses `FROM` to establish the relational source and joins to expand that source with related records.

The `WHERE` condition then restricts the joined result to active projects.

This is an extension of the same core model rather than a replacement for it: source rows are established, conditions filter them, and `SELECT` determines what is returned.

## Python Implementation

The Python program uses the standard-library `sqlite3` module, so it executes real SQL without requiring an external package.

The database is created in memory. This keeps the example self-contained while still providing genuine SQL parsing, execution, constraints, filtering, grouping, joins, and query planning.

The `employees` table contains realistic fields such as department, job title, city, salary, experience, employment status, and an optional manager relationship.

The Python program demonstrates:

- `SELECT *` and explicit column projection
- aliases such as `AS employee`
- calculated salary expressions
- `WHERE` comparisons
- `AND` and `OR`
- explicit logical grouping
- `IN`
- `BETWEEN`
- `LIKE`
- `IS NULL` and `IS NOT NULL`
- `DISTINCT`
- `ORDER BY`
- `LIMIT`
- `CASE`
- aggregate functions
- `GROUP BY`
- joins across employee and project tables
- parameterized SQL using `?` placeholders
- safe dynamic ordering through an allow-list
- application-side validation
- database constraint failure handling
- `EXPLAIN QUERY PLAN`
- edge-case demonstrations

The `execute_query` helper keeps SQL execution and result formatting separate. Exceptions from SQLite are converted into a clear application-level error while retaining the original exception as the cause.

The parameterized query example is particularly important for production code. A value such as `"Engineering"` is passed separately from the SQL statement. It is not interpolated into the SQL string.

The dynamic ordering example demonstrates a different problem: SQL parameters represent values, not identifiers. A column name therefore should not be accepted as arbitrary SQL text. The program maps permitted user-facing sort choices to fixed column names before constructing the query.

## JavaScript Implementation

The JavaScript file takes a complementary approach instead of translating the Python SQL statements line by line.

It represents relational rows as JavaScript objects and exposes query-like operations through functions:

`where()` models row filtering.

`projectRows()` models the projection performed by `SELECT`.

`distinct()` models duplicate elimination.

`orderBy()` models result ordering.

`limit()` models result-size restriction.

`sqlLike()` demonstrates SQL wildcard semantics.

`sqlIn()` models membership filtering.

`sqlBetween()` models inclusive range filtering.

This design makes the conceptual relationship between `FROM`, `WHERE`, and `SELECT` visible in executable JavaScript.

The JavaScript version also demonstrates application concerns that commonly surround SQL queries in Node.js:

- validation of filter values
- allow-listing dynamic sort choices
- explicit missing-value handling
- asynchronous execution through a Promise-based query executor
- error propagation through `try`/`catch`
- relationship traversal for employee-project data

The asynchronous example is intentionally small because the purpose is not to implement a database driver. It demonstrates the application-level shape used when a real Node.js database operation waits for I/O.

The JavaScript file can be executed with Node.js without npm dependencies.

## C++ Case Study

The C++ program presents a typed technical case study for an employee compensation and project reporting system.

The central case is a request for active Engineering employees whose salary is at least one million units.

The modeled query is conceptually:

`SELECT name, title, salary, salary / 12 FROM employees WHERE department = 'Engineering' AND status = 'Active' AND salary >= 1000000;`

The C++ implementation separates the stages rather than treating the query as one opaque operation.

The employee vector acts as the source relation.

`selectFrom()` applies a predicate and models the filtering role of `WHERE`.

`projectEmployees()` selects the fields required by the report and calculates monthly salary, modeling the projection role of `SELECT`.

The case study then connects employee assignments to active projects, modeling a join across related entities.

The C++ representation uses `std::optional<int>` for `managerId`. This avoids the common modeling error of using an arbitrary integer as a replacement for SQL `NULL`.

The implementation also uses:

- `std::vector` for ordered collections of rows
- `std::unordered_set` for membership and distinct-value tracking
- `std::find_if` for relationship lookup
- `std::sort` for ordered result generation
- `std::optional` for missing relational values
- lambdas for row predicates
- exception handling for invalid query parameters

The program validates the department and salary filter before executing the case-study query. Negative salary thresholds are rejected at the application boundary.

## Query Parameters and Security

A common application mistake is constructing SQL by directly concatenating user input.

Unsafe construction conceptually resembles:

`SELECT ... FROM employees WHERE department = '` followed by arbitrary input and then another SQL fragment.

This makes data capable of changing the structure of the SQL statement.

Parameterized queries separate SQL structure from values.

The Python program demonstrates:

`WHERE department = ? AND salary >= ?`

with the values supplied separately.

A real application should use the parameter-binding mechanism provided by its database driver.

Dynamic identifiers require a separate approach. A placeholder generally cannot be used to safely turn arbitrary text into a table or column identifier. For options such as sorting, applications should map user choices to a fixed set of permitted identifiers.

The Python and JavaScript implementations both demonstrate this allow-listing pattern.

Security is therefore not only about the SQL text itself. It also involves controlling which query structures the application permits users to select.

## Validation and Failure Conditions

SQL syntax errors and application validation errors are different failure categories.

An application can reject an invalid salary threshold before contacting the database.

The database can reject data that violates a schema constraint.

The SQL engine can reject malformed query syntax.

A production application should preserve these distinctions because they affect error reporting, logging, retry behavior, and debugging.

The Python example includes a database `CHECK` constraint requiring salary to be positive. An intentionally invalid insert demonstrates how a database-level constraint failure is surfaced.

The JavaScript implementation validates the expected types and allowed sort options before performing its simulated query.

The C++ implementation throws `std::invalid_argument` when query parameters do not satisfy application-level requirements.

## Performance Considerations

Basic queries can become expensive as table sizes increase.

A `WHERE` condition does not guarantee that every row will be inspected. The database optimizer can use indexes and other access strategies when appropriate.

The Python program creates an index on `employees(department)` and uses `EXPLAIN QUERY PLAN` to inspect the resulting execution strategy.

Index design should be based on actual workload patterns. An index can accelerate reads but also consumes storage and introduces maintenance work during inserts, updates, and deletes.

Selecting only the required columns can reduce result size. This becomes especially significant when rows contain large text or binary fields.

Pattern matching also deserves attention. A predicate such as `LIKE '%Engineer%'` generally has fewer opportunities for an ordinary prefix index than a prefix pattern such as `LIKE 'Engineer%'`.

The most appropriate optimization should be confirmed through query plans and measurements rather than assumed from SQL syntax alone.

## Common Query Mistakes

### Confusing `SELECT` with filtering

`SELECT` chooses returned expressions. `WHERE` decides which source rows qualify.

Changing:

`SELECT full_name, salary`

to:

`SELECT full_name`

does not filter employees. It only changes the result columns.

### Using `SELECT *` everywhere

`SELECT *` can expose columns that the application does not need and can make result contracts unstable when schemas evolve.

Explicit columns make the intended result shape clearer.

### Comparing NULL with equality

`manager_id = NULL` is not the correct SQL test for a missing manager.

Use `manager_id IS NULL`.

### Forgetting logical grouping

A query containing both `AND` and `OR` can produce a broader result than intended if precedence is misunderstood.

Parentheses should express business rules explicitly when a condition contains multiple logical branches.

### Treating BETWEEN as exclusive

`BETWEEN 800000 AND 1200000` includes both endpoints.

Applications that need exclusive boundaries should express those boundaries explicitly.

### Treating LIKE as equality

`=` checks a value for equality.

`LIKE` performs pattern matching and interprets wildcard characters.

### Injecting dynamic identifiers

A column name should not be inserted into SQL directly from untrusted input. Map application choices to a fixed allow-list.

## Practical Query Workflow

A reliable way to construct a basic query is to identify the source relation first.

Start with the required table in `FROM`.

Determine the rows that should qualify and express those conditions in `WHERE`.

Determine exactly which values the caller needs and express them in `SELECT`.

Add aliases when result names need clarification.

Add `ORDER BY` when the result requires deterministic ordering.

Add `LIMIT` only when the desired result size is defined.

Use `DISTINCT` when duplicate result combinations are genuinely unwanted rather than as a generic way to hide a query-design problem.

Use joins when required information resides in related tables.

Use parameters for external values.

Check edge cases such as `NULL`, empty result sets, boundary values, and unexpected filter values.

## Production Considerations

A production SQL layer should make query behavior explicit and testable.

Important concerns include:

- Parameter binding for externally supplied values.
- Explicit column selection instead of unnecessarily broad projections.
- Input validation before query execution.
- Appropriate indexes for frequently filtered columns.
- Query-plan inspection for slow queries.
- Clear handling of `NULL`.
- Deterministic ordering when consumers depend on result order.
- Controlled dynamic identifiers through allow-lists.
- Appropriate database permissions so an application account cannot perform operations it does not need.
- Logging that captures useful query context without exposing passwords, tokens, or sensitive parameter values.
- Tests for empty results, boundary conditions, missing values, and combinations of `AND` and `OR`.

The core concepts remain simple, but production reliability depends on applying them precisely.

## File Structure

The repository can contain the three implementations as:

`sql_fundamentals.py`

`sql_fundamentals.js`

`sql_fundamentals.cpp`

`README.md`

The Python file is the only implementation that requires an actual SQL engine, and it uses SQLite from Python's standard library. The JavaScript and C++ files use self-contained relational models to expose the same query concepts from different programming perspectives.

## Running the Implementations

Run the Python implementation with:

`python sql_fundamentals.py`

Run the JavaScript implementation with:

`node sql_fundamentals.js`

Compile and run the C++ implementation with a C++17-compatible compiler:

`g++ -std=c++17 -Wall -Wextra -pedantic sql_fundamentals.cpp -o sql_fundamentals`

Then execute the compiled program using the platform's normal executable invocation.

The Python program demonstrates genuine SQL execution. The JavaScript and C++ programs deliberately model relational behavior so that the mechanics of filtering, projection, membership, ordering, missing values, and relationships remain visible without requiring additional database libraries.
