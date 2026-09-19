import { useEffect, useState } from "react";
import type { WorldState } from "../runtime/worldState";

interface SenseiPanelProps {
  open: boolean;
  world: WorldState;
  starting: boolean;
  startError: string | null;
  onClose: () => void;
  onStart: (brief: string, provider: string) => void;
}

const MIN_BRIEF = 10;
const MAX_BRIEF = 2000;

/**
 * Slice 1 talks to the mission contract APR actually exposes today
 * (verified_website_build). The panel says so instead of pretending the
 * runtime accepts arbitrary work.
 */
export function SenseiPanel({ open, world, starting, startError, onClose, onStart }: SenseiPanelProps) {
  const [brief, setBrief] = useState(
    "Zbuduj zweryfikowaną stronę produktu dla runtime'u, który dowodzi wykonania pracy agentów.",
  );
  const [provider, setProvider] = useState("fixture");
  const offline = world.connection !== "ONLINE";
  const normalized = brief.replace(/\s+/g, " ").trim();
  const tooShort = normalized.length < MIN_BRIEF;
  const tooLong = normalized.length > MAX_BRIEF;

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="scrim" role="dialog" aria-modal="true" aria-label="Sensei">
      <div className="panel">
        <header className="panel__head">
          <div>
            <p className="eyebrow">SENSEI · ORKIESTRATOR APR</p>
            <h2>Uruchom zweryfikowaną misję</h2>
          </div>
          <button type="button" className="ghost" onClick={onClose} aria-label="Zamknij">
            ✕
          </button>
        </header>

        <div className="panel__body">
          <p className="sensei-line">
            {offline
              ? "Nie mogę uruchomić misji — APR jest niedostępny."
              : "Przyjmuję opis zadania i przekazuję go do runtime'u. Nie wykonuję pracy sam i nie deklaruję wyniku — wynik ustala APR."}
          </p>

          <div className="contract">
            <span className="eyebrow">KONTRAKT MISJI (Z RUNTIME)</span>
            <code>mission_type = verified_website_build</code>
            <p>
              To jedyny typ misji, który dzisiejszy backend APR realizuje naprawdę. Opis poniżej trafia do
              pola <code>brief</code> tego kontraktu.
            </p>
          </div>

          <label className="field">
            <span>OPIS ZADANIA</span>
            <textarea
              id="sensei-brief"
              rows={4}
              value={brief}
              maxLength={4000}
              onChange={(event) => setBrief(event.target.value)}
              disabled={starting}
            />
            <small className={tooShort || tooLong ? "warn" : ""}>
              {normalized.length} / {MAX_BRIEF} znaków po normalizacji (minimum {MIN_BRIEF})
            </small>
          </label>

          <label className="field">
            <span>PROVIDER</span>
            <select
              id="sensei-provider"
              value={provider}
              onChange={(event) => setProvider(event.target.value)}
              disabled={starting}
            >
              <option value="fixture">fixture — deterministyczny, offline</option>
              <option value="openai">openai — wymaga klucza po stronie serwera</option>
            </select>
            <small>
              Klucz API jest konfiguracją backendu (zmienna środowiskowa). Ten interfejs nigdy go nie
              przyjmuje ani nie zapisuje.
            </small>
          </label>

          {startError && <p className="alert">{startError}</p>}

          <button
            type="button"
            className="primary"
            id="run-mission"
            disabled={offline || starting || tooShort || tooLong}
            onClick={() => onStart(normalized, provider)}
          >
            {starting ? "URUCHAMIAM…" : "URUCHOM MISJĘ"}
          </button>

          {world.sessionId && (
            <dl className="facts">
              <div>
                <dt>SESJA</dt>
                <dd>{world.sessionId}</dd>
              </div>
              <div>
                <dt>MODEL</dt>
                <dd>{world.model ?? "—"}</dd>
              </div>
              <div>
                <dt>STAN RUNTIME</dt>
                <dd>{world.runtimeState ?? "—"}</dd>
              </div>
              <div>
                <dt>RUN</dt>
                <dd>{world.runId ?? "—"}</dd>
              </div>
            </dl>
          )}
        </div>
      </div>
    </div>
  );
}
