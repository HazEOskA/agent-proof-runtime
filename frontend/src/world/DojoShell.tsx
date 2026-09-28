import { useMemo } from "react";
import dojoHero from "../assets/dojo-hero.png";
import dojoLogo from "../assets/dojo-logo.png";
import type { MissionStoneState, WorldState } from "../runtime/worldState";

const AGENTS = ["KAI", "REN", "SORA", "AKI"] as const;

const POSITIONS = [
  { x: 30, y: 54 },
  { x: 50, y: 30 },
  { x: 70, y: 54 },
  { x: 50, y: 68 },
] as const;

function proofLabel(world: WorldState): string {
  if (world.proof === "VERIFIED") return "LOCAL_VERIFIED";
  if (world.proof === "PENDING") return "PROOF PENDING";
  if (world.proof === "FAILED") return "PROOF FAILED";
  return "NO PROOF";
}

function executionLabel(world: WorldState): string {
  if (world.execution === "COMPLETED") return "EXECUTION COMPLETE";
  if (world.execution === "RUNNING") return "EXECUTION RUNNING";
  if (world.execution === "FAILED") return "EXECUTION FAILED";
  return "EXECUTION IDLE";
}

function toneForSlot(status: string): string {
  if (status === "WORKING") return "working";
  if (status === "DONE") return "done";
  if (status === "FAILED") return "failed";
  if (status === "ASSIGNED") return "assigned";
  return "idle";
}

function stoneLabel(stone: MissionStoneState): string {
  if (stone === "VERIFYING") return "VERIFYING";
  if (stone === "VERIFIED") return "VERIFIED";
  if (stone === "RUNNING") return "RUNNING";
  if (stone === "FAILED") return "FAILED";
  if (stone === "OFFLINE") return "OFFLINE";
  if (stone === "STARTING") return "STARTING";
  return "READY";
}

interface DojoShellProps {
  world: WorldState;
  stone: MissionStoneState;
  onOpenSensei: () => void;
  onOpenProof: () => void;
}

export function DojoShell({ world, stone, onOpenSensei, onOpenProof }: DojoShellProps) {
  const latestEvent = world.log.length > 0 ? world.log[world.log.length - 1] : undefined;
  const visibleHandoffs = useMemo(() => world.handoffs.slice(-5), [world.handoffs]);

  return (
    <main className="osa-dojo">
      <img className="osa-dojo__hero-ghost" src={dojoHero} alt="" aria-hidden="true" />

      <header className="osa-dojo__topline">
        <div className="osa-dojo__identity">
          <img src={dojoLogo} alt="OSA Agent Dojo" />
          <div>
            <strong>OSA AGENT DOJO</strong>
            <span>APR // LIVE CONTROL PLANE</span>
          </div>
        </div>

        <div className="osa-dojo__runtime">
          <span className={`runtime-dot runtime-dot--${world.connection.toLowerCase()}`} />
          <b>{world.connection}</b>
          <span>{world.provider ?? "APR"}</span>
          <span>{world.model ?? "runtime"}</span>
        </div>
      </header>

      <div className="osa-dojo__graffiti">CLAIM ≠ PROOF</div>

      <section className="osa-dojo__arena" aria-label="APR Agent Dojo">
        <div className="dojo-grid" />
        <div className="dojo-ring dojo-ring--outer" />
        <div className="dojo-ring dojo-ring--inner" />
        <div className="dojo-axis dojo-axis--x" />
        <div className="dojo-axis dojo-axis--y" />

        <svg className="dojo-handoffs" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          {visibleHandoffs.map((handoff) => {
            const from = handoff.fromSlot === null ? { x: 50, y: 50 } : POSITIONS[handoff.fromSlot] ?? { x: 50, y: 50 };
            const to = handoff.toCore
              ? { x: 50, y: 50 }
              : handoff.toSlot === null
                ? { x: 50, y: 50 }
                : POSITIONS[handoff.toSlot] ?? { x: 50, y: 50 };
            return (
              <line
                key={handoff.id}
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                className="dojo-handoff-line"
              />
            );
          })}
        </svg>

        <button className={`dojo-core dojo-core--${world.proof.toLowerCase()}`} onClick={onOpenProof}>
          <span className="dojo-core__orbit" />
          <span className="dojo-core__orbit dojo-core__orbit--two" />
          <small>APR PROOF CORE</small>
          <strong>{proofLabel(world)}</strong>
          <em>{world.runId ? world.runId.slice(0, 14) : "NO RUN"}</em>
        </button>

        {AGENTS.map((agent, index) => {
          const slot = world.slots[index];
          const position = POSITIONS[index];
          const tone = toneForSlot(slot?.status ?? "IDLE");
          return (
            <div
              key={agent}
              className={`dojo-agent dojo-agent--${tone}`}
              style={{ left: `${position.x}%`, top: `${position.y}%` }}
            >
              <div className="dojo-agent__halo" />
              <div className="dojo-agent__avatar">{agent.slice(0, 1)}</div>
              <strong>{agent}</strong>
              <span>{slot?.role ?? "IDLE"}</span>
              <small>{slot?.stageName ?? slot?.stageId ?? "WAITING FOR APR"}</small>
              {slot?.outputHash && <code>{slot.outputHash.replace("sha256:", "").slice(0, 10)}</code>}
            </div>
          );
        })}

        <div className={`dojo-event dojo-event--${latestEvent?.tone ?? "neutral"}`}>
          <small>APR EVENT STREAM</small>
          <strong>{latestEvent?.worldEvent ?? "RUNTIME READY"}</strong>
          <span>{latestEvent?.label ?? "Czekam na prawdziwe zdarzenie APR."}</span>
        </div>
      </section>

      <section className="osa-dojo__mission">
        <div>
          <small>MISSION</small>
          <strong>{world.missionTitle ?? "NO ACTIVE MISSION"}</strong>
          <span>{stoneLabel(stone)} · {Math.round(world.progress * 100)}%</span>
        </div>
        <button onClick={onOpenSensei}>URUCHOM MISJĘ</button>
      </section>

      <footer className="osa-dojo__proof-strip">
        <div className={`proof-strip__execution proof-strip--${world.execution.toLowerCase()}`}>
          <small>EXECUTION</small>
          <strong>{executionLabel(world)}</strong>
        </div>

        <div className="proof-strip__divider">≠</div>

        <button
          className={`proof-strip__proof proof-strip--${world.proof.toLowerCase()}`}
          onClick={onOpenProof}
        >
          <small>PROOF</small>
          <strong>{proofLabel(world)}</strong>
        </button>

        <div className="proof-strip__anchor">
          <small>ANCHOR</small>
          <strong>{world.anchorStatus ?? "UNANCHORED"}</strong>
        </div>
      </footer>
    </main>
  );
}
