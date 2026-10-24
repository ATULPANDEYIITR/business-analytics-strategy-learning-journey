"use strict";

const fs = require("node:fs");
const path = require("node:path");

const ChartType = Object.freeze({
  BAR: "bar",
  LINE: "line",
  SCATTER: "scatter",
  HISTOGRAM: "histogram",
  BOX: "box"
});

class ChartValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "ChartValidationError";
  }
}

class SalesRecord {
  constructor({
    month,
    region,
    revenue,
    orders,
    marketingSpend,
    deliveryDays
  }) {
    this.month = month;
    this.region = region;
    this.revenue = revenue;
    this.orders = orders;
    this.marketingSpend = marketingSpend;
    this.deliveryDays = deliveryDays;
  }
}

function validateRecords(records) {
  if (!Array.isArray(records) || records.length === 0) {
    throw new ChartValidationError("At least one record is required.");
  }

  for (const record of records) {
    if (!(record instanceof SalesRecord)) {
      throw new ChartValidationError("Invalid sales record.");
    }

    if (!record.month || !record.region) {
      throw new ChartValidationError("Month and region are required.");
    }

    if (
      !Number.isFinite(record.revenue) ||
      record.revenue < 0 ||
      !Number.isInteger(record.orders) ||
      record.orders < 0 ||
      !Number.isFinite(record.marketingSpend) ||
      record.marketingSpend < 0 ||
      !Number.isFinite(record.deliveryDays) ||
      record.deliveryDays < 0
    ) {
      throw new ChartValidationError(
        `Invalid numeric values for ${record.region}/${record.month}.`
      );
    }
  }

  return records;
}

function groupSum(records, key, valueKey) {
  const result = new Map();

  for (const record of records) {
    const group = record[key];
    result.set(group, (result.get(group) || 0) + record[valueKey]);
  }

  return new Map(
    [...result.entries()].sort((a, b) => a[1] - b[1])
  );
}

function pearsonCorrelation(x, y) {
  if (x.length !== y.length || x.length < 2) {
    throw new ChartValidationError(
      "Correlation requires equally sized arrays with at least two values."
    );
  }

  const xMean = x.reduce((sum, value) => sum + value, 0) / x.length;
  const yMean = y.reduce((sum, value) => sum + value, 0) / y.length;

  let numerator = 0;
  let xVariance = 0;
  let yVariance = 0;

  for (let i = 0; i < x.length; i++) {
    const dx = x[i] - xMean;
    const dy = y[i] - yMean;

    numerator += dx * dy;
    xVariance += dx * dx;
    yVariance += dy * dy;
  }

  const denominator = Math.sqrt(xVariance * yVariance);

  if (denominator === 0) {
    throw new ChartValidationError(
      "Correlation is undefined for zero-variance data."
    );
  }

  return numerator / denominator;
}

function histogram(values, binWidth) {
  if (!values.length || binWidth <= 0) {
    throw new ChartValidationError("Invalid histogram input.");
  }

  const minimum = Math.min(...values);
  const maximum = Math.max(...values);

  if (minimum === maximum) {
    return [{
      lower: minimum,
      upper: minimum + binWidth,
      count: values.length
    }];
  }

  const binCount = Math.floor((maximum - minimum) / binWidth) + 1;
  const counts = Array(binCount).fill(0);

  for (const value of values) {
    let index = Math.floor((value - minimum) / binWidth);
    index = Math.min(index, binCount - 1);
    counts[index]++;
  }

  return counts.map((count, index) => ({
    lower: minimum + index * binWidth,
    upper: minimum + (index + 1) * binWidth,
    count
  }));
}

function percentile(sorted, fraction) {
  const position = (sorted.length - 1) * fraction;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);

  if (lower === upper) {
    return sorted[lower];
  }

  const weight = position - lower;
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

function boxStatistics(values) {
  if (!values.length) {
    throw new ChartValidationError("Box plot requires data.");
  }

  const sorted = [...values].sort((a, b) => a - b);
  const q1 = percentile(sorted, 0.25);
  const median = percentile(sorted, 0.5);
  const q3 = percentile(sorted, 0.75);
  const iqr = q3 - q1;

  const lowerFence = q1 - 1.5 * iqr;
  const upperFence = q3 + 1.5 * iqr;

  const outliers = sorted.filter(
    value => value < lowerFence || value > upperFence
  );

  const regular = sorted.filter(
    value => value >= lowerFence && value <= upperFence
  );

  return {
    minimum: Math.min(...regular),
    q1,
    median,
    q3,
    maximum: Math.max(...regular),
    outliers
  };
}

function evaluateChartPolicy(chartType, records) {
  validateRecords(records);

  const policies = {
    [ChartType.BAR]: records.length >= 1,
    [ChartType.LINE]: records.length >= 2,
    [ChartType.SCATTER]: records.length >= 2,
    [ChartType.HISTOGRAM]: records.length >= 2,
    [ChartType.BOX]: records.length >= 5
  };

  if (!policies[chartType]) {
    throw new ChartValidationError(
      `Chart type '${chartType}' is not supported.`
    );
  }

  return {
    chartType,
    eligible: true,
    reason: `Input satisfies the ${chartType} chart data requirements.`
  };
}

function renderEventDrivenDashboard(records) {
  const handlers = new Map();

  handlers.set(ChartType.BAR, () =>
    groupSum(records, "region", "revenue")
  );

  handlers.set(ChartType.LINE, () =>
    groupSum(records, "month", "revenue")
  );

  handlers.set(ChartType.SCATTER, () => ({
    x: records.map(record => record.marketingSpend),
    y: records.map(record => record.revenue),
    correlation: pearsonCorrelation(
      records.map(record => record.marketingSpend),
      records.map(record => record.revenue)
    )
  }));

  handlers.set(ChartType.HISTOGRAM, () =>
    histogram(
      records.map(record => record.revenue),
      20000
    )
  );

  handlers.set(ChartType.BOX, () =>
    boxStatistics(
      records.map(record => record.deliveryDays)
    )
  );

  return handlers;
}

async function processDashboard(records) {
  validateRecords(records);

  const handlers = renderEventDrivenDashboard(records);
  const output = {};

  for (const chartType of Object.values(ChartType)) {
    evaluateChartPolicy(chartType, records);

    // Promise scheduling makes the chart pipeline independently extensible.
    output[chartType] = await Promise.resolve(
      handlers.get(chartType)()
    );
  }

  return output;
}

function createRecords() {
  return [
    ["2026-01", "North", 72000, 410, 11000, 3.2],
    ["2026-01", "South", 64000, 390, 9500, 4.1],
    ["2026-01", "West", 81000, 450, 12500, 2.8],
    ["2026-02", "North", 76000, 425, 11500, 3.4],
    ["2026-02", "South", 68000, 402, 10200, 4.0],
    ["2026-02", "West", 87000, 478, 13100, 2.6],
    ["2026-03", "North", 83000, 440, 12000, 3.6],
    ["2026-03", "South", 70000, 410, 10500, 4.4],
    ["2026-03", "West", 92000, 495, 13800, 2.9],
    ["2026-04", "North", 88000, 462, 12700, 3.5],
    ["2026-04", "South", 73000, 421, 10800, 4.2],
    ["2026-04", "West", 97000, 510, 14500, 2.7],
    ["2026-05", "North", 91000, 475, 13000, 3.8],
    ["2026-05", "South", 76000, 430, 11100, 4.5],
    ["2026-05", "West", 103000, 535, 15100, 2.5],
    ["2026-06", "North", 96000, 490, 13600, 3.7],
    ["2026-06", "South", 79000, 442, 11400, 4.3],
    ["2026-06", "West", 108000, 552, 15700, 2.8],
    ["2026-06", "West", 155000, 600, 22000, 9.5]
  ].map(
    ([month, region, revenue, orders, marketingSpend, deliveryDays]) =>
      new SalesRecord({
        month,
        region,
        revenue,
        orders,
        marketingSpend,
        deliveryDays
      })
  );
}

async function main() {
  try {
    const records = createRecords();
    const dashboard = await processDashboard(records);

    const outputDirectory = path.join(
      process.cwd(),
      "business_chart_output_js"
    );

    fs.mkdirSync(outputDirectory, { recursive: true });

    fs.writeFileSync(
      path.join(outputDirectory, "chart_metrics.json"),
      JSON.stringify(dashboard, null, 2),
      "utf8"
    );

    console.log("Business chart policy evaluation:");
    for (const chartType of Object.values(ChartType)) {
      console.log(
        evaluateChartPolicy(chartType, records)
      );
    }

    console.log("\nChart metrics:");
    console.log(JSON.stringify(dashboard, null, 2));
    console.log(
      `\nOutput: ${path.resolve(outputDirectory)}`
    );
  } catch (error) {
    if (error instanceof ChartValidationError) {
      console.error(`Validation failure: ${error.message}`);
      process.exitCode = 2;
    } else {
      console.error(`Unexpected failure: ${error.message}`);
      process.exitCode = 1;
    }
  }
}

main();
