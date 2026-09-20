<!-- File: README.md -->

# Statistical Thinking for Business Decisions

## Project purpose

Statistical thinking is the practice of using data, variation, probability, uncertainty, and evidence to improve business decisions.

A business dataset is not automatically a source of certainty. Sales vary between periods. Customers behave differently. Experiments produce different outcomes when repeated. Measurements contain noise. Samples represent larger populations imperfectly.

This repository implements those ideas as a practical educational software project.

The project contains:

- Python statistical calculations and business metrics
- a command-line interface
- unit tests
- an interactive browser dashboard
- a C++ statistical implementation
- CMake build configuration
- Docker support
- automated GitHub Actions validation

The implementations intentionally make the statistical mechanics visible instead of hiding them behind a large analytics framework.

## Repository structure

    .
    ├── .github/
    │   └── workflows/
    │       └── ci.yml
    ├── cpp/
    │   └── statistical_decision.cpp
    ├── src/
    │   └── statistical_business/
    │       ├── __init__.py
    │       ├── business.py
    │       ├── cli.py
    │       └── core.py
    ├── tests/
    │   └── test_core.py
    ├── web/
    │   ├── app.js
    │   ├── index.html
    │   └── styles.css
    ├── CMakeLists.txt
    ├── Dockerfile
    ├── README.md
    ├── pyproject.toml
    ├── requirements.txt
    └── .gitignore

## Prerequisites

Python 3.11 or newer is required for the Python implementation.

C++17 and CMake 3.20 or newer are required for the C++ implementation.

A modern browser is required for the interactive dashboard.

Docker is optional.

## Installation

Create a virtual environment:

    python -m venv .venv

On Windows PowerShell:

    .venv\Scripts\Activate.ps1

On macOS or Linux:

    source .venv/bin/activate

Install the project and development dependencies:

    python -m pip install -e ".[dev]"

## Running the Python implementation

Display descriptive statistics:

    python -m statistical_business.cli describe 120 135 128 142 155 149 131 160

Calculate correlation:

    python -m statistical_business.cli correlation --x 10 12 11 14 16 15 12 17 --y 120 135 128 142 155 149 131 160

Fit a simple regression model and predict the next observation:

    python -m statistical_business.cli regression --x 1 2 3 4 5 --y 100 110 118 130 137 --predict 6

Analyze an A/B conversion experiment:

    python -m statistical_business.cli ab-test --control-conversions 100 --control-visitors 1000 --treatment-conversions 130 --treatment-visitors 1000

Estimate discounted customer lifetime value:

    python -m statistical_business.cli clv --order-value 100 --frequency 4 --margin 0.4 --retention 0.8

## Running the tests

Run the complete Python test suite:

    pytest

Run lint checks:

    ruff check .

## Browser dashboard

The frontend is a static application.

From the repository root, start a local server:

    python -m http.server 8080 --directory web

Open:

    http://localhost:8080

Enter comma-separated business observations such as revenue, order values, response times, or customer counts.

The dashboard calculates the count, mean, median, minimum, maximum, and standard deviation and displays the observations visually.

The dashboard deliberately separates description from inference. A graph showing variation does not establish why that variation occurred.

## C++ implementation

Configure the project:

    cmake -S . -B build

Build it:

    cmake --build build --config Release

On Linux or macOS, run:

    ./build/statistical_business

On Windows with a Visual Studio generator, run the executable from the generated build directory.

The C++ program demonstrates descriptive statistics and correlation using the standard library.

## Core statistical concepts

### Population and sample

A population is the complete set of units relevant to a question.

A sample is the subset actually observed.

For example, a retailer may have millions of customers but analyze the behavior of 20,000 sampled customers.

A sample statistic describes the observed sample. A population parameter describes the underlying population.

This distinction matters because a sample can differ from the population simply because of sampling variation.

### Mean

The arithmetic mean is:

    mean = sum of observations / number of observations

For example, observations 10, 20, and 30 have a mean of 20.

The mean uses every observation but can be strongly affected by extreme values.

### Median

The median is the middle value after sorting.

For 10, 20, 30, 40, the median is 25.

The median is often useful for highly skewed business measurements such as salaries, order values, or transaction amounts.

### Variation

Two businesses can have the same average but very different levels of consistency.

Standard deviation measures the typical scale of deviation from the mean under the selected definition.

A low standard deviation does not mean that a process is good. It only describes lower observed dispersion.

### Percentiles

Percentiles answer questions such as:

- What value is below 90% of observations?
- How large is a typical high-end transaction?
- How long do the slowest customer interactions take?

Percentiles are particularly useful for service-level analysis because averages can hide extreme observations.

### Correlation

Correlation measures the direction and strength of linear association between two variables.

A positive correlation means higher values of one variable tend to occur with higher values of the other.

A negative correlation means higher values of one variable tend to occur with lower values of the other.

A correlation close to zero means there is little linear association.

Correlation does not prove causation.

For example, marketing spending and sales may rise together because both increase during seasonal periods. A correlation alone cannot establish that marketing spending caused every observed sales increase.

### Covariance

Covariance measures whether two variables tend to move together.

Its numerical magnitude depends on the units of measurement, which makes it less directly interpretable than correlation for many business comparisons.

### Regression

Simple linear regression represents a relationship as:

    y = intercept + slope × x

The slope describes the estimated change in y for a one-unit increase in x within the fitted model.

R-squared describes the proportion of observed variation in the response represented by the fitted linear relationship.

R-squared is not a proof of causality and should not be interpreted as a percentage of future business performance guaranteed by the predictor.

## Probability and expected value

Expected value combines possible outcomes and their probabilities:

    E(X) = sum(outcome × probability)

Suppose a decision has two possible financial outcomes:

    gain = 100
    probability of gain = 0.25

    loss = 0
    probability of loss = 0.75

The expected value is 25.

Expected value is not a promise that 25 will occur. It is a probability-weighted long-run average under the stated model.

Business decisions should also consider variance, downside exposure, cash requirements, timing, constraints, and model assumptions.

## Confidence intervals

A confidence interval represents uncertainty around an estimate.

The project includes a simple proportion confidence interval for educational purposes.

For a conversion rate:

    conversion rate = conversions / visitors

The observed conversion rate is an estimate. Another sample may produce a different rate.

A confidence interval communicates a range of plausible population values under the assumptions of the method.

A confidence interval should not be described as the probability that a fixed population parameter is inside that particular interval.

For small samples or extreme proportions, alternative methods such as Wilson or exact intervals can be more appropriate than the simple Wald interval implemented here.

## Hypothesis testing

An A/B test compares outcomes from two groups.

The project implements a two-proportion z test.

The null hypothesis is that the two population conversion proportions are equal.

The test produces a z statistic and a p-value.

A small p-value indicates that the observed difference would be relatively unusual under the null hypothesis, subject to the assumptions of the test.

Statistical significance does not automatically mean:

- the change is large
- the change is profitable
- the result will repeat
- customers prefer the change
- the experiment measured the correct business outcome

Business significance and statistical significance are different concepts.

## Effect size

Suppose conversion changes from 10% to 13%.

The absolute lift is:

    13% - 10% = 3 percentage points

The relative lift is:

    (13% - 10%) / 10% = 30%

These describe the same observed difference in different ways.

Percentage points and percent change must not be confused.

## Customer lifetime value

The project uses a simplified discounted customer lifetime value model.

The annual contribution is approximately:

    average order value × purchase frequency × gross margin

Future contribution is adjusted using retention and discounting.

The estimate is only as useful as its assumptions.

Real customer economics may require:

- acquisition cost
- cohort-specific retention
- churn timing
- refunds
- variable service costs
- discounting
- expansion revenue
- contract duration
- customer segmentation

A single CLV number can conceal substantial heterogeneity.

## Forecasting

The repository includes a simple linear regression forecast.

A trend line can provide a useful baseline, but forecasting is more difficult than extending a historical line.

Real forecasting work can require:

- seasonality
- calendar effects
- promotions
- structural breaks
- changing customer behavior
- missing data
- external variables
- uncertainty intervals
- backtesting

A model that fits historical data well can still forecast poorly.

## Sampling and bias

Statistical thinking starts before calculation.

Important questions include:

- Who was measured?
- Who was not measured?
- How were observations selected?
- Did non-response affect the sample?
- Were measurements collected consistently?
- Is the sample representative of the decision population?
- Could the data-generation process itself create bias?

A mathematically correct calculation on biased data can still produce a misleading business decision.

## Confounding

A confounder is a variable associated with both the apparent cause and the outcome.

Suppose stores that spend more on advertising also tend to be larger.

If those stores generate more sales, store size may help explain the relationship.

Without controlling for relevant factors or using a suitable experimental design, it is difficult to interpret the observed association causally.

## Experiments versus observational data

Observational data records what happened without assigning treatment.

Experiments deliberately assign different conditions to groups.

Randomized experiments can reduce confounding because treatment assignment is randomized.

Even experiments require careful design.

Important considerations include:

- randomization
- control groups
- sample size
- primary outcome
- experiment duration
- contamination
- novelty effects
- multiple testing
- stopping rules
- practical effect size

## Statistical significance versus business significance

Consider a product experiment that increases conversion by 0.05 percentage points.

A large sample could make that difference statistically detectable.

The business question remains:

- How much revenue does the change produce?
- What implementation cost is required?
- Does it affect retention?
- Does it increase refunds?
- Does it affect another important customer metric?
- Is the effect stable across important segments?

Statistical evidence informs the decision. It does not replace business judgment.

## Common mistakes

### Using the mean for heavily skewed data

A few unusually large transactions can pull the average upward.

Inspect the median and distribution as well.

### Treating correlation as causation

Two variables can move together because of seasonality, a third variable, reverse causality, or coincidence.

### Ignoring sample size

A percentage calculated from 20 observations and the same percentage calculated from 2 million observations do not carry the same amount of sampling information.

### Repeatedly checking an experiment

Repeatedly looking at results and stopping whenever a desired p-value appears can alter the statistical properties of the procedure.

### Ignoring multiple comparisons

Testing many hypotheses increases the chance of obtaining at least one apparently unusual result by chance.

### Focusing only on p-values

A p-value does not tell you whether an effect is commercially meaningful.

### Ignoring missing data

Missing observations may not be random. The reason data is missing can itself contain information.

### Treating dashboards as evidence of causality

A dashboard can display relationships, but visualization does not establish causal mechanisms.

## Edge cases handled by the implementation

The Python implementation validates:

- empty datasets
- insufficient observations
- mismatched series lengths
- zero-variance variables
- invalid probabilities
- invalid sample counts
- invalid confidence levels
- invalid A/B test counts
- invalid retention rates
- invalid moving-average windows
- invalid regression predictors

Explicit exceptions make invalid analytical assumptions visible instead of silently producing misleading numbers.

## Performance considerations

Most calculations in the Python implementation process n observations in O(n) time.

Median and percentile calculations sort the data and therefore require O(n log n) time in their current implementation.

The memory requirement is generally O(n) because the implementation materializes input sequences for validation and calculations.

For very large datasets, a production analytics system would normally process data in a database, distributed computation engine, columnar analytics system, or streaming pipeline rather than loading the complete dataset into a small application process.

Performance should be measured against actual workload characteristics instead of assumed from the algorithm alone.

## Security considerations

This project does not require credentials.

Production statistical systems should consider:

- access control for sensitive datasets
- encryption in transit and at rest
- removal or masking of personal identifiers
- audit logging
- controlled database permissions
- dependency management
- validation of uploaded files
- limits on computationally expensive inputs
- safe error messages

Statistical analysis does not remove data-protection obligations.

## Docker

Build the image:

    docker build -t statistical-business .

Run the CLI:

    docker run --rm statistical-business

The container creates a non-root application user and contains only the Python runtime components required by the CLI.

## CI/CD

The GitHub Actions workflow checks three independent areas.

Python validation installs the package, runs Ruff, and executes pytest.

C++ validation configures and builds the CMake project and executes the resulting program.

Frontend validation confirms that the required static application files exist.

No deployment credentials are stored in the repository.

## Production considerations

A production statistical decision system should separate:

1. data collection
2. data validation
3. transformation
4. statistical analysis
5. uncertainty estimation
6. business interpretation
7. decision recording
8. monitoring
9. retrospective evaluation

The analysis code should be version controlled together with its input definitions and assumptions.

Important decisions should preserve the population definition, observation window, filters, transformations, model version, and statistical method.

Reproducibility is particularly important when analysis influences financial, operational, customer, or regulatory decisions.

## Limitations

This repository is an educational implementation.

The simple confidence interval and two-proportion z test are intentionally transparent rather than a complete statistical inference library.

The linear forecast is a baseline and does not model seasonality or complex time-series behavior.

The CLV implementation uses simplified assumptions.

The browser dashboard is a client-side demonstration and does not provide authentication, persistent storage, or a production data-ingestion service.

The examples do not establish causal relationships merely because statistical calculations are available.

The appropriate method for a production decision depends on the data-generating process, measurement design, sample size, assumptions, and decision objective.
