import { reportUrl } from "../api/aprClient";
import type { AprRunDetail } from "../runtime/types";
import type { WorldState } from "../runtime/worldState";

interface ProofBundleOverlayProps {
  open: boolean;
  world: WorldState;
  detail: AprRunDetail | null;
  onClose: () => void;
}

function scalar(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "—";
}

export function ProofBundleOverlay({ open, world, detail, onClose }: ProofBundleOverlayProps) {
  if (!open) return null;
  const integrity = (detail?.evidence.integrity ?? {}) as Record<string, unknown>;
  const run = (detail?.evidence.run ?? {}) as Record<string, unknown>;
  const artifacts = detail?.evidence.artifacts ?? [];
  const checks = detail?.evidence.acceptance?.checks ?? [];

  return (
    <div className="scrim" role="dialog" aria-modal="true" aria-label="Proof Bundle">
      <div className="panel panel--wide">
        <header className="panel__head">
          <div>
            <p className="eyebrow">APR PROOF CORE</p>
            <h2>Proof Bundle</h2>
          </div>
          <button type="button" className="ghost" onClick={onClose} aria-label="Zamknij">
            ✕
          </button>
        </header>

        <div className="panel__body">
          <div className="split">
            <div className="stat">
              <span className="eyebrow">WYKONANIE</span>
              <strong>{world.execution}</strong>
            </div>
            <div className="stat">
              <span className="eyebrow">WERYFIKACJA</span>
              <strong className={world.proof === "VERIFIED" ? "good" : world.proof === "FAILED" ? "bad" : ""}>
                {world.proof}
              </strong>
            </div>
          </div>
          <p className="claim">CLAIM ≠ PROOF — status wykonania nigdy nie zastępuje wyniku weryfikacji.</p>

          {!detail && <p className="sensei-line">Brak Proof Bundle. Uruchom misję i poczekaj na wynik weryfikatora.</p>}

          {detail && (
            <>
              <dl className="facts">
                <div>
                  <dt>MISJA</dt>
                  <dd>{detail.summary.mission_id}</dd>
                </div>
                <div>
                  <dt>RUN</dt>
                  <dd>{detail.summary.run_id}</dd>
                </div>
                <div>
                  <dt>STATUS MISJI</dt>
                  <dd>{detail.summary.mission_status}</dd>
                </div>
                <div>
                  <dt>STATUS DOWODU</dt>
                  <dd>{detail.summary.proof_status}</dd>
                </div>
                <div>
                  <dt>ANCHOR</dt>
                  <dd>{detail.summary.anchor_status}</dd>
                </div>
                <div>
                  <dt>ZDARZENIA</dt>
                  <dd>{detail.summary.event_count}</dd>
                </div>
                <div>
                  <dt>BACKEND</dt>
                  <dd>{scalar(run.sandbox_backend)}</dd>
                </div>
                <div>
                  <dt>SIEĆ</dt>
                  <dd>{scalar(run.network_policy)}</dd>
                </div>
              </dl>

              <h3>INTEGRALNOŚĆ</h3>
              <ul className="hashes">
                <li>
                  <span>merkle root</span>
                  <code>{scalar(integrity.event_merkle_root)}</code>
                </li>
                <li>
                  <span>bundle hash</span>
                  <code>{scalar(integrity.bundle_hash)}</code>
                </li>
                <li>
                  <span>kanonizacja</span>
                  <code>{scalar(integrity.canonicalization)}</code>
                </li>
              </ul>

              <h3>ARTEFAKTY ({artifacts.length})</h3>
              <ul className="hashes">
                {artifacts.map((artifact) => (
                  <li key={artifact.path}>
                    <span>{artifact.path}</span>
                    <code>
                      {artifact.sha256.slice(0, 22)}… · {artifact.size} B
                    </code>
                  </li>
                ))}
              </ul>

              <h3>
                CHECKI AKCEPTACYJNE ({checks.filter((check) => check.passed).length}/{checks.length})
              </h3>
              <p className="checks">
                {checks.map((check) => (
                  <span key={check.id} className={check.passed ? "chip good" : "chip bad"}>
                    {check.id}
                  </span>
                ))}
              </p>

              {detail.summary.errors.length > 0 && (
                <p className="alert">{detail.summary.errors.join(" · ")}</p>
              )}

              <a className="primary as-link" href={reportUrl(detail.summary.run_id)} target="_blank" rel="noreferrer">
                OTWÓRZ RAPORT APR
              </a>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
