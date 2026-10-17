"use strict";

/*
 * Segmentation model with four distinct dimensions:
 * customer, product, geographic, and behavioral.
 *
 * This implementation uses event-driven JavaScript to model changes to
 * customer behavior and recalculates behavioral segment membership when
 * purchase events arrive.
 */

const customers = [
  {
    id: "C001",
    age: 27,
    income: 90000,
    region: "North",
    city: "Delhi",
    preferredCategory: "Electronics"
  },
  {
    id: "C002",
    age: 42,
    income: 145000,
    region: "West",
    city: "Mumbai",
    preferredCategory: "Home"
  },
  {
    id: "C003",
    age: 31,
    income: 42000,
    region: "East",
    city: "Kolkata",
    preferredCategory: "Household"
  },
  {
    id: "C004",
    age: 55,
    income: 70000,
    region: "South",
    city: "Bengaluru",
    preferredCategory: "Electronics"
  },
  {
    id: "C005",
    age: 23,
    income: 52000,
    region: "North",
    city: "Lucknow",
    preferredCategory: "Fashion"
  },
  {
    id: "C006",
    age: 38,
    income: 160000,
    region: "West",
    city: "Pune",
    preferredCategory: "Electronics"
  }
];

const products = [
  {
    id: "P001",
    category: "Electronics",
    family: "Premium",
    price: 120000,
    margin: 0.22
  },
  {
    id: "P002",
    category: "Home",
    family: "Household",
    price: 18000,
    margin: 0.35
  },
  {
    id: "P003",
    category: "Household",
    family: "Essential",
    price: 3500,
    margin: 0.42
  },
  {
    id: "P004",
    category: "Fashion",
    family: "Lifestyle",
    price: 6500,
    margin: 0.48
  },
  {
    id: "P005",
    category: "Electronics",
    family: "Premium",
    price: 42000,
    margin: 0.31
  }
];

const purchases = [
  { customerId: "C001", productId: "P005", quantity: 1, value: 42000, date: "2026-10-05" },
  { customerId: "C001", productId: "P003", quantity: 3, value: 10500, date: "2026-09-20" },
  { customerId: "C002", productId: "P001", quantity: 1, value: 120000, date: "2026-10-10" },
  { customerId: "C002", productId: "P002", quantity: 3, value: 54000, date: "2026-09-11" },
  { customerId: "C003", productId: "P003", quantity: 4, value: 14000, date: "2026-10-01" },
  { customerId: "C004", productId: "P002", quantity: 2, value: 36000, date: "2026-07-05" },
  { customerId: "C005", productId: "P004", quantity: 1, value: 6500, date: "2026-10-03" },
  { customerId: "C006", productId: "P001", quantity: 1, value: 120000, date: "2026-09-30" },
  { customerId: "C006", productId: "P005", quantity: 2, value: 84000, date: "2026-08-29" }
];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function median(values) {
  assert(values.length > 0, "Median requires at least one value.");

  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);

  return sorted.length % 2 === 0
    ? (sorted[middle - 1] + sorted[middle]) / 2
    : sorted[middle];
}

function daysBetween(start, end) {
  const startDate = new Date(`${start}T00:00:00Z`);
  const endDate = new Date(`${end}T00:00:00Z`);

  return Math.floor((endDate - startDate) / 86400000);
}

class SegmentationService {
  constructor(customers, products, purchases) {
    this.customers = new Map(customers.map(customer => [customer.id, customer]));
    this.products = new Map(products.map(product => [product.id, product]));
    this.purchases = [...purchases];

    this.validate();
  }

  validate() {
    for (const customer of this.customers.values()) {
      assert(customer.age >= 18, `Invalid age for ${customer.id}`);
      assert(customer.income >= 0, `Invalid income for ${customer.id}`);
    }

    for (const product of this.products.values()) {
      assert(product.price >= 0, `Invalid price for ${product.id}`);
      assert(product.margin >= 0 && product.margin <= 1,
        `Invalid margin for ${product.id}`);
    }

    for (const purchase of this.purchases) {
      assert(this.customers.has(purchase.customerId),
        `Unknown customer ${purchase.customerId}`);
      assert(this.products.has(purchase.productId),
        `Unknown product ${purchase.productId}`);
      assert(purchase.quantity > 0, "Purchase quantity must be positive");
    }
  }

  customerSegments() {
    const incomeMedian = median(
      [...this.customers.values()].map(customer => customer.income)
    );

    const result = {
      youngProfessionals: [],
      highIncomeEstablished: [],
      valueConscious: []
    };

    for (const customer of this.customers.values()) {
      if (customer.age <= 34 && customer.income >= incomeMedian) {
        result.youngProfessionals.push(customer.id);
      }

      if (customer.age >= 35 && customer.income > incomeMedian) {
        result.highIncomeEstablished.push(customer.id);
      }

      if (customer.income < incomeMedian) {
        result.valueConscious.push(customer.id);
      }
    }

    return result;
  }

  productSegments() {
    const priceMedian = median(
      [...this.products.values()].map(product => product.price)
    );

    const result = {
      premium: [],
      highMargin: [],
      essential: []
    };

    for (const product of this.products.values()) {
      if (product.price > priceMedian) {
        result.premium.push(product.id);
      }

      if (product.margin >= 0.30) {
        result.highMargin.push(product.id);
      }

      if (product.family === "Essential" || product.family === "Household") {
        result.essential.push(product.id);
      }
    }

    return result;
  }

  geographicSegments() {
    const groups = new Map();

    for (const customer of this.customers.values()) {
      if (!groups.has(customer.region)) {
        groups.set(customer.region, []);
      }

      groups.get(customer.region).push(customer.id);
    }

    return Object.fromEntries(groups);
  }

  behavioralMetrics(referenceDate) {
    const metrics = new Map();

    for (const customer of this.customers.values()) {
      const customerPurchases = this.purchases.filter(
        purchase => purchase.customerId === customer.id
      );

      const dates = customerPurchases.map(purchase => purchase.date);

      const latestDate = dates.length > 0
        ? dates.reduce((latest, current) => current > latest ? current : latest)
        : null;

      metrics.set(customer.id, {
        frequency: customerPurchases.length,
        monetary: customerPurchases.reduce(
          (total, purchase) => total + purchase.value,
          0
        ),
        recency: latestDate === null
          ? Infinity
          : daysBetween(latestDate, referenceDate)
      });
    }

    return metrics;
  }

  behavioralSegments(referenceDate) {
    const metrics = this.behavioralMetrics(referenceDate);

    const frequencies = [...metrics.values()].map(value => value.frequency);
    const monetaryValues = [...metrics.values()].map(value => value.monetary);

    const frequencyMedian = median(frequencies);
    const monetaryMedian = median(monetaryValues);

    const result = {
      loyalHighValue: [],
      recentLowFrequency: [],
      atRisk: []
    };

    for (const [customerId, metric] of metrics) {
      if (
        metric.frequency >= frequencyMedian &&
        metric.monetary >= monetaryMedian
      ) {
        result.loyalHighValue.push(customerId);
      }

      if (
        metric.recency <= 30 &&
        metric.frequency < frequencyMedian
      ) {
        result.recentLowFrequency.push(customerId);
      }

      if (metric.recency > 60) {
        result.atRisk.push(customerId);
      }
    }

    return result;
  }

  addPurchase(purchase) {
    assert(this.customers.has(purchase.customerId), "Unknown customer.");
    assert(this.products.has(purchase.productId), "Unknown product.");
    assert(purchase.quantity > 0, "Quantity must be positive.");
    assert(purchase.value >= 0, "Value cannot be negative.");

    this.purchases.push(purchase);
  }

  customerProfile(customerId, referenceDate) {
    assert(this.customers.has(customerId), "Unknown customer.");

    const customerSegments = this.customerSegments();
    const geographicSegments = this.geographicSegments();
    const behavioralSegments = this.behavioralSegments(referenceDate);

    const findMembership = segments =>
      Object.entries(segments)
        .filter(([, members]) => members.includes(customerId))
        .map(([name]) => name);

    return {
      customerId,
      customerSegments: findMembership(customerSegments),
      geographicSegments: findMembership(geographicSegments),
      behavioralSegments: findMembership(behavioralSegments)
    };
  }
}

/*
 * The event bus is useful for behavioral segmentation because behavior
 * changes over time. A purchase event can trigger a new segmentation
 * evaluation without changing the definition of customer or product
 * segments.
 */
class PurchaseEventBus {
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

function cosineSimilarity(left, right) {
  assert(left.length === right.length, "Vectors must have equal dimensions.");

  const dot = left.reduce((sum, value, index) => sum + value * right[index], 0);
  const leftNorm = Math.sqrt(left.reduce((sum, value) => sum + value ** 2, 0));
  const rightNorm = Math.sqrt(right.reduce((sum, value) => sum + value ** 2, 0));

  if (leftNorm === 0 || rightNorm === 0) {
    return 0;
  }

  return dot / (leftNorm * rightNorm);
}

const service = new SegmentationService(customers, products, purchases);

console.log("Customer segments:");
console.table(service.customerSegments());

console.log("Product segments:");
console.table(service.productSegments());

console.log("Geographic segments:");
console.table(service.geographicSegments());

console.log("Behavioral segments:");
console.table(service.behavioralSegments("2026-10-17"));

console.log("Customer C006 profile:");
console.log(service.customerProfile("C006", "2026-10-17"));

const eventBus = new PurchaseEventBus();

eventBus.on("purchase.completed", purchase => {
  service.addPurchase(purchase);

  const refreshed = service.behavioralSegments("2026-10-17");

  console.log("Behavioral segments refreshed after purchase:");
  console.table(refreshed);
});

eventBus.emit("purchase.completed", {
  customerId: "C005",
  productId: "P003",
  quantity: 2,
  value: 7000,
  date: "2026-10-16"
});

console.log(
  "Behavior similarity:",
  cosineSimilarity([0.8, 0.7, 0.6], [0.9, 0.8, 0.7]).toFixed(3)
);

try {
  service.addPurchase({
    customerId: "C999",
    productId: "P001",
    quantity: 1,
    value: 120000,
    date: "2026-10-17"
  });
} catch (error) {
  console.error("Rejected invalid purchase:", error.message);
}
