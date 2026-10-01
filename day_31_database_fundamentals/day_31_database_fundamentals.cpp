/*
 * Database Fundamentals: Repository Inventory Case Study
 *
 * C++17 implementation of a small relational data model for an inventory
 * system. The program demonstrates:
 *
 * - databases as collections of related tables
 * - rows as entity records
 * - columns as typed attributes
 * - primary keys
 * - foreign keys
 * - one-to-many relationships
 * - many-to-many relationships through a junction table
 * - relational joins
 * - aggregation
 * - validation and integrity constraints
 * - transaction-like atomic updates
 * - index-oriented lookup
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic database_fundamentals.cpp -o database_fundamentals
 */

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

struct Customer {
    int id;
    std::string name;
    std::string email;
};

struct Category {
    int id;
    std::string name;
};

struct Product {
    int id;
    std::string name;
    int categoryId;
    double price;
    int stock;
};

enum class OrderStatus {
    Pending,
    Paid,
    Shipped,
    Cancelled
};

std::string statusToString(OrderStatus status) {
    switch (status) {
        case OrderStatus::Pending:
            return "PENDING";
        case OrderStatus::Paid:
            return "PAID";
        case OrderStatus::Shipped:
            return "SHIPPED";
        case OrderStatus::Cancelled:
            return "CANCELLED";
    }

    return "UNKNOWN";
}

struct Order {
    int id;
    int customerId;
    OrderStatus status;
};

struct OrderItem {
    int orderId;
    int productId;
    int quantity;
    double unitPrice;
};

class ConstraintError : public std::runtime_error {
public:
    explicit ConstraintError(const std::string& message)
        : std::runtime_error(message) {}
};

class ValidationError : public std::runtime_error {
public:
    explicit ValidationError(const std::string& message)
        : std::runtime_error(message) {}
};

class RepositoryDatabase {
private:
    std::unordered_map<int, Customer> customers_;
    std::unordered_map<int, Category> categories_;
    std::unordered_map<int, Product> products_;
    std::unordered_map<int, Order> orders_;

    /*
     * orderItems has a composite logical key. An order ID alone is not enough
     * because one order can contain several products.
     */
    std::unordered_map<std::string, OrderItem> orderItems_;

    /*
     * This secondary index maps customer IDs to their orders. A real database
     * index provides a similar purpose: finding matching records without
     * scanning every row in the table.
     */
    std::unordered_multimap<int, int> ordersByCustomer_;

    static std::string itemKey(int orderId, int productId) {
        return std::to_string(orderId) + ":" + std::to_string(productId);
    }

public:
    void insertCustomer(const Customer& customer) {
        if (customer.id <= 0) {
            throw ValidationError("Customer ID must be positive.");
        }

        if (customer.name.size() < 2) {
            throw ValidationError("Customer name is too short.");
        }

        if (customer.email.find('@') == std::string::npos) {
            throw ValidationError("Customer email is invalid.");
        }

        if (customers_.contains(customer.id)) {
            throw ConstraintError("Duplicate customer primary key.");
        }

        const auto duplicateEmail = std::find_if(
            customers_.begin(),
            customers_.end(),
            [&](const auto& entry) {
                return entry.second.email == customer.email;
            }
        );

        if (duplicateEmail != customers_.end()) {
            throw ConstraintError("Customer email must be unique.");
        }

        customers_.emplace(customer.id, customer);
    }

    void insertCategory(const Category& category) {
        if (category.id <= 0 || category.name.empty()) {
            throw ValidationError("Invalid category.");
        }

        if (categories_.contains(category.id)) {
            throw ConstraintError("Duplicate category primary key.");
        }

        const auto duplicate = std::find_if(
            categories_.begin(),
            categories_.end(),
            [&](const auto& entry) {
                return entry.second.name == category.name;
            }
        );

        if (duplicate != categories_.end()) {
            throw ConstraintError("Category name must be unique.");
        }

        categories_.emplace(category.id, category);
    }

    void insertProduct(const Product& product) {
        if (product.id <= 0) {
            throw ValidationError("Product ID must be positive.");
        }

        if (product.price < 0 || product.stock < 0) {
            throw ValidationError("Product price and stock cannot be negative.");
        }

        if (!categories_.contains(product.categoryId)) {
            throw ConstraintError(
                "Product references a category that does not exist."
            );
        }

        if (products_.contains(product.id)) {
            throw ConstraintError("Duplicate product primary key.");
        }

        products_.emplace(product.id, product);
    }

    void insertOrder(const Order& order) {
        if (order.id <= 0) {
            throw ValidationError("Order ID must be positive.");
        }

        if (!customers_.contains(order.customerId)) {
            throw ConstraintError(
                "Order references a customer that does not exist."
            );
        }

        if (orders_.contains(order.id)) {
            throw ConstraintError("Duplicate order primary key.");
        }

        orders_.emplace(order.id, order);
        ordersByCustomer_.emplace(order.customerId, order.id);
    }

    void insertOrderItem(const OrderItem& item) {
        if (!orders_.contains(item.orderId)) {
            throw ConstraintError("Order item references a missing order.");
        }

        auto productIterator = products_.find(item.productId);

        if (productIterator == products_.end()) {
            throw ConstraintError(
                "Order item references a missing product."
            );
        }

        if (item.quantity <= 0) {
            throw ValidationError("Order quantity must be positive.");
        }

        if (item.unitPrice < 0) {
            throw ValidationError("Order item price cannot be negative.");
        }

        const std::string key = itemKey(item.orderId, item.productId);

        if (orderItems_.contains(key)) {
            throw ConstraintError(
                "An order cannot contain the same product twice."
            );
        }

        if (productIterator->second.stock < item.quantity) {
            throw ValidationError(
                "Insufficient stock for the requested product."
            );
        }

        /*
         * The unit price is copied into the order item rather than read from
         * the product forever. This preserves the price actually used by the
         * order even if the product's current price changes later.
         */
        orderItems_.emplace(key, item);
        productIterator->second.stock -= item.quantity;
    }

    std::optional<Customer> findCustomer(int customerId) const {
        auto iterator = customers_.find(customerId);

        if (iterator == customers_.end()) {
            return std::nullopt;
        }

        return iterator->second;
    }

    std::optional<Product> findProduct(int productId) const {
        auto iterator = products_.find(productId);

        if (iterator == products_.end()) {
            return std::nullopt;
        }

        return iterator->second;
    }

    std::optional<Category> findCategory(int categoryId) const {
        auto iterator = categories_.find(categoryId);

        if (iterator == categories_.end()) {
            return std::nullopt;
        }

        return iterator->second;
    }

    std::vector<Order> findOrdersForCustomer(int customerId) const {
        std::vector<Order> result;

        const auto range = ordersByCustomer_.equal_range(customerId);

        for (auto iterator = range.first; iterator != range.second; ++iterator) {
            auto order = orders_.find(iterator->second);

            if (order != orders_.end()) {
                result.push_back(order->second);
            }
        }

        return result;
    }

    std::vector<OrderItem> findItemsForOrder(int orderId) const {
        std::vector<OrderItem> result;

        for (const auto& [key, item] : orderItems_) {
            if (item.orderId == orderId) {
                result.push_back(item);
            }
        }

        return result;
    }

    double orderTotal(int orderId) const {
        if (!orders_.contains(orderId)) {
            throw ValidationError("Cannot calculate a missing order.");
        }

        double total = 0.0;

        for (const auto& item : findItemsForOrder(orderId)) {
            total += item.quantity * item.unitPrice;
        }

        return total;
    }

    void printProductsWithCategories() const {
        std::cout << "\nPRODUCT TABLE JOINED WITH CATEGORY TABLE\n";
        std::cout
            << std::left
            << std::setw(8) << "ID"
            << std::setw(28) << "PRODUCT"
            << std::setw(18) << "CATEGORY"
            << std::setw(14) << "PRICE"
            << "STOCK\n";

        std::cout << std::string(78, '-') << '\n';

        for (const auto& [id, product] : products_) {
            auto category = findCategory(product.categoryId);

            std::cout
                << std::left
                << std::setw(8) << product.id
                << std::setw(28) << product.name
                << std::setw(18)
                << (category ? category->name : "INVALID")
                << std::setw(14)
                << std::fixed
                << std::setprecision(2)
                << product.price
                << product.stock
                << '\n';
        }
    }

    void printCustomerOrders(int customerId) const {
        auto customer = findCustomer(customerId);

        if (!customer) {
            throw ValidationError("Customer does not exist.");
        }

        std::cout << "\nORDERS FOR " << customer->name << '\n';

        const auto orders = findOrdersForCustomer(customerId);

        if (orders.empty()) {
            std::cout << "No orders found.\n";
            return;
        }

        for (const auto& order : orders) {
            std::cout
                << "Order " << order.id
                << " | " << statusToString(order.status)
                << " | ₹" << std::fixed << std::setprecision(2)
                << orderTotal(order.id)
                << '\n';
        }
    }

    void printOrderDetails(int orderId) const {
        auto orderIterator = orders_.find(orderId);

        if (orderIterator == orders_.end()) {
            throw ValidationError("Order does not exist.");
        }

        const Order& order = orderIterator->second;
        auto customer = findCustomer(order.customerId);

        std::cout
            << "\nORDER " << order.id
            << " | CUSTOMER: "
            << (customer ? customer->name : "UNKNOWN")
            << " | STATUS: "
            << statusToString(order.status)
            << '\n';

        std::cout
            << std::left
            << std::setw(28) << "PRODUCT"
            << std::setw(10) << "QTY"
            << std::setw(14) << "UNIT PRICE"
            << "LINE TOTAL\n";

        for (const auto& item : findItemsForOrder(orderId)) {
            auto product = findProduct(item.productId);

            if (!product) {
                continue;
            }

            const double lineTotal = item.quantity * item.unitPrice;

            std::cout
                << std::left
                << std::setw(28) << product->name
                << std::setw(10) << item.quantity
                << std::setw(14) << item.unitPrice
                << lineTotal
                << '\n';
        }

        std::cout
            << "TOTAL: ₹"
            << std::fixed
            << std::setprecision(2)
            << orderTotal(orderId)
            << '\n';
    }

    void printCategoryInventory() const {
        struct Statistics {
            int productCount = 0;
            int totalStock = 0;
            double inventoryValue = 0.0;
        };

        std::unordered_map<int, Statistics> statistics;

        for (const auto& [id, product] : products_) {
            auto& stats = statistics[product.categoryId];

            ++stats.productCount;
            stats.totalStock += product.stock;
            stats.inventoryValue += product.stock * product.price;
        }

        std::cout << "\nCATEGORY INVENTORY AGGREGATION\n";

        for (const auto& [categoryId, stats] : statistics) {
            auto category = findCategory(categoryId);

            std::cout
                << (category ? category->name : "UNKNOWN")
                << " | products=" << stats.productCount
                << " | stock=" << stats.totalStock
                << " | inventory value=₹"
                << std::fixed
                << std::setprecision(2)
                << stats.inventoryValue
                << '\n';
        }
    }

    /*
     * A transaction requires rollback information. For this teaching case,
     * copying the small in-memory database state is sufficient. A production
     * database engine instead maintains transactional state through its
     * storage engine, logging, locks, MVCC, or equivalent mechanisms.
     */
    class Transaction {
    private:
        RepositoryDatabase& database_;
        auto customersBackup_ =
            std::unordered_map<int, Customer>{};
        auto categoriesBackup_ =
            std::unordered_map<int, Category>{};
        auto productsBackup_ =
            std::unordered_map<int, Product>{};
        auto ordersBackup_ =
            std::unordered_map<int, Order>{};
        auto orderItemsBackup_ =
            std::unordered_map<std::string, OrderItem>{};
        auto ordersByCustomerBackup_ =
            std::unordered_multimap<int, int>{};
        bool committed_ = false;

    public:
        explicit Transaction(RepositoryDatabase& database)
            : database_(database),
              customersBackup_(database.customers_),
              categoriesBackup_(database.categories_),
              productsBackup_(database.products_),
              ordersBackup_(database.orders_),
              orderItemsBackup_(database.orderItems_),
              ordersByCustomerBackup_(database.ordersByCustomer_) {}

        void commit() {
            committed_ = true;
        }

        ~Transaction() {
            if (!committed_) {
                database_.customers_ = customersBackup_;
                database_.categories_ = categoriesBackup_;
                database_.products_ = productsBackup_;
                database_.orders_ = ordersBackup_;
                database_.orderItems_ = orderItemsBackup_;
                database_.ordersByCustomer_ = ordersByCustomerBackup_;
            }
        }
    };

    Transaction beginTransaction() {
        return Transaction(*this);
    }

    int nextOrderId() const {
        int maximum = 0;

        for (const auto& [id, order] : orders_) {
            maximum = std::max(maximum, id);
        }

        return maximum + 1;
    }

    std::size_t customerCount() const {
        return customers_.size();
    }

    std::size_t productCount() const {
        return products_.size();
    }

    int productStock(int productId) const {
        auto product = findProduct(productId);

        if (!product) {
            throw ValidationError("Product does not exist.");
        }

        return product->stock;
    }
};

int createOrder(
    RepositoryDatabase& database,
    int customerId,
    const std::vector<std::pair<int, int>>& requestedItems
) {
    if (requestedItems.empty()) {
        throw ValidationError("An order requires at least one product.");
    }

    if (!database.findCustomer(customerId)) {
        throw ValidationError("Customer does not exist.");
    }

    auto transaction = database.beginTransaction();

    /*
     * Duplicate products are consolidated before persistence. This avoids
     * creating conflicting logical lines for the same order/product pair.
     */
    std::unordered_map<int, int> combined;

    for (const auto& [productId, quantity] : requestedItems) {
        if (quantity <= 0) {
            throw ValidationError("Quantity must be positive.");
        }

        if (!database.findProduct(productId)) {
            throw ValidationError("Requested product does not exist.");
        }

        combined[productId] += quantity;
    }

    const int orderId = database.nextOrderId();

    database.insertOrder({
        orderId,
        customerId,
        OrderStatus::Pending
    });

    for (const auto& [productId, quantity] : combined) {
        const auto product = database.findProduct(productId);

        if (!product) {
            throw ValidationError("Product disappeared during order creation.");
        }

        if (product->stock < quantity) {
            throw ValidationError(
                "Insufficient stock for product " + product->name
            );
        }

        database.insertOrderItem({
            orderId,
            productId,
            quantity,
            product->price
        });
    }

    transaction.commit();
    return orderId;
}

void seed(RepositoryDatabase& database) {
    database.insertCategory({1, "Laptops"});
    database.insertCategory({2, "Monitors"});
    database.insertCategory({3, "Accessories"});

    database.insertCustomer({
        1,
        "Atul Pandey",
        "atul@example.com"
    });

    database.insertCustomer({
        2,
        "Priya Sharma",
        "priya@example.com"
    });

    database.insertCustomer({
        3,
        "Rahul Verma",
        "rahul@example.com"
    });

    database.insertProduct({
        101,
        "ThinkPad E16",
        1,
        89999.00,
        12
    });

    database.insertProduct({
        102,
        "Framework Laptop",
        1,
        104999.00,
        8
    });

    database.insertProduct({
        201,
        "27-inch 4K Monitor",
        2,
        32999.00,
        15
    });

    database.insertProduct({
        301,
        "Mechanical Keyboard",
        3,
        6999.00,
        30
    });
}

void demonstrateConstraints(RepositoryDatabase& database) {
    std::cout << "\nCONSTRAINT TESTS\n";

    try {
        database.insertProduct({
            999,
            "Invalid Category Product",
            999,
            100.00,
            1
        });
    } catch (const std::exception& error) {
        std::cout << "Rejected: " << error.what() << '\n';
    }

    try {
        database.insertCustomer({
            1,
            "Duplicate",
            "duplicate@example.com"
        });
    } catch (const std::exception& error) {
        std::cout << "Rejected: " << error.what() << '\n';
    }
}

void demonstrateRollback(RepositoryDatabase& database) {
    std::cout << "\nTRANSACTION ROLLBACK CASE\n";

    const int stockBefore = database.productStock(102);

    try {
        createOrder(
            database,
            2,
            {
                {102, 1},
                {999, 1}
            }
        );
    } catch (const std::exception& error) {
        std::cout << "Order rejected: " << error.what() << '\n';
    }

    const int stockAfter = database.productStock(102);

    std::cout
        << "Stock before failed transaction: " << stockBefore << '\n'
        << "Stock after failed transaction:  " << stockAfter << '\n'
        << "Atomic rollback preserved stock: "
        << std::boolalpha
        << (stockBefore == stockAfter)
        << '\n';
}

int main() {
    try {
        RepositoryDatabase database;
        seed(database);

        std::cout << "DATABASE FUNDAMENTALS CASE STUDY\n";
        std::cout << "Customers: " << database.customerCount() << '\n';
        std::cout << "Products:  " << database.productCount() << '\n';

        database.printProductsWithCategories();

        const int orderId = createOrder(
            database,
            1,
            {
                {101, 1},
                {301, 2}
            }
        );

        std::cout << "\nCreated order " << orderId << ".\n";

        database.printCustomerOrders(1);
        database.printOrderDetails(orderId);
        database.printCategoryInventory();

        demonstrateConstraints(database);
        demonstrateRollback(database);

        std::cout << "\nRELATIONSHIP MODEL\n";
        std::cout
            << "customers 1 --- many orders\n"
            << "categories 1 --- many products\n"
            << "orders 1 --- many orderItems\n"
            << "products 1 --- many orderItems\n"
            << "orders many --- many products through orderItems\n";

        std::cout
            << "\nThe model demonstrates why primary keys identify rows, "
            << "foreign keys connect rows across tables, and junction "
            << "tables represent many-to-many relationships.\n";
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal database case-study error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
