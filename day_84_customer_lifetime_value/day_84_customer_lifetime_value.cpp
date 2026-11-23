#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

class ValidationError : public runtime_error {
public:
    explicit ValidationError(const string& message)
        : runtime_error(message) {}
};

enum class Segment {
    HighValue,
    Growing,
    Standard,
    LowValue,
    Unprofitable
};

enum class ReviewStatus {
    Valid,
    InsufficientData,
    NegativeValue
};

struct Transaction {
    string id;
    double revenue;
    double variableCost;
    double marketingCost;

    Transaction(
        string transactionId,
        double transactionRevenue,
        double cost,
        double acquisitionCost = 0.0
    )
        : id(move(transactionId)),
          revenue(transactionRevenue),
          variableCost(cost),
          marketingCost(acquisitionCost) {

        if (id.empty()) {
            throw ValidationError("Transaction ID is required.");
        }

        if (
            !isfinite(revenue) ||
            !isfinite(variableCost) ||
            !isfinite(marketingCost) ||
            revenue < 0 ||
            variableCost < 0 ||
            marketingCost < 0
        ) {
            throw ValidationError("Invalid transaction amounts.");
        }

        if (variableCost > revenue) {
            throw ValidationError(
                "Variable cost cannot exceed revenue."
            );
        }
    }

    double contribution() const {
        return revenue - variableCost;
    }
};

class Customer {
private:
    string id;
    string acquisitionChannel;
    vector<Transaction> transactions;
    set<string> transactionIds;

public:
    Customer(string customerId, string channel)
        : id(move(customerId)),
          acquisitionChannel(move(channel)) {

        if (id.empty() || acquisitionChannel.empty()) {
            throw ValidationError(
                "Customer ID and acquisition channel are required."
            );
        }
    }

    void addTransaction(const Transaction& transaction) {
        if (transactionIds.count(transaction.id)) {
            throw ValidationError("Duplicate transaction.");
        }

        transactions.push_back(transaction);
        transactionIds.insert(transaction.id);
    }

    const string& getId() const {
        return id;
    }

    const string& getChannel() const {
        return acquisitionChannel;
    }

    const vector<Transaction>& getTransactions() const {
        return transactions;
    }

    double revenue() const {
        double total = 0.0;

        for (const auto& transaction : transactions) {
            total += transaction.revenue;
        }

        return total;
    }

    double contribution() const {
        double total = 0.0;

        for (const auto& transaction : transactions) {
            total += transaction.contribution();
        }

        return total;
    }

    double acquisitionCost() const {
        double total = 0.0;

        for (const auto& transaction : transactions) {
            total += transaction.marketingCost;
        }

        return total;
    }

    double averageOrderValue() const {
        if (transactions.empty()) return 0.0;

        return revenue() / transactions.size();
    }

    double annualPurchaseFrequency() const {
        if (transactions.size() < 2) return 0.0;

        // The input records are assumed to represent an ordered
        // observation period measured in years.
        double observationYears =
            static_cast<double>(transactions.size() - 1);

        return transactions.size() / observationYears;
    }

    size_t orderCount() const {
        return transactions.size();
    }
};

struct CLVPolicy {
    double annualChurnRate = 0.20;
    double discountRate = 0.10;
    double defaultMargin = 0.60;
    double maximumLifetime = 10.0;

    void validate() const {
        if (
            annualChurnRate <= 0 ||
            annualChurnRate > 1 ||
            discountRate < 0 ||
            discountRate >= 1 ||
            defaultMargin < 0 ||
            defaultMargin > 1 ||
            maximumLifetime <= 0
        ) {
            throw ValidationError("Invalid CLV policy.");
        }
    }
};

struct Valuation {
    string customerId;
    double historicalRevenue;
    double contribution;
    double acquisitionCost;
    double margin;
    double projectedCLV;
    double netCLV;
    double expectedLifetime;
    Segment segment;
    ReviewStatus reviewStatus;
};

class CLVEngine {
private:
    CLVPolicy policy;

    Segment classify(double value) const {
        if (value < 0) return Segment::Unprofitable;
        if (value >= 10000) return Segment::HighValue;
        if (value >= 5000) return Segment::Growing;
        if (value >= 1000) return Segment::Standard;
        return Segment::LowValue;
    }

public:
    explicit CLVEngine(const CLVPolicy& configuration)
        : policy(configuration) {
        policy.validate();
    }

    Valuation calculate(const Customer& customer) const {
        const double revenue = customer.revenue();
        const double contribution = customer.contribution();
        const double acquisition = customer.acquisitionCost();

        const double margin =
            revenue > 0
                ? contribution / revenue
                : policy.defaultMargin;

        const double annualRevenue =
            customer.averageOrderValue() *
            customer.annualPurchaseFrequency();

        const double annualContribution =
            annualRevenue * margin;

        const double lifetime = min(
            policy.maximumLifetime,
            1.0 / policy.annualChurnRate
        );

        double projected;

        if (policy.discountRate == 0) {
            projected = annualContribution * lifetime;
        } else {
            projected =
                annualContribution *
                (
                    1.0 -
                    pow(
                        1.0 + policy.discountRate,
                        -lifetime
                    )
                ) /
                policy.discountRate;
        }

        const double netCLV = projected - acquisition;

        return {
            customer.getId(),
            revenue,
            contribution,
            acquisition,
            margin,
            projected,
            netCLV,
            lifetime,
            classify(netCLV),
            customer.orderCount() >= 2
                ? ReviewStatus::Valid
                : ReviewStatus::InsufficientData
        };
    }
};

string segmentName(Segment segment) {
    switch (segment) {
        case Segment::HighValue: return "HIGH_VALUE";
        case Segment::Growing: return "GROWING";
        case Segment::Standard: return "STANDARD";
        case Segment::LowValue: return "LOW_VALUE";
        case Segment::Unprofitable: return "UNPROFITABLE";
    }

    return "UNKNOWN";
}

struct CampaignDecision {
    string customerId;
    vector<string> actions;
};

class StrategicDecisionEngine {
public:
    CampaignDecision evaluate(
        const Valuation& valuation,
        double churnRisk
    ) const {

        if (
            !isfinite(churnRisk) ||
            churnRisk < 0 ||
            churnRisk > 1
        ) {
            throw ValidationError("Invalid churn probability.");
        }

        CampaignDecision decision;
        decision.customerId = valuation.customerId;

        if (valuation.netCLV < 0) {
            decision.actions.push_back(
                "Reduce acquisition cost and review pricing."
            );
        } else if (valuation.segment == Segment::HighValue) {
            decision.actions.push_back(
                "Provide premium loyalty benefits."
            );
        } else if (valuation.segment == Segment::Growing) {
            decision.actions.push_back(
                "Offer relevant cross-selling."
            );
        } else {
            decision.actions.push_back(
                "Improve repeat purchase frequency."
            );
        }

        if (churnRisk >= 0.70) {
            decision.actions.push_back(
                "Launch urgent retention intervention."
            );
        } else if (churnRisk >= 0.40) {
            decision.actions.push_back(
                "Increase engagement monitoring."
            );
        }

        if (
            valuation.reviewStatus ==
            ReviewStatus::InsufficientData
        ) {
            decision.actions.push_back(
                "Collect more behavioral observations."
            );
        }

        return decision;
    }
};

struct ChannelMetrics {
    size_t customers = 0;
    double totalCLV = 0.0;
    double totalAcquisitionCost = 0.0;

    double averageCLV() const {
        return customers
            ? totalCLV / customers
            : 0.0;
    }
};

class Portfolio {
private:
    map<string, Customer> customers;

public:
    void addCustomer(Customer customer) {
        const string id = customer.getId();

        if (customers.count(id)) {
            throw ValidationError("Duplicate customer.");
        }

        customers.emplace(id, move(customer));
    }

    vector<Valuation> evaluate(
        const CLVEngine& engine
    ) const {
        vector<Valuation> results;

        for (const auto& entry : customers) {
            results.push_back(engine.calculate(entry.second));
        }

        return results;
    }

    map<string, ChannelMetrics> analyzeChannels(
        const CLVEngine& engine
    ) const {
        map<string, ChannelMetrics> report;

        for (const auto& entry : customers) {
            const Customer& customer = entry.second;
            const Valuation valuation = engine.calculate(customer);

            auto& metrics = report[customer.getChannel()];

            metrics.customers++;
            metrics.totalCLV += valuation.netCLV;
            metrics.totalAcquisitionCost +=
                valuation.acquisitionCost;
        }

        return report;
    }
};

struct AcquisitionEconomics {
    double marketingSpend;
    size_t acquiredCustomers;
    double averageCLV;

    double cac() const {
        if (
            !isfinite(marketingSpend) ||
            marketingSpend < 0 ||
            acquiredCustomers == 0
        ) {
            throw ValidationError(
                "Invalid acquisition economics."
            );
        }

        return marketingSpend / acquiredCustomers;
    }

    double clvToCac() const {
        if (!isfinite(averageCLV) || averageCLV < 0) {
            throw ValidationError("Invalid average CLV.");
        }

        const double cost = cac();

        if (cost == 0) {
            return numeric_limits<double>::infinity();
        }

        return averageCLV / cost;
    }
};

void runTests() {
    CLVPolicy policy;
    CLVEngine engine(policy);

    Customer customer("TEST", "organic");

    customer.addTransaction(
        Transaction("T1", 1000, 400, 200)
    );

    customer.addTransaction(
        Transaction("T2", 2000, 800)
    );

    Valuation result = engine.calculate(customer);

    if (result.historicalRevenue != 3000) {
        throw runtime_error("Revenue test failed.");
    }

    if (result.contribution != 1800) {
        throw runtime_error("Contribution test failed.");
    }

    if (result.netCLV <= 0) {
        throw runtime_error("CLV test failed.");
    }

    bool duplicateRejected = false;

    try {
        customer.addTransaction(
            Transaction("T1", 100, 20)
        );
    } catch (const ValidationError&) {
        duplicateRejected = true;
    }

    if (!duplicateRejected) {
        throw runtime_error("Duplicate transaction test failed.");
    }

    cout << "All C++ tests passed.\n";
}

int main() {
    try {
        CLVPolicy policy;
        policy.annualChurnRate = 0.20;
        policy.discountRate = 0.10;
        policy.defaultMargin = 0.60;
        policy.maximumLifetime = 10;

        CLVEngine engine(policy);
        Portfolio portfolio;

        Customer c1("C001", "organic");
        c1.addTransaction(Transaction("T001", 5000, 1800, 500));
        c1.addTransaction(Transaction("T002", 6500, 2200));
        c1.addTransaction(Transaction("T003", 7000, 2500));
        c1.addTransaction(Transaction("T004", 8000, 2800));

        Customer c2("C002", "paid_search");
        c2.addTransaction(Transaction("T005", 1500, 900, 2000));
        c2.addTransaction(Transaction("T006", 1800, 1000));
        c2.addTransaction(Transaction("T007", 2000, 1100));

        Customer c3("C003", "referral");
        c3.addTransaction(Transaction("T008", 3000, 1200, 300));
        c3.addTransaction(Transaction("T009", 4000, 1500));
        c3.addTransaction(Transaction("T010", 5000, 1800));

        Customer c4("C004", "paid_social");
        c4.addTransaction(Transaction("T011", 700, 500, 2500));
        c4.addTransaction(Transaction("T012", 800, 600));

        portfolio.addCustomer(move(c1));
        portfolio.addCustomer(move(c2));
        portfolio.addCustomer(move(c3));
        portfolio.addCustomer(move(c4));

        StrategicDecisionEngine strategy;

        cout << fixed << setprecision(2);
        cout << "\nCUSTOMER LIFETIME VALUE REPORT\n";

        for (const auto& valuation : portfolio.evaluate(engine)) {
            cout
                << "\nCustomer: " << valuation.customerId
                << "\nRevenue: " << valuation.historicalRevenue
                << "\nContribution: " << valuation.contribution
                << "\nProjected CLV: " << valuation.projectedCLV
                << "\nNet CLV: " << valuation.netCLV
                << "\nSegment: " << segmentName(valuation.segment)
                << "\n";

            CampaignDecision decision =
                strategy.evaluate(valuation, 0.65);

            for (const auto& action : decision.actions) {
                cout << "  Action: " << action << "\n";
            }
        }

        cout << "\nCHANNEL PERFORMANCE\n";

        for (const auto& entry : portfolio.analyzeChannels(engine)) {
            cout
                << entry.first
                << " | Customers: " << entry.second.customers
                << " | Average CLV: " << entry.second.averageCLV()
                << "\n";
        }

        AcquisitionEconomics economics{
            50000,
            100,
            6000
        };

        cout << "\nACQUISITION ECONOMICS\n";
        cout << "CAC: " << economics.cac() << "\n";
        cout << "CLV/CAC: " << economics.clvToCac() << "\n";

        runTests();

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
