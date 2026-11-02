"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { EventEmitter } = require("node:events");
const assert = require("node:assert/strict");

const SALES = [
  { orderId: 1001, orderDate: "2026-01-03", region: "North", product: "Laptop", category: "Electronics", units: 2, unitPrice: 75000, discount: 0.05, customer: "Apex Ltd" },
  { orderId: 1002, orderDate: "2026-01-05", region: "South", product: "Monitor", category: "Electronics", units: 4, unitPrice: 18000, discount: 0.10, customer: "Beta Corp" },
  { orderId: 1003, orderDate: "2026-01-08", region: "West", product: "Desk", category: "Furniture", units: 3, unitPrice: 12000, discount: 0.00, customer: "Gamma Pvt" },
  { orderId: 1004, orderDate: "2026-01-11", region: "North", product: "Chair", category: "Furniture", units: 10, unitPrice: 6500, discount: 0.08, customer: "Apex Ltd" },
  { orderId: 1005, orderDate: "2026-01-13", region: "East", product: "Laptop", category: "Electronics", units: 1, unitPrice: 82000, discount: 0.05, customer: "Delta Inc" },
  { orderId: 1006, orderDate: "2026-01-18", region: "South", product: "Desk", category: "Furniture", units: 2, unitPrice: 13500, discount: 0.03, customer: "Beta Corp" },
  { orderId: 1007, orderDate: "2026-01-20", region: "West", product: "Keyboard", category: "Accessories", units: 15, unitPrice: 2200, discount: 0.00, customer: "Gamma Pvt" },
  { orderId: 1008, orderDate: "2026-01-23", region: "East", product: "Monitor", category: "Electronics", units: 5, unitPrice: 19500, discount: 0.12, customer: "Delta Inc" },
  { orderId: 1009, orderDate: "2026-02-02", region: "North", product: "Laptop", category: "Electronics", units: 3, unitPrice: 76000, discount: 0.04, customer: "Apex Ltd" },
  { orderId: 1010, orderDate: "2026-02-04", region: "South", product: "Chair", category: "Furniture", units: 8, unitPrice: 6200, discount: 0.06, customer: "Beta Corp" },
  { orderId: 1011, orderDate: "2026-02-09", region: "West", product: "Monitor", category: "Electronics", units: 2, unitPrice: 18500, discount: 0.02, customer: "Gamma Pvt" },
  { orderId: 1012, orderDate: "2026-02-15", region: "East", product: "Keyboard", category: "Accessories", units: 20, unitPrice: 2100, discount: 0.05, customer: "Delta Inc" }
];

const CUSTOMER_DIMENSION = new Map([
  ["Apex Ltd", { segment: "Enterprise", manager: "Neha" }],
  ["Beta Corp", { segment: "Enterprise", manager: "Ravi" }],
  ["Gamma Pvt", { segment: "Mid-Market", manager: "Meera" }],
  ["Delta Inc", { segment: "Enterprise", manager: "Arjun" }]
]);

class DataFrame {
  constructor(rows) {
    this.rows = rows.map(row => ({ ...row }));
  }

  get columns() {
    return this.rows.length === 0 ? [] : Object.keys(this.rows[0]);
  }

  get shape() {
    return [this.rows.length, this.columns.length];
  }

  select(...columns) {
    return new DataFrame(
      this.rows.map(row => Object.fromEntries(columns.map(column => [column, row[column]])))
    );
  }

  filter(predicate) {
    return new DataFrame(this.rows.filter(predicate));
  }

  map(transform) {
    return new DataFrame(this.rows.map(transform));
  }

  sortBy(column, descending = false) {
    const rows = [...this.rows].sort((a, b) => {
      const left = a[column];
      const right = b[column];
      if (left === right) return 0;
      return (left < right ? -1 : 1) * (descending ? -1 : 1);
    });
    return new DataFrame(rows);
  }

  groupBy(keySelector) {
    const groups = new Map();
    for (const row of this.rows) {
      const key = keySelector(row);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(row);
    }
    return groups;
  }

  describeNumeric(column) {
    const values = this.rows
      .map(row => Number(row[column]))
      .filter(Number.isFinite);

    if (values.length === 0) {
      throw new Error(`No numeric values found for ${column}`);
    }

    const sorted = [...values].sort((a, b) => a - b);
    const sum = values.reduce((a, b) => a + b, 0);
    const mean = sum / values.length;
    const middle = Math.floor(sorted.length / 2);
    const median = sorted.length % 2
      ? sorted[middle]
      : (sorted[middle - 1] + sorted[middle]) / 2;

    return {
      count: values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      mean,
      median
    };
  }

  toJSON() {
    return this.rows.map(row => ({ ...row }));
  }
}

function validateRows(rows) {
  if (!Array.isArray(rows) || rows.length === 0) {
    throw new TypeError("A non-empty array of records is required");
  }

  const seen = new Set();

  for (const row of rows) {
    if (!Number.isInteger(row.orderId) || seen.has(row.orderId)) {
      throw new Error(`Invalid or duplicate order ID: ${row.orderId}`);
    }

    if (!Number.isFinite(row.units) || row.units <= 0) {
      throw new Error(`Invalid units for order ${row.orderId}`);
    }

    if (!Number.isFinite(row.unitPrice) || row.unitPrice <= 0) {
      throw new Error(`Invalid unit price for order ${row.orderId}`);
    }

    if (!Number.isFinite(row.discount) || row.discount < 0 || row.discount >= 1) {
      throw new Error(`Invalid discount for order ${row.orderId}`);
    }

    if (Number.isNaN(Date.parse(row.orderDate))) {
      throw new Error(`Invalid date for order ${row.orderId}`);
    }

    seen.add(row.orderId);
  }

  return true;
}

function enrich(rows) {
  return new DataFrame(rows).map(row => {
    const grossSales = row.units * row.unitPrice;
    const discountAmount = grossSales * row.discount;
    const netSales = grossSales - discountAmount;

    return {
      ...row,
      grossSales,
      discountAmount,
      netSales,
      month: row.orderDate.slice(0, 7),
      highValue: netSales >= 100000
    };
  });
}

function aggregateByRegionAndCategory(frame) {
  const groups = frame.groupBy(
    row => `${row.region}|${row.category}`
  );

  return new DataFrame(
    [...groups.entries()].map(([key, rows]) => {
      const [region, category] = key.split("|");
      const units = rows.reduce((sum, row) => sum + row.units, 0);
      const netSales = rows.reduce((sum, row) => sum + row.netSales, 0);

      return {
        region,
        category,
        orders: new Set(rows.map(row => row.orderId)).size,
        units,
        netSales: Number(netSales.toFixed(2)),
        averageOrderValue: Number((netSales / rows.length).toFixed(2))
      };
    })
  ).sortBy("netSales", true);
}

function createPivot(frame) {
  const regions = [...new Set(frame.rows.map(row => row.region))].sort();
  const months = [...new Set(frame.rows.map(row => row.month))].sort();

  return regions.map(region => {
    const output = { region };

    for (const month of months) {
      output[month] = frame.rows
        .filter(row => row.region === region && row.month === month)
        .reduce((sum, row) => sum + row.netSales, 0);
      output[month] = Number(output[month].toFixed(2));
    }

    return output;
  });
}

function mergeCustomerDimension(frame) {
  return frame.map(row => ({
    ...row,
    ...(CUSTOMER_DIMENSION.get(row.customer) || {
      segment: "Unknown",
      manager: "Unassigned"
    })
  }));
}

function rollingMean(frame, windowSize) {
  if (!Number.isInteger(windowSize) || windowSize <= 0) {
    throw new RangeError("windowSize must be a positive integer");
  }

  const sorted = frame.sortBy("orderDate").rows;
  return sorted.map((row, index) => {
    const start = Math.max(0, index - windowSize + 1);
    const window = sorted.slice(start, index + 1);
    const average =
      window.reduce((sum, item) => sum + item.netSales, 0) / window.length;

    return {
      orderId: row.orderId,
      orderDate: row.orderDate,
      netSales: row.netSales,
      rollingMean: Number(average.toFixed(2))
    };
  });
}

class DataPipeline extends EventEmitter {
  constructor(rows) {
    super();
    this.source = rows;
    this.frame = null;
  }

  async execute() {
    this.emit("started", { rows: this.source.length });

    validateRows(this.source);
    await Promise.resolve();

    this.frame = enrich(this.source);
    this.emit("enriched", { shape: this.frame.shape });

    const highValue = this.frame.filter(row => row.highValue);
    this.emit("filtered", { rows: highValue.rows.length });

    return highValue;
  }
}

function writeJsonSafely(frame) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "dataframe-"));
  const file = path.join(directory, "sales.json");

  try {
    fs.writeFileSync(
      file,
      JSON.stringify(frame.toJSON(), null, 2),
      { encoding: "utf8", flag: "wx" }
    );

    const restored = JSON.parse(fs.readFileSync(file, "utf8"));
    assert.equal(restored.length, frame.rows.length);
    return restored;
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
}

async function main() {
  const pipeline = new DataPipeline(SALES);

  pipeline.on("started", info => console.log("Pipeline started:", info));
  pipeline.on("enriched", info => console.log("Enriched shape:", info));
  pipeline.on("filtered", info => console.log("High-value rows:", info));

  const frame = await pipeline.execute();

  console.log("\nDATAFRAME SHAPE");
  console.log(frame.shape);

  console.log("\nSELECTED COLUMNS");
  console.table(
    frame.select("orderId", "region", "category", "netSales").rows
  );

  console.log("\nFILTERED ELECTRONICS");
  console.table(
    frame
      .filter(row => row.category === "Electronics")
      .sortBy("netSales", true)
      .rows
  );

  console.log("\nNUMERIC DESCRIPTION");
  console.log(frame.describeNumeric("netSales"));

  const all = enrich(SALES);

  console.log("\nREGION/CATEGORY AGGREGATION");
  console.table(aggregateByRegionAndCategory(all));

  console.log("\nMONTH PIVOT");
  console.table(createPivot(all));

  console.log("\nCUSTOMER MERGE");
  console.table(
    mergeCustomerDimension(all).select(
      "orderId",
      "customer",
      "segment",
      "manager",
      "netSales"
    ).rows
  );

  console.log("\nROLLING THREE-ORDER MEAN");
  console.table(rollingMean(all, 3));

  console.log("\nJSON ROUND TRIP");
  console.log(`restored rows: ${writeJsonSafely(all).length}`);

  const missingExample = [
    { region: "North", sales: 100000 },
    { region: null, sales: null },
    { region: "East", sales: 80000 }
  ];

  const missingHandled = missingExample.map(row => ({
    region: row.region ?? "Unknown",
    sales: row.sales ?? 90000
  }));

  console.log("\nMISSING-DATA HANDLING");
  console.table(missingHandled);

  assert.equal(all.rows.length, SALES.length);
  assert.equal(new Set(all.rows.map(row => row.orderId)).size, SALES.length);
  assert.ok(all.rows.every(row => row.netSales >= 0));

  assert.throws(
    () => validateRows([
      { ...SALES[0], orderId: SALES[0].orderId },
      { ...SALES[1], orderId: SALES[0].orderId }
    ]),
    /duplicate order ID/
  );

  assert.throws(
    () => validateRows([{ ...SALES[0], discount: 1 }]),
    /Invalid discount/
  );

  console.log("\nDATA QUALITY: VALID");
  console.log("All assertions passed.");
}

main().catch(error => {
  console.error("Pipeline failed:", error.message);
  process.exitCode = 1;
});
