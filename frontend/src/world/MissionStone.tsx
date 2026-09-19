import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import * as THREE from "three";
import { COLORS, STONE_POSITION } from "./theme";
import type { MissionStoneState } from "../runtime/worldState";

const STONE_COLOR: Record<MissionStoneState, string> = {
  IDLE: COLORS.cyanDeep,
  STARTING: COLORS.blue,
  RUNNING: COLORS.cyan,
  VERIFYING: COLORS.amber,
  VERIFIED: COLORS.green,
  FAILED: COLORS.red,
  OFFLINE: "#43555c",
};

const STONE_LABEL: Record<MissionStoneState, string> = {
  IDLE: "GOTOWY",
  STARTING: "URUCHAMIANIE",
  RUNNING: "W TRAKCIE",
  VERIFYING: "WERYFIKACJA",
  VERIFIED: "ZWERYFIKOWANO",
  FAILED: "BŁĄD",
  OFFLINE: "OFFLINE",
};

/** Physical entry point for a mission. Its state comes from the runtime only. */
export function MissionStone({ state, onOpen }: { state: MissionStoneState; onOpen: () => void }) {
  const monolith = useRef<THREE.Mesh>(null);
  const glow = useRef<THREE.Mesh>(null);
  const color = STONE_COLOR[state];
  const active = state === "RUNNING" || state === "VERIFYING" || state === "STARTING";

  useFrame((frame) => {
    const t = frame.clock.elapsedTime;
    if (monolith.current) monolith.current.position.y = 1.36 + Math.sin(t * 0.9) * 0.035;
    if (glow.current) {
      const pulse = active ? 0.45 + Math.abs(Math.sin(t * 2.1)) * 0.45 : 0.4;
      (glow.current.material as THREE.MeshBasicMaterial).opacity = pulse;
    }
  });

  return (
    <group position={STONE_POSITION} onClick={onOpen}>
      <mesh position={[0, 0.14, 0]} receiveShadow>
        <cylinderGeometry args={[1.06, 1.2, 0.28, 6]} />
        <meshStandardMaterial color="#0a1a1f" roughness={0.55} metalness={0.5} />
      </mesh>
      <mesh ref={monolith} position={[0, 1.36, 0]} rotation={[0, Math.PI / 6, 0]} castShadow>
        <boxGeometry args={[0.92, 2.1, 0.5]} />
        <meshStandardMaterial
          color="#0d2229"
          emissive={color}
          emissiveIntensity={active ? 0.55 : 0.28}
          roughness={0.35}
          metalness={0.65}
        />
      </mesh>
      <mesh ref={glow} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.3, 0]}>
        <ringGeometry args={[0.82, 1.18, 48]} />
        <meshBasicMaterial color={color} transparent opacity={0.5} />
      </mesh>
      <pointLight position={[0, 1.7, 0]} color={color} intensity={active ? 3.6 : 1.6} distance={7} />

      <Html position={[0, 2.6, 0]} center distanceFactor={19} zIndexRange={[18, 0]}>
        <span className="world-label" style={{ borderColor: color, color }}>
          MISSION STONE · {STONE_LABEL[state]}
        </span>
      </Html>
    </group>
  );
}
