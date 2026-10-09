"use strict";

/*
 * Event-driven analytical pipeline using Common Table Expression concepts.
 * This file emphasizes immutable intermediate datasets, dependency tracking,
 * asynchronous stage execution, and reproducible analytical results.
 *
 * Run with Node.js 18 or later. No external packages are required.
 */

const orders = Object.freeze([
  Object.freeze({ id: 201, customerId: "C101", month: "2025-01", status: "completed", amount: 1200 }),
  Object.freeze({ id: 202, customerId: "C102", month: "2025-01", status: "completed", amount: 800 }),
  Object.freeze({ id: 203, customerId: "C101", month: "2025-02", status: "completed", amount: 500 }),
  Object.freeze({ id: 204, customerId: "C103", month: "2025-02", status: "cancelled", amount: 950 }),
  Object.freeze({ id: 205, customerId: "C102", month: "2025-02", status: "completed", amount: 1500 }),
  Object.freeze({ id: 206, customerId: "C104", month: "2025-03", status: "completed", amount: 2400 }),
  Object.freeze({ id: 207, customerId: "C101", month: "2025-03", status: "completed", amount: 700 }),
  Object.freeze({ id: 208, customerId: "C104", month: "2025-04", status: "refunded", amount: 2400 }),
  Object.freeze({ id: 209, customerId: "C103", month: "2025-04", status: "completed", amount: 1100 }),
  Object.freeze({ id: 210, customerId: "C102", month: "2025-04", status: "completed", amount: 600 })
]);

class CTEError extends Error {
  constructor(message) {
    super(message);
    this.name = "CTEError";
  }
}

class CTEEngine {
  constructor() {
    this.definitions = new Map();
    this.results = new Map();
    this.running = new Set();
    this.executionLog = [];
  }

  define(name, dependencies, compute) {
    if (typeof name !== "string" || !/^[a-zA-Z_]\w*$/.test(name)) {
      throw new CTEError(`Invalid stage name: ${String(name)}`);
    }
    if (this.definitions.has(name)) {
      throw new CTEError(`Stage already defined: ${name}`);
    }
    if (!Array.isArray(dependencies) || typeof compute !== "function") {
      throw new CTEError(`Stage ${name} requires dependencies and a compute function.`);
    }
    this.definitions.set(name, { dependencies: [...dependencies], compute });
  }

  async evaluate(name) {
    if (this.results.has(name)) {
      return this.results.get(name);
    }

    const definition = this.definitions.get(name);
    if (!definition) {
      throw new CTEError(`Unknown analytical stage: ${name}`);
    }

    // The running set detects cyclic dependencies in the analytical graph.
    if (this.running.has(name)) {
      throw new CTEError(`Circular CTE dependency detected at ${name}`);
    }

    this.running.add(name);
    try {
      const dependencyEntries = await Promise.all(
        definition.dependencies.map(async dependency => [
          dependency,
          await this.evaluate(dependency)
        ])
      );

      const inputs = Object.fromEntries(dependencyEntries);
      const output = await definition.compute(Object.freeze(inputs));

      if (!Array.isArray(output)) {
        throw new CTEError(`Stage ${name} must return an array of records.`);
      }

      // Freeze output records so downstream stages cannot mutate shared results.
      const immutableOutput = Object.freeze(
        output.map(row => Object.freeze({ ...row }))
      );

      this.results.set(name, immutableOutput);
      this.executionLog.push({
        stage: name,
        inputStages: [...definition.dependencies],
        outputRows: immutableOutput.length
      });

      return immutableOutput;
    } finally {
      this.running.delete(name);
    }
  }

  invalidate(name) {
    if (!this.definitions.has(name)) {
      throw new CTEError(`Cannot invalidate unknown stage: ${name}`);
    }

    // Invalidate the selected stage and every dependent stage.
    const affected = new Set([name]);
    let changed = true;

    while (changed) {
      changed = false;
      for (const [candidate, definition] of this.definitions) {
        if (
          !affected.has(candidate) &&
          definition.dependencies.some(dependency => affected.has(dependency))
        ) {
          affected.add(candidate);
          changed = true;
        }
      }
    }

    for (const stage of affected) {
      this.results.delete(stage);
    }
    this.executionLog = this.executionLog.filter(
      entry => !affected.has(entry.stage)
    );
  }
}

function sumBy(records, key, valueKey) {
  const totals = new Map();

  for (const record of records) {
    const group = record[key];
    totals.set(group, (totals.get(group) ?? 0) + record[valueKey]);
  }

  return [...totals.entries()]
    .map(([group, total]) => ({ [key]: group, total }))
    .sort((a, b) => String(a[key]).localeCompare(String(b[key])));
}

function defineRetailPipeline(engine) {
  engine.define("eligible_orders", [], async () =>
    orders.filter(order => order.status === "completed")
  );

  engine.define("monthly_revenue", ["eligible_orders"], async ({ eligible_orders }) =>
    sumBy(eligible_orders, "month", "amount")
  );

  engine.define("customer_lifetime_value", ["eligible_orders"], async ({ eligible_orders }) => {
    const grouped = new Map();

    for (const order of eligible_orders) {
      const current = grouped.get(order.customerId) ?? {
        customerId: order.customerId,
        orderCount: 0,
        revenue: 0
      };
      current.orderCount += 1;
      current.revenue += order.amount;
      grouped.set(order.customerId, current);
    }

    return [...grouped.values()]
      .map(row => ({
        ...row,
        averageOrderValue: Number((row.revenue / row.orderCount).toFixed(2))
      }))
      .sort((a, b) => b.revenue - a.revenue);
  });

  engine.define("monthly_growth", ["monthly_revenue"], async ({ monthly_revenue }) => {
    return monthly_revenue.map((current, index) => {
      const previous = monthly_revenue[index - 1];
      return {
        month: current.month,
        revenue: current.total,
        previousRevenue: previous?.total ?? null,
        change: previous ? current.total - previous.total : null,
        percentageChange: previous && previous.total !== 0
          ? Number(((current.total - previous.total) / previous.total * 100).toFixed(2))
          : null
      };
    });
  });

  engine.define(
    "customer_month_activity",
    ["eligible_orders"],
    async ({ eligible_orders }) => {
      const unique = new Map();
      for (const order of eligible_orders) {
        unique.set(`${order.customerId}:${order.month}`, {
          customerId: order.customerId,
          month: order.month
        });
      }
      return [...unique.values()].sort(
        (a, b) => a.month.localeCompare(b.month) ||
          a.customerId.localeCompare(b.customerId)
      );
    }
  );

  engine.define(
    "retention_report",
    ["eligible_orders", "customer_month_activity"],
    async ({ eligible_orders, customer_month_activity }) => {
      const firstMonth = new Map();

      for (const order of eligible_orders) {
        const previous = firstMonth.get(order.customerId);
        if (!previous || order.month < previous) {
          firstMonth.set(order.customerId, order.month);
        }
      }

      const cohorts = new Map();
      for (const month of firstMonth.values()) {
        cohorts.set(month, (cohorts.get(month) ?? 0) + 1);
      }

      const active = new Map();
      for (const item of customer_month_activity) {
        const cohort = firstMonth.get(item.customerId);
        const key = `${cohort}:${item.month}`;
        if (!active.has(key)) active.set(key, new Set());
        active.get(key).add(item.customerId);
      }

      return [...active.entries()].map(([key, customers]) => {
        const [cohortMonth, activityMonth] = key.split(":");
        const cohortSize = cohorts.get(cohortMonth);
        return {
          cohortMonth,
          activityMonth,
          cohortSize,
          activeCustomers: customers.size,
          retentionPercent: Number((customers.size / cohortSize * 100).toFixed(2))
        };
      }).sort((a, b) =>
        a.cohortMonth.localeCompare(b.cohortMonth) ||
        a.activityMonth.localeCompare(b.activityMonth)
      );
    }
  );
}

function printTable(title, records) {
  console.log(`\n${title}`);
  if (records.length === 0) {
    console.log("(no rows)");
    return;
  }

  const columns = [...new Set(records.flatMap(Object.keys))];
  console.table(records.map(record =>
    Object.fromEntries(columns.map(column => [column, record[column] ?? null]))
  ));
}

async function main() {
  const engine = new CTEEngine();
  defineRetailPipeline(engine);

  // Independent analytical branches can be evaluated concurrently.
  const [monthly, customerValues, growth, retention] = await Promise.all([
    engine.evaluate("monthly_revenue"),
    engine.evaluate("customer_lifetime_value"),
    engine.evaluate("monthly_growth"),
    engine.evaluate("retention_report")
  ]);

  printTable("Monthly revenue", monthly);
  printTable("Customer lifetime value", customerValues);
  printTable("Monthly growth", growth);
  printTable("Cohort activity", retention);

  console.log("\nExecuted dependency stages:");
  console.table(engine.executionLog);

  const cachedResult = await engine.evaluate("monthly_revenue");
  if (cachedResult !== monthly) {
    throw new Error("Expected a cached stage result.");
  }

  engine.invalidate("eligible_orders");
  if (engine.results.has("monthly_revenue")) {
    throw new Error("Dependent stage cache was not invalidated.");
  }

  const recomputed = await engine.evaluate("monthly_revenue");
  if (JSON.stringify(recomputed) !== JSON.stringify(monthly)) {
    throw new Error("Recomputed analytical output differs from original output.");
  }

  console.log("\nCache validation and dependency invalidation passed.");

  // A failed dependency should be surfaced rather than silently producing results.
  const invalidEngine = new CTEEngine();
  invalidEngine.define("missing_input", ["undefined_stage"], async () => []);
  try {
    await invalidEngine.evaluate("missing_input");
  } catch (error) {
    if (!(error instanceof CTEError)) throw error;
    console.log(`Expected dependency failure: ${error.message}`);
  }

  // A cyclic dependency is rejected before a result can be produced.
  const cyclicEngine = new CTEEngine();
  cyclicEngine.define("stage_a", ["stage_b"], async () => []);
  cyclicEngine.define("stage_b", ["stage_a"], async () => []);
  try {
    await cyclicEngine.evaluate("stage_a");
  } catch (error) {
    if (!(error instanceof CTEError)) throw error;
    console.log(`Expected cycle failure: ${error.message}`);
  }
}

main().catch(error => {
  console.error("Analytical pipeline failed:", error);
  process.exitCode = 1;
});
