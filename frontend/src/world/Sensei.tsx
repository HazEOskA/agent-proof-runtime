import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import * as THREE from "three";
import { COLORS, SENSEI_POSITION } from "./theme";

interface SenseiProps {
  online: boolean;
  onOpen: () => void;
}

/** The orchestrator interface. Central, physical, always the way in. */
export function Sensei({ online, onOpen }: SenseiProps) {
  const halo = useRef<THREE.Mesh>(null);
  const inner = useRef<THREE.Mesh>(null);

  useFrame((state, delta) => {
    if (halo.current) halo.current.rotation.z += delta * 0.35;
    if (inner.current) {
      inner.current.rotation.y -= delta * 0.6;
      inner.current.position.y = 2.42 + Math.sin(state.clock.elapsedTime * 1.2) * 0.05;
    }
  });

  const accent = online ? COLORS.cyan : COLORS.red;

  return (
    <group position={SENSEI_POSITION} onClick={onOpen}>
      {/* plinth */}
      <mesh position={[0, 0.16, 0]} receiveShadow>
        <cylinderGeometry args={[1.5, 1.7, 0.32, 48]} />
        <meshStandardMaterial color="#0a1a1f" roughness={0.5} metalness={0.6} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.33, 0]}>
        <ringGeometry args={[1.18, 1.44, 64]} />
        <meshBasicMaterial color={accent} transparent opacity={0.72} />
      </mesh>

      {/* robed body */}
      <mesh position={[0, 1.18, 0]} castShadow>
        <coneGeometry args={[0.82, 1.9, 24]} />
        <meshStandardMaterial color="#0e232a" roughness={0.62} metalness={0.3} />
      </mesh>
      <mesh position={[0, 1.02, 0]}>
        <torusGeometry args={[0.58, 0.035, 8, 40]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.8} />
      </mesh>

      {/* head and hat */}
      <mesh position={[0, 2.26, 0]} castShadow>
        <sphereGeometry args={[0.3, 24, 20]} />
        <meshStandardMaterial color="#13303a" roughness={0.5} metalness={0.35} />
      </mesh>
      <mesh position={[0, 2.5, 0]} castShadow>
        <coneGeometry args={[0.92, 0.42, 26]} />
        <meshStandardMaterial color="#0c2029" roughness={0.6} metalness={0.4} />
      </mesh>

      {/* orbiting sigil */}
      <mesh ref={inner} position={[0, 2.42, 0]}>
        <torusGeometry args={[1.28, 0.018, 8, 60]} />
        <meshBasicMaterial color={accent} transparent opacity={0.85} />
      </mesh>
      <mesh ref={halo} position={[0, 1.6, 0]} rotation={[Math.PI / 2.1, 0, 0]}>
        <torusGeometry args={[1.62, 0.012, 8, 72]} />
        <meshBasicMaterial color={accent} transparent opacity={0.5} />
      </mesh>

      <pointLight position={[0, 2.1, 0]} color={accent} intensity={online ? 4.5 : 1.6} distance={11} />

      {/* invitation */}
      <Html position={[0, 4.15, 0]} center distanceFactor={19} zIndexRange={[20, 0]}>
        <button
          type="button"
          className={`world-label world-label--action${online ? "" : " is-muted"}`}
          onClick={(browserEvent) => {
            browserEvent.stopPropagation();
            onOpen();
          }}
        >
          POROZMAWIAJ Z SENSEIEM
        </button>
      </Html>
      <Html position={[0, 3.74, 0]} center distanceFactor={19} zIndexRange={[19, 0]}>
        <span className="world-label world-label--quiet">SENSEI · ORKIESTRATOR APR</span>
      </Html>
    </group>
  );
}
