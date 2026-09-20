import { useEffect, useMemo, useState } from "react";
import type { MissionRequest } from "../api/aprClient";
import type { WorldState } from "../runtime/worldState";

interface SenseiPanelProps {
  open: boolean;
  world: WorldState;
  starting: boolean;
  startError: string | null;
  onClose: () => void;
  onStart: (request: MissionRequest) => void;
}

const MIN_PROMPT = 10;
const MAX_PROMPT = 4000;

const PROVIDER_STATUS_LABEL: Record<string, string> = {
  NOT_CONFIGURED: "NIESKONFIGUROWANY",
  CONFIGURED: "SKONFIGUROWANY",
  LAST_CALL_OK: "OSTATNIE WYWOŁANIE OK",
  ERROR: "BŁĄD",
  RATE_LIMITED: "LIMIT ZAPYTAŃ",
  AUTH_FAILED: "ODRZUCONE POŚWIADCZENIA",
};

/**
 * Sensei takes a free-form task. The runtime plans it, runs it and decides
 * what is proven — this panel never claims a result of its own.
 */
export function SenseiPanel({ open, world, starting, startError, onClose, onStart }: SenseiPanelProps) {
  const [prompt, setPrompt] = useState(
    "Przeanalizuj poniższy tekst, wskaż trzy najważniejsze problemy, przygotuj ulepszoną wersję i krótkie podsumowanie zmian.",
  );
  const [provider, setProvider] = useState("fixture");
  const [maxAgents, setMaxAgents] = useState(4);
  const offline = world.connection !== "ONLINE";
  const normalized = prompt.replace(/\s+/g, " ").trim();
  const tooShort = normalized.length < MIN_PROMPT;
  const tooLong = normalized.length > MAX_PROMPT;

  const openrouter = useMemo(
    () => world.providers.find((item) => item.provider === "openrouter"),
    [world.providers],
  );
  const providerReady =
    provider === "fixture" || (openrouter ? openrouter.status !== "NOT_CONFIGURED" : false);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const statusLabel = openrouter
    ? PROVIDER_STATUS_LABEL[openrouter.status] ?? openrouter.status
    : "NIEZNANY";

  return (
    <div className="scrim" role="dialog" aria-modal="true" aria-label="Sensei">
      <div className="panel">
        <header className="panel__head">
          <div>
            <p className="eyebrow">SENSEI · ORKIESTRATOR APR</p>
            <h2>Co mam zlecić agentom?</h2>
          </div>
          <button type="button" className="ghost" onClick={onClose} aria-label="Zamknij">
            ✕
          </button>
        </header>

        <div className="panel__body">
          <p className="sensei-line">
            {offline
              ? "Nie mogę uruchomić misji — APR jest niedostępny."
              : "Zaprojektuję plan misji, dobiorę role agentów i przekażę pracę do runtime'u. Wyniku nie ogłaszam ja — ogłasza go weryfikator APR."}
          </p>

          <label className="field">
            <span>ZADANIE</span>
            <textarea
              id="sensei-prompt"
              rows={5}
              value={prompt}
              maxLength={8000}
              onChange={(event) => setPrompt(event.target.value)}
              disabled={starting}
            />
            <small className={tooShort || tooLong ? "warn" : ""}>
              {normalized.length} / {MAX_PROMPT} znaków po normalizacji (minimum {MIN_PROMPT})
            </small>
          </label>

          <div className="row">
            <label className="field">
              <span>PROVIDER</span>
              <select
                id="sensei-provider"
                value={provider}
                onChange={(event) => setProvider(event.target.value)}
                disabled={starting}
              >
                <option value="fixture">fixture — deterministyczny, bez sieci</option>
                <option value="openrouter">openrouter — realne wywołania modelu</option>
              </select>
            </label>
            <label className="field">
              <span>MAKS. AGENTÓW</span>
              <select
                id="sensei-max-agents"
                value={String(maxAgents)}
                onChange={(event) => setMaxAgents(Number(event.target.value))}
                disabled={starting}
              >
                {[1, 2, 3, 4].map((value) => (
                  <option key={value} value={String(value)}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <dl className="facts" id="provider-status">
            <div>
              <dt>PROVIDER</dt>
              <dd>{provider === "fixture" ? "FIXTURE" : "OPENROUTER"}</dd>
            </div>
            <div>
              <dt>MODEL</dt>
              <dd>{provider === "fixture" ? "fixture-v1" : openrouter?.model ?? "—"}</dd>
            </div>
            <div>
              <dt>STATUS</dt>
              <dd className={providerReady ? "good" : "bad"}>
                {provider === "fixture" ? "DETERMINISTYCZNY FIXTURE" : statusLabel}
              </dd>
            </div>
          </dl>

          <p className="contract-note">
            {provider === "fixture"
              ? "Bieg fixture jest deterministyczny i offline. To nie jest wywołanie modelu — nie nazywaj go realnym biegiem providera."
              : "Klucz API jest konfiguracją serwera. Ten interfejs nigdy go nie przyjmuje, nie pokazuje ani nie zapisuje."}
          </p>

          {startError && <p className="alert">{startError}</p>}

          <button
            type="button"
            className="primary"
            id="run-mission"
            disabled={offline || starting || tooShort || tooLong || !providerReady}
            onClick={() =>
              onStart({
                mission_type: "generic_v1",
                prompt: normalized,
                provider,
                max_agents: maxAgents,
              })
            }
          >
            {starting ? "URUCHAMIAM…" : "URUCHOM MISJĘ"}
          </button>

          {world.sessionId && (
            <dl className="facts">
              <div>
                <dt>MISJA</dt>
                <dd>{world.missionTitle ?? "—"}</dd>
              </div>
              <div>
                <dt>SESJA</dt>
                <dd>{world.sessionId}</dd>
              </div>
              <div>
                <dt>MODEL</dt>
                <dd>{world.model ?? "—"}</dd>
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
