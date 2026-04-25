/**
 * Minimal PCA: returns first 2 principal component scores.
 * Input: matrix (n × d), output: scores (n × 2).
 */
export function computePCA(matrix: number[][]): [number, number][] {
  const n = matrix.length;
  const d = matrix[0].length;

  // Center columns
  const mean = new Array<number>(d).fill(0);
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < d; j++) {
      mean[j] += matrix[i][j];
    }
  }
  for (let j = 0; j < d; j++) mean[j] /= n;

  const X = matrix.map((row) => row.map((v, j) => v - mean[j]));

  // Covariance matrix (d × d) = X.T @ X / (n - 1)
  const C: number[][] = Array.from({ length: d }, () => new Array<number>(d).fill(0));
  for (let i = 0; i < n; i++) {
    for (let a = 0; a < d; a++) {
      for (let b = a; b < d; b++) {
        C[a][b] += X[i][a] * X[i][b];
      }
    }
  }
  const denom = Math.max(n - 1, 1);
  for (let a = 0; a < d; a++) {
    for (let b = a; b < d; b++) {
      C[a][b] /= denom;
      C[b][a] = C[a][b];
    }
  }

  // Power iteration for top-2 eigenvectors
  const v1 = powerIterate(C, d, 200);
  const C2 = deflate(C, d, v1);
  const v2 = powerIterate(C2, d, 200);

  // Project
  return X.map((row) => [dot(row, v1), dot(row, v2)]);
}

function powerIterate(C: number[][], d: number, iters: number): number[] {
  let v = new Array<number>(d).fill(0);
  // Deterministic init: use first non-zero column of C to avoid null space
  for (let j = 0; j < d; j++) {
    for (let i = 0; i < d; i++) {
      v[i] += C[i][j] * Math.sin(j + 1);
    }
  }
  // Fallback if v is near-zero (all-zero C)
  if (v.reduce((s, x) => s + x * x, 0) < 1e-24) {
    for (let j = 0; j < d; j++) v[j] = Math.sin(j + 1);
  }
  normalize(v);

  for (let iter = 0; iter < iters; iter++) {
    const w = matvec(C, v, d);
    normalize(w);
    v = w;
  }
  return v;
}

function deflate(C: number[][], d: number, v: number[]): number[][] {
  // Remove the top component: C2 = C - lambda * v * v.T
  const lambda = dot(matvec(C, v, d), v);
  return C.map((row, a) => row.map((val, b) => val - lambda * v[a] * v[b]));
}

function matvec(A: number[][], x: number[], d: number): number[] {
  const out = new Array<number>(d).fill(0);
  for (let i = 0; i < d; i++) {
    for (let j = 0; j < d; j++) {
      out[i] += A[i][j] * x[j];
    }
  }
  return out;
}

function dot(a: number[], b: number[]): number {
  return a.reduce((s, v, i) => s + v * b[i], 0);
}

function normalize(v: number[]): void {
  const norm = Math.sqrt(v.reduce((s, x) => s + x * x, 0));
  if (norm > 1e-12) {
    for (let i = 0; i < v.length; i++) v[i] /= norm;
  }
}
