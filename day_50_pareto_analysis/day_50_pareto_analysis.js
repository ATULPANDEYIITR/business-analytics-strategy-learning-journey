"use strict";

/*
 * Pareto analysis for business prioritization.
 * This implementation models business items as events flowing through
 * an asynchronous analysis pipeline. It separates data validation,
 * aggregation, ranking, threshold selection, and reporting.
 */

class BusinessItem {
  constructor(name, category, value) {
    if (typeof name !== "string" || name.trim() === "") {
      throw new TypeError("Item name must be a non-empty string.");
    }

    if (typeof category !== "string" || category.trim() === "") {
      throw new TypeError("Category must be a non-empty string.");
    }

    if (!Number.isFinite(value) || value < 0) {
      throw new TypeError("Value must be a finite non-negative number.");
    }

    this.name = name.trim();
    this.category = category.trim();
    this.value = value;
  }
}

function validateItems(items) {
  if (!Array.isArray(items) || items.length === 0) {
    throw new Error("At least one business item is required.");
  }

  const names = new Set();

  for (const item of items) {
    if (!(item instanceof BusinessItem)) {
      throw new TypeError("All records must be BusinessItem instances.");
    }

    const key = item.name.toLowerCase();

    if (names.has(key)) {
      throw new Error(`Duplicate business item: ${item.name}`);
    }

    names.add(key);
  }

  const total = items.reduce((sum, item) => sum + item.value, 0);

  if (!Number.isFinite(total) || total <= 0) {
    throw new Error("Total business value must be greater than zero.");
  }

  return items.slice();
}

function calculatePareto(items, threshold = 0.80) {
  if (!Number.isFinite(threshold) || threshold <= 0 || threshold > 1) {
    throw new RangeError("Threshold must be between 0 and 1.");
  }

  const validated = validateItems(items);
  const total = validated.reduce((sum, item) => sum + item.value, 0);

  const sorted = validated
    .slice()
    .sort((a, b) => b.value - a.value);

  let cumulative = 0;

  return sorted.map((item, index) => {
    const share = item.value / total;
    const previous = cumulative;
    cumulative += share;

    let priority = "REMAINDER";

    if (previous < threshold && cumulative >= threshold) {
      priority = "THRESHOLD";
    } else if (previous < threshold) {
      priority = "CORE";
    }

    return Object.freeze({
      rank: index + 1,
      item,
      share,
      cumulativeShare: cumulative,
      priority
    });
  });
}

function selectVitalFew(results, threshold = 0.80) {
  const selected = [];
  let cumulative = 0;

  for (const result of results) {
    selected.push(result);
    cumulative += result.share;

    if (cumulative >= threshold) {
      break;
    }
  }

  return selected;
}

function aggregateCategories(items) {
  const categories = new Map();

  for (const item of items) {
    categories.set(
      item.category,
      (categories.get(item.category) ?? 0) + item.value
    );
  }

  return [...categories.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([category, value]) => ({ category, value }));
}

function evaluateDecision(results, capacity, threshold = 0.80) {
  if (!Number.isInteger(capacity) || capacity <= 0) {
    throw new RangeError("Capacity must be a positive integer.");
  }

  const vitalFew = selectVitalFew(results, threshold);

  return {
    capacity,
    requiredItems: vitalFew.length,
    feasible: vitalFew.length <= capacity,
    selected: vitalFew.map(result => result.item.name),
    capturedShare: vitalFew.reduce(
      (sum, result) => sum + result.share,
      0
    )
  };
}

async function analyzeWithEvents(items, threshold = 0.80) {
  return new Promise((resolve, reject) => {
    queueMicrotask(() => {
      try {
        const results = calculatePareto(items, threshold);
        resolve(results);
      } catch (error) {
        reject(error);
      }
    });
  });
}

function renderReport(results, decision) {
  const rows = results.map(result => ({
    Rank: result.rank,
    Item: result.item.name,
    Category: result.item.category,
    Value: result.item.value,
    Share: `${(result.share * 100).toFixed(1)}%`,
    Cumulative: `${(result.cumulativeShare * 100).toFixed(1)}%`,
    Priority: result.priority
  }));

  console.table(rows);

  console.log("\nPrioritization decision");
  console.log("-----------------------");
  console.log(`Required capacity: ${decision.capacity}`);
  console.log(`Vital-few items: ${decision.requiredItems}`);
  console.log(`Capacity sufficient: ${decision.feasible}`);
  console.log(
    `Value captured: ${(decision.capturedShare * 100).toFixed(1)}%`
  );
  console.log(`Selected: ${decision.selected.join(", ")}`);
}

function createSampleData() {
  return [
    new BusinessItem("Enterprise accounts", "Customers", 420000),
    new BusinessItem("SMB accounts", "Customers", 160000),
    new BusinessItem("Support tickets", "Operations", 90000),
    new BusinessItem("Cloud infrastructure", "Technology", 75000),
    new BusinessItem("Marketing campaigns", "Marketing", 60000),
    new BusinessItem("Training programs", "People", 40000),
    new BusinessItem("Internal tooling", "Technology", 25000),
    new BusinessItem("Legacy reporting", "Operations", 15000),
    new BusinessItem("Office services", "Operations", 10000),
    new BusinessItem("Other requests", "Operations", 5000)
  ];
}

function runTests() {
  const data = createSampleData();
  const results = calculatePareto(data);

  if (results.length !== data.length) {
    throw new Error("Result count does not match input count.");
  }

  if (results[0].item.name !== "Enterprise accounts") {
    throw new Error("Descending ranking failed.");
  }

  const totalShare = results.reduce(
    (sum, result) => sum + result.share,
    0
  );

  if (Math.abs(totalShare - 1) > 1e-10) {
    throw new Error("Shares do not sum to 100%.");
  }

  const categories = aggregateCategories(data);

  if (categories[0].category !== "Customers") {
    throw new Error("Category aggregation failed.");
  }

  let failed = false;

  try {
    calculatePareto([new BusinessItem("Zero", "Test", 0)]);
  } catch {
    failed = true;
  }

  if (!failed) {
    throw new Error("Zero-total data should be rejected.");
  }

  console.log("Self-tests passed.");
}

async function main() {
  const data = createSampleData();

  const results = await analyzeWithEvents(data, 0.80);

  const decision = evaluateDecision(results, 3, 0.80);

  renderReport(results, decision);

  console.log("\nCategory contribution");
  console.table(aggregateCategories(data));

  runTests();
}

main().catch(error => {
  console.error(`Analysis failed: ${error.message}`);
  process.exitCode = 1;
});
