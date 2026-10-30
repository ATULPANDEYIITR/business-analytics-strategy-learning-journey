"use strict";

/*
 * Event-driven executive dashboard model.
 *
 * Accepts the JSON output of executive_dashboard.py or uses a compact
 * built-in dataset. It provides filter state, asynchronous refresh,
 * segment aggregation, and threshold-based management alerts.
 *
 * Run:
 *   node executive_dashboard.js
 *   node executive_dashboard.js --input executive_snapshot.json
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");

const MAX_INPUT_BYTES = 10 * 1024 * 1024;

const DEFAULT_RECORDS = [
  {
    period: "2026-03",
    business_unit: "Consumer",
    region: "North",
    revenue: "455000",
    revenue_target: "440000",
    cogs: "270725",
    operating_expense: "101000",
    orders: 1280,
    delivered_orders: 1250,
    on_time_orders: 1180,
    csat_score_sum: "840",
    csat_responses: 190,
  },
  {
    period: "2026-03",
    business_unit: "Consumer",
    region: "South",
    revenue: "390000",
    revenue_target: "400000",
    cogs: "241800",
    operating_expense: "86000",
    orders: 1120,
    delivered_orders: 1080,
    on_time_orders: 1000,
    csat_score_sum: "660",
    csat_responses: 160,
  },
  {
    period: "2026-03",
    business_unit: "Enterprise",
    region: "North",
    revenue: "660000",
    revenue_target: "650000",
    cogs: "363000",
    operating_expense: "170000",
    orders: 680,
    delivered_orders: 665,
    on_time_orders: 640,
    csat_score_sum: "437",
    csat_responses: 95,
  },
  {
    period: "2026-03",
    business_unit: "Enterprise",
    region: "South",
    revenue: "530000",
    revenue_target: "535000",
    cogs: "296800",
    operating_expense: "135000",
    orders: 550,
    delivered_orders: 535,
    on_time_orders: 500,
    csat_score_sum: "374",
    csat_responses: 85,
  },
];

class DashboardValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "DashboardValidationError";
  }
}

function numeric(value, field, { integer = false } = {}) {
  const parsed = Number(value);

  if (!Number.isFinite(parsed)) {
    throw new DashboardValidationError(`${field} must be a finite number`);
  }

  if (integer && !Number.isSafeInteger(parsed)) {
    throw new DashboardValidationError(`${field} must be a safe integer`);
  }

  return parsed;
}

function validateMonth(month) {
  if (typeof month !== "string" || !/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) {
    throw new DashboardValidationError(
      `Invalid month '${month}'. Expected YYYY-MM.`
    );
  }
}

function normaliseRecord(source) {
  if (!source || typeof source !== "object" || Array.isArray(source)) {
    throw new DashboardValidationError("Each record must be an object");
  }

  validateMonth(source.period);

  const businessUnit = String(source.business_unit ?? "").trim();
  const region = String(source.region ?? "").trim();

  if (!businessUnit || !region) {
    throw new DashboardValidationError(
      "business_unit and region are required"
    );
  }

  const record = {
    period: source.period,
    businessUnit,
    region,
    revenue: numeric(source.revenue, "revenue"),
    revenueTarget: numeric(source.revenue_target, "revenue_target"),
    cogs: numeric(source.cogs, "cogs"),
    operatingExpense: numeric(
      source.operating_expense,
      "operating_expense"
    ),
    orders: numeric(source.orders, "orders", { integer: true }),
    deliveredOrders: numeric(
      source.delivered_orders,
      "delivered_orders",
      { integer: true }
    ),
    onTimeOrders: numeric(
      source.on_time_orders,
      "on_time_orders",
      { integer: true }
    ),
    csatScoreSum: numeric(source.csat_score_sum, "csat_score_sum"),
    csatResponses: numeric(
      source.csat_responses,
      "csat_responses",
      { integer: true }
    ),
  };

  const nonNegative = [
    record.revenue,
    record.cogs,
    record.operatingExpense,
    record.orders,
    record.deliveredOrders,
    record.onTimeOrders,
    record.csatScoreSum,
    record.csatResponses,
  ];

  if (nonNegative.some((value) => value < 0)) {
    throw new DashboardValidationError("Metrics cannot be negative");
  }

  if (record.revenueTarget <= 0) {
    throw new DashboardValidationError("revenue_target must be positive");
  }

  if (
    record.deliveredOrders > record.orders ||
    record.onTimeOrders > record.deliveredOrders
  ) {
    throw new DashboardValidationError(
      "Order, delivery, and on-time counts are inconsistent"
    );
  }

  if (
    (record.csatResponses === 0 && record.csatScoreSum !== 0) ||
    (record.csatResponses > 0 &&
      (record.csatScoreSum < record.csatResponses ||
        record.csatScoreSum > record.csatResponses * 5))
  ) {
    throw new DashboardValidationError(
      "CSAT total is inconsistent with a 1-to-5 response scale"
    );
  }

  return Object.freeze(record);
}

function validateDataset(rawRecords) {
  if (!Array.isArray(rawRecords) || rawRecords.length === 0) {
    throw new DashboardValidationError("Dataset must contain records");
  }

  const records = rawRecords.map(normaliseRecord);
  const keys = new Set();

  for (const record of records) {
    const key = [
      record.period,
      record.businessUnit,
      record.region,
    ].join("|");

    if (keys.has(key)) {
      throw new DashboardValidationError(`Duplicate reporting key: ${key}`);
    }

    keys.add(key);
  }

  return Object.freeze(records);
}

function sum(records, field) {
  return records.reduce((total, record) => total + record[field], 0);
}

function percentage(numerator, denominator) {
  if (denominator === 0) return null;
  return Number(((numerator / denominator) * 100).toFixed(2));
}

function average(numerator, denominator) {
  if (denominator === 0) return null;
  return Number((numerator / denominator).toFixed(2));
}

function calculateMetrics(records) {
  const revenue = sum(records, "revenue");
  const revenueTarget = sum(records, "revenueTarget");
  const cogs = sum(records, "cogs");
  const operatingExpense = sum(records, "operatingExpense");
  const orders = sum(records, "orders");
  const deliveredOrders = sum(records, "deliveredOrders");
  const onTimeOrders = sum(records, "onTimeOrders");
  const csatScoreSum = sum(records, "csatScoreSum");
  const csatResponses = sum(records, "csatResponses");

  const grossProfit = revenue - cogs;
  const operatingProfit = grossProfit - operatingExpense;

  return Object.freeze({
    recordCount: records.length,
    revenue: Number(revenue.toFixed(2)),
    revenueTarget: Number(revenueTarget.toFixed(2)),
    revenueAttainmentPct: percentage(revenue, revenueTarget),
    cogs: Number(cogs.toFixed(2)),
    grossProfit: Number(grossProfit.toFixed(2)),
    grossMarginPct: percentage(grossProfit, revenue),
    operatingExpense: Number(operatingExpense.toFixed(2)),
    operatingProfit: Number(operatingProfit.toFixed(2)),
    operatingMarginPct: percentage(operatingProfit, revenue),
    orders,
    deliveredOrders,
    fulfillmentPct: percentage(deliveredOrders, orders),
    onTimeOrders,
    onTimeDeliveryPct: percentage(onTimeOrders, deliveredOrders),
    csatResponses,
    averageCsat: average(csatScoreSum, csatResponses),
  });
}

class AlertPolicy {
  constructor({
    minimumRevenueAttainment = 95,
    minimumGrossMargin = 35,
    minimumOnTimeDelivery = 90,
    minimumCsat = 4,
  } = {}) {
    this.thresholds = Object.freeze({
      minimumRevenueAttainment,
      minimumGrossMargin,
      minimumOnTimeDelivery,
      minimumCsat,
    });
  }

  evaluate(metrics) {
    if (metrics.recordCount === 0) {
      return [{
        code: "NO_DATA",
        severity: "WARNING",
        message: "No records match the active filters.",
      }];
    }

    const alerts = [];
    const limits = this.thresholds;

    if (
      metrics.revenueAttainmentPct !== null &&
      metrics.revenueAttainmentPct < limits.minimumRevenueAttainment
    ) {
      alerts.push({
        code: "REVENUE_BELOW_PLAN",
        severity: "CRITICAL",
        message: `Revenue attainment is ${metrics.revenueAttainmentPct}%.`,
      });
    }

    if (
      metrics.grossMarginPct !== null &&
      metrics.grossMarginPct < limits.minimumGrossMargin
    ) {
      alerts.push({
        code: "LOW_GROSS_MARGIN",
        severity: "CRITICAL",
        message: `Gross margin is ${metrics.grossMarginPct}%.`,
      });
    }

    if (
      metrics.onTimeDeliveryPct !== null &&
      metrics.onTimeDeliveryPct < limits.minimumOnTimeDelivery
    ) {
      alerts.push({
        code: "DELIVERY_PERFORMANCE",
        severity: "CRITICAL",
        message: `On-time delivery is ${metrics.onTimeDeliveryPct}%.`,
      });
    }

    if (
      metrics.averageCsat !== null &&
      metrics.averageCsat < limits.minimumCsat
    ) {
      alerts.push({
        code: "CUSTOMER_SATISFACTION",
        severity: "WARNING",
        message: `Average customer satisfaction is ${metrics.averageCsat}/5.`,
      });
    }

    return alerts;
  }
}

class ExecutiveDashboard extends EventEmitter {
  constructor(records, alertPolicy = new AlertPolicy()) {
    super();

    this.records = validateDataset(records);
    this.alertPolicy = alertPolicy;
    this.filters = {
      fromMonth: null,
      toMonth: null,
      businessUnit: null,
      region: null,
    };
    this.refreshSequence = 0;
    this.currentSnapshot = null;
  }

  setFilters(nextFilters) {
    const allowed = new Set([
      "fromMonth",
      "toMonth",
      "businessUnit",
      "region",
    ]);

    for (const key of Object.keys(nextFilters)) {
      if (!allowed.has(key)) {
        throw new DashboardValidationError(`Unknown filter: ${key}`);
      }
    }

    const candidate = { ...this.filters, ...nextFilters };

    if (candidate.fromMonth) validateMonth(candidate.fromMonth);
    if (candidate.toMonth) validateMonth(candidate.toMonth);

    if (
      candidate.fromMonth &&
      candidate.toMonth &&
      candidate.fromMonth > candidate.toMonth
    ) {
      throw new DashboardValidationError(
        "fromMonth cannot be later than toMonth"
      );
    }

    for (const field of ["businessUnit", "region"]) {
      if (
        candidate[field] !== null &&
        typeof candidate[field] !== "string"
      ) {
        throw new DashboardValidationError(`${field} must be a string or null`);
      }
    }

    this.filters = Object.freeze(candidate);
    this.emit("filtersChanged", this.filters);
  }

  selectRecords() {
    return this.records.filter((record) => {
      if (
        this.filters.fromMonth &&
        record.period < this.filters.fromMonth
      ) return false;

      if (
        this.filters.toMonth &&
        record.period > this.filters.toMonth
      ) return false;

      if (
        this.filters.businessUnit &&
        record.businessUnit !== this.filters.businessUnit
      ) return false;

      if (
        this.filters.region &&
        record.region !== this.filters.region
      ) return false;

      return true;
    });
  }

  buildSegments(records) {
    const groups = new Map();

    for (const record of records) {
      const key = `${record.businessUnit}|${record.region}`;

      if (!groups.has(key)) {
        groups.set(key, {
          businessUnit: record.businessUnit,
          region: record.region,
          records: [],
        });
      }

      groups.get(key).records.push(record);
    }

    return [...groups.values()]
      .sort((left, right) => {
        const unitOrder = left.businessUnit.localeCompare(
          right.businessUnit
        );
        return unitOrder || left.region.localeCompare(right.region);
      })
      .map((group) => ({
        businessUnit: group.businessUnit,
        region: group.region,
        metrics: calculateMetrics(group.records),
      }));
  }

  async refresh() {
    const sequence = ++this.refreshSequence;
    const filtersAtStart = this.filters;

    // Yield to the event loop so rapid filter changes can supersede a refresh.
    await new Promise((resolve) => setImmediate(resolve));

    const selected = this.selectRecords();
    const metrics = calculateMetrics(selected);

    const snapshot = Object.freeze({
      filters: filtersAtStart,
      metrics,
      alerts: this.alertPolicy.evaluate(metrics),
      segments: this.buildSegments(selected),
      filteredRecordCount: selected.length,
    });

    // Discard an older result if a more recent refresh has started.
    if (sequence !== this.refreshSequence) {
      return null;
    }

    this.currentSnapshot = snapshot;
    this.emit("snapshotUpdated", snapshot);
    return snapshot;
  }
}

async function readRecords(inputPath) {
  const absolutePath = path.resolve(inputPath);
  const fileStats = await fs.stat(absolutePath);

  if (!fileStats.isFile()) {
    throw new Error("Input path must reference a file");
  }

  if (fileStats.size > MAX_INPUT_BYTES) {
    throw new Error("Input file exceeds the 10 MB size limit");
  }

  const text = await fs.readFile(absolutePath, "utf8");
  const parsed = JSON.parse(text);
  const records = Array.isArray(parsed) ? parsed : parsed.records;

  if (!Array.isArray(records)) {
    throw new Error("JSON input must contain a records array");
  }

  return records;
}

function getInputPath() {
  const args = process.argv.slice(2);
  const index = args.indexOf("--input");

  if (index === -1) return null;
  if (!args[index + 1] || args[index + 1].startsWith("--")) {
    throw new Error("--input requires a file path");
  }

  return args[index + 1];
}

async function main() {
  const inputPath = getInputPath();
  const records = inputPath
    ? await readRecords(inputPath)
    : DEFAULT_RECORDS;

  const dashboard = new ExecutiveDashboard(records);

  dashboard.on("filtersChanged", (filters) => {
    process.stdout.write(
      `Filters changed: ${JSON.stringify(filters)}\n`
    );
  });

  dashboard.on("snapshotUpdated", (snapshot) => {
    process.stdout.write(
      `${JSON.stringify(snapshot, null, 2)}\n`
    );
  });

  dashboard.setFilters({
    fromMonth: "2026-01",
    toMonth: "2026-03",
  });
  await dashboard.refresh();

  // Demonstrate an interactive regional filter change.
  dashboard.setFilters({ region: "North" });
  await dashboard.refresh();
}

main().catch((error) => {
  process.stderr.write(`Dashboard failed: ${error.message}\n`);
  process.exitCode = 1;
});

module.exports = {
  AlertPolicy,
  DashboardValidationError,
  ExecutiveDashboard,
  calculateMetrics,
  validateDataset,
};
