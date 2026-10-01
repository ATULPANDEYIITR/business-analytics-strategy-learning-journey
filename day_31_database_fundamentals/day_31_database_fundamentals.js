/**
 * Database Fundamentals
 *
 * This Node.js program models relational database concepts without requiring
 * an external database server. It focuses on the structure and behavior of
 * databases, tables, rows, columns, primary keys, foreign keys, relationships,
 * joins, transactions, validation, and query-oriented data processing.
 *
 * The in-memory repository intentionally mirrors relational behavior so that
 * the file remains executable with a stock Node.js runtime.
 */

"use strict";

class DatabaseConstraintError extends Error {
    constructor(message) {
        super(message);
        this.name = "DatabaseConstraintError";
    }
}

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class Table {
    constructor(name, columns, primaryKey) {
        this.name = name;
        this.columns = columns;
        this.primaryKey = primaryKey;
        this.rows = new Map();
        this.foreignKeys = [];
        this.uniqueIndexes = new Map();
    }

    addForeignKey(column, referencedTable, referencedColumn, options = {}) {
        this.foreignKeys.push({
            column,
            referencedTable,
            referencedColumn,
            onDelete: options.onDelete ?? "RESTRICT"
        });
    }

    addUniqueIndex(name, column) {
        this.uniqueIndexes.set(name, column);
    }

    insert(row, database) {
        const unknownColumns = Object.keys(row).filter(
            (column) => !this.columns.includes(column)
        );

        if (unknownColumns.length > 0) {
            throw new DatabaseConstraintError(
                `Unknown columns in ${this.name}: ${unknownColumns.join(", ")}`
            );
        }

        const primaryKey = row[this.primaryKey];

        if (primaryKey === undefined || primaryKey === null) {
            throw new DatabaseConstraintError(
                `${this.name}.${this.primaryKey} is required`
            );
        }

        if (this.rows.has(primaryKey)) {
            throw new DatabaseConstraintError(
                `Duplicate primary key ${primaryKey} in ${this.name}`
            );
        }

        for (const [indexName, column] of this.uniqueIndexes) {
            const value = row[column];

            if (value === undefined || value === null) {
                continue;
            }

            for (const existing of this.rows.values()) {
                if (existing[column] === value) {
                    throw new DatabaseConstraintError(
                        `Unique constraint ${indexName} rejected value ${value}`
                    );
                }
            }
        }

        for (const foreignKey of this.foreignKeys) {
            const value = row[foreignKey.column];
            const referenced = database.table(foreignKey.referencedTable);

            if (!referenced.rows.has(value)) {
                throw new DatabaseConstraintError(
                    `${this.name}.${foreignKey.column} references missing ` +
                    `${foreignKey.referencedTable}.${foreignKey.referencedColumn}`
                );
            }
        }

        this.rows.set(primaryKey, structuredClone(row));
    }

    get(primaryKey) {
        const row = this.rows.get(primaryKey);
        return row ? structuredClone(row) : null;
    }

    all() {
        return [...this.rows.values()].map((row) => structuredClone(row));
    }
}

class RelationalDatabase {
    constructor() {
        this.tables = new Map();
    }

    createTable(name, columns, primaryKey) {
        if (this.tables.has(name)) {
            throw new DatabaseConstraintError(`Table ${name} already exists`);
        }

        const table = new Table(name, columns, primaryKey);
        this.tables.set(name, table);
        return table;
    }

    table(name) {
        const table = this.tables.get(name);

        if (!table) {
            throw new DatabaseConstraintError(`Unknown table: ${name}`);
        }

        return table;
    }

    insert(tableName, row) {
        this.table(tableName).insert(row, this);
    }

    snapshot() {
        const snapshot = new Map();

        for (const [name, table] of this.tables) {
            snapshot.set(name, new Map(
                [...table.rows.entries()].map(
                    ([key, row]) => [key, structuredClone(row)]
                )
            ));
        }

        return snapshot;
    }

    restore(snapshot) {
        for (const [name, rows] of snapshot) {
            this.tables.get(name).rows = rows;
        }
    }

    transaction(work) {
        const snapshot = this.snapshot();

        try {
            return work();
        } catch (error) {
            this.restore(snapshot);
            throw error;
        }
    }
}

function createDatabase() {
    const db = new RelationalDatabase();

    const customers = db.createTable(
        "customers",
        ["customerId", "name", "email"],
        "customerId"
    );
    customers.addUniqueIndex("customers_email_unique", "email");

    const categories = db.createTable(
        "categories",
        ["categoryId", "name"],
        "categoryId"
    );
    categories.addUniqueIndex("categories_name_unique", "name");

    const products = db.createTable(
        "products",
        ["productId", "name", "categoryId", "price", "stock"],
        "productId"
    );
    products.addForeignKey("categoryId", "categories", "categoryId");

    const orders = db.createTable(
        "orders",
        ["orderId", "customerId", "status"],
        "orderId"
    );
    orders.addForeignKey("customerId", "customers", "customerId");

    const orderItems = db.createTable(
        "orderItems",
        ["orderId", "productId", "quantity", "unitPrice"],
        "key"
    );

    // orderItems uses a composite logical key. The key is derived from both
    // foreign keys because one order should contain a product at most once.
    orderItems.addForeignKey("orderId", "orders", "orderId", {
        onDelete: "CASCADE"
    });
    orderItems.addForeignKey("productId", "products", "productId");

    return db;
}

function seedDatabase(db) {
    for (const category of [
        { categoryId: 1, name: "Laptops" },
        { categoryId: 2, name: "Monitors" },
        { categoryId: 3, name: "Accessories" }
    ]) {
        db.insert("categories", category);
    }

    for (const product of [
        {
            productId: 101,
            name: "ThinkPad E16",
            categoryId: 1,
            price: 89999,
            stock: 12
        },
        {
            productId: 102,
            name: "Framework Laptop",
            categoryId: 1,
            price: 104999,
            stock: 8
        },
        {
            productId: 201,
            name: "27-inch 4K Monitor",
            categoryId: 2,
            price: 32999,
            stock: 15
        },
        {
            productId: 301,
            name: "Mechanical Keyboard",
            categoryId: 3,
            price: 6999,
            stock: 30
        }
    ]) {
        db.insert("products", product);
    }

    for (const customer of [
        { customerId: 1, name: "Atul Pandey", email: "atul@example.com" },
        { customerId: 2, name: "Priya Sharma", email: "priya@example.com" },
        { customerId: 3, name: "Rahul Verma", email: "rahul@example.com" }
    ]) {
        db.insert("customers", customer);
    }
}

function makeOrderItemKey(orderId, productId) {
    return `${orderId}:${productId}`;
}

function createOrder(db, customerId, requestedItems) {
    if (!Number.isInteger(customerId) || customerId <= 0) {
        throw new ValidationError("customerId must be a positive integer");
    }

    if (!Array.isArray(requestedItems) || requestedItems.length === 0) {
        throw new ValidationError("An order requires at least one item");
    }

    return db.transaction(() => {
        const customer = db.table("customers").get(customerId);

        if (!customer) {
            throw new ValidationError("Customer does not exist");
        }

        const combinedItems = new Map();

        for (const item of requestedItems) {
            if (!Number.isInteger(item.productId) || item.productId <= 0) {
                throw new ValidationError("Invalid product ID");
            }

            if (!Number.isInteger(item.quantity) || item.quantity <= 0) {
                throw new ValidationError("Quantity must be positive");
            }

            combinedItems.set(
                item.productId,
                (combinedItems.get(item.productId) ?? 0) + item.quantity
            );
        }

        const orderId =
            Math.max(0, ...db.table("orders").all().map((row) => row.orderId)) + 1;

        db.insert("orders", {
            orderId,
            customerId,
            status: "PENDING"
        });

        for (const [productId, quantity] of combinedItems) {
            const product = db.table("products").get(productId);

            if (!product) {
                throw new ValidationError(`Product ${productId} does not exist`);
            }

            if (product.stock < quantity) {
                throw new ValidationError(
                    `Insufficient stock for ${product.name}`
                );
            }

            const key = makeOrderItemKey(orderId, productId);

            db.insert("orderItems", {
                key,
                orderId,
                productId,
                quantity,
                unitPrice: product.price
            });

            product.stock -= quantity;
            db.table("products").rows.set(product.productId, product);
        }

        return orderId;
    });
}

function innerJoin(leftRows, rightRows, leftKey, rightKey) {
    const result = [];

    for (const left of leftRows) {
        for (const right of rightRows) {
            if (left[leftKey] === right[rightKey]) {
                result.push({
                    ...left,
                    ...right
                });
            }
        }
    }

    return result;
}

function leftJoin(leftRows, rightRows, leftKey, rightKey) {
    const result = [];

    for (const left of leftRows) {
        const matches = rightRows.filter(
            (right) => left[leftKey] === right[rightKey]
        );

        if (matches.length === 0) {
            result.push({ ...left });
        } else {
            for (const right of matches) {
                result.push({ ...left, ...right });
            }
        }
    }

    return result;
}

function demonstrateTablesAndRelationships(db) {
    console.log("\n=== TABLES, ROWS, AND COLUMNS ===");

    for (const [name, table] of db.tables) {
        console.log(`${name}: ${table.all().length} rows`);
    }

    console.log("\nProducts with selected columns:");
    for (const product of db.table("products").all()) {
        console.log(
            `${product.productId} | ${product.name} | ₹${product.price}`
        );
    }

    console.log("\nProducts joined with their category:");
    const joined = innerJoin(
        db.table("products").all(),
        db.table("categories").all(),
        "categoryId",
        "categoryId"
    );

    for (const row of joined) {
        console.log(`${row.name} -> ${row.name_1 ?? row.name}`);
    }

    /*
     * Because object spread cannot preserve duplicate property names, the
     * previous compact join is not appropriate for production reporting.
     * A relational projection explicitly selects the desired columns.
     */
    console.log("\nExplicit relational projection:");

    for (const product of db.table("products").all()) {
        const category = db.table("categories").get(product.categoryId);

        console.log({
            product: product.name,
            category: category.name,
            price: product.price
        });
    }
}

function demonstrateCustomerOrders(db) {
    console.log("\n=== CUSTOMER-TO-ORDER RELATIONSHIP ===");

    const orders = db.table("orders").all();

    const rows = leftJoin(
        db.table("customers").all(),
        orders,
        "customerId",
        "customerId"
    );

    for (const row of rows) {
        console.log({
            customer: row.name,
            orderId: row.orderId ?? null,
            status: row.status ?? null
        });
    }

    console.log(
        "\nThe left join preserves customers that have no matching orders."
    );
}

function demonstrateOrderDetails(db, orderId) {
    console.log("\n=== MANY-TO-MANY ORDER/PRODUCT RELATIONSHIP ===");

    const order = db.table("orders").get(orderId);

    if (!order) {
        throw new ValidationError("Order does not exist");
    }

    const customer = db.table("customers").get(order.customerId);

    const items = db.table("orderItems")
        .all()
        .filter((item) => item.orderId === orderId);

    let total = 0;

    console.log(`Order ${orderId} belongs to ${customer.name}`);

    for (const item of items) {
        const product = db.table("products").get(item.productId);
        const lineTotal = item.quantity * item.unitPrice;
        total += lineTotal;

        console.log({
            product: product.name,
            quantity: item.quantity,
            unitPrice: item.unitPrice,
            lineTotal
        });
    }

    console.log(`Order total: ₹${total.toFixed(2)}`);
}

function demonstrateAggregation(db) {
    console.log("\n=== RELATIONAL AGGREGATION ===");

    const products = db.table("products").all();

    const categoryStats = new Map();

    for (const product of products) {
        const category = db.table("categories").get(product.categoryId);

        if (!categoryStats.has(category.categoryId)) {
            categoryStats.set(category.categoryId, {
                category: category.name,
                productCount: 0,
                totalStock: 0,
                totalInventoryValue: 0
            });
        }

        const stats = categoryStats.get(category.categoryId);
        stats.productCount += 1;
        stats.totalStock += product.stock;
        stats.totalInventoryValue += product.stock * product.price;
    }

    for (const stats of categoryStats.values()) {
        console.log({
            ...stats,
            totalInventoryValue:
                Math.round(stats.totalInventoryValue * 100) / 100
        });
    }
}

function demonstrateValidationFailure(db) {
    console.log("\n=== CONSTRAINT AND TRANSACTION FAILURE ===");

    try {
        db.insert("products", {
            productId: 999,
            name: "Invalid Reference",
            categoryId: 404,
            price: 100,
            stock: 1
        });
    } catch (error) {
        console.log(`${error.name}: ${error.message}`);
    }

    const stockBefore = db.table("products").get(102).stock;

    try {
        createOrder(db, 2, [
            { productId: 102, quantity: 1 },
            { productId: 404, quantity: 1 }
        ]);
    } catch (error) {
        console.log(`Transaction rejected: ${error.message}`);
    }

    const stockAfter = db.table("products").get(102).stock;

    console.log({
        stockBefore,
        stockAfter,
        atomicRollbackPreservedStock: stockBefore === stockAfter
    });
}

async function demonstrateAsyncWorkflow(db) {
    console.log("\n=== EVENT-DRIVEN ASYNCHRONOUS WORKFLOW ===");

    /*
     * Real applications commonly perform database work behind asynchronous
     * APIs. Promise-based boundaries let application code wait for persistence
     * without blocking the event loop.
     */
    const persistAuditEvent = async (event) => {
        await Promise.resolve();
        return {
            persisted: true,
            event
        };
    };

    const result = await persistAuditEvent({
        type: "ORDER_CREATED",
        entity: "orders",
        entityId: 1
    });

    console.log(result);
}

function demonstrateParameterValidation() {
    console.log("\n=== APPLICATION-LEVEL VALIDATION ===");

    const validateCustomer = (customer) => {
        if (!customer || typeof customer !== "object") {
            throw new ValidationError("Customer must be an object");
        }

        if (!Number.isInteger(customer.customerId) || customer.customerId <= 0) {
            throw new ValidationError("customerId must be a positive integer");
        }

        if (typeof customer.email !== "string" ||
            !customer.email.includes("@")) {
            throw new ValidationError("Customer email is invalid");
        }
    };

    try {
        validateCustomer({
            customerId: -5,
            email: "invalid"
        });
    } catch (error) {
        console.log(`${error.name}: ${error.message}`);
    }

    console.log(
        "Application validation improves error messages, while database "
        + "constraints remain the final integrity boundary."
    );
}

async function main() {
    const db = createDatabase();
    seedDatabase(db);

    console.log("RELATIONAL DATABASE FUNDAMENTALS");

    demonstrateTablesAndRelationships(db);

    const orderId = createOrder(db, 1, [
        { productId: 101, quantity: 1 },
        { productId: 301, quantity: 2 }
    ]);

    console.log(`\nCreated order ${orderId}.`);

    demonstrateCustomerOrders(db);
    demonstrateOrderDetails(db, orderId);
    demonstrateAggregation(db);
    demonstrateValidationFailure(db);
    demonstrateParameterValidation();
    await demonstrateAsyncWorkflow(db);

    console.log("\n=== DATA MODEL ===");
    console.log(`
customers
    |
    +----< orders
              |
              +----< orderItems >---- products >---- categories

The customer/order and category/product relationships are one-to-many.
The order/product relationship is many-to-many and is represented through
the orderItems junction table.
`);

    console.log("The in-memory model is intentionally small, but the same");
    console.log("relationships map directly to tables and foreign keys in");
    console.log("a production relational database.");
}

main().catch((error) => {
    console.error(`Fatal error: ${error.name}: ${error.message}`);
    process.exitCode = 1;
});
