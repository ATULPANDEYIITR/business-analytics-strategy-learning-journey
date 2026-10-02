#include <algorithm>
#include <iomanip>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

/*
 * SQL Fundamentals Case Study
 *
 * Scenario:
 * A company wants a small repository-independent governance report for its
 * employee and project database. The program models the relational behavior
 * behind common SQL queries:
 *
 *   FROM   -> identify the source relation
 *   WHERE  -> filter candidate rows
 *   SELECT -> project the values needed by the report
 *
 * The program then extends the model with:
 * - IN and BETWEEN-style predicates
 * - LIKE-style matching
 * - NULL-aware filtering
 * - DISTINCT
 * - ORDER BY and LIMIT
 * - CASE-style classification
 * - JOIN-like relationship traversal
 * - parameter validation
 * - query-planning considerations
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic sql_fundamentals.cpp -o sql_fundamentals
 */

struct Employee {
    int id;
    std::string name;
    std::string department;
    std::string title;
    std::string city;
    long salary;
    int experience;
    std::string status;
    std::optional<int> managerId;
};

struct Project {
    int id;
    std::string name;
    std::string department;
    std::string status;
    long budget;
};

struct Assignment {
    int employeeId;
    int projectId;
    std::string role;
};

struct ReportRow {
    std::string employee;
    std::string department;
    std::string value;
};

void printHeader(const std::string& title) {
    std::cout << "\n--- " << title << " ---\n";
}

void printEmployees(const std::vector<Employee>& employees) {
    std::cout
        << std::left
        << std::setw(18) << "Employee"
        << std::setw(16) << "Department"
        << std::setw(28) << "Title"
        << std::setw(14) << "Salary"
        << std::setw(8) << "Years"
        << "Status\n";

    std::cout << std::string(92, '-') << '\n';

    for (const auto& employee : employees) {
        std::cout
            << std::left
            << std::setw(18) << employee.name
            << std::setw(16) << employee.department
            << std::setw(28) << employee.title
            << std::setw(14) << employee.salary
            << std::setw(8) << employee.experience
            << employee.status
            << '\n';
    }
}

std::vector<Employee> makeEmployees() {
    return {
        {1, "Anita Rao", "Engineering", "Senior Backend Engineer",
         "Bengaluru", 1450000, 8, "Active", std::nullopt},

        {2, "Rohan Mehta", "Engineering", "Software Engineer",
         "Pune", 920000, 4, "Active", 1},

        {3, "Sara Khan", "Engineering", "Data Engineer",
         "Hyderabad", 1180000, 6, "Active", 1},

        {4, "Vikram Singh", "Finance", "Financial Analyst",
         "Mumbai", 840000, 5, "Active", std::nullopt},

        {5, "Neha Sharma", "Product", "Product Manager",
         "Delhi", 1320000, 7, "Active", std::nullopt},

        {6, "Arjun Nair", "Engineering", "QA Engineer",
         "Kochi", 760000, 3, "On Leave", 1},

        {7, "Meera Iyer", "Sales", "Account Executive",
         "Chennai", 680000, 2, "Active", std::nullopt},

        {8, "Kabir Das", "Engineering", "Platform Engineer",
         "Noida", 1250000, 7, "Active", 1},

        {9, "Pooja Verma", "HR", "People Operations Specialist",
         "Lucknow", 620000, 3, "Active", std::nullopt},

        {10, "Dev Malhotra", "Finance", "Senior Financial Analyst",
         "Mumbai", 1090000, 9, "Inactive", 4},

        {11, "Ishita Bose", "Product", "Product Analyst",
         "Kolkata", 880000, 3, "Active", 5},

        {12, "Rahul Joshi", "Sales", "Sales Operations Analyst",
         "Jaipur", 720000, 4, "Active", 7}
    };
}

std::vector<Project> makeProjects() {
    return {
        {101, "Cloud Migration", "Engineering", "Active", 2800000},
        {102, "Risk Analytics", "Finance", "Active", 1600000},
        {103, "Customer Portal", "Product", "Completed", 2200000},
        {104, "Security Hardening", "Engineering", "Active", 1900000}
    };
}

std::vector<Assignment> makeAssignments() {
    return {
        {1, 101, "Technical Lead"},
        {2, 101, "Backend Developer"},
        {3, 101, "Data Engineer"},
        {8, 101, "Platform Engineer"},
        {13, 104, "Security Lead"},
        {1, 104, "Engineering Sponsor"},
        {4, 102, "Project Analyst"},
        {10, 102, "Senior Analyst"}
    };
}

bool contains(const std::unordered_set<std::string>& values,
              const std::string& value) {
    return values.find(value) != values.end();
}

bool betweenInclusive(long value, long lower, long upper) {
    return value >= lower && value <= upper;
}

bool containsCaseInsensitive(const std::string& value,
                             const std::string& fragment) {
    if (fragment.empty()) {
        return true;
    }

    auto normalize = [](const std::string& input) {
        std::string result = input;

        std::transform(
            result.begin(),
            result.end(),
            result.begin(),
            [](unsigned char character) {
                return static_cast<char>(std::tolower(character));
            }
        );

        return result;
    };

    const std::string normalizedValue = normalize(value);
    const std::string normalizedFragment = normalize(fragment);

    return normalizedValue.find(normalizedFragment) != std::string::npos;
}

std::vector<Employee> selectFrom(
    const std::vector<Employee>& source,
    const std::function<bool(const Employee&)>& predicate) {

    std::vector<Employee> result;

    for (const auto& employee : source) {
        /*
         * This loop models the logical role of WHERE: only rows whose
         * predicate is true survive into the result relation.
         */
        if (predicate(employee)) {
            result.push_back(employee);
        }
    }

    return result;
}

std::vector<std::string> selectDepartments(
    const std::vector<Employee>& source) {

    std::vector<std::string> departments;
    std::unordered_set<std::string> seen;

    for (const auto& employee : source) {
        if (seen.insert(employee.department).second) {
            departments.push_back(employee.department);
        }
    }

    return departments;
}

std::vector<ReportRow> projectEmployees(
    const std::vector<Employee>& source) {

    std::vector<ReportRow> result;

    for (const auto& employee : source) {
        /*
         * SELECT is represented here as projection. The source object may
         * contain many attributes, but the report intentionally exposes only
         * the requested columns and a calculated monthly salary.
         */
        const long monthlySalary = employee.salary / 12;

        result.push_back({
            employee.name,
            employee.department,
            std::to_string(monthlySalary)
        });
    }

    return result;
}

void printReportRows(const std::vector<ReportRow>& rows) {
    std::cout
        << std::left
        << std::setw(20) << "Employee"
        << std::setw(18) << "Department"
        << "Calculated Value\n";

    std::cout << std::string(60, '-') << '\n';

    for (const auto& row : rows) {
        std::cout
            << std::left
            << std::setw(20) << row.employee
            << std::setw(18) << row.department
            << row.value
            << '\n';
    }
}

void demonstrateBasicSelectFrom(
    const std::vector<Employee>& employees) {

    printHeader("SELECT specific columns FROM employees");

    const auto activeEmployees = selectFrom(
        employees,
        [](const Employee& employee) {
            return employee.status == "Active";
        }
    );

    const auto report = projectEmployees(activeEmployees);

    printReportRows(report);
}

void demonstrateWhereComparisons(
    const std::vector<Employee>& employees) {

    printHeader("WHERE comparison predicates");

    const auto engineeringExperts = selectFrom(
        employees,
        [](const Employee& employee) {
            return employee.department == "Engineering" &&
                   employee.experience >= 7;
        }
    );

    printEmployees(engineeringExperts);
}

void demonstrateInAndBetween(
    const std::vector<Employee>& employees) {

    printHeader("IN and BETWEEN-style filtering");

    const std::unordered_set<std::string> targetCities{
        "Mumbai",
        "Bengaluru",
        "Pune"
    };

    const auto cityMatches = selectFrom(
        employees,
        [&](const Employee& employee) {
            return contains(targetCities, employee.city);
        }
    );

    printEmployees(cityMatches);

    printHeader("Salary BETWEEN 800000 AND 1200000");

    const auto salaryMatches = selectFrom(
        employees,
        [](const Employee& employee) {
            return betweenInclusive(
                employee.salary,
                800000,
                1200000
            );
        }
    );

    printEmployees(salaryMatches);
}

void demonstrateLike(
    const std::vector<Employee>& employees) {

    printHeader("LIKE-style job-title filtering");

    const auto engineers = selectFrom(
        employees,
        [](const Employee& employee) {
            return containsCaseInsensitive(
                employee.title,
                "engineer"
            );
        }
    );

    printEmployees(engineers);
}

void demonstrateNull(
    const std::vector<Employee>& employees) {

    printHeader("NULL-aware manager filtering");

    const auto topLevelEmployees = selectFrom(
        employees,
        [](const Employee& employee) {
            /*
             * std::optional models SQL NULL more accurately than a magic
             * integer such as zero. No manager is represented by an empty
             * optional value.
             */
            return !employee.managerId.has_value();
        }
    );

    printEmployees(topLevelEmployees);

    printHeader("Employees with a recorded manager");

    const auto managedEmployees = selectFrom(
        employees,
        [](const Employee& employee) {
            return employee.managerId.has_value();
        }
    );

    printEmployees(managedEmployees);
}

void demonstrateLogicalPrecedence(
    const std::vector<Employee>& employees) {

    printHeader("Explicit logical grouping");

    const auto result = selectFrom(
        employees,
        [](const Employee& employee) {
            return
                (
                    employee.department == "Engineering" &&
                    employee.salary >= 1200000
                )
                ||
                employee.department == "Product";
        }
    );

    printEmployees(result);
}

void demonstrateDistinct(
    const std::vector<Employee>& employees) {

    printHeader("DISTINCT department values");

    const auto departments = selectDepartments(employees);

    for (const auto& department : departments) {
        std::cout << department << '\n';
    }
}

void demonstrateOrderAndLimit(
    std::vector<Employee> employees) {

    printHeader("ORDER BY salary DESC LIMIT 5");

    auto active = selectFrom(
        employees,
        [](const Employee& employee) {
            return employee.status == "Active";
        }
    );

    std::sort(
        active.begin(),
        active.end(),
        [](const Employee& left, const Employee& right) {
            if (left.salary != right.salary) {
                return left.salary > right.salary;
            }

            return left.name < right.name;
        }
    );

    if (active.size() > 5) {
        active.resize(5);
    }

    printEmployees(active);
}

void demonstrateCaseClassification(
    const std::vector<Employee>& employees) {

    printHeader("CASE-style compensation classification");

    for (const auto& employee : employees) {
        std::string band;

        if (employee.salary >= 1300000) {
            band = "Senior compensation band";
        } else if (employee.salary >= 900000) {
            band = "Mid compensation band";
        } else {
            band = "Entry compensation band";
        }

        std::cout
            << std::left
            << std::setw(20) << employee.name
            << std::setw(15) << employee.salary
            << band
            << '\n';
    }
}

void demonstrateJoin(
    const std::vector<Employee>& employees,
    const std::vector<Project>& projects,
    const std::vector<Assignment>& assignments) {

    printHeader("JOIN-style active project report");

    for (const auto& assignment : assignments) {
        auto employeeIt = std::find_if(
            employees.begin(),
            employees.end(),
            [&](const Employee& employee) {
                return employee.id == assignment.employeeId;
            }
        );

        auto projectIt = std::find_if(
            projects.begin(),
            projects.end(),
            [&](const Project& project) {
                return project.id == assignment.projectId &&
                       project.status == "Active";
            }
        );

        if (employeeIt == employees.end() ||
            projectIt == projects.end()) {
            continue;
        }

        std::cout
            << employeeIt->name
            << " -> "
            << projectIt->name
            << " -> "
            << assignment.role
            << '\n';
    }
}

struct QueryParameters {
    std::string department;
    long minimumSalary;
};

void validateParameters(const QueryParameters& parameters) {
    /*
     * SQL parameters should be treated as data, not executable query text.
     * The application still needs semantic validation before sending those
     * values to the database.
     */
    if (parameters.department.empty()) {
        throw std::invalid_argument(
            "department cannot be empty"
        );
    }

    if (parameters.minimumSalary < 0) {
        throw std::invalid_argument(
            "minimumSalary cannot be negative"
        );
    }
}

std::vector<Employee> parameterizedFilter(
    const std::vector<Employee>& employees,
    const QueryParameters& parameters) {

    validateParameters(parameters);

    return selectFrom(
        employees,
        [&](const Employee& employee) {
            return employee.department == parameters.department &&
                   employee.salary >= parameters.minimumSalary;
        }
    );
}

void demonstrateParameterValidation(
    const std::vector<Employee>& employees) {

    printHeader("Validated parameterized filter");

    const QueryParameters validParameters{
        "Engineering",
        1000000
    };

    const auto result = parameterizedFilter(
        employees,
        validParameters
    );

    printEmployees(result);

    try {
        const QueryParameters invalidParameters{
            "Engineering",
            -500
        };

        static_cast<void>(
            parameterizedFilter(
                employees,
                invalidParameters
            )
        );
    } catch (const std::invalid_argument& error) {
        std::cout
            << "\nRejected invalid filter: "
            << error.what()
            << '\n';
    }
}

void demonstrateQueryPlanning() {
    printHeader("Query-planning considerations");

    std::cout
        << "A WHERE filter on department may benefit from an index when the "
           "table becomes large.\n"
        << "A composite index can be useful when queries repeatedly filter "
           "by department and salary together.\n"
        << "Selecting only required columns can reduce transferred data, "
           "especially when rows contain large text or binary values.\n"
        << "The database optimizer, rather than application code, should "
           "normally decide the physical access strategy.\n";
}

void demonstrateCaseStudy(
    const std::vector<Employee>& employees,
    const std::vector<Project>& projects,
    const std::vector<Assignment>& assignments) {

    /*
     * Case study:
     * A finance manager asks for active Engineering employees earning at
     * least one million units annually. The result needs the employee name,
     * job title, annual salary, and monthly salary.
     *
     * Conceptually:
     *
     * FROM employees
     * WHERE department = 'Engineering'
     *   AND status = 'Active'
     *   AND salary >= 1000000
     * SELECT name, title, salary, salary / 12
     *
     * The implementation first filters the relation and then projects the
     * required fields, making the relational stages explicit.
     */
    printHeader("Technical case study: engineering compensation report");

    const QueryParameters parameters{
        "Engineering",
        1000000
    };

    const auto filtered = parameterizedFilter(
        employees,
        parameters
    );

    const auto activeFiltered = selectFrom(
        filtered,
        [](const Employee& employee) {
            return employee.status == "Active";
        }
    );

    std::vector<ReportRow> report;

    for (const auto& employee : activeFiltered) {
        report.push_back({
            employee.name,
            employee.title,
            "annual=" +
                std::to_string(employee.salary) +
                ", monthly=" +
                std::to_string(employee.salary / 12)
        });
    }

    printReportRows(report);

    demonstrateJoin(
        employees,
        projects,
        assignments
    );
}

int main() {
    try {
        const auto employees = makeEmployees();
        const auto projects = makeProjects();
        const auto assignments = makeAssignments();

        std::cout << "SQL FUNDAMENTALS CASE STUDY\n";
        std::cout << "===========================\n";
        std::cout
            << "Focus: SELECT, FROM, WHERE and practical basic-query behavior.\n";

        demonstrateBasicSelectFrom(employees);
        demonstrateWhereComparisons(employees);
        demonstrateInAndBetween(employees);
        demonstrateLike(employees);
        demonstrateNull(employees);
        demonstrateLogicalPrecedence(employees);
        demonstrateDistinct(employees);
        demonstrateOrderAndLimit(employees);
        demonstrateCaseClassification(employees);
        demonstrateParameterValidation(employees);
        demonstrateCaseStudy(
            employees,
            projects,
            assignments
        );
        demonstrateQueryPlanning();

        std::cout
            << "\nC++ SQL fundamentals case study completed successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
