"use strict";

/*
 * Excel Tables: Structured Data and Dynamic Calculations
 *
 * This JavaScript study file models the concepts behind Excel Tables:
 * structured records, named columns, calculated columns, filtering,
 * sorting, aggregation, lookup indexes, dynamic expansion, validation,
 * and dependency-aware calculations.
 *
 * The implementation is intentionally self-contained and runs in Node.js
 * without external packages.
 */

// ---------------------------------------------------------------------------
// 1. BASIC STRUCTURED RECORDS
// ---------------------------------------------------------------------------

const salesRecords = [
  {
    orderId: 1001,
    customer: "Asha",
    region: "North",
    product: "Laptop",
    quantity: 2,
    unitPrice: 75000,
    discountRate: 0.05
  },
  {
    orderId: 1002,
    customer: "Ravi",
    region: "South",
    product: "Monitor",
    quantity: 3,
    unitPrice: 18000,
    discountRate: 0.10
  }
];

function calculateGrossAmount(row) {
  return row.quantity * row.unitPrice;
}

function calculateDiscountAmount(row) {
  return calculateGrossAmount(row) * row.discountRate;
}

function calculateNetAmount(row) {
  return calculateGrossAmount(row) - calculateDiscountAmount(row);
}

console.log("=== BASIC STRUCTURED RECORDS ===");

for (const row of salesRecords) {
  console.log({
    orderId: row.orderId,
    customer: row.customer,
    netAmount: calculateNetAmount(row)
  });
}


// ---------------------------------------------------------------------------
// 2. TABLE ABSTRACTION
// ---------------------------------------------------------------------------

class StructuredTable {
  constructor(columns, rows = []) {
    if (new Set(columns).size !== columns.length) {
      throw new Error("Column names must be unique.");
    }

    this.columns = [...columns];
    this.rows = [];

    for (const row of rows) {
      this.addRow(row);
    }
  }

  validateColumns(row) {
    for (const column of this.columns) {
      if (!(column in row)) {
        throw new Error(`Missing column: ${column}`);
      }
    }
  }

  addRow(row) {
    this.validateColumns(row);

    this.rows.push({ ...row });
    return this;
  }

  addRows(rows) {
    for (const row of rows) {
      this.addRow(row);
    }

    return this;
  }

  addCalculatedColumn(columnName, calculation) {
    if (!this.columns.includes(columnName)) {
      this.columns.push(columnName);
    }

    for (const row of this.rows) {
      row[columnName] = calculation(row);
    }

    return this;
  }

  filter(predicate) {
    return new StructuredTable(
      this.columns,
      this.rows.filter(predicate)
    );
  }

  sortBy(columnName, descending = false) {
    if (!this.columns.includes(columnName)) {
      throw new Error(`Unknown column: ${columnName}`);
    }

    const sortedRows = [...this.rows].sort((a, b) => {
      if (a[columnName] < b[columnName]) {
        return descending ? 1 : -1;
      }

      if (a[columnName] > b[columnName]) {
        return descending ? -1 : 1;
      }

      return 0;
    });

    return new StructuredTable(this.columns, sortedRows);
  }

  select(...columnNames) {
    for (const name of columnNames) {
      if (!this.columns.includes(name)) {
        throw new Error(`Unknown column: ${name}`);
      }
    }

    return this.rows.map(row => {
      const selected = {};

      for (const name of columnNames) {
        selected[name] = row[name];
      }

      return selected;
    });
  }

  sum(columnName) {
    return this.rows.reduce(
      (total, row) => total + Number(row[columnName] || 0),
      0
    );
  }

  average(columnName) {
    if (this.rows.length === 0) {
      throw new Error("Cannot average an empty table.");
    }

    return this.sum(columnName) / this.rows.length;
  }

  count() {
    return this.rows.length;
  }

  unique(columnName) {
    return [...new Set(this.rows.map(row => row[columnName]))];
  }

  groupSum(groupColumn, valueColumn) {
    const result = new Map();

    for (const row of this.rows) {
      const key = row[groupColumn];
      const oldValue = result.get(key) || 0;

      result.set(key, oldValue + Number(row[valueColumn] || 0));
    }

    return Object.fromEntries(result);
  }
}


// ---------------------------------------------------------------------------
// 3. BUILD A SALES TABLE
// ---------------------------------------------------------------------------

function buildSalesTable() {
  const columns = [
    "orderId",
    "customer",
    "region",
    "product",
    "category",
    "quantity",
    "unitPrice",
    "discountRate"
  ];

  const rows = [
    {
      orderId: 1001,
      customer: "Asha",
      region: "North",
      product: "Laptop",
      category: "Computers",
      quantity: 2,
      unitPrice: 75000,
      discountRate: 0.05
    },
    {
      orderId: 1002,
      customer: "Ravi",
      region: "South",
      product: "Monitor",
      category: "Displays",
      quantity: 3,
      unitPrice: 18000,
      discountRate: 0.10
    },
    {
      orderId: 1003,
      customer: "Meera",
      region: "North",
      product: "Keyboard",
      category: "Accessories",
      quantity: 5,
      unitPrice: 2500,
      discountRate: 0
    },
    {
      orderId: 1004,
      customer: "Kabir",
      region: "West",
      product: "Laptop",
      category: "Computers",
      quantity: 1,
      unitPrice: 82000,
      discountRate: 0.08
    },
    {
      orderId: 1005,
      customer: "Neha",
      region: "East",
      product: "Mouse",
      category: "Accessories",
      quantity: 10,
      unitPrice: 1200,
      discountRate: 0.02
    }
  ];

  return new StructuredTable(columns, rows);
}

function addSalesCalculations(table) {
  // Equivalent conceptually to:
  // =[@quantity]*[@unitPrice]
  table.addCalculatedColumn(
    "grossAmount",
    row => row.quantity * row.unitPrice
  );

  // Equivalent conceptually to:
  // =[@grossAmount]*[@discountRate]
  table.addCalculatedColumn(
    "discountAmount",
    row => row.grossAmount * row.discountRate
  );

  // Equivalent conceptually to:
  // =[@grossAmount]-[@discountAmount]
  table.addCalculatedColumn(
    "netAmount",
    row => row.grossAmount - row.discountAmount
  );

  // Conditional calculated column.
  table.addCalculatedColumn(
    "orderSize",
    row => row.netAmount >= 100000 ? "Large" : "Standard"
  );
}


// ---------------------------------------------------------------------------
// 4. DYNAMIC EXPANSION
// ---------------------------------------------------------------------------

function demonstrateDynamicExpansion() {
  console.log("\n=== DYNAMIC EXPANSION ===");

  const table = buildSalesTable();
  addSalesCalculations(table);

  console.log("Initial rows:", table.count());

  table.addRow({
    orderId: 1006,
    customer: "Arjun",
    region: "South",
    product: "Tablet",
    category: "Computers",
    quantity: 4,
    unitPrice: 30000,
    discountRate: 0.05,
    grossAmount: 0,
    discountAmount: 0,
    netAmount: 0,
    orderSize: "Pending"
  });

  // Recalculation models the propagation of a calculated-column formula.
  addSalesCalculations(table);

  console.log("Rows after expansion:", table.count());
  console.table(table.rows);
}


// ---------------------------------------------------------------------------
// 5. STRUCTURED REFERENCE CONCEPTS
// ---------------------------------------------------------------------------

function demonstrateStructuredReferences() {
  console.log("\n=== STRUCTURED REFERENCE CONCEPTS ===");

  const table = buildSalesTable();
  addSalesCalculations(table);

  // Table1[netAmount] is modeled by mapping the named column.
  const netAmounts = table.rows.map(row => row.netAmount);

  // Table1[@netAmount] corresponds conceptually to row.netAmount.
  console.log("Column values:", netAmounts);
  console.log("Total:", table.sum("netAmount"));
}


// ---------------------------------------------------------------------------
// 6. FILTERING
// ---------------------------------------------------------------------------

function demonstrateFiltering() {
  console.log("\n=== FILTERING ===");

  const table = buildSalesTable();
  addSalesCalculations(table);

  const northOrders = table.filter(
    row => row.region === "North"
  );

  const highValueOrders = table.filter(
    row => row.netAmount >= 50000
  );

  const northHighValue = table.filter(
    row => row.region === "North" &&
           row.netAmount >= 50000
  );

  console.log(
    "North:",
    northOrders.rows.map(row => row.orderId)
  );

  console.log(
    "High value:",
    highValueOrders.rows.map(row => row.orderId)
  );

  console.log(
    "North + high value:",
    northHighValue.rows.map(row => row.orderId)
  );
}


// ---------------------------------------------------------------------------
// 7. SORTING
// ---------------------------------------------------------------------------

function demonstrateSorting() {
  console.log("\n=== SORTING ===");

  const table = buildSalesTable();
  addSalesCalculations(table);

  const sorted = table.sortBy("netAmount", true);

  console.table(
    sorted.select("orderId", "product", "netAmount")
  );
}


// ---------------------------------------------------------------------------
// 8. AGGREGATION
// ---------------------------------------------------------------------------

function demonstrateAggregation() {
  console.log("\n=== AGGREGATION ===");

  const table = buildSalesTable();
  addSalesCalculations(table);

  console.log("Order count:", table.count());
  console.log("Total sales:", table.sum("netAmount"));
  console.log("Average order:", table.average("netAmount"));

  console.log(
    "Sales by region:",
    table.groupSum("region", "netAmount")
  );

  console.log(
    "Sales by category:",
    table.groupSum("category", "netAmount")
  );
}


// ---------------------------------------------------------------------------
// 9. TOTALS ROW
// ---------------------------------------------------------------------------

function calculateTotalsRow(table) {
  return {
    quantity: table.sum("quantity"),
    grossAmount: table.sum("grossAmount"),
    discountAmount: table.sum("discountAmount"),
    netAmount: table.sum("netAmount")
  };
}

function demonstrateTotalsRow() {
  console.log("\n=== TOTALS ROW ===");

  const table = buildSalesTable();
  addSalesCalculations(table);

  console.table(calculateTotalsRow(table));
}


// ---------------------------------------------------------------------------
// 10. VALIDATION
// ---------------------------------------------------------------------------

const validRegions = new Set([
  "North",
  "South",
  "East",
  "West"
]);

function validateSalesRow(row) {
  const errors = [];

  if (!Number.isInteger(row.orderId)) {
    errors.push("orderId must be an integer.");
  }

  if (typeof row.customer !== "string" ||
      row.customer.trim() === "") {
    errors.push("customer is required.");
  }

  if (!validRegions.has(row.region)) {
    errors.push("region is invalid.");
  }

  if (!Number.isInteger(row.quantity) ||
      row.quantity <= 0) {
    errors.push("quantity must be a positive integer.");
  }

  if (typeof row.unitPrice !== "number" ||
      !Number.isFinite(row.unitPrice) ||
      row.unitPrice < 0) {
    errors.push("unitPrice must be a non-negative number.");
  }

  if (typeof row.discountRate !== "number" ||
      row.discountRate < 0 ||
      row.discountRate > 1) {
    errors.push("discountRate must be between 0 and 1.");
  }

  return errors;
}

function demonstrateValidation() {
  console.log("\n=== VALIDATION ===");

  const invalidRow = {
    orderId: "bad",
    customer: "",
    region: "Unknown",
    quantity: 0,
    unitPrice: -100,
    discountRate: 2
  };

  console.log(validateSalesRow(invalidRow));
}


// ---------------------------------------------------------------------------
// 11. LOOKUPS
// ---------------------------------------------------------------------------

function linearLookup(rows, key, value) {
  return rows.find(row => row[key] === value) || null;
}

function buildIndex(rows, key) {
  const index = new Map();

  for (const row of rows) {
    if (index.has(row[key])) {
      throw new Error(`Duplicate key: ${row[key]}`);
    }

    index.set(row[key], row);
  }

  return index;
}

function demonstrateLookups() {
  console.log("\n=== LOOKUPS ===");

  const table = buildSalesTable();
  addSalesCalculations(table);

  const linearResult = linearLookup(
    table.rows,
    "orderId",
    1003
  );

  console.log(
    "Linear lookup:",
    linearResult?.customer
  );

  const index = buildIndex(table.rows, "orderId");
  const indexedResult = index.get(1003);

  console.log(
    "Indexed lookup:",
    indexedResult?.customer
  );
}


// ---------------------------------------------------------------------------
// 12. OPTIONAL VALUES
// ---------------------------------------------------------------------------

function safeNetAmount(row) {
  if (!Number.isFinite(row.quantity) ||
      !Number.isFinite(row.unitPrice)) {
    return null;
  }

  const discount = Number.isFinite(row.discountRate)
    ? row.discountRate
    : 0;

  return row.quantity *
         row.unitPrice *
         (1 - discount);
}

function demonstrateMissingValues() {
  console.log("\n=== MISSING VALUES ===");

  const examples = [
    {
      quantity: 2,
      unitPrice: 100,
      discountRate: 0.1
    },
    {
      quantity: null,
      unitPrice: 100,
      discountRate: 0.1
    },
    {
      quantity: 2,
      unitPrice: null,
      discountRate: 0.1
    }
  ];

  for (const row of examples) {
    console.log(safeNetAmount(row));
  }
}


// ---------------------------------------------------------------------------
// 13. ABSOLUTE AND RELATIVE PARAMETERS
// ---------------------------------------------------------------------------

function demonstrateReferenceSemantics() {
  console.log("\n=== RELATIVE AND SHARED PARAMETERS ===");

  // This models a shared absolute parameter such as:
  // =[@Amount]*(1+$B$1)
  //
  // amount changes by row while taxRate remains shared.
  const taxRate = 0.18;
  const amounts = [1000, 2500, 5000];

  for (const amount of amounts) {
    console.log(amount * (1 + taxRate));
  }
}


// ---------------------------------------------------------------------------
// 14. DYNAMIC UNIQUE RESULTS
// ---------------------------------------------------------------------------

function demonstrateDynamicArrays() {
  console.log("\n=== DYNAMIC RESULTS ===");

  const table = buildSalesTable();

  const regions = [...new Set(
    table.rows.map(row => row.region)
  )].sort();

  const products = [...new Set(
    table.rows.map(row => row.product)
  )].sort();

  const northProducts = [...new Set(
    table.rows
      .filter(row => row.region === "North")
      .map(row => row.product)
  )].sort();

  console.log("Regions:", regions);
  console.log("Products:", products);
  console.log("North products:", northProducts);
}


// ---------------------------------------------------------------------------
// 15. DEPENDENCY-AWARE CALCULATIONS
// ---------------------------------------------------------------------------

function addFinancialCalculations(table) {
  // Dependency chain:
  // grossRevenue
  //     ↓
  // discount
  //     ↓
  // netRevenue
  //     ↓
  // cost
  //     ↓
  // profit
  //     ↓
  // margin

  table.addCalculatedColumn(
    "grossRevenue",
    row => row.quantity * row.unitPrice
  );

  table.addCalculatedColumn(
    "discount",
    row => row.grossRevenue * row.discountRate
  );

  table.addCalculatedColumn(
    "netRevenue",
    row => row.grossRevenue - row.discount
  );

  table.addCalculatedColumn(
    "cost",
    row => row.netRevenue * 0.70
  );

  table.addCalculatedColumn(
    "profit",
    row => row.netRevenue - row.cost
  );

  table.addCalculatedColumn(
    "margin",
    row => row.netRevenue === 0
      ? 0
      : row.profit / row.netRevenue
  );
}

function demonstrateFinancialModel() {
  console.log("\n=== DEPENDENCY CHAIN ===");

  const table = buildSalesTable();
  addFinancialCalculations(table);

  console.table(
    table.select(
      "orderId",
      "netRevenue",
      "profit",
      "margin"
    )
  );
}


// ---------------------------------------------------------------------------
// 16. ASYNCHRONOUS APPLICATION PATTERN
// ---------------------------------------------------------------------------

function fetchSalesData() {
  // In a production application this could represent an HTTP/database
  // operation. The timeout makes the asynchronous execution model visible.
  return new Promise(resolve => {
    setTimeout(() => {
      resolve([
        {
          orderId: 2001,
          customer: "Isha",
          region: "East",
          product: "Laptop",
          category: "Computers",
          quantity: 2,
          unitPrice: 70000,
          discountRate: 0.05
        },
        {
          orderId: 2002,
          customer: "Dev",
          region: "West",
          product: "Monitor",
          category: "Displays",
          quantity: 4,
          unitPrice: 15000,
          discountRate: 0.08
        }
      ]);
    }, 10);
  });
}

async function demonstrateAsyncPipeline() {
  console.log("\n=== ASYNCHRONOUS DATA PIPELINE ===");

  const rawRows = await fetchSalesData();

  const table = new StructuredTable(
    [
      "orderId",
      "customer",
      "region",
      "product",
      "category",
      "quantity",
      "unitPrice",
      "discountRate"
    ],
    rawRows
  );

  addSalesCalculations(table);

  const highValue = table.filter(
    row => row.netAmount >= 50000
  );

  console.table(
    highValue.select(
      "orderId",
      "customer",
      "netAmount"
    )
  );
}


// ---------------------------------------------------------------------------
// 17. PERFORMANCE TEST
// ---------------------------------------------------------------------------

function benchmarkLookup() {
  console.log("\n=== LOOKUP PERFORMANCE ===");

  const rows = Array.from(
    { length: 10000 },
    (_, index) => ({
      id: index + 1,
      value: (index + 1) * 10
    })
  );

  const target = 9999;
  const iterations = 1000;

  let start = performance.now();

  for (let i = 0; i < iterations; i++) {
    linearLookup(rows, "id", target);
  }

  const linearMilliseconds = performance.now() - start;

  const index = buildIndex(rows, "id");

  start = performance.now();

  for (let i = 0; i < iterations; i++) {
    index.get(target);
  }

  const indexedMilliseconds = performance.now() - start;

  console.log(
    "Linear lookup:",
    `${linearMilliseconds.toFixed(3)} ms`
  );

  console.log(
    "Indexed lookup:",
    `${indexedMilliseconds.toFixed(3)} ms`
  );
}


// ---------------------------------------------------------------------------
// 18. TESTING
// ---------------------------------------------------------------------------

function runTests() {
  console.log("\n=== TESTS ===");

  const table = buildSalesTable();
  addSalesCalculations(table);

  if (table.rows[0].grossAmount !== 150000) {
    throw new Error("Gross calculation failed.");
  }

  if (table.rows[0].discountAmount !== 7500) {
    throw new Error("Discount calculation failed.");
  }

  if (table.rows[0].netAmount !== 142500) {
    throw new Error("Net calculation failed.");
  }

  if (table.count() !== 5) {
    throw new Error("Row count test failed.");
  }

  const invalidErrors = validateSalesRow({
    orderId: "bad",
    customer: "",
    region: "Invalid",
    quantity: 0,
    unitPrice: -10,
    discountRate: 2
  });

  if (invalidErrors.length === 0) {
    throw new Error("Validation test failed.");
  }

  console.log("All tests passed.");
}


// ---------------------------------------------------------------------------
// 19. PRODUCTION DESIGN RULES
// ---------------------------------------------------------------------------

function printDesignRules() {
  console.log("\n=== PRODUCTION DESIGN RULES ===");

  const rules = [
    "Keep one logical record per row.",
    "Use stable and descriptive column names.",
    "Keep input columns separate from calculated columns.",
    "Validate imported data before processing it.",
    "Do not evaluate untrusted strings as executable code.",
    "Use an index for repeated key-based lookups.",
    "Use explicit handling for missing values.",
    "Keep dependent calculations in a deterministic order.",
    "Test financial calculations with known expected results.",
    "Use appropriate access controls for confidential spreadsheet data."
  ];

  for (const rule of rules) {
    console.log("-", rule);
  }
}


// ---------------------------------------------------------------------------
// 20. MAIN PROGRAM
// ---------------------------------------------------------------------------

async function main() {
  console.log("Excel Tables: Structured Data and Dynamic Calculations");

  demonstrateDynamicExpansion();
  demonstrateStructuredReferences();
  demonstrateFiltering();
  demonstrateSorting();
  demonstrateAggregation();
  demonstrateTotalsRow();
  demonstrateValidation();
  demonstrateLookups();
  demonstrateMissingValues();
  demonstrateReferenceSemantics();
  demonstrateDynamicArrays();
  demonstrateFinancialModel();
  await demonstrateAsyncPipeline();
  benchmarkLookup();
  runTests();
  printDesignRules();

  console.log("\nStudy program completed.");
}

main().catch(error => {
  console.error("Program error:", error.message);
  process.exitCode = 1;
});
