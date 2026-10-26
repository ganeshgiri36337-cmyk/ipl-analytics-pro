const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000")
  .replace(/\/$/, "");

export function queryString(filters = {}) {
  const params = new URLSearchParams();
  for (const [key, values] of Object.entries(filters)) {
    for (const value of values || []) {
      params.append(key, value);
    }
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export async function getJson(path, filters = {}, signal) {
  const response = await fetch(`${API_BASE}${path}${queryString(filters)}`, {
    signal,
    headers: { Accept: "application/json" },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || `Request failed (${response.status}).`);
  }
  return body;
}

export async function uploadCsv(dataset, file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/api/upload/${dataset}`, {
    method: "POST",
    body: formData,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || `Upload failed (${response.status}).`);
  }
  return body;
}
