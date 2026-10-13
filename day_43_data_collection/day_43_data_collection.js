"use strict";

/*
 * Data collection workflow for a retail analytics service.
 *
 * Demonstrates source-specific event handling, asynchronous ingestion,
 * schema validation, consent-aware behavioral collection, transactional
 * events, retryable failures, deduplication, and derived metrics.
 *
 * Run with Node.js 18 or later:
 *     node data_collection.js
 */

const crypto = require("node:crypto");
const { setTimeout: delay } = require("node:timers/promises");

const Categories = Object.freeze({
  INTERNAL: "internal",
  EXTERNAL: "external",
  TRANSACTIONAL: "transactional",
  BEHAVIORAL: "behavioral",
});

class CollectionError extends Error {
  constructor(message, code = "INVALID_RECORD") {
    super(message);
    this.name = "CollectionError";
    this.code = code;
  }
}

function requireNonEmptyString(value, fieldName) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new CollectionError(`${fieldName} must be a non-empty string.`);
  }
  return value.trim();
}

function parseTimestamp(value) {
  const timestamp = new Date(value);

  if (Number.isNaN(timestamp.getTime())) {
    throw new CollectionError(`Invalid timestamp: ${String(value)}`);
  }

  return timestamp.toISOString();
}

function parseMoney(value) {
  // Decimal arithmetic is not built into JavaScript. Store money as integer
  // minor units so aggregation does not depend on binary floating point.
  const normalized = String(value).trim();
  const match = normalized.match(/^(0|[1-9]\d*)(?:\.(\d{1,2}))?$/);

  if (!match) {
    throw new CollectionError(
      `Invalid non-negative monetary amount: ${normalized}`
    );
  }

  const fraction = (match[2] || "").padEnd(2, "0");
  const minorUnits = BigInt(match[1]) * 100n + BigInt(fraction || "0");

  return minorUnits;
}

function formatMoney(minorUnits) {
  const sign = minorUnits < 0n ? "-" : "";
  const absolute = minorUnits < 0n ? -minorUnits : minorUnits;

  return `${sign}${absolute / 100n}.${String(absolute % 100n).padStart(2, "0")}`;
}

function fingerprint(source, externalId) {
  const material = [
    requireNonEmptyString(source, "source").toLowerCase(),
    requireNonEmptyString(externalId, "externalId"),
  ].join(":");

  return crypto.createHash("sha256").update(material).digest("hex");
}

class ConsentRegistry {
  #permissions = new Map();

  setPermission(subjectId, purpose, allowed) {
    requireNonEmptyString(subjectId, "subjectId");
    requireNonEmptyString(purpose, "purpose");

    if (typeof allowed !== "boolean") {
      throw new CollectionError("Permission must be a boolean.");
    }

    this.#permissions.set(`${subjectId}:${purpose}`, allowed);
  }

  allows(subjectId, purpose) {
    return this.#permissions.get(`${subjectId}:${purpose}`) === true;
  }
}

class SourceAdapter {
  constructor(sourceName, category, schemaValidator) {
    this.sourceName = requireNonEmptyString(sourceName, "sourceName");
    this.category = category;
    this.schemaValidator = schemaValidator;

    if (!Object.values(Categories).includes(category)) {
      throw new CollectionError(`Unknown category: ${category}`);
    }
  }

  normalize(rawPayload) {
    const normalized = this.schemaValidator(rawPayload);
    return Object.freeze({ ...normalized });
  }
}

const adapters = {
  inventory: new SourceAdapter(
    "erp_inventory",
    Categories.INTERNAL,
    (payload) => {
      const available = Number(payload.availableUnits);
      const reserved = Number(payload.reservedUnits);

      if (
        !Number.isInteger(available) ||
        !Number.isInteger(reserved) ||
        available < 0 ||
        reserved < 0 ||
        reserved > available
      ) {
        throw new CollectionError("Invalid inventory quantities.");
      }

      return {
        warehouse: requireNonEmptyString(payload.warehouse, "warehouse"),
        sku: requireNonEmptyString(payload.sku, "sku"),
        availableUnits: available,
        reservedUnits: reserved,
      };
    }
  ),

  supplier: new SourceAdapter(
    "supplier_catalog_api",
    Categories.EXTERNAL,
    (payload) => {
      if (!["INR", "USD", "EUR", "GBP"].includes(payload.currency)) {
        throw new CollectionError("Unsupported supplier currency.");
      }

      return {
        supplier: requireNonEmptyString(payload.supplier, "supplier"),
        sku: requireNonEmptyString(payload.sku, "sku"),
        unitPrice: formatMoney(parseMoney(payload.unitPrice)),
        currency: payload.currency,
        revision: requireNonEmptyString(payload.revision, "revision"),
      };
    }
  ),

  order: new SourceAdapter(
    "order_management",
    Categories.TRANSACTIONAL,
    (payload) => {
      const status = payload.status;

      if (!["pending", "paid", "refunded", "cancelled"].includes(status)) {
        throw new CollectionError("Unsupported order status.");
      }

      if (!Array.isArray(payload.items) || payload.items.length === 0) {
        throw new CollectionError("An order must contain at least one item.");
      }

      const items = payload.items.map((item) => {
        const quantity = Number(item.quantity);

        if (!Number.isInteger(quantity) || quantity <= 0) {
          throw new CollectionError("Item quantity must be positive.");
        }

        return {
          sku: requireNonEmptyString(item.sku, "item.sku"),
          quantity,
        };
      });

      return {
        orderId: requireNonEmptyString(payload.orderId, "orderId"),
        customerId: requireNonEmptyString(payload.customerId, "customerId"),
        amount: formatMoney(parseMoney(payload.amount)),
        currency: requireNonEmptyString(payload.currency, "currency"),
        status,
        items,
      };
    }
  ),

  analytics: new SourceAdapter(
    "web_analytics",
    Categories.BEHAVIORAL,
    (payload) => {
      const allowedEvents = new Set([
        "page_view",
        "product_view",
        "add_to_cart",
        "search",
        "checkout_started",
      ]);

      if (!allowedEvents.has(payload.eventType)) {
        throw new CollectionError("Unsupported behavioral event.");
      }

      const pagePath = requireNonEmptyString(payload.pagePath, "pagePath");

      if (!pagePath.startsWith("/") || pagePath.startsWith("//")) {
        throw new CollectionError("Page path must be relative.");
      }

      return {
        visitorId: requireNonEmptyString(payload.visitorId, "visitorId"),
        eventType: payload.eventType,
        pagePath,
      };
    }
  ),
};

class DataCollectionService {
  #records = new Map();
  #deadLetterQueue = [];

  constructor(consentRegistry) {
    this.consentRegistry = consentRegistry;
  }

  async ingest({
    adapter,
    externalId,
    observedAt,
    payload,
    purpose,
    lawfulBasis,
    subjectId = null,
    requiresConsent = false,
    simulateTransientFailure = false,
  }) {
    const source = adapter.sourceName;
    const key = fingerprint(source, externalId);

    if (requiresConsent) {
      if (
        !subjectId ||
        !this.consentRegistry.allows(subjectId, purpose)
      ) {
        throw new CollectionError(
          "Behavioral collection is not authorized for this purpose.",
          "CONSENT_REQUIRED"
        );
      }
    }

    const normalizedPayload = adapter.normalize(payload);
    const observedTimestamp = parseTimestamp(observedAt);
    const collectedTimestamp = new Date().toISOString();

    if (Date.parse(observedTimestamp) > Date.parse(collectedTimestamp)) {
      throw new CollectionError("Observation cannot be in the future.");
    }

    if (!requireNonEmptyString(lawfulBasis, "lawfulBasis")) {
      throw new CollectionError("Collection basis is required.");
    }

    const candidate = {
      recordId: key,
      source,
      category: adapter.category,
      observedAt: observedTimestamp,
      collectedAt: collectedTimestamp,
      purpose: requireNonEmptyString(purpose, "purpose"),
      lawfulBasis,
      schemaVersion: "1.0",
      payload: normalizedPayload,
    };

    const previous = this.#records.get(key);

    if (previous) {
      const previousPayload = JSON.stringify(previous.payload);
      const nextPayload = JSON.stringify(candidate.payload);

      if (previousPayload !== nextPayload) {
        throw new CollectionError(
          "Conflicting duplicate requires reconciliation.",
          "DUPLICATE_CONFLICT"
        );
      }

      return { record: previous, duplicate: true };
    }

    if (simulateTransientFailure) {
      throw new CollectionError(
        "Temporary source transport failure.",
        "TRANSIENT_SOURCE_FAILURE"
      );
    }

    this.#records.set(key, candidate);
    return { record: candidate, duplicate: false };
  }

  async ingestWithRetry(request, maximumAttempts = 3) {
    if (!Number.isInteger(maximumAttempts) || maximumAttempts < 1) {
      throw new CollectionError("maximumAttempts must be positive.");
    }

    for (let attempt = 1; attempt <= maximumAttempts; attempt += 1) {
      try {
        // The simulation fails on the first attempt and succeeds on retry.
        const requestForAttempt = {
          ...request,
          simulateTransientFailure:
            request.simulateTransientFailure && attempt === 1,
        };

        return await this.ingest(requestForAttempt);
      } catch (error) {
        const retryable = error.code === "TRANSIENT_SOURCE_FAILURE";

        if (!retryable || attempt === maximumAttempts) {
          this.#deadLetterQueue.push({
            externalId: request.externalId,
            source: request.adapter.sourceName,
            error: error.message,
            attempts: attempt,
            failedAt: new Date().toISOString(),
          });
          throw error;
        }

        // Bounded exponential backoff prevents immediate repeated load.
        await delay(20 * 2 ** (attempt - 1));
      }
    }

    throw new Error("Unreachable retry state.");
  }

  get records() {
    return Array.from(this.#records.values(), (record) => ({
      ...record,
      payload: { ...record.payload },
    }));
  }

  get deadLetterQueue() {
    return this.#deadLetterQueue.map((entry) => ({ ...entry }));
  }
}

function analyzeCollection(records) {
  const categoryCounts = new Map();
  const sourceCounts = new Map();
  const behavioralEvents = new Map();
  let paidRevenueMinorUnits = 0n;
  let paidOrderCount = 0;

  for (const record of records) {
    categoryCounts.set(
      record.category,
      (categoryCounts.get(record.category) || 0) + 1
    );
    sourceCounts.set(
      record.source,
      (sourceCounts.get(record.source) || 0) + 1
    );

    if (record.category === Categories.TRANSACTIONAL) {
      if (
        record.payload.status === "paid" &&
        record.payload.currency === "INR"
      ) {
        paidRevenueMinorUnits += parseMoney(record.payload.amount);
        paidOrderCount += 1;
      }
    }

    if (record.category === Categories.BEHAVIORAL) {
      const eventType = record.payload.eventType;
      behavioralEvents.set(
        eventType,
        (behavioralEvents.get(eventType) || 0) + 1
      );
    }
  }

  return {
    totalRecords: records.length,
    categoryCounts: Object.fromEntries(categoryCounts),
    sourceCounts: Object.fromEntries(sourceCounts),
    paidOrderCount,
    paidRevenueINR: formatMoney(paidRevenueMinorUnits),
    behavioralEvents: Object.fromEntries(behavioralEvents),
  };
}

async function main() {
  const consent = new ConsentRegistry();
  consent.setPermission(
    "visitor-201",
    "product_experience_analytics",
    true
  );
  consent.setPermission(
    "visitor-202",
    "product_experience_analytics",
    false
  );

  const service = new DataCollectionService(consent);
  const now = new Date().toISOString();

  const requests = [
    {
      adapter: adapters.inventory,
      externalId: "stock-2026-10-13",
      observedAt: now,
      purpose: "inventory_reconciliation",
      lawfulBasis: "documented_business_purpose",
      payload: {
        warehouse: "DEL-01",
        sku: "LAPTOP-14",
        availableUnits: 184,
        reservedUnits: 16,
      },
    },
    {
      adapter: adapters.supplier,
      externalId: "supplier-feed-8842",
      observedAt: now,
      purpose: "supplier_price_comparison",
      lawfulBasis: "contract_and_documented_purpose",
      payload: {
        supplier: "Northstar Components",
        sku: "LAPTOP-14",
        unitPrice: "64500.00",
        currency: "INR",
        revision: "r18",
      },
      simulateTransientFailure: true,
    },
    {
      adapter: adapters.order,
      externalId: "ORD-2026-1001",
      observedAt: now,
      purpose: "order_fulfillment",
      lawfulBasis: "contract_performance",
      payload: {
        orderId: "ORD-2026-1001",
        customerId: "CUS-0081",
        amount: "72999.90",
        currency: "INR",
        status: "paid",
        items: [
          { sku: "LAPTOP-14", quantity: 1 },
          { sku: "USB-C-DOCK", quantity: 1 },
        ],
      },
    },
    {
      adapter: adapters.analytics,
      externalId: "evt-5001",
      observedAt: now,
      purpose: "product_experience_analytics",
      lawfulBasis: "consent",
      subjectId: "visitor-201",
      requiresConsent: true,
      payload: {
        visitorId: "visitor-201",
        eventType: "product_view",
        pagePath: "/products/laptop-14",
      },
    },
    {
      adapter: adapters.analytics,
      externalId: "evt-5002",
      observedAt: now,
      purpose: "product_experience_analytics",
      lawfulBasis: "consent",
      subjectId: "visitor-201",
      requiresConsent: true,
      payload: {
        visitorId: "visitor-201",
        eventType: "checkout_started",
        pagePath: "/checkout",
      },
    },
    {
      adapter: adapters.analytics,
      externalId: "evt-5003",
      observedAt: now,
      purpose: "product_experience_analytics",
      lawfulBasis: "consent",
      subjectId: "visitor-202",
      requiresConsent: true,
      payload: {
        visitorId: "visitor-202",
        eventType: "page_view",
        pagePath: "/home",
      },
    },
  ];

  for (const request of requests) {
    try {
      const result = await service.ingestWithRetry(request);
      console.log(
        `${result.duplicate ? "Duplicate" : "Collected"}: ` +
        `${result.record.category} from ${result.record.source}`
      );
    } catch (error) {
      console.warn(`Rejected ${request.externalId}: ${error.message}`);
    }
  }

  console.log("\nCollection analysis");
  console.log(JSON.stringify(analyzeCollection(service.records), null, 2));

  console.log("\nDead-letter records");
  console.log(JSON.stringify(service.deadLetterQueue, null, 2));

  // Do not log raw behavioral payloads or customer identifiers in production.
}

main().catch((error) => {
  console.error("Collection pipeline failed:", error.message);
  process.exitCode = 1;
});
