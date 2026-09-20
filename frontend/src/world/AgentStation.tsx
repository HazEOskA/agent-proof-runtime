import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import * as THREE from "three";
import { COLORS, IDLE_POSITIONS, STATION_POSITIONS, workPoint } from "./theme";
import type { AgentSlot } from "../runtime/worldState";

const STATUS_COLOR: Record<AgentSlot["status"], string> = {
  IDLE: "#28474f",
  ASSIGNED: COLORS.blue,
  WORKING: COLORS.cyan,
  DONE: COLORS.green,
  FAILED: COLORS.red,
};

const STATUS_LABEL: Record<AgentSlot["status"], string> = {
  IDLE: "WOLNE",
  ASSIGNED: "PRZYDZIELONE",
  WORKING: "PRACUJE",
  DONE: "UKOŃCZONE",
  FAILED: "BŁĄD",
};

export function AgentStation({ slot }: { slot: AgentSlot }) {
  const avatar = useRef<THREE.Group>(null);
  const column = useRef<THREE.Mesh>(null);
  const ring = useRef<THREE.Mesh>(null);
  const station = STATION_POSITIONS[slot.index];
  const idle = IDLE_POSITIONS[slot.index];
  const work = workPoint(slot.index);
  const engaged = slot.status === "WORKING" || slot.status === "ASSIGNED";
  const color = STATUS_COLOR[slot.status];

  useFrame((frame, delta) => {
    if (avatar.current) {
      const target = engaged ? work : idle;
      avatar.current.position.x = THREE.MathUtils.damp(avatar.current.position.x, target.x, 2.5, delta);
      avatar.current.position.z = THREE.MathUtils.damp(avatar.current.position.z, target.z, 2.5, delta);
      avatar.current.position.y = Math.sin(frame.clock.elapsedTime * 1.35 + slot.index) * 0.035;
      avatar.current.lookAt(engaged ? station.x : 0, 1.0, engaged ? station.z : 0);
    }
    if (column.current) {
      const material = column.current.material as THREE.MeshBasicMaterial;
      const target = slot.status === "WORKING" ? 0.12 + Math.abs(Math.sin(frame.clock.elapsedTime * 2.2)) * 0.1 : 0.018;
      material.opacity = THREE.MathUtils.damp(material.opacity, target, 3.2, delta);
    }
    if (ring.current) ring.current.rotation.z += delta * (slot.status === "WORKING" ? 0.7 : 0.16);
  });

  return (
    <group>
      <group position={station}>
        <mesh position={[0, 0.28, 0]} receiveShadow castShadow>
          <cylinderGeometry args={[1.48, 1.68, 0.56, 8]} />
          <meshStandardMaterial color="#08171c" roughness={0.46} metalness={0.62} />
        </mesh>
        <mesh position={[0, 0.62, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[1.12, 1.38, 56]} />
          <meshBasicMaterial color={color} transparent opacity={slot.status === "IDLE" ? 0.28 : 0.68} />
        </mesh>
        <mesh position={[0, 1.06, 0]} rotation={[-Math.PI / 2.48, 0, 0]}>
          <planeGeometry args={[2.0, 1.08]} />
          <meshBasicMaterial color={color} transparent opacity={engaged ? 0.2 : 0.08} side={THREE.DoubleSide} />
        </mesh>
        <mesh ref={ring} position={[0, 1.74, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.72, 0.018, 8, 56]} />
          <meshBasicMaterial color={color} transparent opacity={engaged ? 0.62 : 0.18} />
        </mesh>
        <mesh ref={column} position={[0, 2.8, 0]}>
          <cylinderGeometry args={[0.34, 0.62, 4.1, 22, 1, true]} />
          <meshBasicMaterial color={color} transparent opacity={0.018} side={THREE.DoubleSide} depthWrite={false} />
        </mesh>

        <pointLight
          position={[0, 1.7, 0]}
          color={color}
          intensity={slot.status === "WORKING" ? 3.8 : slot.status === "DONE" ? 1.6 : 0.65}
          distance={8}
        />

        {slot.outputHash && (
          <group position={[0, 1.92, 0]}>
            <mesh rotation={[0.45, 0.65, 0]}>
              <octahedronGeometry args={[0.31, 0]} />
              <meshStandardMaterial color={COLORS.green} emissive={COLORS.green} emissiveIntensity={0.8} metalness={0.45} />
            </mesh>
            <Html position={[0, 0.58, 0]} center distanceFactor={20} zIndexRange={[13, 0]}>
              <span className="artifact-label">ARTIFACT · {slot.outputHash.slice(0, 10)}…</span>
            </Html>
          </group>
        )}

        <Html position={[0, 3.04, 0]} center distanceFactor={18} zIndexRange={[15, 0]}>
          <span className="station-label" style={{ borderColor: color }}>
            <b>AGENT 0{slot.index + 1}</b>
            <i style={{ color }}>{slot.role ?? STATUS_LABEL[slot.status]}</i>
            <em>{slot.role ? STATUS_LABEL[slot.status] : "OCZEKUJE NA RUNTIME"}</em>
          </span>
        </Html>
      </group>

      <group ref={avatar} position={[idle.x, 0, idle.z]}>
        <mesh position={[0, 0.76, 0]} castShadow>
          <capsuleGeometry args={[0.28, 0.72, 7, 16]} />
          <meshStandardMaterial color="#10252c" roughness={0.5} metalness={0.42} />
        </mesh>
        <mesh position={[0, 1.4, 0]} castShadow>
          <sphereGeometry args={[0.23, 20, 16]} />
          <meshStandardMaterial color="#17343e" roughness={0.4} metalness={0.45} />
        </mesh>
        <mesh position={[0, 1.4, 0.21]}>
          <planeGeometry args={[0.16, 0.07]} />
          <meshBasicMaterial color={color} transparent opacity={0.92} />
        </mesh>
        <mesh position={[0, 0.06, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.34, 0.46, 28]} />
          <meshBasicMaterial color={color} transparent opacity={engaged ? 0.78 : 0.36} />
        </mesh>
      </group>
    </group>
  );
}
