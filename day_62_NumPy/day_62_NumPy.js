'use strict';

/*
 * NumPy-inspired numerical computing workflow implemented with
 * JavaScript typed arrays and standard Node.js functionality.
 *
 * The implementation focuses on:
 * - dense numeric matrices
 * - indexing and slicing
 * - vectorized-style operations
 * - broadcasting
 * - masking
 * - statistics
 * - normalization
 * - anomaly detection
 * - event-driven policy evaluation
 * - validation and failure handling
 *
 * JavaScript has no built-in NumPy equivalent, so Float64Array and
 * explicit matrix operations provide predictable numeric storage.
 */

const { EventEmitter } = require('node:events');
const assert = require('node:assert/strict');

class Matrix {
    constructor(rows, cols, data = null) {
        if (!Number.isInteger(rows) || rows <= 0) {
            throw new RangeError('rows must be a positive integer');
        }
        if (!Number.isInteger(cols) || cols <= 0) {
            throw new RangeError('cols must be a positive integer');
        }

        this.rows = rows;
        this.cols = cols;
        this.data = data instanceof Float64Array
            ? new Float64Array(data)
            : new Float64Array(rows * cols);

        if (this.data.length !== rows * cols) {
            throw new RangeError('Data length does not match matrix dimensions');
        }
    }

    static fromNested(values) {
        if (!Array.isArray(values) || values.length === 0) {
            throw new TypeError('Matrix requires a non-empty array');
        }

        const cols = values[0].length;

        if (!Number.isInteger(cols) || cols === 0) {
            throw new TypeError('Matrix rows must be non-empty');
        }

        for (const row of values) {
            if (!Array.isArray(row) || row.length !== cols) {
                throw new TypeError('Matrix rows must have equal lengths');
            }
            for (const value of row) {
                if (!Number.isFinite(value)) {
                    throw new TypeError('Matrix values must be finite numbers');
                }
            }
        }

        const flat = new Float64Array(values.length * cols);
        let offset = 0;

        for (const row of values) {
            flat.set(row, offset);
            offset += cols;
        }

        return new Matrix(values.length, cols, flat);
    }

    index(row, col) {
        if (
            !Number.isInteger(row) ||
            !Number.isInteger(col) ||
            row < 0 ||
            row >= this.rows ||
            col < 0 ||
            col >= this.cols
        ) {
            throw new RangeError(`Invalid index (${row}, ${col})`);
        }

        return row * this.cols + col;
    }

    get(row, col) {
        return this.data[this.index(row, col)];
    }

    set(row, col, value) {
        if (!Number.isFinite(value)) {
            throw new TypeError('Matrix values must be finite');
        }
        this.data[this.index(row, col)] = value;
    }

    row(rowIndex) {
        if (!Number.isInteger(rowIndex) || rowIndex < 0 || rowIndex >= this.rows) {
            throw new RangeError('Invalid row index');
        }

        const start = rowIndex * this.cols;
        return this.data.slice(start, start + this.cols);
    }

    column(columnIndex) {
        if (!Number.isInteger(columnIndex) || columnIndex < 0 || columnIndex >= this.cols) {
            throw new RangeError('Invalid column index');
        }

        const result = new Float64Array(this.rows);

        for (let row = 0; row < this.rows; row++) {
            result[row] = this.get(row, columnIndex);
        }

        return result;
    }

    map(fn) {
        const result = new Float64Array(this.data.length);

        for (let i = 0; i < this.data.length; i++) {
            const value = fn(this.data[i], i);
            if (!Number.isFinite(value)) {
                throw new RangeError('Matrix transformation produced a non-finite value');
            }
            result[i] = value;
        }

        return new Matrix(this.rows, this.cols, result);
    }

    broadcastAdd(vector) {
        if (vector.length !== this.cols) {
            throw new RangeError('Broadcast vector length must equal matrix columns');
        }

        const result = new Float64Array(this.data.length);

        for (let row = 0; row < this.rows; row++) {
            for (let col = 0; col < this.cols; col++) {
                result[row * this.cols + col] =
                    this.get(row, col) + vector[col];
            }
        }

        return new Matrix(this.rows, this.cols, result);
    }

    minByColumn() {
        const result = new Float64Array(this.cols);
        result.fill(Infinity);

        for (let row = 0; row < this.rows; row++) {
            for (let col = 0; col < this.cols; col++) {
                result[col] = Math.min(result[col], this.get(row, col));
            }
        }

        return result;
    }

    maxByColumn() {
        const result = new Float64Array(this.cols);
        result.fill(-Infinity);

        for (let row = 0; row < this.rows; row++) {
            for (let col = 0; col < this.cols; col++) {
                result[col] = Math.max(result[col], this.get(row, col));
            }
        }

        return result;
    }

    meanByColumn() {
        const result = new Float64Array(this.cols);

        for (let row = 0; row < this.rows; row++) {
            for (let col = 0; col < this.cols; col++) {
                result[col] += this.get(row, col);
            }
        }

        for (let col = 0; col < this.cols; col++) {
            result[col] /= this.rows;
        }

        return result;
    }

    normalizeColumns() {
        const min = this.minByColumn();
        const max = this.maxByColumn();
        const result = new Float64Array(this.data.length);

        for (let row = 0; row < this.rows; row++) {
            for (let col = 0; col < this.cols; col++) {
                const range = max[col] - min[col];
                result[row * this.cols + col] =
                    range === 0 ? 0 : (this.get(row, col) - min[col]) / range;
            }
        }

        return new Matrix(this.rows, this.cols, result);
    }

    weightedRows(weights) {
        if (weights.length !== this.cols) {
            throw new RangeError('Weight count must match matrix columns');
        }

        const scores = new Float64Array(this.rows);

        for (let row = 0; row < this.rows; row++) {
            let score = 0;
            for (let col = 0; col < this.cols; col++) {
                score += this.get(row, col) * weights[col];
            }
            scores[row] = score;
        }

        return scores;
    }

    toNested() {
        const result = [];

        for (let row = 0; row < this.rows; row++) {
            result.push(Array.from(this.row(row)));
        }

        return result;
    }
}

function zScores(matrix) {
    const means = matrix.meanByColumn();
    const result = new Float64Array(matrix.data.length);
    const std = new Float64Array(matrix.cols);

    for (let col = 0; col < matrix.cols; col++) {
        let squared = 0;

        for (let row = 0; row < matrix.rows; row++) {
            const delta = matrix.get(row, col) - means[col];
            squared += delta * delta;
        }

        std[col] = Math.sqrt(squared / matrix.rows);
    }

    for (let row = 0; row < matrix.rows; row++) {
        for (let col = 0; col < matrix.cols; col++) {
            const safeStd = std[col] === 0 ? 1 : std[col];
            result[row * matrix.cols + col] =
                (matrix.get(row, col) - means[col]) / safeStd;
        }
    }

    return new Matrix(matrix.rows, matrix.cols, result);
}

function detectAnomalies(matrix, threshold = 2) {
    if (!Number.isFinite(threshold) || threshold <= 0) {
        throw new RangeError('Threshold must be positive');
    }

    const scores = zScores(matrix);
    const anomalies = [];

    for (let row = 0; row < matrix.rows; row++) {
        let anomalous = false;

        for (let col = 0; col < matrix.cols; col++) {
            if (Math.abs(scores.get(row, col)) >= threshold) {
                anomalous = true;
                break;
            }
        }

        anomalies.push(anomalous);
    }

    return anomalies;
}

class NumericalMonitor extends EventEmitter {
    constructor(matrix, weights) {
        super();
        this.matrix = matrix;
        this.weights = Float64Array.from(weights);
        this.listenersAttached = false;
    }

    start() {
        if (this.listenersAttached) {
            throw new Error('Monitor is already running');
        }

        this.listenersAttached = true;

        this.on('result', ({ index, score }) => {
            const state = score >= 0.60 ? 'ALERT' : 'NORMAL';
            console.log(`record=${index + 1} score=${score.toFixed(3)} state=${state}`);
        });

        this.on('completed', count => {
            console.log(`Processed ${count} records.`);
        });

        const normalized = this.matrix.normalizeColumns();
        const scores = normalized.weightedRows(this.weights);

        for (let index = 0; index < scores.length; index++) {
            this.emit('result', { index, score: scores[index] });
        }

        this.emit('completed', scores.length);
    }
}

async function runAsyncStatistics(matrix) {
    return new Promise(resolve => {
        setImmediate(() => {
            resolve({
                means: Array.from(matrix.meanByColumn()),
                minimums: Array.from(matrix.minByColumn()),
                maximums: Array.from(matrix.maxByColumn())
            });
        });
    });
}

async function main() {
    const matrix = Matrix.fromNested([
        [22.4, 45.0, 1012.3, 0.12],
        [23.1, 46.5, 1011.8, 0.15],
        [24.8, 49.2, 1010.4, 0.18],
        [26.7, 54.0, 1008.9, 0.31],
        [28.4, 58.1, 1007.5, 0.42],
        [29.1, 61.0, 1006.2, 0.55],
        [27.8, 57.3, 1007.1, 0.38],
        [25.6, 51.4, 1009.2, 0.22]
    ]);

    console.log('=== Matrix ===');
    console.log(matrix.toNested());

    console.log('\n=== Indexing ===');
    console.log('First row:', Array.from(matrix.row(0)));
    console.log('Temperature column:', Array.from(matrix.column(0)));

    console.log('\n=== Broadcasting ===');
    const adjusted = matrix.broadcastAdd(
        Float64Array.from([1.0, -2.0, 0.5, 0.0])
    );
    console.log('Adjusted first row:', Array.from(adjusted.row(0)));

    console.log('\n=== Statistics ===');
    const statistics = await runAsyncStatistics(matrix);
    console.log(statistics);

    console.log('\n=== Anomaly detection ===');
    const anomalyFlags = detectAnomalies(matrix);
    console.log(anomalyFlags);

    console.log('\n=== Normalized weighted evaluation ===');
    const normalized = matrix.normalizeColumns();
    const scores = normalized.weightedRows(
        Float64Array.from([0.35, 0.20, 0.25, 0.20])
    );
    console.log(Array.from(scores));

    console.log('\n=== Event-driven processing ===');
    const monitor = new NumericalMonitor(matrix, [0.35, 0.20, 0.25, 0.20]);
    monitor.start();

    console.log('\n=== Validation ===');

    assert.equal(matrix.rows, 8);
    assert.equal(matrix.cols, 4);
    assert.equal(matrix.data.length, 32);

    try {
        matrix.get(100, 0);
    } catch (error) {
        console.log('Invalid index rejected:', error.message);
    }

    try {
        matrix.broadcastAdd([1, 2]);
    } catch (error) {
        console.log('Invalid broadcast rejected:', error.message);
    }

    try {
        Matrix.fromNested([[1, 2], [3]]);
    } catch (error) {
        console.log('Irregular matrix rejected:', error.message);
    }

    console.log('\nNumerical workflow completed successfully.');
}

main().catch(error => {
    console.error('Fatal numerical processing error:', error.message);
    process.exitCode = 1;
});
