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
  PENDING: "PENDING",
  VERIFIED: "LOCAL_VERIFIED",
  FAILED: "FAILED",
};

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
      core.current.rotation.y += delta * 0.34;
      core.current.rotation.x += delta * 0.1;
      const pulse = proof === "PENDING" ? 1 + Math.sin(t * 3.1) * 0.1 : proof === "VERIFIED" ? 1.04 : 1;
      core.current.scale.setScalar(pulse);
    }
    if (ringA.current) ringA.current.rotation.z += delta * (proof === "PENDING" ? 1.5 : 0.34);
    if (ringB.current) ringB.current.rotation.x -= delta * (proof === "PENDING" ? 1.0 : 0.22);
  });

  return (
    <group position={CORE_POSITION} onClick={onOpen}>
      <mesh ref={core}>
        <icosahedronGeometry args={[1.0, 1]} />
        <meshStandardMaterial
          color="#061419"
          emissive={color}
          emissiveIntensity={proof === "VERIFIED" ? 0.92 : 0.68}
          roughness={0.2}
          metalness={0.84}
          flatShading
        />
      </mesh>
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[0.46, 20, 16]} />
        <meshBasicMaterial color={color} transparent opacity={proof === "NONE" ? 0.12 : 0.34} />
      </mesh>
      <mesh ref={ringA} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.8, 0.028, 8, 88]} />
        <meshBasicMaterial color={color} transparent opacity={0.82} />
      </mesh>
      <mesh ref={ringB} rotation={[0, 0, Math.PI / 3]}>
        <torusGeometry args={[2.35, 0.016, 8, 88]} />
        <meshBasicMaterial color={color} transparent opacity={0.44} />
      </mesh>
      <pointLight color={color} intensity={proof === "VERIFIED" ? 8.5 : 6.2} distance={18} />

      <Html position={[0, 3.18, 0]} center distanceFactor={19} zIndexRange={[22, 0]}>
        <span className="core-label" style={{ borderColor: color }}>
          <b>APR PROOF CORE</b>
          <u>WYKONANIE · {EXECUTION_LABEL[execution]}</u>
          <i style={{ color }}>WERYFIKACJA · {PROOF_LABEL[proof]}</i>
        </span>
      </Html>
    </group>
  );
}
