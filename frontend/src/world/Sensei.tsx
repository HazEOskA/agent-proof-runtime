import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import * as THREE from "three";
import { COLORS, SENSEI_POSITION } from "./theme";

interface SenseiProps {
  online: boolean;
  onOpen: () => void;
}

export function Sensei({ online, onOpen }: SenseiProps) {
  const halo = useRef<THREE.Mesh>(null);
  const inner = useRef<THREE.Mesh>(null);
  const body = useRef<THREE.Group>(null);

  useFrame((state, delta) => {
    if (halo.current) halo.current.rotation.z += delta * 0.24;
    if (inner.current) inner.current.rotation.y -= delta * 0.42;
    if (body.current) body.current.position.y = Math.sin(state.clock.elapsedTime * 0.8) * 0.035;
  });

  const accent = online ? COLORS.cyan : COLORS.red;

  return (
    <group position={SENSEI_POSITION} onClick={onOpen}>
      <mesh position={[0, 0.12, 0]} receiveShadow>
        <cylinderGeometry args={[1.7, 1.9, 0.3, 64]} />
        <meshStandardMaterial color="#08171c" roughness={0.46} metalness={0.65} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.3, 0]}>
        <ringGeometry args={[1.18, 1.58, 72]} />
        <meshBasicMaterial color={accent} transparent opacity={online ? 0.68 : 0.34} />
      </mesh>

      <group ref={body}>
        <mesh position={[0, 1.14, 0]} castShadow>
          <coneGeometry args={[0.86, 1.95, 28]} />
          <meshStandardMaterial color="#0b2027" roughness={0.58} metalness={0.4} />
        </mesh>
        <mesh position={[0, 1.12, 0]}>
          <torusGeometry args={[0.61, 0.032, 10, 48]} />
          <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.9} />
        </mesh>
        <mesh position={[0, 2.29, 0]} castShadow>
          <sphereGeometry args={[0.3, 28, 22]} />
          <meshStandardMaterial color="#14323a" roughness={0.4} metalness={0.42} />
        </mesh>
        <mesh position={[0, 2.51, 0]} castShadow>
          <coneGeometry args={[0.96, 0.4, 32]} />
          <meshStandardMaterial color="#091c23" roughness={0.56} metalness={0.5} />
        </mesh>
        <mesh position={[0, 2.3, 0.27]}>
          <planeGeometry args={[0.22, 0.08]} />
          <meshBasicMaterial color={accent} transparent opacity={0.92} />
        </mesh>
      </group>

      <mesh ref={inner} position={[0, 2.46, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.34, 0.018, 8, 72]} />
        <meshBasicMaterial color={accent} transparent opacity={0.82} />
      </mesh>
      <mesh ref={halo} position={[0, 1.6, 0]} rotation={[Math.PI / 2.05, 0, 0]}>
        <torusGeometry args={[1.82, 0.013, 8, 84]} />
        <meshBasicMaterial color={accent} transparent opacity={0.44} />
      </mesh>

      <pointLight position={[0, 2.0, 0]} color={accent} intensity={online ? 4.1 : 1.4} distance={12} />

      <Html position={[0, 4.12, 0]} center distanceFactor={18} zIndexRange={[20, 0]}>
        <button
          type="button"
          className={"world-label world-label--action" + (online ? "" : " is-muted")}
          onClick={(event) => {
            event.stopPropagation();
            onOpen();
          }}
        >
          {online ? "POROZMAWIAJ Z SENSEIEM" : "SENSEI · APR OFFLINE"}
        </button>
      </Html>
      <Html position={[0, 3.7, 0]} center distanceFactor={18} zIndexRange={[19, 0]}>
        <span className="world-label world-label--quiet">SENSEI // ORKIESTRATOR</span>
      </Html>
    </group>
  );
}
