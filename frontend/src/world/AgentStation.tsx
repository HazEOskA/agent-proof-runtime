import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import * as THREE from "three";
import { COLORS, IDLE_POSITIONS, STATION_POSITIONS, workPoint } from "./theme";
import type { AgentSlot } from "../runtime/worldState";

const STATUS_COLOR: Record<AgentSlot["status"], string> = {
  IDLE: "#2c4a52",
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

/**
 * One physical workstation. The avatar walks here when the runtime reports
 * that its stage started. The walk is interpolated; the decision is not.
 */
export function AgentStation({ slot }: { slot: AgentSlot }) {
  const avatar = useRef<THREE.Group>(null);
  const column = useRef<THREE.Mesh>(null);
  const station = STATION_POSITIONS[slot.index];
  const idle = IDLE_POSITIONS[slot.index];
  const work = workPoint(slot.index);
  const engaged = slot.status === "WORKING" || slot.status === "ASSIGNED";
  const color = STATUS_COLOR[slot.status];

  useFrame((frame, delta) => {
    if (avatar.current) {
      const target = engaged ? work : idle;
      avatar.current.position.x = THREE.MathUtils.damp(avatar.current.position.x, target.x, 2.2, delta);
      avatar.current.position.z = THREE.MathUtils.damp(avatar.current.position.z, target.z, 2.2, delta);
      avatar.current.position.y = Math.abs(Math.sin(frame.clock.elapsedTime * 2.4 + slot.index)) * 0.05;
      avatar.current.lookAt(engaged ? station.x : 0, 0.95, engaged ? station.z : 0);
    }
    if (column.current) {
      const material = column.current.material as THREE.MeshBasicMaterial;
      const target = slot.status === "WORKING" ? 0.1 + Math.abs(Math.sin(frame.clock.elapsedTime * 2.6)) * 0.08 : 0.02;
      material.opacity = THREE.MathUtils.damp(material.opacity, target, 3, delta);
    }
  });

  return (
    <group>
      <group position={station}>
        {/* pedestal */}
        <mesh position={[0, 0.3, 0]} receiveShadow castShadow>
          <cylinderGeometry args={[1.35, 1.5, 0.6, 6]} />
          <meshStandardMaterial color="#0a1a20" roughness={0.55} metalness={0.55} />
        </mesh>
        {/* holographic desk */}
        <mesh position={[0, 1.02, 0]} rotation={[-Math.PI / 2.6, 0, 0]}>
          <planeGeometry args={[1.8, 1.0]} />
          <meshBasicMaterial color={color} transparent opacity={0.16} side={THREE.DoubleSide} />
        </mesh>
        <mesh position={[0, 0.62, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[1.08, 1.3, 42]} />
          <meshBasicMaterial color={color} transparent opacity={0.5} />
        </mesh>
        {/* activity column */}
        <mesh ref={column} position={[0, 2.6, 0]}>
          <cylinderGeometry args={[0.32, 0.52, 3.8, 18, 1, true]} />
          <meshBasicMaterial color={color} transparent opacity={0.02} side={THREE.DoubleSide} depthWrite={false} />
        </mesh>
        <pointLight position={[0, 1.7, 0]} color={color} intensity={slot.status === "WORKING" ? 3.2 : 0.9} distance={7} />

        {/* artifact shard, present once the stage produced a hash */}
        {slot.outputHash && (
          <mesh position={[0, 1.85, 0]} rotation={[0.4, 0.6, 0]}>
            <octahedronGeometry args={[0.28, 0]} />
            <meshStandardMaterial color={COLORS.green} emissive={COLORS.green} emissiveIntensity={0.65} />
          </mesh>
        )}

        <Html position={[0, 2.85, 0]} center distanceFactor={19} zIndexRange={[15, 0]}>
          <span className="station-label" style={{ borderColor: color }}>
            <b>AGENT 0{slot.index + 1}</b>
            <i style={{ color }}>{slot.role ?? STATUS_LABEL[slot.status]}</i>
            <em>{slot.role ? STATUS_LABEL[slot.status] : "OCZEKUJE NA RUNTIME"}</em>
          </span>
        </Html>
      </group>

      {/* the agent itself */}
      <group ref={avatar} position={[idle.x, 0, idle.z]}>
        <mesh position={[0, 0.72, 0]} castShadow>
          <capsuleGeometry args={[0.24, 0.64, 6, 14]} />
          <meshStandardMaterial color="#12272e" roughness={0.6} metalness={0.35} />
        </mesh>
        <mesh position={[0, 1.34, 0]} castShadow>
          <sphereGeometry args={[0.21, 18, 14]} />
          <meshStandardMaterial color="#183a44" roughness={0.45} metalness={0.4} />
        </mesh>
        <mesh position={[0, 1.34, 0.18]}>
          <sphereGeometry args={[0.07, 12, 10]} />
          <meshBasicMaterial color={color} />
        </mesh>
        <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.3, 0.42, 24]} />
          <meshBasicMaterial color={color} transparent opacity={0.6} />
        </mesh>
      </group>
    </group>
  );
}
