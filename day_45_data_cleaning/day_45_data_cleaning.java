import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/**
 * Enterprise-oriented data quality model.
 *
 * The domain separates missingness, duplicate identity, and inconsistent
 * representation. Cleaning rules are encoded as services and policies rather
 * than scattered across output statements.
 */
public class DataCleaningEnterprise {

    enum CustomerStatus {
        ACTIVE,
        PENDING,
        INACTIVE
    }

    record CustomerTransaction(
            String customerId,
            String name,
            String email,
            String phone,
            String city,
            BigDecimal amount,
            String currency,
            CustomerStatus status,
            LocalDate signupDate
    ) {
        CustomerTransaction {
            if (customerId == null || customerId.isBlank()) {
                throw new IllegalArgumentException(
                        "customerId is required"
                );
            }

            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                        "name is required"
                );
            }
        }

        String businessKey() {
            return String.join(
                    "|",
                    customerId,
                    Objects.toString(name, "<NULL>"),
                    Objects.toString(email, "<NULL>"),
                    Objects.toString(phone, "<NULL>"),
                    Objects.toString(city, "<NULL>"),
                    Objects.toString(amount, "<NULL>"),
                    Objects.toString(currency, "<NULL>"),
                    Objects.toString(status, "<NULL>"),
                    Objects.toString(signupDate, "<NULL>")
            );
        }
    }

    record AuditEvent(
            String customerId,
            String field,
            String category,
            String action,
            String detail
    ) {}

    interface CleaningRule {
        CustomerTransaction apply(
                CustomerTransaction transaction,
                List<AuditEvent> audit
        );
    }

    static final class MissingValueRule implements CleaningRule {

        private static final Set<String> MISSING =
                Set.of("", "na", "n/a", "null", "none", "unknown", "-", "--");

        private String standardize(String value) {
            if (value == null) {
                return null;
            }

            String trimmed = value.trim();

            if (MISSING.contains(trimmed.toLowerCase())) {
                return null;
            }

            return trimmed;
        }

        @Override
        public CustomerTransaction apply(
                CustomerTransaction transaction,
                List<AuditEvent> audit
        ) {
            String email = standardize(transaction.email());
            String phone = standardize(transaction.phone());

            if (!Objects.equals(email, transaction.email())) {
                audit.add(new AuditEvent(
                        transaction.customerId(),
                        "email",
                        "missing",
                        "standardized",
                        "Missing representation converted to null"
                ));
            }

            if (!Objects.equals(phone, transaction.phone())) {
                audit.add(new AuditEvent(
                        transaction.customerId(),
                        "phone",
                        "missing",
                        "standardized",
                        "Missing representation converted to null"
                ));
            }

            return new CustomerTransaction(
                    transaction.customerId(),
                    transaction.name(),
                    email,
                    phone,
                    transaction.city(),
                    transaction.amount(),
                    transaction.currency(),
                    transaction.status(),
                    transaction.signupDate()
            );
        }
    }

    static final class ConsistencyRule implements CleaningRule {

        private String canonicalCity(String city) {
            if (city == null) {
                return null;
            }

            String value = city.trim().toLowerCase();

            return switch (value) {
                case "lucknow", "lko" -> "Lucknow";
                case "kanpur", "knp" -> "Kanpur";
                default -> city.trim();
            };
        }

        private String canonicalPhone(String phone) {
            if (phone == null) {
                return null;
            }

            String digits = phone.replaceAll("\\D", "");

            if (digits.isBlank()) {
                return null;
            }

            if (digits.length() == 10) {
                return "+91 "
                        + digits.substring(0, 5)
                        + " "
                        + digits.substring(5);
            }

            if (digits.length() == 12 &&
                    digits.startsWith("91")) {
                return "+91 "
                        + digits.substring(2, 7)
                        + " "
                        + digits.substring(7);
            }

            return "+" + digits;
        }

        private String canonicalCurrency(String currency) {
            if (currency == null) {
                return null;
            }

            String value = currency.trim().toUpperCase();

            return switch (value) {
                case "RS", "RS.", "₹", "RUPEE", "RUPEES" -> "INR";
                default -> value;
            };
        }

        private CustomerStatus canonicalStatus(String status) {
            if (status == null) {
                return null;
            }

            return switch (status.trim().toLowerCase()) {
                case "active", "act" -> CustomerStatus.ACTIVE;
                case "pending", "pend" -> CustomerStatus.PENDING;
                case "inactive", "in-active" -> CustomerStatus.INACTIVE;
                default -> throw new IllegalArgumentException(
                        "Unknown customer status: " + status
                );
            };
        }

        @Override
        public CustomerTransaction apply(
                CustomerTransaction transaction,
                List<AuditEvent> audit
        ) {
            String city = canonicalCity(transaction.city());
            String phone = canonicalPhone(transaction.phone());
            String currency = canonicalCurrency(transaction.currency());
            CustomerStatus status = canonicalStatus(
                    transaction.status().name()
            );

            if (!Objects.equals(city, transaction.city())) {
                audit.add(new AuditEvent(
                        transaction.customerId(),
                        "city",
                        "inconsistent",
                        "normalized",
                        transaction.city() + " -> " + city
                ));
            }

            if (!Objects.equals(phone, transaction.phone())) {
                audit.add(new AuditEvent(
                        transaction.customerId(),
                        "phone",
                        "inconsistent",
                        "normalized",
                        transaction.phone() + " -> " + phone
                ));
            }

            if (!Objects.equals(currency, transaction.currency())) {
                audit.add(new AuditEvent(
                        transaction.customerId(),
                        "currency",
                        "inconsistent",
                        "normalized",
                        transaction.currency() + " -> " + currency
                ));
            }

            return new CustomerTransaction(
                    transaction.customerId(),
                    transaction.name().trim(),
                    transaction.email() == null
                            ? null
                            : transaction.email().trim().toLowerCase(),
                    phone,
                    city,
                    transaction.amount(),
                    currency,
                    status,
                    transaction.signupDate()
            );
        }
    }

    static final class ValidationService {

        private static final Set<String> CURRENCIES =
                Set.of("INR", "USD", "EUR", "GBP");

        List<String> validate(CustomerTransaction transaction) {
            List<String> errors = new ArrayList<>();

            if (transaction.amount() != null &&
                    transaction.amount().signum() < 0) {
                errors.add("amount cannot be negative");
            }

            if (!CURRENCIES.contains(transaction.currency())) {
                errors.add("unsupported currency");
            }

            if (transaction.email() != null &&
                    !transaction.email().matches(
                            "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
                errors.add("invalid email structure");
            }

            if (transaction.phone() != null &&
                    !transaction.phone().matches(
                            "^\\+91 \\d{5} \\d{5}$")) {
                errors.add("phone is not in canonical format");
            }

            return errors;
        }
    }

    static final class DeduplicationService {

        List<CustomerTransaction> removeDuplicates(
                List<CustomerTransaction> transactions,
                List<AuditEvent> audit
        ) {
            Set<String> seen = new HashSet<>();
            List<CustomerTransaction> unique = new ArrayList<>();

            for (CustomerTransaction transaction : transactions) {
                if (!seen.add(transaction.businessKey())) {
                    audit.add(new AuditEvent(
                            transaction.customerId(),
                            "__record__",
                            "duplicate",
                            "removed",
                            "Business key already exists"
                    ));
                    continue;
                }

                unique.add(transaction);
            }

            return unique;
        }
    }

    static final class MedianImputationService {

        void fillMissingAmounts(
                List<CustomerTransaction> transactions,
                List<AuditEvent> audit
        ) {
            Map<String, List<BigDecimal>> cityAmounts = new HashMap<>();

            for (CustomerTransaction transaction : transactions) {
                if (transaction.amount() == null) {
                    continue;
                }

                cityAmounts
                        .computeIfAbsent(
                                transaction.city(),
                                ignored -> new ArrayList<>()
                        )
                        .add(transaction.amount());
            }

            Map<String, BigDecimal> medians = new HashMap<>();

            for (Map.Entry<String, List<BigDecimal>> entry :
                    cityAmounts.entrySet()) {

                List<BigDecimal> values = entry.getValue();

                values.sort(Comparator.naturalOrder());

                int middle = values.size() / 2;

                BigDecimal median;

                if (values.size() % 2 == 1) {
                    median = values.get(middle);
                } else {
                    median = values.get(middle - 1)
                            .add(values.get(middle))
                            .divide(
                                    BigDecimal.valueOf(2),
                                    2,
                                    RoundingMode.HALF_UP
                            );
                }

                medians.put(entry.getKey(), median);
            }

            for (int index = 0; index < transactions.size(); index++) {
                CustomerTransaction transaction =
                        transactions.get(index);

                if (transaction.amount() == null &&
                        medians.containsKey(transaction.city())) {

                    BigDecimal replacement =
                            medians.get(transaction.city());

                    transactions.set(
                            index,
                            new CustomerTransaction(
                                    transaction.customerId(),
                                    transaction.name(),
                                    transaction.email(),
                                    transaction.phone(),
                                    transaction.city(),
                                    replacement,
                                    transaction.currency(),
                                    transaction.status(),
                                    transaction.signupDate()
                            )
                    );

                    audit.add(new AuditEvent(
                            transaction.customerId(),
                            "amount",
                            "missing",
                            "imputed",
                            "City-level median = " + replacement
                    ));
                }
            }
        }
    }

    static final class DataCleaningService {

        private final List<CleaningRule> rules = List.of(
                new MissingValueRule(),
                new ConsistencyRule()
        );

        private final DeduplicationService deduplication =
                new DeduplicationService();

        private final MedianImputationService imputation =
                new MedianImputationService();

        private final ValidationService validation =
                new ValidationService();

        private final List<AuditEvent> audit =
                new ArrayList<>();

        List<CustomerTransaction> clean(
                List<CustomerTransaction> source
        ) {
            List<CustomerTransaction> current =
                    new ArrayList<>(source);

            for (CleaningRule rule : rules) {
                List<CustomerTransaction> transformed =
                        new ArrayList<>();

                for (CustomerTransaction transaction : current) {
                    transformed.add(rule.apply(transaction, audit));
                }

                current = transformed;
            }

            current = deduplication.removeDuplicates(current, audit);

            imputation.fillMissingAmounts(current, audit);

            return Collections.unmodifiableList(current);
        }

        List<AuditEvent> audit() {
            return Collections.unmodifiableList(audit);
        }

        ValidationService validation() {
            return validation;
        }
    }

    private static CustomerTransaction transaction(
            String id,
            String name,
            String email,
            String phone,
            String city,
            String amount,
            String currency,
            CustomerStatus status,
            String date
    ) {
        BigDecimal parsedAmount = amount == null
                ? null
                : new BigDecimal(amount);

        LocalDate parsedDate = date == null
                ? null
                : parseDate(date);

        return new CustomerTransaction(
                id,
                name,
                email,
                phone,
                city,
                parsedAmount,
                currency,
                status,
                parsedDate
        );
    }

    private static LocalDate parseDate(String value) {
        try {
            return LocalDate.parse(value);
        } catch (DateTimeParseException first) {
            return LocalDate.parse(
                    value,
                    DateTimeFormatter.ofPattern("dd/MM/yyyy")
            );
        }
    }

    public static void main(String[] args) {
        List<CustomerTransaction> source = List.of(
                transaction(
                        "C001", "Asha Sharma",
                        "ASHA@EXAMPLE.COM",
                        "+91 98765 43210",
                        "Lucknow", "1250", "INR",
                        CustomerStatus.ACTIVE, "2026-01-05"
                ),
                transaction(
                        "C002", "Rahul Verma",
                        "rahul@example.com",
                        "9876543211",
                        "Lucknow", "850", "inr",
                        CustomerStatus.ACTIVE, "05/01/2026"
                ),
                transaction(
                        "C003", "Meera Singh",
                        null,
                        "+91-91234-56789",
                        "Kanpur", null, "INR",
                        CustomerStatus.ACTIVE, "2026-01-08"
                ),
                transaction(
                        "C004", "Arun Kumar",
                        "arun@example.com",
                        null,
                        "Kanpur", "450", "INR",
                        CustomerStatus.ACTIVE, "2026-01-09"
                ),
                transaction(
                        "C005", "Neha Gupta",
                        "neha@example.com",
                        "+91 90000 11111",
                        "Lucknow", "1250", "INR",
                        CustomerStatus.ACTIVE, "2026-01-10"
                ),
                transaction(
                        "C005", "Neha Gupta",
                        "neha@example.com",
                        "+91 90000 11111",
                        "Lucknow", "1250", "INR",
                        CustomerStatus.ACTIVE, "2026-01-10"
                ),
                transaction(
                        "C006", "Ravi Patel",
                        "ravi@example.com",
                        "+91-98888-22222",
                        "lucknow", "850", "INR",
                        CustomerStatus.ACTIVE, "2026-01-11"
                ),
                transaction(
                        "C009", "Pooja Nair",
                        "pooja@example.com",
                        "+91 95555 55555",
                        "Lucknow", "1250", "Rs.",
                        CustomerStatus.ACTIVE, "2026-01-14"
                )
        );

        DataCleaningService service =
                new DataCleaningService();

        List<CustomerTransaction> cleaned =
                service.clean(source);

        System.out.println("DATA CLEANING ENTERPRISE MODEL");
        System.out.println("==============================");

        System.out.println("\nCLEANED RECORDS");

        for (CustomerTransaction transaction : cleaned) {
            System.out.println(transaction);
        }

        System.out.println("\nVALIDATION RESULTS");

        for (CustomerTransaction transaction : cleaned) {
            List<String> errors =
                    service.validation().validate(transaction);

            if (errors.isEmpty()) {
                System.out.println(
                        transaction.customerId() + ": valid"
                );
            } else {
                System.out.println(
                        transaction.customerId() + ": " + errors
                );
            }
        }

        System.out.println("\nAUDIT EVENTS");

        for (AuditEvent event : service.audit()) {
            System.out.println(event);
        }

        /*
         * The rule interface makes normalization extensible without changing
         * the orchestration service. This matters in enterprise pipelines
         * because a new data-quality rule should not require rewriting the
         * complete ingestion workflow.
         *
         * Deduplication uses a HashSet for average O(1) business-key lookup.
         * Median imputation sorts values per city, giving O(k log k) work for
         * a city containing k non-missing transaction amounts.
         */
    }
}
