import { useCallback, useState } from "react";
import type { MissionRequest } from "./api/aprClient";
import { ProofBundleOverlay } from "./ui/ProofBundleOverlay";
import { SenseiPanel } from "./ui/SenseiPanel";
import { useRuntime } from "./runtime/useRuntime";
import { DojoShell } from "./world/DojoShell";

export default function App() {
  const runtime = useRuntime();
  const [senseiOpen, setSenseiOpen] = useState(false);
  const [proofOpen, setProofOpen] = useState(false);

  const startMission = useCallback(
    async (request: MissionRequest) => {
      const started = await runtime.startMission(request);
      if (started) setSenseiOpen(false);
    },
    [runtime],
  );

  return (
    <div className="stage dojo-stage">
      <DojoShell
        world={runtime.world}
        stone={runtime.stone}
        onOpenSensei={() => setSenseiOpen(true)}
        onOpenProof={() => setProofOpen(true)}
      />

      <SenseiPanel
        open={senseiOpen}
        world={runtime.world}
        starting={runtime.starting}
        startError={runtime.startError}
        onClose={() => {
          setSenseiOpen(false);
          runtime.clearStartError();
        }}
        onStart={(request) => {
          void startMission(request);
        }}
      />

      <ProofBundleOverlay
        open={proofOpen}
        world={runtime.world}
        detail={runtime.runDetail}
        onClose={() => setProofOpen(false)}
      />
    </div>
  );
}
