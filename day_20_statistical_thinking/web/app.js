// File: web/app.js

const state = {
    chart: null
};

function numbersFromInput(value) {
    const numbers = value
        .split(",")
        .map((item) => Number(item.trim()))
        .filter((item) => Number.isFinite(item));

    if (numbers.length < 2) {
        throw new Error("Enter at least two numeric observations.");
    }

    return numbers;
}

function mean(values) {
    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function median(values) {
    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);

    return sorted.length % 2 === 0
        ? (sorted[middle - 1] + sorted[middle]) / 2
        : sorted[middle];
}

function standardDeviation(values) {
    const average = mean(values);
    const variance =
        values.reduce((sum, value) => sum + (value - average) ** 2, 0) /
        values.length;

    return Math.sqrt(variance);
}

function describe(values) {
    return {
        count: values.length,
        mean: mean(values),
        median: median(values),
        minimum: Math.min(...values),
        maximum: Math.max(...values),
        standardDeviation: standardDeviation(values)
    };
}

function renderStatistics(statistics) {
    const output = document.querySelector("#statistics-output");

    output.innerHTML = Object.entries(statistics)
        .map(
            ([key, value]) => `
                <div class="metric">
                    <span>${key}</span>
                    <strong>${Number(value).toFixed(2)}</strong>
                </div>
            `
        )
        .join("");
}

function renderChart(values) {
    const canvas = document.querySelector("#business-chart");
    const context = canvas.getContext("2d");

    if (state.chart) {
        state.chart.destroy();
    }

    state.chart = new Chart(context, {
        type: "line",
        data: {
            labels: values.map((_, index) => `Observation ${index + 1}`),
            datasets: [
                {
                    label: "Business observations",
                    data: values,
                    tension: 0.25
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

document.querySelector("#analyze-form").addEventListener("submit", (event) => {
    event.preventDefault();

    const message = document.querySelector("#message");

    try {
        const values = numbersFromInput(
            document.querySelector("#observations").value
        );

        const statistics = describe(values);
        renderStatistics(statistics);
        renderChart(values);
        message.textContent =
            "Descriptive statistics describe the observed data. They do not, by themselves, establish causation.";
        message.className = "message success";
    } catch (error) {
        message.textContent = error.message;
        message.className = "message error";
    }
});
