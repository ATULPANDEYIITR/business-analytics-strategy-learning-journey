'use strict';

/*
 * SQL JOIN Laboratory in JavaScript
 *
 * This file models INNER, LEFT, RIGHT, and FULL joins using JavaScript
 * collections. It focuses on join-specific behavior instead of presenting
 * generic JavaScript syntax.
 *
 * The event-driven portion models a repository governance workflow in which
 * repositories, pull requests, reviews, and branch policies arrive as
 * events.
 *
 * No external packages are required.
 */

const NULL = null;

function heading(title) {
    console.log(`\n${'='.repeat(78)}\n${title}\n${'='.repeat(78)}`);
}

function validateRows(rows, name) {
    if (!Array.isArray(rows)) {
        throw new TypeError(`${name} must be an array`);
    }

    rows.forEach((row, index) => {
        if (row === null || typeof row !== 'object' || Array.isArray(row)) {
            throw new TypeError(`${name}[${index}] must be an object`);
        }
    });
}

function columnsOf(rows) {
    return [...new Set(rows.flatMap(row => Object.keys(row)))];
}

function prefixedRow(row, prefix, columns) {
    const result = {};

    for (const column of columns) {
        result[`${prefix}.${column}`] =
            row === null || row === undefined
                ? NULL
                : Object.prototype.hasOwnProperty.call(row, column)
                    ? row[column]
                    : NULL;
    }

    return result;
}

function mergeRows(left, right, leftColumns, rightColumns) {
    return {
        ...prefixedRow(left, 'left', leftColumns),
        ...prefixedRow(right, 'right', rightColumns)
    };
}

function sqlEquals(leftValue, rightValue) {
    // SQL's NULL = NULL does not evaluate to TRUE. It evaluates to UNKNOWN.
    // A join predicate requires TRUE for a match.
    if (leftValue === NULL || rightValue === NULL) {
        return false;
    }

    return leftValue === rightValue;
}

function nestedLoopJoin(left, right, key, joinType) {
    validateRows(left, 'left');
    validateRows(right, 'right');

    const normalizedType = joinType.toUpperCase();

    if (!['INNER', 'LEFT', 'RIGHT', 'FULL'].includes(normalizedType)) {
        throw new Error(`Unsupported join type: ${joinType}`);
    }

    if (!key) {
        throw new Error('A join key is required');
    }

    const leftColumns = columnsOf(left);
    const rightColumns = columnsOf(right);
    const result = [];
    const matchedRight = new Set();

    for (const leftRow of left) {
        let matched = false;

        right.forEach((rightRow, rightIndex) => {
            if (sqlEquals(leftRow[key], rightRow[key])) {
                matched = true;
                matchedRight.add(rightIndex);

                result.push(
                    mergeRows(
                        leftRow,
                        rightRow,
                        leftColumns,
                        rightColumns
                    )
                );
            }
        });

        if (!matched && ['LEFT', 'FULL'].includes(normalizedType)) {
            result.push(
                mergeRows(
                    leftRow,
                    null,
                    leftColumns,
                    rightColumns
                )
            );
        }
    }

    if (['RIGHT', 'FULL'].includes(normalizedType)) {
        right.forEach((rightRow, rightIndex) => {
            if (!matchedRight.has(rightIndex)) {
                result.push(
                    mergeRows(
                        null,
                        rightRow,
                        leftColumns,
                        rightColumns
                    )
                );
            }
        });
    }

    return result;
}

function hashJoin(left, right, key, joinType) {
    /*
     * Build an index on the right side. A Map preserves multiple matching
     * rows, which is essential because a SQL join is not a dictionary lookup.
     * One key can correspond to many rows.
     */
    validateRows(left, 'left');
    validateRows(right, 'right');

    const normalizedType = joinType.toUpperCase();

    if (!['INNER', 'LEFT', 'RIGHT', 'FULL'].includes(normalizedType)) {
        throw new Error(`Unsupported join type: ${joinType}`);
    }

    const leftColumns = columnsOf(left);
    const rightColumns = columnsOf(right);
    const index = new Map();
    const matchedRight = new Set();
    const result = [];

    right.forEach((row, indexPosition) => {
        const value = row[key];

        if (value === NULL) {
            return;
        }

        if (!index.has(value)) {
            index.set(value, []);
        }

        index.get(value).push({ row, indexPosition });
    });

    for (const leftRow of left) {
        const value = leftRow[key];
        const matches = value === NULL ? [] : (index.get(value) || []);

        if (matches.length === 0) {
            if (['LEFT', 'FULL'].includes(normalizedType)) {
                result.push(
                    mergeRows(
                        leftRow,
                        null,
                        leftColumns,
                        rightColumns
                    )
                );
            }

            continue;
        }

        for (const match of matches) {
            matchedRight.add(match.indexPosition);

            result.push(
                mergeRows(
                    leftRow,
                    match.row,
                    leftColumns,
                    rightColumns
                )
            );
        }
    }

    if (['RIGHT', 'FULL'].includes(normalizedType)) {
        right.forEach((rightRow, indexPosition) => {
            if (!matchedRight.has(indexPosition)) {
                result.push(
                    mergeRows(
                        null,
                        rightRow,
                        leftColumns,
                        rightColumns
                    )
                );
            }
        });
    }

    return result;
}

function predicateJoin(left, right, predicate, joinType) {
    const normalizedType = joinType.toUpperCase();

    if (!['INNER', 'LEFT', 'RIGHT', 'FULL'].includes(normalizedType)) {
        throw new Error(`Unsupported join type: ${joinType}`);
    }

    const leftColumns = columnsOf(left);
    const rightColumns = columnsOf(right);
    const result = [];
    const matchedRight = new Set();

    left.forEach(leftRow => {
        let matched = false;

        right.forEach((rightRow, rightIndex) => {
            if (predicate(leftRow, rightRow)) {
                matched = true;
                matchedRight.add(rightIndex);

                result.push(
                    mergeRows(
                        leftRow,
                        rightRow,
                        leftColumns,
                        rightColumns
                    )
                );
            }
        });

        if (!matched && ['LEFT', 'FULL'].includes(normalizedType)) {
            result.push(
                mergeRows(
                    leftRow,
                    null,
                    leftColumns,
                    rightColumns
                )
            );
        }
    });

    if (['RIGHT', 'FULL'].includes(normalizedType)) {
        right.forEach((rightRow, rightIndex) => {
            if (!matchedRight.has(rightIndex)) {
                result.push(
                    mergeRows(
                        null,
                        rightRow,
                        leftColumns,
                        rightColumns
                    )
                );
            }
        });
    }

    return result;
}

function printRows(rows) {
    console.table(rows);
}

function demonstrateJoinTypes() {
    heading('Join type behavior');

    const repositories = [
        { repositoryId: 1, name: 'payments-api' },
        { repositoryId: 2, name: 'identity-service' },
        { repositoryId: 3, name: 'analytics-engine' }
    ];

    const pullRequests = [
        { repositoryId: 1, prId: 101, state: 'OPEN' },
        { repositoryId: 1, prId: 102, state: 'MERGED' },
        { repositoryId: 2, prId: 103, state: 'OPEN' },
        { repositoryId: 9, prId: 104, state: 'OPEN' }
    ];

    for (const type of ['INNER', 'LEFT', 'RIGHT', 'FULL']) {
        console.log(`\n${type} JOIN`);
        printRows(
            hashJoin(
                repositories,
                pullRequests,
                'repositoryId',
                type
            )
        );
    }
}

function demonstrateNullSemantics() {
    heading('NULL-like join keys');

    const developers = [
        { id: 1, name: 'Asha' },
        { id: 2, name: 'Rahul' },
        { id: null, name: 'Unassigned' }
    ];

    const reviews = [
        { developerId: 1, reviewId: 501 },
        { developerId: null, reviewId: 502 }
    ];

    const result = hashJoin(
        developers,
        reviews,
        'id',
        'FULL'
    );

    console.log(
        'The review key is named developerId while the developer key is id, ' +
        'so a predicate join expresses the actual relationship.'
    );

    const corrected = predicateJoin(
        developers,
        reviews,
        (developer, review) =>
            sqlEquals(developer.id, review.developerId),
        'FULL'
    );

    printRows(corrected);
}

function demonstrateOnAndWhere() {
    heading('ON-style restriction versus post-join filtering');

    const developers = [
        { id: 1, name: 'Asha' },
        { id: 2, name: 'Rahul' },
        { id: 3, name: 'Maya' }
    ];

    const reviews = [
        { developerId: 1, state: 'APPROVED' },
        { developerId: 1, state: 'CHANGES_REQUESTED' },
        { developerId: 2, state: 'COMMENTED' }
    ];

    const joined = predicateJoin(
        developers,
        reviews,
        (developer, review) =>
            sqlEquals(developer.id, review.developerId),
        'LEFT'
    );

    const whereApproved = joined.filter(
        row => row['right.state'] === 'APPROVED'
    );

    console.log(
        'Post-join filtering removes developers whose matching row does not ' +
        'satisfy the state condition.'
    );
    printRows(whereApproved);

    const approvedInJoin = predicateJoin(
        developers,
        reviews,
        (developer, review) =>
            sqlEquals(developer.id, review.developerId) &&
            review.state === 'APPROVED',
        'LEFT'
    );

    console.log(
        'Putting the state condition into the join predicate preserves ' +
        'developers without an approved review.'
    );
    printRows(approvedInJoin);
}

function demonstrateCompositeJoin() {
    heading('Composite-key join');

    const employees = [
        { department: 'IT', region: 'IN', employee: 'Asha' },
        { department: 'IT', region: 'US', employee: 'Rahul' },
        { department: 'HR', region: 'IN', employee: 'Maya' }
    ];

    const permissions = [
        { department: 'IT', region: 'IN', permission: 'DEPLOY' },
        { department: 'IT', region: 'US', permission: 'READ' },
        { department: 'IT', region: 'IN', permission: 'READ' }
    ];

    const result = predicateJoin(
        employees,
        permissions,
        (employee, permission) =>
            sqlEquals(employee.department, permission.department) &&
            sqlEquals(employee.region, permission.region),
        'LEFT'
    );

    printRows(result);
}

function demonstrateEventDrivenWorkflow() {
    heading('Event-driven repository workflow');

    /*
     * Event-driven processing is useful when join inputs arrive at different
     * times. A pull request may exist before its review, and a branch policy
     * may be loaded after both. The Map stores current state while join logic
     * determines relationships when a governance evaluation is requested.
     */
    const repositories = new Map();
    const pullRequests = new Map();
    const reviews = new Map();
    const policies = new Map();

    const handlers = {
        RepositoryCreated(event) {
            repositories.set(event.repositoryId, event);
        },

        PullRequestOpened(event) {
            pullRequests.set(event.prId, event);
        },

        ReviewSubmitted(event) {
            reviews.set(event.reviewId, event);
        },

        BranchPolicyConfigured(event) {
            policies.set(event.repositoryId, event);
        }
    };

    const events = [
        {
            type: 'RepositoryCreated',
            repositoryId: 10,
            name: 'billing-service'
        },
        {
            type: 'PullRequestOpened',
            prId: 900,
            repositoryId: 10,
            author: 'dev-7',
            baseBranch: 'main'
        },
        {
            type: 'ReviewSubmitted',
            reviewId: 3000,
            prId: 900,
            reviewer: 'reviewer-1',
            state: 'APPROVED'
        },
        {
            type: 'BranchPolicyConfigured',
            repositoryId: 10,
            requiredApprovals: 1,
            requiredChecks: ['build', 'test']
        }
    ];

    for (const event of events) {
        const handler = handlers[event.type];

        if (!handler) {
            throw new Error(`No handler for event type ${event.type}`);
        }

        handler(event);
    }

    const repositoryRows = [...repositories.values()];
    const pullRequestRows = [...pullRequests.values()];
    const reviewRows = [...reviews.values()];
    const policyRows = [...policies.values()];

    const prsWithRepositories = predicateJoin(
        pullRequestRows,
        repositoryRows,
        (pr, repository) =>
            sqlEquals(pr.repositoryId, repository.repositoryId),
        'LEFT'
    );

    const prsWithReviews = predicateJoin(
        prsWithRepositories,
        reviewRows,
        (joined, review) =>
            sqlEquals(joined['left.prId'], review.prId),
        'LEFT'
    );

    const governanceRows = predicateJoin(
        prsWithReviews,
        policyRows,
        (joined, policy) =>
            sqlEquals(joined['left.left.repositoryId'], policy.repositoryId),
        'LEFT'
    );

    printRows(governanceRows);
}

function demonstrateFailureCases() {
    heading('Failure handling');

    const cases = [
        () => hashJoin(null, [], 'id', 'INNER'),
        () => hashJoin([], [], 'id', 'CROSS'),
        () => hashJoin([], [], '', 'INNER')
    ];

    for (const operation of cases) {
        try {
            operation();
        } catch (error) {
            console.log(`Rejected invalid join request: ${error.message}`);
        }
    }
}

function runAssertions() {
    heading('Semantic assertions');

    const left = [{ id: 1 }, { id: 2 }, { id: 3 }];
    const right = [{ id: 2 }, { id: 3 }, { id: 4 }];

    const expected = {
        INNER: 2,
        LEFT: 3,
        RIGHT: 3,
        FULL: 4
    };

    for (const [type, count] of Object.entries(expected)) {
        const actual = hashJoin(left, right, 'id', type).length;

        if (actual !== count) {
            throw new Error(
                `${type}: expected ${count} rows but received ${actual}`
            );
        }

        console.log(`${type}: ${actual} rows`);
    }

    console.log('All semantic assertions passed.');
}

function main() {
    demonstrateJoinTypes();
    demonstrateNullSemantics();
    demonstrateOnAndWhere();
    demonstrateCompositeJoin();
    demonstrateEventDrivenWorkflow();
    demonstrateFailureCases();
    runAssertions();
}

main();
