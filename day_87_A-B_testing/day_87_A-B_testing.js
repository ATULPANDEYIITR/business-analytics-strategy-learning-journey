'use strict';

const crypto = require('node:crypto');
const { EventEmitter } = require('node:events');

// ============================================================
// A/B TESTING: EVENT-DRIVEN EXPERIMENT MANAGEMENT
// ============================================================

const ExperimentStatus = Object.freeze({
    DRAFT: 'draft',
    RUNNING: 'running',
    COMPLETED: 'completed',
    STOPPED: 'stopped'
});

const Variant = Object.freeze({
    CONTROL: 'control',
    TREATMENT: 'treatment'
});

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}

class ExperimentError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ExperimentError';
    }
}

// Numerical approximation of the complementary error function.
function erfc(x) {
    const z = Math.abs(x);
    const t = 1 / (1 + z / 2);

    const answer = t * Math.exp(
        -z * z - 1.26551223 +
        t * (
            1.00002368 +
            t * (
                0.37409196 +
                t * (
                    0.09678418 +
                    t * (
                        -0.18628806 +
                        t * (
                            0.27886807 +
                            t * (
                                -1.13520398 +
                                t * (
                                    1.48851587 +
                                    t * (
                                        -0.82215223 +
                                        t * 0.17087277
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    );

    return x >= 0 ? answer : 2 - answer;
}

function normalCDF(x) {
    return 0.5 * erfc(-x / Math.sqrt(2));
}

function normalInverseCDF(p) {
    if (!(p > 0 && p < 1)) {
        throw new ValidationError('Probability must be between 0 and 1.');
    }

    // Acklam rational approximation.
    const a = [
        -39.6968302866538,
        220.946098424521,
        -275.928510446969,
        138.357751867269,
        -30.6647980661472,
        2.50662827745924
    ];

    const b = [
        -54.4760987982241,
        161.585836858041,
        -155.698979859887,
        66.8013118877197,
        -13.2806815528857
    ];

    const c = [
        -0.00778489400243029,
        -0.322396458041136,
        -2.40075827716184,
        -2.54973253934373,
        4.37466414146497,
        2.93816398269878
    ];

    const d = [
        0.00778469570904146,
        0.32246712907004,
        2.445134137143,
        3.75440866190742
    ];

    const low = 0.02425;
    const high = 1 - low;

    if (p < low) {
        const q = Math.sqrt(-2 * Math.log(p));

        return (
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        );
    }

    if (p > high) {
        const q = Math.sqrt(-2 * Math.log(1 - p));

        return -(
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        );
    }

    const q = p - 0.5;
    const r = q * q;

    return (
        (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
        (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    );
}

class ExperimentPolicy {
    constructor({
        allocationRatio = 0.5,
        alpha = 0.05,
        power = 0.80,
        minimumDetectableEffect = 0.02,
        baselineRate = 0.10
    } = {}) {
        if (!(allocationRatio > 0 && allocationRatio < 1)) {
            throw new ValidationError('Invalid allocation ratio.');
        }

        if (!(alpha > 0 && alpha < 1)) {
            throw new ValidationError('Invalid significance level.');
        }

        if (!(power > 0 && power < 1)) {
            throw new ValidationError('Invalid power.');
        }

        if (!(minimumDetectableEffect > 0 && minimumDetectableEffect < 1)) {
            throw new ValidationError('Invalid minimum detectable effect.');
        }

        if (!(baselineRate > 0 && baselineRate < 1)) {
            throw new ValidationError('Invalid baseline conversion rate.');
        }

        this.allocationRatio = allocationRatio;
        this.alpha = alpha;
        this.power = power;
        this.minimumDetectableEffect = minimumDetectableEffect;
        this.baselineRate = baselineRate;

        Object.freeze(this);
    }
}

class Experiment extends EventEmitter {
    constructor({ id, name, policy }) {
        super();

        if (!id || !name || !(policy instanceof ExperimentPolicy)) {
            throw new ValidationError('Experiment requires an ID, name and valid policy.');
        }

        this.id = id;
        this.name = name;
        this.policy = policy;
        this.status = ExperimentStatus.DRAFT;
        this.participants = new Map();
        this.outcomes = new Map();
        this.startedAt = null;
        this.completedAt = null;
    }

    start() {
        if (this.status !== ExperimentStatus.DRAFT) {
            throw new ExperimentError('Only draft experiments can start.');
        }

        this.status = ExperimentStatus.RUNNING;
        this.startedAt = new Date();

        this.emit('started', {
            experimentId: this.id,
            timestamp: this.startedAt
        });
    }

    assign(participantId) {
        this.assertRunning();

        if (typeof participantId !== 'string' || !participantId.trim()) {
            throw new ValidationError('Invalid participant ID.');
        }

        if (this.participants.has(participantId)) {
            return this.participants.get(participantId);
        }

        // Stable assignment using a cryptographic hash.
        const digest = crypto
            .createHash('sha256')
            .update(`${this.id}:${participantId}`)
            .digest();

        const bucket = digest.readBigUInt64BE(0);
        const threshold = BigInt(
            Math.floor(this.policy.allocationRatio * 1_000_000)
        );

        const variant =
            bucket % 1_000_000n < threshold
                ? Variant.CONTROL
                : Variant.TREATMENT;

        this.participants.set(participantId, variant);

        this.emit('participantAssigned', {
            participantId,
            variant
        });

        return variant;
    }

    recordOutcome(participantId, { converted, revenue = 0 }) {
        this.assertRunning();

        if (!this.participants.has(participantId)) {
            throw new ExperimentError('Participant has not been assigned.');
        }

        if (this.outcomes.has(participantId)) {
            throw new ExperimentError('Outcome already recorded.');
        }

        if (typeof converted !== 'boolean') {
            throw new ValidationError('Conversion must be boolean.');
        }

        if (!Number.isFinite(revenue) || revenue < 0) {
            throw new ValidationError('Revenue must be finite and non-negative.');
        }

        const outcome = Object.freeze({
            converted,
            revenue,
            recordedAt: new Date()
        });

        this.outcomes.set(participantId, outcome);

        this.emit('outcomeRecorded', {
            participantId,
            outcome
        });
    }

    assertRunning() {
        if (this.status !== ExperimentStatus.RUNNING) {
            throw new ExperimentError('Experiment is not running.');
        }
    }

    complete() {
        this.assertRunning();

        this.status = ExperimentStatus.COMPLETED;
        this.completedAt = new Date();

        this.emit('completed', {
            experimentId: this.id,
            completedAt: this.completedAt
        });
    }

    stop(reason) {
        this.assertRunning();

        this.status = ExperimentStatus.STOPPED;
        this.completedAt = new Date();

        this.emit('stopped', {
            experimentId: this.id,
            reason: reason || 'Manual stop'
        });
    }
}

class ExperimentAnalyzer {
    static analyze(experiment) {
        if (
            ![
                ExperimentStatus.COMPLETED,
                ExperimentStatus.STOPPED
            ].includes(experiment.status)
        ) {
            throw new ExperimentError('Experiment must be closed before analysis.');
        }

        const groups = {
            control: { n: 0, conversions: 0, revenue: 0 },
            treatment: { n: 0, conversions: 0, revenue: 0 }
        };

        for (const [id, outcome] of experiment.outcomes) {
            const variant = experiment.participants.get(id);
            const group = groups[variant];

            group.n++;
            group.conversions += Number(outcome.converted);
            group.revenue += outcome.revenue;
        }

        const control = groups.control;
        const treatment = groups.treatment;

        if (control.n === 0 || treatment.n === 0) {
            throw new ExperimentError('Both groups need observed outcomes.');
        }

        const p1 = control.conversions / control.n;
        const p2 = treatment.conversions / treatment.n;

        const lift = p2 - p1;
        const relativeLift = p1 > 0 ? lift / p1 : 0;

        const pooled =
            (control.conversions + treatment.conversions) /
            (control.n + treatment.n);

        const pooledSE = Math.sqrt(
            pooled * (1 - pooled) *
            (1 / control.n + 1 / treatment.n)
        );

        const z = pooledSE === 0 ? 0 : lift / pooledSE;
        const pValue = pooledSE === 0 ? 1 : 2 * normalCDF(-Math.abs(z));

        const ciSE = Math.sqrt(
            p1 * (1 - p1) / control.n +
            p2 * (1 - p2) / treatment.n
        );

        const critical = normalInverseCDF(1 - experiment.policy.alpha / 2);

        const confidenceInterval = [
            lift - critical * ciSE,
            lift + critical * ciSE
        ];

        return Object.freeze({
            control: Object.freeze({
                ...control,
                conversionRate: p1,
                averageRevenue: control.revenue / control.n
            }),
            treatment: Object.freeze({
                ...treatment,
                conversionRate: p2,
                averageRevenue: treatment.revenue / treatment.n
            }),
            absoluteLift: lift,
            relativeLift,
            zScore: z,
            pValue,
            confidenceInterval,
            statisticallySignificant: pValue < experiment.policy.alpha,
            practicallySignificant:
                lift >= experiment.policy.minimumDetectableEffect
        });
    }
}

class ExperimentDesigner {
    static requiredSampleSize({
        baselineRate,
        minimumDetectableEffect,
        alpha = 0.05,
        power = 0.80
    }) {
        const treatmentRate = baselineRate + minimumDetectableEffect;

        if (!(baselineRate > 0 && baselineRate < 1)) {
            throw new ValidationError('Invalid baseline rate.');
        }

        if (!(treatmentRate > baselineRate && treatmentRate < 1)) {
            throw new ValidationError('Invalid treatment rate.');
        }

        if (!(alpha > 0 && alpha < 1 && power > 0 && power < 1)) {
            throw new ValidationError('Invalid statistical parameters.');
        }

        const za = normalInverseCDF(1 - alpha / 2);
        const zb = normalInverseCDF(power);

        const pooled = (baselineRate + treatmentRate) / 2;

        const numerator = Math.pow(
            za * Math.sqrt(2 * pooled * (1 - pooled)) +
            zb * Math.sqrt(
                baselineRate * (1 - baselineRate) +
                treatmentRate * (1 - treatmentRate)
            ),
            2
        );

        return Math.ceil(
            numerator / Math.pow(minimumDetectableEffect, 2)
        );
    }
}

// Event consumers can monitor experiment execution independently.
class ExperimentMonitor {
    constructor(experiment) {
        this.assignmentCount = 0;
        this.outcomeCount = 0;

        experiment.on('participantAssigned', () => {
            this.assignmentCount++;
        });

        experiment.on('outcomeRecorded', () => {
            this.outcomeCount++;
        });

        experiment.on('stopped', event => {
            process.stdout.write(
                `Experiment stopped: ${event.reason}\n`
            );
        });
    }

    report() {
        return {
            assignments: this.assignmentCount,
            recordedOutcomes: this.outcomeCount,
            missingOutcomes: this.assignmentCount - this.outcomeCount
        };
    }
}

async function runSimulation() {
    const policy = new ExperimentPolicy({
        allocationRatio: 0.5,
        alpha: 0.05,
        power: 0.80,
        baselineRate: 0.10,
        minimumDetectableEffect: 0.02
    });

    const experiment = new Experiment({
        id: 'checkout-2026',
        name: 'Checkout Conversion Optimization',
        policy
    });

    const monitor = new ExperimentMonitor(experiment);

    const required = ExperimentDesigner.requiredSampleSize({
        baselineRate: 0.10,
        minimumDetectableEffect: 0.02,
        alpha: 0.05,
        power: 0.80
    });

    console.log('Required sample size per group:', required);

    experiment.start();

    // Async batches model independent ingestion and processing.
    const batchSize = 1000;
    const totalParticipants = 20000;

    for (let start = 0; start < totalParticipants; start += batchSize) {
        const batch = [];

        for (
            let i = start;
            i < Math.min(start + batchSize, totalParticipants);
            i++
        ) {
            batch.push(Promise.resolve().then(() => {
                const id = `customer-${i}`;

                const variant = experiment.assign(id);

                const conversionRate =
                    variant === Variant.CONTROL ? 0.10 : 0.12;

                const converted = crypto.randomInt(0, 1_000_000) <
                    Math.floor(conversionRate * 1_000_000);

                const revenue = converted
                    ? crypto.randomInt(2000, 15001) / 100
                    : 0;

                experiment.recordOutcome(id, {
                    converted,
                    revenue
                });
            }));
        }

        await Promise.all(batch);
    }

    experiment.complete();

    const result = ExperimentAnalyzer.analyze(experiment);

    console.log('\nCONTROL');
    console.log(result.control);

    console.log('\nTREATMENT');
    console.log(result.treatment);

    console.log('\nSTATISTICAL COMPARISON');
    console.log({
        absoluteLift: result.absoluteLift,
        relativeLift: result.relativeLift,
        zScore: result.zScore,
        pValue: result.pValue,
        confidenceInterval: result.confidenceInterval,
        statisticallySignificant: result.statisticallySignificant,
        practicallySignificant: result.practicallySignificant
    });

    console.log('\nMONITORING');
    console.log(monitor.report());

    console.log('\nEDGE CASE VALIDATION');

    try {
        experiment.assign('late-user');
    } catch (error) {
        console.log(error.name, error.message);
    }

    try {
        ExperimentDesigner.requiredSampleSize({
            baselineRate: 0.9,
            minimumDetectableEffect: 0.2
        });
    } catch (error) {
        console.log(error.name, error.message);
    }
}

runSimulation().catch(error => {
    console.error('Experiment execution failed:', error.message);
    process.exitCode = 1;
});
