'use strict';

const fs = require('node:fs/promises');

class Metric {
    constructor({ name, current, previous, target, unit = '' }) {
        if (typeof name !== 'string' || !name.trim()) {
            throw new Error('Metric name must be a non-empty string.');
        }

        for (const [key, value] of Object.entries({ current, previous, target })) {
            if (typeof value !== 'number' || !Number.isFinite(value)) {
                throw new Error(`${key} must be a finite number.`);
            }
        }

        this.name = name.trim();
        this.current = current;
        this.previous = previous;
        this.target = target;
        this.unit = unit;
    }

    get change() {
        return this.current - this.previous;
    }

    get changePercent() {
        if (this.previous === 0) {
            return this.current === 0 ? 0 : Infinity;
        }
        return (this.change / this.previous) * 100;
    }

    get targetGap() {
        return this.current - this.target;
    }
}

class InsightEngine {
    constructor(metrics) {
        if (!Array.isArray(metrics) || metrics.length === 0) {
            throw new Error('At least one metric is required.');
        }

        const names = new Set();

        for (const metric of metrics) {
            if (!(metric instanceof Metric)) {
                throw new Error('All items must be Metric objects.');
            }

            const normalized = metric.name.toLowerCase();
            if (names.has(normalized)) {
                throw new Error(`Duplicate metric: ${metric.name}`);
            }
            names.add(normalized);
        }

        this.metrics = metrics;
    }

    classify(metric) {
        const change = metric.changePercent;

        if (change <= -10) return 'critical';
        if (change < -3) return 'high';
        if (change >= 10) return 'high';
        if (change >= 3) return 'medium';
        return 'low';
    }

    createInsight(metric) {
        const priority = this.classify(metric);
        const change = metric.changePercent;

        let implication;
        let action;

        if (change <= -10) {
            implication =
                `${metric.name} has materially deteriorated and may create business risk.`;
            action =
                `Segment ${metric.name} by customer, channel, product, and period, then assign an owner to the largest driver.`;
        } else if (change < -3) {
            implication =
                `${metric.name} is declining enough to require targeted investigation.`;
            action =
                `Identify the main contributors to ${metric.name}'s decline before selecting a corrective action.`;
        } else if (change >= 10) {
            implication =
                `${metric.name} is improving strongly and may represent a scalable opportunity.`;
            action =
                `Identify the operating behavior responsible for the improvement and test whether it can be scaled.`;
        } else if (change >= 3) {
            implication =
                `${metric.name} is improving, but persistence and target attainment should be tested.`;
            action =
                `Monitor ${metric.name} across important segments and verify that the improvement is not isolated.`;
        } else {
            implication =
                `${metric.name} is relatively stable and currently provides a weaker decision signal.`;
            action =
                `Continue monitoring ${metric.name} while prioritizing stronger business signals.`;
        }

        return {
            metric: metric.name,
            priority,
            observation:
                `${metric.name} changed from ${metric.previous}${metric.unit} to ${metric.current}${metric.unit}.`,
            implication,
            action,
            evidence: {
                current: metric.current,
                previous: metric.previous,
                target: metric.target,
                change: metric.change,
                changePercent: Number(change.toFixed(2)),
                targetGap: metric.targetGap
            }
        };
    }

    generateStory() {
        const insights = this.metrics
            .map(metric => this.createInsight(metric))
            .sort((a, b) => {
                const rank = { critical: 0, high: 1, medium: 2, low: 3 };
                return rank[a.priority] - rank[b.priority];
            });

        const improved = this.metrics.filter(metric => metric.change > 0).length;
        const declined = this.metrics.filter(metric => metric.change < 0).length;
        const lead = insights[0];

        return {
            headline: lead.observation,
            narrative: {
                whatHappened: lead.observation,
                whyItMatters: lead.implication,
                whatToDo: lead.action
            },
            portfolioSignal: {
                improved,
                declined,
                stable: this.metrics.length - improved - declined
            },
            insights
        };
    }
}

class StoryDashboard {
    constructor(container) {
        this.container = container;
        this.engine = null;
    }

    load(metrics) {
        this.engine = new InsightEngine(metrics);
        this.render();
    }

    render() {
        const story = this.engine.generateStory();

        const cards = story.insights.map(insight => `
            <article class="insight-card">
                <h3>${escapeHtml(insight.metric)}</h3>
                <strong>${escapeHtml(insight.priority.toUpperCase())}</strong>
                <p><b>Observation:</b> ${escapeHtml(insight.observation)}</p>
                <p><b>Implication:</b> ${escapeHtml(insight.implication)}</p>
                <p><b>Action:</b> ${escapeHtml(insight.action)}</p>
            </article>
        `).join('');

        this.container.innerHTML = `
            <section>
                <h2>${escapeHtml(story.headline)}</h2>
                <p>${escapeHtml(story.narrative.whyItMatters)}</p>
                <p><b>Recommended action:</b> ${escapeHtml(story.narrative.whatToDo)}</p>
                <p>
                    Improved: ${story.portfolioSignal.improved},
                    Declined: ${story.portfolioSignal.declined},
                    Stable: ${story.portfolioSignal.stable}
                </p>
                ${cards}
            </section>
        `;
    }
}

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function parseCsv(text) {
    const lines = text.trim().split(/\r?\n/);
    if (lines.length < 2) {
        throw new Error('CSV requires a header and at least one record.');
    }

    const headers = lines[0].split(',').map(value => value.trim());
    const required = ['name', 'current', 'previous', 'target'];

    for (const field of required) {
        if (!headers.includes(field)) {
            throw new Error(`Missing CSV field: ${field}`);
        }
    }

    return lines.slice(1).map((line, index) => {
        const values = line.split(',').map(value => value.trim());

        if (values.length !== headers.length) {
            throw new Error(`Invalid CSV row ${index + 2}.`);
        }

        const row = Object.fromEntries(
            headers.map((header, position) => [header, values[position]])
        );

        return new Metric({
            name: row.name,
            current: Number(row.current),
            previous: Number(row.previous),
            target: Number(row.target),
            unit: row.unit || ''
        });
    });
}

async function saveStory(path, story) {
    await fs.writeFile(path, JSON.stringify(story, null, 2), 'utf8');
}

async function runNodeDemo() {
    const metrics = [
        new Metric({ name: 'Revenue', current: 12.4, previous: 10.8, target: 12.0, unit: 'M' }),
        new Metric({ name: 'Conversion Rate', current: 4.7, previous: 5.3, target: 5.0, unit: '%' }),
        new Metric({ name: 'Customer Retention', current: 91, previous: 88, target: 90, unit: '%' }),
        new Metric({ name: 'Support Cost', current: 1.9, previous: 1.6, target: 1.7, unit: 'M' }),
        new Metric({ name: 'Gross Margin', current: 37.5, previous: 35.8, target: 36, unit: '%' })
    ];

    const engine = new InsightEngine(metrics);
    const story = engine.generateStory();

    console.log('BUSINESS STORY');
    console.log('==============');
    console.log(story.headline);
    console.log(story.narrative.whyItMatters);
    console.log(`Action: ${story.narrative.whatToDo}`);

    for (const insight of story.insights) {
        console.log(`\n[${insight.priority.toUpperCase()}] ${insight.metric}`);
        console.log(insight.observation);
        console.log(insight.implication);
        console.log(`Action: ${insight.action}`);
    }

    await saveStory('business_story.json', story);
}

if (typeof window !== 'undefined') {
    window.BusinessStorytelling = {
        Metric,
        InsightEngine,
        StoryDashboard,
        parseCsv
    };
} else {
    runNodeDemo().catch(error => {
        console.error(`Story generation failed: ${error.message}`);
        process.exitCode = 1;
    });
}
