"use strict";

/*
 * Root Cause Analysis:
 * - Five Whys models a causal chain.
 * - Fishbone branches separate possible causes by category.
 * - Evidence scoring prevents an attractive hypothesis from being treated
 *   as proven without supporting observations.
 * - The diagnostic engine evaluates hypotheses and proposed corrective
 *   actions without confusing symptoms with causes.
 */

const CauseCategory = Object.freeze({
  PEOPLE: "People",
  PROCESS: "Process",
  TECHNOLOGY: "Technology",
  DATA: "Data",
  ENVIRONMENT: "Environment",
  MANAGEMENT: "Management"
});

const EvidenceStrength = Object.freeze({
  WEAK: 1,
  MODERATE: 2,
  STRONG: 3
});

class Evidence {
  constructor(observation, source, strength) {
    if (!observation?.trim() || !source?.trim()) {
      throw new Error("Evidence requires an observation and source.");
    }

    if (!Object.values(EvidenceStrength).includes(strength)) {
      throw new Error("Invalid evidence strength.");
    }

    this.observation = observation;
    this.source = source;
    this.strength = strength;
  }
}

class Cause {
  constructor(statement, category, evidence = []) {
    if (!statement?.trim()) {
      throw new Error("Cause statement cannot be empty.");
    }

    if (!Object.values(CauseCategory).includes(category)) {
      throw new Error("Invalid cause category.");
    }

    this.statement = statement;
    this.category = category;
    this.evidence = [...evidence];
    this.children = [];
  }

  addChild(child) {
    if (!(child instanceof Cause)) {
      throw new TypeError("A fishbone child must be a Cause.");
    }

    this.children.push(child);
  }

  get evidenceScore() {
    return this.evidence.reduce(
      (total, evidence) => total + evidence.strength,
      0
    );
  }
}

class FiveWhys {
  constructor(problem) {
    this.problem = problem;
    this.steps = [];
  }

  addStep(question, answer, evidence = []) {
    if (!question?.trim() || !answer?.trim()) {
      throw new Error("Each Why requires a question and answer.");
    }

    if (this.steps.length >= 5) {
      throw new Error("Five Whys cannot contain more than five causal levels.");
    }

    this.steps.push({
      question,
      answer,
      evidence: [...evidence]
    });
  }

  get rootCause() {
    if (this.steps.length === 0) {
      throw new Error("No Why analysis has been recorded.");
    }

    return this.steps[this.steps.length - 1].answer;
  }
}

class RCAEngine {
  constructor(problem) {
    if (!problem?.trim()) {
      throw new Error("Problem statement is required.");
    }

    this.problem = problem;
    this.whys = new FiveWhys(problem);
    this.fishbone = new Map();
    this.hypotheses = [];
    this.actions = [];
  }

  addFishboneCause(cause) {
    this.fishbone.set(cause.category, cause);
  }

  addHypothesis(cause) {
    this.hypotheses.push(cause);
  }

  addAction(action) {
    if (
      !action?.name?.trim() ||
      !action?.owner?.trim() ||
      typeof action.measure !== "function"
    ) {
      throw new Error("Corrective actions require a name, owner and measure.");
    }

    this.actions.push(action);
  }

  rankHypotheses() {
    return [...this.hypotheses].sort(
      (a, b) => b.evidenceScore - a.evidenceScore
    );
  }

  evaluateActions(observations) {
    return this.actions.map(action => ({
      name: action.name,
      owner: action.owner,
      verified: Boolean(action.measure(observations))
    }));
  }

  renderReport() {
    console.log("\nROOT CAUSE ANALYSIS");
    console.log("=".repeat(70));
    console.log(`Problem: ${this.problem}`);

    console.log("\n5 WHYS");
    console.log("-".repeat(70));

    this.whys.steps.forEach((step, index) => {
      console.log(`Why ${index + 1}: ${step.question}`);
      console.log(`Answer: ${step.answer}`);

      step.evidence.forEach(item => {
        console.log(
          `  Evidence: ${item.observation} [${item.source}]`
        );
      });
    });

    console.log("\nFISHBONE");
    console.log("-".repeat(70));

    for (const [category, cause] of this.fishbone) {
      console.log(`[${category}] ${cause.statement}`);
      cause.evidence.forEach(item => {
        console.log(`  - ${item.observation}`);
      });

      cause.children.forEach(child => {
        console.log(`  -> ${child.statement}`);
      });
    }

    console.log("\nHYPOTHESIS RANKING");
    console.log("-".repeat(70));

    this.rankHypotheses().forEach((cause, index) => {
      console.log(
        `${index + 1}. ${cause.statement} | score=${cause.evidenceScore}`
      );
    });
  }
}

function average(values) {
  if (!Array.isArray(values) || values.length === 0) {
    throw new Error("At least one numeric measurement is required.");
  }

  if (!values.every(Number.isFinite)) {
    throw new Error("Measurements must contain finite numbers.");
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function verifyReduction(before, after) {
  return average(after) < average(before);
}

function groupFailureSignals(events) {
  const counts = new Map();

  for (const event of events) {
    if (typeof event !== "string" || !event.trim()) {
      continue;
    }

    const key = event.trim().toLowerCase();
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

function delay(milliseconds) {
  return new Promise(resolve => setTimeout(resolve, milliseconds));
}

async function investigateIncident(engine) {
  /*
   * The asynchronous investigation models evidence arriving from
   * independent operational sources. Promise.all prevents one source
   * from being silently ignored.
   */
  const [metrics, logs, tests] = await Promise.all([
    delay(40).then(() => ({
      poolUtilization: 100,
      connectionGrowth: "continuous"
    })),
    delay(20).then(() => ({
      repeatedError: "connection pool exhausted"
    })),
    delay(30).then(() => ({
      resourceLifecycleCoverage: false
    }))
  ]);

  engine.addAction({
    name: "Add connection-lifecycle regression test",
    owner: "Platform Engineering",
    measure: observations =>
      observations.tests.resourceLifecycleCoverage === true
  });

  return { metrics, logs, tests };
}

async function main() {
  const engine = new RCAEngine(
    "Production payment requests failed for 17 minutes after deployment."
  );

  engine.whys.addStep(
    "Why did payment requests fail?",
    "The service exhausted its database connection pool.",
    [
      new Evidence(
        "Connection-pool utilization reached 100%.",
        "metrics",
        EvidenceStrength.STRONG
      )
    ]
  );

  engine.whys.addStep(
    "Why was the connection pool exhausted?",
    "A new endpoint failed to release database connections reliably.",
    [
      new Evidence(
        "Connections increased with every repeated request.",
        "database telemetry",
        EvidenceStrength.STRONG
      )
    ]
  );

  engine.whys.addStep(
    "Why could the endpoint reach production with that defect?",
    "Tests did not exercise repeated requests under resource pressure.",
    [
      new Evidence(
        "The existing suite covered only successful single requests.",
        "test suite",
        EvidenceStrength.STRONG
      )
    ]
  );

  engine.whys.addStep(
    "Why were resource-pressure tests missing?",
    "Acceptance criteria measured API responses but not resource lifecycle behavior.",
    [
      new Evidence(
        "No test asserted connection count before and after repeated calls.",
        "test design",
        EvidenceStrength.MODERATE
      )
    ]
  );

  engine.whys.addStep(
    "Why did acceptance criteria omit resource lifecycle?",
    "The engineering delivery process did not require operational-resource checks for database-backed endpoints.",
    [
      new Evidence(
        "Release checklist contained functional checks only.",
        "release process",
        EvidenceStrength.MODERATE
      )
    ]
  );

  const processCause = new Cause(
    "Release acceptance omitted resource-lifecycle verification.",
    CauseCategory.PROCESS,
    [
      new Evidence(
        "Deployment checklist had no connection-pressure test.",
        "release checklist",
        EvidenceStrength.STRONG
      )
    ]
  );

  const technologyCause = new Cause(
    "The client allowed unreleased connections to accumulate.",
    CauseCategory.TECHNOLOGY,
    [
      new Evidence(
        "Pool reached its configured maximum.",
        "database metrics",
        EvidenceStrength.STRONG
      )
    ]
  );

  const dataCause = new Cause(
    "Monitoring detected saturation but not the earlier growth pattern.",
    CauseCategory.DATA,
    [
      new Evidence(
        "Alert threshold was based on saturation.",
        "monitoring configuration",
        EvidenceStrength.MODERATE
      )
    ]
  );

  engine.addFishboneCause(processCause);
  engine.addFishboneCause(technologyCause);
  engine.addFishboneCause(dataCause);

  engine.addHypothesis(processCause);
  engine.addHypothesis(technologyCause);
  engine.addHypothesis(dataCause);

  const observations = await investigateIncident(engine);

  engine.renderReport();

  console.log("\nASYNC EVIDENCE");
  console.log("-".repeat(70));
  console.log(JSON.stringify(observations, null, 2));

  console.log("\nCORRECTIVE ACTION VERIFICATION");
  console.log("-".repeat(70));

  const actionResults = engine.evaluateActions(observations);
  for (const result of actionResults) {
    console.log(
      `${result.name}: ${result.verified ? "verified" : "not verified"}`
    );
  }

  console.log("\nMEASUREMENT VALIDATION");
  console.log("-".repeat(70));

  const before = [99, 103, 101, 100];
  const after = [71, 69, 73, 70];

  console.log(`Before average: ${average(before).toFixed(2)}`);
  console.log(`After average:  ${average(after).toFixed(2)}`);
  console.log(`Reduction verified: ${verifyReduction(before, after)}`);

  console.log("\nRECURRING FAILURE SIGNALS");
  console.log("-".repeat(70));

  const signals = groupFailureSignals([
    "connection leak",
    "timeout",
    "connection leak",
    "connection leak",
    "timeout",
    "slow query"
  ]);

  for (const [name, count] of signals) {
    console.log(`${name}: ${count}`);
  }

  console.log("\nROOT CAUSE");
  console.log("-".repeat(70));
  console.log(engine.whys.rootCause);
}

main().catch(error => {
  console.error(`Investigation failed: ${error.message}`);
  process.exitCode = 1;
});
