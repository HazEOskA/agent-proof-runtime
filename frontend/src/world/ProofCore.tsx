import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import * as THREE from "three";
import { COLORS, CORE_POSITION } from "./theme";
import type { ExecutionStatus, ProofStatus } from "../runtime/worldState";

const PROOF_COLOR: Record<ProofStatus, string> = {
  NONE: COLORS.cyanDeep,
  PENDING: COLORS.amber,
  VERIFIED: COLORS.green,
  FAILED: COLORS.red,
};

const EXECUTION_LABEL: Record<ExecutionStatus, string> = {
  IDLE: "BEZCZYNNE",
  RUNNING: "W TRAKCIE",
  COMPLETED: "ZAKOŃCZONE",
  FAILED: "NIEUDANE",
};

const PROOF_LABEL: Record<ProofStatus, string> = {
  NONE: "BRAK",
  PENDING: "OCZEKUJE NA WERYFIKACJĘ",
  VERIFIED: "LOCAL_VERIFIED",
  FAILED: "NIEZWERYFIKOWANE",
};

/** APR PROOF CORE. Execution and proof are shown apart, never merged. */
export function ProofCore({
  execution,
  proof,
  onOpen,
}: {
  execution: ExecutionStatus;
  proof: ProofStatus;
  onOpen: () => void;
}) {
  const core = useRef<THREE.Mesh>(null);
  const ringA = useRef<THREE.Mesh>(null);
  const ringB = useRef<THREE.Mesh>(null);
  const color = PROOF_COLOR[proof];

  useFrame((frame, delta) => {
    const t = frame.clock.elapsedTime;
    if (core.current) {
      core.current.rotation.y += delta * 0.4;
      core.current.rotation.x += delta * 0.15;
      const pulse = proof === "PENDING" ? 1 + Math.sin(t * 3.4) * 0.09 : 1;
      core.current.scale.setScalar(pulse);
    }
    if (ringA.current) ringA.current.rotation.z += delta * (proof === "PENDING" ? 1.3 : 0.4);
    if (ringB.current) ringB.current.rotation.x -= delta * (proof === "PENDING" ? 0.9 : 0.25);
  });

  return (
    <group position={CORE_POSITION} onClick={onOpen}>
      <mesh ref={core}>
        <icosahedronGeometry args={[0.92, 1]} />
        <meshStandardMaterial
          color="#08181d"
          emissive={color}
          emissiveIntensity={0.7}
          roughness={0.25}
          metalness={0.8}
          flatShading
        />
      </mesh>
      <mesh ref={ringA} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.7, 0.026, 8, 80]} />
        <meshBasicMaterial color={color} transparent opacity={0.85} />
      </mesh>
      <mesh ref={ringB} rotation={[0, 0, Math.PI / 3]}>
        <torusGeometry args={[2.25, 0.015, 8, 80]} />
        <meshBasicMaterial color={color} transparent opacity={0.5} />
      </mesh>
      <pointLight color={color} intensity={7} distance={17} />

      <Html position={[0, 2.85, 0]} center distanceFactor={20} zIndexRange={[22, 0]}>
        <span className="core-label" style={{ borderColor: color }}>
          <b>APR PROOF CORE</b>
          <u>WYKONANIE · {EXECUTION_LABEL[execution]}</u>
          <i style={{ color }}>WERYFIKACJA · {PROOF_LABEL[proof]}</i>
        </span>
      </Html>
    </group>
  );
}
