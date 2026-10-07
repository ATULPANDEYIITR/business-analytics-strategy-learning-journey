"""
SQL JOIN Laboratory
===================

A self-contained Python simulation of INNER, LEFT, RIGHT, and FULL joins.

The implementation uses in-memory tables represented as lists of dictionaries.
It deliberately models SQL join semantics rather than merely demonstrating
Python list operations.

The examples use a repository-development dataset so the join behavior can be
observed against realistic entities:

    developers
    pull_requests
    reviews

The core join implementation supports:
    INNER JOIN
    LEFT JOIN
    RIGHT JOIN
    FULL OUTER JOIN

The script also demonstrates:
    - duplicate matching rows
    - NULL-like missing values
    - composite join keys
    - filtering after joins
    - outer-join preservation
    - anti-join style analysis
    - validation and failure cases
    - performance characteristics
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Iterable


NULL = None
Row = dict[str, Any]
Predicate = Callable[[Row, Row], bool]


def print_title(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_table(rows: list[Row], columns: list[str] | None = None) -> None:
    if not rows:
        print("(no rows)")
        return

    if columns is None:
        columns = list(dict.fromkeys(key for row in rows for key in row))

    widths = {
        column: max(
            len(column),
            max(
                (len(str(row.get(column, ""))) for row in rows),
                default=0,
            ),
        )
        for column in columns
    }

    header = " | ".join(column.ljust(widths[column]) for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(separator)

    for row in rows:
        print(
            " | ".join(
                str(row.get(column, "")).ljust(widths[column])
                for column in columns
            )
        )


def validate_table(rows: Iterable[Row], name: str) -> None:
    if not isinstance(rows, Iterable):
        raise TypeError(f"{name} must be an iterable of row dictionaries")

    for position, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(
                f"{name}[{position}] must be a dictionary, got {type(row).__name__}"
            )


def prefixed_row(row: Row | None, prefix: str, columns: list[str]) -> Row:
    """
    Prefix columns so that columns with identical names from both tables do not
    silently overwrite each other.

    SQL clients normally expose table-qualified columns when ambiguity exists.
    This simulation makes that behavior explicit.
    """
    if row is None:
        return {f"{prefix}.{column}": NULL for column in columns}

    return {f"{prefix}.{column}": row.get(column, NULL) for column in columns}


def merge_rows(
    left: Row | None,
    right: Row | None,
    left_columns: list[str],
    right_columns: list[str],
) -> Row:
    result = {}
    result.update(prefixed_row(left, "left", left_columns))
    result.update(prefixed_row(right, "right", right_columns))
    return result


def sql_equals(left_value: Any, right_value: Any) -> bool:
    """
    SQL equality is not TRUE when either operand is NULL.

    For ordinary equality joins:
        10 = 10 -> TRUE
        10 = 20 -> FALSE
        NULL = 10 -> UNKNOWN
        NULL = NULL -> UNKNOWN

    A WHERE/JOIN predicate retains a row only when the result is TRUE, so the
    Python representation treats NULL comparisons as non-matches.
    """
    if left_value is NULL or right_value is NULL:
        return False
    return left_value == right_value


def nested_loop_join(
    left: list[Row],
    right: list[Row],
    key: str,
    join_type: str,
) -> list[Row]:
    """
    Reference implementation using the conceptual nested-loop algorithm.

    For every left row, every right row is examined. This closely mirrors the
    logical definition of a join and is useful for understanding semantics.

    Complexity:
        O(len(left) * len(right))

    It is intentionally not the fastest implementation.
    """
    validate_table(left, "left")
    validate_table(right, "right")

    if not key:
        raise ValueError("Join key cannot be empty")

    allowed = {"INNER", "LEFT", "RIGHT", "FULL"}
    normalized_type = join_type.upper()

    if normalized_type not in allowed:
        raise ValueError(
            f"Unsupported join type {join_type!r}; expected one of {sorted(allowed)}"
        )

    left_columns = list(dict.fromkeys(key for row in left for key in row))
    right_columns = list(dict.fromkeys(key for row in right for key in row))

    results: list[Row] = []
    matched_right_indexes: set[int] = set()

    for left_row in left:
        matched = False

        for right_index, right_row in enumerate(right):
            if sql_equals(left_row.get(key), right_row.get(key)):
                matched = True
                matched_right_indexes.add(right_index)
                results.append(
                    merge_rows(
                        left_row,
                        right_row,
                        left_columns,
                        right_columns,
                    )
                )

        if not matched and normalized_type in {"LEFT", "FULL"}:
            results.append(
                merge_rows(
                    left_row,
                    None,
                    left_columns,
                    right_columns,
                )
            )

    if normalized_type in {"RIGHT", "FULL"}:
        for right_index, right_row in enumerate(right):
            if right_index not in matched_right_indexes:
                results.append(
                    merge_rows(
                        None,
                        right_row,
                        left_columns,
                        right_columns,
                    )
                )

    return results


def indexed_join(
    left: list[Row],
    right: list[Row],
    key: str,
    join_type: str,
) -> list[Row]:
    """
    Hash-indexed implementation.

    An index is built for the right table. Matching rows can then be found
    without scanning the entire right table for every left row.

    Average-case complexity:
        O(L + R + M)

    where M is the number of produced matching rows.

    This is a useful conceptual model for why database engines can execute
    equality joins efficiently with hash-join strategies.
    """
    validate_table(left, "left")
    validate_table(right, "right")

    normalized_type = join_type.upper()
    if normalized_type not in {"INNER", "LEFT", "RIGHT", "FULL"}:
        raise ValueError(f"Unsupported join type: {join_type}")

    left_columns = list(dict.fromkeys(key for row in left for key in row))
    right_columns = list(dict.fromkeys(key for row in right for key in row))

    right_index: dict[Any, list[tuple[int, Row]]] = defaultdict(list)

    for right_index_position, right_row in enumerate(right):
        value = right_row.get(key)
        if value is not NULL:
            right_index[value].append((right_index_position, right_row))

    matched_right_indexes: set[int] = set()
    results: list[Row] = []

    for left_row in left:
        value = left_row.get(key)
        matches = [] if value is NULL else right_index.get(value, [])

        if matches:
            for right_position, right_row in matches:
                matched_right_indexes.add(right_position)
                results.append(
                    merge_rows(
                        left_row,
                        right_row,
                        left_columns,
                        right_columns,
                    )
                )
        elif normalized_type in {"LEFT", "FULL"}:
            results.append(
                merge_rows(
                    left_row,
                    None,
                    left_columns,
                    right_columns,
                )
            )

    if normalized_type in {"RIGHT", "FULL"}:
        for position, right_row in enumerate(right):
            if position not in matched_right_indexes:
                results.append(
                    merge_rows(
                        None,
                        right_row,
                        left_columns,
                        right_columns,
                    )
                )

    return results


def join_with_predicate(
    left: list[Row],
    right: list[Row],
    predicate: Predicate,
    join_type: str,
) -> list[Row]:
    """
    General join where the match condition is a Python predicate.

    This represents SQL's ON condition more directly than a single-key join.
    """
    left_columns = list(dict.fromkeys(key for row in left for key in row))
    right_columns = list(dict.fromkeys(key for row in right for key in row))

    normalized_type = join_type.upper()
    if normalized_type not in {"INNER", "LEFT", "RIGHT", "FULL"}:
        raise ValueError(f"Unsupported join type: {join_type}")

    results: list[Row] = []
    matched_right: set[int] = set()

    for left_row in left:
        matched = False

        for right_position, right_row in enumerate(right):
            if predicate(left_row, right_row):
                matched = True
                matched_right.add(right_position)
                results.append(
                    merge_rows(
                        left_row,
                        right_row,
                        left_columns,
                        right_columns,
                    )
                )

        if not matched and normalized_type in {"LEFT", "FULL"}:
            results.append(
                merge_rows(
                    left_row,
                    None,
                    left_columns,
                    right_columns,
                )
            )

    if normalized_type in {"RIGHT", "FULL"}:
        for position, right_row in enumerate(right):
            if position not in matched_right:
                results.append(
                    merge_rows(
                        None,
                        right_row,
                        left_columns,
                        right_columns,
                    )
                )

    return results


def rows_where(rows: list[Row], predicate: Callable[[Row], bool]) -> list[Row]:
    return [row for row in rows if predicate(row)]


def demonstrate_basic_join_semantics() -> None:
    print_title("INNER, LEFT, RIGHT, and FULL JOIN semantics")

    developers = [
        {"developer_id": 1, "name": "Asha", "team": "Platform"},
        {"developer_id": 2, "name": "Rahul", "team": "Payments"},
        {"developer_id": 3, "name": "Maya", "team": "Security"},
        {"developer_id": 4, "name": "Daniel", "team": "Data"},
    ]

    pull_requests = [
        {"developer_id": 1, "pr_id": 101, "title": "Improve API caching"},
        {"developer_id": 1, "pr_id": 102, "title": "Add cache metrics"},
        {"developer_id": 2, "pr_id": 103, "title": "Validate payment amount"},
        {"developer_id": 9, "pr_id": 104, "title": "External contributor fix"},
    ]

    columns = [
        "left.developer_id",
        "left.name",
        "left.team",
        "right.developer_id",
        "right.pr_id",
        "right.title",
    ]

    for join_type in ("INNER", "LEFT", "RIGHT", "FULL"):
        print(f"\n{join_type} JOIN")
        result = nested_loop_join(
            developers,
            pull_requests,
            "developer_id",
            join_type,
        )
        print_table(result, columns)


def demonstrate_outer_join_analysis() -> None:
    print_title("Outer joins preserve unmatched rows")

    developers = [
        {"developer_id": 1, "name": "Asha"},
        {"developer_id": 2, "name": "Rahul"},
        {"developer_id": 3, "name": "Maya"},
    ]

    reviews = [
        {"developer_id": 1, "review_id": 501, "state": "APPROVED"},
        {"developer_id": 1, "review_id": 502, "state": "CHANGES_REQUESTED"},
        {"developer_id": 7, "review_id": 503, "state": "APPROVED"},
    ]

    left_join = indexed_join(
        developers,
        reviews,
        "developer_id",
        "LEFT",
    )

    print("All developers, including developers without reviews:")
    print_table(
        left_join,
        [
            "left.developer_id",
            "left.name",
            "right.review_id",
            "right.state",
        ],
    )

    without_reviews = [
        row
        for row in left_join
        if row["right.review_id"] is NULL
    ]

    print("\nDevelopers with no matching review:")
    print_table(
        without_reviews,
        [
            "left.developer_id",
            "left.name",
            "right.review_id",
            "right.state",
        ],
    )

    right_join = indexed_join(
        developers,
        reviews,
        "developer_id",
        "RIGHT",
    )

    print("\nAll reviews, including reviews whose developer is absent:")
    print_table(
        right_join,
        [
            "left.developer_id",
            "left.name",
            "right.review_id",
            "right.state",
        ],
    )

    full_join = indexed_join(
        developers,
        reviews,
        "developer_id",
        "FULL",
    )

    print("\nFULL JOIN exposes unmatched rows on either side:")
    print_table(
        full_join,
        [
            "left.developer_id",
            "left.name",
            "right.review_id",
            "right.state",
        ],
    )


def demonstrate_duplicates() -> None:
    print_title("Duplicate matches and row multiplication")

    teams = [
        {"team_id": 10, "team_name": "Platform"},
        {"team_id": 20, "team_name": "Security"},
    ]

    pull_requests = [
        {"pr_id": 1001, "team_id": 10, "title": "Caching"},
        {"pr_id": 1002, "team_id": 10, "title": "Tracing"},
        {"pr_id": 1003, "team_id": 10, "title": "Metrics"},
        {"pr_id": 1004, "team_id": 20, "title": "Hardening"},
    ]

    result = indexed_join(
        teams,
        pull_requests,
        "team_id",
        "INNER",
    )

    print(
        "One team can match multiple pull requests. "
        "The join therefore returns multiple rows for that team."
    )
    print_table(
        result,
        [
            "left.team_id",
            "left.team_name",
            "right.pr_id",
            "right.title",
        ],
    )


def demonstrate_null_behavior() -> None:
    print_title("NULL join-key behavior")

    left = [
        {"customer_id": 1, "customer": "Customer A"},
        {"customer_id": 2, "customer": "Customer B"},
        {"customer_id": None, "customer": "Unknown Customer"},
    ]

    right = [
        {"customer_id": 1, "invoice_id": 9001},
        {"customer_id": None, "invoice_id": 9002},
    ]

    result = indexed_join(left, right, "customer_id", "FULL")

    print(
        "SQL equality does not match NULL to NULL. "
        "The two NULL-key rows remain unmatched."
    )

    print_table(
        result,
        [
            "left.customer_id",
            "left.customer",
            "right.customer_id",
            "right.invoice_id",
        ],
    )


def demonstrate_composite_join() -> None:
    print_title("Composite-key join")

    employees = [
        {"employee_id": 1, "department": "IT", "region": "IN", "name": "Asha"},
        {"employee_id": 2, "department": "IT", "region": "US", "name": "Rahul"},
        {"employee_id": 3, "department": "HR", "region": "IN", "name": "Maya"},
    ]

    permissions = [
        {"department": "IT", "region": "IN", "permission": "DEPLOY"},
        {"department": "IT", "region": "US", "permission": "READ"},
        {"department": "IT", "region": "IN", "permission": "READ"},
    ]

    result = join_with_predicate(
        employees,
        permissions,
        lambda employee, permission: (
            sql_equals(employee.get("department"), permission.get("department"))
            and sql_equals(employee.get("region"), permission.get("region"))
        ),
        "LEFT",
    )

    print(
        "Both department and region participate in the match. "
        "A match on only one component is insufficient."
    )
    print_table(
        result,
        [
            "left.employee_id",
            "left.name",
            "left.department",
            "left.region",
            "right.permission",
        ],
    )


def demonstrate_on_vs_where_behavior() -> None:
    print_title("ON condition versus post-join filtering")

    developers = [
        {"developer_id": 1, "name": "Asha"},
        {"developer_id": 2, "name": "Rahul"},
        {"developer_id": 3, "name": "Maya"},
    ]

    reviews = [
        {"developer_id": 1, "review_id": 701, "state": "APPROVED"},
        {"developer_id": 1, "review_id": 702, "state": "CHANGES_REQUESTED"},
        {"developer_id": 2, "review_id": 703, "state": "COMMENTED"},
    ]

    all_reviews = indexed_join(
        developers,
        reviews,
        "developer_id",
        "LEFT",
    )

    approved_after_join = rows_where(
        all_reviews,
        lambda row: row["right.state"] == "APPROVED",
    )

    print(
        "Filtering the completed LEFT JOIN with WHERE right.state = APPROVED "
        "removes developers that have no approved review."
    )
    print_table(
        approved_after_join,
        [
            "left.developer_id",
            "left.name",
            "right.review_id",
            "right.state",
        ],
    )

    approved_only_predicate = join_with_predicate(
        developers,
        reviews,
        lambda developer, review: (
            sql_equals(
                developer.get("developer_id"),
                review.get("developer_id"),
            )
            and review.get("state") == "APPROVED"
        ),
        "LEFT",
    )

    print(
        "\nApplying the review-state restriction as part of the JOIN condition "
        "preserves developers without an approved review."
    )
    print_table(
        approved_only_predicate,
        [
            "left.developer_id",
            "left.name",
            "right.review_id",
            "right.state",
        ],
    )


@dataclass(frozen=True)
class JoinScenario:
    name: str
    left_count: int
    right_count: int
    join_type: str
    expected_property: str


def validate_join_scenario(
    scenario: JoinScenario,
    left: list[Row],
    right: list[Row],
    result: list[Row],
) -> bool:
    """
    Lightweight semantic assertions.

    These checks are intentionally about join behavior rather than testing
    implementation internals.
    """
    if scenario.join_type == "INNER":
        return len(result) <= scenario.left_count * scenario.right_count

    if scenario.join_type == "LEFT":
        return len(result) >= scenario.left_count

    if scenario.join_type == "RIGHT":
        return len(result) >= scenario.right_count

    if scenario.join_type == "FULL":
        return len(result) >= max(scenario.left_count, scenario.right_count)

    return False


def demonstrate_validation_and_failures() -> None:
    print_title("Validation and failure conditions")

    examples = [
        ("missing key", [{"id": 1}], [{"id": 1}], ""),
        ("invalid join type", [{"id": 1}], [{"id": 1}], "CROSS"),
        ("non-dictionary row", [{"id": 1}, "invalid"], [{"id": 1}], "INNER"),
    ]

    for description, left, right, join_type in examples:
        try:
            if description == "missing key":
                indexed_join(left, right, "missing", "INNER")
            elif description == "invalid join type":
                indexed_join(left, right, "id", join_type)
            else:
                indexed_join(left, right, "id", join_type)

        except (KeyError, TypeError, ValueError) as exc:
            print(f"{description}: rejected safely -> {exc}")


def demonstrate_case_sensitive_values() -> None:
    print_title("Join values are compared according to the chosen equality rule")

    left = [
        {"code": "ABC", "description": "Uppercase code"},
        {"code": "xyz", "description": "Lowercase code"},
    ]

    right = [
        {"code": "abc", "value": 10},
        {"code": "xyz", "value": 20},
    ]

    case_sensitive = indexed_join(left, right, "code", "INNER")

    print("Default equality is case-sensitive:")
    print_table(
        case_sensitive,
        [
            "left.code",
            "left.description",
            "right.code",
            "right.value",
        ],
    )

    case_insensitive = join_with_predicate(
        left,
        right,
        lambda l, r: (
            l.get("code") is not NULL
            and r.get("code") is not NULL
            and str(l["code"]).casefold() == str(r["code"]).casefold()
        ),
        "INNER",
    )

    print("\nA deliberately case-insensitive predicate changes the join semantics:")
    print_table(
        case_insensitive,
        [
            "left.code",
            "left.description",
            "right.code",
            "right.value",
        ],
    )


def demonstrate_realistic_repository_workflow() -> None:
    print_title("Repository governance join analysis")

    repositories = [
        {"repository_id": 1, "name": "payments-api", "protected_branch": "main"},
        {"repository_id": 2, "name": "identity-service", "protected_branch": "main"},
        {"repository_id": 3, "name": "analytics-engine", "protected_branch": "main"},
    ]

    pull_requests = [
        {"repository_id": 1, "pr_id": 100, "status": "OPEN"},
        {"repository_id": 1, "pr_id": 101, "status": "MERGED"},
        {"repository_id": 2, "pr_id": 102, "status": "OPEN"},
        {"repository_id": 9, "pr_id": 103, "status": "OPEN"},
    ]

    branch_policies = [
        {"repository_id": 1, "required_reviews": 2, "require_ci": True},
        {"repository_id": 2, "required_reviews": 1, "require_ci": True},
        {"repository_id": 4, "required_reviews": 3, "require_ci": True},
    ]

    repository_prs = indexed_join(
        repositories,
        pull_requests,
        "repository_id",
        "LEFT",
    )

    governance_view = join_with_predicate(
        repository_prs,
        branch_policies,
        lambda row, policy: sql_equals(
            row.get("left.repository_id"),
            policy.get("repository_id"),
        ),
        "LEFT",
    )

    print(
        "The first LEFT JOIN preserves repositories without pull requests. "
        "The second LEFT JOIN preserves repositories without a matching policy."
    )

    print_table(
        governance_view,
        [
            "left.left.repository_id",
            "left.left.name",
            "left.right.pr_id",
            "left.right.status",
            "right.required_reviews",
            "right.require_ci",
        ],
    )


def demonstrate_performance_model() -> None:
    print_title("Join algorithm and performance model")

    left = [{"id": index, "value": f"L{index}"} for index in range(1, 1001)]
    right = [{"id": index, "value": f"R{index}"} for index in range(500, 1501)]

    print(
        f"Left rows: {len(left)}, right rows: {len(right)}"
    )

    nested = nested_loop_join(left, right, "id", "INNER")
    indexed = indexed_join(left, right, "id", "INNER")

    print(f"Nested-loop result rows: {len(nested)}")
    print(f"Indexed result rows: {len(indexed)}")
    print(
        "Both implementations produce the same matching cardinality, "
        "while the indexed implementation avoids comparing every possible pair."
    )


def run_semantic_assertions() -> None:
    print_title("Semantic assertions")

    left = [{"id": 1}, {"id": 2}, {"id": 3}]
    right = [{"id": 2}, {"id": 3}, {"id": 4}]

    expected = {
        "INNER": 2,
        "LEFT": 3,
        "RIGHT": 3,
        "FULL": 4,
    }

    for join_type, expected_count in expected.items():
        result = indexed_join(left, right, "id", join_type)
        actual = len(result)

        if actual != expected_count:
            raise AssertionError(
                f"{join_type} expected {expected_count} rows, got {actual}"
            )

        print(f"{join_type}: {actual} rows as expected")

    print("All join-semantic assertions passed.")


def main() -> None:
    demonstrate_basic_join_semantics()
    demonstrate_outer_join_analysis()
    demonstrate_duplicates()
    demonstrate_null_behavior()
    demonstrate_composite_join()
    demonstrate_on_vs_where_behavior()
    demonstrate_validation_and_failures()
    demonstrate_case_sensitive_values()
    demonstrate_realistic_repository_workflow()
    demonstrate_performance_model()
    run_semantic_assertions()


if __name__ == "__main__":
    main()
