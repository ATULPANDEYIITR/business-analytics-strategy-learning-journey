"use strict";

/*
 * Data Quality Engineering in JavaScript
 *
 * This implementation focuses on an event-driven quality pipeline.
 * Accuracy, completeness, consistency, and validity are deliberately
 * represented as different rule families.
 */

const readline = require("node:readline");

// ---------------------------------------------------------------------------
// Domain configuration
// ---------------------------------------------------------------------------

const DIMENSIONS = Object.freeze({
  ACCURACY: "accuracy",
  COMPLETENESS: "completeness",
  CONSISTENCY: "consistency",
  VALIDITY: "validity"
});

const REQUIRED_FIELDS = Object.freeze([
  "customerId",
  "name",
  "email",
  "country",
  "currency",
  "status",
  "signupDate",
  "creditLimit"
]);

const VALID_COUNTRIES = new Set(["IN", "US", "GB", "DE", "FR", "JP", "SG", "AU"]);
const VALID_STATUSES = new Set(["active", "inactive", "pending"]);

const CURRENCY_BY_COUNTRY = Object.freeze({
  IN: "INR",
  US: "USD",
  GB: "GBP",
  DE: "EUR",
  FR: "EUR",
  JP: "JPY",
  SG: "SGD",
  AU: "AUD"
});

const VERIFIED_CUSTOMERS = Object.freeze({
  C1001: {
    email: "atul@example.com",
    country: "IN",
    currency: "INR"
  }
});

// ---------------------------------------------------------------------------
// Event bus
//
// Quality events make the pipeline observable. A production system could
// route these events to logs, metrics, a queue, or an audit system.
// ---------------------------------------------------------------------------

class QualityEventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(eventName, listener) {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, []);
    }
    this.listeners.get(eventName).push(listener);
  }

  emit(eventName, payload) {
    for (const listener of this.listeners.get(eventName) ?? []) {
      listener(payload);
    }
  }
}

// ---------------------------------------------------------------------------
// Quality issue model
// ---------------------------------------------------------------------------

class QualityIssue {
  constructor({ dimension, field, recordId, message, value, severity = "error" }) {
    this.dimension = dimension;
    this.field = field;
    this.recordId = recordId;
    this.message = message;
    this.value = value;
    this.severity = severity;
  }
}

// ---------------------------------------------------------------------------
// Rule abstractions
// ---------------------------------------------------------------------------

class QualityRule {
  constructor(name, dimension, evaluator) {
    this.name = name;
    this.dimension = dimension;
    this.evaluator = evaluator;
  }

  evaluate(record, context) {
    return this.evaluator(record, context);
  }
}

function issue(rule, record, field, message, value) {
  return new QualityIssue({
    dimension: rule.dimension,
    field,
    recordId: String(record.customerId ?? "<missing-id>"),
    message,
    value
  });
}

// ---------------------------------------------------------------------------
// Rule definitions
// ---------------------------------------------------------------------------

function createRules() {
  return [
    new QualityRule(
      "required-fields",
      DIMENSIONS.COMPLETENESS,
      (record) => {
        const issues = [];

        for (const field of REQUIRED_FIELDS) {
          const value = record[field];

          if (value === undefined || value === null || String(value).trim() === "") {
            issues.push(
              new QualityIssue({
                dimension: DIMENSIONS.COMPLETENESS,
                field,
                recordId: String(record.customerId ?? "<missing-id>"),
                message: "Required value is missing or empty.",
                value
              })
            );
          }
        }

        return issues;
      }
    ),

    new QualityRule(
      "email-format",
      DIMENSIONS.VALIDITY,
      (record) => {
        if (!record.email) return [];

        const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        return pattern.test(record.email)
          ? []
          : [
              issue(
                { dimension: DIMENSIONS.VALIDITY },
                record,
                "email",
                "Email format is invalid.",
                record.email
              )
            ];
      }
    ),

    new QualityRule(
      "domain-values",
      DIMENSIONS.VALIDITY,
      (record) => {
        const issues = [];

        if (!VALID_COUNTRIES.has(record.country)) {
          issues.push(
            issue(
              { dimension: DIMENSIONS.VALIDITY },
              record,
              "country",
              "Country code is outside the accepted domain.",
              record.country
            )
          );
        }

        if (!VALID_STATUSES.has(record.status)) {
          issues.push(
            issue(
              { dimension: DIMENSIONS.VALIDITY },
              record,
              "status",
              "Status is outside the accepted domain.",
              record.status
            )
          );
        }

        return issues;
      }
    ),

    new QualityRule(
      "date-and-number-ranges",
      DIMENSIONS.VALIDITY,
      (record) => {
        const issues = [];
        const parsedDate = new Date(`${record.signupDate}T00:00:00`);
        const creditLimit = Number(record.creditLimit);

        if (
          Number.isNaN(parsedDate.getTime()) ||
          !/^\d{4}-\d{2}-\d{2}$/.test(String(record.signupDate))
        ) {
          issues.push(
            issue(
              { dimension: DIMENSIONS.VALIDITY },
              record,
              "signupDate",
              "Signup date must use YYYY-MM-DD.",
              record.signupDate
            )
          );
        } else if (parsedDate > new Date()) {
          issues.push(
            issue(
              { dimension: DIMENSIONS.VALIDITY },
              record,
              "signupDate",
              "Signup date cannot be in the future.",
              record.signupDate
            )
          );
        }

        if (!Number.isFinite(creditLimit) || creditLimit < 0) {
          issues.push(
            issue(
              { dimension: DIMENSIONS.VALIDITY },
              record,
              "creditLimit",
              "Credit limit must be a non-negative number.",
              record.creditLimit
            )
          );
        }

        return issues;
      }
    ),

    new QualityRule(
      "country-currency",
      DIMENSIONS.CONSISTENCY,
      (record) => {
        const expected = CURRENCY_BY_COUNTRY[record.country];

        if (!expected || record.currency === expected) {
          return [];
        }

        return [
          issue(
            { dimension: DIMENSIONS.CONSISTENCY },
            record,
            "currency",
            `Currency ${record.currency} conflicts with country ${record.country}.`,
            record.currency
          )
        ];
      }
    ),

    new QualityRule(
      "status-credit-policy",
      DIMENSIONS.CONSISTENCY,
      (record) => {
        const creditLimit = Number(record.creditLimit);

        if (record.status === "inactive" && Number.isFinite(creditLimit) && creditLimit > 0) {
          return [
            issue(
              { dimension: DIMENSIONS.CONSISTENCY },
              record,
              "creditLimit",
              "Inactive customer has a positive credit limit.",
              record.creditLimit
            )
          ];
        }

        return [];
      }
    ),

    new QualityRule(
      "verified-reference",
      DIMENSIONS.ACCURACY,
      (record) => {
        const verified = VERIFIED_CUSTOMERS[record.customerId];
        if (!verified) return [];

        const issues = [];

        for (const [field, expected] of Object.entries(verified)) {
          if (record[field] !== expected) {
            issues.push(
              issue(
                { dimension: DIMENSIONS.ACCURACY },
                record,
                field,
                `Value differs from verified reference value ${expected}.`,
                record[field]
              )
            );
          }
        }

        return issues;
      }
    )
  ];
}

// ---------------------------------------------------------------------------
// Dataset-level consistency checks
// ---------------------------------------------------------------------------

function datasetRules(records) {
  const issues = [];
  const idCounts = new Map();
  const emailOwners = new Map();

  for (const record of records) {
    const id = String(record.customerId ?? "<missing-id>");
    idCounts.set(id, (idCounts.get(id) ?? 0) + 1);

    const email = String(record.email ?? "").trim().toLowerCase();
    if (email) {
      if (!emailOwners.has(email)) emailOwners.set(email, []);
      emailOwners.get(email).push(id);
    }
  }

  for (const [id, count] of idCounts) {
    if (id !== "<missing-id>" && count > 1) {
      issues.push(
        new QualityIssue({
          dimension: DIMENSIONS.CONSISTENCY,
          field: "customerId",
          recordId: id,
          message: `Customer identifier appears ${count} times.`,
          value: id
        })
      );
    }
  }

  for (const [email, owners] of emailOwners) {
    if (owners.length > 1) {
      for (const id of owners) {
        issues.push(
          new QualityIssue({
            dimension: DIMENSIONS.CONSISTENCY,
            field: "email",
            recordId: id,
            message: "Email address belongs to multiple customer records.",
            value: email
          })
        );
      }
    }
  }

  return issues;
}

// ---------------------------------------------------------------------------
// Quality pipeline
// ---------------------------------------------------------------------------

class QualityPipeline {
  constructor(rules, eventBus) {
    this.rules = rules;
    this.eventBus = eventBus;
  }

  normalize(records) {
    return records.map((record) => ({
      ...record,
      customerId: typeof record.customerId === "string"
        ? record.customerId.trim()
        : record.customerId,
      name: typeof record.name === "string" ? record.name.trim() : record.name,
      email: typeof record.email === "string"
        ? record.email.trim().toLowerCase()
        : record.email,
      country: typeof record.country === "string"
        ? record.country.trim().toUpperCase()
        : record.country,
      currency: typeof record.currency === "string"
        ? record.currency.trim().toUpperCase()
        : record.currency,
      status: typeof record.status === "string"
        ? record.status.trim().toLowerCase()
        : record.status
    }));
  }

  run(records) {
    const issues = [];
    const normalized = this.normalize(records);

    this.eventBus.emit("quality.started", {
      recordCount: normalized.length
    });

    for (const record of normalized) {
      for (const rule of this.rules) {
        const ruleIssues = rule.evaluate(record, { records: normalized });

        for (const foundIssue of ruleIssues) {
          issues.push(foundIssue);
          this.eventBus.emit("quality.issue", foundIssue);
        }
      }
    }

    for (const foundIssue of datasetRules(normalized)) {
      issues.push(foundIssue);
      this.eventBus.emit("quality.issue", foundIssue);
    }

    const scores = this.calculateScores(normalized, issues);

    const report = {
      totalRecords: normalized.length,
      validRecords: normalized.filter(
        (record) =>
          !issues.some(
            (foundIssue) =>
              foundIssue.recordId === String(record.customerId)
          )
      ).length,
      issues,
      scores
    };

    this.eventBus.emit("quality.completed", report);

    return report;
  }

  calculateScores(records, issues) {
    const dimensions = Object.values(DIMENSIONS);
    const affected = new Map(dimensions.map((dimension) => [dimension, new Set()]));

    for (const foundIssue of issues) {
      affected.get(foundIssue.dimension)?.add(foundIssue.recordId);
    }

    return Object.fromEntries(
      dimensions.map((dimension) => {
        const affectedCount = affected.get(dimension).size;
        const score = records.length === 0
          ? 100
          : ((records.length - affectedCount) / records.length) * 100;

        return [dimension, Number(score.toFixed(2))];
      })
    );
  }
}

// ---------------------------------------------------------------------------
// Demonstration
// ---------------------------------------------------------------------------

const records = [
  {
    customerId: "C1001",
    name: " Atul Pandey ",
    email: "ATUL@EXAMPLE.COM",
    country: "in",
    currency: "INR",
    status: "active",
    signupDate: "2026-01-15",
    creditLimit: "500000"
  },
  {
    customerId: "C1002",
    name: "Maria Silva",
    email: "maria.changed@example.com",
    country: "DE",
    currency: "EUR",
    status: "active",
    signupDate: "2026-02-12",
    creditLimit: "75000"
  },
  {
    customerId: "C1003",
    name: "Ravi Kumar",
    email: "",
    country: "IN",
    currency: "INR",
    status: "pending",
    signupDate: "2026-03-10",
    creditLimit: "25000"
  },
  {
    customerId: "C1004",
    name: "Elena7",
    email: "elena@example",
    country: "XX",
    currency: "USD",
    status: "unknown",
    signupDate: "2027-04-01",
    creditLimit: "-500"
  },
  {
    customerId: "C1005",
    name: "John Smith",
    email: "john@example.com",
    country: "US",
    currency: "EUR",
    status: "inactive",
    signupDate: "2026-02-01",
    creditLimit: "1000"
  },
  {
    customerId: "C1006",
    name: "Duplicate User",
    email: "atul@example.com",
    country: "IN",
    currency: "INR",
    status: "active",
    signupDate: "2026-04-01",
    creditLimit: "30000"
  }
];

const bus = new QualityEventBus();

bus.on("quality.started", ({ recordCount }) => {
  console.log(`Quality pipeline started for ${recordCount} records.`);
});

bus.on("quality.issue", (foundIssue) => {
  console.log(
    `[${foundIssue.dimension}] ${foundIssue.recordId}.${foundIssue.field}: ` +
    foundIssue.message
  );
});

bus.on("quality.completed", (report) => {
  console.log("\nQUALITY SCORECARD");
  console.table(report.scores);
  console.log(`Valid records: ${report.validRecords}/${report.totalRecords}`);
});

const pipeline = new QualityPipeline(createRules(), bus);
const report = pipeline.run(records);

// A quality gate can stop downstream processing when the operational
// threshold is not achieved. This makes data quality an enforcement step,
// not merely a reporting activity.
const minimumOverallScore = 90;
const overallScore =
  Object.values(report.scores).reduce((sum, score) => sum + score, 0) /
  Object.values(report.scores).length;

if (overallScore < minimumOverallScore) {
  console.error(
    `QUALITY GATE FAILED: ${overallScore.toFixed(2)} < ${minimumOverallScore}`
  );
} else {
  console.log("QUALITY GATE PASSED.");
}

// ---------------------------------------------------------------------------
// Small asynchronous example
//
// The asynchronous function models a common production boundary where data
// arrives from a file, message queue, HTTP service, or database.
// ---------------------------------------------------------------------------

async function validateIncomingBatch(batch) {
  await Promise.resolve();

  const batchReport = pipeline.run(batch);

  return {
    accepted: batchReport.issues.length === 0,
    report: batchReport
  };
}

validateIncomingBatch([
  {
    customerId: "ASYNC-1",
    name: "Valid Customer",
    email: "valid@example.com",
    country: "IN",
    currency: "INR",
    status: "active",
    signupDate: "2026-04-01",
    creditLimit: "10000"
  }
]).then((result) => {
  console.log(`\nAsync batch accepted: ${result.accepted}`);
});
