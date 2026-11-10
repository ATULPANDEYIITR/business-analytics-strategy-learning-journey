import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/*
 * FINANCIAL STATEMENTS AND ENTERPRISE REPORTING
 *
 * Java 17
 *
 * Domain architecture:
 * Account -> JournalEntry -> Ledger -> Financial Statements
 *
 * Implements:
 * - Immutable account and journal models
 * - Double-entry accounting
 * - Financial reporting services
 * - Indirect cash flow
 * - Approval-ready accounting validation
 * - Financial ratios
 * - Error handling
 * - Automated tests
 *
 * Monetary calculations use BigDecimal.
 */

public class FinancialStatements {

    private static final BigDecimal ZERO = new BigDecimal("0.00");

    private static BigDecimal amount(String value) {
        return new BigDecimal(value).setScale(
            2, RoundingMode.HALF_UP
        );
    }

    enum AccountType {
        ASSET,
        LIABILITY,
        EQUITY,
        REVENUE,
        EXPENSE,
        CONTRA_ASSET
    }

    enum JournalSide {
        DEBIT,
        CREDIT
    }

    enum StatementStatus {
        VALID,
        INVALID
    }

    record Account(
        String code,
        String name,
        AccountType type
    ) {
        Account {
            if (code == null || code.isBlank() ||
                name == null || name.isBlank() || type == null) {
                throw new IllegalArgumentException(
                    "Invalid account definition."
                );
            }
        }
    }

    record JournalLine(
        String accountCode,
        JournalSide side,
        BigDecimal amount
    ) {
        JournalLine {
            if (accountCode == null || accountCode.isBlank() ||
                side == null || amount == null ||
                amount.compareTo(ZERO) <= 0) {
                throw new IllegalArgumentException(
                    "Invalid journal line."
                );
            }
        }
    }

    record JournalEntry(
        String id,
        String description,
        List<JournalLine> lines
    ) {
        JournalEntry {
            if (id == null || id.isBlank() ||
                description == null || description.isBlank() ||
                lines == null || lines.isEmpty()) {
                throw new IllegalArgumentException(
                    "Invalid journal entry."
                );
            }

            lines = List.copyOf(lines);
        }
    }

    record IncomeStatement(
        BigDecimal revenue,
        BigDecimal cogs,
        BigDecimal grossProfit,
        BigDecimal operatingExpenses,
        BigDecimal depreciation,
        BigDecimal operatingIncome,
        BigDecimal interest,
        BigDecimal pretaxIncome,
        BigDecimal tax,
        BigDecimal netIncome
    ) {}

    record BalanceSheet(
        BigDecimal cash,
        BigDecimal receivables,
        BigDecimal inventory,
        BigDecimal currentAssets,
        BigDecimal equipment,
        BigDecimal accumulatedDepreciation,
        BigDecimal netFixedAssets,
        BigDecimal totalAssets,
        BigDecimal payables,
        BigDecimal taxPayable,
        BigDecimal debt,
        BigDecimal totalLiabilities,
        BigDecimal capital,
        BigDecimal retainedEarnings,
        BigDecimal totalEquity,
        BigDecimal liabilitiesAndEquity
    ) {}

    record CashFlowStatement(
        BigDecimal operating,
        BigDecimal investing,
        BigDecimal financing,
        BigDecimal openingCash,
        BigDecimal netChange,
        BigDecimal closingCash
    ) {}

    record FinancialReport(
        IncomeStatement income,
        BalanceSheet balance,
        CashFlowStatement cashFlow,
        Map<String, BigDecimal> ratios,
        StatementStatus status
    ) {}

    static class AccountingException extends RuntimeException {
        AccountingException(String message) {
            super(message);
        }
    }

    static class ChartOfAccounts {
        private final Map<String, Account> accounts = new HashMap<>();

        void register(Account account) {
            if (accounts.putIfAbsent(account.code(), account) != null) {
                throw new AccountingException(
                    "Duplicate account: " + account.code()
                );
            }
        }

        Account get(String code) {
            Account account = accounts.get(code);

            if (account == null) {
                throw new AccountingException(
                    "Unknown account: " + code
                );
            }

            return account;
        }

        boolean contains(String code) {
            return accounts.containsKey(code);
        }

        Map<String, Account> all() {
            return Collections.unmodifiableMap(accounts);
        }
    }

    static class JournalService {
        private final ChartOfAccounts chart;
        private final List<JournalEntry> entries = new ArrayList<>();
        private final Set<String> ids = new HashSet<>();

        JournalService(ChartOfAccounts chart) {
            this.chart = chart;
        }

        void post(JournalEntry entry) {
            if (ids.contains(entry.id())) {
                throw new AccountingException(
                    "Duplicate journal entry."
                );
            }

            BigDecimal debit = ZERO;
            BigDecimal credit = ZERO;

            for (JournalLine line : entry.lines()) {
                chart.get(line.accountCode());

                if (line.side() == JournalSide.DEBIT) {
                    debit = debit.add(line.amount());
                } else {
                    credit = credit.add(line.amount());
                }
            }

            if (debit.compareTo(credit) != 0) {
                throw new AccountingException(
                    "Journal entry is not balanced."
                );
            }

            // State is changed only after every validation succeeds.
            entries.add(entry);
            ids.add(entry.id());
        }

        List<JournalEntry> entries() {
            return List.copyOf(entries);
        }
    }

    static class LedgerService {
        private final ChartOfAccounts chart;

        LedgerService(ChartOfAccounts chart) {
            this.chart = chart;
        }

        Map<String, BigDecimal> calculate(
            List<JournalEntry> entries
        ) {
            Map<String, BigDecimal> balances = new HashMap<>();

            for (String code : chart.all().keySet()) {
                balances.put(code, ZERO);
            }

            for (JournalEntry entry : entries) {
                for (JournalLine line : entry.lines()) {
                    Account account = chart.get(line.accountCode());

                    boolean debitNormal =
                        account.type() == AccountType.ASSET ||
                        account.type() == AccountType.EXPENSE ||
                        account.type() == AccountType.CONTRA_ASSET;

                    BigDecimal movement;

                    if (debitNormal) {
                        movement = line.side() == JournalSide.DEBIT
                            ? line.amount()
                            : line.amount().negate();
                    } else {
                        movement = line.side() == JournalSide.CREDIT
                            ? line.amount()
                            : line.amount().negate();
                    }

                    balances.merge(
                        line.accountCode(),
                        movement,
                        BigDecimal::add
                    );
                }
            }

            return Collections.unmodifiableMap(balances);
        }
    }

    static class ReportingService {
        private final Map<String, BigDecimal> ledger;

        ReportingService(Map<String, BigDecimal> ledger) {
            this.ledger = ledger;
        }

        private BigDecimal get(String code) {
            BigDecimal result = ledger.get(code);

            if (result == null) {
                throw new AccountingException(
                    "Missing ledger balance: " + code
                );
            }

            return result;
        }

        IncomeStatement incomeStatement() {
            BigDecimal revenue = get("4000");
            BigDecimal cogs = get("5000");
            BigDecimal operatingExpenses = get("5100");
            BigDecimal depreciation = get("5200");
            BigDecimal interest = get("5300");
            BigDecimal tax = get("5400");

            BigDecimal grossProfit = revenue.subtract(cogs);

            BigDecimal operatingIncome = grossProfit
                .subtract(operatingExpenses)
                .subtract(depreciation);

            BigDecimal pretaxIncome = operatingIncome.subtract(interest);
            BigDecimal netIncome = pretaxIncome.subtract(tax);

            return new IncomeStatement(
                revenue,
                cogs,
                grossProfit,
                operatingExpenses,
                depreciation,
                operatingIncome,
                interest,
                pretaxIncome,
                tax,
                netIncome
            );
        }

        BalanceSheet balanceSheet(IncomeStatement income) {
            BigDecimal cash = get("1000");
            BigDecimal receivables = get("1100");
            BigDecimal inventory = get("1200");
            BigDecimal equipment = get("1500");
            BigDecimal accumulatedDepreciation = get("1590");

            BigDecimal currentAssets = cash
                .add(receivables)
                .add(inventory);

            BigDecimal netFixedAssets = equipment
                .subtract(accumulatedDepreciation);

            BigDecimal totalAssets = currentAssets.add(netFixedAssets);

            BigDecimal payables = get("2000");
            BigDecimal taxPayable = get("2100");
            BigDecimal debt = get("2500");

            BigDecimal totalLiabilities = payables
                .add(taxPayable)
                .add(debt);

            BigDecimal capital = get("3000");
            BigDecimal dividends = get("3100");

            BigDecimal retainedEarnings =
                income.netIncome().subtract(dividends);

            BigDecimal totalEquity = capital.add(retainedEarnings);

            BigDecimal liabilitiesAndEquity =
                totalLiabilities.add(totalEquity);

            return new BalanceSheet(
                cash,
                receivables,
                inventory,
                currentAssets,
                equipment,
                accumulatedDepreciation,
                netFixedAssets,
                totalAssets,
                payables,
                taxPayable,
                debt,
                totalLiabilities,
                capital,
                retainedEarnings,
                totalEquity,
                liabilitiesAndEquity
            );
        }

        CashFlowStatement cashFlowStatement(
            IncomeStatement income,
            BalanceSheet balance
        ) {
            BigDecimal operating = income.netIncome()
                .add(balance.accumulatedDepreciation())
                .subtract(balance.receivables())
                .subtract(balance.inventory())
                .add(balance.payables())
                .add(balance.taxPayable());

            BigDecimal investing = balance.equipment().negate();

            BigDecimal dividends = income.netIncome()
                .subtract(balance.retainedEarnings());

            BigDecimal financing = balance.capital()
                .add(balance.debt())
                .subtract(dividends);

            BigDecimal netChange = operating
                .add(investing)
                .add(financing);

            return new CashFlowStatement(
                operating,
                investing,
                financing,
                ZERO,
                netChange,
                balance.cash()
            );
        }

        private BigDecimal ratio(
            BigDecimal numerator,
            BigDecimal denominator
        ) {
            if (denominator.compareTo(ZERO) == 0) {
                return ZERO;
            }

            return numerator.divide(
                denominator,
                4,
                RoundingMode.HALF_UP
            );
        }

        Map<String, BigDecimal> calculateRatios(
            IncomeStatement income,
            BalanceSheet balance
        ) {
            Map<String, BigDecimal> ratios = new HashMap<>();

            BigDecimal currentLiabilities = balance.payables()
                .add(balance.taxPayable());

            ratios.put(
                "current_ratio",
                ratio(balance.currentAssets(), currentLiabilities)
            );

            ratios.put(
                "debt_to_equity",
                ratio(balance.totalLiabilities(), balance.totalEquity())
            );

            ratios.put(
                "gross_profit_margin",
                ratio(income.grossProfit(), income.revenue())
                    .multiply(amount("100"))
            );

            ratios.put(
                "net_profit_margin",
                ratio(income.netIncome(), income.revenue())
                    .multiply(amount("100"))
            );

            ratios.put(
                "return_on_assets",
                ratio(income.netIncome(), balance.totalAssets())
                    .multiply(amount("100"))
            );

            return Collections.unmodifiableMap(ratios);
        }

        FinancialReport generate() {
            IncomeStatement income = incomeStatement();
            BalanceSheet balance = balanceSheet(income);

            CashFlowStatement cashFlow =
                cashFlowStatement(income, balance);

            if (balance.totalAssets().compareTo(
                    balance.liabilitiesAndEquity()) != 0) {
                throw new AccountingException(
                    "Balance sheet does not balance."
                );
            }

            if (cashFlow.netChange().compareTo(balance.cash()) != 0) {
                throw new AccountingException(
                    "Cash flow reconciliation failed."
                );
            }

            return new FinancialReport(
                income,
                balance,
                cashFlow,
                calculateRatios(income, balance),
                StatementStatus.VALID
            );
        }
    }

    static JournalLine debit(String account, String value) {
        return new JournalLine(
            account, JournalSide.DEBIT, amount(value)
        );
    }

    static JournalLine credit(String account, String value) {
        return new JournalLine(
            account, JournalSide.CREDIT, amount(value)
        );
    }

    static JournalEntry entry(
        String id,
        String description,
        JournalLine... lines
    ) {
        return new JournalEntry(
            id, description, List.of(lines)
        );
    }

    static void initializeAccounts(ChartOfAccounts chart) {
        List<Account> accounts = List.of(
            new Account("1000", "Cash and Bank", AccountType.ASSET),
            new Account("1100", "Accounts Receivable", AccountType.ASSET),
            new Account("1200", "Inventory", AccountType.ASSET),
            new Account("1500", "Equipment", AccountType.ASSET),
            new Account("1590", "Accumulated Depreciation", AccountType.CONTRA_ASSET),
            new Account("2000", "Accounts Payable", AccountType.LIABILITY),
            new Account("2100", "Tax Payable", AccountType.LIABILITY),
            new Account("2500", "Long-Term Loan", AccountType.LIABILITY),
            new Account("3000", "Share Capital", AccountType.EQUITY),
            new Account("3100", "Dividends", AccountType.EQUITY),
            new Account("4000", "Sales Revenue", AccountType.REVENUE),
            new Account("5000", "Cost of Goods Sold", AccountType.EXPENSE),
            new Account("5100", "Operating Expenses", AccountType.EXPENSE),
            new Account("5200", "Depreciation Expense", AccountType.EXPENSE),
            new Account("5300", "Interest Expense", AccountType.EXPENSE),
            new Account("5400", "Income Tax Expense", AccountType.EXPENSE)
        );

        accounts.forEach(chart::register);
    }

    static void loadTransactions(JournalService service) {
        List<JournalEntry> entries = List.of(
            entry("JE001", "Share capital",
                debit("1000", "100000"), credit("3000", "100000")),

            entry("JE002", "Cash sales",
                debit("1000", "120000"), credit("4000", "120000")),

            entry("JE003", "Credit sales",
                debit("1100", "30000"), credit("4000", "30000")),

            entry("JE004", "Inventory on credit",
                debit("1200", "40000"), credit("2000", "40000")),

            entry("JE005", "Cash inventory purchase",
                debit("1200", "25000"), credit("1000", "25000")),

            entry("JE006", "Cost of goods sold",
                debit("5000", "60000"), credit("1200", "60000")),

            entry("JE007", "Operating expenses",
                debit("5100", "25000"), credit("1000", "25000")),

            entry("JE008", "Equipment purchase",
                debit("1500", "50000"), credit("1000", "50000")),

            entry("JE009", "Depreciation",
                debit("5200", "5000"), credit("1590", "5000")),

            entry("JE010", "Interest payment",
                debit("5300", "2000"), credit("1000", "2000")),

            entry("JE011", "Tax provision",
                debit("5400", "8000"), credit("2100", "8000")),

            entry("JE012", "Customer collection",
                debit("1000", "20000"), credit("1100", "20000")),

            entry("JE013", "Supplier payment",
                debit("2000", "15000"), credit("1000", "15000")),

            entry("JE014", "Loan receipt",
                debit("1000", "30000"), credit("2500", "30000")),

            entry("JE015", "Dividend distribution",
                debit("3100", "5000"), credit("1000", "5000"))
        );

        entries.forEach(service::post);
    }

    static void display(FinancialReport report) {
        System.out.println("\nINCOME STATEMENT");
        System.out.println(report.income());

        System.out.println("\nBALANCE SHEET");
        System.out.println(report.balance());

        System.out.println("\nCASH FLOW STATEMENT");
        System.out.println(report.cashFlow());

        System.out.println("\nFINANCIAL RATIOS");

        report.ratios().forEach(
            (name, value) -> System.out.println(name + ": " + value)
        );
    }

    static void test(FinancialReport report, JournalService journal) {
        if (report.income().revenue().compareTo(amount("150000")) != 0 ||
            report.income().netIncome().compareTo(amount("50000")) != 0 ||
            report.balance().totalAssets().compareTo(amount("208000")) != 0 ||
            report.balance().totalLiabilities().compareTo(amount("63000")) != 0 ||
            report.balance().totalEquity().compareTo(amount("145000")) != 0 ||
            report.cashFlow().operating().compareTo(amount("73000")) != 0 ||
            report.cashFlow().closingCash().compareTo(amount("148000")) != 0) {
            throw new AssertionError("Financial statement test failed.");
        }

        try {
            journal.post(entry(
                "INVALID",
                "Unbalanced journal",
                debit("1000", "100"),
                credit("4000", "50")
            ));

            throw new AssertionError("Unbalanced entry was accepted.");
        } catch (AccountingException expected) {
            System.out.println("Unbalanced journal correctly rejected.");
        }

        System.out.println("All accounting tests passed.");
    }

    public static void main(String[] args) {
        try {
            ChartOfAccounts chart = new ChartOfAccounts();
            initializeAccounts(chart);

            JournalService journal = new JournalService(chart);
            loadTransactions(journal);

            LedgerService ledgerService = new LedgerService(chart);

            Map<String, BigDecimal> ledger =
                ledgerService.calculate(journal.entries());

            ReportingService reporting = new ReportingService(ledger);

            FinancialReport report = reporting.generate();

            System.out.println(
                "COMPANY: Apex Manufacturing Private Limited"
            );

            System.out.println(
                "POSTED ENTRIES: " + journal.entries().size()
            );

            display(report);
            test(report, journal);

        } catch (Exception error) {
            System.err.println(
                "Financial reporting failed: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
