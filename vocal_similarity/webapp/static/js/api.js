// HTTP API 클라이언트: 모든 서버 호출은 이 모듈을 통해서만 합니다.

export class ApiError extends Error {
  constructor(status, detail) {
    const message = typeof detail === 'string' ? detail : detail?.message || `HTTP ${status}`;
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    let detail = data?.detail ?? res.statusText;
    if (Array.isArray(detail)) detail = detail.map((d) => d.msg).join(', '); // pydantic 검증 오류
    throw new ApiError(res.status, detail);
  }
  return data;
}

const enc = encodeURIComponent;

export const api = {
  listArtists: () => request('GET', 'api/artists'),
  saveArtist: (name, urls) => request('PUT', `api/artists/${enc(name)}`, { urls }),
  deleteArtist: (name, purge = false) => request('DELETE', `api/artists/${enc(name)}?purge=${purge}`),

  listJobs: () => request('GET', 'api/jobs'),
  startJob: (artists) => request('POST', 'api/jobs', { artists: artists?.length ? artists : null }),
  getJob: (id, logOffset = 0) => request('GET', `api/jobs/${enc(id)}?log_offset=${logOffset}`),
  cancelJob: (id) => request('POST', `api/jobs/${enc(id)}/cancel`),

  listResultRuns: () => request('GET', 'api/results/runs'),
  similarity: (runId) => request('GET', `api/results/similarity${runId ? `?run_id=${enc(runId)}` : ''}`),
  similarityCsvUrl: (runId) => `api/results/similarity.csv${runId ? `?run_id=${enc(runId)}` : ''}`,
  topPairsCsvUrl: (runId) => `api/results/top-pairs.csv${runId ? `?run_id=${enc(runId)}` : ''}`,
  topPairsTxtUrl: (runId) => `api/results/top-pairs.txt${runId ? `?run_id=${enc(runId)}` : ''}`,
  clustermapUrl: (runId) => `api/results/clustermap.png?${runId ? `run_id=${enc(runId)}&` : ''}t=${Date.now()}`,
};
