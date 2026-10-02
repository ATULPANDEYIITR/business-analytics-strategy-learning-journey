"use strict";

/*
 * SQL Fundamentals in JavaScript
 *
 * This file models SQL query behavior in an event-driven Node.js style.
 * It uses an in-memory relational dataset and a small query engine so the
 * file remains executable without external npm dependencies.
 *
 * The implementation focuses on:
 * SELECT projection
 * FROM source selection
 * WHERE filtering
 * aliases and expressions
 * DISTINCT
 * comparison and logical predicates
 * NULL semantics
 * LIKE, IN, BETWEEN
 * ORDER BY and LIMIT
 * parameterized filtering
 * review of query structure
 * asynchronous query execution
 *
 * Run with:
 *   node sql_fundamentals.js
 */

const employees = [
  {
    employeeId: 1,
    fullName: "Anita Rao",
    department: "Engineering",
    jobTitle: "Senior Backend Engineer",
    city: "Bengaluru",
    salary: 1450000,
    yearsExperience: 8,
    employmentStatus: "Active",
    managerId: null
  },
  {
    employeeId: 2,
    fullName: "Rohan Mehta",
    department: "Engineering",
    jobTitle: "Software Engineer",
    city: "Pune",
    salary: 920000,
    yearsExperience: 4,
    employmentStatus: "Active",
    managerId: 1
  },
  {
    employeeId: 3,
    fullName: "Sara Khan",
    department: "Engineering",
    jobTitle: "Data Engineer",
    city: "Hyderabad",
    salary: 1180000,
    yearsExperience: 6,
    employmentStatus: "Active",
    managerId: 1
  },
  {
    employeeId: 4,
    fullName: "Vikram Singh",
    department: "Finance",
    jobTitle: "Financial Analyst",
    city: "Mumbai",
    salary: 840000,
    yearsExperience: 5,
    employmentStatus: "Active",
    managerId: null
  },
  {
    employeeId: 5,
    fullName: "Neha Sharma",
    department: "Product",
    jobTitle: "Product Manager",
    city: "Delhi",
    salary: 1320000,
    yearsExperience: 7,
    employmentStatus: "Active",
    managerId: null
  },
  {
    employeeId: 6,
    fullName: "Arjun Nair",
    department: "Engineering",
    jobTitle: "QA Engineer",
    city: "Kochi",
    salary: 760000,
    yearsExperience: 3,
    employmentStatus: "On Leave",
    managerId: 1
  },
  {
    employeeId: 7,
    fullName: "Meera Iyer",
    department: "Sales",
    jobTitle: "Account Executive",
    city: "Chennai",
    salary: 680000,
    yearsExperience: 2,
    employmentStatus: "Active",
    managerId: null
  },
  {
    employeeId: 8,
    fullName: "Kabir Das",
    department: "Engineering",
    jobTitle: "Platform Engineer",
    city: "Noida",
    salary: 1250000,
    yearsExperience: 7,
    employmentStatus: "Active",
    managerId: 1
  },
  {
    employeeId: 9,
    fullName: "Pooja Verma",
    department: "HR",
    jobTitle: "People Operations Specialist",
    city: "Lucknow",
    salary: 620000,
    yearsExperience: 3,
    employmentStatus: "Active",
    managerId: null
  },
  {
    employeeId: 10,
    fullName: "Dev Malhotra",
    department: "Finance",
    jobTitle: "Senior Financial Analyst",
    city: "Mumbai",
    salary: 1090000,
    yearsExperience: 9,
    employmentStatus: "Inactive",
    managerId: 4
  },
  {
    employeeId: 11,
    fullName: "Ishita Bose",
    department: "Product",
    jobTitle: "Product Analyst",
    city: "Kolkata",
    salary: 880000,
    yearsExperience: 3,
    employmentStatus: "Active",
    managerId: 5
  },
  {
    employeeId: 12,
    fullName: "Rahul Joshi",
    department: "Sales",
    jobTitle: "Sales Operations Analyst",
    city: "Jaipur",
    salary: 720000,
    yearsExperience: 4,
    employmentStatus: "Active",
    managerId: 7
  }
];

const projects = [
  {
    projectId: 101,
    projectName: "Cloud Migration",
    department: "Engineering",
    status: "Active",
    budget: 2800000
  },
  {
    projectId: 102,
    projectName: "Risk Analytics",
    department: "Finance",
    status: "Active",
    budget: 1600000
  },
  {
    projectId: 103,
    projectName: "Customer Portal",
    department: "Product",
    status: "Completed",
    budget: 2200000
  },
  {
    projectId: 104,
    projectName: "Security Hardening",
    department: "Engineering",
    status: "Active",
    budget: 1900000
  }
];

const employeeProjects = [
  { employeeId: 1, projectId: 101, assignedRole: "Technical Lead" },
  { employeeId: 2, projectId: 101, assignedRole: "Backend Developer" },
  { employeeId: 3, projectId: 101, assignedRole: "Data Engineer" },
  { employeeId: 13, projectId: 104, assignedRole: "Security Lead" },
  { employeeId: 1, projectId: 104, assignedRole: "Engineering Sponsor" },
  { employeeId: 4, projectId: 102, assignedRole: "Project Analyst" },
  { employeeId: 10, projectId: 102, assignedRole: "Senior Analyst" }
];

function cloneRows(rows) {
  return rows.map((row) => ({ ...row }));
}

function projectRows(rows, selectors) {
  /*
   * SELECT is projection: after the source rows are chosen, selectors decide
   * what values become columns in the result.
   */
  return rows.map((row) => {
    const projected = {};
    for (const [alias, selector] of Object.entries(selectors)) {
      projected[alias] = selector(row);
    }
    return projected;
  });
}

function where(rows, predicate) {
  /*
   * WHERE keeps rows for which the predicate evaluates to true.
   * Undefined or null results are not treated as a match.
   */
  return rows.filter((row) => predicate(row) === true);
}

function distinct(rows) {
  const seen = new Set();

  return rows.filter((row) => {
    const key = JSON.stringify(row);

    if (seen.has(key)) {
      return false;
    }

    seen.add(key);
    return true;
  });
}

function orderBy(rows, field, direction = "ASC") {
  const multiplier = direction.toUpperCase() === "DESC" ? -1 : 1;

  return [...rows].sort((left, right) => {
    const a = left[field];
    const b = right[field];

    if (a === b) {
      return 0;
    }

    if (a === null || a === undefined) {
      return -1 * multiplier;
    }

    if (b === null || b === undefined) {
      return 1 * multiplier;
    }

    return (a < b ? -1 : 1) * multiplier;
  });
}

function limit(rows, count) {
  if (!Number.isInteger(count) || count < 0) {
    throw new RangeError("LIMIT must be a non-negative integer");
  }

  return rows.slice(0, count);
}

function sqlLike(value, pattern) {
  /*
   * SQL LIKE uses % for any sequence and _ for a single character.
   * This implementation converts those operators to a regular expression
   * while escaping ordinary regex metacharacters.
   */
  if (value === null || value === undefined) {
    return false;
  }

  let expression = "^";

  for (const character of pattern) {
    if (character === "%") {
      expression += ".*";
    } else if (character === "_") {
      expression += ".";
    } else {
      expression += character.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }
  }

  expression += "$";

  return new RegExp(expression, "i").test(String(value));
}

function sqlIn(value, values) {
  /*
   * SQL IN checks membership against the supplied value set.
   * JavaScript's Set provides efficient repeated membership tests.
   */
  return values.includes(value);
}

function sqlBetween(value, lower, upper) {
  /*
   * BETWEEN is inclusive at both boundaries.
   */
  return value >= lower && value <= upper;
}

function printTable(title, rows) {
  console.log(`\n--- ${title} ---`);

  if (rows.length === 0) {
    console.log("(no rows)");
    return;
  }

  console.table(rows);
}

function selectFromEmployees() {
  const result = projectRows(cloneRows(employees), {
    employee_id: (row) => row.employeeId,
    full_name: (row) => row.fullName,
    department: (row) => row.department
  });

  printTable("SELECT specific columns FROM employees", result);
}

function selectCalculatedColumns() {
  const result = projectRows(
    where(employees, (row) => row.employmentStatus === "Active"),
    {
      employee: (row) => row.fullName,
      role: (row) => row.jobTitle,
      salary: (row) => row.salary,
      estimated_bonus: (row) => row.salary * 0.10
    }
  );

  printTable("Aliases and calculated columns", result);
}

function basicWherePredicates() {
  const highSalary = where(
    employees,
    (row) => row.salary >= 1200000
  );

  printTable(
    "WHERE salary >= 1200000",
    projectRows(highSalary, {
      name: (row) => row.fullName,
      salary: (row) => row.salary
    })
  );

  const engineeringExperts = where(
    employees,
    (row) =>
      row.department === "Engineering" &&
      row.yearsExperience >= 7
  );

  printTable(
    "Engineering employees with seven or more years",
    projectRows(engineeringExperts, {
      name: (row) => row.fullName,
      experience: (row) => row.yearsExperience
    })
  );

  const financeOrProduct = where(
    employees,
    (row) =>
      row.department === "Finance" ||
      row.department === "Product"
  );

  printTable(
    "Finance OR Product",
    projectRows(financeOrProduct, {
      name: (row) => row.fullName,
      department: (row) => row.department
    })
  );
}

function membershipAndPatterns() {
  const selectedCities = where(
    employees,
    (row) => sqlIn(row.city, ["Mumbai", "Bengaluru", "Pune"])
  );

  printTable(
    "IN selected cities",
    projectRows(selectedCities, {
      name: (row) => row.fullName,
      city: (row) => row.city
    })
  );

  const salaryRange = where(
    employees,
    (row) => sqlBetween(row.salary, 800000, 1200000)
  );

  printTable(
    "BETWEEN salary range",
    projectRows(salaryRange, {
      name: (row) => row.fullName,
      salary: (row) => row.salary
    })
  );

  const engineers = where(
    employees,
    (row) => sqlLike(row.jobTitle, "%Engineer%")
  );

  printTable(
    "LIKE '%Engineer%'",
    projectRows(engineers, {
      name: (row) => row.fullName,
      role: (row) => row.jobTitle
    })
  );
}

function nullSemantics() {
  const missingManagers = where(
    employees,
    (row) => row.managerId === null
  );

  printTable(
    "IS NULL equivalent",
    projectRows(missingManagers, {
      name: (row) => row.fullName,
      manager_id: (row) => row.managerId
    })
  );

  const assignedManagers = where(
    employees,
    (row) => row.managerId !== null
  );

  printTable(
    "IS NOT NULL equivalent",
    projectRows(assignedManagers, {
      name: (row) => row.fullName,
      manager_id: (row) => row.managerId
    })
  );

  /*
   * JavaScript's null equality is not identical to SQL's three-valued logic.
   * This explicit check keeps the simulation clear: a missing SQL value must
   * be tested using an IS NULL-style predicate rather than normal comparison.
   */
  const incorrectNullComparison = where(
    employees,
    (row) => row.managerId === undefined
  );

  printTable(
    "A deliberately different missing-value test",
    incorrectNullComparison
  );
}

function logicalPrecedence() {
  const withoutExplicitGrouping = where(
    employees,
    (row) =>
      (row.department === "Engineering" &&
        row.salary >= 1200000) ||
      row.department === "Product"
  );

  printTable(
    "Explicitly grouped Engineering OR Product rule",
    projectRows(withoutExplicitGrouping, {
      name: (row) => row.fullName,
      department: (row) => row.department,
      salary: (row) => row.salary
    })
  );
}

function distinctDepartments() {
  const departments = projectRows(employees, {
    department: (row) => row.department
  });

  printTable(
    "DISTINCT department",
    distinct(departments)
  );
}

function orderedAndLimitedQuery() {
  const activeEmployees = where(
    employees,
    (row) => row.employmentStatus === "Active"
  );

  const ordered = orderBy(
    activeEmployees,
    "salary",
    "DESC"
  );

  const highestPaid = limit(ordered, 5);

  printTable(
    "ORDER BY salary DESC LIMIT 5",
    projectRows(highestPaid, {
      name: (row) => row.fullName,
      salary: (row) => row.salary
    })
  );
}

function classifyCompensation() {
  const result = projectRows(employees, {
    name: (row) => row.fullName,
    salary: (row) => row.salary,
    compensation_band: (row) => {
      if (row.salary >= 1300000) {
        return "Senior compensation band";
      }

      if (row.salary >= 900000) {
        return "Mid compensation band";
      }

      return "Entry compensation band";
    }
  });

  printTable("CASE-style classification", result);
}

function parameterizedQuery(filters) {
  /*
   * A real SQL driver would bind values to placeholders such as $1, ?, or
   * named parameters. This function mirrors that separation: filters are
   * data, while the predicate structure is fixed by the application.
   */
  if (!Number.isInteger(filters.minimumSalary) || filters.minimumSalary < 0) {
    throw new TypeError("minimumSalary must be a non-negative integer");
  }

  if (typeof filters.department !== "string" || filters.department.length === 0) {
    throw new TypeError("department must be a non-empty string");
  }

  return where(
    employees,
    (row) =>
      row.department === filters.department &&
      row.salary >= filters.minimumSalary
  );
}

function safeDynamicOrdering(rows, requestedSort) {
  /*
   * A SQL parameter cannot safely substitute for a column identifier.
   * Applications that expose sorting controls should map user choices to
   * a fixed allow-list rather than inserting arbitrary SQL text.
   */
  const allowedColumns = {
    name: "fullName",
    salary: "salary",
    experience: "yearsExperience"
  };

  const selectedColumn = allowedColumns[requestedSort];

  if (!selectedColumn) {
    throw new Error("Unsupported sort field");
  }

  return orderBy(rows, selectedColumn, "DESC");
}

function joinActiveProjects() {
  /*
   * This is a small relational join demonstration. SQL JOIN combines rows
   * using key relationships rather than copying project information into
   * every employee record.
   */
  const activeProjects = projects.filter(
    (project) => project.status === "Active"
  );

  const result = [];

  for (const assignment of employeeProjects) {
    const employee = employees.find(
      (candidate) => candidate.employeeId === assignment.employeeId
    );

    const project = activeProjects.find(
      (candidate) => candidate.projectId === assignment.projectId
    );

    if (employee && project) {
      result.push({
        employee: employee.fullName,
        project: project.projectName,
        role: assignment.assignedRole,
        project_status: project.status
      });
    }
  }

  printTable("JOIN + WHERE active projects", result);
}

function inspectQueryShape() {
  /*
   * Thinking in relational stages is useful even before a query becomes
   * complex:
   *
   * FROM -> establishes the source rows
   * WHERE -> removes rows that do not satisfy the predicate
   * SELECT -> projects the remaining rows
   */
  const sourceRows = cloneRows(employees);

  const filteredRows = where(
    sourceRows,
    (row) =>
      row.department === "Finance" &&
      row.employmentStatus === "Active" &&
      row.salary > 800000
  );

  const projectedRows = projectRows(filteredRows, {
    employee: (row) => row.fullName,
    annual_salary: (row) => row.salary,
    monthly_salary: (row) => Math.round(row.salary / 12)
  });

  printTable("FROM -> WHERE -> SELECT", projectedRows);
}

function createAsyncQueryExecutor() {
  /*
   * Node.js applications frequently execute database operations
   * asynchronously. A Promise-based interface prevents blocking application
   * code while a real database driver waits for I/O.
   */
  return async function executeAsync(operation) {
    await new Promise((resolve) => setTimeout(resolve, 5));
    return operation();
  };
}

async function runAsyncExamples() {
  const executeAsync = createAsyncQueryExecutor();

  const result = await executeAsync(() =>
    parameterizedQuery({
      department: "Engineering",
      minimumSalary: 1000000
    })
  );

  printTable(
    "Asynchronous parameterized query",
    projectRows(result, {
      name: (row) => row.fullName,
      department: (row) => row.department,
      salary: (row) => row.salary
    })
  );
}

async function main() {
  console.log("SQL FUNDAMENTALS");
  console.log("================");
  console.log(
    "Focus: SELECT, FROM, WHERE and the mechanics surrounding basic queries."
  );

  selectFromEmployees();
  selectCalculatedColumns();
  basicWherePredicates();
  membershipAndPatterns();
  nullSemantics();
  logicalPrecedence();
  distinctDepartments();
  orderedAndLimitedQuery();
  classifyCompensation();
  joinActiveProjects();
  inspectQueryShape();

  try {
    const filtered = parameterizedQuery({
      department: "Engineering",
      minimumSalary: 1100000
    });

    printTable(
      "Validated parameterized filter",
      projectRows(filtered, {
        name: (row) => row.fullName,
        salary: (row) => row.salary
      })
    );
  } catch (error) {
    console.error(`Query validation failed: ${error.message}`);
  }

  try {
    const sorted = safeDynamicOrdering(
      employees,
      "salary"
    );

    printTable(
      "Allow-listed dynamic ordering",
      projectRows(limit(sorted, 3), {
        name: (row) => row.fullName,
        salary: (row) => row.salary
      })
    );
  } catch (error) {
    console.error(`Ordering failed: ${error.message}`);
  }

  try {
    safeDynamicOrdering(employees, "salary; DROP TABLE employees;");
  } catch (error) {
    console.error(
      `Rejected unsafe sort selection: ${error.message}`
    );
  }

  await runAsyncExamples();

  console.log("\nJavaScript SQL fundamentals demonstrations completed.");
}

main().catch((error) => {
  console.error("Fatal execution error:", error);
  process.exitCode = 1;
});
