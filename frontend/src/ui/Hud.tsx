import type { Quality } from "../world/Scene";
import type { MissionStoneState, WorldState } from "../runtime/worldState";

const SENSEI_LINE: Record<string, string> = {
  MISSION_ACCEPTED: "Misja przyjęta przez APR.",
  PLAN_REQUESTED: "Tworzę plan misji…",
  PLAN_ACCEPTED: "Plan zaakceptowany. Dobieram role agentów.",
  AGENT_STARTED: "Uruchamiam agenta.",
  AGENT_COMPLETED: "Agent zakończył pracę.",
  HANDOFF: "Przekazuję artefakt dalej.",
  RUN_STARTED: "Zbieram evidence.",
  CONTRACT_ENFORCED: "Kontrakt artefaktów wyegzekwowany.",
  RUN_COMPLETED: "Wykonanie zakończone. Proof jeszcze nie jest zatwierdzony.",
  VERIFICATION_COMPLETED: "APR zakończył weryfikację.",
  MISSION_FAILED: "Misja nieudana.",
};

function senseiLine(world: WorldState): string {
  if (world.connection === "OFFLINE") return "APR jest niedostępny — bez backendu nie uruchamiam świata.";
  if (!world.sessionId) return "Czekam na zadanie.";
  const last = world.log[world.log.length - 1];
  if (!last) return "Czekam na zadanie.";
  return SENSEI_LINE[last.worldEvent] ?? last.label;
}

const CONNECTION_LABEL = {
  CONNECTING: "ŁĄCZENIE…",
  ONLINE: "RUNTIME ONLINE",
  OFFLINE: "RUNTIME OFFLINE",
} as const;

export function Hud({
  world,
  stone,
  quality,
  onToggleQuality,
  onResetCamera,
  onOpenSensei,
  onOpenProof,
}: {
  world: WorldState;
  stone: MissionStoneState;
  quality: Quality;
  onToggleQuality: () => void;
  onResetCamera: () => void;
  onOpenSensei: () => void;
  onOpenProof: () => void;
}) {
  const connectionTone =
    world.connection === "ONLINE" ? "good" : world.connection === "OFFLINE" ? "bad" : "";

  return (
    <div className="hud">
      <div className="hud__corner hud__corner--tl">
        <div className="hero-lockup">
          <p className="brand">APR</p>
          <p className="brand__sub">AGENT PROOF RUNTIME · 3D CONTROL PLANE</p>
          <p className="brand__statement">CLAIM ≠ PROOF</p>
          <p className="brand__flow">EXECUTION · EVIDENCE · VERIFICATION</p>
        </div>
        {world.missionTitle && (
          <p className="brand__mission" id="mission-title">
            MISJA · {world.missionTitle}
          </p>
        )}
      </div>

      <div className="hud__corner hud__corner--tr">
        <span id="connection-state" className={"chip " + connectionTone}>
          {CONNECTION_LABEL[world.connection]}
        </span>
        <button type="button" className="ghost" onClick={onToggleQuality}>
          JAKOŚĆ · {quality === "high" ? "WYSOKA" : "OSZCZĘDNA"}
        </button>
        <button type="button" className="ghost" onClick={onResetCamera}>
          RESET KAMERY
        </button>
      </div>

      <div className="hud__corner hud__corner--bl">
        <button type="button" className="primary" onClick={onOpenSensei}>
          POROZMAWIAJ Z SENSEIEM
        </button>
        <p className="sensei-hud" id="sensei-line">
          SENSEI · {senseiLine(world)}
        </p>
        <div className="statuses">
          <div>
            <span className="eyebrow">MISSION</span>
            <strong id="stone-state">{stone}</strong>
          </div>
          <div>
            <span className="eyebrow">WYKONANIE</span>
            <strong id="execution-status">{world.execution}</strong>
          </div>
          <div>
            <span className="eyebrow">WERYFIKACJA</span>
            <strong
              id="proof-status"
              className={world.proof === "VERIFIED" ? "good" : world.proof === "FAILED" ? "bad" : ""}
            >
              {world.proof}
            </strong>
          </div>
        </div>
        {world.failure && <p className="alert alert--compact">{world.failure}</p>}
      </div>

      <div className="hud__corner hud__corner--br">
        <div className="log" id="world-log">
          <p className="eyebrow">LIVE TRACE · APR EVENTS</p>
          {world.log.length === 0 && <p className="log__empty">Brak zdarzeń runtime.</p>}
          {world.log.slice(-5).map((entry) => (
            <p key={entry.id} className={"log__row " + entry.tone} data-world-event={entry.worldEvent}>
              <b>{entry.worldEvent}</b>
              <span>{entry.label}</span>
            </p>
          ))}
        </div>
        <div className="micro-tags">
          <span>#VERIFIABLEAI</span>
          <span>#PROOFBUNDLE</span>
        </div>
        {world.runId && (
          <button type="button" className="ghost proof-button" onClick={onOpenProof}>
            OTWÓRZ PROOF BUNDLE
          </button>
        )}
      </div>
    </div>
  );
}
