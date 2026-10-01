# Database Fundamentals: Databases, Tables, Rows, Columns, and Relationships

## Topic Scope

This repository develops the foundations of relational database design through a concrete inventory and order-management model.

The central data model contains customers, product categories, products, orders, and order items. These entities are separated because they represent different kinds of information and participate in different relationships.

The implementations demonstrate the distinction between:

- a **database**, which provides the persistent or managed environment containing related data structures;
- a **table**, which represents a structured collection of records for an entity or relationship;
- a **row**, which represents one record in a table;
- a **column**, which defines one attribute stored for every applicable row;
- a **primary key**, which identifies a row;
- a **foreign key**, which connects a row to a row in another table;
- a **relationship**, which describes how records in different tables correspond.

The examples intentionally use relational concepts rather than treating a database as a collection of unrelated lists.

---

## The Domain Model

The case study represents a small commerce system.

A customer can place multiple orders. A product belongs to one category. An order can contain multiple products, and a product can occur in multiple orders. Because the order/product relationship is many-to-many, it is represented through the `order_items` or `orderItems` junction table.

The conceptual structure is:

    customers
        |
        | one-to-many
        v
      orders
        |
        | one-to-many
        v
    order_items
        ^
        | many-to-one
        |
     products
        |
        | many-to-one
        v
    categories

The two relationships around `order_items` combine to form:

    orders many-to-many products

This decomposition is important because putting an arbitrary number of product columns directly into `orders` would make the structure difficult to query, constrain, and extend.

---

## Databases and Tables

A database is the broader data-management environment. Within a relational database, tables provide structured storage for related records.

The Python implementation uses SQLite because Python's standard library provides `sqlite3`, allowing the relational model to be demonstrated without an external database server.

The Python database contains these tables:

| Table | Purpose | Primary key |
| --- | --- | --- |
| `customers` | Stores customer identity and contact information | `customer_id` |
| `categories` | Stores product categories | `category_id` |
| `products` | Stores products, prices, inventory, and category references | `product_id` |
| `orders` | Stores order-level information | `order_id` |
| `order_items` | Connects orders to products and stores quantity and historical unit price | `(order_id, product_id)` |

The JavaScript implementation models the same relational ideas in memory rather than requiring an npm database driver. Its `RelationalDatabase` class owns tables, while the `Table` class owns rows and enforces primary-key, unique, and foreign-key rules.

The C++ case study uses typed structures and associative containers to represent the same entities while emphasizing how database concepts can be implemented at the application-system level.

---

## Columns and Data Attributes

A column defines an attribute of the records stored in a table.

For example, the `products` table contains:

    product_id
    name
    category_id
    price
    stock_quantity

Each row supplies values for these attributes.

A product row can therefore be represented conceptually as:

    product_id = 101
    name = "ThinkPad E16"
    category_id = 1
    price = 89999.00
    stock_quantity = 12

The column definition is different from the value stored in an individual row. `price` is the attribute; `89999.00` is one value for that attribute.

Good relational schemas also attach appropriate rules to columns. The Python implementation uses `NOT NULL`, `UNIQUE`, `CHECK`, primary-key, and foreign-key constraints. These rules prevent structurally invalid records from entering the database.

---

## Rows and Record Identity

A row represents one record.

For example, one customer row represents one customer:

    customer_id = 1
    name = "Atul Pandey"
    email = "atul@example.com"

The `customer_id` is the primary key.

A primary key provides stable identity for a record within its table. It also allows other tables to refer to that record through a foreign key.

The implementations intentionally use numeric identifiers because they make relationships easy to inspect:

    customers.customer_id
    orders.customer_id

An `orders.customer_id` value of `1` refers to the customer whose `customers.customer_id` is `1`.

---

## Primary Keys

A primary key identifies a row uniquely.

The Python schema declares definitions such as `customer_id INTEGER PRIMARY KEY`. SQLite then prevents two rows from using the same primary-key value.

The JavaScript `Table` class maintains rows in a `Map` keyed by the primary-key value. Attempting to insert another row with an existing key raises a `DatabaseConstraintError`.

The C++ implementation uses `std::unordered_map<int, Customer>`, `std::unordered_map<int, Product>`, and similar structures. The map key models the uniqueness requirement of the primary key.

A primary key should not be confused with an ordinary attribute. An email address may be unique in a particular business model, but its business meaning and change behavior are different from a generated database identifier.

---

## Foreign Keys

A foreign key creates a referential relationship between tables.

The Python `products.category_id` column references `categories.category_id`.

The relationship means a product cannot legitimately reference category `999` when category `999` does not exist.

The same principle appears in:

    orders.customer_id -> customers.customer_id

and:

    order_items.order_id -> orders.order_id
    order_items.product_id -> products.product_id

The JavaScript implementation checks referenced rows during insertion. The C++ implementation performs equivalent checks before adding products, orders, and order items.

Foreign keys therefore do more than document a relationship. When enforced, they prevent references to nonexistent parent records.

---

## One-to-Many Relationships

A one-to-many relationship means one record on one side can correspond to many records on the other side.

The customer/order relationship is one-to-many:

    one customer
        |
        +--- order A
        +--- order B
        +--- order C

The foreign key is stored on the many side:

    orders.customer_id

The category/product relationship has the same structure:

    one category
        |
        +--- product A
        +--- product B
        +--- product C

The corresponding foreign key is:

    products.category_id

This arrangement avoids copying the complete customer or category record into every child row.

---

## Many-to-Many Relationships

Orders and products have a many-to-many relationship.

One order can contain multiple products:

    Order 1001
        -> Laptop
        -> Keyboard
        -> USB-C Dock

One product can appear in multiple orders:

    Laptop
        -> Order 1001
        -> Order 1002
        -> Order 1008

A direct foreign key from `orders` to one product would not represent this structure correctly.

The solution is a junction table:

    order_items

It contains:

    order_id
    product_id
    quantity
    unit_price

The pair `(order_id, product_id)` identifies the product occurrence within an order.

This converts the many-to-many relationship into two one-to-many relationships:

    orders -> order_items
    products -> order_items

The junction table can also hold relationship-specific attributes. `quantity` does not describe the product globally and does not describe the order globally. It describes the relationship between a particular order and a particular product.

---

## Historical Values in Relationship Tables

The `unit_price` column in `order_items` demonstrates an important modeling decision.

A product has a current price:

    products.price

An order item records the price actually used when the order was created:

    order_items.unit_price

If the product price later changes, historical orders should not silently change their financial meaning.

For example:

    products.price = 89999

might later become:

    products.price = 94999

A previous order can still retain:

    order_items.unit_price = 89999

This illustrates why relational modeling requires understanding the meaning of attributes, not simply deciding which table has available space for a value.

---

## Queries and Projections

A query can retrieve only the columns needed for a particular operation.

The Python implementation demonstrates:

    SELECT name, price
    FROM products

rather than always retrieving every product column.

Selecting specific columns is called a projection in relational-algebra terminology.

The C++ implementation performs an equivalent conceptual projection when it prints product names, categories, prices, and stock after resolving their related records.

The JavaScript implementation demonstrates explicit projection after resolving the product/category relationship rather than relying on an object merge that could accidentally overwrite fields with identical names.

---

## Joins

A join combines related rows from different tables according to a relationship.

The product/category relationship can be queried conceptually as:

    products
        JOIN categories
        ON products.category_id = categories.category_id

The Python program executes this directly with SQL.

The JavaScript program implements `innerJoin()` and `leftJoin()` to expose the mechanics of matching rows in memory.

The C++ program performs the same relationship resolution through primary-key lookups.

A join is therefore not merely a way to "combine tables." The join condition defines which records correspond.

---

## Inner Joins

An inner join returns rows for which the join condition has a matching record on both sides.

For products and categories, an inner join can produce:

| Product | Category |
| --- | --- |
| ThinkPad E16 | Laptops |
| Framework Laptop | Laptops |
| 27-inch 4K Monitor | Monitors |
| Mechanical Keyboard | Accessories |

A product whose category reference is invalid would not produce a valid inner-join result.

The Python implementation uses an SQL `INNER JOIN`, while the JavaScript implementation contains an explicit matching loop to demonstrate the underlying operation.

---

## Left Joins and Missing Related Records

A left join preserves every row from the left table even if no related row exists on the right.

The Python program uses a customer-to-order left join so a customer with no orders remains visible.

The missing order attributes become `NULL`.

Conceptually:

| Customer | Order |
| --- | --- |
| Customer A | 1001 |
| Customer B | 1002 |
| Customer C | NULL |

This distinction matters in reporting. An inner join can accidentally remove entities that have no related records, while a left join can preserve them for questions such as "show every customer and their order count."

---

## NULL and Missing Data

`NULL` represents the absence of a value in a relational database. It is not equivalent to zero, an empty string, or the text `"NULL"`.

In the left-join example, a customer without an order receives `NULL` for order-specific columns.

The difference is important:

- `0` can mean a measured numeric quantity is zero.
- `''` can mean an empty text value.
- `NULL` means the value is absent or unknown according to the database model.

Queries involving `NULL` also require appropriate SQL semantics. Equality comparisons with `NULL` do not behave like ordinary value comparisons, which is why SQL provides predicates such as `IS NULL`.

---

## Constraints and Data Integrity

The Python schema contains several constraints.

`NOT NULL` prevents required attributes from being omitted.

`UNIQUE` prevents duplicate values where the model requires uniqueness, such as customer email addresses.

`CHECK` enforces domain rules such as:

    price >= 0
    stock_quantity >= 0
    quantity > 0

Foreign keys enforce valid references.

The JavaScript and C++ versions reproduce these rules at the application-model level.

A useful architectural distinction is that application validation and database constraints have different roles. Application validation can produce immediate and user-friendly errors, while database constraints protect the data boundary itself.

---

## Referential Actions

The Python schema deliberately uses different deletion behaviors.

For `products.category_id`, deletion of a referenced category is restricted because silently deleting or invalidating the category relationship could damage product classification.

For `order_items.order_id`, `ON DELETE CASCADE` is used because an order item has no independent meaning in this model without its parent order.

This illustrates that foreign-key behavior should reflect domain meaning.

`CASCADE` is not automatically safer than `RESTRICT`. The appropriate action depends on whether child data should survive independently when the parent disappears.

---

## Transactions and Atomicity

Creating an order modifies several related pieces of data:

- an order row is created;
- one or more order-item rows are created;
- product inventory is reduced.

These operations should behave as one unit.

The Python `transaction()` context manager commits when the operation succeeds and rolls back when an exception occurs.

The JavaScript `RelationalDatabase.transaction()` method takes a snapshot and restores it after a failure.

The C++ `Transaction` class stores rollback state for the small in-memory case study.

The failed-order demonstrations are particularly important. If product `102` is valid but product `999` does not exist, the entire order operation fails rather than leaving a partially created order with partially modified inventory.

This is the application-level meaning of atomicity: the grouped operation is treated as one logical unit.

---

## Database Normalization in the Case Study

The schema avoids several obvious forms of duplication.

Customer information is stored in `customers`, not repeated in every order.

Category names are stored in `categories`, not copied into every product row.

Product attributes are stored in `products`, while order-specific quantity and historical price are stored in `order_items`.

This separation reduces update anomalies.

If a category name changes, the category row can be updated rather than searching through every product for repeated copies of that name.

Normalization is not simply "make many tables." It is the process of organizing attributes and relationships so that facts have appropriate ownership and duplication is controlled.

---

## Python Implementation

The Python program uses the standard-library `sqlite3` module.

Its most important database-specific components are:

- `Database`, which owns the SQLite connection and enables foreign-key enforcement.
- `create_schema()`, which creates the five related tables and indexes.
- `create_order()`, which demonstrates validation, foreign-key lookup, inventory modification, and transactional atomicity.
- `demonstrate_relationships()`, which executes real SQL joins.
- `demonstrate_aggregation()`, which uses `GROUP BY`, `COUNT`, `AVG`, and `SUM`.
- `demonstrate_null_and_outer_join()`, which shows why a left join preserves customers without orders.
- `demonstrate_constraints()`, which deliberately attempts invalid inserts.
- `demonstrate_safe_parameterization()`, which uses SQL parameters instead of concatenating untrusted input.
- `demonstrate_index_inspection()`, which inspects indexes and the SQLite query plan.

The Python version is the most database-native implementation because it uses an actual relational database engine.

---

## JavaScript Implementation

The JavaScript program takes a different approach.

Instead of translating the SQLite code line by line, it implements a small relational model using JavaScript classes and `Map` objects.

`RelationalDatabase` manages tables.

`Table` manages rows and enforces:

- primary-key uniqueness;
- unique indexes;
- foreign-key references.

`createOrder()` demonstrates transactional behavior through snapshots.

`innerJoin()` and `leftJoin()` expose the row-matching mechanics explicitly.

The JavaScript implementation also includes an asynchronous persistence-style function to show how relational operations can sit behind Promise-based application boundaries in Node.js.

This representation is useful for understanding the relationship between database rules and application code without requiring a database server.

---

## C++ Case Study

The C++ implementation models a typed repository inventory system.

Its entity structures are:

    Customer
    Category
    Product
    Order
    OrderItem

The `RepositoryDatabase` class owns these collections and enforces relational rules.

`std::unordered_map` is used for primary-key-oriented storage and lookup. The `ordersByCustomer_` structure acts as a secondary index, demonstrating why indexes can change the cost of locating related rows.

The C++ program also preserves order-time pricing through `OrderItem::unitPrice`, rather than relying on the product's current price.

The order creation workflow validates the customer, consolidates duplicate products, validates product references, checks inventory, creates the order, creates order items, and reduces stock.

The `Transaction` class provides rollback behavior for the intentionally small in-memory case study. It copies state before the operation and restores the previous state if the transaction object is destroyed without being committed.

This is deliberately different from the implementation strategy of a production database engine. A real database normally uses storage-level transaction mechanisms rather than copying the complete database into application memory.

---

## Aggregation

Relational databases are not limited to retrieving individual rows.

The Python implementation calculates category-level information using:

    COUNT
    AVG
    SUM
    GROUP BY

The resulting reports include product counts, average prices, and total stock.

The JavaScript and C++ implementations calculate comparable category statistics through application-side aggregation.

The distinction is technically important. In a production relational database, pushing appropriate aggregation into SQL can reduce the amount of data transferred to the application and allow the database query optimizer to select efficient execution strategies.

---

## Indexes

An index is an additional data structure maintained to accelerate particular lookup patterns.

The Python schema creates indexes for:

    products.category_id
    orders.customer_id
    order_items.product_id
    orders.status

These indexes correspond to columns frequently used for relationship lookups or filtering.

An index is not free. It consumes storage and generally increases the work required for inserts, updates, and deletes because the index must remain synchronized with the table.

Index design should therefore follow actual query patterns rather than placing an index on every column.

The Python program uses `EXPLAIN QUERY PLAN` to inspect how SQLite approaches a customer-based order lookup.

The C++ `ordersByCustomer_` structure provides a simplified conceptual demonstration of the same access-path idea.

---

## Data Integrity Failure Modes

The examples deliberately exercise failure conditions.

A duplicate customer email is rejected by a uniqueness rule.

A negative product price is rejected by a check constraint.

A product referencing an unknown category is rejected by referential integrity.

An order requesting more inventory than exists is rejected by business validation.

An order referencing a nonexistent product fails and rolls back the previously valid part of the operation.

These cases show why relational systems need more than data storage. A useful schema defines what constitutes valid data.

---

## Common Modeling Mistakes

### Repeating entity information

Copying the customer's name and email into every order creates duplicated facts. Changes to customer information can then produce inconsistent records.

The case study instead stores `customer_id` in `orders`.

### Storing multiple products in one text column

A value such as:

    "Laptop, Keyboard, Dock"

does not provide the relational structure required for quantities, product identity, pricing, constraints, or efficient product-level queries.

The `order_items` table represents each relationship as a row.

### Confusing current and historical attributes

Using `products.price` when reconstructing an old order can produce an incorrect historical total after a price change.

The case study therefore stores `unit_price` in `order_items`.

### Treating a foreign key as ordinary text

A category name stored directly in a product row does not enforce that the category exists.

A foreign key such as `products.category_id` establishes an explicit relationship.

### Relying only on application validation

Application validation can be bypassed by another program, script, migration, administrative action, or concurrent process.

Database-level constraints provide a stronger integrity boundary.

---

## Performance Considerations

A relational design must consider both logical correctness and query behavior.

Primary-key lookups are commonly optimized through the database's primary-key structures.

Foreign-key columns involved in joins can benefit from appropriate indexes, particularly as tables grow.

Aggregation over millions of rows has very different performance characteristics from aggregation over a few dozen rows.

The Python program therefore includes query-plan inspection rather than treating indexes as purely theoretical objects.

The C++ implementation demonstrates the same principle with `ordersByCustomer_`: searching an indexed structure can avoid scanning every order when the access pattern is known.

The precise performance of a production relational database depends on its storage engine, statistics, indexes, query planner, transaction isolation, hardware, data distribution, and workload.

---

## Security Considerations

The Python implementation demonstrates parameterized SQL:

    SELECT customer_id, name, email
    FROM customers
    WHERE name = ?

The input value is passed separately from the SQL statement.

This separation prevents ordinary user input from being interpreted as SQL syntax.

Concatenating untrusted strings into SQL statements can create SQL injection vulnerabilities.

Database security also extends beyond query construction. Production systems should apply appropriate authentication, authorization, least-privilege database accounts, protected credentials, encrypted connections where required, auditing, backups, and controlled schema migrations.

The in-memory JavaScript and C++ examples do not require database credentials because they do not connect to an external database server.

---

## Debugging and Diagnostics

When a relational query produces an unexpected result, the relationship itself should be inspected rather than assuming the database is incorrect.

Useful diagnostic questions include:

- Which table owns the attribute being displayed?
- Which column identifies the row?
- Which foreign key connects the tables?
- Is the join condition matching the intended columns?
- Is an inner join unintentionally removing records with no related row?
- Could `NULL` be responsible for an unexpected result?
- Is duplicate data causing multiple join matches?
- Does an aggregate require grouping at a different level?
- Is an index being used for an important lookup?

The Python program exposes schema metadata through `PRAGMA table_info`, foreign-key metadata through `PRAGMA foreign_key_list`, and execution planning through `EXPLAIN QUERY PLAN`.

These diagnostics connect the logical model to the actual database structure.

---

## Practical Relationship Reference

| Relationship | Foreign key location | Cardinality | Example |
| --- | --- | --- | --- |
| Customer → Order | `orders.customer_id` | One-to-many | One customer can place many orders |
| Category → Product | `products.category_id` | One-to-many | One category can contain many products |
| Order → Order Item | `order_items.order_id` | One-to-many | One order can contain many lines |
| Product → Order Item | `order_items.product_id` | One-to-many | One product can occur in many order lines |
| Order ↔ Product | `order_items` | Many-to-many | Orders contain products and products appear in orders |

The final relationship is represented indirectly through the junction table rather than by placing multiple product references inside `orders`.

---

## Implementation Relationship

The three implementations use different techniques for the same relational ideas.

| Concern | Python | JavaScript | C++ |
| --- | --- | --- | --- |
| Storage | SQLite database | In-memory table objects | Typed in-memory repository |
| Row identity | SQLite primary keys | `Map` keys | `unordered_map` keys |
| Relationships | SQL foreign keys | Explicit foreign-key validation | Explicit reference validation |
| Joins | SQL joins | Join functions and key lookups | Repository lookups |
| Transactions | SQLite transaction | Snapshot and restore | State backup and restore |
| Aggregation | SQL aggregate functions | JavaScript maps | C++ maps and arithmetic |
| Indexing | SQLite indexes | Map-based access | Secondary customer index |
| Validation | SQL plus Python | JavaScript validation | C++ exceptions and validation |

The differences are intentional. A database concept should remain understandable even when the implementation technology changes.

---

## Production Considerations

A production relational system would normally separate the database schema, migration process, data-access layer, business logic, and application interface.

Schema changes should be managed through controlled migrations rather than casually rebuilding tables.

Transactions should cover operations whose partial completion would violate business consistency.

Foreign keys should be enabled and tested when referential integrity is required.

Indexes should be derived from observed query patterns and measured workload behavior.

Financial or historical data should preserve the values needed to reconstruct the meaning of past transactions.

Constraints should be treated as part of the domain model, not merely as database decoration.

The small examples in these files intentionally keep infrastructure simple so that the underlying relationships remain visible.
