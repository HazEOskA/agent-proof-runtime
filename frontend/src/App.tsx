import { useCallback, useRef, useState } from "react";
import type { MissionRequest } from "./api/aprClient";
import { Hud } from "./ui/Hud";
import { ProofBundleOverlay } from "./ui/ProofBundleOverlay";
import { SenseiPanel } from "./ui/SenseiPanel";
import { useRuntime } from "./runtime/useRuntime";
import { Scene, type Quality } from "./world/Scene";

function webglSupported(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2"));
  } catch {
    return false;
  }
}

export default function App() {
  const runtime = useRuntime();
  const [quality, setQuality] = useState<Quality>("high");
  const [senseiOpen, setSenseiOpen] = useState(false);
  const [proofOpen, setProofOpen] = useState(false);
  const controlsRef = useRef<{ reset: () => void } | null>(null);
  const [supported] = useState(webglSupported);

  const startMission = useCallback(
    async (request: MissionRequest) => {
      const started = await runtime.startMission(request);
      if (started) setSenseiOpen(false);
    },
    [runtime],
  );

  if (!supported) {
    return (
      <div className="fallback">
        <p className="eyebrow">APR 3D CONTROL PLANE</p>
        <h1>RENDEROWANIE 3D NIEDOSTĘPNE</h1>
        <p>Ten control plane wymaga WebGL 2.</p>
      </div>
    );
  }

  return (
    <div className="stage">
      <Scene
        world={runtime.world}
        stone={runtime.stone}
        quality={quality}
        controlsRef={controlsRef}
        onOpenSensei={() => setSenseiOpen(true)}
        onOpenProof={() => setProofOpen(true)}
      />
      <Hud
        world={runtime.world}
        stone={runtime.stone}
        quality={quality}
        onToggleQuality={() => setQuality((value) => (value === "high" ? "balanced" : "high"))}
        onResetCamera={() => controlsRef.current?.reset()}
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
