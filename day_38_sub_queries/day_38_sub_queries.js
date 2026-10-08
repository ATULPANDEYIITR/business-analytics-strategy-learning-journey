"use strict";

/*
 * Subqueries and Nested Queries: analytical logic in JavaScript.
 *
 * This file models a small analytical query engine in memory rather than
 * depending on an external database package. The implementation focuses on
 * the same reasoning that SQL subqueries provide: scalar comparisons,
 * membership, correlated evaluation, existence tests, derived datasets,
 * nested aggregation, and multi-stage analysis.
 *
 * Run with:
 *   node subqueries.js
 */

const customers = [
  { id: 1, name: "Aarav Mehta", region: "North", tier: "Gold" },
  { id: 2, name: "Diya Sharma", region: "North", tier: "Silver" },
  { id: 3, name: "Kabir Singh", region: "West", tier: "Gold" },
  { id: 4, name: "Meera Iyer", region: "South", tier: "Standard" },
  { id: 5, name: "Rohan Gupta", region: "West", tier: "Silver" },
  { id: 6, name: "Ananya Rao", region: "South", tier: "Gold" },
  { id: 7, name: "Vikram Joshi", region: "East", tier: "Standard" },
  { id: 8, name: "Sara Khan", region: "East", tier: "Silver" }
];

const products = [
  { id: 1, name: "Laptop Pro", category: "Electronics", price: 1200 },
  { id: 2, name: "Mechanical Keyboard", category: "Electronics", price: 140 },
  { id: 3, name: "Office Chair", category: "Furniture", price: 350 },
  { id: 4, name: "Monitor 27", category: "Electronics", price: 420 },
  { id: 5, name: "Standing Desk", category: "Furniture", price: 650 },
  { id: 6, name: "USB-C Hub", category: "Accessories", price: 80 },
  { id: 7, name: "Webcam", category: "Accessories", price: 110 }
];

const orders = [
  { id: 101, customerId: 1, status: "Completed" },
  { id: 102, customerId: 1, status: "Completed" },
  { id: 103, customerId: 2, status: "Completed" },
  { id: 104, customerId: 2, status: "Completed" },
  { id: 105, customerId: 3, status: "Completed" },
  { id: 106, customerId: 3, status: "Completed" },
  { id: 107, customerId: 3, status: "Completed" },
  { id: 108, customerId: 4, status: "Completed" },
  { id: 109, customerId: 4, status: "Cancelled" },
  { id: 110, customerId: 5, status: "Completed" },
  { id: 111, customerId: 5, status: "Completed" },
  { id: 112, customerId: 6, status: "Completed" },
  { id: 113, customerId: 6, status: "Completed" },
  { id: 114, customerId: 7, status: "Completed" },
  { id: 115, customerId: 8, status: "Pending" }
];

const orderItems = [
  { orderId: 101, productId: 1, quantity: 1 },
  { orderId: 101, productId: 2, quantity: 1 },
  { orderId: 102, productId: 4, quantity: 1 },
  { orderId: 102, productId: 6, quantity: 2 },
  { orderId: 103, productId: 3, quantity: 1 },
  { orderId: 103, productId: 7, quantity: 1 },
  { orderId: 104, productId: 2, quantity: 2 },
  { orderId: 104, productId: 6, quantity: 1 },
  { orderId: 105, productId: 1, quantity: 1 },
  { orderId: 105, productId: 6, quantity: 1 },
  { orderId: 106, productId: 5, quantity: 1 },
  { orderId: 106, productId: 4, quantity: 1 },
  { orderId: 107, productId: 1, quantity: 1 },
  { orderId: 107, productId: 7, quantity: 2 },
  { orderId: 108, productId: 3, quantity: 1 },
  { orderId: 108, productId: 6, quantity: 2 },
  { orderId: 109, productId: 4, quantity: 1 },
  { orderId: 110, productId: 5, quantity: 1 },
  { orderId: 110, productId: 2, quantity: 1 },
  { orderId: 111, productId: 3, quantity: 2 },
  { orderId: 111, productId: 7, quantity: 1 },
  { orderId: 112, productId: 1, quantity: 1 },
  { orderId: 112, productId: 4, quantity: 1 },
  { orderId: 113, productId: 5, quantity: 1 },
  { orderId: 113, productId: 6, quantity: 2 },
  { orderId: 114, productId: 2, quantity: 1 },
  { orderId: 114, productId: 7, quantity: 1 },
  { orderId: 115, productId: 4, quantity: 1 }
];

function average(values) {
  if (values.length === 0) {
    return null;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function money(value) {
  return value === null ? "NULL" : `$${value.toFixed(2)}`;
}

function print(title, rows) {
  console.log(`\n--- ${title} ---`);

  if (rows.length === 0) {
    console.log("(no rows)");
    return;
  }

  console.table(rows);
}

function getProduct(productId) {
  return products.find((product) => product.id === productId);
}

function getCustomer(customerId) {
  return customers.find((customer) => customer.id === customerId);
}

function getOrderTotal(orderId) {
  return orderItems
    .filter((item) => item.orderId === orderId)
    .reduce((total, item) => {
      const product = getProduct(item.productId);

      if (!product) {
        throw new Error(`Unknown product ${item.productId}`);
      }

      return total + product.price * item.quantity;
    }, 0);
}

/*
 * Scalar-subquery equivalent:
 * calculate one global benchmark first, then compare every product against it.
 */
function productsAboveAveragePrice() {
  const averagePrice = average(products.map((product) => product.price));

  return products
    .filter((product) => product.price > averagePrice)
    .map((product) => ({
      product: product.name,
      category: product.category,
      price: money(product.price),
      averagePrice: money(averagePrice)
    }))
    .sort((a, b) => parseFloat(b.price.slice(1)) - parseFloat(a.price.slice(1)));
}

/*
 * IN-subquery equivalent:
 * the inner operation creates the set of customer IDs that have completed
 * orders, and the outer operation uses that set as a membership predicate.
 */
function customersWithCompletedOrders() {
  const completedCustomerIds = new Set(
    orders
      .filter((order) => order.status === "Completed")
      .map((order) => order.customerId)
  );

  return customers
    .filter((customer) => completedCustomerIds.has(customer.id))
    .map(({ id, name, region }) => ({ id, name, region }));
}

/*
 * EXISTS-subquery equivalent:
 * membership is tested without needing to return matching child records.
 * Some customers have multiple matching orders, but each customer appears once.
 */
function customersWhoBoughtFurniture() {
  return customers
    .filter((customer) =>
      orders.some(
        (order) =>
          order.customerId === customer.id &&
          order.status === "Completed" &&
          orderItems.some((item) => {
            if (item.orderId !== order.id) {
              return false;
            }

            const product = getProduct(item.productId);
            return product?.category === "Furniture";
          })
      )
    )
    .map(({ name, tier }) => ({ name, tier }));
}

/*
 * Correlated-subquery equivalent:
 * for each customer, independently calculate the customer's completed
 * order average. The inner computation depends on the current customer.
 */
function averageOrderValuePerCustomer() {
  return customers
    .map((customer) => {
      const customerOrders = orders.filter(
        (order) =>
          order.customerId === customer.id &&
          order.status === "Completed"
      );

      const totals = customerOrders.map((order) => getOrderTotal(order.id));

      return {
        customer: customer.name,
        averageOrderValue: average(totals)
      };
    })
    .filter((row) => row.averageOrderValue !== null)
    .sort((a, b) => b.averageOrderValue - a.averageOrderValue)
    .map((row) => ({
      customer: row.customer,
      averageOrderValue: money(row.averageOrderValue)
    }));
}

/*
 * Derived-table equivalent:
 * orderTotals is an intermediate relation. A second aggregation operates on
 * those already-computed rows instead of recomputing item-level revenue.
 */
function regionalOrderAnalysis() {
  const orderTotals = orders
    .filter((order) => order.status === "Completed")
    .map((order) => {
      const customer = getCustomer(order.customerId);

      return {
        orderId: order.id,
        region: customer.region,
        total: getOrderTotal(order.id)
      };
    });

  const byRegion = new Map();

  for (const row of orderTotals) {
    if (!byRegion.has(row.region)) {
      byRegion.set(row.region, []);
    }

    byRegion.get(row.region).push(row.total);
  }

  return [...byRegion.entries()]
    .map(([region, totals]) => ({
      region,
      averageOrderValue: money(average(totals)),
      largestOrder: money(Math.max(...totals)),
      orderCount: totals.length
    }))
    .sort(
      (a, b) =>
        parseFloat(b.averageOrderValue.slice(1)) -
        parseFloat(a.averageOrderValue.slice(1))
    );
}

/*
 * Multi-level nesting:
 * order rows -> customer revenue -> overall average customer revenue ->
 * customers whose revenue exceeds that benchmark.
 */
function highValueCustomers() {
  const customerRevenue = customers
    .map((customer) => {
      const revenue = orders
        .filter(
          (order) =>
            order.customerId === customer.id &&
            order.status === "Completed"
        )
        .reduce((sum, order) => sum + getOrderTotal(order.id), 0);

      return {
        customerId: customer.id,
        customer: customer.name,
        revenue
      };
    })
    .filter((row) => row.revenue > 0);

  const overallAverageRevenue = average(
    customerRevenue.map((row) => row.revenue)
  );

  return customerRevenue
    .filter((row) => row.revenue > overallAverageRevenue)
    .sort((a, b) => b.revenue - a.revenue)
    .map((row) => ({
      customer: row.customer,
      revenue: money(row.revenue),
      benchmark: money(overallAverageRevenue)
    }));
}

/*
 * Correlated ranking:
 * count how many products in the same category are more expensive. A count
 * of zero identifies the category leader without sorting every category.
 */
function mostExpensiveProductsByCategory() {
  return products
    .filter((product) => {
      const moreExpensiveProducts = products.filter(
        (candidate) =>
          candidate.category === product.category &&
          candidate.price > product.price
      );

      return moreExpensiveProducts.length === 0;
    })
    .map((product) => ({
      product: product.name,
      category: product.category,
      price: money(product.price)
    }));
}

/*
 * Nested analytical filter:
 * category revenue is calculated first. The outer operation then compares
 * each category with the average category revenue.
 */
function categoriesAboveAverageRevenue() {
  const categoryRevenue = new Map();

  for (const order of orders.filter(
    (candidate) => candidate.status === "Completed"
  )) {
    for (const item of orderItems.filter(
      (candidate) => candidate.orderId === order.id
    )) {
      const product = getProduct(item.productId);
      const revenue = product.price * item.quantity;

      categoryRevenue.set(
        product.category,
        (categoryRevenue.get(product.category) || 0) + revenue
      );
    }
  }

  const rows = [...categoryRevenue.entries()].map(([category, revenue]) => ({
    category,
    revenue
  }));

  const benchmark = average(rows.map((row) => row.revenue));

  return rows
    .filter((row) => row.revenue > benchmark)
    .sort((a, b) => b.revenue - a.revenue)
    .map((row) => ({
      category: row.category,
      revenue: money(row.revenue),
      averageCategoryRevenue: money(benchmark)
    }));
}

/*
 * NOT EXISTS equivalent:
 * require at least one completed order while excluding customers with any
 * cancellation. This demonstrates that existence and non-existence can be
 * combined to express business predicates.
 */
function completedWithoutCancellation() {
  return customers
    .filter((customer) => {
      const completed = orders.some(
        (order) =>
          order.customerId === customer.id &&
          order.status === "Completed"
      );

      const cancelled = orders.some(
        (order) =>
          order.customerId === customer.id &&
          order.status === "Cancelled"
      );

      return completed && !cancelled;
    })
    .map(({ name, region }) => ({ name, region }));
}

/*
 * Parameterized analytical function:
 * category is validated before being used. In a database-backed application,
 * the corresponding SQL should use bound parameters rather than string
 * concatenation.
 */
function productsAboveCategoryAverage(category) {
  if (typeof category !== "string" || category.trim() === "") {
    throw new TypeError("Category must be a non-empty string.");
  }

  const scopedProducts = products.filter(
    (product) => product.category === category
  );

  if (scopedProducts.length === 0) {
    return [];
  }

  const categoryAverage = average(
    scopedProducts.map((product) => product.price)
  );

  return scopedProducts
    .filter((product) => product.price > categoryAverage)
    .map((product) => ({
      product: product.name,
      price: money(product.price),
      categoryAverage: money(categoryAverage)
    }));
}

/*
 * NULL-like edge case:
 * JavaScript uses null explicitly here to model the fact that SQL AVG over an
 * empty input does not produce a numeric zero. A caller must decide whether a
 * missing benchmark should remain null or receive a business-defined default.
 */
function emptySubqueryBenchmark(category) {
  const matchingPrices = products
    .filter((product) => product.category === category)
    .map((product) => product.price);

  const benchmark = average(matchingPrices);

  return {
    category,
    benchmark,
    safeBenchmark: benchmark ?? 0
  };
}

function main() {
  print("Products above overall average price", productsAboveAveragePrice());
  print(
    "Customers with completed orders",
    customersWithCompletedOrders()
  );
  print(
    "Customers who bought furniture",
    customersWhoBoughtFurniture()
  );
  print(
    "Correlated average order value per customer",
    averageOrderValuePerCustomer()
  );
  print(
    "Regional analysis from a derived dataset",
    regionalOrderAnalysis()
  );
  print(
    "Customers above average customer revenue",
    highValueCustomers()
  );
  print(
    "Most expensive product in each category",
    mostExpensiveProductsByCategory()
  );
  print(
    "Categories above average category revenue",
    categoriesAboveAverageRevenue()
  );
  print(
    "Customers with completed orders and no cancellation",
    completedWithoutCancellation()
  );
  print(
    "Electronics above category average",
    productsAboveCategoryAverage("Electronics")
  );
  print(
    "Empty-subquery benchmark",
    [emptySubqueryBenchmark("Nonexistent")]
  );

  console.log("\nValidation and failure handling:");

  try {
    productsAboveCategoryAverage("");
  } catch (error) {
    console.log(`Validation rejected invalid category: ${error.message}`);
  }

  try {
    getOrderTotal(999999);
  } catch (error) {
    console.log(`Unknown order produced: ${error.message}`);
  }
}

main();
