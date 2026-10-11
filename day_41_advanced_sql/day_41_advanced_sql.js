"use strict";

/*
 * Advanced SQL companion: event-driven query analysis.
 *
 * Run with Node.js 18 or later:
 *     node advanced_sql.js
 *
 * This program builds a realistic order dataset, executes relational
 * operations in JavaScript, and emits SQL that illustrates window functions,
 * joins, and optimizer-aware query design.
 */

const orders = [
  { id: 501, customerId: 11, date: "2026-01-04", status: "delivered", amount: 42000 },
  { id: 502, customerId: 11, date: "2026-01-18", status: "delivered", amount: 18000 },
  { id: 503, customerId: 12, date: "2026-01-19", status: "shipped", amount: 27000 },
  { id: 504, customerId: 12, date: "2026-02-02", status: "cancelled", amount: 12000 },
  { id: 505, customerId: 13, date: "2026-02-12", status: "delivered", amount: 72000 },
  { id: 506, customerId: 14, date: "2026-02-21", status: "delivered", amount: 18000 },
  { id: 507, customerId: 11, date: "2026-03-07", status: "delivered", amount: 35000 },
  { id: 508, customerId: 15, date: "2026-03-14", status: "pending", amount: 8000 },
  { id: 509, customerId: 13, date: "2026-03-19", status: "delivered", amount: 72000 },
];

const customers = [
  { id: 11, name: "Riya Mehta", region: "North" },
  { id: 12, name: "Arjun Das", region: "South" },
  { id: 13, name: "Sara Khan", region: "West" },
  { id: 14, name: "Dev Patel", region: "North" },
  { id: 15, name: "Maya Iyer", region: "East" },
  { id: 16, name: "Noah Roy", region: "East" },
];

const checks = [
  { name: "unit-tests", state: "success", required: true },
  { name: "sql-lint", state: "success", required: true },
  { name: "integration-tests", state: "pending", required: true },
];

function assert(condition, message) {
  if (!condition) {
    throw new Error(`Invariant failed: ${message}`);
  }
}

function sum(values) {
  return values.reduce((total, value) => total + value, 0);
}

function money(value) {
  return Number(value.toFixed(2));
}

function groupBy(rows, keySelector) {
  const groups = new Map();

  for (const row of rows) {
    const key = keySelector(row);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }

  return groups;
}

function leftJoin(leftRows, rightRows, leftKey, rightKey) {
  const rightIndex = groupBy(rightRows, rightKey);

  return leftRows.flatMap((left) => {
    const matches = rightIndex.get(leftKey(left)) ?? [];
    return matches.length
      ? matches.map((right) => ({ left, right }))
      : [{ left, right: null }];
  });
}

function calculateCustomerRevenue() {
  // Aggregate orders per customer before joining to the customer dimension.
  // This preserves customers with no orders and avoids accidental row loss.
  const revenueByCustomer = new Map();

  for (const order of orders) {
    if (order.status === "cancelled") continue;

    revenueByCustomer.set(
      order.customerId,
      (revenueByCustomer.get(order.customerId) ?? 0) + order.amount
    );
  }

  return customers
    .map((customer) => ({
      ...customer,
      revenue: money(revenueByCustomer.get(customer.id) ?? 0),
    }))
    .sort((a, b) => b.revenue - a.revenue || a.id - b.id);
}

function rankWithinGroups(rows, groupKey, valueKey) {
  const groups = groupBy(rows, (row) => row[groupKey]);
  const ranked = [];

  for (const [group, members] of groups) {
    members.sort(
      (a, b) => b[valueKey] - a[valueKey] || a.id - b.id
    );

    let previousValue;
    let rank = 0;

    members.forEach((member, index) => {
      if (member[valueKey] !== previousValue) rank = index + 1;
      previousValue = member[valueKey];

      ranked.push({
        ...member,
        partition: group,
        rank,
        rowNumber: index + 1,
      });
    });
  }

  return ranked;
}

function calculateRunningRevenue(sourceOrders) {
  const byDate = groupBy(
    sourceOrders.filter((order) => order.status === "delivered"),
    (order) => order.date
  );

  const dates = [...byDate.keys()].sort();
  let runningTotal = 0;

  return dates.map((date) => {
    const dailyRevenue = sum(byDate.get(date).map((order) => order.amount));
    runningTotal += dailyRevenue;

    return {
      date,
      dailyRevenue,
      runningRevenue: runningTotal,
    };
  });
}

function findLatestOrderPerCustomer(sourceOrders) {
  const latest = new Map();

  for (const order of sourceOrders) {
    const previous = latest.get(order.customerId);

    // ISO dates sort chronologically as strings. The ID resolves same-date
    // ties deterministically, like ORDER BY order_date DESC, order_id DESC.
    if (
      !previous ||
      order.date > previous.date ||
      (order.date === previous.date && order.id > previous.id)
    ) {
      latest.set(order.customerId, order);
    }
  }

  return [...latest.values()].sort((a, b) => a.customerId - b.customerId);
}

function evaluateRequiredChecks(statusChecks) {
  const missing = statusChecks.filter(
    (check) => check.required && !check.state
  );
  const pending = statusChecks.filter(
    (check) => check.required && check.state === "pending"
  );
  const failed = statusChecks.filter(
    (check) => check.required && check.state === "failure"
  );

  return {
    eligible: missing.length === 0 && pending.length === 0 && failed.length === 0,
    missing: missing.map((check) => check.name),
    pending: pending.map((check) => check.name),
    failed: failed.map((check) => check.name),
  };
}

function demonstrateJoinCardinality() {
  const selectedCustomers = customers.filter((customer) => customer.id === 11);
  const customerOrders = orders.filter((order) => order.customerId === 11);

  const joined = leftJoin(
    selectedCustomers,
    customerOrders,
    (customer) => customer.id,
    (order) => order.customerId
  );

  console.log("\nJoin cardinality:");
  console.table(
    joined.map(({ left, right }) => ({
      customer: left.name,
      orderId: right?.id ?? null,
      amount: right?.amount ?? null,
    }))
  );

  assert(joined.length === 3, "one customer should match three orders");
}

function printSqlPatterns() {
  console.log("\nSQL pattern: regional ranking and running totals");

  const sql = `
WITH customer_revenue AS (
    SELECT
        c.customer_id,
        c.region,
        SUM(o.total_amount) FILTER (
            WHERE o.status <> 'cancelled'
        ) AS revenue
    FROM customers AS c
    LEFT JOIN orders AS o
      ON o.customer_id = c.customer_id
    GROUP BY c.customer_id, c.region
),
ranked AS (
    SELECT
        customer_id,
        region,
        COALESCE(revenue, 0) AS revenue,
        DENSE_RANK() OVER (
            PARTITION BY region
            ORDER BY COALESCE(revenue, 0) DESC
        ) AS regional_rank
    FROM customer_revenue
)
SELECT customer_id, region, revenue, regional_rank
FROM ranked
ORDER BY region, regional_rank, customer_id;

SELECT
    order_date,
    daily_revenue,
    SUM(daily_revenue) OVER (
        ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_revenue
FROM daily_sales
ORDER BY order_date;
`;

  console.log(sql);

  console.log("SQL pattern: index-friendly range predicate");
  console.log(`
CREATE INDEX idx_orders_customer_date
    ON orders (customer_id, order_date DESC);

SELECT order_id, order_date, status
FROM orders
WHERE customer_id = $1
  AND order_date >= $2
  AND order_date < $3
ORDER BY order_date DESC;
`);
}

async function processAnalyticsEvents() {
  // Event-driven processing can recompute a customer's latest order when a
  // new order event arrives. The queue serializes events to avoid concurrent
  // mutation of the same in-memory aggregate.
  const events = [
    { type: "ORDER_CREATED", order: orders[0] },
    { type: "ORDER_CREATED", order: orders[1] },
    { type: "ORDER_CREATED", order: orders[6] },
  ];

  const state = new Map();

  for (const event of events) {
    if (event.type !== "ORDER_CREATED") continue;

    const current = state.get(event.order.customerId);
    if (!current || event.order.date > current.date) {
      state.set(event.order.customerId, event.order);
    }

    // Yield to the event loop to illustrate asynchronous event processing.
    await Promise.resolve();
  }

  console.log("\nEvent-derived latest orders:");
  console.table([...state.values()]);
}

async function main() {
  console.log("Customer revenue, including customers with no orders:");
  const revenue = calculateCustomerRevenue();
  console.table(revenue);

  console.log("Regional customer ranking:");
  console.table(rankWithinGroups(revenue, "region", "revenue"));

  console.log("Daily revenue and cumulative total:");
  console.table(calculateRunningRevenue(orders));

  console.log("Latest order per customer:");
  console.table(findLatestOrderPerCustomer(orders));

  demonstrateJoinCardinality();

  const eligibility = evaluateRequiredChecks(checks);
  console.log("\nRequired status-check evaluation:");
  console.dir(eligibility, { depth: null });
  assert(!eligibility.eligible, "pending required check must block eligibility");

  await processAnalyticsEvents();
  printSqlPatterns();

  console.log("\nOptimization principles:");
  console.log("- Compare estimated and actual row counts on production-like data.");
  console.log("- Avoid multiplying independent one-to-many relations before aggregation.");
  console.log("- Index selective predicates and join keys, not every column.");
  console.log("- Benchmark complete workloads, including sorting and result transfer.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
