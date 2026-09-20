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

export function MissionStone({ state, onOpen }: { state: MissionStoneState; onOpen: () => void }) {
  const monolith = useRef<THREE.Mesh>(null);
  const glow = useRef<THREE.Mesh>(null);
  const ringA = useRef<THREE.Mesh>(null);
  const ringB = useRef<THREE.Mesh>(null);
  const color = STONE_COLOR[state];
  const active = state === "RUNNING" || state === "VERIFYING" || state === "STARTING";

  useFrame((frame, delta) => {
    const t = frame.clock.elapsedTime;
    if (monolith.current) {
      monolith.current.position.y = 1.48 + Math.sin(t * 0.82) * 0.055;
      monolith.current.rotation.y += delta * (state === "VERIFYING" ? 0.34 : 0.08);
    }
    if (glow.current) {
      const pulse = active ? 0.38 + Math.abs(Math.sin(t * 2.1)) * 0.42 : 0.3;
      (glow.current.material as THREE.MeshBasicMaterial).opacity = pulse;
    }
    if (ringA.current) ringA.current.rotation.z += delta * (state === "VERIFYING" ? 1.0 : 0.24);
    if (ringB.current) ringB.current.rotation.x -= delta * (state === "VERIFYING" ? 0.72 : 0.18);
  });

  return (
    <group position={STONE_POSITION} onClick={onOpen}>
      <mesh position={[0, 0.13, 0]} receiveShadow>
        <cylinderGeometry args={[1.18, 1.42, 0.3, 8]} />
        <meshStandardMaterial color="#08171b" roughness={0.5} metalness={0.62} />
      </mesh>

      <mesh ref={monolith} position={[0, 1.48, 0]} rotation={[0, Math.PI / 5, 0]} castShadow>
        <dodecahedronGeometry args={[0.92, 0]} />
        <meshStandardMaterial
          color="#0b2027"
          emissive={color}
          emissiveIntensity={active ? 0.62 : state === "VERIFIED" ? 0.72 : 0.26}
          roughness={0.3}
          metalness={0.7}
          flatShading
        />
      </mesh>

      <mesh ref={glow} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.31, 0]}>
        <ringGeometry args={[0.86, 1.28, 56]} />
        <meshBasicMaterial color={color} transparent opacity={0.42} />
      </mesh>
      <mesh ref={ringA} position={[0, 1.47, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.34, 0.02, 8, 64]} />
        <meshBasicMaterial color={color} transparent opacity={0.5} />
      </mesh>
      <mesh ref={ringB} position={[0, 1.47, 0]} rotation={[0, 0, Math.PI / 3]}>
        <torusGeometry args={[1.58, 0.014, 8, 64]} />
        <meshBasicMaterial color={color} transparent opacity={0.3} />
      </mesh>

      <pointLight position={[0, 1.8, 0]} color={color} intensity={active || state === "VERIFIED" ? 4.0 : 1.3} distance={8} />

      <Html position={[0, 2.96, 0]} center distanceFactor={18} zIndexRange={[18, 0]}>
        <span className="world-label mission-stone-label" style={{ borderColor: color, color }}>
          MISSION STONE · {STONE_LABEL[state]}
        </span>
      </Html>
    </group>
  );
}
