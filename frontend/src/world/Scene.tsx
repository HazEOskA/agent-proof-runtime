import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { Bloom, EffectComposer } from "@react-three/postprocessing";
import * as THREE from "three";
import { AgentStation } from "./AgentStation";
import { Dojo } from "./Dojo";
import { Handoffs } from "./Handoffs";
import { MissionStone } from "./MissionStone";
import { ProofCore } from "./ProofCore";
import { Sensei } from "./Sensei";
import { COLORS } from "./theme";
import type { MissionStoneState, WorldState } from "../runtime/worldState";

export type Quality = "high" | "balanced";

interface SceneProps {
  world: WorldState;
  stone: MissionStoneState;
  quality: Quality;
  controlsRef: React.MutableRefObject<{ reset: () => void } | null>;
  onOpenSensei: () => void;
  onOpenProof: () => void;
}

export function Scene({ world, stone, quality, controlsRef, onOpenSensei, onOpenProof }: SceneProps) {
  const high = quality === "high";
  return (
    <Canvas
      shadows={high}
      dpr={high ? [1, 1.75] : [1, 1.1]}
      gl={{ antialias: high, powerPreference: "high-performance" }}
      camera={{ position: [0, 18.5, 25.5], fov: 42, near: 0.1, far: 300 }}
      onCreated={({ gl, scene }) => {
        gl.toneMapping = THREE.ACESFilmicToneMapping;
        gl.toneMappingExposure = 1.05;
        scene.background = new THREE.Color(COLORS.void);
        scene.fog = new THREE.Fog(COLORS.void, 40, 130);
      }}
    >
      <Suspense fallback={null}>
        <ambientLight intensity={0.38} color="#3f7f8c" />
        <hemisphereLight args={["#1d4e5a", "#03080b", 0.5]} />
        <directionalLight
          position={[12, 18, -10]}
          intensity={0.85}
          color="#77d7ff"
          castShadow={high}
          shadow-mapSize={[1024, 1024]}
        />
        <spotLight
          position={[-14, 16, 12]}
          angle={0.7}
          penumbra={0.9}
          intensity={42}
          color={COLORS.cyan}
          distance={70}
        />

        <Dojo quality={quality} />
        <Sensei online={world.connection === "ONLINE"} onOpen={onOpenSensei} />
        <MissionStone state={stone} onOpen={onOpenSensei} />
        {world.slots.map((slot) => (
          <AgentStation key={slot.index} slot={slot} />
        ))}
        <ProofCore execution={world.execution} proof={world.proof} onOpen={onOpenProof} />
        <Handoffs handoffs={world.handoffs} />

        {high && (
          <EffectComposer enableNormalPass={false}>
            <Bloom intensity={0.42} luminanceThreshold={0.36} luminanceSmoothing={0.6} mipmapBlur />
          </EffectComposer>
        )}

        <OrbitControls
          ref={controlsRef as never}
          makeDefault
          enablePan={false}
          minDistance={11}
          maxDistance={52}
          maxPolarAngle={Math.PI / 2.12}
          target={[0, 2.0, 0]}
          enableDamping
          dampingFactor={0.08}
        />
      </Suspense>
    </Canvas>
  );
}
