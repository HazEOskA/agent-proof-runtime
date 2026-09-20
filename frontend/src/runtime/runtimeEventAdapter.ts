import type { AprEvent } from "./types";
import {
  assignSlot,
  pushLog,
  slotForStage,
  type HandoffVisual,
  type WorldState,
} from "./worldState";

/**
 * APR EVENT -> RuntimeEventAdapter -> WORLD EVENT
 *
 * The backend event vocabulary is the one APR already emits. This adapter is
 * the only place that knows those names; the world itself only ever reacts to
 * the world events produced here. Nothing in this file may invent progress:
 * every world event is the consequence of one recorded APR event.
 */

export type WorldEventName =
  | "MISSION_ACCEPTED"
  | "PLAN_REQUESTED"
  | "PLAN_ACCEPTED"
  | "AGENT_STARTED"
  | "AGENT_COMPLETED"
  | "HANDOFF"
  | "RUN_STARTED"
  | "CONTRACT_ENFORCED"
  | "RUN_COMPLETED"
  | "VERIFICATION_COMPLETED"
  | "MISSION_FAILED";

const AGENT_EVENT = /^agent\.(.+)\.(started|completed)$/;
const HANDOFF_EVENT = /^handoff\.(.+)_to_(.+)$/;

function text(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function shortHash(value: string | null): string {
  if (!value) return "";
  const bare = value.startsWith("sha256:") ? value.slice(7) : value;
  return bare.slice(0, 10);
}

/** Folds a single real APR event into the world. Pure — no timers, no guesses. */
export function applyAprEvent(state: WorldState, event: AprEvent): WorldState {
  const type = event.type;

  if (type === "studio.mission_accepted") {
    return pushLog({ ...state, execution: "RUNNING" }, {
      worldEvent: "MISSION_ACCEPTED",
      label: "Misja przyjęta przez APR",
      tone: "neutral",
    });
  }

  if (type === "studio.plan_requested") {
    return pushLog(state, {
      worldEvent: "PLAN_REQUESTED",
      label: "Sensei projektuje plan misji",
      tone: "neutral",
    });
  }

  if (type === "studio.plan_accepted") {
    const title = text(event.title);
    const stageCount = typeof event.stage_count === "number" ? event.stage_count : null;
    return pushLog(state, {
      worldEvent: "PLAN_ACCEPTED",
      label:
        stageCount === null
          ? `Plan zaakceptowany: ${title ?? "misja"}`
          : `Plan zaakceptowany: ${title ?? "misja"} · ${stageCount} etapów`,
      tone: "good",
    });
  }

  const agentMatch = AGENT_EVENT.exec(type);
  if (agentMatch) {
    const stageId = agentMatch[1];
    const phase = agentMatch[2];
    const stageName = text(event.stage_name);
    if (phase === "started") {
      const next = assignSlot(state, stageId, stageName, "WORKING");
      const slot = slotForStage(next, stageId);
      return pushLog(next, {
        worldEvent: "AGENT_STARTED",
        label: `AGENT 0${(slot?.index ?? 0) + 1} · ${slot?.role ?? stageId} — start`,
        tone: "neutral",
      });
    }
    const outputHash = text(event.output_hash);
    const withSlot = assignSlot(state, stageId, stageName, "DONE");
    const slot = slotForStage(withSlot, stageId);
    const slots = withSlot.slots.map((item) =>
      item.stageId === stageId ? { ...item, status: "DONE" as const, outputHash } : item,
    );
    return pushLog({ ...withSlot, slots }, {
      worldEvent: "AGENT_COMPLETED",
      label: `AGENT 0${(slot?.index ?? 0) + 1} · ${slot?.role ?? stageId} — ukończono ${shortHash(outputHash)}`,
      tone: "neutral",
    });
  }

  const handoffMatch = HANDOFF_EVENT.exec(type);
  if (handoffMatch) {
    const source = text(event.source_stage) ?? handoffMatch[1];
    const destination = text(event.destination_stage) ?? handoffMatch[2];
    const toCore = destination === "apr";
    let next = state;
    // Reserve the destination station so the transfer has a physical target.
    if (!toCore) next = assignSlot(next, destination, null, "ASSIGNED");
    const fromSlot = slotForStage(next, source)?.index ?? null;
    const toSlot = toCore ? null : slotForStage(next, destination)?.index ?? null;
    const handoff: HandoffVisual = {
      id: `${event.id}-${type}`,
      fromSlot,
      toSlot,
      toCore,
      outputHash: text(event.output_hash),
      createdAt: performance.now(),
    };
    const label = toCore
      ? `Przekazanie do APR PROOF CORE ${shortHash(handoff.outputHash)}`
      : `AGENT 0${(fromSlot ?? 0) + 1} → AGENT 0${(toSlot ?? 0) + 1} ${shortHash(handoff.outputHash)}`;
    return pushLog({ ...next, handoffs: [...next.handoffs, handoff].slice(-6) }, {
      worldEvent: "HANDOFF",
      label,
      tone: "neutral",
    });
  }

  if (type === "apr.run.started") {
    return pushLog(state, {
      worldEvent: "RUN_STARTED",
      label: "APR rozpoczął run dowodowy",
      tone: "neutral",
    });
  }

  if (type === "apr.contract_enforced") {
    const count = typeof event.artifact_count === "number" ? event.artifact_count : null;
    return pushLog(state, {
      worldEvent: "CONTRACT_ENFORCED",
      label: count === null ? "Kontrakt artefaktów wyegzekwowany" : `Kontrakt artefaktów wyegzekwowany (${count})`,
      tone: "neutral",
    });
  }

  if (type === "apr.run.completed") {
    // Execution is finished. Proof is NOT. This split is the product.
    const runId = text(event.run_id);
    return pushLog({ ...state, execution: "COMPLETED", proof: "PENDING", runId: runId ?? state.runId }, {
      worldEvent: "RUN_COMPLETED",
      label: "Wykonanie zakończone — oczekiwanie na weryfikację",
      tone: "neutral",
    });
  }

  if (type === "verifier.completed") {
    const status = text(event.status);
    const verified = status === "LOCAL_VERIFIED";
    return pushLog(
      { ...state, proof: verified ? "VERIFIED" : "FAILED", anchorStatus: text(event.anchor_status) },
      {
        worldEvent: "VERIFICATION_COMPLETED",
        label: verified ? "Weryfikacja APR: LOCAL_VERIFIED" : `Weryfikacja APR: ${status ?? "FAILED"}`,
        tone: verified ? "good" : "bad",
      },
    );
  }

  if (type === "studio.mission_failed") {
    const category = text(event.category);
    return pushLog(
      { ...state, execution: "FAILED", proof: "FAILED", handoffs: [] },
      {
        worldEvent: "MISSION_FAILED",
        label: category ? `Misja nieudana: ${category}` : "Misja nieudana",
        tone: "bad",
      },
    );
  }

  return state;
}

/**
 * Accepts every APR event not yet taken from the runtime and queues it in the
 * runtime's own order. Queueing never changes world state on its own.
 */
export function enqueueAprEvents(state: WorldState, events: AprEvent[]): WorldState {
  if (events.length <= state.consumedEvents) return state;
  return {
    ...state,
    pending: [...state.pending, ...events.slice(state.consumedEvents)],
    consumedEvents: events.length,
  };
}

/** Folds the next queued APR event. Returns the state unchanged when idle. */
export function drainAprEvent(state: WorldState): WorldState {
  if (state.pending.length === 0) return state;
  const [next, ...rest] = state.pending;
  return { ...applyAprEvent(state, next), pending: rest };
}
