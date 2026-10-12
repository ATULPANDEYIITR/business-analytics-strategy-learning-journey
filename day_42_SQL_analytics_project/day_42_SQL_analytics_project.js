"use strict";

/*
 * Retail Business Analytics in JavaScript.
 *
 * Node.js 18+; no third-party dependencies.
 * Demonstrates asynchronous ingestion, streaming CSV parsing, data quality,
 * customer lifetime metrics, monthly performance, discount effectiveness,
 * rolling forecasts, anomaly flags, and JSON report generation.
 *
 * Usage:
 *   node retail_analytics.js
 *   node retail_analytics.js transactions.csv
 */

const fs = require("node:fs");
const path = require("node:path");
const readline = require("node:readline");
const { once } = require("node:events");

const OUTPUT_DIRECTORY = path.resolve("retail_js_output");

function roundMoney(value) {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

function parseCsvLine(line) {
  const fields = [];
  let value = "";
  let quoted = false;

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];

    if (character === '"') {
      if (quoted && line[index + 1] === '"') {
        value += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (character === "," && !quoted) {
      fields.push(value);
      value = "";
    } else {
      value += character;
    }
  }

  if (quoted) {
    throw new Error("CSV contains an unterminated quoted field");
  }

  fields.push(value);
  return fields;
}

async function readCsv(filePath) {
  const stream = fs.createReadStream(filePath, { encoding: "utf8" });
  const reader = readline.createInterface({
    input: stream,
    crlfDelay: Infinity,
  });

  const rows = [];
  let headers = null;
  let lineNumber = 0;

  try {
    for await (const line of reader) {
      lineNumber += 1;
      if (!line.trim()) continue;

      const fields = parseCsvLine(line.replace(/^\uFEFF/, ""));

      if (headers === null) {
        headers = fields.map((header) => header.trim());
        if (new Set(headers).size !== headers.length) {
          throw new Error("CSV contains duplicate column names");
        }
        continue;
      }

      if (fields.length !== headers.length) {
        throw new Error(
          `CSV line ${lineNumber} has ${fields.length} fields; ` +
          `expected ${headers.length}`
        );
      }

      rows.push(Object.fromEntries(
        headers.map((header, index) => [header, fields[index]])
      ));
    }
  } catch (error) {
    reader.close();
    stream.destroy();
    throw error;
  }

  if (headers === null) {
    throw new Error("CSV file is empty");
  }

  return rows;
}

function normalizeOrder(row) {
  const order = {
    orderId: String(row.order_id ?? "").trim(),
    orderDate: String(row.order_date ?? "").trim(),
    customerId: String(row.customer_id ?? "").trim(),
    region: String(row.region ?? "").trim(),
    category: String(row.category ?? "").trim(),
    product: String(row.product ?? "").trim(),
    quantity: Number(row.quantity),
    unitPrice: Number(row.unit_price),
    unitCost: Number(row.unit_cost),
    discount: Number(row.discount),
    paymentMethod: String(row.payment_method ?? "").trim(),
    returned: ["true", "1", "yes"].includes(
      String(row.returned ?? "false").trim().toLowerCase()
    ),
  };

  const errors = validateOrder(order);
  if (errors.length) {
    throw new Error(`${order.orderId || "Unknown order"}: ${errors.join("; ")}`);
  }

  return Object.freeze(order);
}

function validateOrder(order) {
  const errors = [];

  if (!order.orderId) errors.push("missing order identifier");
  if (!order.customerId) errors.push("missing customer identifier");
  if (!order.region) errors.push("missing region");
  if (!order.category) errors.push("missing category");
  if (!order.product) errors.push("missing product");

  if (!Number.isInteger(order.quantity) || order.quantity <= 0) {
    errors.push("quantity must be a positive integer");
  }

  for (const field of ["unitPrice", "unitCost"]) {
    if (!Number.isFinite(order[field]) || order[field] < 0) {
      errors.push(`${field} must be finite and non-negative`);
    }
  }

  if (!Number.isFinite(order.discount) ||
      order.discount < 0 ||
      order.discount > 1) {
    errors.push("discount must be between zero and one");
  }

  // Validate a calendar date, not just the appearance of YYYY-MM-DD.
  if (!/^\d{4}-\d{2}-\d{2}$/.test(order.orderDate)) {
    errors.push("orderDate must use YYYY-MM-DD");
  } else {
    const parsed = new Date(`${order.orderDate}T00:00:00Z`);
    if (Number.isNaN(parsed.getTime()) ||
        parsed.toISOString().slice(0, 10) !== order.orderDate) {
      errors.push("orderDate is not a valid calendar date");
    }
  }

  const validPayments = new Set([
    "Card", "UPI", "Cash", "Bank Transfer", "Wallet",
  ]);
  if (!validPayments.has(order.paymentMethod)) {
    errors.push("unsupported payment method");
  }

  return errors;
}

function grossSales(order) {
  return order.quantity * order.unitPrice;
}

function netSales(order) {
  return grossSales(order) * (1 - order.discount);
}

function recognizedRevenue(order) {
  return order.returned ? 0 : netSales(order);
}

function recognizedCost(order) {
  return order.returned ? 0 : order.quantity * order.unitCost;
}

function summarize(orders) {
  const gross = orders.reduce((sum, order) => sum + grossSales(order), 0);
  const discounts = orders.reduce(
    (sum, order) => sum + grossSales(order) * order.discount, 0
  );
  const revenue = orders.reduce(
    (sum, order) => sum + recognizedRevenue(order), 0
  );
  const cost = orders.reduce(
    (sum, order) => sum + recognizedCost(order), 0
  );
  const returned = orders.filter((order) => order.returned).length;

  return {
    transactions: orders.length,
    returnedTransactions: returned,
    grossSales: roundMoney(gross),
    discounts: roundMoney(discounts),
    recognizedRevenue: roundMoney(revenue),
    recognizedCost: roundMoney(cost),
    profit: roundMoney(revenue - cost),
    profitMargin: revenue === 0 ? 0 : (revenue - cost) / revenue,
    averageRevenuePerTransaction:
      orders.length === 0 ? 0 : roundMoney(revenue / orders.length),
    returnRate: orders.length === 0 ? 0 : returned / orders.length,
  };
}

function aggregateBy(orders, keyFunction) {
  const groups = new Map();

  for (const order of orders) {
    const key = keyFunction(order);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(order);
  }

  return [...groups.entries()]
    .map(([group, groupOrders]) => ({
      group,
      ...summarize(groupOrders),
    }))
    .sort((left, right) =>
      right.recognizedRevenue - left.recognizedRevenue
    );
}

function customerLifetimeAnalysis(orders) {
  const customers = new Map();

  for (const order of orders) {
    if (!customers.has(order.customerId)) {
      customers.set(order.customerId, {
        customerId: order.customerId,
        firstPurchase: order.orderDate,
        lastPurchase: order.orderDate,
        transactions: 0,
        revenue: 0,
        cost: 0,
        products: new Set(),
      });
    }

    const customer = customers.get(order.customerId);
    customer.transactions += 1;
    customer.firstPurchase = order.orderDate < customer.firstPurchase
      ? order.orderDate : customer.firstPurchase;
    customer.lastPurchase = order.orderDate > customer.lastPurchase
      ? order.orderDate : customer.lastPurchase;

    customer.revenue += recognizedRevenue(order);
    customer.cost += recognizedCost(order);

    if (!order.returned) customer.products.add(order.product);
  }

  return [...customers.values()]
    .map((customer) => {
      const revenue = roundMoney(customer.revenue);
      return {
        customerId: customer.customerId,
        firstPurchase: customer.firstPurchase,
        lastPurchase: customer.lastPurchase,
        transactions: customer.transactions,
        revenue,
        profit: roundMoney(customer.revenue - customer.cost),
        distinctProductsPurchased: customer.products.size,
        segment: revenue >= 1500 ? "High Value"
          : revenue >= 400 ? "Regular" : "Occasional",
      };
    })
    .sort((left, right) => right.revenue - left.revenue);
}

function analyzeDiscountBands(orders) {
  const bands = [
    { name: "No discount", accepts: (d) => d === 0 },
    { name: "Up to 5%", accepts: (d) => d > 0 && d <= 0.05 },
    { name: "6% to 10%", accepts: (d) => d > 0.05 && d <= 0.10 },
    { name: "11% to 15%", accepts: (d) => d > 0.10 && d <= 0.15 },
    { name: "Above 15%", accepts: (d) => d > 0.15 },
  ];

  return bands.map((band) => {
    const matching = orders.filter((order) => band.accepts(order.discount));
    const summary = summarize(matching);

    return {
      discountBand: band.name,
      transactions: summary.transactions,
      recognizedRevenue: summary.recognizedRevenue,
      profit: summary.profit,
      profitMargin: summary.profitMargin,
    };
  }).filter((band) => band.transactions > 0);
}

function detectOutliers(orders) {
  const values = orders.map(recognizedRevenue).sort((a, b) => a - b);
  if (values.length < 4) return [];

  function percentile(fraction) {
    const position = (values.length - 1) * fraction;
    const lower = Math.floor(position);
    const upper = Math.ceil(position);
    if (lower === upper) return values[lower];

    return values[lower] * (upper - position) +
      values[upper] * (position - lower);
  }

  const q1 = percentile(0.25);
  const q3 = percentile(0.75);
  const limit = q3 + 1.5 * (q3 - q1);

  return orders
    .filter((order) => recognizedRevenue(order) > limit)
    .map((order) => ({
      orderId: order.orderId,
      customerId: order.customerId,
      revenue: roundMoney(recognizedRevenue(order)),
      upperIqrLimit: roundMoney(limit),
    }));
}

function buildMonthlyForecast(monthlyRows, horizon = 3) {
  if (!Number.isInteger(horizon) || horizon < 1 || horizon > 24) {
    throw new RangeError("Forecast horizon must be an integer from 1 to 24");
  }

  const ordered = [...monthlyRows].sort((a, b) =>
    a.group.localeCompare(b.group)
  );

  const history = ordered.map((row) => row.recognizedRevenue);
  if (history.length === 0) return [];

  const latest = ordered[ordered.length - 1].group;
  const [year, month] = latest.split("-").map(Number);
  const results = [];

  for (let step = 1; step <= horizon; step += 1) {
    const window = history.slice(-3);
    const forecast = window.reduce((sum, value) => sum + value, 0) /
      window.length;

    const nextDate = new Date(Date.UTC(year, month - 1 + step, 1));
    results.push({
      month: nextDate.toISOString().slice(0, 7),
      forecastRevenue: roundMoney(forecast),
      method: "Three-month moving average",
    });

    history.push(forecast);
  }

  return results;
}

async function writeJson(fileName, data) {
  const destination = path.join(OUTPUT_DIRECTORY, fileName);
  const temporary = `${destination}.tmp`;

  // Writing to a temporary file avoids exposing a partially written report.
  await fs.promises.writeFile(
    temporary,
    `${JSON.stringify(data, null, 2)}\n`,
    "utf8"
  );
  await fs.promises.rename(temporary, destination);
}

function createSampleData() {
  const categories = [
    ["Laptop", "Electronics", 850, 610],
    ["Monitor", "Electronics", 260, 175],
    ["Office Chair", "Furniture", 190, 118],
    ["Desk", "Furniture", 320, 220],
    ["Backpack", "Accessories", 55, 24],
    ["USB Hub", "Accessories", 28, 11],
    ["Notebook Pack", "Stationery", 12, 4],
  ];

  const regions = ["North", "South", "East", "West", "Central"];
  const payments = ["Card", "UPI", "Cash", "Bank Transfer", "Wallet"];
  const orders = [];

  for (let index = 1; index <= 300; index += 1) {
    const item = categories[index % categories.length];
    const month = String((index % 12) + 1).padStart(2, "0");
    const day = String((index % 27) + 1).padStart(2, "0");

    orders.push(normalizeOrder({
      order_id: `ORD-${String(index).padStart(5, "0")}`,
      order_date: `2025-${month}-${day}`,
      customer_id: `CUST-${String((index * 7) % 90 + 1).padStart(3, "0")}`,
      region: regions[index % regions.length],
      category: item[1],
      product: item[0],
      quantity: index % 15 === 0 ? 8 : (index % 3) + 1,
      unit_price: item[2],
      unit_cost: item[3],
      discount: [0, 0.05, 0.1, 0.15][index % 4],
      payment_method: payments[index % payments.length],
      returned: index % 23 === 0 ? "true" : "false",
    }));
  }

  return orders;
}

async function main() {
  const inputPath = process.argv[2];
  const rawRows = inputPath ? await readCsv(path.resolve(inputPath)) : null;
  const orders = rawRows
    ? rawRows.map(normalizeOrder)
    : createSampleData();

  // Map-based deduplication keeps the first record for each business key.
  // Conflicting duplicates are reported rather than silently overwritten.
  const unique = new Map();
  const duplicateIds = [];

  for (const order of orders) {
    if (unique.has(order.orderId)) {
      duplicateIds.push(order.orderId);
      continue;
    }
    unique.set(order.orderId, order);
  }

  if (duplicateIds.length) {
    throw new Error(
      `Duplicate order IDs detected: ${[...new Set(duplicateIds)].join(", ")}`
    );
  }

  const cleanOrders = [...unique.values()];
  const overall = summarize(cleanOrders);
  const monthly = aggregateBy(cleanOrders, (order) =>
    order.orderDate.slice(0, 7)
  );
  const report = {
    generatedAt: new Date().toISOString(),
    dataQuality: {
      rowsLoaded: orders.length,
      uniqueRows: cleanOrders.length,
      invalidRows: 0,
    },
    overall,
    regions: aggregateBy(cleanOrders, (order) => order.region),
    categories: aggregateBy(cleanOrders, (order) => order.category),
    paymentMethods: aggregateBy(cleanOrders, (order) => order.paymentMethod),
    discounts: analyzeDiscountBands(cleanOrders),
    customers: customerLifetimeAnalysis(cleanOrders),
    monthly,
    forecast: buildMonthlyForecast(monthly),
    highRevenueOutliers: detectOutliers(cleanOrders),
  };

  await fs.promises.mkdir(OUTPUT_DIRECTORY, { recursive: true });
  await writeJson("analytics_report.json", report);
  await writeJson("normalized_orders.json", cleanOrders);

  console.log("Retail analytics completed");
  console.log(JSON.stringify(overall, null, 2));
  console.log("\nRegional revenue:");
  for (const region of report.regions) {
    console.log(
      `${region.group}: ${region.recognizedRevenue.toFixed(2)} revenue, ` +
      `${region.profit.toFixed(2)} profit`
    );
  }

  console.log("\nRevenue forecast:");
  for (const item of report.forecast) {
    console.log(`${item.month}: ${item.forecastRevenue.toFixed(2)}`);
  }

  console.log(`\nReports saved to ${OUTPUT_DIRECTORY}`);
}

main().catch((error) => {
  console.error(`Analytics failed: ${error.message}`);
  process.exitCode = 1;
});
