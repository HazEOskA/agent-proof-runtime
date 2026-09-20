/**
 * Shapes returned by the real Agent Proof Runtime HTTP surface.
 * Nothing here is invented: every field is read from an actual APR response.
 */

export interface AprEvent {
  id: string;
  type: string;
  timestamp: string;
  [key: string]: unknown;
}

export interface AprSessionAgent {
  stage_id: string;
  stage_name: string;
  status: "ready" | "working" | "handing_off" | "completed" | "failed";
  output_hash: string | null;
}

export interface AprPlanStage {
  id: string;
  role: string;
  instruction: string;
  expected_output: { type: string };
  acceptance: Array<Record<string, unknown>>;
  inputs: string[];
}

export interface AprMissionPlan {
  version: string;
  title: string;
  goal: string;
  stages: AprPlanStage[];
}

export interface AprProviderStatus {
  provider: string;
  model: string | null;
  base_url: string | null;
  status: string;
}

export interface AprServiceState {
  name: string;
  version: string;
  mission_types?: string[];
  providers?: AprProviderStatus[];
}

export interface AprSession {
  session_id: string;
  mission_type: string;
  brief: string;
  prompt?: string;
  mission_title?: string | null;
  plan?: AprMissionPlan | null;
  verification_scope?: string[];
  provider: string;
  model: string;
  state: string;
  progress: number;
  current_stage: string | null;
  current_output_hash: string | null;
  current_handoff: { source_stage: string; destination_stage: string; output_hash: string } | null;
  agents: AprSessionAgent[];
  apr: { status: string };
  events: AprEvent[];
  apr_run_id: string | null;
  mission_status: string | null;
  proof_status: string | null;
  anchor_status: string | null;
  failure_category: string | null;
  error: string | null;
}

export interface AprRunSummary {
  run_id: string;
  mission_id: string;
  started_at: string | null;
  duration_ms?: number;
  mission_status: string;
  proof_status: string;
  anchor_status: string;
  event_count: number;
  security_level: string;
  backend: string;
  provider?: string;
  report_url: string | null;
  bundle_url?: string;
  errors: string[];
}

export interface AprProofBundle {
  schema_version?: string;
  mission?: { manifest?: Record<string, unknown>; manifest_hash?: string };
  provider?: Record<string, unknown>;
  run?: Record<string, unknown>;
  events?: Array<Record<string, unknown>>;
  artifacts?: Array<{ path: string; media_type: string; size: number; sha256: string }>;
  acceptance?: { status?: string; checks?: Array<{ id: string; passed: boolean }> };
  verification?: { claimed_status?: string };
  integrity?: Record<string, unknown>;
}

export interface AprRunDetail {
  summary: AprRunSummary;
  evidence: AprProofBundle;
}

/** Terminal session states. Polling stops here — nothing else moves the world. */
export const TERMINAL_STATES = new Set(["completed", "failed"]);
