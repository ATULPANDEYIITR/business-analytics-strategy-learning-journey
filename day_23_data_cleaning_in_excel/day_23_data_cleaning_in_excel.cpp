/*
 * Data Cleaning in Excel
 * ======================
 *
 * C++17 case study:
 *
 * "Customer Transaction Data Quality Engine"
 *
 * Scenario
 * --------
 * An organization receives customer transaction records from multiple
 * operational sources. The records resemble spreadsheet rows and contain
 * inconsistent whitespace, categories, states, dates, phone numbers, numeric
 * amounts, missing values, duplicate customer IDs, invalid ages, and invalid
 * transactions.
 *
 * The program develops a complete data-quality workflow:
 *
 * 1. Load representative raw records.
 * 2. Profile the dataset.
 * 3. Standardize text.
 * 4. Normalize phone numbers.
 * 5. Parse currency.
 * 6. Parse dates with validation.
 * 7. Validate business rules.
 * 8. Detect duplicate identifiers.
 * 9. Detect exact duplicate records.
 * 10. Build an audit trail.
 * 11. Calculate data-quality metrics.
 * 12. Aggregate transactions.
 * 13. Export a cleaned CSV representation.
 *
 * Compile:
 *     g++ -std=c++17 -O2 -Wall -Wextra -pedantic main.cpp -o cleaner
 *
 * Run:
 *     ./cleaner
 */

#include <algorithm>
#include <cctype>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <regex>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;


// ============================================================================
// SECTION 1: DOMAIN MODEL
// ============================================================================

struct CustomerRecord {
    string customerId;
    string name;
    string email;
    string phone;
    string city;
    string state;
    string amountText;
    string orderDateText;
    string category;
    string ageText;
};

struct CleanCustomerRecord {
    string customerId;
    string name;
    optional<string> email;
    optional<string> phone;
    string city;
    string state;
    optional<double> amount;
    optional<string> orderDate;
    string category;
    optional<int> age;
};

struct ValidationResult {
    bool valid;
    vector<string> errors;
};


// ============================================================================
// SECTION 2: STRING UTILITIES
// ============================================================================

string trim(const string& input) {
    size_t start = 0;
    size_t end = input.size();

    while (
        start < end &&
        isspace(static_cast<unsigned char>(input[start]))
    ) {
        ++start;
    }

    while (
        end > start &&
        isspace(static_cast<unsigned char>(input[end - 1]))
    ) {
        --end;
    }

    return input.substr(start, end - start);
}


string collapseWhitespace(const string& input) {
    string result;
    bool previousWasWhitespace = false;

    for (unsigned char character : input) {
        if (isspace(character)) {
            if (!previousWasWhitespace) {
                result.push_back(' ');
            }

            previousWasWhitespace = true;
        } else {
            result.push_back(static_cast<char>(character));
            previousWasWhitespace = false;
        }
    }

    return trim(result);
}


string toLower(string input) {
    transform(
        input.begin(),
        input.end(),
        input.begin(),
        [](unsigned char character) {
            return static_cast<char>(tolower(character));
        }
    );

    return input;
}


string titleCase(string input) {
    input = toLower(collapseWhitespace(input));

    bool capitalizeNext = true;

    for (char& character : input) {
        if (isspace(static_cast<unsigned char>(character))) {
            capitalizeNext = true;
        } else if (capitalizeNext) {
            character = static_cast<char>(
                toupper(static_cast<unsigned char>(character))
            );
            capitalizeNext = false;
        }
    }

    return input;
}


bool isMissing(const string& value) {
    return trim(value).empty();
}


// ============================================================================
// SECTION 3: CONTROLLED VOCABULARIES
// ============================================================================

const unordered_map<string, string> CATEGORY_MAP = {
    {"electronics", "Electronics"},
    {"electronic", "Electronics"},
    {"home appliance", "Home Appliances"},
    {"home appliances", "Home Appliances"},
    {"furniture", "Furniture"}
};


const unordered_map<string, string> STATE_MAP = {
    {"up", "Uttar Pradesh"},
    {"u.p.", "Uttar Pradesh"},
    {"uttar pradesh", "Uttar Pradesh"},
    {"dl", "Delhi"},
    {"delhi", "Delhi"}
};


string normalizeCategory(const string& value) {
    if (isMissing(value)) {
        return "";
    }

    string key = toLower(collapseWhitespace(value));

    auto iterator = CATEGORY_MAP.find(key);

    if (iterator != CATEGORY_MAP.end()) {
        return iterator->second;
    }

    return titleCase(key);
}


string normalizeState(const string& value) {
    if (isMissing(value)) {
        return "";
    }

    string key = toLower(collapseWhitespace(value));

    auto iterator = STATE_MAP.find(key);

    if (iterator != STATE_MAP.end()) {
        return iterator->second;
    }

    return titleCase(key);
}


// ============================================================================
// SECTION 4: PHONE NORMALIZATION
// ============================================================================

optional<string> normalizePhone(const string& value) {
    if (isMissing(value)) {
        return nullopt;
    }

    string digits;

    for (char character : value) {
        if (isdigit(static_cast<unsigned char>(character))) {
            digits.push_back(character);
        }
    }

    if (digits.size() == 12 && digits.rfind("91", 0) == 0) {
        digits = digits.substr(2);
    }

    if (digits.size() == 11 && digits[0] == '0') {
        digits = digits.substr(1);
    }

    if (digits.size() != 10) {
        return nullopt;
    }

    return digits;
}


// ============================================================================
// SECTION 5: EMAIL VALIDATION
// ============================================================================

bool validateEmail(const string& value) {
    if (isMissing(value)) {
        return false;
    }

    static const regex pattern(
        R"(^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$)"
    );

    return regex_match(trim(value), pattern);
}


// ============================================================================
// SECTION 6: CURRENCY PARSING
// ============================================================================

optional<double> parseAmount(const string& value) {
    if (isMissing(value)) {
        return nullopt;
    }

    string cleaned;

    for (char character : value) {
        /*
         * Currency symbols are ignored.
         * Commas and spaces are formatting characters.
         * Unknown alphabetic characters are deliberately rejected rather than
         * guessed, because automatic guessing can silently corrupt financial
         * information.
         */
        if (
            character == ',' ||
            character == ' ' ||
            character == '$'
        ) {
            continue;
        }

        if (
            character == '-' ||
            character == '.' ||
            isdigit(static_cast<unsigned char>(character))
        ) {
            cleaned.push_back(character);
        } else {
            return nullopt;
        }
    }

    try {
        size_t consumed = 0;
        double amount = stod(cleaned, &consumed);

        if (consumed != cleaned.size()) {
            return nullopt;
        }

        if (!isfinite(amount)) {
            return nullopt;
        }

        return amount;
    } catch (...) {
        return nullopt;
    }
}


// ============================================================================
// SECTION 7: DATE PARSING
// ============================================================================

struct Date {
    int year;
    int month;
    int day;
};


bool isLeapYear(int year) {
    return (
        (year % 4 == 0 && year % 100 != 0) ||
        (year % 400 == 0)
    );
}


int daysInMonth(int year, int month) {
    static const int days[] = {
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    };

    if (month == 2 && isLeapYear(year)) {
        return 29;
    }

    return days[month - 1];
}


bool isValidDate(const Date& date) {
    if (date.month < 1 || date.month > 12) {
        return false;
    }

    if (date.day < 1 || date.day > daysInMonth(date.year, date.month)) {
        return false;
    }

    return true;
}


optional<Date> parseDate(const string& value) {
    if (isMissing(value)) {
        return nullopt;
    }

    string input = trim(value);

    smatch match;

    regex dayMonthYear(R"(^(\d{2})[/-](\d{2})[/-](\d{4})$)");
    regex yearMonthDay(R"(^(\d{4})-(\d{2})-(\d{2})$)");

    if (regex_match(input, match, dayMonthYear)) {
        Date date{
            stoi(match[3]),
            stoi(match[2]),
            stoi(match[1])
        };

        if (isValidDate(date)) {
            return date;
        }

        return nullopt;
    }

    if (regex_match(input, match, yearMonthDay)) {
        Date date{
            stoi(match[1]),
            stoi(match[2]),
            stoi(match[3])
        };

        if (isValidDate(date)) {
            return date;
        }

        return nullopt;
    }

    return nullopt;
}


string dateToIso(const Date& date) {
    ostringstream output;

    output
        << setfill('0')
        << setw(4) << date.year
        << "-"
        << setw(2) << date.month
        << "-"
        << setw(2) << date.day;

    return output.str();
}


// ============================================================================
// SECTION 8: AGE PARSING
// ============================================================================

optional<int> parseAge(const string& value) {
    if (isMissing(value)) {
        return nullopt;
    }

    string input = trim(value);

    if (
        !all_of(
            input.begin(),
            input.end(),
            [](unsigned char character) {
                return isdigit(character);
            }
        )
    ) {
        return nullopt;
    }

    try {
        int age = stoi(input);

        if (age < 0 || age > 120) {
            return nullopt;
        }

        return age;
    } catch (...) {
        return nullopt;
    }
}


// ============================================================================
// SECTION 9: CLEANING
// ============================================================================

CleanCustomerRecord cleanRecord(const CustomerRecord& raw) {
    CleanCustomerRecord clean;

    clean.customerId = collapseWhitespace(raw.customerId);
    clean.name = titleCase(raw.name);

    if (!isMissing(raw.email)) {
        clean.email = toLower(collapseWhitespace(raw.email));
    }

    clean.phone = normalizePhone(raw.phone);
    clean.city = titleCase(raw.city);
    clean.state = normalizeState(raw.state);

    clean.amount = parseAmount(raw.amountText);

    auto parsedDate = parseDate(raw.orderDateText);

    if (parsedDate.has_value()) {
        clean.orderDate = dateToIso(parsedDate.value());
    }

    clean.category = normalizeCategory(raw.category);
    clean.age = parseAge(raw.ageText);

    return clean;
}


// ============================================================================
// SECTION 10: VALIDATION
// ============================================================================

bool validateCustomerId(const string& value) {
    static const regex pattern(R"(^C\d{3}$)");
    return regex_match(value, pattern);
}


ValidationResult validateRecord(const CleanCustomerRecord& record) {
    ValidationResult result{true, {}};

    if (isMissing(record.customerId)) {
        result.errors.push_back("Customer ID is required");
    } else if (!validateCustomerId(record.customerId)) {
        result.errors.push_back("Customer ID has invalid format");
    }

    if (isMissing(record.name)) {
        result.errors.push_back("Name is required");
    }

    if (!record.phone.has_value()) {
        result.errors.push_back("Phone is missing or invalid");
    }

    if (record.email.has_value() && !validateEmail(record.email.value())) {
        result.errors.push_back("Email is invalid");
    }

    if (!record.amount.has_value()) {
        result.errors.push_back("Amount is missing or invalid");
    } else if (record.amount.value() < 0) {
        result.errors.push_back("Amount cannot be negative");
    }

    if (!record.orderDate.has_value()) {
        result.errors.push_back("Order date is missing or invalid");
    }

    if (record.age.has_value()) {
        if (
            record.age.value() < 0 ||
            record.age.value() > 120
        ) {
            result.errors.push_back("Age is outside the allowed range");
        }
    } else {
        result.errors.push_back("Age is missing or invalid");
    }

    const set<string> allowedCategories = {
        "Electronics",
        "Home Appliances",
        "Furniture"
    };

    if (!allowedCategories.contains(record.category)) {
        result.errors.push_back(
            "Category is outside the controlled vocabulary"
        );
    }

    result.valid = result.errors.empty();

    return result;
}


// ============================================================================
// SECTION 11: CROSS-FIELD VALIDATION
// ============================================================================

vector<string> validateRelationships(
    const CleanCustomerRecord& record
) {
    vector<string> errors;

    if (
        (record.city == "Lucknow" || record.city == "Kanpur") &&
        record.state != "Uttar Pradesh"
    ) {
        errors.push_back(
            "City/state relationship is inconsistent"
        );
    }

    if (
        record.amount.has_value() &&
        record.amount.value() < 0
    ) {
        errors.push_back("Amount cannot be negative");
    }

    return errors;
}


// ============================================================================
// SECTION 12: DUPLICATE DETECTION
// ============================================================================

vector<pair<string, vector<int>>> findDuplicateCustomerIds(
    const vector<CleanCustomerRecord>& rows
) {
    map<string, vector<int>> groups;

    for (size_t index = 0; index < rows.size(); ++index) {
        groups[rows[index].customerId].push_back(
            static_cast<int>(index) + 2
        );
    }

    vector<pair<string, vector<int>>> duplicates;

    for (const auto& [customerId, indexes] : groups) {
        if (indexes.size() > 1) {
            duplicates.push_back({customerId, indexes});
        }
    }

    return duplicates;
}


// ============================================================================
// SECTION 13: ROW SIGNATURE
// ============================================================================

string recordSignature(const CleanCustomerRecord& record) {
    ostringstream output;

    output
        << record.customerId << "|"
        << record.name << "|"
        << (record.email.has_value() ? record.email.value() : "") << "|"
        << (record.phone.has_value() ? record.phone.value() : "") << "|"
        << record.city << "|"
        << record.state << "|";

    if (record.amount.has_value()) {
        output << fixed << setprecision(2) << record.amount.value();
    }

    output << "|";

    if (record.orderDate.has_value()) {
        output << record.orderDate.value();
    }

    output << "|"
           << record.category
           << "|";

    if (record.age.has_value()) {
        output << record.age.value();
    }

    return output.str();
}


// ============================================================================
// SECTION 14: QUALITY METRICS
// ============================================================================

double completenessScore(
    const vector<CleanCustomerRecord>& rows
) {
    if (rows.empty()) {
        return 100.0;
    }

    size_t populated = 0;
    size_t total = rows.size() * 8;

    for (const auto& row : rows) {
        populated += !isMissing(row.customerId);
        populated += !isMissing(row.name);
        populated += row.email.has_value();
        populated += row.phone.has_value();
        populated += !isMissing(row.city);
        populated += !isMissing(row.state);
        populated += row.amount.has_value();
        populated += row.orderDate.has_value();
    }

    return static_cast<double>(populated) /
           static_cast<double>(total) *
           100.0;
}


double validityScore(
    const vector<CleanCustomerRecord>& rows
) {
    if (rows.empty()) {
        return 100.0;
    }

    size_t validRows = 0;

    for (const auto& row : rows) {
        ValidationResult validation = validateRecord(row);
        vector<string> relationshipErrors =
            validateRelationships(row);

        if (
            validation.valid &&
            relationshipErrors.empty()
        ) {
            ++validRows;
        }
    }

    return static_cast<double>(validRows) /
           static_cast<double>(rows.size()) *
           100.0;
}


// ============================================================================
// SECTION 15: AUDIT TRAIL
// ============================================================================

struct AuditEntry {
    int row;
    string field;
    string before;
    string after;
};


vector<AuditEntry> createAuditTrail(
    const vector<CustomerRecord>& before,
    const vector<CleanCustomerRecord>& after
) {
    vector<AuditEntry> audit;

    for (size_t index = 0; index < before.size(); ++index) {
        const auto& raw = before[index];
        const auto& clean = after[index];

        string cleanEmail =
            clean.email.has_value() ? clean.email.value() : "";

        string cleanPhone =
            clean.phone.has_value() ? clean.phone.value() : "";

        string cleanAmount;

        if (clean.amount.has_value()) {
            ostringstream amountStream;
            amountStream
                << fixed
                << setprecision(2)
                << clean.amount.value();

            cleanAmount = amountStream.str();
        }

        string cleanDate =
            clean.orderDate.has_value()
                ? clean.orderDate.value()
                : "";

        string cleanAge;

        if (clean.age.has_value()) {
            cleanAge = to_string(clean.age.value());
        }

        vector<tuple<string, string, string>> fields = {
            {"Customer ID", raw.customerId, clean.customerId},
            {"Name", raw.name, clean.name},
            {"Email", raw.email, cleanEmail},
            {"Phone", raw.phone, cleanPhone},
            {"City", raw.city, clean.city},
            {"State", raw.state, clean.state},
            {"Amount", raw.amountText, cleanAmount},
            {"Order Date", raw.orderDateText, cleanDate},
            {"Category", raw.category, clean.category},
            {"Age", raw.ageText, cleanAge}
        };

        for (const auto& [field, oldValue, newValue] : fields) {
            if (oldValue != newValue) {
                audit.push_back(
                    {
                        static_cast<int>(index) + 2,
                        field,
                        oldValue,
                        newValue
                    }
                );
            }
        }
    }

    return audit;
}


// ============================================================================
// SECTION 16: AGGREGATION
// ============================================================================

map<string, double> amountByCategory(
    const vector<CleanCustomerRecord>& rows
) {
    map<string, double> totals;

    for (const auto& row : rows) {
        if (row.amount.has_value()) {
            totals[row.category] += row.amount.value();
        }
    }

    return totals;
}


// ============================================================================
// SECTION 17: CSV ESCAPING
// ============================================================================

string csvEscape(const string& value) {
    if (
        value.find(',') != string::npos ||
        value.find('"') != string::npos ||
        value.find('\n') != string::npos
    ) {
        string escaped = value;

        size_t position = 0;

        while (
            (position = escaped.find('"', position))
            != string::npos
        ) {
            escaped.insert(position, 1, '"');
            position += 2;
        }

        return "\"" + escaped + "\"";
    }

    return value;
}


string cleanedCsv(
    const vector<CleanCustomerRecord>& rows
) {
    ostringstream output;

    output
        << "Customer ID,Name,Email,Phone,City,State,Amount,"
        << "Order Date,Category,Age\n";

    for (const auto& row : rows) {
        output
            << csvEscape(row.customerId) << ","
            << csvEscape(row.name) << ","
            << csvEscape(
                row.email.has_value() ? row.email.value() : ""
            ) << ","
            << csvEscape(
                row.phone.has_value() ? row.phone.value() : ""
            ) << ","
            << csvEscape(row.city) << ","
            << csvEscape(row.state) << ",";

        if (row.amount.has_value()) {
            output
                << fixed
                << setprecision(2)
                << row.amount.value();
        }

        output << ",";

        if (row.orderDate.has_value()) {
            output << csvEscape(row.orderDate.value());
        }

        output
            << ","
            << csvEscape(row.category)
            << ",";

        if (row.age.has_value()) {
            output << row.age.value();
        }

        output << "\n";
    }

    return output.str();
}


// ============================================================================
// SECTION 18: MAIN CASE STUDY
// ============================================================================

int main() {
    cout << string(78, '=') << "\n";
    cout << "CUSTOMER TRANSACTION DATA QUALITY ENGINE\n";
    cout << string(78, '=') << "\n";

    vector<CustomerRecord> rawData = {
        {
            " C001 ",
            "  Rahul Sharma ",
            "RAHUL.SHARMA@EXAMPLE.COM ",
            "98765 43210",
            " lucknow",
            "UP",
            "₹ 12,500",
            "15/09/2026",
            " electronics ",
            "29"
        },
        {
            "C002",
            "PRIYA SINGH",
            "priya.singh@example.com",
            "+91-9876543211",
            "Lucknow ",
            "Uttar Pradesh",
            "15000",
            "2026-09-16",
            "Electronics",
            "31"
        },
        {
            "C003",
            " Amit Kumar ",
            " amit.kumar@example.com",
            "98765-43212",
            "KANPUR",
            "UP",
            "₹8,750.50",
            "16-09-2026",
            "electronics",
            "twenty-eight"
        },
        {
            "C004",
            "Neha Verma",
            "neha.verma@example.com",
            "9876543213",
            "Kanpur",
            "U.P.",
            "10,000",
            "17/09/2026",
            " Home Appliances ",
            "42"
        },
        {
            "C005",
            "Suresh Patel",
            "",
            "9876543214",
            "Delhi",
            "Delhi",
            "12500",
            "",
            "home appliance",
            "37"
        },
        {
            "C005",
            " Suresh Patel ",
            "",
            "9876543214",
            "Delhi ",
            "Delhi",
            "12500",
            "",
            "Home Appliances",
            "37"
        },
        {
            "C006",
            "Meera Joshi",
            "meera.joshi@example.com",
            "09876543215",
            "Delhi",
            "DL",
            "-500",
            "31/09/2026",
            "Furniture",
            "150"
        },
        {
            "C007",
            "Arjun Mehta",
            "arjun.mehta@example",
            "9876543216",
            "Lucknow",
            "Uttar Pradesh",
            "1O,500",
            "18/09/2026",
            "Furniture",
            "34"
        }
    };


    // ------------------------------------------------------------------------
    // STEP 1: Profile the raw dataset.
    // ------------------------------------------------------------------------

    cout << "\nRAW DATASET PROFILE\n";

    cout << "Rows: " << rawData.size() << "\n";
    cout << "Columns: 10\n";


    // ------------------------------------------------------------------------
    // STEP 2: Clean all records.
    // ------------------------------------------------------------------------

    vector<CleanCustomerRecord> cleanedData;

    for (const auto& raw : rawData) {
        cleanedData.push_back(cleanRecord(raw));
    }


    // ------------------------------------------------------------------------
    // STEP 3: Display cleaned records.
    // ------------------------------------------------------------------------

    cout << "\nCLEANED RECORDS\n";

    for (size_t index = 0; index < cleanedData.size(); ++index) {
        const auto& row = cleanedData[index];

        cout
            << "Excel row " << index + 2
            << " | ID=" << row.customerId
            << " | Name=" << row.name
            << " | City=" << row.city
            << " | State=" << row.state
            << " | Category=" << row.category
            << "\n";
    }


    // ------------------------------------------------------------------------
    // STEP 4: Validate each record.
    // ------------------------------------------------------------------------

    cout << "\nVALIDATION RESULTS\n";

    for (size_t index = 0; index < cleanedData.size(); ++index) {
        const auto& row = cleanedData[index];

        ValidationResult result =
            validateRecord(row);

        vector<string> relationshipErrors =
            validateRelationships(row);

        bool valid =
            result.valid &&
            relationshipErrors.empty();

        cout
            << "Row " << index + 2
            << ": "
            << (valid ? "VALID" : "INVALID")
            << "\n";

        for (const string& error : result.errors) {
            cout << "  - " << error << "\n";
        }

        for (const string& error : relationshipErrors) {
            cout << "  - " << error << "\n";
        }
    }


    // ------------------------------------------------------------------------
    // STEP 5: Detect duplicate customer IDs.
    // ------------------------------------------------------------------------

    cout << "\nDUPLICATE CUSTOMER IDs\n";

    auto duplicates =
        findDuplicateCustomerIds(cleanedData);

    for (const auto& [customerId, indexes] : duplicates) {
        cout << customerId << ": ";

        for (size_t index = 0; index < indexes.size(); ++index) {
            if (index > 0) {
                cout << ", ";
            }

            cout << indexes[index];
        }

        cout << "\n";
    }


    // ------------------------------------------------------------------------
    // STEP 6: Detect exact duplicate records.
    // ------------------------------------------------------------------------

    map<string, vector<int>> exactGroups;

    for (size_t index = 0; index < cleanedData.size(); ++index) {
        exactGroups[
            recordSignature(cleanedData[index])
        ].push_back(
            static_cast<int>(index) + 2
        );
    }

    cout << "\nEXACT DUPLICATE GROUPS\n";

    for (const auto& [signature, indexes] : exactGroups) {
        if (indexes.size() > 1) {
            cout << "Rows: ";

            for (size_t index = 0; index < indexes.size(); ++index) {
                if (index > 0) {
                    cout << ", ";
                }

                cout << indexes[index];
            }

            cout << "\n";
        }
    }


    // ------------------------------------------------------------------------
    // STEP 7: Calculate quality metrics.
    // ------------------------------------------------------------------------

    cout << "\nDATA QUALITY METRICS\n";

    cout
        << fixed
        << setprecision(2)
        << "Completeness: "
        << completenessScore(cleanedData)
        << "%\n";

    cout
        << "Validity: "
        << validityScore(cleanedData)
        << "%\n";


    // ------------------------------------------------------------------------
    // STEP 8: Audit transformations.
    // ------------------------------------------------------------------------

    cout << "\nAUDIT TRAIL\n";

    vector<AuditEntry> audit =
        createAuditTrail(rawData, cleanedData);

    for (const auto& entry : audit) {
        cout
            << "Row " << entry.row
            << " | "
            << entry.field
            << " | "
            << "'" << entry.before << "'"
            << " -> "
            << "'" << entry.after << "'"
            << "\n";
    }


    // ------------------------------------------------------------------------
    // STEP 9: Aggregate transaction values by category.
    // ------------------------------------------------------------------------

    cout << "\nAMOUNT BY CATEGORY\n";

    auto categoryTotals =
        amountByCategory(cleanedData);

    for (const auto& [category, total] : categoryTotals) {
        cout
            << category
            << ": "
            << fixed
            << setprecision(2)
            << total
            << "\n";
    }


    // ------------------------------------------------------------------------
    // STEP 10: Export cleaned data.
    // ------------------------------------------------------------------------

    cout << "\nCLEANED CSV PREVIEW\n";
    cout << cleanedCsv(cleanedData);


    // ------------------------------------------------------------------------
    // STEP 11: Demonstrate edge-case handling.
    // ------------------------------------------------------------------------

    cout << "\nEDGE CASE TESTS\n";

    vector<string> invalidDates = {
        "31/09/2026",
        "29/02/2025",
        "2024-02-29",
        "01/13/2026"
    };

    for (const string& value : invalidDates) {
        auto parsed = parseDate(value);

        cout
            << value
            << " -> "
            << (parsed.has_value()
                ? dateToIso(parsed.value())
                : "REJECTED")
            << "\n";
    }


    // ------------------------------------------------------------------------
    // STEP 12: Architectural observations.
    // ------------------------------------------------------------------------

    cout << "\nARCHITECTURAL DECISIONS\n";

    cout
        << "1. Raw records and cleaned records use separate structures.\n"
        << "2. Parsing functions return optional values instead of inventing data.\n"
        << "3. Validation occurs after normalization.\n"
        << "4. Controlled vocabularies are represented by lookup maps.\n"
        << "5. Business rules are separated from basic parsing.\n"
        << "6. Audit entries record important transformations.\n"
        << "7. Duplicate detection uses explicit keys.\n"
        << "8. CSV output escapes fields that require quoting.\n"
        << "9. Invalid dates are rejected rather than silently normalized.\n"
        << "10. The workflow separates transformation from validation.\n";


    // ------------------------------------------------------------------------
    // STEP 13: Complexity discussion.
    // ------------------------------------------------------------------------

    cout << "\nCOMPLEXITY CONSIDERATIONS\n";

    cout
        << "Text normalization is approximately O(L) per field, where L is "
        << "the field length.\n"
        << "Processing N records with a fixed number of columns is "
        << "approximately O(N * L).\n"
        << "Hash-map-based duplicate grouping is approximately O(N) average "
        << "time.\n"
        << "Ordered map grouping is approximately O(N log N).\n"
        << "The audit trail is proportional to the number of changed fields.\n"
        << "Memory consumption is O(N) when the entire dataset is held in memory.\n";


    // ------------------------------------------------------------------------
    // STEP 14: Production considerations.
    // ------------------------------------------------------------------------

    cout << "\nPRODUCTION CONSIDERATIONS\n";

    cout
        << "A production system should preserve raw input, version cleaning "
        << "rules, protect sensitive data, log failures, test transformations, "
        << "define business ownership for validation rules, and separate "
        << "statistical anomaly detection from confirmed data errors.\n";


    cout << "\n" << string(78, '=') << "\n";
    cout << "END OF C++ DATA CLEANING CASE STUDY\n";
    cout << string(78, '=') << "\n";

    return 0;
}
