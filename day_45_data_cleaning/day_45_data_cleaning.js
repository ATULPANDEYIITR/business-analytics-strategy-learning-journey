/**
 * Data Cleaning: Missing Values, Duplicates, and Inconsistent Data
 *
 * Node.js-compatible implementation using JavaScript-specific techniques:
 * Maps and Sets for duplicate detection, event-driven audit reporting,
 * immutable normalization stages, validation, and asynchronous processing.
 */

"use strict";

const rawRecords = [
  {
    customerId: "C001",
    name: "Asha Sharma",
    email: "ASHA@EXAMPLE.COM",
    phone: "+91 98765 43210",
    city: "Lucknow",
    amount: "1250",
    currency: "INR",
    status: "active",
    signupDate: "2026-01-05"
  },
  {
    customerId: "C002",
    name: "Rahul Verma",
    email: "rahul@example.com",
    phone: "9876543211",
    city: "Lucknow",
    amount: "850",
    currency: "inr",
    status: "Active",
    signupDate: "05/01/2026"
  },
  {
    customerId: "C003",
    name: "Meera Singh",
    email: "",
    phone: "+91-91234-56789",
    city: "Kanpur",
    amount: null,
    currency: "INR",
    status: "ACTIVE",
    signupDate: "2026-01-08"
  },
  {
    customerId: "C004",
    name: "Arun Kumar",
    email: "arun@example.com",
    phone: null,
    city: "Kanpur",
    amount: "450",
    currency: "INR",
    status: "active",
    signupDate: "2026-01-09"
  },
  {
    customerId: "C005",
    name: "Neha Gupta",
    email: "neha@example.com",
    phone: "+91 90000 11111",
    city: "Lucknow",
    amount: "1250",
    currency: "INR",
    status: "Active",
    signupDate: "2026-01-10"
  },
  {
    customerId: "C005",
    name: "Neha Gupta",
    email: "neha@example.com",
    phone: "+91 90000 11111",
    city: "Lucknow",
    amount: "1250",
    currency: "INR",
    status: "Active",
    signupDate: "2026-01-10"
  },
  {
    customerId: "C006",
    name: "Ravi Patel",
    email: "ravi@example.com",
    phone: "+91-98888-22222",
    city: "lucknow",
    amount: "850",
    currency: "INR",
    status: "active",
    signupDate: "2026-01-11"
  },
  {
    customerId: "C007",
    name: "Sonia Rao",
    email: "sonia@example.com",
    phone: "+91 97777 33333",
    city: "Kanpur",
    amount: "N/A",
    currency: "INR",
    status: "pending",
    signupDate: "2026-01-12"
  },
  {
    customerId: "C008",
    name: "Vikram Das",
    email: "vIKRAM@EXAMPLE.COM",
    phone: "+91 96666 44444",
    city: "Kanpur",
    amount: "1,250",
    currency: "INR",
    status: "active",
    signupDate: "2026-01-13"
  },
  {
    customerId: "C009",
    name: "Pooja Nair",
    email: "pooja@example.com",
    phone: "+91 95555 55555",
    city: "Lucknow",
    amount: "1250",
    currency: "Rs.",
    status: "active",
    signupDate: "2026-01-14"
  },
  {
    customerId: "C010",
    name: "Dev Shah",
    email: "dev@example.com",
    phone: "+91 94444 66666",
    city: "Lucknow",
    amount: "900",
    currency: "INR",
    status: "ACTIVE",
    signupDate: null
  }
];

const MISSING_TOKENS = new Set([
  "", "na", "n/a", "null", "none", "unknown", "-", "--"
]);

class CleaningEventBus extends require("events") {
  record(event) {
    this.emit("cleaning-event", event);
  }
}

const eventBus = new CleaningEventBus();
const auditLog = [];

eventBus.on("cleaning-event", (event) => {
  auditLog.push(Object.freeze({ ...event }));
});

function normalizeMissing(value) {
  if (value === null || value === undefined) {
    return null;
  }

  const text = String(value).trim();

  return MISSING_TOKENS.has(text.toLowerCase()) ? null : text;
}

function normalizeName(value) {
  if (value === null) return null;
  return String(value).trim().replace(/\s+/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function normalizeEmail(value) {
  if (value === null) return null;

  const email = String(value).trim().toLowerCase();

  if (email === "") return null;

  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? email : email;
}

function normalizePhone(value) {
  if (value === null) return null;

  const digits = String(value).replace(/\D/g, "");

  if (!digits) return null;

  if (digits.startsWith("91") && digits.length === 12) {
    return `+91 ${digits.slice(2, 7)} ${digits.slice(7)}`;
  }

  if (digits.length === 10) {
    return `+91 ${digits.slice(0, 5)} ${digits.slice(5)}`;
  }

  return `+${digits}`;
}

function normalizeCity(value) {
  if (value === null) return null;

  const token = String(value).trim().toLowerCase();

  const aliases = new Map([
    ["lucknow", "Lucknow"],
    ["lko", "Lucknow"],
    ["kanpur", "Kanpur"],
    ["knp", "Kanpur"]
  ]);

  return aliases.get(token) || token.replace(/\b\w/g, c => c.toUpperCase());
}

function normalizeAmount(value) {
  if (value === null) return null;

  const cleaned = String(value)
    .trim()
    .replace(/,/g, "")
    .replace(/^(rs\.?|inr)\s*/i, "");

  if (!cleaned || MISSING_TOKENS.has(cleaned.toLowerCase())) {
    return null;
  }

  const amount = Number(cleaned);

  if (!Number.isFinite(amount)) {
    return null;
  }

  if (amount < 0) {
    throw new Error("Transaction amount cannot be negative");
  }

  return amount;
}

function normalizeCurrency(value) {
  if (value === null) return null;

  const token = String(value).trim().toUpperCase();

  const aliases = new Map([
    ["RS", "INR"],
    ["RS.", "INR"],
    ["₹", "INR"],
    ["RUPEE", "INR"],
    ["RUPEES", "INR"]
  ]);

  return aliases.get(token) || token;
}

function normalizeStatus(value) {
  if (value === null) return null;

  const token = String(value).trim().toLowerCase();

  const aliases = new Map([
    ["active", "active"],
    ["act", "active"],
    ["pending", "pending"],
    ["pend", "pending"],
    ["inactive", "inactive"],
    ["in-active", "inactive"]
  ]);

  return aliases.get(token) || token;
}

function normalizeDate(value) {
  if (value === null) return null;

  const text = String(value).trim();

  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
    return text;
  }

  const match = text.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);

  if (match) {
    return `${match[3]}-${match[2]}-${match[1]}`;
  }

  return text;
}

function normalizeRecord(raw, rowNumber) {
  const record = {};

  for (const [field, rawValue] of Object.entries(raw)) {
    const normalized = normalizeMissing(rawValue);
    record[field] = normalized;

    if (rawValue !== normalized) {
      eventBus.record({
        rowNumber,
        field,
        issue: "missing_value",
        action: "standardized",
        original: rawValue,
        cleaned: normalized
      });
    }
  }

  const transformations = {
    name: normalizeName,
    email: normalizeEmail,
    phone: normalizePhone,
    city: normalizeCity,
    amount: normalizeAmount,
    currency: normalizeCurrency,
    status: normalizeStatus,
    signupDate: normalizeDate
  };

  for (const [field, transform] of Object.entries(transformations)) {
    const before = record[field];
    let after;

    try {
      after = transform(before);
    } catch (error) {
      eventBus.record({
        rowNumber,
        field,
        issue: "invalid_value",
        action: "rejected",
        original: before,
        cleaned: null,
        reason: error.message
      });
      after = null;
    }

    record[field] = after;

    if (before !== null && before !== after) {
      eventBus.record({
        rowNumber,
        field,
        issue: "inconsistent_representation",
        action: "normalized",
        original: before,
        cleaned: after
      });
    }
  }

  return Object.freeze(record);
}

function duplicateKey(record) {
  return [
    record.customerId,
    record.name,
    record.email,
    record.phone,
    record.city,
    record.amount,
    record.currency,
    record.status,
    record.signupDate
  ].map(value => value === null ? "<NULL>" : String(value)).join("|");
}

function removeDuplicates(records) {
  const seen = new Map();
  const result = [];

  records.forEach((record, index) => {
    const key = duplicateKey(record);

    if (seen.has(key)) {
      eventBus.record({
        rowNumber: index + 2,
        issue: "duplicate",
        action: "removed",
        duplicateOfRow: seen.get(key)
      });
      return;
    }

    seen.set(key, index + 2);
    result.push(record);
  });

  return result;
}

function calculateCityMedians(records) {
  const cityValues = new Map();

  for (const record of records) {
    if (record.amount === null) continue;

    if (!cityValues.has(record.city)) {
      cityValues.set(record.city, []);
    }

    cityValues.get(record.city).push(record.amount);
  }

  const medians = new Map();

  for (const [city, values] of cityValues.entries()) {
    const ordered = [...values].sort((a, b) => a - b);
    const middle = Math.floor(ordered.length / 2);

    const median = ordered.length % 2 === 1
      ? ordered[middle]
      : (ordered[middle - 1] + ordered[middle]) / 2;

    medians.set(city, median);
  }

  return medians;
}

function imputeMissingAmounts(records) {
  const medians = calculateCityMedians(records);

  return records.map((record, index) => {
    if (record.amount !== null || !medians.has(record.city)) {
      return record;
    }

    const replacement = medians.get(record.city);

    eventBus.record({
      rowNumber: index + 2,
      field: "amount",
      issue: "missing_value",
      action: "imputed",
      original: null,
      cleaned: replacement,
      reason: "City-level median"
    });

    return Object.freeze({
      ...record,
      amount: replacement
    });
  });
}

function validateRecord(record) {
  const errors = [];

  if (!record.customerId) {
    errors.push("customerId is required");
  }

  if (!record.name) {
    errors.push("name is required");
  }

  if (
    record.email !== null &&
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(record.email)
  ) {
    errors.push("email has invalid structure");
  }

  if (record.amount !== null && record.amount < 0) {
    errors.push("amount cannot be negative");
  }

  if (
    record.currency !== null &&
    !new Set(["INR", "USD", "EUR", "GBP"]).has(record.currency)
  ) {
    errors.push("unsupported currency");
  }

  if (
    record.status !== null &&
    !new Set(["active", "pending", "inactive"]).has(record.status)
  ) {
    errors.push("unsupported status");
  }

  if (
    record.signupDate !== null &&
    !/^\d{4}-\d{2}-\d{2}$/.test(record.signupDate)
  ) {
    errors.push("signupDate is not canonical ISO format");
  }

  return errors;
}

async function cleanDataset(records) {
  /*
   * Promise.resolve creates an asynchronous boundary without introducing
   * an unnecessary dependency. This makes the pipeline easy to place
   * behind an asynchronous file or API ingestion layer in production.
   */
  const normalized = await Promise.resolve(
    records.map((record, index) => normalizeRecord(record, index + 2))
  );

  const deduplicated = removeDuplicates(normalized);
  return imputeMissingAmounts(deduplicated);
}

function calculateQualityMetrics(source, cleaned) {
  const sourceMissingCells = source.reduce(
    (total, record) =>
      total + Object.values(record).filter(
        value => normalizeMissing(value) === null
      ).length,
    0
  );

  const duplicateEvents = auditLog.filter(
    event => event.issue === "duplicate"
  ).length;

  const inconsistencyEvents = auditLog.filter(
    event => event.issue === "inconsistent_representation"
  ).length;

  const completeRows = cleaned.filter(
    record => Object.values(record).every(value => value !== null)
  ).length;

  return {
    sourceRows: source.length,
    cleanedRows: cleaned.length,
    sourceMissingCells,
    duplicateRowsRemoved: duplicateEvents,
    inconsistentRepresentationsNormalized: inconsistencyEvents,
    completeCleanedRows: completeRows,
    completenessRate: cleaned.length === 0
      ? 100
      : (completeRows / cleaned.length) * 100
  };
}

function printAudit() {
  console.log("\nCLEANING AUDIT");
  console.log("=".repeat(80));

  for (const event of auditLog) {
    console.log(JSON.stringify(event));
  }
}

async function main() {
  console.log("DATA CLEANING PIPELINE");
  console.log("=".repeat(80));
  console.log(
    "Focus: missing values, duplicate records, and inconsistent representations"
  );

  const cleaned = await cleanDataset(rawRecords);

  const validationFailures = cleaned
    .map((record, index) => ({
      rowNumber: index + 2,
      errors: validateRecord(record)
    }))
    .filter(item => item.errors.length > 0);

  const metrics = calculateQualityMetrics(rawRecords, cleaned);

  console.log("\nQUALITY METRICS");
  console.table(metrics);

  printAudit();

  if (validationFailures.length > 0) {
    console.log("\nVALIDATION FAILURES");
    console.table(validationFailures);
  }

  console.log("\nCLEANED DATA");
  console.table(cleaned);

  console.log("\nCLEANED JSON");
  console.log(JSON.stringify(cleaned, null, 2));
}

main().catch(error => {
  console.error("Cleaning pipeline failed:", error.message);
  process.exitCode = 1;
});
