/*
 * CASE Statements: Creating Business Logic Using SQL
 *
 * This Node.js program complements the SQL implementation by modeling
 * conditional business rules as event-driven workflow decisions.
 *
 * It deliberately does not pretend JavaScript CASE syntax is equivalent to
 * SQL CASE. Instead, it shows how an application can evaluate the same
 * business policy, generate SQL CASE expressions, and consume the resulting
 * classification as part of an order-processing workflow.
 */

"use strict";

class BusinessRuleError extends Error {
    constructor(message) {
        super(message);
        this.name = "BusinessRuleError";
    }
}

const customers = [
    {
        id: 1,
        name: "Aarav Labs",
        country: "IN",
        lifetimeValue: 125000,
        status: "active"
    },
    {
        id: 2,
        name: "Northwind",
        country: "US",
        lifetimeValue: 62000,
        status: "active"
    },
    {
        id: 3,
        name: "BerlinWorks",
        country: "DE",
        lifetimeValue: 18000,
        status: "active"
    },
    {
        id: 4,
        name: "RiskAccount",
        country: "US",
        lifetimeValue: 200000,
        status: "suspended"
    }
];

const orders = [
    {
        id: 501,
        customerId: 1,
        subtotal: 12000,
        shipping: 250,
        paymentStatus: "paid",
        orderStatus: "confirmed"
    },
    {
        id: 502,
        customerId: 2,
        subtotal: 7000,
        shipping: 200,
        paymentStatus: "pending",
        orderStatus: "confirmed"
    },
    {
        id: 503,
        customerId: 4,
        subtotal: 15000,
        shipping: 250,
        paymentStatus: "paid",
        orderStatus: "confirmed"
    }
];

function classifyCustomer(customer) {
    if (customer.status === "suspended") {
        return "RESTRICTED";
    }

    if (customer.lifetimeValue >= 100000) {
        return "PLATINUM";
    }

    if (customer.lifetimeValue >= 50000) {
        return "GOLD";
    }

    if (customer.lifetimeValue >= 10000) {
        return "SILVER";
    }

    return "STANDARD";
}

function paymentLabel(paymentStatus) {
    switch (paymentStatus) {
        case "paid":
            return "SETTLED";
        case "pending":
            return "AWAITING PAYMENT";
        case "failed":
            return "PAYMENT FAILED";
        case "refunded":
            return "REFUNDED";
        default:
            return "UNKNOWN PAYMENT STATE";
    }
}

function calculateDiscount(customer, order) {
    if (order.paymentStatus !== "paid" || customer.status === "suspended") {
        return 0;
    }

    const gross = order.subtotal + order.shipping;

    if (customer.lifetimeValue >= 100000 && gross >= 5000) {
        return 0.15;
    }

    if (customer.lifetimeValue >= 50000) {
        return 0.10;
    }

    if (gross >= 10000) {
        return 0.08;
    }

    if (gross >= 5000) {
        return 0.05;
    }

    return 0;
}

function shippingDecision(order) {
    if (order.orderStatus === "cancelled") {
        return "DO NOT SHIP";
    }

    if (order.paymentStatus !== "paid") {
        return "HOLD";
    }

    const gross = order.subtotal + order.shipping;

    if (gross >= 10000) {
        return "URGENT";
    }

    if (gross >= 5000) {
        return "HIGH";
    }

    return "NORMAL";
}

function regionFor(country) {
    const regions = new Map([
        ["IN", "APAC"],
        ["JP", "APAC"],
        ["SG", "APAC"],
        ["DE", "EUROPE"],
        ["FR", "EUROPE"],
        ["GB", "EUROPE"],
        ["US", "NORTH_AMERICA"],
        ["CA", "NORTH_AMERICA"]
    ]);

    return regions.get(country) ?? "OTHER";
}

function buildOrderDecision(customer, order) {
    if (!customer) {
        throw new BusinessRuleError(
            `Order ${order.id} references unknown customer ${order.customerId}`
        );
    }

    if (order.subtotal < 0 || order.shipping < 0) {
        throw new BusinessRuleError(
            `Order ${order.id} contains a negative monetary amount`
        );
    }

    const gross = order.subtotal + order.shipping;
    const discountRate = calculateDiscount(customer, order);
    const discount = Number((gross * discountRate).toFixed(2));

    return {
        orderId: order.id,
        customer: customer.name,
        segment: classifyCustomer(customer),
        region: regionFor(customer.country),
        payment: paymentLabel(order.paymentStatus),
        shipping: shippingDecision(order),
        gross,
        discountRate,
        discount,
        net: Number((gross - discount).toFixed(2))
    };
}

function generatePostgreSQLCase() {
    return `
CASE
    WHEN status = 'suspended' THEN 'RESTRICTED'
    WHEN lifetime_value >= 100000 THEN 'PLATINUM'
    WHEN lifetime_value >= 50000 THEN 'GOLD'
    WHEN lifetime_value >= 10000 THEN 'SILVER'
    ELSE 'STANDARD'
END AS customer_segment
`.trim();
}

class OrderProcessor {
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

    process(customer, order) {
        const decision = buildOrderDecision(customer, order);

        this.emit("classified", decision);

        if (decision.shipping === "HOLD") {
            this.emit("paymentRequired", decision);
        }

        if (decision.shipping === "URGENT") {
            this.emit("priorityShipment", decision);
        }

        return decision;
    }
}

async function runWorkflow() {
    const customerMap = new Map(customers.map(customer => [customer.id, customer]));
    const processor = new OrderProcessor();

    processor.on("classified", decision => {
        console.log(
            `Order ${decision.orderId}: ${decision.segment}, ` +
            `${decision.payment}, ${decision.shipping}, net=${decision.net}`
        );
    });

    processor.on("paymentRequired", decision => {
        console.log(
            `  Payment workflow: order ${decision.orderId} remains on hold.`
        );
    });

    processor.on("priorityShipment", decision => {
        console.log(
            `  Logistics workflow: order ${decision.orderId} receives priority handling.`
        );
    });

    console.log("SQL CASE business-rule workflow\n");

    for (const order of orders) {
        const customer = customerMap.get(order.customerId);
        processor.process(customer, order);
    }

    console.log("\nGenerated PostgreSQL CASE expression:");
    console.log(generatePostgreSQLCase());

    console.log("\nCASE-specific design notes:");
    console.log(
        "The first matching SQL WHEN branch wins, so condition ordering " +
        "must place restrictive exceptions before broad thresholds."
    );
    console.log(
        "ELSE is important when the business domain contains values that " +
        "were not anticipated by the current rule set."
    );
    console.log(
        "CASE can classify rows, calculate derived values, map statuses, " +
        "and participate in aggregates such as SUM(CASE WHEN ... END)."
    );
}

runWorkflow().catch(error => {
    console.error(`${error.name}: ${error.message}`);
    process.exitCode = 1;
});
