import type { AprRunDetail, AprServiceState, AprSession } from "../runtime/types";

/**
 * Thin client over the existing APR Mission Control endpoints.
 * No endpoint is invented here; every call maps to a route that already exists.
 */

export class AprOfflineError extends Error {}
export class AprRequestError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

/**
 * The CSRF token is injected by the runtime into the served document.
 * In `vite dev` it can be supplied through VITE_APR_TOKEN. It is never
 * persisted by this application.
 */
function aprToken(): string {
  const injected = (window as unknown as { __APR_TOKEN__?: string }).__APR_TOKEN__;
  if (typeof injected === "string" && injected.length > 0) return injected;
  const fromEnv = import.meta.env.VITE_APR_TOKEN;
  if (typeof fromEnv === "string" && fromEnv.length > 0) return fromEnv;
  return "";
}

async function readJson(response: Response): Promise<Record<string, unknown>> {
  let value: unknown;
  try {
    value = await response.json();
  } catch {
    throw new AprRequestError("APR zwrócił odpowiedź, której nie da się odczytać.", response.status);
  }
  if (typeof value !== "object" || value === null) {
    throw new AprRequestError("APR zwrócił nieoczekiwany kształt odpowiedzi.", response.status);
  }
  return value as Record<string, unknown>;
}

async function get(path: string, signal?: AbortSignal): Promise<Record<string, unknown>> {
  let response: Response;
  try {
    response = await fetch(path, { method: "GET", cache: "no-store", signal });
  } catch (error) {
    if ((error as Error).name === "AbortError") throw error;
    throw new AprOfflineError("APR jest nieosiągalny.");
  }
  const value = await readJson(response);
  if (!response.ok || value.ok === false) {
    throw new AprRequestError(String(value.error ?? "Żądanie APR zostało odrzucone."), response.status);
  }
  return value;
}

async function post(path: string, body: unknown): Promise<Record<string, unknown>> {
  const token = aprToken();
  if (!token) {
    throw new AprRequestError(
      "Brak tokenu APR w tym dokumencie. Otwórz control plane spod adresu serwowanego przez APR.",
      403,
    );
  }
  let response: Response;
  try {
    response = await fetch(path, {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json", "X-APR-Token": token },
      body: JSON.stringify(body),
    });
  } catch {
    throw new AprOfflineError("APR jest nieosiągalny.");
  }
  const value = await readJson(response);
  if (!response.ok || value.ok === false) {
    throw new AprRequestError(String(value.error ?? "Żądanie APR zostało odrzucone."), response.status);
  }
  return value;
}

export async function health(signal?: AbortSignal): Promise<boolean> {
  try {
    const value = await get("/health", signal);
    return value.status === "healthy";
  } catch (error) {
    if ((error as Error).name === "AbortError") throw error;
    return false;
  }
}

/**
 * Starts a real Mission Studio run. The request shape belongs to the backend:
 * `generic_v1` takes a free-form prompt, `verified_website_build` takes a brief.
 */
export type MissionRequest =
  | { mission_type: "generic_v1"; prompt: string; provider: string; max_agents: number }
  | { mission_type: "verified_website_build"; brief: string; provider: string };

export async function startMission(input: MissionRequest): Promise<AprSession> {
  const value = await post("/api/studio/start", input);
  return value.session as AprSession;
}

/** Service state, including provider configuration status. Never a credential. */
export async function readState(signal?: AbortSignal): Promise<AprServiceState> {
  const value = await get("/api/state", signal);
  return value.service as AprServiceState;
}

export async function readSession(sessionId: string, signal?: AbortSignal): Promise<AprSession> {
  const value = await get(`/api/studio/${encodeURIComponent(sessionId)}`, signal);
  return value.session as AprSession;
}

export async function readRun(runId: string, signal?: AbortSignal): Promise<AprRunDetail> {
  const value = await get(`/api/runs/${encodeURIComponent(runId)}`, signal);
  return { summary: value.summary, evidence: value.evidence } as AprRunDetail;
}

export function reportUrl(runId: string): string {
  return `/runs/${encodeURIComponent(runId)}/report.html`;
}
