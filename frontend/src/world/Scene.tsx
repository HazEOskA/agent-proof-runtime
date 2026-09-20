import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
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
      dpr={high ? [1, 1.65] : [1, 1.05]}
      gl={{ antialias: high, powerPreference: "high-performance" }}
      camera={{ position: [0, 16.8, 27.8], fov: 40, near: 0.1, far: 320 }}
      onCreated={({ gl, scene }) => {
        gl.toneMapping = THREE.ACESFilmicToneMapping;
        gl.toneMappingExposure = 0.88;
        scene.background = new THREE.Color(COLORS.void);
        scene.fog = new THREE.FogExp2(COLORS.void, 0.017);
      }}
    >
      <Suspense fallback={null}>
        {high && <Stars radius={120} depth={50} count={950} factor={2.2} saturation={0} fade speed={0.25} />}
        <ambientLight intensity={0.24} color="#2d6972" />
        <hemisphereLight args={["#174e58", "#020507", 0.42]} />
        <directionalLight
          position={[14, 22, -14]}
          intensity={0.95}
          color="#88e8ff"
          castShadow={high}
          shadow-mapSize={[1024, 1024]}
        />
        <spotLight
          position={[-13, 18, 11]}
          angle={0.58}
          penumbra={0.92}
          intensity={31}
          color={COLORS.cyan}
          distance={62}
        />
        <spotLight
          position={[13, 15, 8]}
          angle={0.7}
          penumbra={1}
          intensity={19}
          color={COLORS.violet}
          distance={58}
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
            <Bloom intensity={0.52} luminanceThreshold={0.62} luminanceSmoothing={0.72} mipmapBlur />
          </EffectComposer>
        )}

        <OrbitControls
          ref={controlsRef as never}
          makeDefault
          enablePan={false}
          minDistance={12}
          maxDistance={48}
          minPolarAngle={0.48}
          maxPolarAngle={Math.PI / 2.13}
          target={[0, 2.1, 0]}
          enableDamping
          dampingFactor={0.075}
          autoRotate={world.execution === "IDLE"}
          autoRotateSpeed={0.18}
        />
      </Suspense>
    </Canvas>
  );
}
