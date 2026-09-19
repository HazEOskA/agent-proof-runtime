import type { AprEvent, AprSession } from "./types";

export const SLOT_COUNT = 4;

export type ConnectionState = "CONNECTING" | "ONLINE" | "OFFLINE";

export type MissionStoneState =
  | "IDLE"
  | "STARTING"
  | "RUNNING"
  | "VERIFYING"
  | "VERIFIED"
  | "FAILED"
  | "OFFLINE";

/** Deliberately separate from proof status. CLAIM != PROOF. */
export type ExecutionStatus = "IDLE" | "RUNNING" | "COMPLETED" | "FAILED";
export type ProofStatus = "NONE" | "PENDING" | "VERIFIED" | "FAILED";

export type SlotStatus = "IDLE" | "ASSIGNED" | "WORKING" | "DONE" | "FAILED";

export interface AgentSlot {
  index: number;
  stageId: string | null;
  /** Role label as returned by the runtime — never hardcoded in the world. */
  role: string | null;
  stageName: string | null;
  status: SlotStatus;
  outputHash: string | null;
  /** Monotonic counter used only to pick the least recently released slot. */
  releasedAt: number;
}

export interface HandoffVisual {
  id: string;
  fromSlot: number | null;
  toSlot: number | null;
  toCore: boolean;
  outputHash: string | null;
  createdAt: number;
}

export interface WorldLogEntry {
  id: string;
  worldEvent: string;
  label: string;
  tone: "neutral" | "good" | "bad";
}

export interface WorldState {
  connection: ConnectionState;
  sessionId: string | null;
  missionType: string | null;
  provider: string | null;
  model: string | null;
  runtimeState: string | null;
  progress: number;
  stone: MissionStoneState;
  execution: ExecutionStatus;
  proof: ProofStatus;
  aprStatus: string | null;
  anchorStatus: string | null;
  runId: string | null;
  failure: string | null;
  slots: AgentSlot[];
  handoffs: HandoffVisual[];
  log: WorldLogEntry[];
  /** Index of the last APR event already taken from the runtime. */
  consumedEvents: number;
  /**
   * Real APR events accepted but not yet folded into the world. The runtime
   * finishes a fixture run faster than a human can watch it, so the renderer
   * plays the recorded events back at a visible rate. Nothing is invented
   * here and nothing is dropped: the queue always drains to the real state.
   */
  pending: AprEvent[];
  /** Final mission_status held back until the queue has drained. */
  terminalMissionStatus: string | null;
  clock: number;
}

function emptySlots(): AgentSlot[] {
  return Array.from({ length: SLOT_COUNT }, (_, index) => ({
    index,
    stageId: null,
    role: null,
    stageName: null,
    status: "IDLE" as SlotStatus,
    outputHash: null,
    releasedAt: 0,
  }));
}

export function initialWorldState(): WorldState {
  return {
    connection: "CONNECTING",
    sessionId: null,
    missionType: null,
    provider: null,
    model: null,
    runtimeState: null,
    progress: 0,
    stone: "IDLE",
    execution: "IDLE",
    proof: "NONE",
    aprStatus: null,
    anchorStatus: null,
    runId: null,
    failure: null,
    slots: emptySlots(),
    handoffs: [],
    log: [],
    consumedEvents: 0,
    pending: [],
    terminalMissionStatus: null,
    clock: 0,
  };
}

export function resetMission(state: WorldState): WorldState {
  return {
    ...initialWorldState(),
    connection: state.connection,
    clock: state.clock,
  };
}

/** Derives the visible role from the stage identifier the runtime reported. */
export function roleFromStageId(stageId: string): string {
  return stageId.replace(/[_-]+/g, " ").trim().toUpperCase();
}

export function slotForStage(state: WorldState, stageId: string): AgentSlot | undefined {
  return state.slots.find((slot) => slot.stageId === stageId);
}

/**
 * Four physical stations serve a runtime that has more stages than stations.
 * A stage takes a free station; released stations are reused in the order
 * they were released.
 */
export function assignSlot(
  state: WorldState,
  stageId: string,
  stageName: string | null,
  status: SlotStatus,
): WorldState {
  const existing = slotForStage(state, stageId);
  if (existing) {
    const slots = state.slots.map((slot) =>
      slot.index === existing.index ? { ...slot, status, stageName: stageName ?? slot.stageName } : slot,
    );
    return { ...state, slots };
  }
  const free = state.slots.filter((slot) => slot.status === "IDLE" || slot.status === "DONE");
  const pool = free.length > 0 ? free : state.slots;
  const target = [...pool].sort((a, b) => {
    if (a.status === "IDLE" && b.status !== "IDLE") return -1;
    if (b.status === "IDLE" && a.status !== "IDLE") return 1;
    if (a.releasedAt !== b.releasedAt) return a.releasedAt - b.releasedAt;
    return a.index - b.index;
  })[0];
  const slots = state.slots.map((slot) =>
    slot.index === target.index
      ? {
          ...slot,
          stageId,
          role: roleFromStageId(stageId),
          stageName,
          status,
          outputHash: null,
        }
      : slot,
  );
  return { ...state, slots };
}

export function pushLog(state: WorldState, entry: Omit<WorldLogEntry, "id">): WorldState {
  const id = `world-${state.clock + 1}`;
  return {
    ...state,
    clock: state.clock + 1,
    log: [...state.log, { id, ...entry }].slice(-40),
  };
}

/**
 * Derived only from world events, never from a runtime field the world has
 * not caught up with yet. That keeps the stone from announcing a result the
 * player has not been shown.
 */
export function missionStoneState(state: WorldState): MissionStoneState {
  if (state.connection === "OFFLINE") return "OFFLINE";
  if (!state.sessionId) return "IDLE";
  if (state.execution === "FAILED" || state.proof === "FAILED") return "FAILED";
  if (state.proof === "VERIFIED") return "VERIFIED";
  if (state.proof === "PENDING") return "VERIFYING";
  if (state.execution === "RUNNING") return "RUNNING";
  return "STARTING";
}

export function applySessionSnapshot(state: WorldState, session: AprSession): WorldState {
  return {
    ...state,
    sessionId: session.session_id,
    missionType: session.mission_type,
    provider: session.provider,
    model: session.model,
    runtimeState: session.state,
    progress: session.progress,
    aprStatus: session.apr?.status ?? null,
    anchorStatus: session.anchor_status,
    runId: session.apr_run_id,
    failure: session.error,
  };
}
