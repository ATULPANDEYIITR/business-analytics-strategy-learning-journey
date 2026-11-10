#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * FINANCIAL STATEMENTS AND REPORTING ENGINE
 *
 * C++17
 *
 * Implements:
 * - Account classification
 * - Double-entry journal processing
 * - Ledger balances
 * - Income statement
 * - Balance sheet
 * - Indirect cash flow statement
 * - Financial ratios
 * - Accounting equation enforcement
 * - Transaction validation
 *
 * Monetary values are represented as integer paise/cents to
 * avoid floating-point accounting errors.
 */

using Amount = long long;

enum class AccountType {
    Asset,
    Liability,
    Equity,
    Revenue,
    Expense,
    ContraAsset
};

struct Account {
    string code;
    string name;
    AccountType type;
};

struct JournalLine {
    string accountCode;
    Amount debit = 0;
    Amount credit = 0;
};

struct JournalEntry {
    string id;
    string description;
    vector<JournalLine> lines;
};

struct IncomeStatement {
    Amount revenue = 0;
    Amount cogs = 0;
    Amount grossProfit = 0;
    Amount operatingExpenses = 0;
    Amount depreciation = 0;
    Amount operatingIncome = 0;
    Amount interest = 0;
    Amount pretaxIncome = 0;
    Amount tax = 0;
    Amount netIncome = 0;
};

struct BalanceSheet {
    Amount cash = 0;
    Amount receivables = 0;
    Amount inventory = 0;
    Amount currentAssets = 0;
    Amount equipment = 0;
    Amount accumulatedDepreciation = 0;
    Amount netFixedAssets = 0;
    Amount totalAssets = 0;
    Amount payables = 0;
    Amount taxPayable = 0;
    Amount debt = 0;
    Amount totalLiabilities = 0;
    Amount capital = 0;
    Amount retainedEarnings = 0;
    Amount totalEquity = 0;
    Amount liabilitiesAndEquity = 0;
};

struct CashFlowStatement {
    Amount operating = 0;
    Amount investing = 0;
    Amount financing = 0;
    Amount netChange = 0;
    Amount openingCash = 0;
    Amount closingCash = 0;
};

class AccountingEngine {
private:
    string companyName;
    map<string, Account> accounts;
    vector<JournalEntry> entries;
    set<string> entryIds;

    static bool isDebitNormal(AccountType type) {
        return type == AccountType::Asset ||
               type == AccountType::Expense ||
               type == AccountType::ContraAsset;
    }

    static string formatMoney(Amount value) {
        bool negative = value < 0;
        if (negative) value = -value;

        long long units = value / 100;
        long long fraction = value % 100;

        string result = to_string(units);
        for (int i = static_cast<int>(result.size()) - 3;
             i > 0; i -= 3) {
            result.insert(i, ",");
        }

        result += "." + (fraction < 10 ? "0" : "") +
                  to_string(fraction);

        return negative ? "-" + result : result;
    }

    Amount balance(const map<string, Amount>& ledger,
                   const string& code) const {
        auto it = ledger.find(code);

        if (it == ledger.end()) {
            throw runtime_error("Missing ledger account: " + code);
        }

        return it->second;
    }

public:
    explicit AccountingEngine(string company)
        : companyName(move(company)) {
        if (companyName.empty()) {
            throw invalid_argument("Company name is required.");
        }
    }

    void addAccount(Account account) {
        if (account.code.empty() || account.name.empty()) {
            throw invalid_argument("Invalid account definition.");
        }

        if (accounts.count(account.code)) {
            throw invalid_argument("Duplicate account code.");
        }

        accounts.emplace(account.code, move(account));
    }

    void post(const JournalEntry& entry) {
        if (entry.id.empty() || entry.description.empty() ||
            entry.lines.empty()) {
            throw invalid_argument("Incomplete journal entry.");
        }

        if (entryIds.count(entry.id)) {
            throw invalid_argument("Duplicate journal entry.");
        }

        Amount debitTotal = 0;
        Amount creditTotal = 0;

        for (const auto& line : entry.lines) {
            if (!accounts.count(line.accountCode)) {
                throw invalid_argument("Unknown account: " +
                                       line.accountCode);
            }

            if (line.debit < 0 || line.credit < 0 ||
                (line.debit == 0 && line.credit == 0) ||
                (line.debit > 0 && line.credit > 0)) {
                throw invalid_argument("Invalid journal line.");
            }

            if (debitTotal > LLONG_MAX - line.debit ||
                creditTotal > LLONG_MAX - line.credit) {
                throw overflow_error("Journal total overflow.");
            }

            debitTotal += line.debit;
            creditTotal += line.credit;
        }

        if (debitTotal != creditTotal) {
            throw invalid_argument("Journal entry is unbalanced.");
        }

        // Atomic logical posting: validation precedes state mutation.
        entries.push_back(entry);
        entryIds.insert(entry.id);
    }

    map<string, Amount> buildLedger() const {
        map<string, Amount> ledger;

        for (const auto& [code, account] : accounts) {
            ledger[code] = 0;
        }

        for (const auto& entry : entries) {
            for (const auto& line : entry.lines) {
                const auto& account = accounts.at(line.accountCode);

                Amount movement = isDebitNormal(account.type)
                    ? line.debit - line.credit
                    : line.credit - line.debit;

                if ((movement > 0 &&
                     ledger[line.accountCode] > LLONG_MAX - movement) ||
                    (movement < 0 &&
                     ledger[line.accountCode] < LLONG_MIN - movement)) {
                    throw overflow_error("Ledger balance overflow.");
                }

                ledger[line.accountCode] += movement;
            }
        }

        return ledger;
    }

    IncomeStatement incomeStatement(
        const map<string, Amount>& ledger) const {

        IncomeStatement report;

        report.revenue = balance(ledger, "4000");
        report.cogs = balance(ledger, "5000");
        report.grossProfit = report.revenue - report.cogs;

        report.operatingExpenses = balance(ledger, "5100");
        report.depreciation = balance(ledger, "5200");

        report.operatingIncome =
            report.grossProfit -
            report.operatingExpenses -
            report.depreciation;

        report.interest = balance(ledger, "5300");
        report.pretaxIncome = report.operatingIncome - report.interest;
        report.tax = balance(ledger, "5400");
        report.netIncome = report.pretaxIncome - report.tax;

        return report;
    }

    BalanceSheet balanceSheet(
        const map<string, Amount>& ledger,
        const IncomeStatement& income) const {

        BalanceSheet report;

        report.cash = balance(ledger, "1000");
        report.receivables = balance(ledger, "1100");
        report.inventory = balance(ledger, "1200");

        report.currentAssets =
            report.cash + report.receivables + report.inventory;

        report.equipment = balance(ledger, "1500");
        report.accumulatedDepreciation = balance(ledger, "1590");

        report.netFixedAssets =
            report.equipment - report.accumulatedDepreciation;

        report.totalAssets =
            report.currentAssets + report.netFixedAssets;

        report.payables = balance(ledger, "2000");
        report.taxPayable = balance(ledger, "2100");
        report.debt = balance(ledger, "2500");

        report.totalLiabilities =
            report.payables + report.taxPayable + report.debt;

        report.capital = balance(ledger, "3000");
        Amount dividends = balance(ledger, "3100");

        report.retainedEarnings = income.netIncome - dividends;
        report.totalEquity = report.capital + report.retainedEarnings;

        report.liabilitiesAndEquity =
            report.totalLiabilities + report.totalEquity;

        if (report.totalAssets != report.liabilitiesAndEquity) {
            throw runtime_error("Accounting equation violated.");
        }

        return report;
    }

    CashFlowStatement cashFlowStatement(
        const IncomeStatement& income,
        const BalanceSheet& balance) const {

        CashFlowStatement report;

        report.operating =
            income.netIncome
            + balance.accumulatedDepreciation
            - balance.receivables
            - balance.inventory
            + balance.payables
            + balance.taxPayable;

        report.investing = -balance.equipment;

        report.financing =
            balance.capital + balance.debt -
            balance.retainedEarnings + income.netIncome -
            balance.capital - (income.netIncome - balance.retainedEarnings);

        // Financing cash flows are equity contributions, borrowings,
        // and distributions, not retained earnings.
        // Dividends are derived from net income and retained earnings.
        Amount dividends = income.netIncome - balance.retainedEarnings;

        report.financing =
            balance.capital + balance.debt - dividends;

        report.netChange =
            report.operating + report.investing + report.financing;

        report.openingCash = 0;
        report.closingCash = report.netChange;

        if (report.closingCash != balance.cash) {
            throw runtime_error("Cash flow reconciliation failed.");
        }

        return report;
    }

    void displayIncome(const IncomeStatement& r) const {
        cout << "\nINCOME STATEMENT\n";

        cout << "Revenue:             "
             << formatMoney(r.revenue) << '\n';
        cout << "Cost of goods sold:  "
             << formatMoney(r.cogs) << '\n';
        cout << "Gross profit:        "
             << formatMoney(r.grossProfit) << '\n';
        cout << "Operating expenses:  "
             << formatMoney(r.operatingExpenses) << '\n';
        cout << "Depreciation:        "
             << formatMoney(r.depreciation) << '\n';
        cout << "Operating income:    "
             << formatMoney(r.operatingIncome) << '\n';
        cout << "Interest:            "
             << formatMoney(r.interest) << '\n';
        cout << "Pretax income:       "
             << formatMoney(r.pretaxIncome) << '\n';
        cout << "Tax:                 "
             << formatMoney(r.tax) << '\n';
        cout << "Net income:          "
             << formatMoney(r.netIncome) << '\n';
    }

    void displayBalance(const BalanceSheet& r) const {
        cout << "\nBALANCE SHEET\n";

        cout << "Cash:                " << formatMoney(r.cash) << '\n';
        cout << "Receivables:         " << formatMoney(r.receivables) << '\n';
        cout << "Inventory:           " << formatMoney(r.inventory) << '\n';
        cout << "Current assets:      " << formatMoney(r.currentAssets) << '\n';
        cout << "Equipment:           " << formatMoney(r.equipment) << '\n';
        cout << "Accumulated dep.:    "
             << formatMoney(r.accumulatedDepreciation) << '\n';
        cout << "Net fixed assets:    " << formatMoney(r.netFixedAssets) << '\n';
        cout << "Total assets:        " << formatMoney(r.totalAssets) << '\n';
        cout << "Accounts payable:    " << formatMoney(r.payables) << '\n';
        cout << "Tax payable:         " << formatMoney(r.taxPayable) << '\n';
        cout << "Long-term debt:      " << formatMoney(r.debt) << '\n';
        cout << "Total liabilities:   "
             << formatMoney(r.totalLiabilities) << '\n';
        cout << "Share capital:       " << formatMoney(r.capital) << '\n';
        cout << "Retained earnings:   "
             << formatMoney(r.retainedEarnings) << '\n';
        cout << "Total equity:        " << formatMoney(r.totalEquity) << '\n';
        cout << "Liabilities + equity:"
             << formatMoney(r.liabilitiesAndEquity) << '\n';
    }

    void displayCashFlow(const CashFlowStatement& r) const {
        cout << "\nCASH FLOW STATEMENT\n";

        cout << "Operating activities: "
             << formatMoney(r.operating) << '\n';
        cout << "Investing activities: "
             << formatMoney(r.investing) << '\n';
        cout << "Financing activities: "
             << formatMoney(r.financing) << '\n';
        cout << "Net change in cash:   "
             << formatMoney(r.netChange) << '\n';
        cout << "Closing cash:         "
             << formatMoney(r.closingCash) << '\n';
    }

    void displayRatios(
        const IncomeStatement& income,
        const BalanceSheet& balance) const {

        cout << "\nFINANCIAL RATIOS\n";

        auto percentage = [](Amount numerator, Amount denominator) {
            return denominator == 0 ? 0.0 :
                static_cast<double>(numerator) /
                static_cast<double>(denominator) * 100.0;
        };

        Amount currentLiabilities =
            balance.payables + balance.taxPayable;

        cout << fixed << setprecision(2);

        cout << "Current ratio: "
             << (currentLiabilities == 0 ? 0.0 :
                 static_cast<double>(balance.currentAssets) /
                 currentLiabilities) << '\n';

        cout << "Debt to equity: "
             << (balance.totalEquity == 0 ? 0.0 :
                 static_cast<double>(balance.totalLiabilities) /
                 balance.totalEquity) << '\n';

        cout << "Gross margin: "
             << percentage(income.grossProfit, income.revenue) << "%\n";

        cout << "Net margin: "
             << percentage(income.netIncome, income.revenue) << "%\n";

        cout << "Return on assets: "
             << percentage(income.netIncome, balance.totalAssets) << "%\n";
    }

    size_t entryCount() const {
        return entries.size();
    }

    const string& company() const {
        return companyName;
    }
};

JournalLine debit(string account, Amount amount) {
    return {move(account), amount, 0};
}

JournalLine credit(string account, Amount amount) {
    return {move(account), 0, amount};
}

JournalEntry makeEntry(
    string id,
    string description,
    vector<JournalLine> lines) {

    return {move(id), move(description), move(lines)};
}

void addAccounts(AccountingEngine& engine) {
    const vector<Account> accounts = {
        {"1000", "Cash and Bank", AccountType::Asset},
        {"1100", "Accounts Receivable", AccountType::Asset},
        {"1200", "Inventory", AccountType::Asset},
        {"1500", "Equipment", AccountType::Asset},
        {"1590", "Accumulated Depreciation", AccountType::ContraAsset},
        {"2000", "Accounts Payable", AccountType::Liability},
        {"2100", "Tax Payable", AccountType::Liability},
        {"2500", "Long-Term Loan", AccountType::Liability},
        {"3000", "Share Capital", AccountType::Equity},
        {"3100", "Dividends", AccountType::Equity},
        {"4000", "Sales Revenue", AccountType::Revenue},
        {"5000", "Cost of Goods Sold", AccountType::Expense},
        {"5100", "Operating Expenses", AccountType::Expense},
        {"5200", "Depreciation Expense", AccountType::Expense},
        {"5300", "Interest Expense", AccountType::Expense},
        {"5400", "Income Tax Expense", AccountType::Expense}
    };

    for (const auto& account : accounts) {
        engine.addAccount(account);
    }
}

void loadTransactions(AccountingEngine& engine) {
    const vector<JournalEntry> transactions = {
        makeEntry("JE001", "Share capital",
            {debit("1000", 10000000), credit("3000", 10000000)}),

        makeEntry("JE002", "Cash sales",
            {debit("1000", 12000000), credit("4000", 12000000)}),

        makeEntry("JE003", "Credit sales",
            {debit("1100", 3000000), credit("4000", 3000000)}),

        makeEntry("JE004", "Inventory on credit",
            {debit("1200", 4000000), credit("2000", 4000000)}),

        makeEntry("JE005", "Cash inventory purchase",
            {debit("1200", 2500000), credit("1000", 2500000)}),

        makeEntry("JE006", "Cost of goods sold",
            {debit("5000", 6000000), credit("1200", 6000000)}),

        makeEntry("JE007", "Operating expenses",
            {debit("5100", 2500000), credit("1000", 2500000)}),

        makeEntry("JE008", "Equipment purchase",
            {debit("1500", 5000000), credit("1000", 5000000)}),

        makeEntry("JE009", "Depreciation",
            {debit("5200", 500000), credit("1590", 500000)}),

        makeEntry("JE010", "Interest",
            {debit("5300", 200000), credit("1000", 200000)}),

        makeEntry("JE011", "Tax provision",
            {debit("5400", 800000), credit("2100", 800000)}),

        makeEntry("JE012", "Customer collection",
            {debit("1000", 2000000), credit("1100", 2000000)}),

        makeEntry("JE013", "Supplier payment",
            {debit("2000", 1500000), credit("1000", 1500000)}),

        makeEntry("JE014", "Loan receipt",
            {debit("1000", 3000000), credit("2500", 3000000)}),

        makeEntry("JE015", "Dividend distribution",
            {debit("3100", 500000), credit("1000", 500000)})
    };

    for (const auto& transaction : transactions) {
        engine.post(transaction);
    }
}

void runTests(
    AccountingEngine& engine,
    const IncomeStatement& income,
    const BalanceSheet& balance,
    const CashFlowStatement& cashFlow) {

    if (income.revenue != 15000000 ||
        income.netIncome != 5000000 ||
        balance.totalAssets != 20800000 ||
        balance.totalLiabilities != 6300000 ||
        balance.totalEquity != 14500000 ||
        cashFlow.operating != 7300000 ||
        cashFlow.closingCash != 14800000) {
        throw runtime_error("Financial validation test failed.");
    }

    try {
        engine.post(makeEntry(
            "INVALID",
            "Unbalanced transaction",
            {debit("1000", 10000), credit("4000", 5000)}
        ));

        throw runtime_error("Invalid entry was accepted.");
    } catch (const invalid_argument&) {
        // Expected validation failure.
    }

    cout << "\nAll accounting tests passed.\n";
}

int main() {
    try {
        AccountingEngine engine(
            "Apex Manufacturing Private Limited"
        );

        addAccounts(engine);
        loadTransactions(engine);

        const auto ledger = engine.buildLedger();
        const auto income = engine.incomeStatement(ledger);
        const auto balance = engine.balanceSheet(ledger, income);
        const auto cashFlow = engine.cashFlowStatement(income, balance);

        cout << "COMPANY: " << engine.company() << '\n';
        cout << "JOURNAL ENTRIES: " << engine.entryCount() << '\n';

        engine.displayIncome(income);
        engine.displayBalance(balance);
        engine.displayCashFlow(cashFlow);
        engine.displayRatios(income, balance);

        runTests(engine, income, balance, cashFlow);

    } catch (const exception& error) {
        cerr << "Accounting error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
