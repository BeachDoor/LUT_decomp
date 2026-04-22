import { UMAP } from "umap-js";

interface WorkerRequest {
  matrix: number[][];
  nNeighbors: number;
}

self.onmessage = (e: MessageEvent<WorkerRequest>) => {
  const { matrix, nNeighbors } = e.data;
  const umap = new UMAP({ nNeighbors, minDist: 0.1, nComponents: 2 });
  const embedding = umap.fit(matrix);
  self.postMessage({ embedding });
};
