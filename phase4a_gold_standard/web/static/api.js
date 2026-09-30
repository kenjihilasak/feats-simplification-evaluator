const DEFAULT_API_BASE = "/api";
let sessionCsrfToken = null;

export class ApiError extends Error {
  constructor(message, { status = 0, code = "request_failed", details = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function configuredBase() {
  const configured = globalThis.PHASE4A_CONFIG?.apiBase;
  return String(configured || DEFAULT_API_BASE).replace(/\/$/, "");
}

function readCookie(name) {
  const prefix = `${encodeURIComponent(name)}=`;
  for (const part of document.cookie.split(";")) {
    const cookie = part.trim();
    if (cookie.startsWith(prefix)) {
      return decodeURIComponent(cookie.slice(prefix.length));
    }
  }
  return null;
}

function csrfToken() {
  return (
    sessionCsrfToken ||
    globalThis.PHASE4A_CONFIG?.csrfToken ||
    document.querySelector('meta[name="csrf-token"]')?.content ||
    readCookie("phase4a_csrf") ||
    readCookie("csrf_token") ||
    null
  );
}

function rememberSession(payload) {
  const token = payload?.csrf_token ?? payload?.data?.csrf_token;
  if (token) sessionCsrfToken = String(token);
  return payload;
}

async function request(path, { method = "GET", body, signal } = {}) {
  const headers = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const token = csrfToken();
  if (token && method !== "GET" && method !== "HEAD") {
    headers["X-CSRF-Token"] = token;
  }

  let response;
  try {
    response = await fetch(`${configuredBase()}${path}`, {
      method,
      credentials: "same-origin",
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new ApiError("The review server could not be reached. Your draft remains in this browser.", {
      code: "network_error",
      details: error.message,
    });
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json().catch(() => null)
    : await response.text().catch(() => "");

  if (!response.ok) {
    const detail = payload?.detail;
    const message =
      (typeof detail === "string" && detail) ||
      detail?.message ||
      payload?.message ||
      `Request failed (${response.status}).`;
    throw new ApiError(message, {
      status: response.status,
      code: payload?.code || detail?.code || "request_failed",
      details: detail || payload,
    });
  }

  return payload;
}

export const api = {
  async login(username, password, signal) {
    return rememberSession(
      await request("/auth/login", {
        method: "POST",
        body: { username, password },
        signal,
      }),
    );
  },

  async me(signal) {
    return rememberSession(await request("/auth/me", { signal }));
  },

  async logout(signal) {
    const payload = await request("/auth/logout", { method: "POST", signal });
    sessionCsrfToken = null;
    return payload;
  },

  progress(filters = {}, signal) {
    const query = new URLSearchParams();
    (filters.sources || []).forEach((value) => query.append("sources", value));
    (filters.models || []).forEach((value) => query.append("models", value));
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request(`/me/progress${suffix}`, { signal });
  },

  queueFilters(signal) {
    return request("/queue/filters", { signal });
  },

  nextTask(filters = {}, signal) {
    const query = new URLSearchParams();
    (filters.sources || []).forEach((value) => query.append("sources", value));
    (filters.models || []).forEach((value) => query.append("models", value));
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request(`/tasks/next${suffix}`, { signal });
  },

  task(taskId, signal) {
    return request(`/tasks/${encodeURIComponent(taskId)}`, { signal });
  },

  renewLease(taskId, signal) {
    return request(`/tasks/${encodeURIComponent(taskId)}/lease`, {
      method: "POST",
      signal,
    });
  },

  saveDraft(taskId, annotation, expectedVersion, signal) {
    return request(`/annotations/${encodeURIComponent(taskId)}/draft`, {
      method: "PATCH",
      body: { annotation, expected_version: expectedVersion },
      signal,
    });
  },

  submit(taskId, annotation, expectedVersion, signal) {
    return request(`/annotations/${encodeURIComponent(taskId)}/submit`, {
      method: "POST",
      body: { annotation, expected_version: expectedVersion },
      signal,
    });
  },

  skip(taskId, reason, notes, expectedVersion, signal) {
    return request(`/annotations/${encodeURIComponent(taskId)}/skip`, {
      method: "POST",
      body: { reason, notes, expected_version: expectedVersion },
      signal,
    });
  },

  mine(states = ["submitted"], signal) {
    const query = new URLSearchParams();
    states.forEach((value) => query.append("states", value));
    return request(`/annotations/mine?${query.toString()}`, { signal });
  },

  resume(taskId, expectedVersion, signal) {
    return request(`/annotations/${encodeURIComponent(taskId)}/resume`, {
      method: "POST",
      body: { expected_version: expectedVersion },
      signal,
    });
  },
};

export function unwrapTask(payload) {
  if (!payload) return null;
  if (Object.prototype.hasOwnProperty.call(payload, "task")) return payload.task;
  if (payload.data && Object.prototype.hasOwnProperty.call(payload.data, "task")) {
    return payload.data.task;
  }
  return payload.data ?? payload;
}

export function unwrapAnnotation(payload) {
  return payload?.annotation ?? payload?.draft ?? payload?.data?.annotation ??
    (Object.prototype.hasOwnProperty.call(payload || {}, "version") ? payload : null);
}

export function unwrapProgress(payload) {
  return payload?.progress ?? payload?.data?.progress ?? payload?.data ?? payload ?? {};
}
