'use strict';

/*
 * GROUP BY: Segmenting and Aggregating Business Data
 *
 * This Node.js program models analytical grouping as an event-driven
 * reporting workflow. It uses Map, Set, reducers, asynchronous event
 * handling, validation, and policy-like report construction.
 *
 * Run with:
 *   node group_by_business_data.js
 */

const { EventEmitter } = require('node:events');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');

const sales = [
  {
    id: 1001, date: '2026-01-05', region: 'North', channel: 'Online',
    category: 'Electronics', product: 'Laptop', customerSegment: 'Enterprise',
    units: 4, revenue: 4800, cost: 3600, discount: 0.05
  },
  {
    id: 1002, date: '2026-01-08', region: 'North', channel: 'Retail',
    category: 'Office', product: 'Monitor', customerSegment: 'SMB',
    units: 10, revenue: 3000, cost: 2100, discount: 0
  },
  {
    id: 1003, date: '2026-01-12', region: 'South', channel: 'Online',
    category: 'Electronics', product: 'Phone', customerSegment: 'Consumer',
    units: 15, revenue: 9000, cost: 6300, discount: 0.10
  },
  {
    id: 1004, date: '2026-01-15', region: 'West', channel: 'Partner',
    category: 'Software', product: 'Analytics', customerSegment: 'Enterprise',
    units: 3, revenue: 7500, cost: 2250, discount: 0.15
  },
  {
    id: 1005, date: '2026-01-20', region: 'East', channel: 'Retail',
    category: 'Office', product: 'Chair', customerSegment: 'SMB',
    units: 20, revenue: 4000, cost: 2600, discount: 0.05
  },
  {
    id: 1006, date: '2026-02-02', region: 'North', channel: 'Online',
    category: 'Software', product: 'CRM', customerSegment: 'Enterprise',
    units: 5, revenue: 10000, cost: 3000, discount: 0.08
  },
  {
    id: 1007, date: '2026-02-05', region: 'South', channel: 'Retail',
    category: 'Electronics', product: 'Laptop', customerSegment: 'Consumer',
    units: 3, revenue: 3600, cost: 2700, discount: 0.03
  },
  {
    id: 1008, date: '2026-02-11', region: 'West', channel: 'Online',
    category: 'Office', product: 'Desk', customerSegment: 'SMB',
    units: 12, revenue: 4800, cost: 3000, discount: 0
  },
  {
    id: 1009, date: '2026-02-17', region: 'East', channel: 'Partner',
    category: 'Software', product: 'Analytics', customerSegment: 'Enterprise',
    units: 4, revenue: 10000, cost: 3000, discount: 0.12
  },
  {
    id: 1010, date: '2026-02-22', region: 'North', channel: 'Retail',
    category: 'Electronics', product: 'Phone', customerSegment: 'Consumer',
    units: 8, revenue: 4800, cost: 3360, discount: 0.07
  },
  {
    id: 1011, date: '2026-03-03', region: 'South', channel: 'Online',
    category: 'Software', product: 'CRM', customerSegment: 'SMB',
    units: 7, revenue: 8400, cost: 2800, discount: 0.05
  },
  {
    id: 1012, date: '2026-03-07', region: 'West', channel: 'Partner',
    category: 'Electronics', product: 'Laptop', customerSegment: 'Enterprise',
    units: 6, revenue: 7200, cost: 5400, discount: 0.10
  },
  {
    id: 1013, date: '2026-03-10', region: 'East', channel: 'Retail',
    category: 'Office', product: 'Monitor', customerSegment: 'Consumer',
    units: 14, revenue: 4200, cost: 2940, discount: 0.04
  },
  {
    id: 1014, date: '2026-03-18', region: 'North', channel: 'Online',
    category: 'Software', product: 'Analytics', customerSegment: 'Enterprise',
    units: 2, revenue: 5000, cost: 1500, discount: 0.20
  },
  {
    id: 1015, date: '2026-03-24', region: 'South', channel: 'Partner',
    category: 'Office', product: 'Chair', customerSegment: 'SMB',
    units: 25, revenue: 5000, cost: 3250, discount: 0.06
  }
];


function validateSale(sale) {
  const required = [
    'id', 'date', 'region', 'channel', 'category', 'product',
    'customerSegment', 'units', 'revenue', 'cost', 'discount'
  ];

  for (const field of required) {
    if (!(field in sale)) {
      throw new Error(`Sale ${sale.id ?? 'unknown'} is missing ${field}`);
    }
  }

  if (!Number.isInteger(sale.units) || sale.units <= 0) {
    throw new Error(`Sale ${sale.id}: units must be a positive integer`);
  }

  if (!Number.isFinite(sale.revenue) || sale.revenue < 0) {
    throw new Error(`Sale ${sale.id}: invalid revenue`);
  }

  if (!Number.isFinite(sale.cost) || sale.cost < 0 || sale.cost > sale.revenue) {
    throw new Error(`Sale ${sale.id}: invalid cost`);
  }

  if (!Number.isFinite(sale.discount) || sale.discount < 0 || sale.discount > 1) {
    throw new Error(`Sale ${sale.id}: discount must be between 0 and 1`);
  }
}


function validateDataset(records) {
  const identifiers = new Set();

  for (const sale of records) {
    validateSale(sale);

    if (identifiers.has(sale.id)) {
      throw new Error(`Duplicate sale identifier: ${sale.id}`);
    }

    identifiers.add(sale.id);
  }
}


function groupBy(records, keyFunction) {
  /*
   * Map is appropriate here because it explicitly models a key-to-bucket
   * relationship and does not restrict keys to strings.
   */
  const groups = new Map();

  for (const record of records) {
    const key = keyFunction(record);

    if (!groups.has(key)) {
      groups.set(key, []);
    }

    groups.get(key).push(record);
  }

  return groups;
}


function sum(records, selector) {
  return records.reduce((total, record) => total + selector(record), 0);
}


function average(records, selector) {
  return records.length === 0
    ? 0
    : sum(records, selector) / records.length;
}


function aggregateSales(records) {
  const revenue = sum(records, sale => sale.revenue);
  const cost = sum(records, sale => sale.cost);

  return {
    transactions: records.length,
    units: sum(records, sale => sale.units),
    revenue,
    averageOrderValue: records.length ? revenue / records.length : 0,
    profit: revenue - cost,
    margin: revenue ? (revenue - cost) / revenue : 0
  };
}


function money(value) {
  return Number(value.toFixed(2));
}


function percentage(value) {
  return `${(value * 100).toFixed(2)}%`;
}


function rowsByRegion(records) {
  const groups = groupBy(records, sale => sale.region);

  return [...groups.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([region, rows]) => {
      const aggregate = aggregateSales(rows);

      return {
        region,
        transactions: aggregate.transactions,
        units: aggregate.units,
        revenue: money(aggregate.revenue),
        profit: money(aggregate.profit),
        margin: percentage(aggregate.margin)
      };
    });
}


function rowsByRegionAndChannel(records) {
  /*
   * A serialized composite key makes the Map directly usable while the
   * split operation reconstructs the dimensions for reporting.
   *
   * The delimiter is safe for this controlled domain because dimension
   * values are validated against the known business vocabulary.
   */
  const groups = groupBy(
    records,
    sale => `${sale.region}|${sale.channel}`
  );

  return [...groups.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, rows]) => {
      const [region, channel] = key.split('|');
      const aggregate = aggregateSales(rows);

      return {
        region,
        channel,
        transactions: aggregate.transactions,
        revenue: money(aggregate.revenue),
        profit: money(aggregate.profit)
      };
    });
}


function conditionalAggregation(records) {
  /*
   * The conditions belong inside the aggregate calculation. This mirrors
   * SUM(CASE WHEN ...) without filtering away rows needed by other metrics.
   */
  const groups = groupBy(records, sale => sale.region);

  return [...groups.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([region, rows]) => ({
      region,
      totalRevenue: money(sum(rows, sale => sale.revenue)),
      onlineRevenue: money(
        sum(rows.filter(sale => sale.channel === 'Online'), sale => sale.revenue)
      ),
      softwareRevenue: money(
        sum(rows.filter(sale => sale.category === 'Software'), sale => sale.revenue)
      ),
      enterpriseTransactions: rows.filter(
        sale => sale.customerSegment === 'Enterprise'
      ).length
    }));
}


function havingRevenue(records, threshold) {
  /*
   * This is a HAVING-style operation. Every transaction first participates
   * in its region's aggregate, and only then is the region filtered.
   */
  return rowsByRegion(records)
    .filter(row => row.revenue >= threshold)
    .map(row => ({
      region: row.region,
      revenue: row.revenue,
      transactions: row.transactions
    }));
}


function monthKey(dateString) {
  const date = new Date(`${dateString}T00:00:00Z`);
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`;
}


function quarterKey(dateString) {
  const date = new Date(`${dateString}T00:00:00Z`);
  const quarter = Math.floor(date.getUTCMonth() / 3) + 1;
  return `${date.getUTCFullYear()}-Q${quarter}`;
}


function monthlyChannelRevenue(records) {
  const groups = groupBy(
    records,
    sale => `${monthKey(sale.date)}|${sale.channel}`
  );

  return [...groups.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, rows]) => {
      const [month, channel] = key.split('|');

      return {
        month,
        channel,
        transactions: rows.length,
        revenue: money(sum(rows, sale => sale.revenue)),
        units: sum(rows, sale => sale.units)
      };
    });
}


function quarterlyCategoryProfit(records) {
  const groups = groupBy(
    records,
    sale => `${quarterKey(sale.date)}|${sale.category}`
  );

  return [...groups.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, rows]) => {
      const [quarter, category] = key.split('|');
      const revenue = sum(rows, sale => sale.revenue);
      const profit = sum(rows, sale => sale.revenue - sale.cost);

      return {
        quarter,
        category,
        revenue: money(revenue),
        profit: money(profit),
        margin: percentage(revenue ? profit / revenue : 0)
      };
    });
}


function distinctProductsBySegment(records) {
  const groups = groupBy(records, sale => sale.customerSegment);

  return [...groups.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([customerSegment, rows]) => {
      const products = new Set(rows.map(sale => sale.product));
      const revenue = sum(rows, sale => sale.revenue);

      return {
        customerSegment,
        distinctProducts: products.size,
        transactions: rows.length,
        revenue: money(revenue)
      };
    });
}


function topCategories(records, limit = 3) {
  const groups = groupBy(records, sale => sale.category);

  return [...groups.entries()]
    .map(([category, rows]) => ({
      category,
      profit: money(sum(rows, sale => sale.revenue - sale.cost)),
      revenue: money(sum(rows, sale => sale.revenue))
    }))
    .sort((left, right) => right.profit - left.profit)
    .slice(0, limit);
}


class ReportBus extends EventEmitter {
  publish(reportName, rows) {
    this.emit('report-ready', {
      reportName,
      generatedAt: new Date().toISOString(),
      rows
    });
  }
}


class BusinessAnalyticsService {
  constructor(records) {
    validateDataset(records);
    this.records = Object.freeze([...records]);
    this.events = new ReportBus();
  }

  onReport(listener) {
    this.events.on('report-ready', listener);
  }

  generateReports() {
    /*
     * EventEmitter demonstrates an event-driven reporting boundary:
     * generation produces a result and subscribers decide how to consume it.
     */
    this.events.publish('region-revenue', rowsByRegion(this.records));
    this.events.publish(
      'region-channel-revenue',
      rowsByRegionAndChannel(this.records)
    );
    this.events.publish(
      'conditional-region-metrics',
      conditionalAggregation(this.records)
    );
    this.events.publish(
      'high-value-regions',
      havingRevenue(this.records, 15000)
    );
    this.events.publish(
      'monthly-channel-revenue',
      monthlyChannelRevenue(this.records)
    );
    this.events.publish(
      'quarterly-category-profit',
      quarterlyCategoryProfit(this.records)
    );
  }

  getExecutiveView() {
    const revenue = sum(this.records, sale => sale.revenue);
    const profit = sum(this.records, sale => sale.revenue - sale.cost);

    return Object.freeze({
      transactions: this.records.length,
      revenue: money(revenue),
      profit: money(profit),
      margin: percentage(revenue ? profit / revenue : 0),
      topCategories: topCategories(this.records)
    });
  }
}


async function exportJson(service) {
  const directory = await fs.mkdtemp(
    path.join(os.tmpdir(), 'group-by-business-')
  );

  const outputPath = path.join(directory, 'regional-report.json');

  await fs.writeFile(
    outputPath,
    JSON.stringify(rowsByRegion(service.records), null, 2),
    'utf8'
  );

  return outputPath;
}


function demonstrateMissingDimension() {
  const records = [
    { region: 'North', revenue: 100 },
    { region: null, revenue: 200 },
    { region: '', revenue: 300 }
  ];

  /*
   * JavaScript null and empty strings are different values. For business
   * reporting they are normalized deliberately so incomplete dimensions are
   * visible instead of creating unexplained separate categories.
   */
  const groups = groupBy(
    records,
    row => row.region?.trim() || 'Unknown'
  );

  return [...groups.entries()].map(([region, rows]) => ({
    region,
    transactions: rows.length,
    revenue: money(sum(rows, row => row.revenue))
  }));
}


function printReport(title, rows) {
  console.log(`\n=== ${title} ===`);
  console.table(rows);
}


async function main() {
  validateDataset(sales);

  console.log('GROUP BY: Segmenting and Aggregating Business Data');
  console.log(`Validated ${sales.length} sales transactions.`);

  const service = new BusinessAnalyticsService(sales);

  service.onReport(report => {
    printReport(report.reportName, report.rows);
  });

  service.generateReports();

  printReport(
    'Customer Segment and Distinct Product Analysis',
    distinctProductsBySegment(sales)
  );

  printReport(
    'Top Categories by Profit',
    topCategories(sales)
  );

  console.log('\n=== Executive View ===');
  console.table([service.getExecutiveView()]);

  printReport(
    'Explicit Missing-Dimension Handling',
    demonstrateMissingDimension()
  );

  try {
    validateSale({
      id: 9999,
      date: '2026-04-01',
      region: 'North',
      channel: 'Online',
      category: 'Software',
      product: 'CRM',
      customerSegment: 'Enterprise',
      units: 1,
      revenue: 100,
      cost: 125,
      discount: 0.05
    });
  } catch (error) {
    console.log('\n=== Validation Failure ===');
    console.log(error.message);
  }

  const outputPath = await exportJson(service);

  console.log('\n=== Asynchronous Export ===');
  console.log(`Report written to: ${outputPath}`);
  console.log('\nHash-based grouping is approximately O(n) expected time.');
  console.log('Sorting grouped output adds approximately O(g log g).');
}


main().catch(error => {
  console.error('Analytics execution failed:', error.message);
  process.exitCode = 1;
});
