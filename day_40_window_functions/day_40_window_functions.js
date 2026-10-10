"use strict";

/*
 * Window-function analytics for a repository of monthly sales events.
 *
 * Run with Node.js 18 or later:
 *   node window_functions.js
 *
 * This implementation focuses on immutable transformations, asynchronous
 * data ingestion, deterministic ordering, partition-local state, and
 * composable analytical operators.
 */

const sales = [
  { id: 1, person: "Asha", region: "North", month: "2026-01", revenue: 12000 },
  { id: 2, person: "Ravi", region: "North", month: "2026-01", revenue: 12000 },
  { id: 3, person: "Meera", region: "North", month: "2026-01", revenue: 9000 },
  { id: 4, person: "Asha", region: "North", month: "2026-02", revenue: 15000 },
  { id: 5, person: "Ravi", region: "North", month: "2026-02", revenue: 11000 },
  { id: 6, person: "Meera", region: "North", month: "2026-02", revenue: 11000 },
  { id: 7, person: "Asha", region: "North", month: "2026-03", revenue: 14000 },
  { id: 8, person: "Ravi", region: "North", month: "2026-03", revenue: 16000 },
  { id: 9, person: "Meera", region: "North", month: "2026-03", revenue: 10000 },
  { id: 10, person: "Kabir", region: "South", month: "2026-01", revenue: 8000 },
  { id: 11, person: "Nila", region: "South", month: "2026-01", revenue: 10000 },
  { id: 12, person: "Kabir", region: "South", month: "2026-02", revenue: 12000 },
  { id: 13, person: "Nila", region: "South", month: "2026-02", revenue: 10000 },
  { id: 14, person: "Kabir", region: "South", month: "2026-03", revenue: 12000 },
  { id: 15, person: "Nila", region: "South", month: "2026-03", revenue: 14000 }
];

function validateRows(rows) {
  if (!Array.isArray(rows)) {
    throw new TypeError("Expected an array of sales records");
  }

  const ids = new Set();

  for (const row of rows) {
    if (!Number.isSafeInteger(row.id) || row.id <= 0) {
      throw new TypeError("Each record needs a positive safe-integer ID");
    }
    if (ids.has(row.id)) {
      throw new Error(`Duplicate record ID: ${row.id}`);
    }
    ids.add(row.id);

    if (typeof row.region !== "string" || !row.region.trim()) {
      throw new TypeError(`Record ${row.id} has no region`);
    }
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(row.month)) {
      throw new TypeError(`Record ${row.id} has an invalid month`);
    }
    if (!Number.isFinite(row.revenue) || row.revenue < 0) {
      throw new TypeError(`Record ${row.id} has invalid revenue`);
    }
  }
}

function compareValues(left, right) {
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

function partitionRows(rows, keySelector) {
  const partitions = new Map();

  for (const row of rows) {
    const key = keySelector(row);
    if (!partitions.has(key)) partitions.set(key, []);
    partitions.get(key).push(row);
  }

  return partitions;
}

function orderRows(rows, keySelector, direction = "asc") {
  if (direction !== "asc" && direction !== "desc") {
    throw new RangeError("Direction must be asc or desc");
  }

  const multiplier = direction === "asc" ? 1 : -1;

  // Sorting a copied array avoids mutating the caller's input.
  return [...rows].sort((left, right) => {
    const comparison = compareValues(
      keySelector(left),
      keySelector(right)
    );
    return comparison * multiplier || left.id - right.id;
  });
}

function rankPartition(rows, valueSelector) {
  const ordered = orderRows(rows, valueSelector, "desc");
  const output = [];
  let previousValue;
  let rank = 0;
  let denseRank = 0;

  ordered.forEach((row, index) => {
    const value = valueSelector(row);
    if (index === 0 || value !== previousValue) {
      rank = index + 1;
      denseRank += 1;
    }

    output.push({
      ...row,
      rowNumber: index + 1,
      rank,
      denseRank
    });
    previousValue = value;
  });

  return output;
}

function withRunningTotal(rows, valueSelector) {
  let total = 0;
  return rows.map((row) => {
    total += valueSelector(row);
    return { ...row, runningTotal: total };
  });
}

function withMovingAverage(rows, valueSelector, preceding) {
  if (!Number.isInteger(preceding) || preceding < 0) {
    throw new RangeError("preceding must be a non-negative integer");
  }

  return rows.map((row, index) => {
    const start = Math.max(0, index - preceding);
    const frame = rows.slice(start, index + 1);
    const total = frame.reduce(
      (sum, entry) => sum + valueSelector(entry),
      0
    );

    return {
      ...row,
      movingAverage: total / frame.length,
      frameStartIndex: start
    };
  });
}

function withLagLead(rows, valueSelector, offset = 1) {
  if (!Number.isInteger(offset) || offset < 0) {
    throw new RangeError("offset must be a non-negative integer");
  }

  return rows.map((row, index) => ({
    ...row,
    previousValue: index >= offset
      ? valueSelector(rows[index - offset])
      : null,
    nextValue: index + offset < rows.length
      ? valueSelector(rows[index + offset])
      : null
  }));
}

function withPeriodChange(rows, valueSelector) {
  const adjacent = withLagLead(rows, valueSelector, 1);

  return adjacent.map((row) => {
    const previous = row.previousValue;
    const current = valueSelector(row);

    return {
      ...row,
      percentChange:
        previous === null || previous === 0
          ? null
          : ((current - previous) / previous) * 100
    };
  });
}

function analyzeRegion(regionRows) {
  const chronological = orderRows(regionRows, (row) => row.month);
  const ranked = rankPartition(chronological, (row) => row.revenue);
  const byId = new Map(ranked.map((row) => [row.id, row]));

  const withTotals = withRunningTotal(
    chronological,
    (row) => row.revenue
  );
  const withAverages = withMovingAverage(
    withTotals,
    (row) => row.revenue,
    1
  );
  const withChanges = withPeriodChange(
    withAverages,
    (row) => row.revenue
  );

  return withChanges.map((row) => ({
    ...row,
    rowNumber: byId.get(row.id).rowNumber,
    rank: byId.get(row.id).rank,
    denseRank: byId.get(row.id).denseRank
  }));
}

async function loadSales() {
  // The async boundary mirrors a database or HTTP data source. A real
  // service should validate response schemas before trusting external data.
  await Promise.resolve();
  return sales.map((row) => Object.freeze({ ...row }));
}

async function main() {
  const rows = await loadSales();
  validateRows(rows);

  const partitions = partitionRows(rows, (row) => row.region);
  const reports = [];

  for (const [region, regionRows] of partitions) {
    reports.push(...analyzeRegion(regionRows).map((row) => ({
      id: row.id,
      region,
      person: row.person,
      month: row.month,
      revenue: row.revenue,
      rowNumber: row.rowNumber,
      rank: row.rank,
      denseRank: row.denseRank,
      runningTotal: row.runningTotal,
      movingAverage: Number(row.movingAverage.toFixed(2)),
      previousValue: row.previousValue,
      nextValue: row.nextValue,
      percentChange: row.percentChange === null
        ? null
        : Number(row.percentChange.toFixed(2))
    })));
  }

  console.log("Partition-local window analytics");
  console.table(reports);

  const regionalTotals = [...partitionRows(rows, (row) => row.region)]
    .map(([region, entries]) => ({
      region,
      revenue: entries.reduce((sum, row) => sum + row.revenue, 0),
      transactionCount: entries.length
    }))
    .sort((left, right) => right.revenue - left.revenue);

  console.table(regionalTotals);

  // A zero-offset lag is the current row, whereas a negative offset is
  // rejected because it does not have the expected lag semantics.
  try {
    withLagLead(rows, (row) => row.revenue, -1);
  } catch (error) {
    console.log(`Expected validation failure: ${error.message}`);
  }
}

main().catch((error) => {
  console.error("Analytics failed:", error.message);
  process.exitCode = 1;
});
